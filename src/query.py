import datetime
import re
from SPARQLWrapper import *
from SPARQLWrapper import SPARQLWrapper
from xml.dom.minidom import Document
import time
import utils
import warnings
import xml.etree.ElementTree as ET
import rdflib

def log_in_out(func):

    def decorated_func(*args, **kwargs):
        print("Doing ", func.__name__)
        result = func(*args, **kwargs)
        print("Done ")
        return result

    return decorated_func
@log_in_out
def checkEndPoint(url): 
    sparql = SPARQLWrapper(url) 
    sparql.setQuery("""
    SELECT ?s
    WHERE {?s ?p ?o .}
    LIMIT 1
    """)
    sparql.setTimeout(300) #10 minutes
    result = sparql.query().convert()
    return result

@log_in_out
def TPQuery(url,offset): 
    sparql = SPARQLWrapper(url) 
    sparql.setQuery("""
    SELECT ?s
    WHERE {?s ?p ?o .}
    LIMIT 1
    OFFSET %d
    """%offset)
    sparql.setTimeout(300) #10 minutes
    result = sparql.query().convert()
    return result

@log_in_out
def getNumTripleQuery(url): #TODO QUERY WITHOUT COUNT (MAY NOT BE SUPPORTED)
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
    SELECT (COUNT(?s) AS ?triples) 
    WHERE { ?s ?p ?o }
    """)
    sparql.setTimeout(300) #5 minutes
    sparql.setReturnFormat(XML)
    results = sparql.query().convert()
    if isinstance(results,Document):
        desc = results.getElementsByTagName("binding")[0]
        triples = desc.getElementsByTagName("literal")
        triplesValue = triples[0].firstChild.nodeValue
        return (int(triplesValue))

@log_in_out
def testLatency(url): 
    sparql = SPARQLWrapper(url)
    latency = []
    for i in range(5):
        sparql.setQuery("""
        SELECT *  
        WHERE {?s ?p ?o .}
        LIMIT 1
        """)
        sparql.setTimeout(300)
        start = time.time()
        sparql.query()
        latencyValue = (time.time() - start)
        latency.append(latencyValue)
    return latency

@log_in_out
def numBlankNode(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
    SELECT (COUNT(?bnode) AS ?triples) 
    WHERE { ?bnode ?p ?o
    FILTER (isBlank(?bnode))}
    """)
    sparql.setReturnFormat(JSON) #ASKS TO RECEIVE DATA IN JSON FORMAT IS SUPPORTED
    sparql.setTimeout(300) #5 minutes
    results = sparql.query().convert()
    if isinstance(results,dict):
        numBnode = utils.getResultsFromJSONCountInt(results) #BEFORE WITHOUT INT
        return numBnode
    elif isinstance(results,Document):
        numBnode = utils.getResultsFromXMLCount(results)
        return numBnode
    else:
        return False

@log_in_out
def getLangugeSupported(url):
    languages = []
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
    SELECT DISTINCT ?triples 
    WHERE{
    ?s ?p ?o.
    BIND(LANG(?o) as ?triples)}
    """)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(300) #5 minutes
    results = sparql.query().convert()
    if isinstance(results,dict):
        languages = utils.getResultsFromJSONCount(results)
        return languages
    elif isinstance(results,Document): #IF RESULT IS IN XML 
        languages = utils.getResultsFromXML(results)
        return languages
    else:
        return False

@log_in_out
def checkRDFDataStructures(url):  
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
    PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT *
    WHERE{
    {?s rdf:type rdf:List }
    UNION
    {?s rdf:type rdf:Statement}
    UNION
    {?s rdf:type rdf:Alt}
    UNION
    {?s rdf:type rdf:Bag}
    UNION
    {?s rdf:type rdf:Seq}
    UNION
    {?s rdf:type rdf:Container}
    UNION
    {?s rdf:subject ?o}
    UNION
    {?s rdf:predicate ?o}
    UNION
    {?s rdf:object ?o}
    UNION
    {?s rdfs:member ?o}
    UNION
    {?s rdf:first ?o}
    UNION
    {?s rdf:rest ?o}
    UNION
    {?s rdf:_'[0-9]+'}
    }
    LIMIT 1
    """)
    sparql.setTimeout(300) #5 minutes
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        result = results.get('results')
        bindings = result.get('bindings')
        if isinstance(bindings,list):
            if len(bindings) > 0:
                return True
            else:
                return False
        else:
            return False
    elif isinstance(results,Document):
        numTags = results.getElementsByTagName("binding").length
        if numTags > 0:
            return True
        else:
            return False
    else:
        return False

