import json
import logging
import os
from pathlib import Path
import re
import tempfile
import time

from SPARQLWrapper import JSON, POST, SPARQLWrapper



WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
USER_AGENT = "KGHeartbeat/1.5 (https://github.com/isislab-unisa/KGHeartbeat)"
logger = logging.getLogger(__name__)


def _query(query, context="query"):
    for attempt in range(3):
        started = time.monotonic()
        try:
            logger.info("Wikidata %s: attempt %d/3", context, attempt + 1)
            sparql = SPARQLWrapper(WIKIDATA_SPARQL_URL)
            sparql.setMethod(POST)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(300)
            sparql.addCustomHttpHeader("User-Agent", USER_AGENT)
            data = sparql.query().convert()
            logger.info(
                "Wikidata %s completed in %.1fs", context, time.monotonic() - started
            )
            return data
        except Exception as e:
            logger.warning(
                "Wikidata %s failed on attempt %d/3 after %.1fs (%s): %s",
                context, attempt + 1, time.monotonic() - started,
                type(e).__name__, e,
            )
            if attempt == 2:
                return False
            time.sleep(5 * (2 ** attempt))

    return False


def _save_catalogue(catalogue, path):
    """Replace the catalogue atomically so interruptions leave valid JSON."""
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.name}.", suffix=".tmp", delete=False,
        ) as output:
            temporary_path = Path(output.name)
            json.dump(catalogue, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def getWikidataSPARQLEndpoint(
    include_metadata=False, catalogue_path="wikidata-catalogue.json"
):
    """List endpoints; optionally fetch metadata sequentially for every result.

    By default, results contain only qid, title, and access_url. Use
    getMetadata(qid) to fetch metadata for selected entities separately.
    With include_metadata=True, save each successful result to catalogue_path
    (relative to the current working directory). Existing entries are refreshed
    by QID and endpoint; failed requests leave saved metadata intact.
    """
    query = """
SELECT ?item ?name ?endpoint
WHERE {
  ?item wdt:P5305 ?endpoint.
  OPTIONAL {
    ?item rdfs:label ?labelEN.
    FILTER(LANG(?labelEN) = "en")
  }
  OPTIONAL {
    ?item rdfs:label ?labelMUL.
    FILTER(LANG(?labelMUL) = "mul")
  }
  BIND(COALESCE(?labelEN, ?labelMUL, STRAFTER(STR(?item), "/entity/")) AS ?name)
}
ORDER BY ?name
"""
    data = _query(query, context="endpoint discovery")

    if not data:
        return False

    datasets = []
    for result in data.get("results", {}).get("bindings", []):
        item = result.get("item", {}).get("value", "")
        endpoint = result.get("endpoint", {}).get("value")
        if not endpoint:
            continue

        qid_match = re.search(r"/(Q\d+)$", item)
        if not qid_match:
            continue

        qid = qid_match.group(1)
        datasets.append({
            "qid": qid,
            "title": result.get("name", {}).get("value", qid),
            "access_url": endpoint,
        })

    datasets.sort(key=lambda dataset: dataset["title"].casefold())
    logger.info("Wikidata endpoint discovery found %d datasets", len(datasets))
    if include_metadata:
        path = Path(catalogue_path)
        try:
            with path.open(encoding="utf-8") as source:
                catalogue = json.load(source)
        except FileNotFoundError:
            catalogue = []
        if not isinstance(catalogue, list) or any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("qid"), str)
            or not isinstance(entry.get("access_url"), str)
            or not isinstance(entry.get("metadata"), dict)
            for entry in catalogue
        ):
            raise ValueError(f"Invalid Wikidata catalogue: {path}")
        positions = {
            (entry["qid"], entry["access_url"]): index
            for index, entry in enumerate(catalogue)
        }
        for dataset in datasets:
            dataset["metadata"] = getMetadata(dataset["qid"])
            if not dataset["metadata"]:
                logger.warning("No metadata saved for %s", dataset["qid"])
                continue
            key = (dataset["qid"], dataset["access_url"])
            if key in positions:
                catalogue[positions[key]] = dataset
            else:
                positions[key] = len(catalogue)
                catalogue.append(dataset)
            _save_catalogue(catalogue, path)
            logger.info("Saved metadata for %s to %s", dataset["qid"], path)

    return datasets or False


