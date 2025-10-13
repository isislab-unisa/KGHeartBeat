from importlib import resources
import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os

#INPUT: DATASET ID TO LOOK FOR
#OUTPUT: FILE JSON WITH METADATA OF THE DATASET
def getDataPackage(idDataset, pages=12, rows=1000, snapshot='./datahub.json'):
    datasets = []
    start = 0
    base_url = "https://old.datahub.io/api/3/action/package_search"

    for i in range(pages):
        params = {"rows": rows, "start": start}
        try:
            response = requests.get(base_url, params=params, timeout=15)
            if response.status_code == 200:
                print(f"Request {i+1}/{pages} successful — start={start}")
                data = response.json()
                currentDS = data.get("result", {}).get("results", [])
                datasets.extend(currentDS)
            else:
                print(f"DataHub Request {i+1} failed with status {response.status_code}")
        except Exception as e:
            print(f"DataHub Request {i+1} failed: {e}")
        start += rows

    if os.path.exists(snapshot) and len(datasets) == 0:
        print(f"Loading metadata for '{idDataset}' from local snapshot...")
        with open(snapshot, 'r', encoding='utf-8') as f:
            datasets = json.load(f)
    elif len(datasets) > 0:
        with open(snapshot, 'w', encoding='utf-8') as f:
            json.dump(datasets, f, ensure_ascii=False, indent=2)

    # Search for dataset with matching field
    for ds in datasets:
        if ds.get('name') == idDataset:
            return ds
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
        if isinstance(license,dict):
            licenseTitle = license.get('title')
            type = license.get('type')
            licenseStr = '%s - %s -'%(licenseTitle,type)
            return licenseStr
        else:
            return False
    else:
        return False

def getSources(jsonFile):
    if isinstance(jsonFile,dict):
        sources = jsonFile.get('sources',False)
        if isinstance(sources,list):
            return sources[0]
        else:
            return False
    else:
        return False


def getAuthor(jsonFile):
    if isinstance(jsonFile,dict):
        author = jsonFile.get('author')
        if isinstance(author,dict):
            authorName = author.get('name')
            authorEmail = author.get('email')
            authorStr = 'Name: %s, Email:%s'%(authorName,authorEmail)
            return authorStr
        else:
            return False
    else:
        return False

def getOtherResources(jsonFile):
    if isinstance(jsonFile,dict):
        resources = []
        resources = jsonFile.get('resources')
        if isinstance(resources,list):
            for i in range(len(resources)):  #DELETING UNNECESSARY ELEMENT FROM THE DICTIONARY 
                resources[i].pop('name',None)
                resources[i].pop('hash',None)
            return resources
        else:
            return False
    else: 
        return False

def getSPARQLEndpoint(jsonFile):
    if isinstance(jsonFile,dict):
        resources = jsonFile.get('resources')
        if isinstance(resources,list):
            for i in range(len(resources)):
                d = resources[i]
                format = d.get('format','')
                name = d.get('name','')
                if format == 'api/sparql' or 'sparql' in name:
                    url = d.get('path',False)
                    return url
            return False
        else:
            return False
    else:
        return False

def checkRDFDump(jsonFile):
    if isinstance(jsonFile,dict):
        resources = jsonFile.get('resources')
        if isinstance(resources,list):
            for i in range(len(resources)):
                format = resources[i].get('format')
                if format =='ZIP' or format == 'RAR:RDF' or format == 'RDF':
                    return True
        else:
            return False
    else:
        return False

def getTriples(jsonFile):
    if isinstance(jsonFile,dict):
        extras = jsonFile.get('extras')
        if isinstance(extras,dict):
            triples = extras.get('triples',0)
            return triples
        else:
            return False
    else:
        return False

def getExternalLinks(jsonFile):
    if isinstance(jsonFile,dict):
        extras = {}
        extras = jsonFile.get('extras')
        if isinstance(extras,dict):
            extras = {i:extras[i] for i in extras if'links:' in i} #CLEAN THE DICTIONARY FROM OTHER ENTRY THAT ISN'T LINKS
            for i in extras.copy().keys():
                try:
                    extras[i.removeprefix('links:')] = extras.pop(i,None) #REMOVING THE PREFIX LINK
                except:
                    continue
            return extras
    else:
        return False

def getDescription(jsonFile):
    if isinstance(jsonFile,dict):
        description = jsonFile.get('description','absent')
        return description
    else:
        return False

def getExtrasLang(jsonFile):
    extras = jsonFile.get('extras')
    if isinstance(extras,dict):
        extras = {i:extras[i] for i in extras if'language' in i}
        return extras
    else:
        return False

def getKeywords(jsonFile):
    if isinstance(jsonFile,dict):
        keywords = jsonFile.get('keywords')
        if isinstance(keywords,list):
            return keywords
        else:
            return []
    else:
        return []