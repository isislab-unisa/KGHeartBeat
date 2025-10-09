import VoIDAnalyses
import utils
import query

class DeafHearingAccessibility:
    def __init__(self):
        return

    def examples(self, void_file_url, sparql_endpoint_url, search_engine_metadata):
        
        examples = search_engine_metadata.get("example", [])
        if len(examples) > 0:
            return 1

        if utils.is_url(void_file_url):
            examples_void = VoIDAnalyses.getExamples(void_file_url)
            if examples_void and len(examples_void) > 0:
                return 1
        
        if utils.is_url(sparql_endpoint_url):
            examples_sparql = query.get_examples(sparql_endpoint_url)
            if examples_sparql and len(examples_sparql) > 0:
                return 1
        
        return 0
