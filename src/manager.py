from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import Configuration
from API import AGAPI
from API import Aggregator
from API import LODCloudAPI
import analyses as analyses
from JsonValidator import JsonValidator
from OutputCSV import OutputCSV
from score import Score
import utils
import gc
import time
import fromCSV_to_KG
import Graph
from API.monitoring_requests import MonitoringRequests
from evaluate_fairness import EvaluateFAIRness
from evaluate_human_centered_acc import EvaluateHumanCenteredAcc
from API import CHeCloudAPI
from API import YummyDataAPI
from API import WikidataAPI
from API import KGCatalogAPI
from API import GitHubEndpointFinder
useDB = False
# try :
#     import pymongo
#     from db_interface import DBinterface
#     useDB = True
# except:
#     useDB = False


def analyse_target(analysis_date, source, target_options, analysis_options):
    """Run all calculations for one independent KG without writing shared output."""
    start_analysis = time.time()
    with analyses.analysis_session(analysis_date, **target_options, **analysis_options) as kg:
        score = Score(kg, 20)
        total_score, normalized_score = score.getWeightedDimensionScore(1)
        kg.extra.score = float(f"{total_score:.3f}")
        kg.extra.normalizedScore = float(f"{normalized_score:.3f}")
        kg.extra.scoreObj = score

        evaluation = EvaluateFAIRness(kg)
        evaluation.evaluate_findability()
        evaluation.evaluate_availability()
        evaluation.evaluate_interoperability()
        evaluation.evaluate_reusability()
        evaluation.calculate_FAIR_score()
        kg.fairness = evaluation.fairness

        human_accessibility_evaluation = EvaluateHumanCenteredAcc(kg)
        kg.human_accessibility = human_accessibility_evaluation.evaluate_all()

    return source, kg, score, time.time() - start_analysis


def write_analysis_result(result, output_ids, analysis_date):
    """Write shared result files from the coordinator thread only."""
    source, kg, score, elapsed = result
    utils.write_time(source, elapsed, '--- Analysis', 'INFO', analysis_date)
    OutputCSV(kg, output_ids).writeRow(analysis_date)
    OutputCSV(kg, output_ids).writeRow(analysis_date, include_dimensions=True)
    print(f"KG score: {kg.extra.score}")
    if useDB:
        mongo_interface = DBinterface()
        mongo_interface.insert_quality_data(kg, score)
    del kg
    gc.collect()


def analyse_batch(targets, output_ids, analysis_date, analysis_options, max_parallel_kgs):
    """Analyse independent targets concurrently and persist each completed result."""
    if not targets:
        return
    print(f"Analysing {len(targets)} KG(s) with {max_parallel_kgs} worker(s)")
    with ThreadPoolExecutor(max_workers=max_parallel_kgs) as executor:
        futures = [
            executor.submit(analyse_target, analysis_date, source, target_options, analysis_options)
            for source, target_options in targets
        ]
        # Write a result as soon as its worker finishes; CSV row order therefore
        # reflects completion order rather than input order.
        for future in as_completed(futures):
            write_analysis_result(future.result(), output_ids, analysis_date)

try: #GET THE CONFIGURATION FILE AND CHEK IF IT IS VALID
    here = os.path.dirname(os.path.abspath(__file__))
    configFile = os.path.join(here,'configuration.json')
    with open(configFile,'r') as f:
        input = json.load(f)
    validator = JsonValidator(input)
    result = validator.validateJson()
    #result = JsonValidator.validate(input)
    if result:
        print(input)
        print("Given data JSON is Valid")
    else:
        print(input)
        raise SystemExit("Given JSON data is invalid")
except  FileNotFoundError:
    Configuration.createConfiguration()   #IF THE FILE DOESN'T EXISTS, WE CREATING IT
    try:
        with open('configuration.json','r') as f:
            input = json.load(f)
    except:
        print('Error')
        quit()

rdf_dump_urls = input.get('rdf_dump_url', [])
analysis_options = {'include_profile': input.get('include_profile', True)}
max_parallel_kgs = input.get('max_parallel_kgs', 1)
if 'triple_limit' in input:
    analysis_options['triple_limit'] = input['triple_limit']
if len(input.get('id')) == 0 and len(input.get('name')) == 0 and len(input.get('sparql_url')) == 0 and not rdf_dump_urls:
    print('You have not entered any KGs for analysis')

start = time.time()
LODCloudAPI.clear_metadata_cache()

toAnalyze = []
id = input.get('id')
tuple_id = []

