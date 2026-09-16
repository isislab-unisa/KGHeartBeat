from bloomfilter import BloomFilter
import query
from QualityDimensions.base import MISSING_VALUE


class Conciseness:
    def __init__(self,exC,intC):
        self.exC = exC
        self.intC = intC
    

    def getConciseness(self):
        return f"-Conciseness\n   Extensional conciseness:{self.exC}\n   Intensional conciseness:{self.intC}\n"


def calculate(context, all_triples):
    return Conciseness(
        _extensional_conciseness(context, all_triples),
        _intensional_conciseness(context),
    )


def _extensional_conciseness(context, all_triples):
    try:
        def calculate_value():
            triples = []
            duplicates = []
            if isinstance(all_triples, list) and len(all_triples) > 0:
                for triple in all_triples:
                    subject = triple.get('s').get('value')
                    predicate = triple.get('p').get('value')
                    obj = triple.get('o').get('value')
                    triples.append(subject + predicate + obj)

                bloom_filter = BloomFilter(len(triples), 0.05)
                context.logger.info(
                    f'Bloom filter parameter: \n -Size of bit array: {str(bloom_filter.size)}\n -False positive Probability:{str(bloom_filter.fp_prob)}\n -Number of hash functions:{str(bloom_filter.hash_count)}',
                    extra=context.kg_info,
                )
                for triple in triples:
                    if not bloom_filter.check(triple):
                        bloom_filter.add(triple)
                    else:
                        duplicates.append(triple)

                return f"{1.0 - (len(duplicates) / len(all_triples))} (out of {len(all_triples)} triples considered)"

            context.warning('Conciseness | Extensional conciseness | Insufficient data to compute the metric')
            return MISSING_VALUE

        return context.timed('Check Extensional conciseness', 'Conciseness', calculate_value)
    except Exception as error:
        context.warning(f'Conciseness | Extensional conciseness | {str(error)}')
        return MISSING_VALUE


def _intensional_conciseness(context):
    try:
        def calculate_value():
            triples = []
            duplicates = []
            count = 0
            for prop in query.getAllPropertySP(context.access_url):
                subject = prop.get('s').get('value')
                predicate = prop.get('p').get('value')
                triples.append(subject + predicate)
                count = count + 1

            bloom_filter = BloomFilter(len(triples), 0.05)
            for triple in triples:
                if not bloom_filter.check(triple):
                    bloom_filter.add(triple)
                else:
                    duplicates.append(triple)

            if count > 0:
                return f"{1.0 - (len(duplicates) / count)} (out of {count} triples considered)"

            context.warning('Conciseness | Intensional conciseness | Insufficient data to compute the metric')
            return MISSING_VALUE

        return context.timed('Check Intensional conciseness', 'Conciseness', calculate_value)
    except Exception as error:
        context.warning(f'Conciseness | Intensional conciseness | {str(error)}')
        return MISSING_VALUE
