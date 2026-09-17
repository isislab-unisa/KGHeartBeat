from copy import deepcopy
import logging
from urllib.parse import urlsplit

from rdf_formats import rdf_media_type
from API import DataHubAPI
from API import LODCloudAPI
from API.monitoring_requests import MonitoringRequests
from API import CHeCloudAPI
import utils

def getDataPackage(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    monitoring_resources = MonitoringRequests()
    metadata_monitoring_resources = monitoring_resources.getMetadata(idKG)
    metadataCHeCloud = CHeCloudAPI.getDatasetMetadata(idKG)
    if isinstance(metadataCHeCloud,dict):
        return metadataCHeCloud
    elif isinstance(metadata_monitoring_resources,dict):
        return metadata_monitoring_resources
    elif isinstance(metadataLODC,dict):
        return metadataLODC
    elif isinstance(metadataDH,dict):
        return metadataDH
    else:
        return False

def check_if_on_lodc_dh(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    if isinstance(metadataLODC,dict):
        return True
    elif isinstance(metadataDH,dict):
        return True
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
    monitoring_resources = MonitoringRequests()
    endpointMR = monitoring_resources.getSPARQLEndpoint(idKG)
    endpointLODC = LODCloudAPI.getSPARQLEndpoint(metadataLODC)  
    endpointDH = DataHubAPI.getSPARQLEndpoint(metadataDH)
    endpointCHeCloud = CHeCloudAPI.getSPARQLEndpoint(idKG)
    if endpointMR != False:
        return endpointMR
    if endpointCHeCloud != False and endpointCHeCloud != '':
        return endpointCHeCloud
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
    """Combine resources from every catalog, tolerating individual failures."""
    providers = [
        ('manual', lambda: utils.return_updated_rdf_dump(idKG)),
        ('monitoring_requests', lambda: MonitoringRequests().getOtherResources(idKG)),
        ('CHeCloud', lambda: CHeCloudAPI.getOtherResources(idKG)),
        ('LODCloud', lambda: LODCloudAPI.getOtherResources(deepcopy(LODCloudAPI.getJSONMetadata(idKG)))),
        ('DataHub', lambda: DataHubAPI.getOtherResources(deepcopy(DataHubAPI.getDataPackage(idKG)))),
    ]
    resources = {}
    for catalog, fetch in providers:
        try:
            entries = fetch()
        except Exception as error:
            logging.getLogger(__name__).warning('Could not recover %s resources for %s: %s', catalog, idKG, error)
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            resource = deepcopy(entry)
            url = (resource.get('path') or resource.get('url')
                   or resource.get('download_url') or resource.get('access_url'))
            if not isinstance(url, str) or not url.strip():
                continue
            url = url.strip()
            resource['path'] = url
            resource['format'] = (resource.get('format') or resource.get('media_type')
                                  or resource.get('mimetype'))
            resource['catalogs'] = [catalog]
            if url not in resources:
                resources[url] = resource
            else:
                previous = resources[url]
                previous['catalogs'].append(catalog)
                if resource.get('type') == 'full_download':
                    previous['type'] = 'full_download'
                if not rdf_media_type(url, previous.get('format')) and rdf_media_type(url, resource.get('format')):
                    previous['format'] = resource['format']
    return list(resources.values())


def getRDFDumps(idKG, resources=None):
    """Return ordered (URL, RDF media type) candidates across supported catalogs.

    Discovery does not download files, probe availability, or require Oxigraph.
    Pass previously fetched resources to avoid repeating catalog requests.
    """
    if resources is None:
        resources = getOtherResources(idKG)
    candidates = []
    for resource in resources:
        url = resource.get('path')
        if not isinstance(url, str) or urlsplit(url).scheme not in ('http', 'https'):
            continue
        kind = resource.get('type')
        if kind in ('sparql', 'example'):
            continue
        media_type = rdf_media_type(url, resource.get('format'))
        if kind == 'full_download' or media_type:
            candidates.append((url, media_type, kind == 'full_download'))
    candidates.sort(key=lambda item: not item[2])
    seen = set()
    result = []
    for url, media_type, _ in candidates:
        if url not in seen:
            seen.add(url)
            result.append((url, media_type))
    return result


def getExternalLinks(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    linksDH = DataHubAPI.getExternalLinks(metadataDH)
    if linksDH == False or linksDH is None:
        linksDH = {}   #BECAUSE IS USED TO CLEAN THE RESULTS FROM LODCLOUD (IN CASE DATAHUB NOT HAVE EXTERNAL LINKS)
    linksLODC = LODCloudAPI.getExternalLinks(metadataLODC)
    linksCHeCloud = CHeCloudAPI.getExternalLinks(idKG)
    monitoring_requests = MonitoringRequests()
    linksMR = monitoring_requests.getExternalLinks(idKG)
    if isinstance(linksLODC,list):
        for i in range(len(linksLODC)):
            d = linksLODC[i]
            key = d.get('target')
            value = d.get('value')
            linksDH[key] = value
        return linksDH
    elif isinstance(linksMR,list):
        for i in range(len(linksMR)):
            d = linksMR[i]
            key = d.get('target')
            value = d.get('value')
            linksDH[key] = value
        return linksDH
    elif isinstance(linksCHeCloud,list):
        for i in range(len(linksCHeCloud)):
            d = linksCHeCloud[i]
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
    keywordsCHeCloud = CHeCloudAPI.getKeywords(idKg)
    monitoring_resources = MonitoringRequests()
    keywordsMR = monitoring_resources.getKeywords(idKg)
    keywords = keywordsDH + keywordsLODC + keywordsMR + keywordsCHeCloud
    return keywords

def getDOI(idKG):
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    doiLODC = LODCloudAPI.getDOI(metadataLODC)
    doiCHeCloud = CHeCloudAPI.getDOI(idKG)
    monitoring_resources = MonitoringRequests()
    doiMR = monitoring_resources.getDOI(idKG)
    print(f"DOI from LODC: {doiLODC}, CHeCloud: {doiCHeCloud}, MR: {doiMR}")
    if doiLODC != False and doiLODC != None:
        return doiLODC
    if doiMR != False and doiMR != None:
        return doiMR
    if doiCHeCloud != False and doiCHeCloud != None:
        return doiCHeCloud
    
    return False