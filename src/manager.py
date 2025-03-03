from datetime import date
import json
import os
import Configuration
from API import AGAPI
import analyses as analyses
from JsonValidator import JsonValidator
from OutputCSV import OutputCSV
from score import Score
import utils
import gc
import time
import fromCSV_to_KG 
import Graph

useDB = False
# try : 
#     import pymongo
#     from db_interface import DBinterface
#     useDB = True
# except: 
#     useDB = False

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
        print("Given JSON data is invalid")
except  FileNotFoundError:
    Configuration.createConfiguration()   #IF THE FILE DOESN'T EXISTS, WE CREATING IT 
    try:
        with open('configuration.json','r') as f:
            input = json.load(f)
    except:
        print('Error')
        quit()

if len(input.get('id')) == 0 and len(input.get('name')) == 0 and len(input.get('sparql_url')) == 0:
    print('You have not entered any KGs for analysis')
 
start = time.time()

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
    print(f"Number of KG found: {len(kgFound)}")
    toAnalyze = toAnalyze + kgFound

toAnalyze = toAnalyze + tuple_id
toAnalyze = list(dict.fromkeys(toAnalyze)) #CLEAN THE LIST FROM DUPLICATES

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

for i in range(len(toAnalyze)):
    start_analysis = time.time()
    kg = analyses.analyses(idKG=toAnalyze[i][0],analysis_date=filename,nameKG=toAnalyze[i][1])
    score = Score(kg,20)
    totalScore,normalizedScore = score.getWeightedDimensionScore(1)
    totalScore = "%.3f"%totalScore
    normalizedScore = "%.3f"%normalizedScore
    totalScore = float(totalScore)
    normalizedScore = float(normalizedScore)
    kg.extra.score = totalScore
    kg.extra.normalizedScore = normalizedScore
    kg.extra.scoreObj = score
    end_analysis = time.time()
    utils.write_time(toAnalyze[i][0],end_analysis-start_analysis,'--- Analysis','INFO',filename)
    csv = OutputCSV(kg,toAnalyze)
    csv_with_dim = OutputCSV(kg,toAnalyze)
    csv.writeRow(filename)
    csv_with_dim.writeRow(filename,include_dimensions=True)
    print(f"KG score: {kg.extra.score}")
    if(useDB == True):
        mongo_interface = DBinterface()
        mongo_interface.insert_quality_data(kg,score)
    del csv
    del kg
    gc.collect()
    #print(kg.getQualityKG()) #PRINT THE KG QUALITY ON THE COMAND LINE

if len(input.get('sparql_url')) > 0 and not 'all' in input.get('sparql_url'):
    sparql_urls = input.get('sparql_url')
    for sparql_url in sparql_urls:
        start_analysis = time.time()
        kg = analyses.analyses(filename,sparql_endpoint=sparql_url)
        score = Score(kg,20)
        totalScore,normalizedScore = score.getWeightedDimensionScore(1)
        totalScore = "%.3f"%totalScore
        normalizedScore = "%.3f"%normalizedScore
        totalScore = float(totalScore)
        normalizedScore = float(normalizedScore)
        kg.extra.score = totalScore
        kg.extra.normalizedScore = normalizedScore
        kg.extra.scoreObj = score
        end_analysis = time.time()
        utils.write_time(sparql_url,end_analysis-start_analysis,'--- Analysis','INFO',filename)
        csv = OutputCSV(kg,sparql_urls)
        csv_with_dim = OutputCSV(kg,sparql_urls)
        csv.writeRow(filename)
        csv_with_dim.writeRow(filename,include_dimensions=True)
        print(f"KG score: {kg.extra.score}")
        if(useDB == True):
            mongo_interface = DBinterface()
            mongo_interface.insert_quality_data(kg,score)
        del csv
        del kg
        gc.collect()

if len(input.get('sparql_url')) > 0:
    sparql_urls = input.get('sparql_url')
    for sparql_url in sparql_urls:
        start_analysis = time.time()
        kg = analyses.analyses(filename,sparql_endpoint=sparql_url)
        score = Score(kg,20)
        totalScore,normalizedScore = score.getWeightedDimensionScore(1)
        totalScore = "%.3f"%totalScore
        normalizedScore = "%.3f"%normalizedScore
        totalScore = float(totalScore)
        normalizedScore = float(normalizedScore)
        kg.extra.score = totalScore
        kg.extra.normalizedScore = normalizedScore
        kg.extra.scoreObj = score
        end_analysis = time.time()
        utils.write_time(sparql_url,end_analysis-start_analysis,'--- Analysis','INFO',filename)
        csv = OutputCSV(kg,sparql_urls)
        csv_with_dim = OutputCSV(kg,sparql_urls)
        csv.writeRow(filename)
        csv_with_dim.writeRow(filename,include_dimensions=True)
        print(f"KG score: {kg.extra.score}")
        if(useDB == True):
            mongo_interface = DBinterface()
            mongo_interface.insert_quality_data(kg,score)
        del csv
        del kg
        gc.collect()

end = time.time()
save_path = os.path.join(here,'../Analysis results')
with open(f'{save_path}/performance-{filename}.txt','a') as file:
        file.write(f'\n--- Total time for analysis:{end-start}s ---')
        file.write(f'\n--- Total time for analysis:{(end-start) / 3600} hours ---')


fromCSV_to_KG.convert_to_kg_code_from_llm(filename + '_with_dimensions')
#fromCSV_to_KG.merge_kgs_to_single_kg()
