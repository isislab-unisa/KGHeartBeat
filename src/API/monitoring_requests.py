import json
import os

class MonitoringRequests:

    def __init__(self,data_path = './monitoring_requests/manually_added.json'):
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        data_path = os.path.abspath(os.path.join(base_dir, "..", "..", data_path)) 
        with open(data_path, 'r') as json_file:
            self.dataset_metadata = json.load(json_file)

    def getIDs(self):
        dataset = []
        for key in self.dataset_metadata:
            dataset.append((key,self.dataset_metadata[key]['title']))
        return dataset
    
    def getMetadata(self, id_kg):
        if id_kg in self.dataset_metadata:
            return self.dataset_metadata[id_kg]
        else: 
            return False
    
    def getSPARQLEndpoint(self, id_kg):
        if id_kg in self.dataset_metadata:
            return self.dataset_metadata[id_kg]['sparql'][0]['access_url']
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
            return []
    
    def getExternalLinks(self,id_kg):
        if id_kg in self.dataset_metadata:
            jsonFile = self.dataset_metadata[id_kg]
            if isinstance(jsonFile,dict):
                links = jsonFile.get('links',0)
                if isinstance(links,list):
                    return links
                else:
                    return links
            else:
                return False
        else: 
            return False
    
    def getDOI(self,id_kg):
        if id_kg in self.dataset_metadata:
            if self.dataset_metadata[id_kg]['doi'] != '':
                return self.dataset_metadata[id_kg]['doi']
            else: 
                return False
        else: 
            return False