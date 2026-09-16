import urllib.error
from SPARQLWrapper import SPARQLExceptions

import query
import utils
from QualityDimensions.base import MISSING_VALUE


class AmountOfData:
    def __init__(self,numTriplesM,numTriplesQ,numEntities,numProperty,entitiesRe):
        self.numTriplesM = numTriplesM
        self.numTriplesQ = numTriplesQ
        self.numEntities = numEntities
        self.numProperty = numProperty
        self.entitiesRe = entitiesRe
    
    def getAmountOfData(self):
        return f"-Amount of data\n   Number of triples (metadata):{self.numTriplesM}\n   Number of triples (query):{self.numTriplesQ}\n   Number of entities:{self.numEntities}\n   Number of entities counted with regex:{self.entitiesRe}\n   Number of property:{self.numProperty}\n"

    @classmethod
    def calculate(cls, context, triples_metadata, regex, all_triples):
        triples_query = count_triples(context)
        num_property = count_properties(context)
        num_entities, entities_regex = count_entities(context, regex, all_triples)

        return cls(triples_metadata, triples_query, num_entities, num_property, entities_regex), {
            "triples_query": triples_query,
            "num_property": num_property,
            "num_entities": num_entities,
            "entities_regex": entities_regex,
        }


def unavailable(triples_metadata, error_message=MISSING_VALUE):
    return AmountOfData(triples_metadata, error_message, error_message, error_message, error_message)


def count_triples(context):
    try:
        return context.timed(
            'Number of triples check',
            'Amount of data',
            lambda: query.getNumTripleQuery(context.access_url),
        )
    except urllib.error.HTTPError as response:
        context.warning(f'Error while counting the number of triples: {str(response)}')
    except (SPARQLExceptions.QueryBadFormed, SPARQLExceptions.EndPointInternalError) as response:
        context.warning(f'Error while counting the number of triples: {str(response)}')
    except Exception as error:
        context.warning(f'Error while counting the number of triples: {str(error)}')
    return MISSING_VALUE


def count_properties(context):
    try:
        return context.timed(
            'Number of property check',
            'Amount of data',
            lambda: query.numberOfProperty(context.access_url),
        )
    except Exception as error:
        context.warning(f'Amount of data | Number of properties | {str(error)}')
        return MISSING_VALUE


def count_entities(context, regex, all_triples):
    try:
        num_entities = query.getNumEntities(context.access_url)
    except Exception as error:
        context.warning(f'Amount of data | Scope | {str(error)}')
        num_entities = MISSING_VALUE

    entities_regex = _count_entities_with_regex_query(context, regex)
    if not isinstance(entities_regex, int) or entities_regex == 0:
        entities_regex = _count_entities_with_regex_in_triples(context, regex, all_triples)

    return num_entities, entities_regex


def _count_entities_with_regex_query(context, regex):
    try:
        if len(regex) > 0:
            entities_regex = 0
            for item in regex:
                entities_regex = entities_regex + query.getNumEntitiesRegex(context.access_url, item)
            return entities_regex

        context.warning('Amount of data | Scope | Insufficient data')
        return MISSING_VALUE
    except Exception as error:
        context.warning(f'Amount of data | Scope | {str(error)}')
        return MISSING_VALUE


def _count_entities_with_regex_in_triples(context, regex, all_triples):
    try:
        if isinstance(all_triples, list) and isinstance(regex, list) and len(regex) > 0:
            def calculate():
                entities_regex = 0
                for item in regex:
                    for triple in all_triples:
                        subject = triple.get('s')
                        value = subject.get('value')
                        if utils.checkString(item, value):
                            entities_regex = entities_regex + 1
                return f"{entities_regex} (out of {len(all_triples)} triples considered)"

            return context.timed(
                'Check the number of entities',
                'Amount of data',
                calculate,
            )

        context.warning('Amount of data | Scope | Insufficient data')
    except Exception as error:
        context.warning(f'Amount of data | Scope | {str(error)}')

    return MISSING_VALUE
