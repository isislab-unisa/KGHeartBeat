import subprocess
import time
import requests
import os
import zipfile
import gzip
import shutil

GRAPHDB_CONTAINER_NAME = "graphdb"
GRAPHDB_IMAGE = "ontotext/graphdb:10.3.3"
REPO_ID = "myrepo"
REPO_TITLE = "My Repository"
GRAPHDB_PORT = 7200
DATA_DIR = "./data"
GRAPHDB_ADDRESS = "host.docker.internal"


def download_rdf(url):
    """Download RDF file (supports .zip or .gz) and extract if needed."""
    os.makedirs(DATA_DIR, exist_ok=True)
    local_file = os.path.join(DATA_DIR, url.split("/")[-1])
    print(f"Downloading {url} ...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_file, "wb") as f:
            shutil.copyfileobj(r.raw, f)

    # Handle extraction
    if local_file.endswith(".zip"):
        with zipfile.ZipFile(local_file, 'r') as zip_ref:
            zip_ref.extractall(DATA_DIR)
            # assume the first file is the RDF
            extracted_files = zip_ref.namelist()
            rdf_file = os.path.join(DATA_DIR, extracted_files[0])
        print(f"Extracted {rdf_file} from zip.")
    elif local_file.endswith(".gz"):
        rdf_file = local_file.rstrip(".gz")
        with gzip.open(local_file, "rb") as f_in:
            with open(rdf_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        print(f"Extracted {rdf_file} from gz.")
    else:
        rdf_file = local_file

    return rdf_file, local_file


def start_graphdb():
    """Start GraphDB Docker container."""
    subprocess.run([
        "docker", "run", "-d",
        "--name", GRAPHDB_CONTAINER_NAME,
        "-p", f"{GRAPHDB_PORT}:7200",
        "-v", f"{os.path.abspath('./graphdb-data')}:/opt/graphdb/home",
        "-v", f"{os.path.abspath(DATA_DIR)}:/data",
        "-e", "GDB_HEAP_SIZE=4g",
        GRAPHDB_IMAGE
    ])
    print("Waiting for GraphDB to start...")
    wait_for_graphdb()


def wait_for_graphdb(max_attempts=30, delay=2):
    """Wait for GraphDB to be ready by checking the health endpoint."""
    url = f"http://{GRAPHDB_ADDRESS}:{GRAPHDB_PORT}/rest/repositories"
    for i in range(max_attempts):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                print("GraphDB is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Waiting for GraphDB... (attempt {i+1}/{max_attempts})")
        time.sleep(delay)
    raise Exception("GraphDB did not start in time")


def create_repository():
    """Create a repository in GraphDB."""
    # Use host.docker.internal since we're in a devcontainer
    url = f"http://{GRAPHDB_ADDRESS}:{GRAPHDB_PORT}/rest/repositories"
    
    # Complete payload format for GraphDB 10.x with all required parameters
    payload = {
        "id": REPO_ID,
        "title": REPO_TITLE,
        "type": "graphdb",
        "params": {
            "ruleset": {
                "label": "Ruleset",
                "name": "ruleset",
                "value": "owl-horst-optimized"
            },
            "baseURL": {
                "label": "Base URL",
                "name": "baseURL",
                "value": f"http://example.org/graphdb#{REPO_ID}"
            },
            "defaultNS": {
                "label": "Default namespaces for imports(';' delimited)",
                "name": "defaultNS",
                "value": ""
            },
            "imports": {
                "label": "Imported RDF files(';' delimited)",
                "name": "imports",
                "value": ""
            },
            "repositoryType": {
                "label": "Repository type",
                "name": "repositoryType",
                "value": "file-repository"
            },
            "id": {
                "label": "Repository ID",
                "name": "id",
                "value": REPO_ID
            },
            "title": {
                "label": "Repository title",
                "name": "title",
                "value": REPO_TITLE
            }
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"Repository creation status code: {r.status_code}")
        print(f"Response: {r.text}")
        
        if r.status_code not in (200, 201):
            raise Exception(f"Failed to create repository. Status: {r.status_code}, Response: {r.text}")
        
        print(f"Repository '{REPO_ID}' created successfully.")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to GraphDB: {e}")


def load_rdf_dump(rdf_file):
    """Load RDF dump into the repository with chunked upload for large files."""
    url = f"http://host.docker.internal:{GRAPHDB_PORT}/repositories/{REPO_ID}/statements"
    
    # Determine content type based on file extension
    content_type = "application/n-triples"
    if rdf_file.endswith(".ttl"):
        content_type = "text/turtle"
    elif rdf_file.endswith(".rdf") or rdf_file.endswith(".xml"):
        content_type = "application/rdf+xml"
    elif rdf_file.endswith(".jsonld"):
        content_type = "application/ld+json"
    
    file_size = os.path.getsize(rdf_file)
    print(f"Loading RDF file: {rdf_file} (size: {file_size / (1024*1024):.2f} MB)")
    
    # For very large files, use streaming upload with no timeout on read
    # but keep connection timeout
    try:
        with open(rdf_file, "rb") as f:
            print("Uploading data to GraphDB (this may take a while)...")
            r = requests.post(
                url, 
                data=f, 
                headers={"Content-Type": content_type},
                timeout=(30, None)  # 30s connection timeout, no read timeout
            )
        
        if r.status_code not in (200, 204):
            print(f"Error response: {r.text}")
            raise Exception(f"Failed to load RDF dump. Status: {r.status_code}")
        
        print(f"RDF dump '{rdf_file}' loaded successfully into repository.")
        
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Connection error while loading RDF: {e}")
    except requests.exceptions.Timeout as e:
        raise Exception(f"Connection timeout while loading RDF: {e}")


def delete_repository():
    """Delete the repository from GraphDB."""
    url = f"http://{GRAPHDB_ADDRESS}:{GRAPHDB_PORT}/rest/repositories/{REPO_ID}"
    try:
        r = requests.delete(url, timeout=30)
        print(f"Repository deletion status code: {r.status_code}")
        
        if r.status_code in (200, 204):
            print(f"Repository '{REPO_ID}' deleted successfully.")
        else:
            print(f"Response: {r.text}")
            raise Exception(f"Failed to delete repository. Status: {r.status_code}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to GraphDB: {e}")

def cleanup_all(rdf_file=None, archive_file=None):
    """Delete all files in data folder and remove repository from GraphDB."""
    print("\n--- Starting cleanup ---")
    
    # Delete repository from GraphDB
    try:
        delete_repository()
    except Exception as e:
        print(f"Warning: Could not delete repository: {e}")
    
    # Delete all files in data folder
    if os.path.exists(DATA_DIR):
        for filename in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed directory {file_path}")
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
        
        # Optionally remove the data directory itself
        try:
            os.rmdir(DATA_DIR)
            print(f"Removed directory {DATA_DIR}")
        except Exception as e:
            print(f"Could not remove {DATA_DIR}: {e}")
    else:
        print(f"Data directory {DATA_DIR} does not exist")
    
    print("--- Cleanup complete ---")

def get_sparql_endpoint():
    return f"http://{GRAPHDB_ADDRESS}:{GRAPHDB_PORT}/repositories/{REPO_ID}"


if __name__ == "__main__":
    cleanup_all()
    rdf_url = "http://sonika-malik.github.io/super-ontology/sup_proton.xml"

    # 1. Download and extract RDF
    rdf_file, archive_file = download_rdf(rdf_url)

    # 2. Start GraphDB (uncomment if not already running)
    # start_graphdb()
    
    # If GraphDB is already running, just wait for it to be ready
    wait_for_graphdb()

    # 3. Create repository
    create_repository()

    # 4. Load RDF dump
    load_rdf_dump(rdf_file)

    # 5. Get SPARQL endpoint
    endpoint = get_sparql_endpoint()
    print("SPARQL endpoint:", endpoint)

    # --- Example: query endpoint ---
    from SPARQLWrapper import SPARQLWrapper, JSON
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery("""
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX schema: <http://schema.org/>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX sioc: <http://rdfs.org/sioc/ns#>
    PREFIX exif: <http://www.w3.org/2003/12/exif/ns#>
    PREFIX dcmitype: <http://purl.org/dc/dcmitype/>

    SELECT DISTINCT ?o
    WHERE {
    VALUES ?prop {
        foaf:depiction dcterms:thumbnail foaf:img foaf:thumbnail schema:image schema:photo 
        schema:logo schema:thumbnail schema:thumbnailUrl foaf:image schema:contentUrl 
        dbo:thumbnail dbo:image sioc:avatar wdt:P18 <http://example.org/hasImage> exif:image dcmitype:Image
    }
    ?resource ?prop ?o .
    }
                    """)
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    print(results)

    cleanup_all()


    # remove_files(rdf_file, archive_file)