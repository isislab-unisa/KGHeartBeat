import os
import sys
import json
import pandas as pd
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from graphdb_pipeline import graphdb_interface
from API import Aggregator, AGAPI, CHeCloudAPI
from API.monitoring_requests import MonitoringRequests
import utils
from QualityDimensions.Accessibility4All import Accessibility4All
from QualityDimensions.DeafHearingAccessibility import DeafHearingAccessibility
from QualityDimensions.Accessibility4VisuallyImpaired import Accessibility4VisuallyImpaired
import query
import VoIDAnalyses

# ---------------------------------------------------------------------
# Optional: start from a specific KG ID (skip all before and including it)
# ---------------------------------------------------------------------
start_from_kg_id = "agrovoc"  # e.g., "kg_12345" or leave "" / None to process all
skip_mode = bool(start_from_kg_id)
skipping = True if skip_mode else False
# ---------------------------------------------------------------------

toAnalyze = []
kgFound = AGAPI.getIdByName('')
CHe_Cloud = CHeCloudAPI.getAllDatasetIDs()
monitoring_requests = MonitoringRequests()
kg_added_by_users = monitoring_requests.getIDs()

print(f"Number of KG found from AGAPI: {len(kgFound)}")
print(f"Number of KGs from monitoring requests: {len(kg_added_by_users)}")
print(f"Number of KGs from CHe Cloud: {len(CHe_Cloud)}")

toAnalyze = toAnalyze + kgFound + kg_added_by_users + CHe_Cloud

results = {}

