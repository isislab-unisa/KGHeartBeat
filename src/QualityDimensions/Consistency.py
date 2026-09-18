from collections import Counter

import query
import utils
from API import LOVAPI
from QualityDimensions.base import MISSING_VALUE


class Consistency:
    def __init__(self,deprecated,disjointClasses,triplesMP,triplesMC,oHijacking,undefinedClass,undefinedProperties):
        self.deprecated = deprecated
        self.disjointClasses = disjointClasses
        self.triplesMP = triplesMP 
        self.triplesMC = triplesMC
        self.oHijacking = oHijacking
        self.undefinedClass = undefinedClass
        self.undefinedProperties = undefinedProperties

    def getConsistency(self):
        return f"-Consistency\n   Deprecated classes/properties used:{self.deprecated}\n   Entities as member of disjoint class:{self.disjointClasses}\n   Triples with misplaced property problem:{self.triplesMP}\n   Triples with misplaced class problem:{self.triplesMC}\n   Ontology Hijacking problem:{self.oHijacking}\n   Undefined class used without declaration:{self.undefinedClass}\n   Undefined properties used without declaration:{self.undefinedProperties}\n"


def collect_metrics(context, all_triples=None):
    """Prefer endpoint queries; reuse retrieved triples when a query fails."""
    metrics = {
        "deprecated": _deprecated(context),
        "num_disjoint": _num_disjoint(context),
        "classes": [],
        "properties": [],
        "misplaced_property": MISSING_VALUE,
        "misplaced_class": MISSING_VALUE,
        "hijacking": MISSING_VALUE,
        "undefined_classes": MISSING_VALUE,
        "undefined_properties": MISSING_VALUE,
    }
    metrics["classes"], metrics["misplaced_property"] = _misplaced_properties(context)
    metrics["properties"], metrics["misplaced_class"] = _misplaced_classes(context, all_triples)
    metrics["all_type"], metrics["hijacking"] = _ontology_hijacking(context)
    metrics["undefined_classes"] = _undefined_classes(context, all_triples, metrics["all_type"])
    metrics["undefined_properties"] = _undefined_properties(context, metrics["properties"])
    return metrics


def build(context, metrics, triples_query, num_entities, entities_regex):
    deprecated = metrics["deprecated"]
    classes = metrics["classes"]
    properties = metrics["properties"]
    num_disjoint = metrics["num_disjoint"]

    disjoint_value = _disjoint_value(context, num_disjoint, num_entities, entities_regex)
    deprecated_value = _deprecated_value(context, deprecated, classes, properties)
    misplaced_property = _ratio_or_message(context, metrics["misplaced_property"], triples_query, 'Consistecy | Misplaced classes or properties | Unable to retrieve properties from the endpoint')
    misplaced_total = context.query_fallbacks.get('consistency.triplesMC', {}).get('triples', triples_query)
    undefined_total = context.query_fallbacks.get('consistency.undefinedClass', {}).get('triples', triples_query)
    misplaced_class = _ratio_or_message(context, metrics["misplaced_class"], misplaced_total, 'Consistecy | Misplaced classes or properties | Unable to retrieve classes from the endpoint')
    undefined_class = _ratio_or_message(context, metrics["undefined_classes"], undefined_total, 'Consistecy | Invalid usage of undefined classes and properties | Unable to retrieve classes from the endpoint')
    undefined_property = _ratio_or_message(context, metrics["undefined_properties"], triples_query, 'Consistecy | Invalid usage of undefined classes and properties | Unable to retrieve properties from the endpoint')

    return Consistency(
        deprecated_value,
        disjoint_value,
        misplaced_property,
        misplaced_class,
        metrics["hijacking"],
        undefined_class,
        undefined_property,
    )


def unavailable(error_message=MISSING_VALUE):
    return Consistency(error_message, error_message, error_message, error_message, error_message, error_message, error_message)


def _deprecated(context):
    try:
        return context.timed('Deprecated classes/propertiers check', 'Consistency', lambda: query.getDeprecated(context.access_url))
    except Exception as error:
        context.warning(f'Consistency| Use of members of deprecated classes or properties| {str(error)}')
        return MISSING_VALUE


def _num_disjoint(context):
    try:
        return context.timed('Disjoint class check', 'Consistency', lambda: query.getDisjoint(context.access_url))
    except Exception as error:
        context.warning(f'Consistency | Entities as members of disjoint classes | {str(error)}')
        return MISSING_VALUE


def _misplaced_properties(context):
    try:
        def calculate():
            misplaced = []
            classes = query.getAllClasses(context.access_url)
            if isinstance(classes, list):
                classes.sort()
                for predicate in query.getAllPredicate(context.access_url):
                    if utils.validateURI(predicate):
                        if utils.binarySearch(classes, 0, len(classes) - 1, predicate) != -1:
                            misplaced.append(predicate)
            else:
                misplaced = 'insufficient data'
            return classes, misplaced

        return context.timed('Check Misplaced properties', 'Consistency', calculate)
    except Exception as error:
        context.warning(f'Consistency | Misplaced properties | {str(error)}')
        return [], MISSING_VALUE


