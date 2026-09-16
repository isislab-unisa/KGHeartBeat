import time
from dataclasses import dataclass

import utils


MISSING_VALUE = '-'


@dataclass
class AnalysisContext:
    access_url: str
    name_kg: str
    analysis_date: str
    logger: object
    kg_info: dict

    def warning(self, message):
        self.logger.warning(message, extra=self.kg_info)

    def error(self, message):
        self.logger.error(message, extra=self.kg_info)

    def write_time(self, elapsed, label, dimension):
        utils.write_time(self.name_kg, elapsed, label, dimension, self.analysis_date)

    def timed(self, label, dimension, callback):
        start = time.time()
        result = callback()
        self.write_time(time.time() - start, label, dimension)
        return result


def missing_stats(keys):
    return {key: MISSING_VALUE for key in keys}


def decimal(value, precision=None):
    if precision is not None:
        value = f"{value:.{precision}f}"
    value = str(value)
    return value.replace('.', ',')
