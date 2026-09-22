import yaml
import requests
import json

API = "https://api.github.com"
OWNER = "dbpedia"
REPO = "kg-catalog"
BRANCH = "main"
PREFIX = "knowledge-graphs/"

def json_default(value):
    """Convert YAML date/datetime values into JSON-compatible strings."""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def getAllDatasetIDs(repo_url = f"{API}/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1"):

    headers = {
        "Accept": "application/vnd.github+json"
    }

    response = requests.get(
        repo_url,
        headers=headers
    )
    response.raise_for_status()

    tree = response.json()["tree"]

    metadata_paths = [
    item["path"]
    for item in tree
    if item["type"] == "blob"
    and item["path"].startswith(PREFIX)
    and item["path"].endswith("/metadata.yaml")
]
    results = []

    for path in metadata_paths:
        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{OWNER}/{REPO}/{BRANCH}/{path}"
        )

        metadata_response = requests.get(raw_url)
        metadata_response.raise_for_status()
        

        metadata = yaml.safe_load(metadata_response.text)
        results.append({
            "directory": path.removesuffix("/metadata.yaml"),
            "metadata": metadata
        })

    print(f"Found {len(results)} knowledge graphs")

    if results:
        print(f"Saving metadata to kg-catalog-metadata.json")
        with open("kg-catalog-metadata.json", "w", encoding="utf-8") as f:
            json.dump(
                results,
                f,
                ensure_ascii=False,
                indent=2,
                default=json_default,
            )
    else:
        with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
            results = json.load(f)

    return results

def getDatasetMetadata(idKG):
    metadata_list = getAllDatasetIDs()
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"]
    return False

def getLocalDatasetMetadata(idKG):
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"]
    return False

def getDatasetName(metadata):
    idKG = metadata.get("id")
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("title")
    return False

def getLicense(metadata):
    idKG = metadata.get("id")
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("license")
    return False

def getAuthor(metadata):
    idKG = metadata.get("id")
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("maintainers").get("name")
    return False

def getSource(metadata):
    idKG = metadata.get("id")
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("homepage")
    return False

def getTriples(metadata):
    idKG = metadata.get("id")
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("last-version-size")
    return False

def getSPARQLEndpoint(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    if isinstance(metadata,dict):
        sparql = metadata.get('sparql')
        if isinstance(sparql,dict):
            url = sparql.get('url')
            return url
        else:
            return False
    else:
        return False

def getOtherResources(idKG):  
    metadata = getLocalDatasetMetadata(idKG)
    if not isinstance(metadata, dict):
        return False

    resources = []
    artifacts = metadata.get("artifacts", [])

    # KGCatalog stores downloads as artifacts -> versions -> distributions.
    # Aggregator expects a flat list with at least a `path` field.
    for artifact in artifacts if isinstance(artifacts, list) else []:
        if not isinstance(artifact, dict):
            continue
        for version in artifact.get("versions", []):
            if not isinstance(version, dict):
                continue
            for distribution in version.get("distributions", []):
                if not isinstance(distribution, dict):
                    continue

                path = distribution.get("file")
                if not isinstance(path, str) or not path.strip():
                    continue

                resource = {
                    "path": path.strip(),
                    "format": distribution.get("format"),
                }

                # Preserve useful catalog information without changing the
                # field names consumed by Aggregator.
                for key in ("compression", "size", "sha256", "status"):
                    if key in distribution:
                        resource[key] = distribution[key]
                resources.append(resource)

    # The largest declared distribution is the best catalog equivalent of a
    # full download. Other resources remain available to the Aggregator.
    sized_resources = [
        resource for resource in resources
        if isinstance(resource.get("size"), (int, float))
    ]
    if sized_resources:
        largest = max(sized_resources, key=lambda resource: resource["size"])
        largest["type"] = "full_download"

    return resources

# TODO: Update with correct links discovering when KGCatalog supports them
def getExternalLinks(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    if not isinstance(metadata, dict):
        return False

    links = metadata.get("links")
    if isinstance(links, list):
        return links
    return []

def getDescription(metadata):
    idKG = metadata.get("id")
    with open("kg-catalog-metadata.json", "r", encoding="utf-8") as f:
        metadata_list = json.load(f)
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("description")
    return False

def getLanguage(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    for item in metadata:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("language")
    return False

def getKeywords(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    for item in metadata:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("keywords")
    return []

def getDOI(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    for item in metadata:
        if item["metadata"].get("id") == idKG:
            return item["metadata"].get("doi")
    return False
    
if __name__ == "__main__":
    metadata_list = getAllDatasetIDs()
    metadata = getLocalDatasetMetadata("dblp")
    title = getDatasetName(metadata)
    license = getLicense(metadata)
    print(f"Title for 'dblp': {title}")
    print(f"License for 'dblp': {license}")
    print(f"Metadata for 'dblp':")
    print(json.dumps(metadata, indent=2, ensure_ascii=False, default=json_default))
