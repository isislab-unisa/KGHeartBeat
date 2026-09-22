from copy import deepcopy
import logging
from urllib.parse import urlsplit, urlunsplit

from rdf_formats import rdf_media_type
from API import DataHubAPI
from API import LODCloudAPI
from API.monitoring_requests import MonitoringRequests
from API import CHeCloudAPI
from API import KGCatalogAPI
from API import WikidataAPI
import utils


def _dataset_tuple(dataset):
    """Normalize the dataset shapes returned by the supported catalogues."""
    if isinstance(dataset, str):
        return (dataset, '') if dataset.strip() else None
    if isinstance(dataset, (tuple, list)) and dataset:
        dataset_id = dataset[0]
        title = dataset[1] if len(dataset) > 1 else ''
    elif isinstance(dataset, dict):
        metadata = dataset.get('metadata', dataset)
        if not isinstance(metadata, dict):
            return None
        dataset_id = metadata.get('id') or metadata.get('qid') or metadata.get('identifier')
        title = metadata.get('title') or metadata.get('name') or ''
    else:
        return None
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        return None
    return dataset_id.strip(), title.strip() if isinstance(title, str) else ''


def _canonical_resource_url(value):
    """Normalize harmless URL variations used by different catalogues."""
    if not isinstance(value, str) or not value.strip():
        return None
    value = value.strip()
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or '').lower()
    try:
        port = parsed.port
    except ValueError:
        return value
    if port is not None and not ((scheme == 'http' and port == 80)
                                 or (scheme == 'https' and port == 443)):
        hostname = f'{hostname}:{port}'
    if parsed.username:
        credentials = parsed.username
        if parsed.password:
            credentials += f':{parsed.password}'
        hostname = f'{credentials}@{hostname}'
    path = parsed.path.rstrip('/') or '/'
    return urlunsplit((scheme, hostname, path, parsed.query, ''))


def deduplicate_datasets(datasets, endpoint_getter=None, dump_getter=None):
    """Keep one KG for a shared ID, SPARQL endpoint, or RDF dump URL.

    Catalogue order defines precedence. Lookup failures do not remove a KG.
    Signatures from discarded entries are retained, allowing transitive matches
    (same endpoint as one entry and same dump as another) to collapse together.
    """
    endpoint_getter = endpoint_getter or getSPARQLEndpoint
    dump_getter = dump_getter or getRDFDumps
    unique = []
    known_signatures = set()

    for raw_dataset in datasets:
        dataset = _dataset_tuple(raw_dataset)
        if dataset is None:
            continue
        dataset_id, _ = dataset
        signatures = {('id', dataset_id.casefold())}
        try:
            endpoint = _canonical_resource_url(endpoint_getter(dataset_id))
            if endpoint:
                signatures.add(('sparql', endpoint))
        except Exception as error:
            logging.getLogger(__name__).warning(
                'Could not resolve a SPARQL endpoint for %s during deduplication: %s',
                dataset_id, error,
            )
        try:
            for dump in dump_getter(dataset_id) or []:
                url = dump[0] if isinstance(dump, (tuple, list)) and dump else dump
                url = _canonical_resource_url(url)
                if url:
                    signatures.add(('rdf_dump', url))
        except Exception as error:
            logging.getLogger(__name__).warning(
                'Could not resolve RDF dumps for %s during deduplication: %s',
                dataset_id, error,
            )

        is_duplicate = bool(signatures & known_signatures)
        known_signatures.update(signatures)
        if not is_duplicate:
            unique.append(dataset)

    return unique

