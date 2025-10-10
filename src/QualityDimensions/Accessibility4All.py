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
        # Case 1: all elements are '-'
        if all(license == '-' for license in kg_license):
            self.open_license_value = 0
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
                self.open_license_value = 1
            else:
                # Case 3: licenses are present but not recognized as open
                self.open_license_value = 0.5

            return self.open_license_value

        else:
            # Request failed
            return {"error": "Failed to retrieve license information"}

    def assistive_technologies(self, sparql_endpoint, void_file_url):
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            ass_tech_in_void = VoIDAnalyses.check_acc_feature(void_file)
        else:
            ass_tech_in_void = False
        if utils.is_url(sparql_endpoint):
            ass_tech_in_kg = query.check_acc_feature(sparql_endpoint)
            ass_tech_in_kg = 1 if isinstance(ass_tech_in_kg, list) and len(ass_tech_in_kg) > 0 else 0
        else:
            ass_tech_in_kg = False

        return 1 if ass_tech_in_void == True or ass_tech_in_kg == 1 else 0
    
    def webpage_status(self, website_url):
        try:
            response = requests.get(website_url)
            if response.status_code == 200:
                return 1
            else:
                return 0
        except:
            return 0

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
            return broken_links / (no_broken_links + broken_links) if (no_broken_links + broken_links) > 0 else 0
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
            return broken_links / (no_broken_links + broken_links) if (no_broken_links + broken_links) > 0 else 0
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

            return unavailable_resources_count / (available_resources_count + unavailable_resources_count) if (available_resources_count + unavailable_resources_count) > 0 else 0

        return 'No metadata objects found'

    def robots_txt(self, search_engine_metadata, sparql_endpoint, website_url):
        if utils.is_url(sparql_endpoint):
            robots_url = sparql_endpoint.rstrip('/') + '/robots.txt'
            try:
                response = requests.get(robots_url)
                if response.status_code == 200:
                    return 1
                else:
                    return 0
            except:
                return 0
        if utils.is_url(website_url):
            robots_url = website_url.rstrip('/') + '/robots.txt'
            try:
                response = requests.get(robots_url)
                if response.status_code == 200:
                    return 1
                else:
                    return 0
            except:
                return 0
        other_downlaoads = search_engine_metadata.get('other_downloads', [])
        for link in other_downlaoads:
            if 'robots.txt' in link['access_url']:
                try:
                    response = requests.get(link)
                    if response.status_code == 200:
                        return 1
                    else:
                        return 0
                except:
                    return 0
        return 0
    

    def common_formats_availability(self, idKG):
        resourcesDH = Aggregator.getOtherResources(idKG)
        resourcesDH = utils.insertAvailability(resourcesDH)
        metadata_media_type = utils.extract_media_type(resourcesDH)
        common_formats_availability = utils.check_common_acceppted_format(metadata_media_type)
        if common_formats_availability:
            return 1   
        else:    
            return 0
    
    def check_authentication(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            try:
                response = requests.get(sparql_endpoint)
                if response.status_code == 200:
                    return 1
                elif response.status_code == 401:
                    return 0
            except Exception as e:
                return f'Error accessig SPARQL endpoint: {e}'
        else:
            return 0
    
    def version(self, void_file_url, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            version_in_kg = query.get_version(sparql_endpoint)
            if isinstance(version_in_kg, list) and len(version_in_kg) > 0:
                return 1
        if utils.is_url(void_file_url):
            version_in_void = VoIDAnalyses.get_version(void_file_url)
            if version_in_void != False:
                return 1
        
        return 0

    def canonical_citation(self, void_file_url, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            identifier = query.get_identifier(sparql_endpoint)
            if isinstance(identifier, list) and len(identifier) > 0:
                return 1
        if utils.is_url(void_file_url):
            identifier = VoIDAnalyses.get_identifier(void_file_url)
            if identifier != False:
                return 1
        
        return 0
    
    def contact_point(self, search_engine_metadata, sparql_endpoint, void_file_url):
        contact_in_metadata = search_engine_metadata.get('contact_point', False)
        name = contact_in_metadata.get('name', False)
        email = contact_in_metadata.get('email', False)
        if (email and email != 'null') or (name and name != 'null'):
            return 1
        
        if utils.is_url(sparql_endpoint):
            contact_in_sparql = query.get_contact_point(sparql_endpoint)
            if isinstance(contact_in_sparql, list) and len(contact_in_sparql) > 0:
                return 1
        
        if utils.is_url(void_file_url):
            contact_in_void = VoIDAnalyses.get_contact_point(void_file_url)
            if isinstance(contact_in_void, list) and len(contact_in_void) > 0:
                return 1

        return 0

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