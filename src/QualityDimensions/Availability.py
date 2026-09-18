import requests

import query
import utils
from QualityDimensions.base import MISSING_VALUE


class Availability:
    def __init__(self,sparqlEndpoint,RDFDumpM,RDFDumpQ,inactiveLinks,uriDef):
        self.sparqlEndpoint = sparqlEndpoint
        self.RDFDumpM = RDFDumpM
        self.RDFDumpQ = RDFDumpQ
        self.inactiveLinks = inactiveLinks
        self.uriDef = uriDef
    
    def getAvailability(self):
        return f"-Availability\n   Sparql endpoint:{self.sparqlEndpoint}\n   Availability of RDF dump (metadata):{self.RDFDumpM}\n   Availability of RDF dump (query):{self.RDFDumpQ}\n   Inactive links:{self.inactiveLinks}\n   Uri deferenceability:{self.uriDef}\n"


def rdf_dump_from_endpoint(context, download_url, offline_dump):
    try:
        def calculate():
            available_dump = 'absent'
            url_list = query.checkDataDump(context.access_url)
            if isinstance(url_list, list):
                available_dump = utils.checkAvailabilityListResources(url_list)
                download_url.extend(utils.getActiveDumps(url_list))
                offline_dump.extend(utils.getInactiveDumps(url_list))
            return available_dump

        return context.timed('RDF dump link check', 'Availability', calculate)
    except Exception as error:
        context.warning(f'Availability | RDF dump| {str(error)}')
        return MISSING_VALUE


def uri_dereferenceability(context, all_triples):
    try:
        if context.triple_limit is not None:
            return context.timed('Check URIs Dereferenciability', 'Availability', lambda: _dereference_from_triples(context, all_triples))
        return context.timed('Check URIs Dereferenciability', 'Availability', lambda: _dereference_from_endpoint(context))
    except Exception:
        try:
            return context.timed('Check URIs Dereferenciability', 'Availability', lambda: _dereference_from_triples(context, all_triples))
        except Exception as error:
            context.warning(f'Availability | Derefereaceability of the URI | {str(error)}')
            return MISSING_VALUE


def _dereference_from_endpoint(context):
    def_count = 0
    uri_count = 0
    uris = query.getUris(context.access_url)
    for uri in uris:
        if utils.validateURI(uri):
            uri_count = uri_count + 1
            try:
                response = requests.get(uri, headers={"Accept": "application/rdf+xml"}, stream=True, timeout=2)
                if response.status_code == 200:
                    def_count = def_count + 1
            except Exception:
                continue
    if uri_count > 0:
        return def_count / uri_count
    context.warning('Availability | Derefereaceability of the URI | No URIs retrieved from the endpoint')
    return MISSING_VALUE


def _dereference_from_triples(context, all_triples):
    uri_count = 0
    def_count = 0
    if not isinstance(all_triples, list):
        return MISSING_VALUE
    uris = dict.fromkeys(triple['s']['value'] for triple in all_triples if triple['s']['type'] == 'uri')
    for value in list(uris)[:10]:
        if utils.validateURI(value):
            uri_count = uri_count + 1
            try:
                with requests.get(value, headers={"Accept": "application/rdf+xml"}, stream=True, timeout=2) as response:
                    if response.status_code == 200:
                        def_count = def_count + 1
            except Exception:
                continue
    if uri_count > 0:
        return def_count / uri_count
    context.warning('Availability | Derefereaceability of the URI | No URIs retrieved from the endpoint')
    return MISSING_VALUE
