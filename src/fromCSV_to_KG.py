import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS, FOAF
import os
import csv
from itertools import islice    
from langchain_core.prompts import PromptTemplate
from from_kg_to_csv.prompt_llms  import PromptLLMS
from from_kg_to_csv.evaluate_answer import EvaluateKG
from datetime import datetime
from pathlib import Path

ontology_path = './Generate KG from csv (ESWC Workshop)/dqv.ttl'
kg_as_example_path = './Generate KG from csv (ESWC Workshop)/Full/cz-nace-full.ttl'

#Function to split in block the CSV file
def read_csv_in_blocks(filename, block_dimension = 10):
    with open(f'../Analysis results/{filename}.csv', mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)
        while True:
            block = list(islice(reader, block_dimension))
            if not block:
                break
            yield header, block


def convert_to_kg_with_llms(filename,block_dimension):
    # Read and trasfromt the ttl ontology into text
    with open(ontology_path) as f:
        ttl_text = f.read() + '\n'

    # Read and trasform the ttl KG in a string
    with open(kg_as_example_path) as f:
        kg_as_example = f.read() + '\n'
    
    final_kg = ''
    #Read the CSV in blocks of size block_dimension
    #One KG at a time could take too many API calls and instead too many KGs at a time could lead to exceeding the character limit, 
    # need to balance according to llms
    for header, block in read_csv_in_blocks(filename,block_dimension):
        header = ", ".join(header)
        block_to_llm = header + '\n'
        for row in block:
            row = ", ".join(row)
            block_to_llm += row + '\n'
        one_shot_prompt = PromptTemplate(
            input_variables=["csv_title","csv_content","ontology_content","kg_example"],
            template='''Consider the following csv entitled "{csv_title}".csv: {csv_content} \n
            Consider the following ontology in ttl format entitled "dqv.ttl": {ontology_content} \n
            Let's consider that the CSV file contains all dimensions concerning the trust category and for each dimension, the file details its metrics. To distinguish metrics and dimension, consider that all the file column names follow the pattern of DIMENSION_METRIC. 
            With these premises, can you model the data contained in csv file according to the "dqv.ttl" ontology and return the complete and detailed set of resulting triples in rdf format? Below I show you an example for cz-nace, do the same for the remaining KGs in the CSV file: \n
            {kg_example}
            \nReturn me only ttl code, don't add more.
            '''
        )

        llms = PromptLLMS(one_shot_prompt,filename,block_to_llm,ttl_text,kg_as_example_path)

        kg_generated_gemini = llms.execute_on_gemini()
        #kg_generated_gpt4 = llms.execute_on_gpt_4()
        kg_generated_gemini = kg_generated_gemini.replace('`','')

        #Evaluate Gemini
        evaluated_kg_gemini = EvaluateKG(kg_generated_gemini,'Gemini 1.5 pro')
        evaluated_kg_gemini.execute_evaluation(block_dimension,20,100)

        #Evaluate GPT-4o
        #evaluated_kg_gpt4o = EvaluateKG(kg_generated_gpt4,'GPT-4o')
        #evaluated_kg_gpt4o.execute_evaluation(block_dimension,20,100)

        #Find best answare compare the different evaluation from the different LLMs snd return the best soluzione (takes a list of ecaluated_kg and returns the bes evaluated_kg obj) 
        #kg_to_use = EvaluateKG.find_the_best_answer([kg_generated_gemini,kg_generated_gpt4])
        final_kg += evaluated_kg_gemini.kg_from_llm

    #At the end, put toghether all the KGs snippet and serialize the .ttl file
    #Clean result to avoid incorrect parsing
    final_kg = final_kg.replace('turtle','')
    final_kg = final_kg.replace('ttl','')
    print(final_kg)
    g = Graph()
    g.parse(data=final_kg, format="turtle")
    g.serialize(destination=f"../Analysis results/{filename.split('_')[0]}.ttl", format="turtle")