def getMetadata(qid):
    """Return metadata for one Wikidata entity identified by its QID."""
    if not isinstance(qid, str) or not re.fullmatch(r"Q\d+", qid):
        return False

    query = f"""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX wikibase: <http://wikiba.se/ontology#>

SELECT DISTINCT ?itemLabel ?itemDescription ?access_url
                ?propertyId ?propertyLabel ?value ?valueLabel
WHERE {{
  BIND(wd:{qid} AS ?item)
  OPTIONAL {{ ?item wdt:P5305 ?access_url . }}
  OPTIONAL {{ ?item rdfs:label ?itemLabel . FILTER(LANG(?itemLabel) = "en") }}
  OPTIONAL {{ ?item schema:description ?itemDescription . FILTER(LANG(?itemDescription) = "en") }}
  OPTIONAL {{
    ?item ?predicate ?value .
    ?property wikibase:directClaim ?predicate .
    BIND(STRAFTER(STR(?property), "/entity/") AS ?propertyId)
    ?property rdfs:label ?propertyLabel .
    FILTER(LANG(?propertyLabel) = "en")
    OPTIONAL {{ ?value rdfs:label ?valueLabel . FILTER(LANG(?valueLabel) = "en") }}
  }}
}}
"""
    data = _query(query, context=f"metadata for {qid}")
    if not data:
        return False

    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return False

    first = bindings[0]
    metadata = {
        "qid": qid,
        "title": first.get("itemLabel", {}).get("value", ""),
        "description": first.get("itemDescription", {}).get("value", ""),
        "access_url": first.get("access_url", {}).get("value", ""),
        "download_urls": [],
        "linked_datasets": [],
        "keywords": [],
        "doi": [],
        "authors": [],
        "licenses": [],
        "webpages": [],
        "contact_points": [],
        "number_of_triples": [],
        "properties": [],
        "LODC_id": [],
    }

    property_fields = {
        "P4945": "download_urls",       
        "P1325": "download_urls",       
        "P953": "download_urls",        
        "P361": "linked_datasets",      
        "P527": "linked_datasets",      
        "P2702": "linked_datasets",     
        "P921": "keywords",             
        "P356": "doi",    
        "P8605": "LODC_id",
        "P50": "authors",               
        "P2093": "authors",     
        "P170": "authors",       
        "P275": "licenses",            
        "P856": "webpages",             
        "P973": "webpages",        
        "P2699": "webpages",
        "P968": "contact_points",       
        "P11266": "contact_points",     
        "P10209": "number_of_triples",  
        "P4876": "number_of_triples",
    }

    seen = set()
    for binding in bindings:
        property_id = binding.get("propertyId", {}).get("value")
        value = binding.get("value", {}).get("value")
        key = (property_id, value)
        if not property_id or key in seen:
            continue
        seen.add(key)
        metadata["properties"].append({
            "id": property_id,
            "title": binding.get("propertyLabel", {}).get("value", ""),
            "value": value,
            "value_label": binding.get("valueLabel", {}).get("value", ""),
        })

        field = property_fields.get(property_id)
        if field is None:
            continue

        value_label = binding.get("valueLabel", {}).get("value")
        if field == "linked_datasets":
            value = {
                "qid": value.rsplit("/", 1)[-1] if value and "/" in value else value,
                "title": value_label or "",
            }
        elif field in {"authors", "keywords", "licenses"}:
            value = value_label or value
        elif field == "number_of_triples":
            try:
                value = int(value)
            except (TypeError, ValueError):
                pass

        if value not in metadata[field]:
            metadata[field].append(value)

    return metadata

def getLocalMetadata(qid, catalogue_path=None):
    """Return metadata for one Wikidata entity identified by its QID.

    This function reads the local catalogue file (catalogue_path) and returns
    the metadata for the specified QID if it exists. By default, look in the
    working directory, then beside this module. If the QID is not found,
    return False.
    """
    path = Path(catalogue_path) if catalogue_path is not None else Path("wikidata-catalogue.json")
    if catalogue_path is None and not path.exists():
        path = Path(__file__).with_name("wikidata-catalogue.json")
    try:
        with path.open(encoding="utf-8") as source:
            catalogue = json.load(source)
    except FileNotFoundError:
        return False

    for entry in catalogue:
        if entry.get("qid") == qid:
            return entry.get("metadata", {})

    return False


