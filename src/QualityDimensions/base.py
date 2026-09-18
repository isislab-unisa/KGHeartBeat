import time
from dataclasses import dataclass, field

import utils


MISSING_VALUE = '-'


@dataclass
class AnalysisContext:
    access_url: str
    name_kg: str
    analysis_date: str
    logger: object
    kg_info: dict
    triple_limit: int | None = 10000
    query_fallbacks: dict = field(default_factory=dict)

    def record_fallback(self, metric, triples, considered=None):
        """Record the coverage of a check evaluated locally after a query failed."""
        self.query_fallbacks[metric] = {
            'triples': len(triples),
            'considered': len(triples) if considered is None else considered,
        }

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
