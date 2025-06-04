from importlib import resources
import json
import requests
import utils
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#INPUT: DATASET ID TO LOOK FOR
#OUTPUT: FILE JSON WITH METADATA OF THE DATASET
def getDataPackage(idDataset):
    api_url = "https://old.datahub.io/dataset/%s/datapackage.json" %idDataset
    try:
        response = requests.get(api_url,verify=False)
        if response.status_code == 200:
            responseApi = response.json()
            return responseApi
        elif response.status_code == 404:
            print("Dataset not found on DataHub")
            return False
    except:
        print('Failed to connect to DataHub')
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
