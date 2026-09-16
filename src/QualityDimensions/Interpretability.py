from rdflib import RDF
import urllib.error
from SPARQLWrapper import SPARQLExceptions

import query
from QualityDimensions.base import MISSING_VALUE


class Interpretability:
    def __init__(self,numBN,RDFStructures):
        self.numBN = numBN
        self.RDFStructures = RDFStructures

    def getInterpretability(self):
        return f"-Interpretability:\n   Number of blank nodes:{self.numBN}\n   Uses RDF structures:{self.RDFStructures}\n"


def blank_nodes(context):
    try:
        return context.timed('Number of blank nodes check', 'Interpretability', lambda: query.numBlankNode(context.access_url))
    except urllib.error.HTTPError:
        context.warning('Interpretability | Number of blank nodes | HTTP error')
    except (SPARQLExceptions.QueryBadFormed, SPARQLExceptions.EndPointInternalError) as response:
        context.warning(f'Interpretability | Number of blank nodes | {str(response)}')
    except Exception as error:
        context.warning(f'Interpretability | Number of blank nodes | {str(error)}')
    return MISSING_VALUE
