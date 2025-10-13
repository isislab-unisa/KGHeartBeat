import VoIDAnalyses
import utils
import query
from API import Aggregator


class DeafHearingAccessibility:
    def __init__(self):
        return

    def examples(self, void_file_url, sparql_endpoint_url, search_engine_metadata):
        
        examples = search_engine_metadata.get("example", [])
        if len(examples) > 0:
            return (1, examples)

        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            examples_void = VoIDAnalyses.getExamples(void_file)
            if examples_void and len(examples_void) > 0:
                return (1, examples_void)
        
        if utils.is_url(sparql_endpoint_url):
            examples_sparql = query.get_examples(sparql_endpoint_url)
            if examples_sparql and len(examples_sparql) > 0:
                return (1, examples_sparql)
        
        return 0, "No examples found"
    
    def alternative_access_point(self, void_file_url, sparql_endpoint_url, idKG):
        available_download = False
        available_sparql = False
        available_api = False

        # Check availability in the download links in the search engine metadata
        resourcesDH = Aggregator.getOtherResources(idKG)
        resourcesDH = utils.insertAvailability(resourcesDH)
        available_download = any(res.get("status") == "active" for res in resourcesDH)

        # Check links availability from the SPARQL endpoint if online
        if utils.is_url(sparql_endpoint_url):
            available_sparql = bool(query.check_if_up(sparql_endpoint_url))

            if available_sparql:
                # Check API links
                for link in query.get_apis_url(sparql_endpoint_url):
                    if utils.checkAvailabilityResource(link):
                        available_api = True
                        break

                # Check dump links
                for link in query.get_download_link(sparql_endpoint_url):
                    if utils.checkAvailabilityResource(link):
                        available_download = True
                        break
        
        # Check links availability from the VoID file if provided
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)

            # Data dumps
            for link in VoIDAnalyses.getDataDump(void_file):
                if utils.checkAvailabilityResource(link):
                    available_download = True
                    break

            # SPARQL endpoint
            sparql_endpoint = VoIDAnalyses.getSparqlEndpoint(void_file)
            if utils.is_url(sparql_endpoint):
                available_sparql = bool(query.check_if_up(sparql_endpoint))

            # API links
            for link in VoIDAnalyses.getAccessPoint(void_file):
                if utils.checkAvailabilityResource(link):
                    available_api = True
                    break

        # To have 1 as result, at least two access points must be available
        result = int(sum([available_download, available_sparql, available_api]) >= 2)
        return (result, {
            "download": available_download, 
            "sparql_endpoint": available_sparql,
            "api": available_api
        })


    def human_redeable_labels(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            num_labels = query.count_res_with_label(sparql_endpoint)
            num_res = query.count_res(sparql_endpoint)
            if num_res > 0:
                ratio = num_labels / num_res
                return (ratio, f"Number of resources in the KG:{num_res}")
            return (0, "No resources found")
        return (0, "SPARQL endpoint not available")
