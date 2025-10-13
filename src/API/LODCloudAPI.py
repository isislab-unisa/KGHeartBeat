import json
from urllib import response
import requests
import utils
import itertools
import urllib3
import os
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
abs_path = os.path.dirname(os.path.abspath(__file__))

def getJSONMetadata(idKG, snapshot= f'{abs_path}/lodcloud.json'):
    """
    Retrieve JSON metadata for a given Knowledge Graph (KG) from the LOD Cloud.
    Falls back to a local snapshot if the online source is unavailable.
    """
    url = f'https://lod-cloud.net/versions/latest/lod-data.json'

    try:
        response = requests.get(url, verify=False, timeout=10)
        if response.status_code == 200:
            jsonMetadata = response.json()

            with open(snapshot, 'w', encoding='utf-8') as f:
                json.dump(jsonMetadata, f, ensure_ascii=False, indent=2)

            return jsonMetadata.get(idKG, False)
        else:
            print(f"LOD Cloud responded with status {response.status_code}, loading local snapshot if available.")
    except Exception as e:
        print(f"Failed to connect to LOD Cloud: {e}")

    # Fallback: load local snapshot
    if os.path.exists(snapshot):
        print(f"Loading metadata for '{idKG}' from local snapshot...")
        with open(snapshot, 'r', encoding='utf-8') as f:
            jsonMetadata = json.load(f)
            return jsonMetadata.get(idKG, False)
    else:
        print(f"No local snapshot found for '{idKG}'.")
        return False

def getNameKG(metadata):
    if isinstance(metadata,dict):
        title = metadata.get('title')
        return title
    else:
        return False

def getLicense(jsonFile):
    if isinstance(jsonFile,dict):
        license = jsonFile.get('license')
        if (not license):
            return False
        else:
            return license
    else:
        return False

def getAuthor(jsonFile):
    if isinstance(jsonFile,dict):
        owner = jsonFile.get('owner')
        if isinstance(owner,dict):
            name = owner.get('name')
            if (not name):
                name = 'absent'    
            email = owner.get('email')
            if (not email):
                email = 'absent'
            ownerStr = 'Name: %s, email: %s'%(name,email)
            return ownerStr
        else:
            return False
    else:
        return False

def getSource(jsonFile):
    if isinstance(jsonFile,dict):
        website = jsonFile.get('website')
        if(not website):
            website = 'absent'
        contactPoint = jsonFile.get('contact_point')
        if isinstance(contactPoint,dict):
            contactPoint["web"] = website 
            name = contactPoint.get('name')
            email = contactPoint.get('email')
            if(not name):
                name = 'absent'
            if(not email):
                email = 'absent'
            return contactPoint
        else:
            return False
    else:
        return False

        
def getSourceDict(jsonFile):
    if isinstance(jsonFile,dict):
        website = jsonFile.get('website')
        if(not website):
            website = 'absent'
        contactPoint = jsonFile.get('contact_point')
        if isinstance(contactPoint,dict):
            contactPoint["web"] = website 
            return contactPoint
        else:
            return False
    else:
        return False

def getOtherResources(jsonFile):  
    if isinstance(jsonFile,dict):
        fullDownload = []
        example = []
        resources = []
        fullDownload = jsonFile.get('full_download')
        for i in range(len(fullDownload)):
            d = fullDownload[i]
            d['access_url'] = d.pop('download_url',None)  #RENAME THE KEY VALUE TO HAVE THE SAME NAME OF THE FIELD
            d['type'] = 'full_download'
        example = jsonFile.get('example')
        otherDownload = jsonFile.get('other_download')
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

def getTriples(jsonFile):
    if isinstance(jsonFile,dict):
        triples = jsonFile.get('triples',0)
        return triples
    else:
        return False

def getSPARQLEndpoint(jsonFile):
    if isinstance(jsonFile,dict):
        listSparql = jsonFile.get('sparql')
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

def getExternalLinks(jsonFile):
    if isinstance(jsonFile,dict):
        links = jsonFile.get('links',0)
        if isinstance(links,list):
            return links
        else:
            return links
    else:
        return False

def getDescription(jsonFile):
    if isinstance(jsonFile,dict):
        en = jsonFile.get('description','absent')
        if isinstance(en,dict):
            description = en.get('en','absent')
            return description
        else:
            return 'absent'
    else:
        return False

def getKeywords(jsonfile):
    if isinstance(jsonfile,dict):
        keywords = jsonfile.get('keywords')
        if isinstance(keywords,list):
            return keywords
        else:
            return []
    else:
        return []

def getDOI(jsonfile):
    if isinstance(jsonfile,dict):
        doi = jsonfile.get('doi')
        if doi != '':
            return doi
    else:
        return False