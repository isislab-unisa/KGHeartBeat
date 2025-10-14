import requests
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

            # Extract URLs of open licenses
            okfn_urls = [lic["url"] for lic in open_license_data.values() if lic.get("url")]
   
            # At least one KG license matches an open license
            if any(license in okfn_urls for license in kg_license):
                self.open_license_value = (1, kg_license)
            else:
                # Case 3: licenses are present but not recognized as open
                self.open_license_value = (0.5, kg_license)

            return self.open_license_value

        else:
            # Request failed
            return {"error": "Failed to retrieve license information"}

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
    
    def webpage_status(self, website_url):
        try:
            response = requests.get(website_url)
            if response.status_code == 200:
                return (1, website_url)
            else:
                return (0, website_url)
        except Exception as e:
            return (0, e)

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
                        response = requests.get(obj)
                        if response.status_code != 200:
                            broken_links += 1
                        elif response.status_code == 200:
                            no_broken_links += 1
                    except:
                        broken_links += 1
            broken_links_ratio =  broken_links / (no_broken_links + broken_links) if (no_broken_links + broken_links) > 0 else 0
            return (broken_links_ratio, f"Metadata from VoID file: {all_obj_void}")
        elif isinstance(all_obj_sparql, list) and len(all_obj_sparql) > 0:
            broken_links = 0
            no_broken_links = 0
            for obj in all_obj_sparql:
                if utils.is_url(obj):
                    try:
                        response = requests.get(obj)
                        if response.status_code != 200:
                            broken_links += 1
                        elif response.status_code == 200:
                            no_broken_links += 1
                    except:
                        broken_links += 1
            broken_links_ratio =  broken_links / (no_broken_links + broken_links) if (no_broken_links + broken_links) > 0 else 0
            return (broken_links_ratio, f"Metadata from SPARQL endpoint: {all_obj_sparql}")
        elif isinstance(search_engine_metadata, dict):
            available_resources_count = 0
            unavailable_resources_count = 0

            # Check website link
            website_links = search_engine_metadata.get('website', [])
            if utils.is_url(website_links):
                try:
                    response = requests.get(website_links)
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

            broken_links_ratio = unavailable_resources_count / (available_resources_count + unavailable_resources_count) if (available_resources_count + unavailable_resources_count) > 0 else 0
            return (broken_links_ratio, f"Metadata from Search engine file: {resources}")

        return (1, "No metadata found in SPARQL endpoint, VoID file or search engine metadata")

    def robots_txt(self, resources, sparql_endpoint, website_url):
        if utils.is_url(sparql_endpoint):
            robots_url = sparql_endpoint.rstrip('/') + '/robots.txt'
            try:
                response = requests.get(robots_url)
                if response.status_code == 200:
                    return (1, robots_url)
                else:
                    return (0, robots_url)
            except Exception as e:
                return (0, str(e))
        if utils.is_url(website_url):
            robots_url = website_url.rstrip('/') + '/robots.txt'
            try:
                response = requests.get(robots_url)
                if response.status_code == 200:
                    return (1, robots_url)
                else:
                    return (0, robots_url)
            except Exception as e:
                return e
        for link in resources:
            if 'robots.txt' in link['path']:
                try:
                    response = requests.get(link['path'])
                    if response.status_code == 200:
                        return (1, link['path'])
                    else:
                        return (0, link['path'])
                except Exception as e:
                    return (0, str(e))
        return (0, "No robots.txt found")
    

    def common_formats_availability(self, idKG):
        resourcesDH = Aggregator.getOtherResources(idKG)
        resourcesDH = utils.insertAvailability(resourcesDH)
        metadata_media_type = utils.extract_media_type(resourcesDH)
        common_formats_availability = utils.check_common_acceppted_format(metadata_media_type)
        if common_formats_availability:
            return (1, metadata_media_type)
        else:    
            return (0, metadata_media_type)
    
    def check_authentication(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            try:
                response = requests.get(sparql_endpoint)
                if response.status_code == 200:
                    return (1, sparql_endpoint)
                elif response.status_code == 401:
                    return (0, sparql_endpoint)
            except Exception as e:
                return (0, str(e))
        else:
            return (0, "No SPARQL endpoint provided")
    
    def version(self, void_file_url, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            version_in_kg = query.get_version(sparql_endpoint)
            if isinstance(version_in_kg, list) and len(version_in_kg) > 0:
                return (1, version_in_kg)
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            version_in_void = VoIDAnalyses.get_version(void_file)
            if version_in_void != False:
                return (1, version_in_void)
        
        return (0, "No SPARQL endpoint or VoID file provided")

    def canonical_citation(self, void_file_url, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            identifier = query.get_identifier(sparql_endpoint)
            if isinstance(identifier, list) and len(identifier) > 0:
                return (1, identifier)
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            identifier = VoIDAnalyses.get_identifier(void_file)
            if identifier != False:
                return (1, identifier)
        
        return (0, "No SPARQL endpoint or VoID file provided")
    
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

    def image(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            image_in_kg = query.getImagesTriples(sparql_endpoint)
            total_resources_in_kg = query.count_res(sparql_endpoint)
            if isinstance(image_in_kg, int) and isinstance(total_resources_in_kg, int) and total_resources_in_kg > 0:
                image_ratio = image_in_kg / total_resources_in_kg
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


'''
    def data_lang_and_encode(self, sparql_endpoint, void_file_url, idKG):
        total_string, lang_string = query.get_string_literals(sparql_endpoint)

        # Encode on resources indexed in the search engine metadata
        resourcesDH = Aggregator.getOtherResources(idKG)
        if len(resourcesDH) > 0:
            resourcesDH = utils.insertAvailability(resourcesDH)
            metadata_media_type = utils.extract_media_type(resourcesDH)

        # Encode of the link in the VoID file
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            serialzation_formats = VoIDAnalyses.getSerializationFormats(void_file)
            total_dump = VoIDAnalyses.getDataDump(void_file)

        # Encode of the link in the SPARQL endpoint
        if utils.is_url(sparql_endpoint):
            dump_query = query.get_download_link(sparql_endpoint)
            serialzation_formats_query = query.checkSerialisationFormats(sparql_endpoint)
'''