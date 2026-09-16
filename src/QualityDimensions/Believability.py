import re

from API import Aggregator
from QualityDimensions.base import decimal


class Believability:
    def __init__(self,title,description,URI,reliableProvider,trustValue):
        self.title = title
        self.description = description
        self.URI = URI
        self.reliableProvider = reliableProvider
        self.trustValue = trustValue

    def getBelievability(self):
        return f"-Believability\n   KG title:{self.title}\n   Description:{self.description}\n   Dataset URL:{self.URI}\n   Is on a trusted provider list:{self.reliableProvider}\n   Trust value:{self.trustValue}\n"


def description_from_metadata(metadata):
    description = Aggregator.getDescription(metadata)
    if isinstance(description, str):
        description = description.strip()
        description = re.sub(r'\n+', '\n', description)
    return description


def reliable_provider(context, kg_id):
    try:
        providers = ['wikipedia', 'government', 'bioportal', 'bio2RDF', 'academic']
        keywords = Aggregator.getKeywords(kg_id)
        return any(provider in keywords for provider in providers)
    except Exception as error:
        context.warning(f"Believability | Trust value | {str(error)}")
        return '-'


def trust_value(context, name, description, source_url, believable):
    def calculate():
        value_name = 1 if isinstance(name, str) and name not in ['', 'Absent', 'absent'] else 0
        value_description = 1 if isinstance(description, str) and description not in ['', False, 'Absent'] else 0
        value_url = 1 if isinstance(source_url, str) and source_url not in ['', 'Absent', 'absent'] else 0
        value_provider = 1 if believable is True else 0
        return decimal((value_name + value_description + value_url + value_provider) / 4)

    return context.timed('Calculation of trust value', 'Believability', calculate)
