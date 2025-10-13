import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from API import Aggregator, AGAPI, CHeCloudAPI
from API.monitoring_requests import MonitoringRequests 
import utils
import requests
from QualityDimensions.Accessibility4All import Accessibility4All
from QualityDimensions.DeafHearingAccessibility import DeafHearingAccessibility
from QualityDimensions.Accessibility4VisuallyImpaired import Accessibility4VisuallyImpaired
import query
import VoIDAnalyses
import json
import pandas as pd


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
    print(f"Analyzing {kg_id[0]} - {kg_id[1]}")
    metadata = Aggregator.getDataPackage(kg_id[0])
    if metadata == False:
        print(f"Metadata not found for {kg_id[0]}")
        continue
    sparql_endpoint_url = Aggregator.getSPARQLEndpoint(kg_id[0])
    resourcesDH = Aggregator.getOtherResources(kg_id[0])
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
    
    accessibility4all = Accessibility4All()
    # Metadata license
    license = Aggregator.getLicense(metadata)
    if not license and utils.is_url(sparql_endpoint_url):
        license_query = query.checkLicenseMR(sparql_endpoint_url)
        if isinstance(license_query, list) and len(license_query) > 0:
            license = license_query
    if not license and utils.is_url(file_void_url):
        license = VoIDAnalyses.getLicense(file_void_url)
    
    results[kg_id[0]] = {}
    results[kg_id[0]]['sparql_endpoint'] = sparql_endpoint_url
    results[kg_id[0]]['void_file'] = file_void_url
    results[kg_id[0]]['open_license'] = accessibility4all.open_license(license)
    results[kg_id[0]]['assistive_technologies'] = accessibility4all.assistive_technologies(sparql_endpoint_url, file_void_url)
    results[kg_id[0]]['webpage_status'] = accessibility4all.webpage_status(metadata['website'])
    results[kg_id[0]]['metadata_broken_links_rate'] = accessibility4all.metadata_broken_links_rate(metadata, sparql_endpoint_url, file_void_url, kg_id[0])
    results[kg_id[0]]['robots_txt'] = accessibility4all.robots_txt(metadata, sparql_endpoint_url, website_url)
    results[kg_id[0]]['common_format_availability'] = accessibility4all.common_formats_availability(kg_id[0])
    results[kg_id[0]]['check_authentication'] = accessibility4all.check_authentication(sparql_endpoint_url)
    results[kg_id[0]]['version'] = accessibility4all.version(file_void_url, sparql_endpoint_url)
    results[kg_id[0]]['canonical_citation'] = accessibility4all.canonical_citation(file_void_url, sparql_endpoint_url)
    results[kg_id[0]]['contact_point'] = accessibility4all.contact_point(metadata, sparql_endpoint_url, file_void_url)
    results[kg_id[0]]['image'] = accessibility4all.image(sparql_endpoint_url)

    defhearing_accessibility = DeafHearingAccessibility()
    results[kg_id[0]]['example'] = defhearing_accessibility.examples(file_void_url, sparql_endpoint_url, metadata)
    results[kg_id[0]]['alternative_access_point'] = defhearing_accessibility.alternative_access_point(file_void_url, sparql_endpoint_url, kg_id[0])
    results[kg_id[0]]['human_redeable_labels'] = defhearing_accessibility.human_redeable_labels(sparql_endpoint_url)


    accessibility4visually_impaired = Accessibility4VisuallyImpaired()
    results[kg_id[0]]['alt_image'] = accessibility4visually_impaired.alt_image(sparql_endpoint_url)

    print(results[kg_id[0]])

    # Save results in JSON file
    with open('HumanAccessibility_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)

    # Save results in CSV file
    df = pd.DataFrame.from_dict(results, orient='index')
    df.index.name = 'KG_ID'
    df.reset_index(inplace=True)
    df.to_csv('HumanAccessibility_results_verbose.csv', index=False)
    
score_rows = []

for kg_id_key, metrics in results.items():
    score_entry = {"KG_ID": kg_id_key}
    for metric, value in metrics.items():
        if metric in ['sparql_endpoint', 'void_file']:
            print("Val",value)
            score_entry[metric] = value
        elif isinstance(value, tuple) and len(value) > 0:
            score_entry[metric] = value[0]
        else:
            score_entry[metric] = None 
    score_rows.append(score_entry)

df_scores = pd.DataFrame(score_rows)
df_scores.to_csv('HumanAccessibility_results_scores.csv', index=False)