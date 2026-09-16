import urllib.error
from SPARQLWrapper import SPARQLExceptions

import query
import utils
from QualityDimensions.base import MISSING_VALUE


class Versatility:
    def __init__(self,languagesQ,languagesM,serializationFormats,sparqlEndpoint,availabilityDownloadQ,availabilityDownloadM):
        self.languagesQ = languagesQ
        self.languagesM = languagesM
        self.serializationFormats = serializationFormats
        self.sparqlEndpoint = sparqlEndpoint
        self.availabilityDownloadQ = availabilityDownloadQ
        self.availabilityDownloadM = availabilityDownloadM
    
    def getVersatility(self):
        return f"-Versatility\n   Languages (query):{self.languagesQ}\n   Languages (metadata):{self.languagesM}\n   Serialization formats:{self.serializationFormats}\n   Sparql endpoint:{self.sparqlEndpoint}\n   Availability for download (query):{self.availabilityDownloadQ}\n   Availability for download (metadata):{self.availabilityDownloadM}\n"


def languages_from_endpoint(context):
    try:
        return context.timed(
            'Languages check',
            'Versatility',
            lambda: query.getLangugeSupported(context.access_url),
        )
    except urllib.error.HTTPError as response:
        return response
    except (SPARQLExceptions.QueryBadFormed, SPARQLExceptions.EndPointNotFound):
        context.warning('Versatility | Languages | Query not supported or endpoint not found')
    except Exception as error:
        context.warning(f'Versatility | Languages | {str(error)}')
    return MISSING_VALUE


def serialization_formats_from_endpoint(context):
    try:
        formats = context.timed(
            'Serialization formats check',
            'Versatility',
            lambda: query.checkSerialisationFormat(context.access_url),
        )
        if isinstance(formats, list) and len(formats) > 0:
            return utils.save_only_unique_values(formats)
        return formats
    except Exception as error:
        context.warning(f'Versatility | Serialization formats | {str(error)}')
        return MISSING_VALUE


def dcat_download_links(context):
    links = []
    try:
        other_download_links = query.get_download_link(context.access_url)
        for link in other_download_links:
            if utils.checkAvailabilityResource(link):
                links.append(link)
    except Exception:
        context.warning('Versatility | Languages | Download links, error during query with the dcat:downloadURL predicate')
    return links
