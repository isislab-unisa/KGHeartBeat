

from Sources import Sources
import query
from QualityDimensions.base import MISSING_VALUE


class Verifiability:
    def __init__(self,vocabularies,authorQ,authorM,contributor,publisher,sources,sign):
        self.vocabularies = vocabularies
        self.authorQ = authorQ
        self.authorM = authorM
        self.contributor = contributor
        self.publisher = publisher
        self.sources = sources
        self.sign = sign
    
    def getVerifiability(self):
        return f"-Verifiability\n   Vocabularies:{self.vocabularies}\n   Author (query):{self.authorQ}\n   Author (metadata):{self.authorM}\n   Contributor:{self.contributor}\n   Publisher:{self.publisher}\n  {Sources.sourcesKG(self.sources)}\n   Signature on the KG:{self.sign}\n"
    
    def to_dict(self):
        return {
            "vocabularies" : self.vocabularies,
            "author-Query" : self.authorQ,
            "autho-Meta" : self.authorM,
            "contributor" : self.contributor,
            "publisher" : self.publisher,
            "sources" : self.sources.to_dict(),
            "sign" : self.sign
        }


def authors_from_endpoint(context):
    try:
        return context.timed(
            'Authors check',
            'Verifiability',
            lambda: query.getCreator(context.access_url),
        )
    except Exception as error:
        context.warning(f'Verifiability | Verifiying publisher information | {str(error)}')
        return MISSING_VALUE


def publishers_from_endpoint(context):
    try:
        return context.timed(
            'Publishers check',
            'Verifiability',
            lambda: query.getPublisher(context.access_url),
        )
    except Exception as error:
        context.warning(f'Verifiability | Verifiying publisher information | {str(error)}')
        return MISSING_VALUE


def contributors_from_endpoint(context):
    try:
        return context.timed(
            'Contribs. check',
            'Verifiability',
            lambda: query.getContributors(context.access_url),
        )
    except Exception as error:
        context.warning(f'Verifiability | Verifiying publisher information | {str(error)}')
        return MISSING_VALUE


def signed_kg(context):
    try:
        sign = context.timed('Sign check', 'Security', lambda: query.getSign(context.access_url))
        if isinstance(sign, int):
            return sign > 0
        return False
    except Exception as error:
        context.warning(f'Verifiability | Verifying usage of digital signatures | {str(error)}')
        return MISSING_VALUE