def getDatasetMetadata(qid, catalogue_path=None):
    """Return locally cached Wikidata metadata using the common API name."""
    return getLocalMetadata(qid, catalogue_path)


def getAllDatasetIDs(catalogue_path=None):
    path = Path(catalogue_path) if catalogue_path is not None else Path("wikidata-catalogue.json")
    if catalogue_path is None and not path.exists():
        path = Path(__file__).with_name("wikidata-catalogue.json")
    try:
        with path.open(encoding="utf-8") as source:
            catalogue = json.load(source)
    except FileNotFoundError:
        return []

    return [entry.get("qid") for entry in catalogue if entry.get("qid")]

def getNameKG(metadata):
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()

def getLicense(metadata):
    licenses = metadata.get("licenses")
    if isinstance(licenses, list) and licenses:
        return licenses[0]
    return False

def getAuthor(metadata):
    authors = metadata.get("authors")
    if isinstance(authors, list) and authors:
        return ", ".join(authors)
    return False

def getSource(metadata):
    webpages = metadata.get("webpages")
    if isinstance(webpages, list) and webpages:
        return webpages[0]
    return False

def getTriples(metadata):
    triples = metadata.get("number_of_triples")
    if isinstance(triples, list) and triples:
        return triples[0]
    return False

def getSPARQLEndpoint(qid):
    metadata = getLocalMetadata(qid)
    if not isinstance(metadata, dict):
        return False
    access_url = metadata.get("access_url")
    if isinstance(access_url, str) and access_url.strip():
        return access_url.strip()
    return False

def getOtherResources(qid):
    """Return local download URLs in the resource format used by Aggregator."""
    metadata = getLocalMetadata(qid)
    if not isinstance(metadata, dict):
        return False

    resources = []
    download_urls = metadata.get("download_urls", [])
    if not isinstance(download_urls, list):
        return resources

    seen = set()
    for url in download_urls:
        if not isinstance(url, str) or not url.strip():
            continue
        path = url.strip()
        if path in seen:
            continue
        seen.add(path)
        # Wikidata supplies URLs without media types or a full-dump guarantee.
        # Aggregator can infer RDF formats from recognized file extensions.
        resources.append({"path": path, "format": None})
    return resources

def getExternalLinks(qid):
    metadata = getLocalMetadata(qid)
    linked_datasets = metadata.get("linked_datasets")
    if isinstance(linked_datasets, list) and linked_datasets:
        return [dataset.get("title") for dataset in linked_datasets if isinstance(dataset, dict) and "title" in dataset]
    else:
        return False

def getDescription(metadata):
    description = metadata.get("description")
    if isinstance(description, str) and description.strip():
        return description.strip()
    return False

def getKeywords(qid):
    metadata = getLocalMetadata(qid)
    keywords = metadata.get("keywords")
    if isinstance(keywords, list) and keywords:
        return keywords
    return []

def getDOI(qid):
    metadata = getLocalMetadata(qid)
    doi = metadata.get("doi")
    if isinstance(doi, list) and doi:
        return doi[0]
    return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="List Wikidata SPARQL endpoints.")
    parser.add_argument(
        "--include-metadata", action="store_true",
        help="Fetch and save metadata after each dataset (requires additional queries).",
    )
    parser.add_argument(
        "--catalogue-path", default="wikidata-catalogue.json",
        help="JSON output path used with --include-metadata (default: %(default)s).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    r = getWikidataSPARQLEndpoint(
        include_metadata=args.include_metadata, catalogue_path=args.catalogue_path
    )
    if r is False:
        raise SystemExit("No endpoint results returned; check the query logs above.")
    print(f"Found {len(r)} datasets with SPARQL endpoints in Wikidata.")
    print(json.dumps(r, indent=2, ensure_ascii=False))
