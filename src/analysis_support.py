import json
import logging
import os
import socket
import time
import urllib
from dataclasses import dataclass
from xml.dom.minidom import Document
from xml.parsers import expat

import networkx as nx
from SPARQLWrapper import SPARQLExceptions
from urllib.error import HTTPError, URLError

import query
import utils
import VoIDAnalyses
from API import Aggregator
from QualityDimensions.Extra import Extra
from Sources import Sources


@dataclass
class Target:
    kg_id: str
    name: str
    metadata: dict
    access_url: str


@dataclass
class EndpointCheck:
    access_url: str
    endpoint: str
    available: bool
    absent: bool
    restricted: bool


@dataclass
class ResourceInfo:
    resources: list
    objects: list
    metadata_media_type: list
    available_download: object
    download_urls: list
    offline_dumps: list


@dataclass
class VoidInfo:
    url: object
    status: str
    available: bool


@dataclass
class MetadataFallback:
    vocabularies: object
    creation_date: object
    modification_date: object
    available_dump: object
    license_mr: object
    num_entities: object
    frequency: object
    regex: object
    formats: object
    languages: object


def resolve_target(kg_id=None, name=None, sparql_endpoint=None):
    if kg_id:
        metadata = Aggregator.getDataPackage(kg_id)
        if name == '':
            name = Aggregator.getNameKG(metadata)
        access_url = Aggregator.getSPARQLEndpoint(kg_id)
    elif sparql_endpoint:
        access_url = sparql_endpoint
        kg_id = sparql_endpoint
        try:
            name = query.get_kg_name(access_url)
        except Exception:
            name = ''
        metadata = None
    else:
        metadata = None
        access_url = False

    if name == '' or name is False:
        name = sparql_endpoint

    return Target(kg_id, name, metadata, access_url)


