from API import DataHubAPI
from API import LODCloudAPI
import utils

def getDataPackage(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    if isinstance(metadataLODC,dict):
        return metadataLODC
    elif isinstance(metadataDH,dict):
        return metadataDH
    else:
        return False

def getNameKG(metadata):
    nameDH = DataHubAPI.getNameKG(metadata)
    nameLODC = LODCloudAPI.getNameKG(metadata)
    if nameLODC != False:
        return nameLODC
    elif nameDH != False:
        return nameDH
    else:
        return False

def getLicense(metadata):
    licenseDH = DataHubAPI.getLicense(metadata)
    licenseLODC = LODCloudAPI.getLicense(metadata)
    if licenseLODC != False:
        return licenseLODC
    elif licenseDH != False:
        return licenseDH
    else:
        return False

def getAuthor(metadata):
    authorDH = DataHubAPI.getAuthor(metadata)
    authorLODC = LODCloudAPI.getAuthor(metadata)
    if authorLODC != False:
        return authorLODC
    elif authorDH != False:
        return authorDH
    else:
        return False

def getSource(metadata):
    sourcesDH = DataHubAPI.getSources(metadata)
    sourcesLODC = LODCloudAPI.getSourceDict(metadata)
    if sourcesLODC != False:
        return sourcesLODC
    elif sourcesDH != False:
        return sourcesDH
    else:
        return False

def getTriples(metadata):
    numTriplesDH = DataHubAPI.getTriples(metadata)
    numTriplesLODC = LODCloudAPI.getTriples(metadata)
    if numTriplesLODC != False:
        return numTriplesLODC
    elif numTriplesDH != False:
        return numTriplesDH
    else:
        return False

def getSPARQLEndpoint(idKG):
    endpoint = utils.return_updated_sparql_endpoint(idKG)
    if endpoint:
        return endpoint
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    metadataDH = DataHubAPI.getDataPackage(idKG)
    endpointLODC = LODCloudAPI.getSPARQLEndpoint(metadataLODC)  
    endpointDH = DataHubAPI.getSPARQLEndpoint(metadataDH)
    if endpointLODC != False:
        if isinstance(endpointLODC,str):
            if endpointLODC != '':
                return endpointLODC
            else:
                return endpointDH
        else:
            return endpointDH
    else:
        return endpointDH

def getOtherResources(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    otResourcesDH = DataHubAPI.getOtherResources(metadataDH)
    otResourcesLODC = LODCloudAPI.getOtherResources(metadataLODC)
    manual_refined_resources = utils.return_updated_rdf_dump(idKG)
    if otResourcesDH == False:
        otResourcesDH = []
    if otResourcesLODC == False:
        otResourcesLODC = []
    otherResources = utils.mergeResources(otResourcesDH,otResourcesLODC)
    if manual_refined_resources != False:
        otherResources + manual_refined_resources
    
    return otherResources

def getExternalLinks(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    linksDH = DataHubAPI.getExternalLinks(metadataDH)
    if linksDH == False or linksDH is None:
        linksDH = {}   #BECAUSE IS USED TO CLEAN THE RESULTS FROM LODCLOUD (IN CASE DATAHUB NOT HAVE EXTERNAL LINKS)
    linksLODC = LODCloudAPI.getExternalLinks(metadataLODC)
    if isinstance(linksLODC,list):
        for i in range(len(linksLODC)):
            d = linksLODC[i]
            key = d.get('target')
            value = d.get('value')
            linksDH[key] = value
        return linksDH
    else:
        return linksDH

def getDescription(metadata):
    descriptionDH = DataHubAPI.getDescription(metadata)
    descriptionLODC = LODCloudAPI.getDescription(metadata)
    if descriptionLODC != False:
        return descriptionLODC
    elif descriptionDH != False and not isinstance(descriptionDH,dict):
        return descriptionDH
    else:
        return False

def getExtrasLanguage(idKg):
    metadataDH = DataHubAPI.getDataPackage(idKg)
    if isinstance(metadataDH,dict):
        language = DataHubAPI.getExtrasLang(metadataDH)
        if isinstance(language,dict):
            return language
        else:
            return 'absent'
    else:
        return 'absent'

def getKeywords(idKg):
    metadataDH = DataHubAPI.getDataPackage(idKg)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKg)
    keywordsDH = DataHubAPI.getKeywords(metadataDH)
    keywordsLODC = LODCloudAPI.getKeywords(metadataLODC)
    keywords = keywordsDH + keywordsLODC
    return keywords
