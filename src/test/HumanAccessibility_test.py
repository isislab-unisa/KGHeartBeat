import os
import sys
import json
import pandas as pd
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
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
start_from_kg_id = ""  # e.g., "kg_12345" or leave "" / None to process all
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

    results[kg_identifier] = {}
    results[kg_identifier]['sparql_endpoint'] = sparql_endpoint_url
    results[kg_identifier]['void_file'] = file_void_url
    results[kg_identifier]['open_license'] = accessibility4all.open_license(license)
    results[kg_identifier]['webpage_status'] = accessibility4all.webpage_status(metadata['website'])
    results[kg_identifier]['check_authentication'] = accessibility4all.check_authentication(sparql_endpoint_url)
    results[kg_identifier]['metadata_broken_links_rate'] = accessibility4all.metadata_broken_links_rate(metadata, sparql_endpoint_url, file_void_url, kg_identifier)
    results[kg_identifier]['version'] = accessibility4all.version(file_void_url, sparql_endpoint_url)
    results[kg_identifier]['assistive_technologies'] = accessibility4all.assistive_technologies(sparql_endpoint_url, file_void_url)
    results[kg_identifier]['canonical_citation'] = accessibility4all.canonical_citation(file_void_url, sparql_endpoint_url, metadata)
    results[kg_identifier]['contact_point'] = accessibility4all.contact_point(metadata, sparql_endpoint_url, file_void_url)
    results[kg_identifier]['dump_size'] = accessibility4all.dump_size(file_void_url, sparql_endpoint_url, kg_identifier)
    results[kg_identifier]['image'] = accessibility4all.image(sparql_endpoint_url)
    results[kg_identifier]['human_redeable_labels'] = accessibility4all.human_redeable_labels(sparql_endpoint_url)
    results[kg_identifier]['robots_txt'] = accessibility4all.robots_txt(resourcesDH, sparql_endpoint_url, website_url)
    results[kg_identifier]['common_format_availability'] = accessibility4all.common_formats_availability(kg_identifier)
    results[kg_identifier]['example'] = accessibility4all.examples(file_void_url, sparql_endpoint_url, metadata)
    results[kg_identifier]['alternative_access_point'] = accessibility4all.alternative_access_point(file_void_url, sparql_endpoint_url, kg_identifier)
    results[kg_identifier]['description_readability'] = accessibility4all.description_readability(sparql_endpoint_url, file_void_url, Aggregator.getDescription(metadata))

    deaf_hearing_accessibility = DeafHearingAccessibility()
    results[kg_identifier]['image_metadata'] = deaf_hearing_accessibility.image_metadata(sparql_endpoint_url, file_void_url, resourcesDH)
    results[kg_identifier]['video_meta'] = deaf_hearing_accessibility.video_meta(sparql_endpoint_url, file_void_url, resourcesDH)
    results[kg_identifier]['video'] = deaf_hearing_accessibility.video(sparql_endpoint_url)
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
    results[kg_identifier]['audio'] = accessibility4visually_impaired.audio(sparql_endpoint_url)

    print(results[kg_identifier])

    # Save results incrementally
    with open('HumanAccessibility_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    df = pd.DataFrame.from_dict(results, orient='index')
    df.index.name = 'KG_ID'
    df.reset_index(inplace=True)
    df.to_csv('HumanAccessibility_results_verbose.csv', index=False)

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
