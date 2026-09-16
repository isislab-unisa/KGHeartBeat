import numpy
import urllib.error
from SPARQLWrapper import SPARQLExceptions

import query
import utils
from QualityDimensions.base import MISSING_VALUE, decimal, missing_stats


class Performance:
    def __init__(self,minLatency,maxLantency,averageLatency,sDLatency,percentile25L,percentile75L,medianL,minThroughput,maxThrougput,averageThroughput,sDThroughput,percentile25T,percentile75T,medianT):
        self.minLatency = minLatency
        self.maxLatency = maxLantency
        self.averageLatency = averageLatency
        self.sDLatency = sDLatency
        self.minThroughput = minThroughput
        self.maxThroughput = maxThrougput
        self.averageThroughput = averageThroughput
        self.sDThroughput = sDThroughput
        self.percentile25L = percentile25L
        self.percentile75L = percentile75L
        self.medianL = medianL
        self.percentile25T = percentile25T
        self.percentile75T = percentile75T
        self.medianT = medianT
    
    def getPerformance(self):
        return f"-Performance\n   Minimum latency:{self.minLatency}\n   25th percentile latency:{self.percentile25L}\n   Median latency:{self.medianL}\n   75th percentile latency:{self.percentile75L}\n   Maximum latency:{self.maxLatency}\n   Average latency:{self.averageLatency}\n   Standard deviation of latency:{self.sDLatency}\n   Minimum throughput:{self.minThroughput}\n   25th percentile throughput:{self.percentile25T}\n   Median throughput:{self.medianT}\n   75th percentile throughput:{self.percentile75T}\n   Maximum throughput:{self.maxThroughput}\n   Average throughput:{self.averageThroughput}\n   Standard deviation of throughput:{self.sDThroughput}\n"

    @classmethod
    def calculate(cls, context):
        latency = _measure_latency(context)
        throughput = _measure_throughput(context)
        throughput_no_offset = _measure_throughput_no_offset(context, throughput)

        return cls(
            latency["min"],
            latency["max"],
            latency["average"],
            latency["standard_deviation"],
            latency["percentile_25"],
            latency["percentile_75"],
            latency["median"],
            throughput["min"],
            throughput["max"],
            throughput["average"],
            throughput["standard_deviation"],
            throughput["percentile_25"],
            throughput["percentile_75"],
            throughput["median"],
        ), throughput_no_offset


def unavailable():
    stats = _missing_latency_stats()
    stats.update(_missing_throughput_stats())
    return Performance(
        stats["min_latency"],
        stats["max_latency"],
        stats["average_latency"],
        stats["standard_deviation_latency"],
        stats["percentile_25_latency"],
        stats["percentile_75_latency"],
        stats["median_latency"],
        stats["min_throughput"],
        stats["max_throughput"],
        stats["average_throughput"],
        stats["standard_deviation_throughput"],
        stats["percentile_25_throughput"],
        stats["percentile_75_throughput"],
        stats["median_throughput"],
    )


def _measure_latency(context):
    keys = ["min", "max", "average", "standard_deviation", "percentile_25", "percentile_75", "median"]

    try:
        values = context.timed(
            'Total latancy measurement',
            'Performance',
            lambda: query.testLatency(context.access_url),
        )
        return _series_stats(values, keys, precision=3)
    except urllib.error.HTTPError as response:
        context.warning(f'Performance | Latency | {str(response)}')
    except SPARQLExceptions.QueryBadFormed:
        context.warning('Performance | Latency | Query bad formed')
    except SPARQLExceptions.EndPointInternalError:
        context.warning('Performance | Latency | SPARQL endpoint internal error')
    except Exception as error:
        context.error('Performance | Latency | ' + str(error))

    return missing_stats(keys)


def _measure_throughput(context):
    keys = ["min", "max", "average", "standard_deviation", "percentile_25", "percentile_75", "median"]

    try:
        values = context.timed(
            'Throughput check',
            'Performance',
            lambda: utils.getThroughput(context.access_url),
        )
        return _series_stats(values, keys)
    except Exception as error:
        context.warning(f'Performance | High Throughput | {str(error)}')
        return missing_stats(keys)


def _measure_throughput_no_offset(context, throughput):
    keys = ["min", "max", "average", "standard_deviation"]

    try:
        values = utils.getThroughputNoOff(context.access_url)
        if not values:
            return missing_stats(keys)

        return {
            "min": min(values),
            "max": max(values),
            "average": decimal(sum(values) / len(values)),
            "standard_deviation": decimal(numpy.std(values)),
        }
    except Exception as error:
        context.warning(f'Performance | High Throughput | {str(error)}')
        return missing_stats(keys)


def _series_stats(values, keys, precision=None):
    if not values:
        return missing_stats(keys)

    stats = {
        "min": decimal(min(values), precision) if precision is not None else min(values),
        "max": decimal(max(values), precision) if precision is not None else max(values),
        "average": decimal(sum(values) / len(values), precision),
        "standard_deviation": decimal(numpy.std(values), precision),
        "percentile_25": decimal(numpy.percentile(values, 25), precision),
        "percentile_75": decimal(numpy.percentile(values, 75), precision),
        "median": decimal(numpy.median(values), precision),
    }
    return {key: stats[key] for key in keys}


def _missing_latency_stats():
    return missing_stats([
        "min_latency",
        "max_latency",
        "average_latency",
        "standard_deviation_latency",
        "percentile_25_latency",
        "percentile_75_latency",
        "median_latency",
    ])


def _missing_throughput_stats():
    return missing_stats([
        "min_throughput",
        "max_throughput",
        "average_throughput",
        "standard_deviation_throughput",
        "percentile_25_throughput",
        "percentile_75_throughput",
        "median_throughput",
    ])
