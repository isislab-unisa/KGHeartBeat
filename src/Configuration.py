import json

def createConfiguration():
    with open('configuration.json','w') as f:
        print("The json file is created")
        data = {}
        name = []
        id = []
        sparql_url = []
        #name.append('museum')
        data["name"] = name
        data["id"] = id
        data["sparql_url"] = sparql_url
        data["rdf_dump_url"] = []
        data["include_profile"] = True
        data["max_parallel_kgs"] = 1
        json.dump(data,f)
