import json
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
import dotenv
import requests

dotenv.load_dotenv()

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")

SEARCH_QUERY = "endpoint extension:rq"

PER_PAGE = 100
MAX_PAGES = 10

SPARQL_TIMEOUT = 10

OUTPUT_FILE = "gitHub_endpoints.json"

ENDPOINT_RE = re.compile(
    r"^\s*#\+\s*endpoint\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


github_headers = {
    "Accept": "application/vnd.github+json",
}

if GITHUB_TOKEN:
    github_headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def search_github():
    """
    Search GitHub for .rq files containing the word 'endpoint'.
    """

    for page in range(1, MAX_PAGES + 1):
        print(f"Searching GitHub page {page}...")

        response = requests.get(
            f"{GITHUB_API}/search/code",
            headers=github_headers,
            params={
                "q": SEARCH_QUERY,
                "per_page": PER_PAGE,
                "page": page,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        if not items:
            break

        yield from items

        if len(items) < PER_PAGE:
            break

        time.sleep(1)


def download_rq(item):
    """
    Download the raw contents of a .rq file returned by GitHub search.
    """

    headers = dict(github_headers)
    headers["Accept"] = "application/vnd.github.raw+json"

    response = requests.get(
        item["url"],
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def extract_endpoints(text):
    """
    Extract endpoint declarations such as:

        #+ endpoint: https://example.org/sparql

    Also supports:

        #+ endpoint: https://one.org/sparql, https://two.org/sparql
    """

    endpoints = []

    for match in ENDPOINT_RE.finditer(text):
        value = match.group(1)

        for endpoint in value.split(","):
            endpoint = endpoint.strip()

            if endpoint:
                endpoints.append(endpoint)

    return endpoints


def normalize_endpoint(endpoint):
    """
    Normalize trivial differences so duplicate URLs are more easily detected.
    """

    endpoint = endpoint.strip()

    # Remove trailing slash for duplicate detection.
    if endpoint.endswith("/"):
        endpoint = endpoint[:-1]

    return endpoint


def is_valid_endpoint_url(endpoint):
    """
    Accept only HTTP(S) URLs and skip localhost endpoints.
    """

    try:
        parsed = urlparse(endpoint)
    except ValueError:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    hostname = parsed.hostname

    if not hostname:
        return False

    hostname = hostname.lower()

    blocked_hosts = {
        "localhost",
        "127.0.0.1",
        "::1",
    }

    if hostname in blocked_hosts:
        return False

    return True


def contains_result(response):
    """
    Return True only when the SPARQL JSON response contains at least one row.
    """

    try:
        data = response.json()
    except ValueError:
        return False

    bindings = data.get("results", {}).get("bindings", [])

    return len(bindings) > 0


def execute_query(endpoint, query):
    """
    Try a SPARQL query using GET first, then POST.
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "sparql-endpoint-discovery/0.1",
    }

    # Try GET
    try:
        response = requests.get(
            endpoint,
            params={"query": query},
            headers=headers,
            timeout=SPARQL_TIMEOUT,
        )

        if response.ok and contains_result(response):
            return {
                "working": True,
                "status_code": response.status_code,
                "method": "GET",
            }

    except requests.RequestException:
        pass

    # Try POST
    try:
        response = requests.post(
            endpoint,
            data={"query": query},
            headers=headers,
            timeout=SPARQL_TIMEOUT,
        )

        if response.ok and contains_result(response):
            return {
                "working": True,
                "status_code": response.status_code,
                "method": "POST",
            }

    except requests.RequestException:
        pass

    return {
        "working": False,
        "status_code": None,
        "method": None,
    }


def test_endpoint(endpoint):
    """
    Try retrieving one triple.

    First check the default graph, then named graphs.
    """

    queries = [
        """
        SELECT ?s ?p ?o
        WHERE {
            ?s ?p ?o
        }
        LIMIT 1
        """,

        """
        SELECT ?g ?s ?p ?o
        WHERE {
            GRAPH ?g {
                ?s ?p ?o
            }
        }
        LIMIT 1
        """,
    ]

    for query in queries:
        result = execute_query(endpoint, query)

        if result["working"]:
            return result

    return {
        "working": False,
        "status_code": None,
        "method": None,
    }

def get_endpoint_urls_from_github():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for endpoint in json.load(f).get("endpoints", []):
            yield endpoint["endpoint"]


def main():

    # Cache of endpoints already encountered during this execution.
    seen_endpoints = set()

    working_endpoints = []

    total_discovered = 0
    duplicates_skipped = 0
    local_skipped = 0
    invalid_skipped = 0

    for item in search_github():

        repository = item["repository"]["full_name"]
        path = item["path"]
        github_url = item["html_url"]

        try:
            text = download_rq(item)

        except requests.RequestException as exc:
            print(
                f"Could not download "
                f"{repository}/{path}: {exc}"
            )
            continue

        endpoints = extract_endpoints(text)

        for endpoint in endpoints:

            total_discovered += 1

            endpoint = normalize_endpoint(endpoint)

            #
            # CACHE CHECK
            #
            if endpoint in seen_endpoints:
                duplicates_skipped += 1

                print(
                    f"Skipping duplicate: {endpoint}"
                )

                continue

            # Add immediately so we never process it twice.
            seen_endpoints.add(endpoint)

            #
            # URL VALIDATION
            #
            parsed = urlparse(endpoint)

            hostname = (
                parsed.hostname.lower()
                if parsed.hostname
                else None
            )

            if hostname in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                local_skipped += 1

                print(
                    f"Skipping local endpoint: {endpoint}"
                )

                continue

            if not is_valid_endpoint_url(endpoint):
                invalid_skipped += 1

                print(
                    f"Skipping invalid endpoint: {endpoint}"
                )

                continue

            #
            # TEST ENDPOINT
            #
            print()
            print(f"Testing: {endpoint}")

            result = test_endpoint(endpoint)

            if not result["working"]:
                print("  ✗ Not working")
                continue

            print("  ✓ Working")

            working_endpoints.append(
                {
                    "endpoint": endpoint,
                    "repository": repository,
                    "rq_file": path,
                    "github_url": github_url,
                    "method": result["method"],
                    "status_code": result["status_code"],
                    "checked_at": datetime.now(
                        timezone.utc
                    ).isoformat(),
                }
            )

    #
    # WRITE JSON
    #
    output = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),

        "statistics": {
            "endpoint_occurrences": total_discovered,
            "unique_endpoints": len(seen_endpoints),
            "duplicates_skipped": duplicates_skipped,
            "local_endpoints_skipped": local_skipped,
            "invalid_endpoints_skipped": invalid_skipped,
            "working_endpoints": len(working_endpoints),
        },

        "endpoints": working_endpoints,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print()
    print("Finished.")
    print(f"Occurrences found:    {total_discovered}")
    print(f"Unique endpoints:     {len(seen_endpoints)}")
    print(f"Duplicates skipped:   {duplicates_skipped}")
    print(f"Local skipped:        {local_skipped}")
    print(f"Invalid skipped:      {invalid_skipped}")
    print(f"Working endpoints:    {len(working_endpoints)}")
    print()
    print(f"Results written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()