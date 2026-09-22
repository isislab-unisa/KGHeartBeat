import yaml
import requests
import json
from functools import lru_cache
from pathlib import Path

API = "https://api.github.com"
OWNER = "dbpedia"
REPO = "kg-catalog"
BRANCH = "main"
PREFIX = "knowledge-graphs/"
SNAPSHOT_PATH = Path(__file__).with_name("kg-catalog-metadata.json")

def json_default(value):
    """Convert YAML date/datetime values into JSON-compatible strings."""
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


@lru_cache(maxsize=4)
def _read_snapshot(snapshot_path):
    with Path(snapshot_path).open(encoding="utf-8") as source:
        results = json.load(source)
    if not isinstance(results, list):
        raise ValueError("KG Catalog snapshot must contain a JSON list")
    return results


def _load_snapshot(snapshot_path=SNAPSHOT_PATH, announce=False):
    """Load the last complete KG Catalog snapshot."""
    try:
        results = _read_snapshot(str(Path(snapshot_path).resolve()))
        if announce:
            print(f"Loaded {len(results)} knowledge graphs from local KG Catalog snapshot")
        return results
    except FileNotFoundError:
        print(f"KG Catalog snapshot not found: {snapshot_path}")
    except (OSError, ValueError) as error:
        print(f"Could not load KG Catalog snapshot {snapshot_path}: {error}")
    return []


def getAllDatasetIDs(
    repo_url=f"{API}/repos/{OWNER}/{REPO}/git/trees/{BRANCH}?recursive=1",
    snapshot_path=SNAPSHOT_PATH,
):
    """Refresh KG Catalog metadata, falling back to the local snapshot."""

    headers = {
        "Accept": "application/vnd.github+json"
    }

    try:
        response = requests.get(repo_url, headers=headers, timeout=15)
        response.raise_for_status()
        tree = response.json()["tree"]
        metadata_paths = [
            item["path"]
            for item in tree
            if item.get("type") == "blob"
            and isinstance(item.get("path"), str)
            and item["path"].startswith(PREFIX)
            and item["path"].endswith("/metadata.yaml")
        ]
        results = []
        for path in metadata_paths:
            raw_url = (
                f"https://raw.githubusercontent.com/"
                f"{OWNER}/{REPO}/{BRANCH}/{path}"
            )
            metadata_response = requests.get(raw_url, headers=headers, timeout=15)
            metadata_response.raise_for_status()
            metadata = yaml.safe_load(metadata_response.text)
            if not isinstance(metadata, dict):
                raise ValueError(f"Invalid metadata document: {path}")
            results.append({
                "directory": path.removesuffix("/metadata.yaml"),
                "metadata": metadata,
            })
    except (requests.RequestException, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
        print(f"Could not refresh KG Catalog metadata ({error}); using local snapshot")
        return _load_snapshot(snapshot_path, announce=True)

    print(f"Found {len(results)} knowledge graphs")

    if results:
        print(f"Saving metadata to {snapshot_path}")
        try:
            with Path(snapshot_path).open("w", encoding="utf-8") as output:
                json.dump(
                    results,
                    output,
                    ensure_ascii=False,
                    indent=2,
                    default=json_default,
                )
            _read_snapshot.cache_clear()
        except OSError as error:
            print(f"Could not save KG Catalog snapshot: {error}")
    else:
        return _load_snapshot(snapshot_path, announce=True)

    return results

def getDatasetMetadata(idKG):
    metadata_list = _load_snapshot()
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"]
    return False

def getLocalDatasetMetadata(idKG):
    metadata_list = _load_snapshot()
    for item in metadata_list:
        if item["metadata"].get("id") == idKG:
            return item["metadata"]
    return False


def _local_metadata_for(metadata):
    if not isinstance(metadata, dict):
        return False
    idKG = metadata.get("id")
    if not isinstance(idKG, str) or not idKG:
        return False
    return getLocalDatasetMetadata(idKG)


def getDatasetName(metadata):
    local_metadata = _local_metadata_for(metadata)
    return local_metadata.get("title", False) if local_metadata else False

def getLicense(metadata):
    local_metadata = _local_metadata_for(metadata)
    return local_metadata.get("license", False) if local_metadata else False

def getAuthor(metadata):
    local_metadata = _local_metadata_for(metadata)
    if not local_metadata:
        return False
    maintainers = local_metadata.get("maintainers")
    if isinstance(maintainers, dict):
        maintainers = [maintainers]
    if not isinstance(maintainers, list):
        return False
    names = [
        maintainer.get("name").strip()
        for maintainer in maintainers
        if isinstance(maintainer, dict)
        and isinstance(maintainer.get("name"), str)
        and maintainer.get("name").strip()
    ]
    return ", ".join(names) if names else False

def getSource(metadata):
    local_metadata = _local_metadata_for(metadata)
    return local_metadata.get("homepage", False) if local_metadata else False

def getTriples(metadata):
    local_metadata = _local_metadata_for(metadata)
    return local_metadata.get("last-version-size", False) if local_metadata else False

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
    local_metadata = _local_metadata_for(metadata)
    return local_metadata.get("description", False) if local_metadata else False

def getLanguage(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    return metadata.get("language", False) if metadata else False

def getKeywords(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    keywords = metadata.get("keywords") if metadata else None
    return keywords if isinstance(keywords, list) else []

def getDOI(idKG):
    metadata = getLocalDatasetMetadata(idKG)
    return metadata.get("doi", False) if metadata else False
    
if __name__ == "__main__":
    metadata_list = getAllDatasetIDs()
    metadata = getLocalDatasetMetadata("dblp")
    title = getDatasetName(metadata)
    license = getLicense(metadata)
    print(f"Title for 'dblp': {title}")
    print(f"License for 'dblp': {license}")
    print(f"Metadata for 'dblp':")
    print(json.dumps(metadata, indent=2, ensure_ascii=False, default=json_default))