def _misplaced_classes(context, all_triples=None):
    properties = None
    try:
        properties = query.getAllProperty(context.access_url)
        if not isinstance(properties, list):
            raise ValueError('Unable to retrieve declared properties')
        count = context.timed('Misplaced classes', 'Consistency',
                              lambda: query.getMisplacedClassCount(context.access_url))
        if type(count) is not int or count < 0:
            raise ValueError('Invalid misplaced-class count')
        return properties, count
    except Exception as error:
        context.warning(f'Consistency | Misplaced-class query failed; using retrieved triples | {error}')
        if not isinstance(all_triples, list):
            return properties if isinstance(properties, list) else [], MISSING_VALUE
        declared = (set(properties) if isinstance(properties, list)
                    else _typed_subjects(all_triples, query.PROPERTY_TYPES))
        count = sum(any(row[position]['type'] == 'uri' and row[position]['value'] in declared
                        for position in ('s', 'o')) for row in all_triples)
        context.record_fallback('consistency.triplesMC', all_triples)
        # A partial local schema must not feed other checks as a complete schema.
        return properties if isinstance(properties, list) else MISSING_VALUE, count


def _ontology_hijacking(context):
    try:
        def calculate():
            all_type = query.getAllType(context.access_url)
            if isinstance(all_type, list):
                triples = LOVAPI.searchTermsList(all_type)
                return all_type, len(triples) > 0
            context.warning('Consistency | Ontology hijacking | Impossible to retrieve the terms defined in the dataset')
            return all_type, MISSING_VALUE

        return context.timed('Check Ontology hijacking', 'Consistency', calculate)
    except Exception as error:
        context.warning(f'Consistency | Ontology hijacking | {str(error)}')
        return MISSING_VALUE, MISSING_VALUE


def _undefined_classes(context, all_triples=None, all_type=None):
    try:
        def calculate():
            try:
                rows = query.getUntypedSubjectCounts(context.access_url)
                if not isinstance(rows, list):
                    raise ValueError('Invalid untyped-subject results')
                counts = {row['s']['value']: int(row['triples']['value']) for row in rows
                          if utils.validateURI(row['s']['value'])}
                if any(count < 0 for count in counts.values()):
                    raise ValueError('Invalid untyped-subject count')
            except Exception as error:
                context.warning(f'Consistency | Undefined-class query failed; using retrieved triples | {error}')
                if not isinstance(all_triples, list):
                    return MISSING_VALUE
                defined = set(all_type) if isinstance(all_type, list) else _typed_subjects(all_triples)
                counts = Counter(row['s']['value'] for row in all_triples
                                 if row['s']['value'] not in defined and utils.validateURI(row['s']['value']))
                context.record_fallback('consistency.undefinedClass', all_triples)
            unknown = LOVAPI.searchTermsList(list(counts))
            if not isinstance(unknown, list):
                return MISSING_VALUE
            return sum(counts[subject] for subject in unknown)

        return context.timed('Check Invalid usage of undefined classes', 'Consistency', calculate)
    except Exception as error:
        context.warning(f'Consistency | Invalid usage of undefined classes and properties | {error}')
        return MISSING_VALUE


def _typed_subjects(triples, types=None):
    """Read declarations from the retrieved triples if schema queries also fail."""
    return {row['s']['value'] for row in triples
            if row['p']['value'] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
            and (types is None or row['o']['value'] in types)}


def _undefined_properties(context, properties):
    try:
        def calculate():
            if not isinstance(properties, list):
                return MISSING_VALUE
            declared = set(properties)
            to_search = [predicate for predicate in query.getAllPredicate(context.access_url)
                         if predicate not in declared and utils.validateURI(predicate)]
            return LOVAPI.searchTermsList(to_search)

        return context.timed('Check Invalid usage of undefined properties', 'Consistency', calculate)
    except Exception as error:
        context.warning(f'Consistency | Invalid usage of undefined classes and properties | {str(error)}')
        return MISSING_VALUE


def _disjoint_value(context, num_disjoint, num_entities, entities_regex):
    if not isinstance(num_disjoint, int):
        return 'insufficient data'
    for value in [num_entities, entities_regex]:
        try:
            value = int(value)
            if value > 0 and value > num_disjoint:
                return num_disjoint / value
        except Exception:
            continue
    context.warning("Consistency | Entities as members of disjoint classes | Insufficent data to compute the metric")
    return MISSING_VALUE


def _deprecated_value(context, deprecated, classes, properties):
    if isinstance(classes, list) and isinstance(properties, list) and len(classes) + len(properties) > 0:
        if isinstance(deprecated, list):
            return 1.0 - (len(deprecated) / (len(classes) + len(properties)))
        return 'insufficient data'
    context.warning("Consistecy | Use of members of deprecated classes or properties | Insufficient data")
    return MISSING_VALUE


def _ratio_or_message(context, value, triples_query, warning):
    if not isinstance(triples_query, int) or triples_query <= 0:
        return 'insufficient data'
    if isinstance(value, list):
        value = len(value)
    if type(value) is int and 0 <= value <= triples_query:
        return 1.0 - (value / triples_query)
    context.warning(warning)
    return MISSING_VALUE