def getDataPackage(idKG):
    metadataDH = DataHubAPI.getDataPackage(idKG)
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    monitoring_resources = MonitoringRequests()
    metadata_monitoring_resources = monitoring_resources.getMetadata(idKG)
    metadataCHeCloud = CHeCloudAPI.getDatasetMetadata(idKG)
    metadataKGCatalog = KGCatalogAPI.getDatasetMetadata(idKG)
    metadataWikidata = WikidataAPI.getDatasetMetadata(idKG)
    # Record catalog provenance separately from the dataset's publisher sources.
    # Monitoring requests take precedence even when another catalog has the KG.
    source = ('manually_added' if isinstance(metadata_monitoring_resources, dict)
              else 'checloud' if isinstance(metadataCHeCloud, dict)
              else 'lodcloud' if isinstance(metadataLODC, dict)
              else 'datahub' if isinstance(metadataDH, dict)
              else 'kgcatalog' if isinstance(metadataKGCatalog, dict)
              else 'wikidata' if isinstance(metadataWikidata, dict)
              else None)
    if isinstance(metadataCHeCloud,dict):
        return dict(metadataCHeCloud, _dataset_source=source)
    elif isinstance(metadata_monitoring_resources,dict):
        return dict(metadata_monitoring_resources, _dataset_source=source)
    elif isinstance(metadataLODC,dict):
        return dict(metadataLODC, _dataset_source=source)
    elif isinstance(metadataDH,dict):
        return dict(metadataDH, _dataset_source=source)
    elif isinstance(metadataKGCatalog,dict):
        return dict(metadataKGCatalog, _dataset_source=source)
    elif isinstance(metadataWikidata,dict):
        return dict(metadataWikidata, _dataset_source=source)
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
    nameKGCatalog = KGCatalogAPI.getDatasetName(metadata)
    nameWikidata = WikidataAPI.getNameKG(metadata)
    if nameKGCatalog != False:
        return nameKGCatalog
    if nameLODC != False:
        return nameLODC
    elif nameDH != False:
        return nameDH
    elif nameWikidata != False:
        return nameWikidata
    else:
        return False

def getLicense(metadata):
    licenseDH = DataHubAPI.getLicense(metadata)
    licenseLODC = LODCloudAPI.getLicense(metadata)
    licenseKGCatalog = KGCatalogAPI.getLicense(metadata)
    licenseWikidata = WikidataAPI.getLicense(metadata)
    if licenseLODC != False:
        return licenseLODC
    elif licenseDH != False:
        return licenseDH
    elif licenseKGCatalog != False:
        return licenseKGCatalog
    elif licenseWikidata != False:
        return licenseWikidata
    else:
        return False

def getAuthor(metadata):
    authorDH = DataHubAPI.getAuthor(metadata)
    authorLODC = LODCloudAPI.getAuthor(metadata)
    authorKGCatalog = KGCatalogAPI.getAuthor(metadata)
    authorWikidata = WikidataAPI.getAuthor(metadata)
    if authorLODC != False:
        return authorLODC
    elif authorDH != False:
        return authorDH
    elif authorKGCatalog != False:
        return authorKGCatalog
    elif authorWikidata != False:
        return authorWikidata
    else:
        return False

def getSource(metadata):
    sourcesDH = DataHubAPI.getSources(metadata)
    sourcesLODC = LODCloudAPI.getSourceDict(metadata)
    sourcesKGCatalog = KGCatalogAPI.getSource(metadata)
    sourcesWikidata = WikidataAPI.getSource(metadata)
    if sourcesLODC != False:
        return sourcesLODC
    elif sourcesDH != False:
        return sourcesDH
    elif sourcesKGCatalog != False:
        return sourcesKGCatalog
    elif sourcesWikidata != False:
        return sourcesWikidata
    else:
        return False

def getTriples(metadata):
    numTriplesDH = DataHubAPI.getTriples(metadata)
    numTriplesLODC = LODCloudAPI.getTriples(metadata)
    numTriplesKGCatalog = KGCatalogAPI.getTriples(metadata)
    numTriplesWikidata = WikidataAPI.getTriples(metadata)
    if numTriplesLODC != False:
        return numTriplesLODC
    elif numTriplesDH != False:
        return numTriplesDH
    elif numTriplesKGCatalog != False:
        return numTriplesKGCatalog
    elif numTriplesWikidata != False:
        return numTriplesWikidata
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
    endpointKGCatalog = KGCatalogAPI.getSPARQLEndpoint(idKG)
    endpointWikidata = WikidataAPI.getSPARQLEndpoint(idKG)
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
    if endpointKGCatalog != False:
        return endpointKGCatalog
    if endpointWikidata != False:
        return endpointWikidata
    else:
        return endpointDH

