from xml.dom.minidom import Document

import query
from QualityDimensions.base import MISSING_VALUE


class Security:
    def __init__(self,useHTTPS,requiresAuth):
        self.useHTTPS = useHTTPS
        self.requiresAuth = requiresAuth
    
    def getSecurity(self):
        return f"-Security\n   Use HTTPS:{self.useHTTPS}\n   Requires authentication:{self.requiresAuth}\n"


def https_available(context):
    try:
        def check():
            sec_access_url = context.access_url.replace('http', 'https')
            result = query.checkEndPoint(sec_access_url)
            return isinstance(result, Document) or isinstance(result, dict)

        return context.timed('Check HTTPS', 'Security', check)
    except Exception:
        return False


def unavailable(error_message=MISSING_VALUE):
    return Security(error_message, error_message)
