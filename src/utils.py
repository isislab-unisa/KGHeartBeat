from ast import Str
from importlib.metadata import requires
import itertools
from operator import truediv
import os
from pathlib import Path
from socket import timeout
import ssl
from typing import Dict
from xml.dom.minidom import Document, parseString
from xml.dom.minidom import parseString
from SPARQLWrapper import *
from SPARQLWrapper import SPARQLWrapper
import requests
import time
import mechanize
from twill.commands import browser
import query
from Resources import Resources
from ExternalLink import ExternalLink
import networkx as nx
import re
import validators
import shutil
import urllib.request
from urllib.parse import urlparse
import json
import ssl


#PRINT THE METADATI OF A KG
def printMetadatiKG(metadct):
    for key, value in metadct.items() :
        print (key, value)

#PRINT THE KGs
def printKGs(kgs):
    print(*kgs, sep = "\n \n \n")

#PRINT KGs WITH NAME AND DESCRIPTION
def printNameKGs(kgs):
    for x in range(len(kgs)): 
        element = kgs[x]
        name = element.get('title')
        description = element.get('description')
        print('Name: %s  \nDescription: %s  \n \n' %(name, description))

def getNameKG(kg):
    name = kg.get('title')
    return name

def getIdKG(metadata):
    id = metadata.get('id')
    return id

