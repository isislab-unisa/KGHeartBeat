from ExternalLink import ExternalLink
import Graph
import query
from QualityDimensions.base import MISSING_VALUE, decimal


class Interlinking:
    def __init__(self,degreeConnection,clustering,centrality,sameAs,externalLinks,skosMapping):
        self.degreeConnection = degreeConnection
        self.clustering = clustering
        self.centrality = centrality
        self.sameAs = sameAs
        self.externalLinks = externalLinks
        self.skosMapping = skosMapping
    
    def getInterlinking(self):
        return f"-Interlinking\n   Degree of connection:{self.degreeConnection}\n   Clustering coefficient:{self.clustering}\n   Centrality:{self.centrality}\n   Number of samAs chains:{self.sameAs}\n   External links:{ExternalLink.getListExLinks(self.externalLinks)}  Skos mapping:{self.externalLinks}\n"

    def to_dict(self):
        if not isinstance(self.degreeConnection,int):
            self.degreeConnection = "Can't retrieve this information, missing metadata"
        return  {
            "Degree-of-connection" : self.degreeConnection,
            "Clustering" : self.clustering,
            "Centrality" : self.centrality,
            "sameAs" : self.sameAs,
            "External-Links": ExternalLink.getListExLinks(self.externalLinks),
            "Skos-mapping": self.skosMapping
        }


def graph_metrics(context, graph, kg_id):
    degree = context.timed(
        'Calculation of Degree of Connection',
        'Interlinking',
        lambda: Graph.getDegreeOfConnection(graph, kg_id),
    )
    centrality = context.timed(
        'Calculation of Centrality',
        'Interlinking',
        lambda: Graph.getCentrality(graph, kg_id),
    )
    if isinstance(centrality, float):
        centrality = decimal(centrality, 3)

    clustering = context.timed(
        'Calculation of Clustering coefficient',
        'Interlinking',
        lambda: Graph.getClusteringCoefficient(graph, kg_id),
    )
    if isinstance(clustering, float):
        clustering = decimal(clustering, 3)

    return degree, centrality, clustering


def same_as_chains(context):
    try:
        return context.timed('sameAs chians check', 'Interlinking', lambda: query.getSameAsChains(context.access_url))
    except Exception as error:
        context.warning(f'Interlinking | sameAs chains | {str(error)}')
        return MISSING_VALUE


def skos_mapping(context):
    try:
        return context.timed('skos check', 'Interlinking', lambda: query.getSkosMapping(context.access_url))
    except Exception as error:
        context.warning(f'Interlinking | SKOS Mapping properties | {str(error)}')
        return MISSING_VALUE
