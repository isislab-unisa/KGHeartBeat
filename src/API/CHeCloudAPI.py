import requests
import json
import os
from copy import deepcopy
from functools import lru_cache
from threading import Lock
abs_path = os.path.dirname(os.path.abspath(__file__))

# Once CHeCloud fails, keep this process on the local snapshot. This prevents
# one timeout per dataset from turning an analysis into hundreds of retries.
_service_offline = False
_service_lock = Lock()


def _load_catalog_snapshot(snapshot_path):
    if not os.path.exists(snapshot_path):
        print("No local snapshot available.")
        return []
    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            print("CHeCloud snapshot is not a dataset list.")
            return []
        print("Loading CHeCloud data from local snapshot...")
        return data
    except (OSError, ValueError) as e:
        print(f"Could not load CHeCloud snapshot: {e}")
        return []

def getAllDatasetIDs(snapshot_path=f'{abs_path}/CHeCLOUD.json'):
    global _service_offline
    url = 'https://checloud.di.unisa.it/checloud-api/CHe_cloud_data/get_all'

    with _service_lock:
        if not _service_offline:
            try:
                response = requests.get(url, verify=False, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    with open(snapshot_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    return [(el.get('identifier'), el.get('title')) for el in data]
                print(f"CHeCloud responded with status {response.status_code}; switching to local snapshot.")
            except Exception as e:
                print(f"CHeCloud connection failed: {e}; switching to local snapshot for this process.")
            _service_offline = True

    data = _load_catalog_snapshot(snapshot_path)
    return [(el.get('identifier'), el.get('title')) for el in data if isinstance(el, dict)]

@lru_cache(maxsize=1024)
def _get_dataset_metadata(idKG, snapshot):
    """Fetch each CHeCloud dataset at most once per process."""
    global _service_offline
    url = f'https://checloud.di.unisa.it/checloud-api/CHe_cloud_data/dataset_metadata/{str(idKG)}'

    def load_snapshot():
        try:
            with open(snapshot, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if not isinstance(data, list):
                print("CHeCloud snapshot is not a dataset list.")
                return False

            dataset_id = str(idKG)
            return next(
                (
                    dataset for dataset in data
                    if isinstance(dataset, dict)
                    and dataset_id in {
                        str(dataset.get('identifier', '')),
                        str(dataset.get('_id', '')),
                    }
                ),
                False,
            )
        except (OSError, ValueError) as e:
            print(f"Could not load CHeCloud snapshot: {e}")
            return False

    with _service_lock:
        if not _service_offline:
            try:
                response = requests.get(url, verify=False, timeout=10)
                if response.status_code == 200:
                    print("Connection to API successful and data recovered")
                    return response.json()
                print(
                    f"CHeCloud responded with status {response.status_code}; "
                    "switching to local snapshot."
                )
            except Exception as e:
                print(f"CHeCloud connection failed: {e}; switching to local snapshot for this process.")
            _service_offline = True
    return load_snapshot()


def clear_metadata_cache():
    """Force CHeCloud metadata to be refreshed on the next lookup."""
    _get_dataset_metadata.cache_clear()


def getDatasetMetadata(idKG, snapshot=f'{abs_path}/CHeCLOUD.json'):
    """Return a mutable copy while retaining one cached network response."""
    metadata = _get_dataset_metadata(str(idKG), os.path.abspath(snapshot))
    return deepcopy(metadata) if isinstance(metadata, dict) else metadata

def getSPARQLEndpoint(idKG):
    metadata = getDatasetMetadata(idKG)
    if isinstance(metadata,dict):
        listSparql = metadata.get('sparql')
        if isinstance(listSparql,list):
            if len(listSparql) >= 1:
                d = listSparql[0]
                url = d.get('access_url')
                return url
            else:
                return False
        else:
            return False
    else:
        return False

def getOtherResources(idKG):  
    metadata = getDatasetMetadata(idKG)
    if isinstance(metadata,dict):
        fullDownload = []
        example = []
        resources = []
        fullDownload = metadata.get('full_download')
        for i in range(len(fullDownload)):
            d = fullDownload[i]
            d['access_url'] = d.pop('download_url',None)  #RENAME THE KEY VALUE TO HAVE THE SAME NAME OF THE FIELD
            d['type'] = 'full_download'
        example = metadata.get('example')
        otherDownload = metadata.get('other_download')
        resources = example + otherDownload + fullDownload
        for i in range (len(resources)):   #DELETING UNNECESSARY ELEMENT FROM THE DICTIONARY 
            resources[i].pop('mirror',None)
            resources[i].pop('status',None)
            resources[i].pop('_id',None)
            d = resources[i]
            d['path'] = d['access_url']   #RENAME THE KEY VALUE TO HAVE THE SAME NAME OF THE FIELD IN THE DATAHUB METADATA
            del d['access_url']
            d['format'] = d.pop('media_type',None)
        return resources
    else:
        return False
    
def getExternalLinks(idKG):
    metadata = getDatasetMetadata(idKG)
    if isinstance(metadata,dict):
        links = metadata.get('links',0)
        if isinstance(links,list):
            return links
        else:
            return links
    else:
        return False
    
def getKeywords(idKG):
    metadata = getDatasetMetadata(idKG)
    if isinstance(metadata,dict):
        keywords = metadata.get('keywords')
        if isinstance(keywords,list):
            return keywords
        else:
            return []
    else:
        return []

def getDOI(idKG):
    metadata = getDatasetMetadata(idKG)
    if isinstance(metadata,dict):
        doi = metadata.get('doi')
        if doi != '':
            return doi
    else:
        return False