def configure_logger(analysis_date, kg_id, kg_name):
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(kg_id)s | %(kg_name)s | %(message)s',
        defaults={'kg_id': '-', 'kg_name': '-'},
    )
    logging.basicConfig(level=logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.handlers[0].setFormatter(formatter)

    logger = logging.getLogger('KG analysis')
    logger.setLevel(logging.DEBUG)

    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here, '../Analysis results')
    save_path = os.path.join(save_path, analysis_date + ".log")
    file_handler = logging.FileHandler(save_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    logger.addHandler(file_handler)

    kg_info = {"kg_id": f"{kg_id}", "kg_name": f"{kg_name}"}
    return logger, kg_info


def check_endpoint(access_url, context, sources=None):
    start = time.time()
    absent = False
    restricted = False
    endpoint = ''
    available = False

    if access_url is False:
        endpoint = '-'
        context.warning('SPARQL endpoint missing in the metadata')
        absent = True
    else:
        endpoint, available, access_url, restricted = _try_endpoint(access_url, context)

    if not available and not absent:
        endpoint, available, access_url, restricted = _try_redirect(access_url, endpoint, restricted, context)

    if not available and not absent and sources is not None and sources.web != 'absent':
        endpoint, available, access_url, restricted = _try_dataset_sparql(access_url, endpoint, sources, restricted, context)

    context.write_time(time.time() - start, 'SPARQL endpoint availability check', 'Availability')
    return EndpointCheck(access_url, endpoint, available, absent, restricted)


def load_sources(metadata, access_url):
    sources = Aggregator.getSource(metadata)
    if sources is False:
        sources_obj = Sources('absent', 'absent', 'absent')
    else:
        sources_obj = Sources(sources.get('web', 'Absent'), sources.get('name', 'Absent'), sources.get('email', 'Absent'))

    if sources_obj.web == 'Absent':
        try:
            kg_uri = query.get_kg_url(access_url)
            if kg_uri:
                sources_obj.web = kg_uri
        except Exception:
            sources_obj.web = 'Absent'

    return sources, sources_obj


def load_resources(kg_id):
    resources = Aggregator.getOtherResources(kg_id)
    resources = utils.insertAvailability(resources)
    available_download = utils.checkAvailabilityForDownload(resources)
    download_urls = utils.getLinkDownload(resources)
    offline_dumps = utils.getLinkOfflineDump(resources)
    objects = utils.toObjectResources(resources)
    metadata_media_type = utils.extract_media_type(resources)
    return ResourceInfo(resources, objects, metadata_media_type, available_download, download_urls, offline_dumps)


def check_void(context, resources, sources):
    start = time.time()
    url = utils.getUrlVoID(resources)
    void_available = False
    status = 'VoID file absent'

    if utils.is_valid_void_url(url):
        if isinstance(url, str):
            void_available, status = _parse_void_url(url)

        if not void_available and not isinstance(url, str) and sources.web not in ['absent', 'Absent']:
            url = sources.web + '/.well-known/void'
            void_available, status = _parse_void_url(url, absent_on_url_error=True)
            if void_available:
                context.logger.info(f"VoID file link: {url}", extra=context.kg_info)

        if not isinstance(url, str):
            status = 'VoID file absent'

    context.logger.info(f"VoID file link: {url}", extra=context.kg_info)
    context.write_time(time.time() - start, 'VoID file availability check', 'Availability')
    return VoidInfo(url, status, void_available)


def endpoint_unavailable_message(context, restricted, is_html, absent):
    if restricted:
        context.warning('Availability | Accessibility of the SPARQL endpoint | Restricted access to the endpoint, only metrics that can ben calculated with the metadata will be computed')
        return '-', ''
    if is_html:
        context.warning("Availability | Accessibility of the SPARQL endpoint | The result format from the SPARQL endpoint aren't structured data, only metrics that can ben calculated with the metadata will be computed")
        return 'Warning the result of endpoint is HTML', None
    if absent:
        context.warning("Availability | Accessibility of the SPARQL endpoint | No SPARQL endpoint indicated, only metrics that can ben calculated with the metadata will be computed")
        return '-', None

    context.warning("Availability | Accessibility of the SPARQL endpoint | SPARQL endpoint offline, only metrics that can ben calculated with the metadata will be computed")
    return '-', None


def parse_void_fallback(void_info):
    if not void_info.available:
        return False, None

    for parser in [VoIDAnalyses.parseVoID, VoIDAnalyses.parseVoIDTtl]:
        try:
            void_file = parser(void_info.url)
            if void_file is not None:
                return True, MetadataFallback(
                    vocabularies=_unique(VoIDAnalyses.getVocabularies(void_file)),
                    creation_date=VoIDAnalyses.getCreationDate(void_file),
                    modification_date=VoIDAnalyses.getModificationDate(void_file),
                    available_dump=VoIDAnalyses.getDataDump(void_file),
                    license_mr=VoIDAnalyses.getLicense(void_file),
                    num_entities=VoIDAnalyses.getNumEntities(void_file),
                    frequency=_frequency(VoIDAnalyses.getFrequency(void_file)),
                    regex=_regex(VoIDAnalyses.getUriRegex(void_file)),
                    formats=_formats(VoIDAnalyses.getSerializationFormats(void_file)),
                    languages=VoIDAnalyses.getLanguage(void_file),
                )
        except Exception:
            continue

    return False, None


def inactive_links(resources):
    return any(resource.status == 'offline' for resource in resources)


def has_example(resources):
    for resource in resources:
        if isinstance(resource.format, str) and 'example' in resource.format:
            return True
        if isinstance(resource.title, str) and 'example' in resource.title:
            return True
    return False


def metadata_language(context, kg_id):
    try:
        return Aggregator.getExtrasLanguage(kg_id)
    except Exception as error:
        context.warning(f"Versatility | Usage of multiple languages | {str(error)}")
        return '-'


def common_formats_availability(available_download, available_dump, metadata_media_type):
    if available_download == 1 or available_dump is True:
        return utils.check_common_acceppted_format(metadata_media_type)
    return 'No dump available'


def metadata_triples(metadata):
    triples = Aggregator.getTriples(metadata)
    try:
        return int(triples)
    except (TypeError, ValueError):
        return 0


def recover_all_triples(context):
    try:
        return context.timed('Recovery of all triples', 'Extra', lambda: query.getAllTriplesSPO(context.access_url))
    except Exception as error:
        context.warning(f'Impossible to recover all the triples in the KG: {error}')
        return '-'


def endpoint_limited(context, all_triples, triples_query):
    if isinstance(all_triples, list) and isinstance(triples_query, int):
        if len(all_triples) < triples_query:
            context.warning('The number of triples that can be retrieved from the sparql endpoint is limited')
            return True
        return False
    return 'impossible to verify'


def type_objects(context):
    try:
        return query.getAllTypeO(context.access_url)
    except Exception as error:
        context.warning(f'Representational-consistency | Reuse of terms | {str(error)}')
        return '-'


def load_graph():
    here = os.path.dirname(os.path.abspath(__file__))
    graph_file = os.path.join(here, 'GraphOfKG.gpickle')
    return nx.read_gpickle(graph_file)


def build_extra_available(
    context,
    kg_id,
    access_url,
    download_urls,
    dcat_links,
    num_triples_updated,
    classes,
    properties,
    all_uri,
    triples_o,
    all_triples,
    und_properties,
    und_classes,
    misplaced_class,
    misplaced_property,
    deprecated,
    limited,
    offline_dump,
    void_info,
    throughput_no_offset,
    metadata_media_type,
    common_formats,
    resources,
):
    download_urls = download_urls + dcat_links
    uri_list_s = []
    if isinstance(all_triples, list):
        for triple in all_triples:
            if len(all_triples) > 0:
                uri_list_s.append(triple.get('s').get('value'))
    else:
        context.warning("Currency | Update history | Insufficient data to compute this metric")

    update_value = num_triples_updated if isinstance(num_triples_updated, int) else '-'
    if update_value == '-':
        context.warning("Currency | Update history | Insufficient data to compute this metric")

    return Extra(
        kg_id,
        access_url,
        download_urls,
        update_value,
        classes,
        properties,
        all_uri,
        triples_o,
        uri_list_s,
        und_properties,
        und_classes,
        misplaced_class,
        misplaced_property,
        deprecated,
        0,
        limited,
        offline_dump,
        void_info.url,
        void_info.status,
        throughput_no_offset["min"],
        throughput_no_offset["average"],
        throughput_no_offset["max"],
        throughput_no_offset["standard_deviation"],
        0,
        None,
        metadata_media_type,
        common_formats,
        resources,
    )


def build_extra_unavailable(
    context,
    kg_id,
    access_url,
    download_urls,
    error_message,
    offline_dump,
    void_info,
    metadata_media_type,
    common_formats,
    resources,
):
    context.warning("Currency | Update history | Insufficient data to compute this metric")
    return Extra(
        kg_id,
        access_url,
        download_urls,
        '-',
        [],
        [],
        0,
        [],
        0,
        error_message,
        error_message,
        error_message,
        error_message,
        error_message,
        0,
        error_message,
        offline_dump,
        void_info.url,
        void_info.status,
        error_message,
        error_message,
        error_message,
        error_message,
        0,
        None,
        metadata_media_type,
        common_formats,
        resources,
    )


def _try_endpoint(access_url, context):
    endpoint = '-'
    available = False
    restricted = False
    try:
        result = query.checkEndPoint(access_url)
        if isinstance(result, bytes):
            new_url = utils.checkRedirect(access_url)
            result = query.checkEndPoint(new_url)
            if isinstance(result, bytes):
                context.warning('The result from the SPARQL endpoint is not structured data (HTML data returned)')
            else:
                endpoint = 'Available'
                available = True
                access_url = new_url
        else:
            endpoint = 'Available'
            available = True
    except (HTTPError, URLError, SPARQLExceptions.EndPointNotFound, socket.gaierror) as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except SPARQLExceptions.EndPointInternalError as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except (json.JSONDecodeError, SPARQLExceptions.QueryBadFormed, expat.ExpatError) as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except SPARQLExceptions.Unauthorized as response:
        endpoint = 'Restricted access to the endpoint'
        restricted = True
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except Exception as error:
        endpoint = 'offline'
        context.warning('Availability | SPARQL endpoint availability | ' + str(error))
    return endpoint, available, access_url, restricted


def _try_redirect(access_url, endpoint, restricted, context):
    available = False
    try:
        new_url = utils.checkRedirect(access_url)
        if new_url != access_url:
            result = query.checkEndPoint(new_url)
            if isinstance(result, Document) or isinstance(result, dict):
                return 'Available', True, new_url, restricted
    except (HTTPError, URLError, SPARQLExceptions.EndPointNotFound, socket.gaierror) as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except SPARQLExceptions.EndPointInternalError as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
        endpoint = '-'
    except (json.JSONDecodeError, SPARQLExceptions.QueryBadFormed, expat.ExpatError) as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
        endpoint = '-'
    except SPARQLExceptions.Unauthorized as response:
        endpoint = 'restricted access to the endpoint'
        restricted = True
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except Exception as error:
        endpoint = 'offline'
        context.warning('Availability | SPARQL endpoint availability | ' + str(error))
    return endpoint, available, access_url, restricted


def _try_dataset_sparql(access_url, endpoint, sources, restricted, context):
    available = False
    try:
        new_url = sources.web + '/sparql'
        result = query.checkEndPoint(new_url)
        if isinstance(result, Document) or isinstance(result, dict):
            context.logger.info(f"SPARQL endpoint link: {new_url}", extra=context.kg_info)
            return 'Available', True, new_url, restricted
    except (HTTPError, URLError, SPARQLExceptions.EndPointNotFound, socket.gaierror) as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
        endpoint = '-'
    except SPARQLExceptions.EndPointInternalError as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
        endpoint = '-'
    except (json.JSONDecodeError, SPARQLExceptions.QueryBadFormed, expat.ExpatError) as response:
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
        endpoint = '-'
    except SPARQLExceptions.Unauthorized as response:
        endpoint = 'Restricted access to the endpoint'
        restricted = True
        context.warning('Availability | SPARQL endpoint availability | ' + str(response))
    except Exception as error:
        endpoint = 'offline'
        context.warning('Availability | SPARQL endpoint availability | ' + str(error))
    return endpoint, available, access_url, restricted


def _parse_void_url(url, absent_on_url_error=False):
    try:
        VoIDAnalyses.parseVoID(url)
        return True, 'VoID file available'
    except Exception:
        try:
            VoIDAnalyses.parseVoIDTtl(url)
            return True, 'VoID file available'
        except urllib.error.HTTPError as error:
            if absent_on_url_error and error.code == 404:
                return False, 'VoID file absent'
            return False, 'VoID file offline'
        except urllib.error.URLError:
            if absent_on_url_error:
                return False, 'VoID file absent'
            return False, 'VoID file offline'
        except Exception:
            return False, 'VoID file offline'


def _unique(values):
    if isinstance(values, list) and len(values) > 0:
        return utils.save_only_unique_values(values)
    return values


def _frequency(values):
    if isinstance(values, list) and len(values) > 0:
        return utils.save_only_frequency(values)
    return values


def _regex(values):
    if isinstance(values, list) and len(values) > 0:
        return utils.save_only_regex(values)
    return values


def _formats(values):
    if isinstance(values, list) and len(values) > 0:
        return utils.save_only_formats(values)
    return values
