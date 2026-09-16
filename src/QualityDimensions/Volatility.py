import query
import utils
from QualityDimensions.base import MISSING_VALUE


class Volatility:
    def __init__(self,frequency):
        self.frequency = frequency

    def to_dict(self):
        return {
            "frequency" : str(self.frequency),
        }
    
    def getVolatility(self):
        return f"-Volatility\n   Dataset update frequency:{self.frequency}\n"


def frequency_from_endpoint(context):
    try:
        frequency = context.timed(
            'dataset update frequency check',
            'Timeliness',
            lambda: query.getFrequency(context.access_url),
        )
        if isinstance(frequency, list) and len(frequency) > 0:
            return utils.save_only_unique_values(frequency)
        return frequency
    except Exception as error:
        context.warning(f'Volatility | Timeliness frequency | {str(error)}')
        return MISSING_VALUE
