import utils
from API import LOVAPI
from QualityDimensions.base import MISSING_VALUE


class RepresentationalConsistency:
    def __init__(self,newVocab,useNewTerms):
        self.newVocab = newVocab
        self.useNewTerms = useNewTerms
    def getRepresentationalConsistency(self):
        return f"-Representational consistency\n   New vocabularies defined in the dataset:{self.newVocab}\n   Dataset define new terms:{self.useNewTerms}\n"


def new_terms(context, triples_o):
    try:
        def calculate():
            values = LOVAPI.searchTermsList(triples_o)
            if isinstance(values, list) and len(values) > 0:
                return utils.save_only_unique_values(values)
            return values

        return context.timed('New terms check', 'Interoperability', calculate)
    except Exception as error:
        context.warning(f'Representational-consistency | Reuse of terms | {str(error)}')
        return MISSING_VALUE


def new_vocabularies(context, vocabularies, label='New vocabularies check'):
    try:
        def calculate():
            values = []
            if isinstance(vocabularies, list):
                for vocab in vocabularies:
                    if LOVAPI.findVocabulary(vocab) is False:
                        values.append(vocab)
            if isinstance(values, list) and len(values) > 0:
                return utils.save_only_unique_values(values)
            return values

        return context.timed(label, 'Interoperability', calculate)
    except Exception as error:
        context.warning(f'Representational-consistency | re-use of existing terms | {str(error)}')
        return MISSING_VALUE
