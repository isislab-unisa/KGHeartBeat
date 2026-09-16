import query
import utils
from QualityDimensions.base import MISSING_VALUE


class Understendability:
    def __init__(self,numLabel,percentageLabel,regexUri,vocabularies,example,name,description,sources):
        self.numLabel = numLabel
        self.percentageLabel = percentageLabel
        self.regexUri = regexUri
        self.vocabularies = vocabularies
        self.example = example
        self.name = name
        self.description = description
        self.sources = sources
    
    def getUnderstendability(self):
        return f"-Understendability\n   Number of labels/comments present on the data:{self.numLabel}\n   Percentage of triples with labels:{self.percentageLabel}\n   Regex uri:{self.regexUri}\n   Vocabularies:{self.vocabularies}\n   Presence of example:{self.example}\n"


def labels_count(context):
    try:
        return context.timed(
            'Number of label check',
            'Understandability',
            lambda: query.getNumLabel(context.access_url),
        )
    except Exception as error:
        context.warning(f'Amount of data | Number of labels | {str(error)}')
        return MISSING_VALUE


def uri_regexes(context):
    regex = []
    try:
        def collect():
            values = query.checkUriRegex(context.access_url)
            if isinstance(values, list) and len(values) > 0:
                values = utils.save_only_regex(values)

            pattern = query.checkUriPattern(context.access_url)
            if isinstance(pattern, list):
                if not isinstance(values, list):
                    values = []
                for item in pattern:
                    values.append(utils.trasforrmToRegex(item))
            return values

        regex = context.timed('URI regex check', 'Understandability', collect)
    except Exception as error:
        context.warning(f'Understandability | URIs regex | {str(error)}')
        regex = MISSING_VALUE
    return regex


def vocabularies_from_endpoint(context):
    try:
        vocabularies = context.timed(
            'Vocabs check',
            'Understandability',
            lambda: query.getVocabularies(context.access_url),
        )
        if isinstance(vocabularies, list) and len(vocabularies) > 0:
            return utils.save_only_unique_values(vocabularies)
        return vocabularies
    except Exception as error:
        context.warning(f'Understandability | Vocabularies | {str(error)}')
        return MISSING_VALUE


def build(num_label, triples_query, triples_metadata, regex, vocabularies, example, name, description, source_url):
    if isinstance(num_label, int) and isinstance(triples_query, int) and triples_query > 0:
        percentage_label = f"{(num_label / triples_query) * 100:.2f}%"
    elif isinstance(num_label, int) and isinstance(triples_metadata, int) and triples_metadata > 0:
        percentage_label = f"{(num_label / triples_metadata) * 100:.2f}%"
    else:
        percentage_label = 'insufficient data'
    return Understendability(num_label, percentage_label, regex, vocabularies, example, name, description, source_url)