for kg_id in toAnalyze:
    kg_identifier = kg_id[0]
    kg_name = kg_id[1]

    # Skip until reaching the specified start_from_kg_id
    if skipping:
        if kg_identifier == start_from_kg_id:
            skipping = False
        else:
            print(f"Skipping {kg_identifier} (before start point)")
            continue

    print(f"\nAnalyzing {kg_identifier} - {kg_name}")
    metadata = Aggregator.getDataPackage(kg_identifier)
    if metadata == False:
        print(f"Metadata not found for {kg_identifier}")
        continue

    sparql_endpoint_url = Aggregator.getSPARQLEndpoint(kg_identifier)
    resourcesDH = Aggregator.getOtherResources(kg_identifier)
    otResources = utils.toObjectResources(resourcesDH)
    file_void_url = utils.getUrlVoID(otResources)
    website_url = metadata['website']

    if not utils.is_url(file_void_url) and utils.is_url(website_url):
        file_void_url_wb = website_url.rstrip('/') + '/.well-known/void'
        try:
            file_void_availability = requests.get(file_void_url_wb, timeout=10)
            if file_void_availability.status_code != 200:
                file_void_url = False
            else:
                file_void_url = file_void_url_wb
                parsed_void = VoIDAnalyses.parseVoID(file_void_url)
                if parsed_void == False:
                    file_void_url = False
        except:
            file_void_url = False
    elif not utils.is_url(file_void_url) and not utils.is_url(website_url):
        file_void_url = False


    if utils.is_url(sparql_endpoint_url):
        available_sparql = bool(query.check_if_up(sparql_endpoint_url))
    # elif sparql_endpoint_url == False:
    #     print(f"SPARQL endpoint {sparql_endpoint_url} is not available.")
    #     resourcesDH = utils.insertAvailability(resourcesDH)
    #     for resource in resourcesDH:
    #         if resource.get("status") == "active" and resource.get("type") == "full_download" and (utils.check_common_acceppted_format(resource.get("format")) or utils.check_if_zipped_dump(resource.get("format")) or utils.url_points_to_graph_file(resource.get("path"))):
    #             print(f"Found active full download resource with accepted format: {resource.get('format')}")
    #             try:
    #                 rdf_file, archive_file = graphdb_interface.download_rdf(resource.get("path"))
    #                 graphdb_interface.create_repository()
    #                 graphdb_interface.load_rdf_dump(rdf_file)
    #                 sparql_endpoint_url = graphdb_interface.get_sparql_endpoint()
    #                 print(f"Started local GraphDB SPARQL endpoint at {sparql_endpoint_url}")
    #             except Exception as e:
    #                 print(f"Error while loading data dump into GraphDB{resource.get('path')}: {e}")
    #                 continue


    accessibility4all = Accessibility4All()

    # Metadata license
    license = Aggregator.getLicense(metadata)
    if not license and utils.is_url(sparql_endpoint_url):
        license_query = query.checkLicenseMR(sparql_endpoint_url)
        if isinstance(license_query, list) and len(license_query) > 0:
            license = license_query
    if not license and utils.is_url(file_void_url):
        void_file = VoIDAnalyses.parseVoID(file_void_url)
        if void_file != False:
            license = VoIDAnalyses.getLicense(void_file)
        else:
            license = False

    total_resources_in_kg = utils.run_with_timeout(query.fetch_subjects,args=(sparql_endpoint_url,), timeout=1800)
    if not isinstance(total_resources_in_kg, int):
        total_resources_in_kg = utils.run_with_timeout(query.count_res,args=(sparql_endpoint_url,), timeout=600)
    elif isinstance(total_resources_in_kg, int) and total_resources_in_kg > 0:
        total_resources_in_kg = utils.run_with_timeout(query.count_res,args=(sparql_endpoint_url,), timeout=600)
    print(f"Total resources in KG: {total_resources_in_kg}")

    results[kg_identifier] = {}
    results[kg_identifier]['sparql_endpoint'] = sparql_endpoint_url
    results[kg_identifier]['void_file'] = file_void_url
    results[kg_identifier]['image'] = accessibility4all.image(sparql_endpoint_url, total_resources_in_kg)
    results[kg_identifier]['data_lang'] = accessibility4all.data_lang(sparql_endpoint_url)
    results[kg_identifier]['metadata_lang'] = accessibility4all.metadata_lang(sparql_endpoint_url, file_void_url)

    deaf_hearing_accessibility = DeafHearingAccessibility()
    results[kg_identifier]['video'] = deaf_hearing_accessibility.video(sparql_endpoint_url, total_resources_in_kg)
    video_descriptions = deaf_hearing_accessibility.check_video_description_subtitles(sparql_endpoint_url)
    results[kg_identifier]['video_description_ratio'] = video_descriptions['description_ratio']
    results[kg_identifier]['video_subtitle_ratio'] = video_descriptions['subtitle_ratio']
    results[kg_identifier]['video_sign_language_ratio'] = video_descriptions['sign_language_ratio']
    audio_descriptions = deaf_hearing_accessibility.check_audio_description_subtitles(sparql_endpoint_url)
    results[kg_identifier]['audio_description_ratio'] = audio_descriptions['description_ratio']
    results[kg_identifier]['audio_subtitle_ratio'] = audio_descriptions['subtitle_ratio']
    results[kg_identifier]['audio_sign_language_ratio'] = audio_descriptions['sign_language_ratio']

    accessibility4visually_impaired = Accessibility4VisuallyImpaired()
    results[kg_identifier]['alt_image'] = accessibility4visually_impaired.alt_image(sparql_endpoint_url)
    results[kg_identifier]['audio_meta'] = accessibility4visually_impaired.audio_meta(sparql_endpoint_url, file_void_url, resourcesDH)
    results[kg_identifier]['audio'] = accessibility4visually_impaired.audio(sparql_endpoint_url, total_resources_in_kg)

    print(results[kg_identifier])

    # Save results incrementally
    with open('HumanAccessibility_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    df = pd.DataFrame.from_dict(results, orient='index')
    df.index.name = 'KG_ID'
    df.reset_index(inplace=True)
    df.to_csv('HumanAccessibility_results_verbose.csv', index=False)

    if isinstance(sparql_endpoint_url, str) and ('host.docker.internal' in sparql_endpoint_url or 'localhost' in sparql_endpoint_url):
        graphdb_interface.cleanup_all()

# Compute final score summary
score_rows = []
for kg_id_key, metrics in results.items():
    score_entry = {"KG_ID": kg_id_key}
    for metric, value in metrics.items():
        if metric in ['sparql_endpoint', 'void_file']:
            score_entry[metric] = value
        elif isinstance(value, tuple) and len(value) > 0:
            score_entry[metric] = value[0]
        else:
            score_entry[metric] = None
    score_rows.append(score_entry)

df_scores = pd.DataFrame(score_rows)
df_scores.to_csv('HumanAccessibility_results_scores.csv', index=False)