@log_in_out
def checkSerialisationFormat(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX schema: <http://schema.org/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>

    SELECT ?o
    WHERE {
    { ?dataset a dcat:Dataset ; dcat:mediaType ?o . }
    UNION
    { ?dataset a dcat:Dataset ; void:feature ?o . }
    UNION
    { ?dataset a dcat:Dataset ; dcterms:format ?o . }
    UNION
    { ?dataset a dcat:Distribution ; dcat:mediaType ?o . }
    UNION
    { ?dataset a dcat:Distribution ; dcterms:format ?o . }
    UNION
    { ?dataset a dcat:Distribution ; void:feature ?o . }
    UNION
    { ?dataset a void:Dataset ; dcat:mediaType ?o . }
    UNION
    { ?dataset a void:Dataset ; void:feature ?o . }
    UNION
    { ?dataset a void:Dataset ; dcterms:format ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        link = utils.getResultsFromJSON(results)
        return link
    elif isinstance(results,Document):
        link = utils.getResultsFromXML(results)
        return link
    else:
        return False

@log_in_out
def checkDataDump(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o 
    WHERE 
    {?s void:dataDump ?o}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        link = utils.getResultsFromJSON(results)
        return link
    elif isinstance(results,Document):
        link = utils.getResultsFromXML(results)
        return link
    else:
        return False

@log_in_out
def checkLicenseMR(url): #PROBLEM ON http://lod.b3kat.de/sparql
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX cc: <http://creativecommons.org/ns#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX schema: <http://schema.org/>
    PREFIX doap: <http://usefulinc.com/ns/doap#>
    PREFIX xhtml: <http://www.w3.org/1999/xhtml#>
    SELECT DISTINCT ?o
    WHERE{
    {?s ?p ?o}
    VALUES (?p) {(dct:license) (dct:rights) (cc:license) (dc:license) (schema:license) (doap:license) (xhtml:license) (dc:rights)}
    }
    LIMIT 1
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        licenses = utils.getResultsFromJSON(results)
        return licenses
    elif isinstance(results,Document):
        licenses = utils.getResultsFromXML(results)
        return licenses
    else:
        return False

@log_in_out
def checkLicenseMR2(url):   #USED IN CASE THE QUERY WITH VALUES ISN'T SUPPORTED
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX cc: <http://creativecommons.org/ns#>
    PREFIX dc: <http://purl.org/dc/elements/1.1/>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX schema: <http://schema.org/>
    PREFIX doap: <http://usefulinc.com/ns/doap#>
    PREFIX xhtml: <http://www.w3.org/1999/xhtml#>
    SELECT DISTINCT ?o
    WHERE{
    {?s dct:license ?o}
    UNION
    {?s dct:rights ?o}
    UNION
    {?s dc:rights ?o}
    UNION
    {?s cc:license ?o}
    UNION
    {?s dc:license ?o}
    UNION
    {?s schema:license ?o}
    UNION
    {?s xhtml:license ?o}
    UNION
    {?s doap:license ?o}
    }
    LIMIT 1
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        licenses = utils.getResultsFromJSON(results)
        return licenses
    elif isinstance(results,Document):
        licenses = utils.getResultsFromXML(results)
        return licenses
    else:
        return False
@log_in_out
def checkLicenseHR(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX dct: <http://purl.org/dc/terms/>
    PREFIX schema: <http://schema.org/>
    SELECT ?o
    WHERE{
        {?s rdfs:label  ?o}
    UNION
        {?s dct:description  ?o}
    UNION
        {?s rdfs:comment  ?o}
    UNION
        {?s rdfs:label  ?o}
    UNION
        {?s schema:description  ?o}
    FILTER regex(?o,".*(licensed?|copyrighte?d?).*(under|grante?d?|rights?).*")
    } 
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        result = results.get('results')
        bindings = result.get('bindings')
        if isinstance(bindings,list):
            if len(bindings) > 0:
                return True
            else:
                return False
        else:
            return False
    elif isinstance(results,Document):
        numTags = results.getElementsByTagName("binding").length
        if numTags > 0:
            return True
        else:
            return False
    else:
        return False
@log_in_out
def numberOfProperty(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT (COUNT(?o) AS ?triples)
    WHERE {
    { ?o a rdf:Property}
    UNION
    {?o a owl:DatatypeProperty}
    UNION
    {?o a skos:Property}
    UNION
    {?o a owl:DatatypeProperty}
    UNION
    {?o a owl:AnnotationProperty}
    UNION
    {?o a owl:OntologyProperty}
    UNION
  	{?o a rdfs:subPropertyOf}
  	UNION
  	{?o a rdfs:Property}
    }
    ''') 
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONCountInt(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXMLCount(results)
        return value
    else:
        return False
@log_in_out
def getNumLabel(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX skosxl:<http://www.w3.org/2008/05/skos-xl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX awol: <http://bblfish.net/work/atom-owl/2006-06-06/#>
    PREFIX wdrs: <http://www.w3.org/2007/05/powder-s#>
    PREFIX schema: <http://schema.org/>
    SELECT (COUNT(?o) AS ?triples)
    WHERE{
    {?s rdfs:label ?o}
    UNION
    {?s foaf:name ?o}
    UNION
    {?s skos:prefLabel ?o}
    UNION
    {?s dcterms:title ?o}
    UNION
    {?s dcterms:decription ?o}
    UNION
    {?s rdfs:comment ?o}
    UNION
    {?s awol:label ?o}
    UNION
    {?s dcterms:alternative ?o}
    UNION
    {?s skos:altLabel ?o}
    UNION
    {?s skos:note ?o}
    UNION
    {?s wdrs:text ?o}
    UNION
    {?s skosxl:altLabel ?o}
    UNION
    {?s skosxl:hiddenLabel ?o}
    UNION
    {?s skosxl:prefLabel ?o}
    UNION
    {?s skosxl:literalForm ?o}
    UNION
    {?s schema:name ?o}
    UNION
    {?s schema:description ?o}
    UNION
    {?s schema:alternateName ?o}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONCountInt(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXMLCount(results)
        return value
    else:
        return False
@log_in_out
def checkUriRegex(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o 
    WHERE{
    {?s void:uriRegexPattern ?o}
    UNION
    {?s void:uriPattern ?o}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        regex = utils.getResultsFromJSON(results)
        return regex
    elif isinstance(results,Document):
        regex = utils.getResultsFromXML(results)
        return regex
    else:
        return False
@log_in_out
def checkUriPattern(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o 
    WHERE
    {?s void:uriSpace ?o}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        regex = utils.getResultsFromJSON(results)
        return regex
    elif isinstance(results,Document):
        regex = utils.getResultsFromXML(results)
        return regex
    else:
        return False
@log_in_out
def getVocabularies(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>

    SELECT DISTINCT ?o
    WHERE {
    { ?dataset a dcat:Dataset ; void:vocabulary ?o . }
    UNION
    { ?dataset a dcat:Distribution ; void:vocabulary ?o . }
    UNION
    { ?dataset a void:Dataset ; void:vocabulary ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        vocabularies = utils.getResultsFromJSON(results)
        return vocabularies
    elif isinstance(results,Document):
        vocabularies = utils.getResultsFromXMLUri(results)
        return vocabularies
    else:
        return False
@log_in_out
def getCreator(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>

    SELECT ?o
    WHERE {
    { ?dataset a dcat:Dataset ; dcterms:creator ?o . }
    UNION
    { ?dataset a dcat:Distribution ; dcterms:creator ?o . }
    UNION
    { ?dataset a void:Dataset ; dcterms:creator ?o . }
    UNION
    { ?dataset a void:Dataset ; foaf:maker ?o . }
    UNION
    { ?dataset a dcat:Dataset ; foaf:maker ?o . }
    UNION
    { ?dataset a dcat:Distribution ; foaf:maker ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        creators = utils.getResultsFromJSON(results)
        return creators
    elif isinstance(results,Document):
        creators = utils.getResultsFromXML(results)
        return creators
    else:
        return False
@log_in_out
def getPublisher(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''                    
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>

    SELECT DISTINCT ?o
    WHERE {
    { ?dataset a dcat:Dataset ; dcterms:publisher ?o . }
    UNION
    { ?dataset a dcat:Distribution ; dcterms:publisher ?o . }
    UNION
    { ?dataset a void:Dataset ; dcterms:publisher ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        creators = utils.getResultsFromJSON(results)
        return creators
    elif isinstance(results,Document):
        creators = utils.getResultsFromXML(results)
        return creators
    else:
        return False
@log_in_out
def getNumEntities(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o
    WHERE {
    { ?dataset a void:Dataset ; void:entities ?o . }
    UNION
    { ?dataset a dcat:Dataset ; void:entities ?o . }
    UNION
    { ?dataset a dcat:Distribution ; void:entities ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        entities = utils.getResultsFromJSON(results)
        return int(entities)
    elif isinstance(results,Document):
        entities = utils.getResultsFromXML(results)
        return int(entities)
    else:
        return False
    
@log_in_out
def getNumEntitiesRegex(url,entityRe):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
   SELECT (COUNT(?s) as ?triples)
   WHERE{
   {?s ?p ?o}
   FILTER(regex(?s,"%s"))
   }
    '''%entityRe)
    sparql.setTimeout(200)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        entities = utils.getResultsFromJSONCountInt(results)
        return entities
    elif isinstance(results,Document):
        entities = utils.getResultsFromXMLCount(results)
        return entities
    else:
        return False        
@log_in_out
def getContributors(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>

    SELECT DISTINCT ?o
    WHERE {
        { ?dataset a dcat:Dataset ; dcterms:contributor ?o . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:contributor ?o . }
        UNION
        { ?dataset a void:Dataset ; dcterms:contributor ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        contributors = utils.getResultsFromJSON(results)
        return contributors
    elif isinstance(results,Document):
        contributors = utils.getResultsFromXML(results)
        return contributors
    else:
        return False
@log_in_out
def getSameAsChains(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX schema: <http://schema.org/>
    SELECT (COUNT(?o) AS ?triples)
    WHERE {
        {?s owl:sameAs ?o}
        UNION
        {?s schema:sameAs ?o}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONCountInt(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXMLCount(results)
        return value
    else:
        return False
@log_in_out
def getFrequency(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>

    SELECT ?o
    WHERE {
    { ?dataset a dcat:Dataset ; dcterms:accrualPeriodicity ?o . }
    UNION
    { ?dataset a dcat:Distribution ; dcterms:accrualPeriodicity ?o . }
    UNION
    { ?dataset a void:Dataset ; dcterms:accrualPeriodicity ?o . }
    UNION
    { ?dataset a void:Dataset ; dcterms:Frequency ?o . }
    UNION
    { ?dataset a dcat:Dataset ; dcterms:Frequency ?o . }
    UNION
    { ?dataset a dcat:Distribution ; dcterms:Frequency ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        frequency = utils.getResultsFromJSON(results)
        return frequency
    elif isinstance(results,Document):
        frequency = utils.getResultsFromXML(results)
        return frequency
    else:
        return False
@log_in_out
def getCreationDate(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o
    WHERE {
        { ?dataset a dcat:Dataset ; dcterms:created ?o . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:created ?o . }
        UNION
        { ?dataset a void:Dataset ; dcterms:created ?o . }
        UNION
        { ?dataset a void:Dataset ; dcterms:issued ?o . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:issued ?o . }
        UNION
        { ?dataset a dcat:Dataset ; dcterms:issued ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        creation = utils.getResultsFromJSON(results)
        match = re.search(r'\d{4}-\d{2}-\d{2}', creation[0])
        date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
        date = str(date)
        return date
    elif isinstance(results,Document):
        creation = utils.getResultsFromXML(results)
        match = re.search(r'\d{4}-\d{2}-\d{2}', creation[0])
        date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
        date = str(date)
        return date
    else:
        return False
@log_in_out
def getCreationDateMin(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    SELECT DISTINCT (MIN (?created) AS ?min)
    WHERE {
        { ?dataset a dcat:Dataset ; dcterms:created ?created . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:created ?created . }
        UNION
        { ?dataset a void:Dataset ; dcterms:created ?created . }
        UNION
        { ?dataset a void:Dataset ; dcterms:issued ?created . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:issued ?created . }
        UNION
        { ?dataset a dcat:Dataset ; dcterms:issued ?created . }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        creation = utils.getResultsFromJSONMin(results)
        match = re.search(r'\d{4}-\d{2}-\d{2}', creation[0])
        date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
        date = str(date)
        return date
    elif isinstance(results,Document):
        creation = utils.getResultsFromXML(results)
        match = re.search(r'\d{4}-\d{2}-\d{2}', creation[0])
        date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
        date = str(date)
        return date
    else:
        return False
@log_in_out
def getModificationDate(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o
    WHERE {
        { ?dataset a dcat:Dataset ; dcterms:modified ?o . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:modified ?o . }
        UNION
        { ?dataset a void:Dataset ; dcterms:modified ?o . }
    }
    ORDER BY ASC(?o)
    LIMIT 1
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        modification = utils.getResultsFromJSON(results)
        if len(modification) > 0:
            match = re.search(r'\d{4}-\d{2}-\d{2}', modification[0])
            date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
            date = str(date)
            return date
        else:
            return False
    elif isinstance(results,Document):
        modification = utils.getResultsFromXML(results)
        if len(modification) > 0:
            match = re.search(r'\d{4}-\d{2}-\d{2}', modification[0])
            date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
            date = str(date)
            return date
        else:
            return False
    else:
        return False
@log_in_out
def getModificationDateMax(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT (MAX (?modified) AS ?max)
    WHERE {
        { ?dataset a dcat:Dataset ; dcterms:modified ?modified . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:modified ?modified . }
        UNION
        { ?dataset a void:Dataset ; dcterms:modified ?modified . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        modification = utils.getResultsFromJSONMax(results)
        if len(modification) > 0:
            match = re.search(r'\d{4}-\d{2}-\d{2}', modification[0])
            date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
            date = str(date)
            return date
        else:
            return False
    elif isinstance(results,Document):
        modification = utils.getResultsFromXML(results)
        if len(modification) > 0:
            match = re.search(r'\d{4}-\d{2}-\d{2}', modification[0])
            date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
            date = str(date)
            return date
        else:
            return False
    else:
        return False

@log_in_out
def getDateUpdates(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o
    WHERE {
        { ?dataset a dcat:Dataset ; dcterms:modified ?o . }
        UNION
        { ?dataset a dcat:Distribution ; dcterms:modified ?o . }
        UNION
        { ?dataset a void:Dataset ; dcterms:modified ?o . }
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    modificationDate = []
    if isinstance(results,dict):
        modification = utils.getResultsFromJSONo(results)
        if len(modification) > 0:
            for i in range(len(modification)):
                match = re.search(r'\d{4}-\d{2}-\d{2}', modification[i])
                date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
                date = str(date)
                modificationDate.append(date)
            return modificationDate
        else:
            return False
    elif isinstance(results,Document):
        modification = utils.getResultsFromXML(results)
        if len(modification) > 0:
            for i in range(len(modification)):
                match = re.search(r'\d{4}-\d{2}-\d{2}', modification[i])
                date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
                date = str(date)
                modificationDate.append(date)
            return modificationDate
        else:
            return False
    else:
        return False
@log_in_out
def getNumUpdatedData(url,date):
    if date != False:
        sparql = SPARQLWrapper(url)
        sparql.setQuery('''
        PREFIX dcterms:<http://purl.org/dc/terms/>
        SELECT DISTINCT (COUNT(?o) AS ?triples)
        WHERE{
        {?s dcterms:modified ?o}
        FILTER regex(?o,'%s')
        }
        '''%date)
        sparql.setTimeout(150)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            value = utils.getResultsFromJSONCountInt(results)
            return value
        elif isinstance(results,Document):
            value = utils.getResultsFromXMLCount(results)
            return value
    else:
        return False

@log_in_out
def getDeprecated(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?s
    WHERE{
    {?s  rdf:type owl:DeprecatedClass}
    UNION
    {?s rdf:type owl:DeprecatedProperty}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        deprecated = utils.getResultsFromJSONs(results)
        return deprecated
    elif isinstance(results,Document):
         deprecated = utils.getResultsFromXML(results)
         return deprecated
    else:
        return False
@log_in_out
def getLabel(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX skosxl:<http://www.w3.org/2008/05/skos-xl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX awol: <http://bblfish.net/work/atom-owl/2006-06-06/#>
    PREFIX wdrs: <http://www.w3.org/2007/05/powder-s#>
    PREFIX schema: <http://schema.org/>
    SELECT ?o
    WHERE{
    {?s rdfs:label ?o}
    UNION
    {?s foaf:name ?o}
    UNION
    {?s skos:prefLabel ?o}
    UNION
    {?s dcterms:title ?o}
    UNION
    {?s dcterms:decription ?o}
    UNION
    {?s rdfs:comment ?o}
    UNION
    {?s awol:label ?o}
    UNION
    {?s dcterms:alternative ?o}
    UNION
    {?s skos:altLabel ?o}
    UNION
    {?s skos:note ?o}
    UNION
    {?s wdrs:text ?o}
    UNION
    {?s skosxl:altLabel ?o}
    UNION
    {?s skosxl:hiddenLabel ?o}
    UNION
    {?s skosxl:prefLabel ?o}
    UNION
    {?s skosxl:literalForm ?o}
    UNION
    {?s schema:name ?o}
    UNION
    {?s schema:description ?o}
    UNION
    {?s schema:alternateName ?o}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        labelList = utils.getResultsFromJSON(results)
        return labelList
    elif isinstance(results,Document):
        labelList = utils.getResultsFromXML(results)
        return labelList
    else:
        return False
@log_in_out
def getDisjoint(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT (COUNT(?s) AS ?triples) 
    WHERE 
    {?s owl:disjointWith ?o.}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONCountInt(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXMLCount(results)
        return value
    else:
        return False

@log_in_out
def getAllClasses(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?s
    WHERE {?s rdf:type owl:Class}
    """)
    sparql.setTimeout(300) #5 minutes
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONs(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXML(results)
        return value
    else:
        return False
@log_in_out
def getAllProperty(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?o
    WHERE {
    { ?o a rdf:Property}
    UNION
    {?o a owl:DatatypeProperty}
    UNION
    {?o a skos:Property}
    UNION
    {?o a owl:DatatypeProperty}
    UNION
    {?o a owl:AnnotationProperty}
    UNION
    {?o a owl:OntologyProperty}
    UNION
  	{?o a rdfs:subPropertyOf}
  	UNION
  	{?o a rdfs:Property}
    }
    ''') 
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        properties = utils.getResultsFromJSONp(results)
        return properties
    elif isinstance(results,Document):
        properties = utils.getResultsFromXML(results)
        return properties
    else:
        return False

@log_in_out
def getAllType(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?s
    WHERE {?s rdf:type ?o}
    ''')
    sparql.setTimeout(300) #5 minutes
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            properties = utils.getResultsFromJSONs(results)
            return properties
        elif isinstance(results,Document):
            properties = utils.getResultsFromXML(results)
            return properties
        else:
            return False
    except Exception as e :
        return e
@log_in_out
def getAllTypeO(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?o
    WHERE {?s rdf:type ?o}
    ''')
    sparql.setTimeout(300) #5 minutes
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        properties = utils.getResultsFromJSONo(results)
        return properties
    elif isinstance(results,Document):
        properties = utils.getResultsFromXML(results)
        return properties
    else:
        return False

@log_in_out
def getSkosMapping(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT (COUNT(?o) AS ?triples)
    WHERE {
        {?s skos:closeMatch ?o}
        UNION   
        {?s skos:exactMatch ?o}
        UNION   
        {?s skos:broadMatch ?o}
        UNION   
        {?s skos:narrowMatch ?o}
        UNION   
        {?s skos:relatedMatch ?o}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONCountInt(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXMLCount(results)
        return value
    else:
        return False

@log_in_out
def getSkosMapping(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    SELECT (COUNT(?o) AS ?triples)
    WHERE {
        {?s skos:closeMatch ?o}
        UNION   
        {?s skos:exactMatch ?o}
        UNION   
        {?s skos:broadMatch ?o}
        UNION   
        {?s skos:narrowMatch ?o}
        UNION   
        {?s skos:relatedMatch ?o}
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        value = utils.getResultsFromJSONCountInt(results)
        return value
    elif isinstance(results,Document):
        value = utils.getResultsFromXMLCount(results)
        return value
    else:
        return False

@log_in_out
def getAllPropertySP(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?s ?p
    WHERE {
    { ?s ?p rdf:Property}
    UNION
    {?s ?p owl:DatatypeProperty}
    UNION
    {?s ?p skos:Property}
    }
    ''') 
    sparql.setTimeout(300) #10 minutes
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            result = results.get('results')
            bindings = result.get('bindings')
            for el in bindings:
                yield el
        elif isinstance(results,Document): 
            bindings = utils.xmlToDictSP(results)
            for el in bindings:
                yield el
        else:
            return False
    except Exception as e:
        return e

@log_in_out
def getAllTriplesSPO(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT *
    WHERE{?s ?p ?o}
    ''')
    sparql.setTimeout(300) #10 minutes
    sparql.setReturnFormat(JSON)
    format = sparql.query()._get_responseFormat()
    if format == 'xml': #IF THE RETURN FORMAT IS SETTED TO JSON AND XML WAS RETURNED
        query = '''
                SELECT *
                WHERE{?s ?p ?o}
               '''
        results = queryWithSingleAcceptFromat(url,query) #TRY TO GET RESULTS IN JSON BY SETTING A SINGLE ACCEPT HEADER (SOME ENDPOINTS MAY BE NOT SUPPORT MULTIPLE ACCEPT FORMAT)
    else:
        results = sparql.query().convert()
    if isinstance(results,dict):
        result = results.get('results')
        bindings = result.get('bindings')
        return bindings
    elif isinstance(results,Document): 
        bindings = utils.xmlToDictSPO(results)
        return bindings
    else:
        return False

@log_in_out
def getAllPredicate(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT DISTINCT ?p
    WHERE{?s ?p ?o}
    ''')
    sparql.setTimeout(300) #10 minutes
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            result = results.get('results')
            bindings = result.get('bindings')
            for el in bindings:
                p = el.get('p')
                yield p.get('value')
        elif isinstance(results,Document): 
            bindings = utils.xmlToDictP(results)
            for el in bindings:
                p = el.get('p')
                yield p.get('value')
        else:
            return False
    except Exception as e:
        return e

@log_in_out
def getSign(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX swp:<http://www.w3.org/2004/03/trix/swp-2/>
    SELECT ?s ?o
    WHERE{
    {?s swp:signature ?o}
    UNION
    {?s swp:authority ?o}
    UNION
    {?s swp:certificate ?o}
    UNION
    {?s swp:quotedBy ?o}
    UNION
    {?s swp:assertedBy ?o}
    }
    ''')
    sparql.setTimeout(300) #10 minutes
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            result = results.get('results')
            bindings = result.get('bindings')
            return len(bindings)
        elif isinstance(results,Document):
            bindings = utils.xmlToDict(results)
            return len(bindings)
        else:
            return False
    except Exception as e:
        return e
@log_in_out
def getDlc(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT (COUNT(?o) AS ?triples)
    WHERE{?s ?p ?o.
    FILTER(?p NOT IN (rdf:type))
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    try:
        if isinstance(results,dict):
            numDlc = utils.getResultsFromJSONCountInt(results) #BEFORE WITHOUT INT
            return numDlc
        elif isinstance(results,Document):
            numDlc = utils.getResultsFromXMLCount(results)
            return numDlc
        else:
            return False
    except Exception as e:
        return e
@log_in_out
def countStruct(url): 
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
     PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT (COUNT(?s) AS ?triples)
    WHERE{
    {?s rdf:type rdf:List }
    UNION
    {?s rdf:type rdf:Statement}
    UNION
    {?s rdf:type rdf:Alt}
    UNION
    {?s rdf:type rdf:Bag}
    UNION
    {?s rdf:type rdf:Seq}
    UNION
    {?s rdf:type rdf:Container}
    UNION
    {?s rdf:subject ?o}
    UNION
    {?s rdf:predicate ?o}
    UNION
    {?s rdf:object ?o}
    UNION
    {?s rdfs:member ?o}
    UNION
    {?s rdf:first ?o}
    UNION
    {?s rdf:rest ?o}
    UNION
    {?s rdf:_'[0-9]+'}
    }
    """)
    sparql.setTimeout(300) #5 minutes
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        rdfS = utils.getResultsFromJSONCountInt(results) 
        return rdfS
    elif isinstance(results,Document):
        rdfS = utils.getResultsFromXMLCount(results)
        return rdfS
    else:
        return False

@log_in_out
def getNumDlcBN(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT (COUNT(?bnode) AS ?triples)
    WHERE { ?bnode ?p ?o
    FILTER (isBlank(?bnode))
    FILTER (?p NOT IN (rdf:type))
    }
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    sparql.setReturnFormat(JSON) #ASKS TO RECEIVE DATA IN JSON FORMAT IS SUPPORTED
    sparql.setTimeout(300) #5 minutes
    results = sparql.query().convert()
    if isinstance(results,dict):
        numBnode = utils.getResultsFromJSONCountInt(results) #BEFORE WITHOUT INT
        return numBnode
    elif isinstance(results,Document):
        numBnode = utils.getResultsFromXMLCount(results)
        return numBnode
    else:
        return False

@log_in_out
def getNumS(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT (COUNT(?s) AS ?triples)
    WHERE {?s ?p ?o}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    sparql.setReturnFormat(JSON) #ASKS TO RECEIVE DATA IN JSON FORMAT IS SUPPORTED
    sparql.setTimeout(300) #5 minutes
    results = sparql.query().convert()
    if isinstance(results,dict):
        numBnode = utils.getResultsFromJSONCountInt(results) #BEFORE WITHOUT INT
        return numBnode
    elif isinstance(results,Document):
        numBnode = utils.getResultsFromXMLCount(results)
        return numBnode
    else:
        return False
    
@log_in_out
def getIFP(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT *
    WHERE 
    {?s owl:InverseFunctionalProperty ?o.}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        result = results.get('results')
        bindings = result.get('bindings')
        return bindings
    elif isinstance(results,Document): 
            bindings = utils.xmlToDictSPO(results)
            return bindings
    else:
        return False
     
@log_in_out
def getFP(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT *
    WHERE 
    {?s owl:FunctionalProperty ?o.}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        result = results.get('results')
        bindings = result.get('bindings')
        return bindings
    elif isinstance(results,Document): 
            bindings = utils.xmlToDictSPO(results)
            return bindings
    else:
        return False
    
@log_in_out
def getAllPredicate2(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT DISTINCT ?p
    WHERE{?s ?p ?o.}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        uriList = utils.getResultsFromJSONp(results)
        return uriList
    elif isinstance(results,Document):
        uriList = utils.getResultsFromXML(results)
        return uriList
    else:
        return False

@log_in_out
def getAllObject(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT DISTINCT ?o
    WHERE{?s ?p ?o.}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        uriList = utils.getResultsFromJSON(results)
        return uriList
    elif isinstance(results,Document):
        uriList = utils.getResultsFromXML(results)
        return uriList
    else:
        return False

@log_in_out
def getUris(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    SELECT DISTINCT ?s
    WHERE {
    ?s ?p ?o
    FILTER(isIRI(?s))
    }
    ORDER BY RAND()
    LIMIT 5000
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        uriList = utils.getResultsFromJSONs(results)
        return uriList
    elif isinstance(results,Document):
        uriList = utils.getResultsFromXML(results)
        return uriList
    else:
        return False
    

def queryWithSingleAcceptFromat(url,query):
    sparql = SPARQLWrapper(url)
    sparql.setQuery(query)
    sparql.setTimeout(300) #10 minutes
    sparql.addCustomHttpHeader('Accept','application/sparql-results+json') #SOME ENDPOINT DOESN'T SUPPORT MULTIPLE ACCEPT FORMAT
    return sparql.query().convert()

@log_in_out
def get_download_link(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery('''
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    SELECT DISTINCT ?o
    WHERE {?s dcat:downloadURL ?o.}
    ''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        urls = utils.getResultsFromJSON(results)
        return urls
    elif isinstance(results,Document):
        urls = utils.getResultsFromXML(results)
        return urls
    else:
        return False
    
def get_kg_name(url):
    sparql = SPARQLWrapper(url)
    query = """
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dct: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
    {
        ?dataset a dcat:Dataset ;
                dct:title ?o .
    }
    UNION
    {
        ?dataset a void:Dataset ;
                dct:title ?o .
    }
    }
    LIMIT 1
    """
    sparql.setQuery(query)
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        urls = utils.getResultsFromJSON(results)
        if isinstance(urls,list):
            return str(urls[0])
        return urls
    elif isinstance(results,Document):
        urls = utils.getResultsFromXML(results)
        if isinstance(urls,list):
            return urls[0]
        return urls
    else:
        return False  


def get_kg_url(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>

    SELECT DISTINCT ?o
    WHERE {
    {
        ?dataset a void:Dataset ;
                foaf:homepage ?o .
    }
    UNION
    {
        ?dataset a dcat:Dataset ;
                dcat:accessURL ?o .
    }
    }
    LIMIT 1
    """
    sparql.setQuery(query)
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        urls = utils.getResultsFromJSON(results)
        if isinstance(urls,list):
            return urls[0]
        return urls
    elif isinstance(results,Document):
        urls = utils.getResultsFromXML(results)
        if isinstance(urls,list):
            return str(urls[0])
        return urls
    else:
        return False

def get_kg_id(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dct: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
    ?dataset a ?type ;
            dct:identifier ?o .
    FILTER (?type IN (dcat:Dataset, void:Dataset))
    }
    LIMIT 1
    """
    sparql.setQuery(query)
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if isinstance(results,dict):
        urls = utils.getResultsFromJSON(results)
        if isinstance(urls,list):
            return str(urls[0])
        return urls
    elif isinstance(results,Document):
        urls = utils.getResultsFromXML(results)
        return urls
    else:
        return False

def get_kg_void(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery("""
    SELECT ?s ?p ?o
    WHERE {
    ?s a <http://rdfs.org/ns/void#Dataset> .
    ?s ?p ?o .
    }
    """)
    formats = [JSON, XML]
    results = None
    response_format = None

    for fmt in formats:
        sparql.setReturnFormat(fmt)
        try:
            results = sparql.query().convert()
            response_format = fmt
            break
        except Exception as e:
            return False

    if results is None:
        return False

    g = rdflib.Graph()

    if response_format == JSON:
        for result in results["results"]["bindings"]:
            s = rdflib.URIRef(result["s"]["value"])
            p = rdflib.URIRef(result["p"]["value"])
            o_value = result["o"]["value"]
            
            if result["o"]["type"] == "uri":
                o = rdflib.URIRef(o_value)
            else:
                o = rdflib.Literal(o_value)
            
            g.add((s, p, o))

    elif response_format == XML:
        for result in results.getElementsByTagName("result"):
            s = None
            p = None
            o = None
            
            for binding in result.getElementsByTagName("binding"):
                name = binding.getAttribute("name")
                value_node = binding.getElementsByTagName("uri")
                if not value_node:
                    value_node = binding.getElementsByTagName("literal")

                if value_node:
                    value = value_node[0].firstChild.nodeValue
                    if name == "s":
                        s = rdflib.URIRef(value)
                    elif name == "p":
                        p = rdflib.URIRef(value)
                    elif name == "o":
                        o = rdflib.URIRef(value) if binding.getElementsByTagName("uri") else rdflib.Literal(value)

            if s and p and o:
                g.add((s, p, o))
    
    return g

def check_void_dcat(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dct: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?s
    WHERE {
    {?s ?p void:Dataset .}
    UNION
    {?S ?p dcat:Dataset}
    }

    LIMIT 1
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            urls = utils.getResultsFromJSONs(results)
            if isinstance(urls,list):
                return str(urls[0])
            return urls
        elif isinstance(results,Document):
            urls = utils.getResultsFromXML(results)
            return urls
        else:
            return False
    except:
        return False