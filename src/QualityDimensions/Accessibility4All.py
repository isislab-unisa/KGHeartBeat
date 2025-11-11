import requests
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import query
import VoIDAnalyses
import utils
from API import Aggregator

class Accessibility4All:
    def __init__(self):
        self.open_license_value = None
        self.assistive_technologies_value = None
        return None

    def open_license(self, kg_license):
        if kg_license == False:
            self.open_license_value = (0, kg_license)
            return self.open_license_value

        # Case 1: all elements are '-'
        if all(license == '-' for license in kg_license):
            self.open_license_value = (0, kg_license)
            return self.open_license_value

        # Retrieve the open license list from Open Knowledge Foundation
        url = "https://raw.githubusercontent.com/okfn/licenses/master/licenses/groups/all.json"
        response = requests.get(url)

        if response.status_code == 200:
            open_license_data = response.json()

            # Extract URLs of open licenses and normalize by removing protocol
            okfn_urls = [lic["url"].replace("http://", "").replace("https://", "") 
                        for lic in open_license_data.values() if lic.get("url")]

            def normalize(url):
                return url.replace("http://", "").replace("https://", "")

            # At least one KG license matches an open license
            if isinstance(kg_license, list):
                if any(normalize(license) in okfn_urls for license in kg_license):
                    self.open_license_value = (1, kg_license)
                else:
                    self.open_license_value = (-1, kg_license)
            else:
                if normalize(kg_license) in okfn_urls:
                    self.open_license_value = (1, kg_license)
                else:
                    self.open_license_value = (-1, kg_license)

            return self.open_license_value
        else:
            # Request failed
            return (0, "Failed to retrieve open license list")
        
    def webpage_status(self, website_url):
        try:
            response = requests.get(website_url)
            if response.status_code == 200:
                return (1, website_url)
            else:
                return (-1, website_url)
        except Exception as e:
            return (-1, e)
        
        try:
            response = requests.get(url, allow_redirects=True, timeout=10)
            # Basic validity check
            if response.status_code != 200:
                return False

            # Lowercase content for keyword search
            content = response.text.lower()

            # Detect common "not found" indicators
            error_indicators = [
                "not found",
                "error",
                "404",
                "page not found",
                "content not found",
                "does not exist",
                "no encontrado",
                "no se encuentra",
            ]

            # If any error indicator appears in the content → treat as broken
            if any(indicator in content for indicator in error_indicators):
                return (-1, website_url)

            return (1, website_url)
        except requests.RequestException:
            return (-1, website_url)
        
    def check_authentication(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            try:
                response = requests.get(sparql_endpoint)
                if response.status_code == 200:
                    return (0, sparql_endpoint)
                elif response.status_code == 401:
                    return (-1, sparql_endpoint)
                else:
                    return (-1, f"{sparql_endpoint} (status: {response.status_code})")
            except Exception as e:
                return (-1, str(e))
        else:
            return (-1, "No SPARQL endpoint provided")


    def metadata_broken_links_rate(self, search_engine_metadata, sparql_endpoint, void_file_url, kg_id):
        if utils.is_url(sparql_endpoint):
            all_obj_sparql = query.get_all_metadata_obj(sparql_endpoint)
        else:
            all_obj_sparql = "Can't query metadata from SPARQL endpoint"
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            all_obj_void = VoIDAnalyses.get_all_obj(void_file)
        else:
            all_obj_void = "Can't query metadata from VoID file"

        if isinstance(all_obj_void, list) and len(all_obj_void) > 0:
            broken_links = 0
            no_broken_links = 0
            for obj in all_obj_void:
                if utils.is_url(obj):
                    try:
                        response = requests.head(obj, timeout=5)
                        if response.status_code != 200:
                            broken_links += 1
                        elif response.status_code == 200:
                            no_broken_links += 1
                    except:
                        broken_links += 1
            broken_links_ratio =  0 - (broken_links / (no_broken_links + broken_links)) if (no_broken_links + broken_links) > 0 else 0
            return (broken_links_ratio, f"Metadata from VoID file: {all_obj_void}")
        elif isinstance(all_obj_sparql, list) and len(all_obj_sparql) > 0:
            broken_links = 0
            no_broken_links = 0
            for obj in all_obj_sparql:
                if utils.is_url(obj):
                    try:
                        response = requests.head(obj, timeout=5)
                        if response.status_code != 200:
                            broken_links += 1
                        elif response.status_code == 200:
                            no_broken_links += 1
                    except:
                        broken_links += 1
            broken_links_ratio =  0 - (broken_links / (no_broken_links + broken_links)) if (no_broken_links + broken_links) > 0 else 0
            return (broken_links_ratio, f"Metadata from SPARQL endpoint: {all_obj_sparql}")
        elif isinstance(search_engine_metadata, dict):
            available_resources_count = 0
            unavailable_resources_count = 0

            # Check website link
            website_links = search_engine_metadata.get('website', [])
            if utils.is_url(website_links):
                try:
                    response = requests.head(website_links, timeout=5)
                    if response.status_code == 200:
                        available_resources_count += 1
                    else:
                        unavailable_resources_count += 1
                except:
                    unavailable_resources_count += 1

            resources = Aggregator.getOtherResources(kg_id)
            resources = utils.insertAvailability(resources)
            
            available_resources = [res for res in resources if res.get("status") == "active"]
            unavailable_resources = [res for res in resources if res.get("status") == "offline"]
            available_resources_count += len(available_resources)
            unavailable_resources_count += len(unavailable_resources)

            broken_links_ratio = 0 - (unavailable_resources_count / (available_resources_count + unavailable_resources_count)) if (available_resources_count + unavailable_resources_count) > 0 else 0
            return (broken_links_ratio, f"Metadata from Search engine file: {resources}")

        return (-1, "No metadata found in SPARQL endpoint, VoID file or search engine metadata")

    def version(self, void_file_url, sparql_endpoint):
        version = False
        if utils.is_url(sparql_endpoint):
            version_in_kg = query.get_version(sparql_endpoint)
            if isinstance(version_in_kg, list):
                if len(version_in_kg) > 0:
                    version = version_in_kg
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            version_in_void = VoIDAnalyses.get_version(void_file)
            if version_in_void != False:
                version = version_in_void

        if version != False:
            return (0, version)
        else:
            return (-1, "No version found")

    def assistive_technologies(self, sparql_endpoint, void_file_url):
        ass_tech = []
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            ass_tech = VoIDAnalyses.check_acc_feature(void_file)
        else:
            ass_tech= False
        if utils.is_url(sparql_endpoint):
            ass_tech = query.check_acc_feature(sparql_endpoint)

        if isinstance(ass_tech, list) and len(ass_tech) > 0:
            return (1, ass_tech)
        else:
            return (0, ass_tech)
        

    def canonical_citation(self, void_file_url, sparql_endpoint, search_engine_metadata):
        citation = False
        if isinstance(search_engine_metadata, dict):
            doi = search_engine_metadata.get('doi', False)
            if doi != False and doi != '':
                citation = doi

        if utils.is_url(sparql_endpoint):
            identifier = query.get_identifier(sparql_endpoint)
            if isinstance(identifier, list):
                if len(identifier) > 0:
                    citation = identifier

        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            identifier = VoIDAnalyses.get_identifier(void_file)
            if identifier != False:
                citation = identifier

        if citation != False:
            return (1, citation)
        else:
            return (0, "No citation found")

    def contact_point(self, search_engine_metadata, sparql_endpoint, void_file_url):
        contact_in_metadata = search_engine_metadata.get('contact_point', False)
        if contact_in_metadata != False and isinstance(contact_in_metadata, dict):
            name = contact_in_metadata.get('name', False)
            email = contact_in_metadata.get('email', False)
            if (email and email != 'null') or (name and name != 'null'):
                return (1, contact_in_metadata)
        
        if utils.is_url(sparql_endpoint):
            contact_in_sparql = query.get_contact_point(sparql_endpoint)
            if isinstance(contact_in_sparql, list) and len(contact_in_sparql) > 0:
                return (1, contact_in_sparql)
        
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            contact_in_void = VoIDAnalyses.get_contact_point(void_file)
            if isinstance(contact_in_void, list) and len(contact_in_void) > 0:
                return (1, contact_in_void)

        return (0, "No contact point found")

    def dump_size(self, void_file_url, sparql_endpoint, idKG):
        resourcesDH = Aggregator.getOtherResources(idKG)
        resourcesDH = utils.insertAvailability(resourcesDH)
        small_dump = False
        medium_dump = False
        large_dump = False
        dumps = []
        for resources in resourcesDH:
            if resources.get("status") == "active" and resources.get("type") == "full_download" and (utils.check_common_acceppted_format(resources.get("format")) or utils.check_if_zipped_dump(resources.get("format"))):
                dumps.append(resources['path'])
                try:
                    size = utils.estimate_file_size_gb(resources['path'])
                except Exception as e:
                    size = False
                if isinstance(size, float) and size < 0.500:
                    small_dump = True
                elif isinstance(size, float) and 0.500 <= size < 4:
                    medium_dump = True
                elif isinstance(size, float) and size >= 4:
                    large_dump = True
        
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            dump = VoIDAnalyses.getDataDump(void_file)
            if utils.is_url(dump):
                dumps.append(dump)
                if isinstance(size, float) and size < 0.500:
                    small_dump = True
                elif isinstance(size, float) and 0.500 <= size < 4:
                    medium_dump = True
                elif isinstance(size, float) and size >= 4:
                    large_dump = True

        if utils.is_url(sparql_endpoint):
            sparql_dumps = query.get_download_link(sparql_endpoint)
            if isinstance(sparql_dumps, list):
                for dump_link in sparql_dumps:
                    if utils.is_url(dump_link):
                        dumps.append(dump_link)
                        size = utils.estimate_file_size_gb(dump_link)
                        if isinstance(size, float) and size < 0.500:
                            small_dump = True
                        elif isinstance(size, float) and 0.500 <= size < 4:
                            medium_dump = True
                        elif isinstance(size, float) and size >= 4:
                            large_dump = True

        if small_dump:
            return (1, dumps)
        elif medium_dump:
            return (0, dumps)
        elif large_dump:
            return (-1, dumps)
        elif len(dumps) == 0:
            return (0, "No data dumps found")
        elif len(dumps) > 0 and not small_dump and not medium_dump and not large_dump:
            return (0, f"Unknown dump size for: {dumps}")

    # TODO: move to extension format
    def image(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            image_in_kg = query.getImageIri(sparql_endpoint)
            total_resources_in_kg = query.fetch_subjects(sparql_endpoint)
            if isinstance(image_in_kg, list) and isinstance(total_resources_in_kg, int) and total_resources_in_kg > 0:
                image_ratio = len(image_in_kg) / total_resources_in_kg
                return (image_ratio, image_in_kg)
            elif image_in_kg == False or total_resources_in_kg == False:
                return (0, 'Error querying SPARQL endpoint')
            else:
                return (0, "No images found")
        else:
            return (0, "No SPARQL endpoint provided")
    
    def human_redeable_labels(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            num_labels = query.count_res_with_label(sparql_endpoint)
            num_res = query.count_res(sparql_endpoint)
            if num_res > 0:
                ratio = num_labels / num_res
                return (ratio, f"Number of resources in the KG:{num_res}")
            return (0, "No resources found")
        return (0, "SPARQL endpoint not available")

    def robots_txt(self, resources, sparql_endpoint, website_url):
        def check_robots(url):
            try:
                response = requests.get(url, timeout=10, allow_redirects=True)
                content_type = response.headers.get("Content-Type", "").lower()

                # Accept only text/plain or text/* as valid robots.txt responses
                if response.status_code == 200 and content_type.startswith("text/"):
                    return (1, url)
                elif response.status_code == 200:
                    # 200 but not text-based → invalid robots.txt
                    return (0, f"{url} (invalid Content-Type: {content_type})")
                else:
                    return (0, f"{url} (status: {response.status_code})")
            except Exception as e:
                return (0, str(e))

        if utils.is_url(sparql_endpoint):
            robots_url = sparql_endpoint.rstrip('/') + '/robots.txt'
            result = check_robots(robots_url)
            if result[0] == 1:
                return result

        if utils.is_url(website_url):
            robots_url = website_url.rstrip('/') + '/robots.txt'
            result = check_robots(robots_url)
            if result[0] == 1:
                return result

        for link in resources or []:
            path = link.get('path', '')
            if 'robots.txt' in path and utils.is_url(path):
                result = check_robots(path)
                if result[0] == 1:
                    return result

        return (0, "No valid robots.txt found")
    

    def common_formats_availability(self, idKG):
        resourcesDH = Aggregator.getOtherResources(idKG)
        resourcesDH = utils.insertAvailability(resourcesDH)
        available_download = []
        for res in resourcesDH:
            if res.get("status") == "active" and res.get("type") == "full_download":
                available_download.append(res)
        metadata_media_type = utils.extract_media_type(available_download)
        common_formats_availability = utils.check_common_acceppted_format(metadata_media_type)
        if common_formats_availability:
            return (0, metadata_media_type)
        else:    
            return (-1, metadata_media_type)

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
        available_download = any(res.get("status") == "active" and 
                                 res.get("type") == "full_download" and (
                                 utils.check_common_acceppted_format(res.get("format") or utils.url_points_to_graph_file(res.get("url")))) for res in resourcesDH)

        # Check links availability from the SPARQL endpoint if online
        if utils.is_url(sparql_endpoint_url):
            available_sparql = bool(query.check_if_up(sparql_endpoint_url))

            if available_sparql:
                # Check API links
                api_links = query.get_apis_url(sparql_endpoint_url)
                if isinstance(api_links, list):
                    for link in api_links:
                        if utils.checkAvailabilityResource(link):
                            available_api = True
                            break

                # Check dump links
                dump_links = query.get_download_link(sparql_endpoint_url)
                if isinstance(dump_links, list):
                    for link in dump_links:
                        if utils.checkAvailabilityResource(link):
                            available_download = True
                            break

        # Check links availability from the VoID file if provided
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)

            # Data dumps
            dump_links_void = VoIDAnalyses.getDataDump(void_file)
            if isinstance(dump_links_void, list):
                for link in dump_links_void:
                    if utils.checkAvailabilityResource(link):
                        available_download = True
                        break

            # SPARQL endpoint
            sparql_endpoint = VoIDAnalyses.getSparqlEndpoint(void_file)
            if utils.is_url(sparql_endpoint):
                available_sparql = bool(query.check_if_up(sparql_endpoint))

            # API links
            access_points = VoIDAnalyses.getAccessPoint(void_file)
            if isinstance(access_points, list): 
                for link in access_points:
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
    
    def description_readability(self, sparql_endpoint_url, void_file_url, description_metadata):
        description = False
        if isinstance(description_metadata, str) and description_metadata != 'absent' and description_metadata != '':
            description = description_metadata
            readability_score = utils.flesch_reading_ease(description)
            if readability_score >= 100:
                return 1 , f"Description from search engine metadata: {description}"
            else:
                return (round((readability_score / 50) - 1, 2), f"Description from search engine metadata: {description}")

        if utils.is_url(sparql_endpoint_url):
            description_sparql = query.getDescription(sparql_endpoint_url)
            if isinstance(description_sparql, list) and len(description_sparql) > 0:
                description = description_sparql[0]
                if isinstance(description, str):
                    return (round(readability_score / 100, 2), f"Description from SPARQL endpoint: {description}")

        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            description_void = VoIDAnalyses.getDescription(void_file)
            if isinstance(description_void, list) and len(description_void) > 0:
                description = description_void[0]
                readability_score = utils.flesch_reading_ease(description)
                return (round(readability_score / 100, 2), f"Description from VoID file: {description}")

        if description == False or description == '':
            return (0, "No description found")

    def data_lang(self, sparql_endpoint_url):
        if utils.is_url(sparql_endpoint_url):
            languages_list = query.getLangugeSupported(sparql_endpoint_url)
            query_results = query.get_string_literals(sparql_endpoint_url)
            if isinstance(query_results, tuple) and query_results[0] != 0:
                total_triple_count, lang_count = query_results

                return round(lang_count / total_triple_count, 2), f"Languages available: {languages_list}"
            
            elif isinstance(languages_list, list):
                return 0, f"Languages available: {languages_list}"
            
            else:
                return 0, f"Error querying SPARQL endpoint: {languages_list} - {query_results}"
        else:
            return 0, "No SPARQL endpoint provided"

    def metadata_lang(self, sparql_endpoint_url, void_file):
        if utils.is_url(sparql_endpoint_url):
            query_results = query.get_metadata_languages(sparql_endpoint_url)
            if isinstance(query_results, list):
                return f"Number of languages found: {len(query_results)}", f"Languages found: {query_results}"
            else:
                return 0, f"Error querying SPARQL endpoint: {query_results}"
        elif utils.is_url(void_file):
            void_file_parsed = VoIDAnalyses.parseVoID(void_file)
            void_languages = VoIDAnalyses.getLanguage(void_file_parsed)
            if isinstance(void_file_parsed, list):
                return f"Number of languages found: {len(void_languages)}", f"Languages found: {void_languages}"
            elif void_languages == 'absent':
                return 0, "No languages found in VoID file"
        else:
            return 0, "No SPARQL endpoint or VoID file provided to check languages in the metadata"
        
#aa = Accessibility4All()
#print(aa.metadata_lang("https://dbpedia.org/sparql"))