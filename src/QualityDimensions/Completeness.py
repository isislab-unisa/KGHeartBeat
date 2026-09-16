import re

import utils
from API import Aggregator


class Completeness:
    def __init__(self,numTriples,numTriplesL,interlinkingC):
        self.numTriples = numTriples
        self.numTriplesL = numTriplesL
        self.interlinkingC = interlinkingC
    
    def getCompleteness(self):
        return f"-Completeness\n   Number of triples:{self.numTriples}\n   Number of triples linked:{self.numTriplesL}\n   Interlinking completeness:{self.interlinkingC}%\n"


def external_links_info(context, kg_id):
    def calculate():
        external_links = Aggregator.getExternalLinks(kg_id)
        external_link_objects = utils.toObjectExternalLinks(external_links)
        linked_triples = 0
        for link in external_link_objects:
            value = re.sub(r"[^\d\.]", "", str(link.value))
            try:
                linked_triples = linked_triples + int(value)
            except Exception:
                continue
        return external_link_objects, linked_triples

    return context.timed('Calculation of interlinking completeness', 'Completeness', calculate)


def build(triples_query, triples_metadata, linked_triples):
    if isinstance(triples_query, int) and isinstance(linked_triples, int) and triples_query > 0 and triples_query >= linked_triples:
        return Completeness(triples_query, linked_triples, f"{(linked_triples / triples_query):.2f}")
    if isinstance(triples_metadata, int) and isinstance(linked_triples, int) and triples_metadata > 0 and triples_metadata >= linked_triples:
        return Completeness(triples_metadata, linked_triples, f"{(linked_triples / triples_metadata):.2f}")
    if isinstance(triples_query, int):
        return Completeness(triples_query, linked_triples, "insufficient data")
    return Completeness(triples_metadata, linked_triples, 0)
