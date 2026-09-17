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
        json.dump(data,f)
