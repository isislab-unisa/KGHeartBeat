import requests
import json

def getAllDatasetIDs():
    dataset_ids = []
    url = 'http://isislab.it:12280/che-cloud/api/CHe_cloud_data/get_all'
    try:
        response = requests.get(url,verify=False)    
        if response.status_code == 200:
            print("Connection to API successful and data recovered")
            response = response.json()
            for el in response:
                dataset_ids.append((el.get('identifier'),el.get('title')))
            return dataset_ids
        else:
            print("Connection failed")
            return False
    except:
        print('Connection failed')
        return False

def getDatasetMetadata(idKG):
    url = f'http://isislab.it:12280/che-cloud/api/CHe_cloud_data/dataset_metadata/{str(idKG)}'
    try:
        response = requests.get(url,verify=False)    
        if response.status_code == 200:
            print("Connection to API successful and data recovered")
            response = response.json()
            return response
        else:
            print("Connection failed")
            return False
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
        return keywords
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