def getResultsFromJSON(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('o')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONo(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('o')
            if isinstance(object,dict):
                value = object.get('value')
                resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONp(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('p')
            if isinstance(object,dict):
                value = object.get('value')
                resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONs(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('s')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONMin(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('min')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONMax(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('max')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONCount(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('triples')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    resultsList.append(value)
        return resultsList
    else:
        return False

def getResultsFromJSONCountInt(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('triples')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    return int(value)
                else:
                    return 'absent'
    else:
        return False

def getResultsFromJSONCountIntT(results):
    result = results.get('results')
    bindings = result.get('bindings')
    if isinstance(bindings,list):
        resultsList = []
        for i in range(len(bindings)):
            object = bindings[i].get('t')
            if isinstance(object,dict):
                value = object.get('value')
                if (not value == ''):
                    return int(value)
                else:
                    return 'absent'
    else:
        return False

def getResultsFromXML(results):
    if isinstance(results,Document): #IF RESULT IS IN XML 
        li = []
        literalList = results.getElementsByTagName('literal')
        numTags = results.getElementsByTagName("literal").length
        for i in range(numTags):
            if literalList[i].firstChild is not None:
                literal = literalList[i].firstChild.nodeValue
                li.append(literal)
        literalList = results.getElementsByTagName('uri')
        numTags = results.getElementsByTagName("uri").length
        for i in range(numTags):
            if literalList[i].firstChild is not None:
                literal = literalList[i].firstChild.nodeValue
                li.append(literal)
        return li

def getResultsFromXMLUri(results):
    if isinstance(results,Document): #IF RESULT IS IN XML 
        li = []
        literalList = results.getElementsByTagName('uri')
        numTags = results.getElementsByTagName("uri").length
        for i in range(numTags):
            if literalList[i].firstChild is not None:
                literal = literalList[i].firstChild.nodeValue
                li.append(literal)
        return li

def getResultsFromXMLCount(results):
    if isinstance(results,Document):
        numTags = results.getElementsByTagName("binding").length
        if numTags > 0:
            desc = results.getElementsByTagName("binding")[0]
            triples = desc.getElementsByTagName("literal")
            triplesValue = triples[0].firstChild.nodeValue
            return (int(triplesValue))
        else:
            return False

#GET SPARQL ENDPOINT OF A GIVEN SET OF METADATI
def getSparqlEndPoint(metadati):
    sparqlInfo = metadati.get('sparql')
    if not sparqlInfo:
        accessUrl = ''
        return accessUrl
    accessUrl = sparqlInfo.get('access_url')
    return accessUrl

def prettyPrintXML(xml):
    xml_pretty_str = xml.toprettyxml()
    print (xml_pretty_str)

def checkRedirect(url):
    if url:
        try:
            br = mechanize.Browser()   #NECESSARIO PER RISOLVERE IL PROBLEMA DI REINDIRIZZAMENTO NEL CASO L'ENDPOINT E' STATO SPOSTATO
            br.set_handle_robots(False)
            #br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
            response = br.open(url)
            newUrl = response.geturl()
            return newUrl
        except:   #IF THERE IS AN EXCEPTION WE RETURN IN THE CODE BECAUSE THEY ARE ALREADY MANAGED IN THE TEST OF THE SPARQ ENDPOINT
            return
    else:
        return

def getNumTriple(metadati): 
    triples = metadati.get('triples')
    try:
        triplesInt = int(triples)
    except ValueError: #IN CASE IN THE METADATA THE VALUE IS IN THE FORMAT '1.3 million'
        triplesInt = triples
    return triples

def getSource(metadata):
    source = metadata.get('website')
    return source

def checkAvailabilityResource(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
    ssl.match_hostname = lambda cert, hostname: True
    try:
        #url = checkRedirect(url) #BEFORE CHECK IF THE URL IS REDIRECTED
        response = requests.head(url,timeout=180,allow_redirects=True, verify=False) #3 MINUTES
        if response.status_code < 400:   #IF FAILS WITH A HEAD REQUEST, WE TEST WITH A GET (HEAD MAY NOT BE SUPPORTED)
            return True
        else:
            response = requests.head(url,timeout=180,allow_redirects=True, verify=False)
            if response.status_code < 400:
                return True
            else:
                newUrl = response.url
                if newUrl != url:
                    response = requests.head(newUrl,timeout=180,allow_redirects=True, verify=False)
                    if response.status_code < 400:
                        return True
                    else:
                         response = requests.head(newUrl,timeout=180,allow_redirects=True, verify=False)
                         if response.status_code < 400:
                             return True
                         else:
                             return False
    except Exception as e:
        return False
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}")
        return False

def checkAvailabilityResourceHead(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'}
    try:
        #url = checkRedirect(url) #BEFORE CHECK IF THE URL IS REDIRECTED
        response = requests.head(url,timeout=120) #3 MINUTES
        if response.status_code < 400:   #IF FAILS WITH A HEAD REQUEST, WE TEST WITH A GET (HEAD MAY NOT BE SUPPORTED)
            return True
        else:
            newUrl = response.url
            if newUrl != url:
                response = requests.head(newUrl,timeout=120)
                if response.status_code < 400:
                    return True
                else:
                    return False
    except:
        return False

def checkAvailabilityListResources(urlList):
    if len(urlList) > 0:
        for i in range(len(urlList)):
            available = checkAvailabilityResource(urlList[i])
            if available == True:
                return True
        return False
    return False

def getActiveDumps(urlList):
    url = []
    if len(urlList) > 0:
        for i in range(len(urlList)):
            available = checkAvailabilityResource(urlList[i])
            if available == True:
                url.append(urlList[i])
        return url
    return url

def getInactiveDumps(urlList):
    url = []
    if len(urlList) > 0:
        for i in range(len(urlList)):
            available = checkAvailabilityResource(urlList[i])
            if available == False:
                url.append(urlList[i])
        return url
    return url

def mergeResources(resourcesDH,resourcesLODC):
    if isinstance(resourcesDH,list) and len(resourcesDH) > 0: #MERGE THE TWO LISTS OF RESOURCES FROM DH E LODC AND DELETING DUPLICATE
        found = False
        for i in range(len(resourcesLODC)): 
            urlLODC = resourcesLODC[i].get('path')
            for j in range(len(resourcesDH)):    #COMPARE AN ITEM IN THE LIST OF RESOURCES FROM LOD CLOUD WITH EACH ITEM IN THE LIST OF RESOURCES FROM DATAHUB
                urlDH = resourcesDH[j].get('path')
                if urlLODC == urlDH:
                    found = True        #IF THE LINK TO THE RESOURCES IS THE SAME, THEN WE DON'T ADD THE ITEM TO THE LIST
            if found == False:
                resourcesDH.append(resourcesLODC[i])
            else:
                found = False
        return resourcesDH
    else:
        return resourcesLODC    #IF IN DATAHUB THERE AREN'T RESOURCES, PRINT ONLY THE RESOURCES IN LOD CLOUD

#INPUT LIST OF RESOURCES
#OUTPUT LIST OF RESOURCES WITH A FIELD STATUS. STATUS = ACTIVE IF URL IS ONLINE, STATUS = OFFLINE IF URL IS OFFLINE
def insertAvailability(resources):
    active = False
    for i in range(len(resources)):
        d = resources[i]
        url = d.get('path')
        active = checkAvailabilityResource(url)
        if active == True:
            d['status'] = 'active'
        else:
            d['status'] = 'offline'
    return resources

def checkhttps(url):
    if 'https' in url: 
         return True
    else:
        url = url.replace('http','https')
        return query.checkEndPoint(url)

def checkAvailabilityForDownload(resources):
    availability = 0
    if len(resources) == 0:
        availability = -1

        return availability
    else: 
        for i in range(len(resources)):
            d = resources[i]
            type = d.get('type')
            status = d.get('status')
            format = d.get('format')
            if isinstance(type,str):
                if type == 'full_download' and status == 'active':  
                    availability = 1
            if isinstance(format,str):
                if status == 'active':
                    availability = 1
                '''
                elif status == 'offline':
                    availability = 0
                if 'zip' in format and status == 'active':
                    availability = 1
                elif 'zip' in format and status == 'offline':
                    availability = 0
                if format == 'application/rdf+xml' and status == 'active':
                    availability = 1
                elif format == 'application/rdf+xml' and status == 'offline':
                    availability = 0
                if format == 'text/turtle' and status == 'active':
                    availability = 1
                elif format == 'text/turtle' and status == 'offline':
                    availability = 0
                if format == 'application/x-ntriples' and status == 'active':
                    availability = 1
                elif format == 'application/x-ntriples' and status == 'offline':
                    availability = 0
                if format == 'application/x-nquads' and status == 'active':
                    availability = 1
                elif format == 'application/x-nquads' and status == 'offline':
                    availability = 0
                if format == 'text/n3' and status == 'active':
                    availability = 1
                elif format == 'text/n3' and status == 'offline':
                    availability = 0
                if format == 'rdf' and status == 'active':
                    availability = 1
                elif format == 'rdf' and status == 'offline':
                    availability = 0
                if format == 'text/rdf+n3' and status == 'active':
                    availability = 1
                elif format == 'text/rdf+n3' and status == 'offline':
                    availability = 0
                if format == 'rdf/turtle' and status == 'active':
                    availability = 1
                elif format == 'rdf/turtle' and status == 'offline':
                    availability = 0
                '''
        return availability

def getLinkDownload(resources):
    urls = []
    availability = False
    for i in range(len(resources)):
        d = resources[i]
        type = d.get('type')
        status = d.get('status')
        format = d.get('format')
        if isinstance(type,str):
            if type == 'full_download' and status == 'active':  
                availability = True
                urls.append(d.get('path'))
        '''
        if isinstance(format,str):
            if status == 'active':
                availability = True
                urls.append(d.get('path'))
            if 'zip' in format and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'application/rdf+xml' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'text/turtle' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'application/x-ntriples' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'application/x-nquads' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'text/n3' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'rdf' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'text/rdf+n3' and status == 'active':
                availability = True
                urls.append(d.get('path'))
            if format == 'rdf/turtle' and status == 'active':
                availability = True
                urls.append(d.get('path'))    
        ''' 
    return urls

def getLinkOfflineDump(resources):
    urls = []
    for i in range(len(resources)):
        d = resources[i]
        type = d.get('type')
        status = d.get('status')
        format = d.get('format')
        if isinstance(type,str):
            if type == 'full_download' and status == 'offline':  
                urls.append(d.get('path'))
        if isinstance(format,str):
            if 'ZIP' in format and status == 'offline':
                urls.append(d.get('path'))
            if 'zip' in format and status == 'offline':
                urls.append(d.get('path'))
            if format == 'application/rdf+xml' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'text/turtle' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'application/x-ntriples' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'application/x-nquads' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'text/n3' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'rdf' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'text/rdf+n3' and status == 'offline':
                urls.append(d.get('path'))
            if format == 'rdf/turtle' and status == 'offline':
                urls.append(d.get('path'))    
    return urls

def toObjectResources(resourcesDH):
    otResources = []
    for i in range(len(resourcesDH)):
        path = resourcesDH[i].get('path')
        format = resourcesDH[i].get('format')
        description = resourcesDH[i].get('description')
        status = resourcesDH[i].get('status')
        title = resourcesDH[i].get('title')
        type = resourcesDH[i].get('type',None)
        resource = Resources(path,title,description,status,format,type)
        otResources.append(resource)
    return otResources

def toObjectExternalLinks(externalLinks):
    exList = []
    if isinstance(externalLinks,dict):
        for i in externalLinks:
            key = i
            value = externalLinks.get(i)
            exLink = ExternalLink(key,value)
            exList.append(exLink)
        return exList
    else:
        return False
   
def calculatePageRank(nameKG,externalLinks):
    if isinstance(externalLinks,list):
        G = nx.Graph()
        for i in range(len(externalLinks)):
            link = externalLinks[i]
            value = str(link.value)
            value = re.sub("[^\d\.]", "",value)
            G.add_edge(nameKG,link.nameKG,weight=value)
        pr = nx.pagerank(G)
        return pr.get(nameKG)
        #pos = nx.spring_layout(G, k=0.8)
        #nx.draw(G,pos,with_labels=True,width=0.4,node_size=400)
        #pos = nx.spring_layout(G)
        #nx.draw_networkx_edge_labels(G,pos)
        #plt.show()
    else:
        return 0

def getDegreeOfConnection(nameKG,externalLinks):
    if isinstance(externalLinks,list):
        G = nx.Graph()
        for i in range(len(externalLinks)):
            link = externalLinks[i]
            value = str(link.value)
            value = re.sub("[^\d\.]", "",value)
            G.add_edge(nameKG,link.nameKG,weight=value)
        degree = G.degree(nbunch=nameKG)   #ONLY THE DEGREE OF THE GRAPH WE ARE ANALYZING
        return degree

def getCentrality(nameKG,externalLinks):
    if isinstance(externalLinks,list):
        G = nx.Graph()
        for i in range(len(externalLinks)):
            link = externalLinks[i]
            value = str(link.value)
            value = re.sub("[^\d\.]", "",value)
            G.add_edge(nameKG,link.nameKG,weight=value)
        degreeCentrality = nx.degree_centrality(G)
        return degreeCentrality.get(nameKG)

def getClusteringCoefficient(nameKG,externalLinks):
    if isinstance(externalLinks,list):
        G = nx.Graph()
        for i in range(len(externalLinks)):
            link = externalLinks[i]
            value = str(link.value)
            value = re.sub("[^\d\.]", "",value)
            G.add_edge(nameKG,link.nameKG,weight=value)
        clusteringCoefficient = nx.clustering(G,nameKG)
        return clusteringCoefficient

def getThroughput(accessUrl):
    count = 0
    countList = []
    for i in range(10):
        count = 0
        start_time = time.time()
        while (time.time() - start_time) < 1:
            query.TPQuery(accessUrl,count)
            count = count +1
        countList.append(count)
    return countList

def getThroughputNoOff(accessUrl):
    count = 0
    countList = []
    for i in range(5):
        count = 0
        start_time = time.time()
        while (time.time() - start_time) < 1:
            query.checkEndPoint(accessUrl)
            count = count +1
        countList.append(count)
    return countList

def getUrlVoID(otResources):
    if isinstance(otResources,list):
        for i in range(len(otResources)):
            resource = otResources[i]
            if resource.format is not None:
                if resource.format == 'meta/void' and resource.status == 'active':
                    urlV = resource.url
                    if isinstance(urlV,str):
                        return urlV
                elif resource.title is not None:
                    if 'void' in resource.title and resource.status == 'active':
                        urlV = resource.url
                        if isinstance(urlV,str):
                            return urlV
    else:
        return False


def getNumberResultsLOV(jsonFile):
    if isinstance(jsonFile,dict):
        totalResults = jsonFile.get('total_results')
        totalResults = int(totalResults)
        if totalResults > 0:
            return True
        else:
            return False
    else:
        return False

def checkURI(uri):
    try:
        r = requests.head(uri,timeout=1)
        if r.status_code == 200:
            return True
        else:
            return False
    except: 
        return False

def validateURI(uri):
    try:
        uri = uri.strip()
        result = urlparse(uri)
        return bool(result.scheme) and bool(result.netloc)
    except ValueError:
        return False

def xmlToDict(results):
    dictList = []
    literalList = results.getElementsByTagName("result")
    for node in literalList:
        alist = node.getElementsByTagName('binding')
        d = {}
        for node2 in alist:
            if node2.getAttribute('name') == 's':
                uriList = node2.getElementsByTagName('uri')
                literalList = node2.getElementsByTagName('literal')
                uriList = uriList+literalList
                for a in uriList:
                    ds = {}
                    uri = a.firstChild.data
                    ds['value'] = uri
                d['s'] = ds
            elif node2.getAttribute('name') == 'o':
                uriList2 = node2.getElementsByTagName('uri')
                literalList2 = node2.getElementsByTagName('literal')
                uriList2 = uriList2 + literalList2
                for a in uriList2:
                    do = {}
                    obj = a.firstChild.data
                    do['value'] = obj
                d['o'] = do
        dictList.append(d)
    return dictList

def xmlToDictSP(results):
    dictList = []
    literalList = results.getElementsByTagName("result")
    for node in literalList:
        alist = node.getElementsByTagName('binding')
        d = {}
        for node2 in alist:
            if node2.getAttribute('name') == 's':
                uriList = node2.getElementsByTagName('uri')
                literalList = node2.getElementsByTagName('literal')
                uriList = uriList+literalList
                for a in uriList:
                    ds = {}
                    uri = a.firstChild.data
                    ds['value'] = uri
                d['s'] = ds
            elif node2.getAttribute('name') == 'p':
                uriList2 = node2.getElementsByTagName('uri')
                literalList2 = node2.getElementsByTagName('literal')
                uriList2 = uriList2 + literalList2
                for a in uriList2:
                    do = {}
                    obj = a.firstChild.data
                    do['value'] = obj
                d['p'] = do
        dictList.append(d)
    return dictList


def xmlToDictO(results):
    dictList = []
    literalList = results.getElementsByTagName("result")
    for node in literalList:
        alist = node.getElementsByTagName('binding')
        d = {}
        for node2 in alist:
            if node2.getAttribute('name') == 'o':
                uriList = node2.getElementsByTagName('uri')
                literalList = node2.getElementsByTagName('literal')
                uriList = uriList+literalList
                for a in uriList:
                    ds = {}
                    if a.firstChild is not None:
                        uri = a.firstChild.data
                        ds['value'] = uri
                d['o'] = ds
        dictList.append(d)
    return dictList

def xmlToDictS(results):
    dictList = []
    literalList = results.getElementsByTagName("result")
    for node in literalList:
        alist = node.getElementsByTagName('binding')
        d = {}
        for node2 in alist:
            if node2.getAttribute('name') == 's':
                uriList = node2.getElementsByTagName('uri')
                literalList = node2.getElementsByTagName('literal')
                uriList = uriList+literalList
                for a in uriList:
                    ds = {}
                    if a.firstChild is not None:
                        uri = a.firstChild.data
                        ds['value'] = uri
                d['s'] = ds
        dictList.append(d)
    return dictList

def xmlToDictP(results):
    dictList = []
    literalList = results.getElementsByTagName("result")
    for node in literalList:
        alist = node.getElementsByTagName('binding')
        d = {}
        for node2 in alist:
            if node2.getAttribute('name') == 'p':
                uriList = node2.getElementsByTagName('uri')
                literalList = node2.getElementsByTagName('literal')
                uriList = uriList+literalList
                for a in uriList:
                    ds = {}
                    if a.firstChild is not None:
                        uri = a.firstChild.data
                        ds['value'] = uri
                d['p'] = ds
        dictList.append(d)
    return dictList

def xmlToDictSPO(results):
    dictList = []
    literalList = results.getElementsByTagName("result")
    for node in literalList:
        alist = node.getElementsByTagName('binding')
        d = {}
        for node2 in alist:
            if node2.getAttribute('name') == 's':
                uriList = node2.getElementsByTagName('uri')
                literalList = node2.getElementsByTagName('literal')
                uriList = uriList+literalList
                for a in uriList:
                    ds = {}
                    uri = a.firstChild.data
                    ds['value'] = uri
                d['s'] = ds
            elif node2.getAttribute('name') == 'p':
                uriList2 = node2.getElementsByTagName('uri')
                literalList2 = node2.getElementsByTagName('literal')
                uriList2 = uriList2 + literalList2
                for a in uriList2:
                    do = {}
                    obj = a.firstChild.data
                    do['value'] = obj
                d['p'] = do
            elif node2.getAttribute('name') == 'o':
                uriList2 = node2.getElementsByTagName('uri')
                literalList2 = node2.getElementsByTagName('literal')
                uriList2 = uriList2 + literalList2
                for a in uriList2:
                    do = {}
                    obj = a.firstChild.data
                    do['value'] = obj
                d['o'] = do
        dictList.append(d)
    return dictList


def searchString(stringList,toFind):
    for i in range(len(stringList)):
        if toFind in stringList[i]:
            return True
    return False

def getRegex(dataType):
    d = {
        'http://www.w3.org/2001/XMLSchema#integer' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#double' : '(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)? |(\+|-)?INF|NaN',
        'http://www.w3.org/2001/XMLSchema#float' : '(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?|(\+|-)?INF|NaN',
        'http://www.w3.org/2001/XMLSchema#any' : '.*',
        'http://www.w3.org/2001/XMLSchema#decimal' : '(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)',
        'http://www.w3.org/2001/XMLSchema#time' : '(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#date' : '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#dateTime' : '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#dateTimeStamp': '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?.*(Z|(\+|-)[0-9][0-9]:[0-9][0-9])',
        'http://www.w3.org/2001/XMLSchema#string' : '.*',
        'http://www.w3.org/2001/XMLSchema#gYear' : '-?([1-9][0-9]{3,}|0[0-9]{3})(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#gMonth' : '--(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#gDay' : '---(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#gYearMonth' : '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#gMonthDay' : '--(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'http://www.w3.org/2001/XMLSchema#duration' : '''-?P( ( ( [0-9]+Y([0-9]+M)?([0-9]+D)?
       | ([0-9]+M)([0-9]+D)?
       | ([0-9]+D)
       )
       (T ( ([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?
          | ([0-9]+M)([0-9]+(\.[0-9]+)?S)?
          | ([0-9]+(\.[0-9]+)?S)
          )
       )?
    )
  | (T ( ([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?
       | ([0-9]+M)([0-9]+(\.[0-9]+)?S)?
       | ([0-9]+(\.[0-9]+)?S)
       )
    )
  )''',
        'http://www.w3.org/2001/XMLSchema#yearMonthDuration' : '[^DT]*',
        'http://www.w3.org/2001/XMLSchema#dayTimeDuration' : '[^YM]*[DT].*',
        'http://www.w3.org/2001/XMLSchema#byte' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#short' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#long' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#unsignedByte' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#unsignedShort' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#unsignedInt' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#unsignedLong' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#positiveInteger' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#nonNegativeInteger' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#negativeInteger' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#nonPositiveInteger' : '[\-+]?[0-9]+',
        'http://www.w3.org/2001/XMLSchema#hexBinary' : '([0-9a-fA-F]{2})*',
        'http://www.w3.org/2001/XMLSchema#base64Binary' : '((([A-Za-z0-9+/] ?){4})*(([A-Za-z0-9+/] ?){3}[A-Za-z0-9+/]|([A-Za-z0-9+/] ?){2}[AEIMQUYcgkosw048] ?=|[A-Za-z0-9+/] ?[AQgw] ?= ?=))?',
        'http://www.w3.org/2001/XMLSchema#language' : '[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*',
        'http://www.w3.org/2001/XMLSchema#normalizedString' : '^\S+$',
        'http://www.w3.org/2001/XMLSchema#NMTOKEN' : '\c+',
        'http://www.w3.org/2001/XMLSchema#Name' : '\i\c*',
        'http://www.w3.org/2001/XMLSchema#NCName' : '\i\c* ∩ [\i-[:]][\c-[:]]*',
        'http://www.w3.org/2001/XMLSchema#boolean' : '^(?i:true|false|0|1)$',
         #ALTERNATIVE METHOD TO INDICATE DATATYPE
        'xsd:integer' : '[\-+]?[0-9]+',
        'xsd:double' : '(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)? |(\+|-)?INF|NaN',
        'xsd:float' : '(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)([Ee](\+|-)?[0-9]+)?|(\+|-)?INF|NaN',
        'xsd:any' : '.*',
        'xsd:decimal' : '(\+|-)?([0-9]+(\.[0-9]*)?|\.[0-9]+)',
        'xsd:time' : '(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:date' : '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:dateTime' : '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:dateTimeStamp': '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])T(([01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](\.[0-9]+)?|(24:00:00(\.0+)?))(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?.*(Z|(\+|-)[0-9][0-9]:[0-9][0-9])',
        'xsd:string' : '.*',
        'xsd:gYear' : '-?([1-9][0-9]{3,}|0[0-9]{3})(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:gMonth' : '--(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:gDay' : '---(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:gYearMonth' : '-?([1-9][0-9]{3,}|0[0-9]{3})-(0[1-9]|1[0-2])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:gMonthDay' : '--(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))?',
        'xsd:duration' : '''-?P( ( ( [0-9]+Y([0-9]+M)?([0-9]+D)?
       | ([0-9]+M)([0-9]+D)?
       | ([0-9]+D)
       )
       (T ( ([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?
          | ([0-9]+M)([0-9]+(\.[0-9]+)?S)?
          | ([0-9]+(\.[0-9]+)?S)
          )
       )?
    )
  | (T ( ([0-9]+H)([0-9]+M)?([0-9]+(\.[0-9]+)?S)?
       | ([0-9]+M)([0-9]+(\.[0-9]+)?S)?
       | ([0-9]+(\.[0-9]+)?S)
       )
    )
  )''',
        'xsd:yearMonthDuration' : '[^DT]*',
        'xsd:dayTimeDuration' : '[^YM]*[DT].*',
        'xsd:byte' : '[\-+]?[0-9]+',
        'xsd:short' : '[\-+]?[0-9]+',
        'xsd:long' : '[\-+]?[0-9]+',
        'xsd:unsignedByte' : '[\-+]?[0-9]+',
        'xsd:unsignedShort' : '[\-+]?[0-9]+',
        'xsd:unsignedInt' : '[\-+]?[0-9]+',
        'xsd:unsignedLong' : '[\-+]?[0-9]+',
        'xsd:positiveInteger' : '[\-+]?[0-9]+',
        'xsd:nonNegativeInteger' : '[\-+]?[0-9]+',
        'xsd:negativeInteger' : '[\-+]?[0-9]+',
        'xsd:nonPositiveInteger' : '[\-+]?[0-9]+',
        'xsd:hexBinary' : '([0-9a-fA-F]{2})*',
        'xsd:base64Binary' : '((([A-Za-z0-9+/] ?){4})*(([A-Za-z0-9+/] ?){3}[A-Za-z0-9+/]|([A-Za-z0-9+/] ?){2}[AEIMQUYcgkosw048] ?=|[A-Za-z0-9+/] ?[AQgw] ?= ?=))?',
        'xsd:language' : '[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*',
        'xsd:normalizedString' : '^\S+$',
        'xsd:NMTOKEN' : '\c+',
        'xsd:Name' : '\i\c*',
        'xsd:NCName' : '\i\c* ∩ [\i-[:]][\c-[:]]*',
        'xsd:boolean' : '^(?i:true|false|0|1)$'



    }

    regex = d.get(dataType,None)
    return regex

def checkString(regex,string):
    match = re.fullmatch(regex,string)
    if match is not None:
        return True
    else:
        return False

def trasforrmToRegex(pattern):
    pattern = '^' + pattern
    pattern = pattern.replace('.',r'\\.')
    pattern = pattern.replace('(',r'\\(')
    pattern = pattern.replace(')',r'\\)')
    pattern = pattern.replace('[',r'\\[')
    pattern = pattern.replace(']',r'\\]')
    pattern = pattern.replace('+',r'\\+')
    pattern = pattern.replace('*',r'\\*')
    pattern = pattern.replace('?',r'\\?')
    pattern = pattern.replace('$',r'\\$')
    return pattern

def skipCheckSSL():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
    # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context

def binarySearch(arr,l,r,x):
    while l<= r:
        mid = l + (r - l) // 2

        if arr[mid] == x:
            return mid
        elif arr[mid] < x:
            l = mid + 1
        else:
            r = mid - 1 
    return -1  #IF WE REACH HERE, THEN THE ELEMENT WAS NOT PRESENT

def getURINamespace(uris):
    namespaces = []
    for uri in uris:
        r = checkURI(uri)
        if  r == True:
            if '#' in uri:
                splittedUri = uri.split('#',1)
                namespace = splittedUri[0]
                namespaces.append(namespace)
    namespaces = list(dict.fromkeys(namespaces))
    return namespaces

def getNormalizedScore(min,max,score):
    if max > min:
        return (score - min) / (max - min) * 100
    else:
        return score

def removeProblematicEndpoint(kgs):
    to_remove = ['b3kat','lotico','UniProt','uniprot','uniprot-citations','uniprot-databases',
                 'uniprot-metadata','uniprot-taxonomy','uniprot-uniparc','uniprot-unipathway','uniprotkb','uniref'
                 'data-open-ac-uk','isocat','allie-abbreviation-and-long-form-database-in-life-science']
    for kg_to_remove in to_remove:
        if kg_to_remove in kgs:
            kgs.remove(kg_to_remove)


def enableForDownload(filename):
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'./Analysis results')
    save_path = os.path.join(save_path, filename+".csv")
    #filename = os.path.basename(filename)
    #save_path = save_path + filename
    dirDown = os.path.join(here,'/var/www/html')
    dirDown = os.path.join(dirDown,filename+".csv")
    shutil.copyfile(save_path,dirDown)
    
def enableNewData():
    here = os.path.dirname(os.path.abspath(__file__))
    csvJS = os.path.join(here,'./Graphs Visualization JS/CSVforJS')
    p = Path(csvJS)
    files = list(p.glob('*.csv'))
    for file in files:
        filename = str(file.stem)
        save_path = os.path.join(here,'./Graphs Visualization JS/CSVforJS')
        save_path = os.path.join(save_path, filename+".csv")    
        #filename = os.path.basename(filename)
        #save_path = save_path + filename
        dirDown = os.path.join(here,'/var/www/html/CSVforJS')
        dirDown = os.path.join(dirDown,filename+".csv")
        shutil.copyfile(save_path,dirDown)
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'./Graphs Visualization JS')
    save_path = os.path.join(save_path, 'KGid.txt')
    dirDown = os.path.join(here,'/var/www/html')
    dirDown = os.path.join(dirDown,'KGid.txt')
    shutil.copyfile(save_path,dirDown)
    
def to_list(old_values):
    if isinstance(old_values,str):
        old_values = old_values.split(';')
    
    return old_values

def normalize_score(score):
    return (score) * 100

def write_time(kg,time,metric,dimension,analysis_date):
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'../Analysis results')
    save_path = os.path.join(save_path, f"performance-{analysis_date}.txt")
    with open(save_path,'a') as file:
            file.write(f'{dimension} | {metric} for {kg} took {time}s\n')

def update_local_kgs_spnapshot():
    url = "http://www.isislab.it:12280/kgsearchengine/brutalsearch?"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
    
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'./API')
    save_path = os.path.join(save_path,"kgs_metadata_snapshot.json")
    with open(save_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def load_kgs_metadata_from_snap():
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'./API')
    save_path = os.path.join(save_path,"kgs_metadata_snapshot.json")
    with open(save_path, 'r') as json_file:
        kgs_metadata = json.load(json_file)
        results = kgs_metadata.get('results')
        kgfound = []
        for i in range(len(results)):
            d = results[i]
            id = d.get('id')
            name = d.get('title')
            kgfound.append((id,name))
        return kgfound

def if_list_return_int(metric):
    if(isinstance(metric,list)):
        return len(metric)
    else:
        return metric

def extract_media_type(resources_metadata):
    media_type = []
    for resource in resources_metadata:
        if 'format' in resource:
            if isinstance(resource['format'],str):
                if 'example' not in resource['format']:
                    media_type.append(resource['format'])
    
    return media_type


def check_common_acceppted_format(media_types):
    common_acceppted_format = ['application/rdf+xml','application/rdf+xml','text/turtle','application/x-ntriples','application/x-nquads', 'application/n-triples',
                               'application/trig','text/n3','rdf','text/rdf+n3','rdf/turtle','plain/text','application/octet-stream','application/x-gzip','gzip:ntriples']
    for media_type in media_types:
        if isinstance(media_type,str):
            if media_type.lower() in common_acceppted_format:
                return True

    return False 

def is_valid_void_url(url):
    try:
        response = requests.head(url, timeout=30, allow_redirects=True)
        if 'text/html' in response.headers.get('Content-Type', ''):
            return False
        return True
    except Exception as e:
        return False

def clean_dqv_values(input_file, output_file, target_metric="<http://example.org/metric/Description>"):
    here = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(here,input_file)
    output_file = os.path.join(here,output_file)

    def clean_value(value):
        value = re.sub(r'\s+', ' ', value).strip()  # Normalize spaces
        value = value.replace("'", " ").replace('"', '')
        return value
    
    with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
        inside_target_block, multiline = False, False
        new_value_buffer = None
        
        for line in infile:
            stripped = line.strip()
            
            if stripped.startswith("dqv:isMeasurementOf") and target_metric in stripped:
                inside_target_block = True
            
            if inside_target_block and stripped.startswith("dqv:value"):
                multiline = not stripped.endswith('^^xsd:string ;')
                new_value_buffer = stripped.split('dqv:value', 1)[1].strip().strip('"')
                continue
            
            if multiline:
                if stripped.endswith('^^xsd:string ;'):
                    new_value_buffer += ' ' + stripped.strip().strip('"')
                    multiline = False
                else:
                    new_value_buffer += ' ' + stripped.strip().strip('"')
                continue
            
            if new_value_buffer is not None:
                cleaned_value = clean_value(new_value_buffer)
                outfile.write(f'    dqv:value "{cleaned_value}"^^xsd:string ;\n')
                new_value_buffer, inside_target_block = None, False
                continue
            
            outfile.write(line)

def is_valid_void_url(url):
    try:
        response = requests.head(url, timeout=30, allow_redirects=True)
        if 'text/html' in response.headers.get('Content-Type', ''):
            return False
        return True
    except Exception as e:
        return False