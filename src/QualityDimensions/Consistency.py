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


def collect_metrics(context, all_triples):
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
    misplaced_class = _ratio_or_message(context, metrics["misplaced_class"], triples_query, 'Consistecy | Misplaced classes or properties | Unable to retrieve classes from the endpoint')
    undefined_class = _ratio_or_message(context, metrics["undefined_classes"], triples_query, 'Consistecy | Invalid usage of undefined classes and properties | Unable to retrieve classes from the endpoint')
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


def _misplaced_classes(context, all_triples):
    try:
        def calculate():
            misplaced = []
            properties = query.getAllProperty(context.access_url)
            found = False
            if isinstance(all_triples, list) and isinstance(properties, list):
                properties.sort()
                for triple in all_triples:
                    value_o = triple.get('o').get('value')
                    value_s = triple.get('s').get('value')
                    if utils.validateURI(value_s):
                        if utils.binarySearch(properties, 0, len(properties) - 1, value_s) != -1:
                            found = True
                    if not found and utils.validateURI(value_o):
                        if utils.binarySearch(properties, 0, len(properties) - 1, value_o) != -1:
                            found = True
                    if found:
                        misplaced.append(value_s)
                        found = False
            else:
                context.warning('Consistency | Misplaced classes | Impossible to recover all information to calculate this metric')
                misplaced = MISSING_VALUE
            return properties, misplaced

        return context.timed('Misplaced classes', 'Consistency', calculate)
    except TimeoutError as error:
        context.warning(f'Consistency | Misplaced classes | {str(error)}')
    except Exception as error:
        context.warning(f'Consistency | Misplaced classes | {str(error)}')
    return [], MISSING_VALUE


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
        return [], MISSING_VALUE


def _undefined_classes(context, all_triples, all_type):
    try:
        def calculate():
            to_search = []
            found = False
            for triple in all_triples:
                subject = triple.get('s').get('value')
                all_type.sort()
                if utils.binarySearch(all_type, 0, len(all_type) - 1, subject) != -1:
                    found = True
                    break
                if not found and utils.validateURI(subject):
                    to_search.append(subject)
                found = False
            return LOVAPI.searchTermsList(to_search)

        return context.timed('Check Invalid usage of undefined classes', 'Consistency', calculate)
    except Exception as error:
        context.warning(f'Consistency | Invalid usage of undefined classes and properties | {str(error)}')
        return MISSING_VALUE


def _undefined_properties(context, properties):
    try:
        def calculate():
            to_search = []
            found = False
            for predicate in query.getAllPredicate(context.access_url):
                properties.sort()
                if utils.binarySearch(properties, 0, len(properties) - 1, predicate) != -1:
                    found = True
                    break
                if not found and utils.validateURI(predicate):
                    to_search.append(predicate)
                found = False
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
        return 1.0 - (len(value) / triples_query)
    context.warning(warning)
    return MISSING_VALUE
