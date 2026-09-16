from SPARQLWrapper import SPARQLExceptions

import query
from QualityDimensions.base import MISSING_VALUE


class Licensing:
    def __init__(self,licenseMetadata,licenseQuery,licenseHR):
        self.licenseMetadata = licenseMetadata
        self.licenseQuery = licenseQuery
        self.licenseHR = licenseHR

    def getLicensing(self):
        return f"-Licensing\n   License machine redeable (metadata):{self.licenseMetadata}\n   License machine redeable (query):{self.licenseQuery}\n   License human redeable:{self.licenseHR}\n"


def machine_readable_from_endpoint(context):
    try:
        license_query = context.timed(
            'MR license check',
            'License',
            lambda: query.checkLicenseMR2(context.access_url),
        )
        if isinstance(license_query, list):
            return license_query[0]
        return license_query
    except Exception as error:
        context.warning(f'Licensing | Machine-redeable license | {str(error)}')
        return MISSING_VALUE


def human_readable_from_endpoint(context):
    try:
        return context.timed(
            'HR license check',
            'License',
            lambda: query.checkLicenseHR(context.access_url),
        )
    except (SPARQLExceptions.QueryBadFormed, SPARQLExceptions.EndPointInternalError) as response:
        context.warning(f'Licensing | Human-redeable license | {str(response)}')
    except Exception as error:
        context.warning(f'Licensing | Human-redeable license | {str(error)}')
    return MISSING_VALUE
