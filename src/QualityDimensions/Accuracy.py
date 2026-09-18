import query
import utils
from QualityDimensions.base import MISSING_VALUE


class Accuracy:
    def __init__(self,emptyAnn,wSA,malformedDataType,FPvalue,IFPvalue):
        self.emptyAnn = emptyAnn
        self.wSA = wSA
        self.malformedDataType = malformedDataType
        self.FPvalue = FPvalue
        self.IFPvalue = IFPvalue


    def getAccuracy(self):
        return f"-Accuracy\n   Triples with empty annotation problem:{self.emptyAnn}\n   Triples with white space in annotation(at the beginning or at the end):{self.wSA}\n   Triples with malformed data type literals problem:{self.malformedDataType}\n   Functional property with incosistent value:{self.FPvalue}\n   Invalid usage of inverse-functional properties:{self.IFPvalue}\n"


def calculate(context, all_triples, triples_query):
    fp_value = _functional_property_value(context, triples_query)
    ifp_value = _inverse_functional_property_value(context, triples_query)
    empty_annotation, white_space_annotation = _annotation_scores(context, all_triples)
    malformed_datatypes = _malformed_datatypes(context, all_triples)
    return Accuracy(empty_annotation, white_space_annotation, malformed_datatypes, fp_value, ifp_value)


def _functional_property_value(context, triples_query):
    try:
        def calculate_value():
            violations = []
            triples = query.getFP(context.access_url)
            for triple in triples:
                subject1 = triple.get('s').get('value')
                obj1 = triple.get('o').get('value')
                for other in triples:
                    subject2 = other.get('s').get('value')
                    obj2 = other.get('o').get('value')
                    if subject1 == subject2 and obj1 != obj2:
                        violations.append(triple)
            return 1.0 - (len(violations) / triples_query)

        return context.timed('Check Functional Property', 'Accuracy', calculate_value)
    except Exception as error:
        context.warning(f'Accuracy | Functional property violation | {str(error)}')
        return MISSING_VALUE


def _inverse_functional_property_value(context, triples_query):
    try:
        def calculate_value():
            violations = []
            triples = query.getIFP(context.access_url)
            for triple in triples:
                subject1 = triple.get('s').get('value')
                obj1 = triple.get('o').get('value')
                for other in triples:
                    subject2 = other.get('s').get('value')
                    obj2 = other.get('o').get('value')
                    if obj1 == obj2 and subject1 != subject2:
                        violations.append(triple)
            return 1.0 - (len(violations) / triples_query)

        return context.timed('Check Inverse Functional Property', 'Accuracy', calculate_value)
    except Exception as error:
        context.warning(f'Accuracy | Inverse functional property violation | {str(error)}')
        return MISSING_VALUE


def _annotation_scores(context, all_triples=None):
    try:
        counts = context.timed('Check annotation labels', 'Accuracy',
                               lambda: query.getLabelQualityCounts(context.access_url))
        if any(type(counts[key]) is not int or counts[key] < 0
               for key in ('total', 'empty', 'whitespace')):
            raise ValueError('Invalid annotation counts')
        if max(counts['empty'], counts['whitespace']) > counts['total']:
            raise ValueError('Annotation counts exceed the total')
    except Exception as error:
        context.warning(f'Accuracy | Annotation query failed; using retrieved triples | {error}')
        if not isinstance(all_triples, list):
            return MISSING_VALUE, MISSING_VALUE
        labels = [row['o'] for row in all_triples if row['p']['value'] in query.LABEL_PREDICATES]
        literals = [obj['value'] for obj in labels if obj['type'] in ('literal', 'typed-literal')]
        counts = {'total': len(labels), 'empty': sum(value == '' for value in literals),
                  'whitespace': sum(value != value.strip() for value in literals)}
        for metric in ('accuracy.emptyAnn', 'accuracy.wSA'):
            context.record_fallback(metric, all_triples, considered=len(labels))
    if counts['total'] > 0:
        return (1.0 - counts['empty'] / counts['total'],
                1.0 - counts['whitespace'] / counts['total'])
    return MISSING_VALUE, MISSING_VALUE


def _malformed_datatypes(context, all_triples):
    try:
        def calculate_value():
            malformed = []
            if isinstance(all_triples, list):
                for triple in all_triples:
                    obj = triple.get('o')
                    value = obj.get('value')
                    if not utils.validateURI(value):
                        data_type = obj.get('datatype')
                        if isinstance(data_type, str):
                            data_type_regex = utils.getRegex(data_type)
                            if data_type_regex is not None and not utils.checkString(data_type_regex, value):
                                malformed.append(obj)
                return 1.0 - (len(malformed) / len(all_triples))

            context.warning('Accuracy | Datatype consistency| Error executing query on SPARQL endpoint ')
            return MISSING_VALUE

        return context.timed('Check Datatype consistency', 'Accuracy', calculate_value)
    except Exception as error:
        context.warning(f'Accuracy | Datatype consistency| {str(error)}')
        return MISSING_VALUE
