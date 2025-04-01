import json
import os
import string
import networkx as nx
from API import AGAPI
from API import Aggregator
import utils
from networkx.readwrite import json_graph
import re
import pickle
import datetime

def buildGraph():
    print('Bulding graph with all the KGs...')
    allKg = AGAPI.getAllKg()
    idList = []
    G = nx.Graph()
    for i in range(len(allKg)):
        element = allKg[i]
        id = element.get('id')
        idList.append(id)
    for j in range(len(idList)):
        externalLinks = Aggregator.getExternalLinks(idList[j])
        exLinksObj = utils.toObjectExternalLinks(externalLinks)
        print(f'Bulding the neighbors of {idList[j]}')
        if isinstance(exLinksObj,list) and len(exLinksObj) > 0:
            for k in range(len(exLinksObj)):
                link = exLinksObj[k]
                value = str(link.value)
                value = re.sub("[^\d\.]", "",value)
                if value == '':
                    value = 0
                value = int(value)
                G.add_edge(idList[j],link.nameKG,weight=value)
        else:
            G.add_node(idList[j])
    here = os.path.dirname(os.path.abspath(__file__))
    gFile = os.path.join(here,'GraphOfKG.gpickle') #GET PATH OF CURRENT WORKING DIRECTORY
    outfile = open(gFile,'wb')
    pickle.dump(G,outfile) #STORE IT ON DISK

    return G

def getPageRank(graph,idKg):
    try:
        pr = nx.pagerank(graph)
        return pr.get(idKg)
    except:
        return '-'

def getDegreeOfConnection(graph,idKg):
    try:
        degree = graph.degree(nbunch=idKg)
        return degree
    except:
        return '-'

def getCentrality(graph,idKg):
    try:
        degreeCentrality = nx.degree_centrality(graph)
        return degreeCentrality.get(idKg)
    except:
        return '-'

def getClusteringCoefficient(graph,idKG):
    try:
        clusteringCoefficient = nx.clustering(graph,idKG)
        return clusteringCoefficient
    except:
        return '-'

def getSubgraph(graph,nodeList):
    subG = graph.subgraph(nodeList)
    return subG

def storeAsJSON(subG):
    here = os.path.dirname(os.path.abspath(__file__))
    subGfile = os.path.join(here,'./docs/subGraph.json')
    with open(subGfile,'w',encoding="utf-8") as f:
        f.write(json.dumps(json_graph.node_link_data(subG)))

def storeEdges(graph,nodelist):
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'./docs/Subgraphs')
    for i in range(len(nodelist)):
        newFilename = re.sub(r'[\\/*?:"<>|]',"",nodelist[i])
        remove_punctuation_map = dict((ord(char), None) for char in '\/*?:"<>|')
        newFilename = newFilename.translate(remove_punctuation_map)
        remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
        newFilename = newFilename.translate(remove_punctuation_map)
        completeName = os.path.join(save_path, newFilename+".txt")
        e = graph.edges(nodelist[i])
        e = str(e)
        e = e.replace('(','[')
        e = e.replace(')',']')
        e = e.replace("'",'"')
        with open(completeName,'w',encoding="utf-8") as f:
            f.write(e)

def check_for_the_KGs_graph():
    try:
        here = os.path.dirname(os.path.abspath(__file__))
        gFile = os.path.join(here,'GraphOfKG.gpickle') #GET PATH OF CURRENT WORKING DIRECTORY
        infile = open(gFile,'rb')
        graph = pickle.load(infile)
        infile.close()
        
        return graph
    except FileNotFoundError: 
        return False

def cheks_for_changes_in_graph():
    '''
        Check if the file was written more than a month ago, if yes update it.
    '''
    here = os.path.dirname(os.path.abspath(__file__))
    gFile = os.path.join(here,'GraphOfKG.gpickle')
    modification_time = os.path.getmtime(gFile)
    modification_date = datetime.datetime.fromtimestamp(modification_time)
    current_date = datetime.datetime.now()
    if (current_date - modification_date).days > 30:
        return True
    else:
        return False