import requests
import json
import os
abs_path = os.path.dirname(os.path.abspath(__file__))

def getAllDatasetIDs(snapshot_path=f'{abs_path}/CHeCLOUD.json'):
    dataset_ids = []
    url = 'http://isislab.it:12280/che-cloud/api/CHe_cloud_data/get_all'

    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            dataset_ids = [(el.get('identifier'), el.get('title')) for el in data]

            # Save snapshot
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return dataset_ids
        else:
            print(f"LOD Cloud responded with status {response.status_code}, loading local snapshot if available.")
    except Exception as e:
        print(f"LOD Cloud Connection failed: {e}")

    if os.path.exists(snapshot_path):
        print("Loading LOD Cloud data from local snapshot...")
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            dataset_ids = [(el.get('identifier'), el.get('title')) for el in data]
        return dataset_ids
    else:
        print("No local snapshot available.")
        return []

def getDatasetMetadata(idKG, snapshot=f'{abs_path}/CHeCLOUD.json'):
    url = f'http://isislab.it:12280/che-cloud/api/CHe_cloud_data/dataset_metadata/{str(idKG)}'
    try:
        response = requests.get(url,verify=False)    
        if response.status_code == 200:
            print("Connection to API successful and data recovered")
            response = response.json()
            return response
        else:
            print("Connection failed")
            print(f"LOD Cloud responded with status {response.status_code}, loading local snapshot if available.")
            with open(snapshot, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(idKG), False)
    except Exception as e:
        print('Connection failed')
        return False

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