if 'all' not in id:
    for input_id in id:
        tuple_id.append((input_id,''))

name = input.get('name')
if 'all' not in name:
    for i in range(len(name)): #IF NAME IS INDICATED WE RECOVER THE ID OF ALL KG FOUND
        kgFound = AGAPI.getIdByName(name[i])
        print(f"Number of KG found with keyword {name[i]}:{len(kgFound)}")
        toAnalyze = toAnalyze + kgFound

if (len(id) == 1 and 'all' in id) or (len(name) == 1 and 'all' in name) or (len(input.get('sparql_url')) == 1 and 'all' in input.get('sparql_url')): #SPECIAL INPUT, WE ANALYZE ALL KG DISCOVERABLE
    kgFound = AGAPI.getIdByName('')
    CHe_Cloud = CHeCloudAPI.getAllDatasetIDs()
    monitoring_requests = MonitoringRequests()
    kg_added_by_users = monitoring_requests.getIDs()
    kg_catalog = KGCatalogAPI.getAllDatasetIDs()
    wikidata_kg = WikidataAPI.getWikidataSPARQLEndpoint(include_metadata=True)
    wikidata_kg_ids = WikidataAPI.getAllDatasetIDs()
    print(f"Number of KG found from AGAPI: {len(kgFound)}")
    print(f"Number of KGs from monitoring requests: {len(kg_added_by_users)}")
    print(f"Number of KGs from CHe Cloud: {len(CHe_Cloud)}")
    print(f"Number of KGs from KGCatalog: {len(kg_catalog)}")
    print(f"Number of KGs from Wikidata: {len(wikidata_kg_ids)}")
    toAnalyze = toAnalyze + kgFound + kg_added_by_users + CHe_Cloud + kg_catalog + wikidata_kg_ids

toAnalyze = toAnalyze + tuple_id
before_deduplication = len(toAnalyze)
toAnalyze = Aggregator.deduplicate_datasets(toAnalyze)
print(
    f"Deduplicated KGs by ID, SPARQL endpoint, and RDF dump: "
    f"{before_deduplication} -> {len(toAnalyze)}"
)

# graph = Graph.check_for_the_KGs_graph()
# if graph:
#     need_to_update = Graph.cheks_for_changes_in_graph()
#     if need_to_update:
#         graph = Graph.buildGraph()
# else:
#     graph = Graph.buildGraph()

#PREPARING THE CSV FILE IN OUTPUT
filename = date.today()
filename = str(filename)
OutputCSV.writeHeader(filename)
OutputCSV.writeHeader(filename,include_dimensions=True)

catalog_targets = [
    (kg_id, {'idKG': kg_id, 'nameKG': kg_name})
    for kg_id, kg_name in toAnalyze
]
analyse_batch(catalog_targets, toAnalyze, filename, analysis_options, max_parallel_kgs)

sparql_urls = []
if (len(id) == 1 and 'all' in id) or (len(name) == 1 and 'all' in name) or (len(input.get('sparql_url')) == 1 and 'all' in input.get('sparql_url')):
    sparql_urls = YummyDataAPI.getSPARQLEndpointURLs()
    sparql_urls.extend(GitHubEndpointFinder.get_endpoint_urls_from_github())

sparql_urls.extend(url for url in input.get('sparql_url') if url != 'all')
analyzed_sparql_endpoints = Aggregator.get_sparql_endpoint_signatures(toAnalyze)
direct_sparql_urls = []
for url in dict.fromkeys(sparql_urls):
    canonical_url = Aggregator.canonical_resource_url(url)
    if canonical_url in analyzed_sparql_endpoints:
        print(f"Skipping direct SPARQL target already analyzed: {url}")
        continue
    direct_sparql_urls.append(url)

direct_targets = [(url, {'sparql_endpoint': url}) for url in direct_sparql_urls]
direct_targets.extend((url, {'rdf_dump': url}) for url in dict.fromkeys(rdf_dump_urls))

source_urls = [url for url, _ in direct_targets]
analyse_batch(direct_targets, source_urls, filename, analysis_options, max_parallel_kgs)

end = time.time()
save_path = os.path.join(here,'../Analysis results')
with open(f'{save_path}/performance-{filename}.txt','a') as file:
        file.write(f'\n--- Total time for analysis:{end-start}s ---')
        file.write(f'\n--- Total time for analysis:{(end-start) / 3600} hours ---')


fromCSV_to_KG.convert_to_kg_code_from_llm(filename + '_with_dimensions')
#fromCSV_to_KG.merge_kgs_to_single_kg()