def getOtherResources(idKG):
    """Combine resources from every catalog, tolerating individual failures."""
    providers = [
        ('manual', lambda: utils.return_updated_rdf_dump(idKG)),
        ('monitoring_requests', lambda: MonitoringRequests().getOtherResources(idKG)),
        ('CHeCloud', lambda: CHeCloudAPI.getOtherResources(idKG)),
        ('KGCatalog', lambda: KGCatalogAPI.getOtherResources(idKG)),
        ('LODCloud', lambda: LODCloudAPI.getOtherResources(deepcopy(LODCloudAPI.getJSONMetadata(idKG)))),
        ('DataHub', lambda: DataHubAPI.getOtherResources(deepcopy(DataHubAPI.getDataPackage(idKG)))),
        ('Wikidata', lambda: WikidataAPI.getOtherResources(idKG)),
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
    linksKGCatalog = KGCatalogAPI.getExternalLinks(idKG)
    linksWikidata = WikidataAPI.getExternalLinks(idKG)
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
    elif isinstance(linksKGCatalog,list):
        for i in range(len(linksKGCatalog)):
            d = linksKGCatalog[i]
            key = d.get('target')
            value = d.get('value')
            linksDH[key] = value
        return linksDH
    elif isinstance(linksWikidata,list):
        for i in range(len(linksWikidata)):
            d = linksWikidata[i]
            key = d.get('target')
            value = d.get('value')
            linksDH[key] = value
        return linksDH
    else:
        return linksDH


def getDescription(metadata):
    descriptionDH = DataHubAPI.getDescription(metadata)
    descriptionLODC = LODCloudAPI.getDescription(metadata)
    descriptionKGCatalog = KGCatalogAPI.getDescription(metadata)
    descriptionWikidata = WikidataAPI.getDescription(metadata)
    if descriptionLODC != False:
        return descriptionLODC
    elif descriptionDH != False and not isinstance(descriptionDH,dict):
        return descriptionDH
    elif descriptionKGCatalog != False and not isinstance(descriptionKGCatalog,dict):
        return descriptionKGCatalog
    elif descriptionWikidata != False and not isinstance(descriptionWikidata,dict):
        return descriptionWikidata
    else:
        return False

def getExtrasLanguage(idKg):
    metadataDH = DataHubAPI.getDataPackage(idKg)
    metadataKGCatalog = KGCatalogAPI.getDatasetMetadata(idKg)
    if isinstance(metadataDH,dict):
        language = DataHubAPI.getExtrasLang(metadataDH)
        if isinstance(language,dict):
            return language
        else:
            return 'absent'
    elif isinstance(metadataKGCatalog,dict) == False:
        language = KGCatalogAPI.getLanguage(metadataKGCatalog)
        if language != False:
            return language
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
    keywordsKGCatalog = KGCatalogAPI.getKeywords(idKg)
    keywordsWikidata = WikidataAPI.getKeywords(idKg)
    keywords = keywordsDH + keywordsLODC + keywordsMR + keywordsCHeCloud + keywordsKGCatalog + keywordsWikidata
    return keywords

def getDOI(idKG):
    metadataLODC = LODCloudAPI.getJSONMetadata(idKG)
    doiLODC = LODCloudAPI.getDOI(metadataLODC)
    doiCHeCloud = CHeCloudAPI.getDOI(idKG)
    monitoring_resources = MonitoringRequests()
    doiMR = monitoring_resources.getDOI(idKG)
    doiKGCatalog = KGCatalogAPI.getDOI(idKG)
    doiWikidata = WikidataAPI.getDOI(idKG)
    print(f"DOI from LODC: {doiLODC}, CHeCloud: {doiCHeCloud}, MR: {doiMR}")
    if doiLODC != False and doiLODC != None:
        return doiLODC
    if doiMR != False and doiMR != None:
        return doiMR
    if doiCHeCloud != False and doiCHeCloud != None:
        return doiCHeCloud
    if doiKGCatalog != False and doiKGCatalog != None:
        return doiKGCatalog
    if doiWikidata != False and doiWikidata != None:
        return doiWikidata
    
    return False
