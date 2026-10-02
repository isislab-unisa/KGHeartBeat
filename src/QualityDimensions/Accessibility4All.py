import requests
import os
import sys
from urllib.parse import urlsplit
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

    def open_license(self, kg_license, kg_license_id=None):
        if kg_license == False and not kg_license_id:
            self.open_license_value = (0, kg_license)
            return self.open_license_value

        # Case 1: all elements are '-'
        if not kg_license_id and isinstance(kg_license, list) and len(kg_license) > 0 and all(license == '-' for license in kg_license):
            self.open_license_value = (0, kg_license)
            return self.open_license_value
        elif not kg_license_id and isinstance(kg_license, str) and kg_license == '-':
            self.open_license_value = (0, kg_license)
            return self.open_license_value

        # Retrieve the open license list from Open Knowledge Foundation
        url = "https://raw.githubusercontent.com/okfn/licenses/master/licenses/groups/all.json"
        response = requests.get(url)

        if response.status_code == 200:
            open_license_data = response.json()

            def normalize(url):
                """Canonicalize equivalent license URLs for registry matching."""
                if not isinstance(url, str) or not url.strip():
                    return None
                value = url.strip()
                parsed = urlsplit(value if "://" in value else f"https://{value}")
                host = (parsed.hostname or "").lower()
                # The Open Definition has historically appeared with or without www.
                if host in ("www.opendefinition.org", "opendefinition.org"):
                    host = "opendefinition.org"
                try:
                    port = parsed.port
                except ValueError:
                    return None
                if port and not ((parsed.scheme.lower() == "http" and port == 80)
                                 or (parsed.scheme.lower() == "https" and port == 443)):
                    host = f"{host}:{port}"
                path = parsed.path.rstrip("/")
                return f"{host}{path}"

            def normalize_id(value):
                if not isinstance(value, str) or not value.strip():
                    return None
                return value.strip().casefold().replace("_", "-")

            # Compare normalized forms so protocol, host alias, and trailing
            # slash differences do not turn a known open license into 0.5.
            okfn_urls = {
                normalized
                for license_data in open_license_data.values()
                if isinstance(license_data, dict)
                for normalized in [normalize(license_data.get("url"))]
                if normalized
            }
            okfn_ids = {
                normalized
                for license_data in open_license_data.values()
                if isinstance(license_data, dict)
                for normalized in [normalize_id(license_data.get("id"))]
                if normalized
            }

            license_values = kg_license if isinstance(kg_license, list) else [kg_license]
            license_ids = kg_license_id if isinstance(kg_license_id, list) else [kg_license_id]
            matched_by_url = any(normalize(value) in okfn_urls for value in license_values)
            matched_by_id = any(normalize_id(value) in okfn_ids for value in license_values + license_ids)
            if matched_by_url or matched_by_id:
                self.open_license_value = (1, kg_license if kg_license else kg_license_id)
            elif isinstance(kg_license, list) and len(kg_license) == 0 and not kg_license_id:
                self.open_license_value = (0, kg_license)  
            else:
                self.open_license_value = (0.5, kg_license if kg_license else kg_license_id)

            return self.open_license_value
        else:
            # Request failed
            return (0, "Failed to retrieve open license list")
        
    def webpage_status(self, search_engine_metadata, sparql_endpoint=None, void_file_url=None):
        checked = set()
        last_failure = None

        def check_webpages(urls):
            nonlocal last_failure
            for website_url in urls:
                if not utils.is_url(website_url) or website_url in checked:
                    continue
                checked.add(website_url)
                try:
                    response = requests.get(website_url, allow_redirects=True, timeout=10)
                    if 200 <= response.status_code < 400:
                        return (1, website_url)
                    last_failure = website_url
                except requests.RequestException as error:
                    last_failure = f"{website_url}: {error}"
            return None

        if isinstance(search_engine_metadata, dict):
            result = check_webpages([search_engine_metadata.get('website')])
            if result is not None:
                return result

        if utils.is_url(sparql_endpoint):
            webpages = query.get_kg_webpages(sparql_endpoint)
            if isinstance(webpages, list):
                result = check_webpages(webpages)
                if result is not None:
                    return result

        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            if void_file is not False:
                result = check_webpages(VoIDAnalyses.get_kg_webpages(void_file))
                if result is not None:
                    return result

        return (0, last_failure or "No KG webpage found in metadata, SPARQL endpoint, or VoID file")

    def check_authentication(self, sparql_endpoint):
        if utils.is_url(sparql_endpoint):
            try:
                response = requests.get(sparql_endpoint)
                if response.status_code == 200:
                    return (1, sparql_endpoint)
                elif response.status_code == 401:
                    return (0, sparql_endpoint)
                else:
                    return (0, f"{sparql_endpoint} (status: {response.status_code})")
            except Exception as e:
                return (0, str(e))
        else:
            return (0, "No SPARQL endpoint provided")


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

        links = []
        if isinstance(all_obj_void, list) and len(all_obj_void) > 0:
            broken_links = 0
            no_broken_links = 0
            for obj in all_obj_void:
                if utils.is_url(obj):
                    links.append(obj)
                    try:
                        response = requests.head(obj, timeout=5)
                        if response.status_code != 200:
                            broken_links += 1
                        elif response.status_code == 200:
                            no_broken_links += 1
                    except:
                        broken_links += 1
            broken_links_ratio =  (no_broken_links / (no_broken_links + broken_links)) if (no_broken_links + broken_links) > 0 else 0
            return (broken_links_ratio, f"Links from VoID file: {links}")
        elif isinstance(all_obj_sparql, list) and len(all_obj_sparql) > 0:
            broken_links = 0
            no_broken_links = 0
            for obj in all_obj_sparql:
                if utils.is_url(obj):
                    links.append(obj)
                    try:
                        response = requests.head(obj, timeout=5)
                        if response.status_code != 200:
                            broken_links += 1
                        elif response.status_code == 200:
                            no_broken_links += 1
                    except:
                        broken_links += 1
            broken_links_ratio =  (no_broken_links / (no_broken_links + broken_links)) if (no_broken_links + broken_links) > 0 else 0
            return (broken_links_ratio, f"Links from SPARQL endpoint: {links}")
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
            links = [res.get("path") for res in resources]
            broken_links_ratio = (available_resources_count / (available_resources_count + unavailable_resources_count)) if (available_resources_count + unavailable_resources_count) > 0 else 0
            return (broken_links_ratio, f"Links from search engine metadata: {links}")

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
            return (1, version)
        else:
            return (0, "No version found")

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
        def has_value(value):
            return isinstance(value, str) and value.strip().lower() not in ('', 'null')

        if isinstance(search_engine_metadata, dict):
            contact_in_metadata = search_engine_metadata.get('contact_point')
            if isinstance(contact_in_metadata, dict):
                if any(has_value(contact_in_metadata.get(field)) for field in ('name', 'email')):
                    return (1, contact_in_metadata)

        if utils.is_url(sparql_endpoint):
            contact_in_sparql = query.get_contact_point(sparql_endpoint)
            if isinstance(contact_in_sparql, list):
                contacts = [contact for contact in contact_in_sparql if has_value(contact)]
                if contacts:
                    return (1, contacts)

        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            if void_file is not False:
                contact_in_void = VoIDAnalyses.get_contact_point(void_file)
                if has_value(contact_in_void):
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
            dumps.append(dump)
            if utils.is_url(dump):
                size = utils.estimate_file_size_gb(dump)
                if isinstance(size, float) and size < 0.500:
                    small_dump = True
                elif isinstance(size, float) and 0.500 <= size < 4:
                    medium_dump = True
                elif isinstance(size, float) and size >= 4:
                    large_dump = True

        if utils.is_url(sparql_endpoint):
            sparql_dumps = query.get_download_link(sparql_endpoint)
            if isinstance(sparql_dumps, list):
                for dump_link in sparql_dumps[0:100]:
                    print(f"Processing link {dump_link}")
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
            return (0.5, dumps)
        elif large_dump:
            return (0, dumps)
        elif len(dumps) == 0:
            return (0, "No data dumps found")
        elif len(dumps) > 0 and not small_dump and not medium_dump and not large_dump:
            return (0, f"Unknown dump size for: {dumps}")

    # TODO: move to extension format
    def image(self, sparql_endpoint, total_resources_in_kg):
        if utils.is_url(sparql_endpoint):
            image_in_kg = query.getImageIri(sparql_endpoint)
            if isinstance(image_in_kg, list) and isinstance(total_resources_in_kg, int) and total_resources_in_kg > 0:
                image_ratio = len(image_in_kg) / total_resources_in_kg
                return (image_ratio, "Number of images in the KG: " + str(len(image_in_kg)))
            elif isinstance(image_in_kg, list):
                return (0, "Number of images in the KG: " + str(len(image_in_kg)))
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
            if isinstance(num_res, int) and num_res > 0:
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
            path = link.url
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
        if isinstance(search_engine_metadata, dict):
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
            readability_score = min(1, max(0, (55 - utils.lix_score(description)) / 30))
            return readability_score, f"Description from search engine metadata: {description}"

        if utils.is_url(sparql_endpoint_url):
            description_sparql = query.getDescription(sparql_endpoint_url)
            if isinstance(description_sparql, list) and len(description_sparql) > 0:
                description = description_sparql[0]
                if isinstance(description, str):
                    readability_score = min(1, max(0, (55 - utils.lix_score(description)) / 30))
                    return readability_score, f"Description from SPARQL metadata: {description}"

        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            description_void = VoIDAnalyses.getDescription(void_file)
            if isinstance(description_void, list) and len(description_void) > 0:
                description = description_void[0]
                readability_score = min(1, max(0, (55 - utils.lix_score(description)) / 30))
                return readability_score, f"Description from VoID file: {description}"

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
        """Score language-tagged metadata triples divided by all metadata triples."""
        errors = []
        if utils.is_url(sparql_endpoint_url):
            counts = query.get_metadata_language_counts(sparql_endpoint_url)
            if isinstance(counts, tuple) and counts[0] > 0:
                total, tagged = counts
                return round(tagged / total, 2), (
                    f"Metadata with language tags: {tagged}/{total} (SPARQL endpoint)"
                )
            errors.append(f"Error querying SPARQL endpoint: {counts}" if not isinstance(counts, tuple)
                          else "No dataset metadata found in SPARQL endpoint")

        if utils.is_url(void_file):
            graph = VoIDAnalyses.parseVoID(void_file)
            if graph is not False:
                total, tagged = VoIDAnalyses.getMetadataLanguageCounts(graph)
                if total > 0:
                    return round(tagged / total, 2), (
                        f"Metadata with language tags: {tagged}/{total} (VoID file)"
                    )
                errors.append("No dataset metadata found in VoID file")
            else:
                errors.append("Error parsing VoID file")

        return 0, "; ".join(errors) if errors else (
            "No SPARQL endpoint or VoID file provided to check languages in the metadata"
        )

#aa = Accessibility4All()
#print(aa.metadata_lang("https://dbpedia.org/sparql"))