def convert_to_kg_code_from_llm(filename):
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'../Analysis results')

    # Define namespaces
    DQV = Namespace("http://www.w3.org/ns/dqv#")
    DCAT = Namespace("http://www.w3.org/ns/dcat#")
    SDMX = Namespace("http://purl.org/linked-data/sdmx/2009/attribute#")
    SDMX_CODE = Namespace("http://purl.org/linked-data/sdmx/2009/code#")
    PROV = Namespace("http://www.w3.org/ns/prov#")

    # Read the CSV file
    df = pd.read_csv(f"{save_path}/{filename}.csv")

    analysis_date = filename.split('_')[0]
    date_obj = datetime.strptime(analysis_date, "%Y-%m-%d")
    # Format as ISO 8601 with time set to 00:00:00Z
    iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Initialize graph
    g = Graph()

    # Bind namespaces
    g.bind("dqv", DQV)
    g.bind("dcat", DCAT)
    g.bind("sdmx", SDMX)
    g.bind("sdmx-code", SDMX_CODE)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)
    g.bind("prov", PROV)

    # Define some common URIs
    vocabulary_uri = URIRef("http://www.w3.org/ns/dqv")
    g.add((vocabulary_uri, RDF.type, URIRef("http://purl.org/vocommons/voaf#Vocabulary")))
    g.add((vocabulary_uri, DCTERMS.title, Literal("Data Quality Vocabulary", lang="en")))
    g.add((vocabulary_uri, DCTERMS.description, Literal("The Data Quality Vocabulary (DQV) is seen as an extension to DCAT to cover the quality of the data...", lang="en")))
    g.add((vocabulary_uri, DCTERMS.created, Literal("2015-12-17", datatype=XSD.date)))
    g.add((vocabulary_uri, DCTERMS.modified, Literal("2016-08-26", datatype=XSD.date)))
    g.add((vocabulary_uri, DCTERMS.publisher, URIRef("http://www.w3.org/data#W3C")))
    g.add((vocabulary_uri, DCTERMS.type, URIRef("http://purl.org/adms/assettype/Ontology")))

    # Generate info about the Quality assessment tool
    kgheartbeat_uri = URIRef("http://example.org/assessment-tool/KGHeartBeat")

    g.add((kgheartbeat_uri, RDF.type, PROV.SoftwareAgent))
    g.add((kgheartbeat_uri, RDFS.label, Literal('A KG quality assessment tool',lang="en")))

    # Process each row in the dataframe
    for _, row in df.iterrows():
        kg_name = row['kg_name']
        kg_id = row['kg_id']
        kg_id = str(kg_id)
        kg_id = kg_id.strip()
        kg_name = str(kg_name)
        kg_name = kg_name.strip()
        kg_id = kg_id.replace(' ','_')
        kg_name = kg_name.replace(' ','_')
        dataset_uri = URIRef(f"http://example.org/dataset/{kg_id}")

        g.add((dataset_uri, RDF.type, DCAT.Dataset))
        g.add((dataset_uri, DCTERMS.title, Literal(kg_name)))
        g.add((dataset_uri, DCTERMS.identifier, Literal(kg_id)))
        #g.add((dataset_uri, DCTERMS.date, Literal(analysis_date, datatype=XSD.date)))

        # Iterate over columns to generate quality measurements
        for column in df.columns:
            if column in ['kg_name', 'kg_id']:
                continue
            
            if '_' in column:
                dimension, metric = column.split('_', 1)
                dimension_uri = URIRef(f"http://example.org/dimension/{dimension}")
                metric_uri = URIRef(f"http://example.org/metric/{metric}")
                observation_uri = URIRef(f"http://example.org/observation/{kg_id}/{column}_{analysis_date}")
                
                # Add dimension and metric to graph
                g.add((dimension_uri, RDF.type, DQV.Dimension))
                g.add((dimension_uri, RDFS.label, Literal(dimension, lang="en")))
                g.add((metric_uri, RDF.type, DQV.Metric))
                g.add((metric_uri, RDFS.label, Literal(metric, lang="en")))
                g.add((metric_uri, DQV.inDimension, dimension_uri))

                # Add observation to graph
                g.add((observation_uri, RDF.type, DQV.QualityMeasurement))
                g.add((observation_uri, DQV.isMeasurementOf, metric_uri))
                g.add((observation_uri, DQV.computedOn, dataset_uri))
                g.add((observation_uri, PROV.generatedAtTime, Literal(iso_date, datatype=XSD.dateTime)))
                g.add((observation_uri, PROV.wasAttributedTo, kgheartbeat_uri))

                value = row[column]
                value = value.replace("\n", " ").strip() 
                value = value.replace('"',' ')
                value = value.replace("'",' ')
                try:
                    value = float(value.replace(',', '.'))
                except ValueError:
                    pass

                if isinstance(value, float):
                    g.add((observation_uri, DQV.value, Literal(value, datatype=XSD.double)))
                elif isinstance(value, int):
                    g.add((observation_uri, DQV.value, Literal(value, datatype=XSD.integer)))
                elif isinstance(value, bool):
                    g.add((observation_uri, DQV.value, Literal(value, datatype=XSD.boolean)))
                else:
                    g.add((observation_uri, DQV.value, Literal(value, datatype=XSD.string)))

            # Process score columns
            else:
                score_uri = URIRef(f"http://example.org/score/{column}")
                score_observation_uri = URIRef(f"http://example.org/observation/{kg_id}/{column}_{analysis_date}")

                g.add((score_uri, RDF.type, DQV.Metric))
                g.add((score_uri, RDFS.label, Literal(column, lang="en")))

                g.add((score_observation_uri, RDF.type, DQV.QualityMeasurement))
                g.add((score_observation_uri, DQV.isMeasurementOf, score_uri))
                g.add((score_observation_uri, DQV.computedOn, dataset_uri))
                g.add((score_observation_uri, PROV.generatedAtTime, Literal(iso_date, datatype=XSD.dateTime)))
                g.add((score_observation_uri, PROV.wasAttributedTo, kgheartbeat_uri))

                score_value = row[column]
                if isinstance(score_value, str):
                    try:
                        score_value = float(score_value.replace(',', '.'))
                    except ValueError:
                        pass

                if isinstance(score_value, float):
                    g.add((score_observation_uri, DQV.value, Literal(score_value, datatype=XSD.double)))
                elif isinstance(score_value, int):
                    g.add((score_observation_uri, DQV.value, Literal(score_value, datatype=XSD.integer)))
                elif isinstance(score_value, bool):
                    g.add((score_observation_uri, DQV.value, Literal(score_value, datatype=XSD.boolean)))
                else:
                    g.add((score_observation_uri, DQV.value, Literal(score_value, datatype=XSD.string)))

    # Serialize the graph to a file
    g.serialize(destination=f"{save_path}/{filename.split('_')[0]}.ttl", format="turtle")
    os.remove(f'{save_path}/{filename}.csv')
    os.chmod(f"{save_path}/{filename.split('_')[0]}.ttl", 0o644)

