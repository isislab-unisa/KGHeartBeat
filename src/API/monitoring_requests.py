import json
import os

class MonitoringRequests:

    def __init__(self,data_path = './monitoring_requests/manually_added.json'):
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        data_path = os.path.abspath(os.path.join(base_dir, "..", "..", data_path)) 
        with open(data_path, 'r') as json_file:
            self.dataset_metadata = json.load(json_file)

    def getIDs(self):
        return list(self.dataset_metadata.keys())
    
    def getMetadata(self, id_kg):
        if id_kg in self.dataset_metadata:
            return self.dataset_metadata[id_kg]
        else: 
            return False
    
    def getSPARQLEndpoint(self, id_kg):
        if id_kg in self.dataset_metadata:
            return self.dataset_metadata[id_kg]['sparql']['access_url']
        else:
            return False
    
    def getOtherResources(self,id_kg):
        if id_kg in self.dataset_metadata:
            jsonFile = self.dataset_metadata[id_kg]
            if isinstance(jsonFile,dict):
                fullDownload = []
                example = []
                resources = []
                fullDownload = jsonFile.get('full_download')
                for i in range(len(fullDownload)):
                    d = fullDownload[i]
                    d['access_url'] = d.pop('download_url',None)  #RENAME THE KEY VALUE TO HAVE THE SAME NAME OF THE FIELD
                    d['type'] = 'full_download'
                example = jsonFile.get('example')
                otherDownload = jsonFile.get('other_download')
                resources = example + otherDownload + fullDownload
                for i in range (len(resources)):   #DELETING UNNECESSARY ELEMENT FROM THE DICTIONARY 
                    resources[i].pop('mirror',None)
                    resources[i].pop('status',None)
                    resources[i].pop('_id',None)
                    d = resources[i]
                    d['path'] = d['access_url']   #RENAME THE KEY VALUE TO HAVE THE SAME NAME OF THE FIELD IN THE DATAHUB METADATA
                    del d['access_url']
                    d['format'] = d.pop('media_type',None)
                return resources
            else:
                return False
        else:
            return False
    
    def getKeywords(self,id_kg):
        if id_kg in self.dataset_metadata:
            return self.dataset_metadata[id_kg]['keywords']
        else: 
            return False