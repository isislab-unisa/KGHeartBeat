import numpy

import query
import utils
from QualityDimensions.base import MISSING_VALUE, decimal


class RepresentationalConciseness:
    def __init__(self,urisLenghtSA,urisLenghtSSd,minLengthS,percentile25LengthS,medianLengthS,percentile75LengthS,maxLengthS,urisLenghtOA,urisLenghtOSd,minLengthO,percentile25LengthO,medianLengthO,percentile75LengthO,maxLengthO,urisLenghtPA,urisLenghtPSd,minLengthP,percentile25LengthP,medianLengthP,percentile75LengthP,maxLengthP,RDFStructures):
        self.urisLenghtSA = urisLenghtSA
        self.urisLenghtSSd = urisLenghtSSd
        self.urisLenghtOA = urisLenghtOA
        self.urisLenghtOSd = urisLenghtOSd
        self.urisLenghtPA = urisLenghtPA
        self.urisLenghtPSd = urisLenghtPSd
        self.minLengthS = minLengthS
        self.percentile25LengthS = percentile25LengthS
        self.medianLenghtS = medianLengthS
        self.percentile75LengthS = percentile75LengthS
        self.maxLengthS = maxLengthS
        self.minLengthO = minLengthO
        self.percentile25LengthO = percentile25LengthO
        self.medianLenghtO = medianLengthO
        self.percentile75LengthO = percentile75LengthO
        self.maxLengthO = maxLengthO
        self.minLengthP = minLengthP
        self.percentile25LengthP = percentile25LengthP
        self.medianLenghtP = medianLengthP
        self.percentile75LengthP = percentile75LengthP
        self.maxLengthP = maxLengthP
        self.RDFStructures = RDFStructures
    
    def getRepresentationalConciseness(self):
        return f"-Representational conciseness\n   Average length of URIs (subject):{self.urisLenghtSA}\n   Standard deviation of URIs length (subject):{self.urisLenghtSSd}\n   Min length URI (subject):{self.minLengthS}\n   25th percentile length URIs (subject):{self.percentile25LengthS}\n   Median length URIs (subject):{self.medianLenghtS}\n   75th percentile length URIs (subject):{self.percentile25LengthS}\n   Max length URIs (subject):{self.maxLengthS}\n   Average lenght of URIs (predicate):{self.urisLenghtPA}\n   Standard deviation of URIs lenght (predicate):{self.urisLenghtPSd}\n   Min length URI (predicate):{self.minLengthP}\n   25th percentile length URIs (predicate):{self.percentile25LengthP}\n   Median length URIs (predicate):{self.medianLenghtP}\n   75th percentile length URIs (predicate):{self.percentile25LengthP}\n   Max length URIs (predicate):{self.maxLengthP}\n   Average length of URIs (object):{self.urisLenghtOA}\n   Standard deviation of URIs lenght (object):{self.urisLenghtOSd}\n   Min length URI (object):{self.minLengthO}\n   25th percentile length URIs (object):{self.percentile25LengthO}\n   Median length URIs (object):{self.medianLenghtO}\n   75th percentile length URIs (object):{self.percentile25LengthO}\n   Max length URIs (object):{self.maxLengthO}\n   Use RDF structures:{self.RDFStructures}\n "


def calculate(context, all_triples, rdf_structures):
    subject_stats = _subject_uri_lengths(context, all_triples)
    object_values, object_stats = _triple_uri_lengths(all_triples, 'o')
    predicate_values, predicate_stats = _triple_uri_lengths(all_triples, 'p')

    subject_values = []
    all_uri = []
    if isinstance(all_triples, list) and isinstance(predicate_values, list) and isinstance(object_values, list):
        subject_values = [triple.get('s').get('value') for triple in all_triples]
        all_uri = object_values + predicate_values + subject_values

    return RepresentationalConciseness(
        subject_stats["average"],
        subject_stats["standard_deviation"],
        subject_stats["min"],
        subject_stats["percentile_25"],
        subject_stats["median"],
        subject_stats["percentile_75"],
        subject_stats["max"],
        object_stats["average"],
        object_stats["standard_deviation"],
        object_stats["min"],
        object_stats["percentile_25"],
        object_stats["median"],
        object_stats["percentile_75"],
        object_stats["max"],
        predicate_stats["average"],
        predicate_stats["standard_deviation"],
        predicate_stats["min"],
        predicate_stats["percentile_25"],
        predicate_stats["median"],
        predicate_stats["percentile_75"],
        predicate_stats["max"],
        rdf_structures,
    ), all_uri, object_values, predicate_values


def rdf_structures(context):
    try:
        return context.timed('RDF structures check', 'Interpretability', lambda: query.checkRDFDataStructures(context.access_url))
    except Exception as error:
        context.warning(f'Representational-conciseness | Use of RDF structures | {str(error)}')
        return MISSING_VALUE


def unavailable(error_message=MISSING_VALUE):
    return RepresentationalConciseness(*([error_message] * 22))


def _subject_uri_lengths(context, all_triples):
    if not isinstance(all_triples, list):
        return _missing_stats()
    try:
        def calculate_value():
            context.logger.info('Calculating the URIs length...', extra=context.kg_info)
            values = []
            for triple in all_triples:
                uri = triple.get('s').get('value')
                if utils.validateURI(uri):
                    values.append(len(uri))
            return _length_stats(values, len(all_triples))

        return context.timed('URIs length', 'Rep.Conc.', calculate_value)
    except Exception as error:
        context.warning(f'Representational-conciseness | Keeping URI short | {str(error)}')
        return _missing_stats()


def _triple_uri_lengths(triples, position):
    if not isinstance(triples, list):
        return MISSING_VALUE, _missing_stats()
    values = list(dict.fromkeys(triple[position]['value'] for triple in triples
                               if triple[position]['type'] == 'uri'))
    return values, _length_stats([len(uri) for uri in values], len(triples))


def _length_stats(lengths, considered_count):
    if not lengths:
        return _missing_stats()

    return {
        "average": f"{decimal(sum(lengths) / len(lengths))} (out of {considered_count} triples considered)",
        "standard_deviation": decimal(numpy.std(lengths)),
        "min": decimal(min(lengths)),
        "max": decimal(max(lengths)),
        "median": decimal(numpy.median(lengths)),
        "percentile_25": decimal(numpy.percentile(lengths, 25)),
        "percentile_75": decimal(numpy.percentile(lengths, 75)),
    }


def _missing_stats():
    return {
        "average": MISSING_VALUE,
        "standard_deviation": MISSING_VALUE,
        "min": MISSING_VALUE,
        "max": MISSING_VALUE,
        "median": MISSING_VALUE,
        "percentile_25": MISSING_VALUE,
        "percentile_75": MISSING_VALUE,
    }