def merge_kgs_to_single_kg(output_file=False):
    """
    Merge RDF files containing observations into a single file, keeping prefixes only once.
    Writes output line by line to reduce memory consumption.
    
    Args:
        output_file (str): Path to the output merged file
    """
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here, '../Analysis results')

    if os.path.exists(f'{save_path}/KGHeartBeat_KG.ttl'):
        os.remove(f'{save_path}/KGHeartBeat_KG.ttl')

    if not output_file:
        output_file = os.path.join(save_path, 'KGHeartBeat_KG.ttl')
    
    observation_pattern = "<http://example.org/observation/"
    files = sorted(Path(save_path).glob('*.ttl'), reverse=True)
    
    if not files:
        return
    
    # Copy the most recent file as the base
    most_recent_file = files[0]
    
    with open(most_recent_file, "rb") as f_in, open(output_file, "wb") as f_out:
        f_out.write(f_in.read())
    
    # Append only observations from older files
    with open(output_file, "ab") as f_out:
        for file_path in files[1:]:
            print(f"Processing {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f_in:
                buffer = []
                inside_observation = False
                for line in f_in:
                    stripped_line = line.strip()
                    if stripped_line.startswith(observation_pattern):
                        inside_observation = True
                        buffer = [stripped_line]
                    elif inside_observation:
                        buffer.append(stripped_line)
                        if stripped_line.endswith("."):
                            f_out.write("\n".join(buffer).encode("utf-8") + b"\n")
                            f_out.write(b"\n")
                            inside_observation = False