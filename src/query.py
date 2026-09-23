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
from urllib.parse import quote


PROPERTY_TYPES = (
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#Property',
    'http://www.w3.org/2002/07/owl#DatatypeProperty',
    'http://www.w3.org/2004/02/skos/core#Property',
    'http://www.w3.org/2002/07/owl#AnnotationProperty',
    'http://www.w3.org/2002/07/owl#OntologyProperty',
    'http://www.w3.org/2000/01/rdf-schema#subPropertyOf',
    'http://www.w3.org/2000/01/rdf-schema#Property',
)
_PROPERTY_TYPES = ' '.join('<' + iri + '>' for iri in PROPERTY_TYPES)

_SCHEMA_PREFIXES = '''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
'''

# Shared by the aggregate query and its local fallback.
LABEL_PREDICATES = (
    'http://www.w3.org/2000/01/rdf-schema#label',
    'http://xmlns.com/foaf/0.1/name',
    'http://www.w3.org/2004/02/skos/core#prefLabel',
    'http://purl.org/dc/terms/title',
    'http://purl.org/dc/terms/decription',
    'http://www.w3.org/2000/01/rdf-schema#comment',
    'http://bblfish.net/work/atom-owl/2006-06-06/#label',
    'http://purl.org/dc/terms/alternative',
    'http://www.w3.org/2004/02/skos/core#altLabel',
    'http://www.w3.org/2004/02/skos/core#note',
    'http://www.w3.org/2007/05/powder-s#text',
    'http://www.w3.org/2008/05/skos-xl#altLabel',
    'http://www.w3.org/2008/05/skos-xl#hiddenLabel',
    'http://www.w3.org/2008/05/skos-xl#prefLabel',
    'http://www.w3.org/2008/05/skos-xl#literalForm',
    'http://schema.org/name',
    'http://schema.org/description',
    'http://schema.org/alternateName',
)


def log_in_out(func):

    def decorated_func(*args, **kwargs):
        print("Doing ", func.__name__)
        result = func(*args, **kwargs)
        print("Done ")
        return result

    return decorated_func


def _query(url, query_text, return_format=JSON, timeout=300):
    sparql = SPARQLWrapper(url)
    if len(query_text) > 2000:
        sparql.setMethod(POST)
    sparql.setQuery(query_text)
    sparql.setTimeout(timeout)
    sparql.setReturnFormat(return_format)
    return sparql.query().convert()


def _extract(results, json_reader, xml_reader, default=False):
    if isinstance(results, dict):
        return json_reader(results)
    if isinstance(results, Document):
        return xml_reader(results)
    return default


def _select_values(url, query_text, json_reader=None, xml_reader=None, timeout=300, default=False):
    # Resolve readers at call time because utils also imports query.
    if json_reader is None:
        json_reader = utils.getResultsFromJSON
    if xml_reader is None:
        xml_reader = utils.getResultsFromXML
    return _extract(_query(url, query_text, timeout=timeout), json_reader, xml_reader, default)


def _select_count(url, query_text, timeout=300):
    return _select_values(url, query_text, utils.getResultsFromJSONCountInt, utils.getResultsFromXMLCount, timeout)


def _select_bindings(url, query_text, timeout=300, xml_reader=None):
    if xml_reader is None:
        xml_reader = utils.xmlToDictSPO
    results = _query(url, query_text, timeout=timeout)
    if isinstance(results, dict):
        return results.get('results', {}).get('bindings', [])
    if isinstance(results, Document):
        return xml_reader(results)
    return False


def getFiveStarDatasetLicenses(url):
    return _select_bindings(url, '''
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX cc: <http://creativecommons.org/ns#>
        SELECT DISTINCT ?s ?p ?o WHERE {
            { ?s a <http://www.w3.org/ns/dcat#Dataset> }
            UNION { ?s a <http://rdfs.org/ns/void#Dataset> }
            ?s ?p ?o .
            FILTER (?p IN (dct:license, dc:license, cc:license,
                           <http://schema.org/license>, <https://schema.org/license>))
        } LIMIT 20
    ''', timeout=30)


def getFiveStarExternalLinks(url):
    return _select_bindings(url, '''
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?s ?p ?o WHERE {
            ?s ?p ?o .
            FILTER (?p IN (owl:sameAs, <http://schema.org/sameAs>,
                <https://schema.org/sameAs>, skos:exactMatch, skos:closeMatch,
                skos:broadMatch, skos:narrowMatch, skos:relatedMatch))
            FILTER (isIRI(?s) && isIRI(?o))
            FILTER (REGEX(STR(?s), "^https?://", "i") && REGEX(STR(?o), "^https?://", "i"))
            FILTER (LCASE(REPLACE(STR(?s), "^https?://([^/]+).*$", "$1", "i")) !=
                    LCASE(REPLACE(STR(?o), "^https?://([^/]+).*$", "$1", "i")))
        } LIMIT 5
    ''', timeout=30)


def _select_exists(url, query_text, timeout=300):
    bindings = _select_bindings(url, query_text, timeout, utils.xmlToDict)
    if isinstance(bindings, list):
        return len(bindings) > 0
    return False


def _first_or_value(value):
    if isinstance(value, list):
        if len(value) > 0:
            return value[0]
        return False
    return value


def _parse_first_date(values):
    if not values:
        return False
    match = re.search(r'\d{4}-\d{2}-\d{2}', values[0])
    date = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
    return str(date)


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

def check_if_up(url):
    sparql = SPARQLWrapper(url)
    sparql.setQuery("""
        SELECT ?s ?p ?o
        WHERE { ?s ?p ?o }
        LIMIT 1
    """)
    sparql.setTimeout(300)  # 5 minutes

    try:
        # Try JSON first
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        if "results" in results and "bindings" in results["results"]:
            bindings = results["results"]["bindings"]
            if len(bindings) > 0:
                return True
            else:
                return False
    except Exception as e_json:
        try:
            sparql.setReturnFormat(XML)
            xml_data = sparql.query().convert()
            root = ET.fromstring(xml_data)
            results = root.findall(".//{http://www.w3.org/2005/sparql-results#}result")

            if len(results) > 0:
                return True
            else:
                return False
        except Exception as e_xml:
            return False

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
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            languages = utils.getResultsFromJSONCount(results)
            return languages
        elif isinstance(results,Document): #IF RESULT IS IN XML 
            languages = utils.getResultsFromXML(results)
            return languages
        else:
            return False
    except Exception as e:
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
    return _select_values(url, '''
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX void: <http://rdfs.org/ns/void#>

        SELECT ?o
        WHERE {
        VALUES ?type { dcat:Dataset dcat:Distribution void:Dataset }
        VALUES ?prop { dcat:mediaType void:feature dcterms:format dcat:compressFormat dcat:packageFormat }

        ?dataset a ?type ;
                ?prop ?o .
        }
    ''')

@log_in_out
def checkDataDump(url):
    return _select_values(url, '''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o 
    WHERE 
    {?s void:dataDump ?o}
    ''')

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
    try:
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
    except Exception as e:
        return False
    
@log_in_out
def checkLicenseMR2(url):   #USED IN CASE THE QUERY WITH VALUES ISN'T SUPPORTED
    return _select_values(url, '''
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
@log_in_out
def checkLicenseHR(url):
    return _select_exists(url, '''
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
@log_in_out
def numberOfProperty(url):
    return _select_count(url, '''
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
@log_in_out
def getNumLabel(url):
    return _select_count(url, '''
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
@log_in_out
def checkUriRegex(url):
    return _select_values(url, '''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o 
    WHERE{
    {?s void:uriRegexPattern ?o}
    UNION
    {?s void:uriPattern ?o}
    }
    ''')
@log_in_out
def checkUriPattern(url):
    return _select_values(url, '''
    PREFIX void: <http://rdfs.org/ns/void#>
    SELECT DISTINCT ?o 
    WHERE
    {?s void:uriSpace ?o}
    ''')
@log_in_out
def getVocabularies(url):
    return _select_values(url, '''
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
@log_in_out
def getCreator(url):
    return _select_values(url, '''
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
@log_in_out
def getPublisher(url):
    return _select_values(url, '''
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
@log_in_out
def getNumEntities(url):
    entities = _select_values(url, '''
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    SELECT DISTINCT ?o
    WHERE {
    { ?dataset a void:Dataset ; void:entities ?o . }
    UNION
    { ?dataset a dcat:Dataset ; void:entities ?o . }
    UNION
    { ?dataset a dcat:Distribution ; void:entities ?o . }
    }
    ''')
    return int(_first_or_value(entities))
    
@log_in_out
def getNumEntitiesRegex(url,entityRe):
    return _select_count(url, '''
   SELECT (COUNT(?s) as ?triples)
   WHERE{
   {?s ?p ?o}
   FILTER(regex(?s,"%s"))
   }
    '''%entityRe, timeout=200)
@log_in_out
def getContributors(url):
    return _select_values(url, '''
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
@log_in_out
def getSameAsChains(url):
    return _select_count(url, '''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX schema: <http://schema.org/>
    SELECT (COUNT(?o) AS ?triples)
    WHERE {
        {?s owl:sameAs ?o}
        UNION
        {?s schema:sameAs ?o}
    }
    ''')
@log_in_out
def getFrequency(url):
    return _select_values(url, '''
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
@log_in_out
def getCreationDate(url):
    return _parse_first_date(_select_values(url, '''
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
    )
@log_in_out
def getCreationDateMin(url):
    return _parse_first_date(_select_values(url, '''
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
    }
    ''', utils.getResultsFromJSONMin, utils.getResultsFromXML))
@log_in_out
def getModificationDate(url):
    return _parse_first_date(_select_values(url, '''
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
    )
@log_in_out
def getModificationDateMax(url):
    return _parse_first_date(_select_values(url, '''
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
    ''', utils.getResultsFromJSONMax, utils.getResultsFromXML))

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
    return _select_values(url, '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT ?s
    WHERE{
    {?s  rdf:type owl:DeprecatedClass}
    UNION
    {?s rdf:type owl:DeprecatedProperty}
    }
    ''', utils.getResultsFromJSONs, utils.getResultsFromXML)
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
def getLabelQualityCounts(url):
    """Return only aggregate counts for the annotation predicates we check."""
    predicates = ' '.join('<' + iri + '>' for iri in LABEL_PREDICATES)
    rows = _select_bindings(url, r'''
    SELECT (COUNT(*) AS ?total)
           (SUM(IF(isLiteral(?o) && STR(?o) = "", 1, 0)) AS ?empty)
           (SUM(IF(isLiteral(?o) && REGEX(STR(?o), "^\\s|\\s$"), 1, 0)) AS ?whitespace)
    WHERE {
        VALUES ?p {''' + predicates + r'''}
        ?s ?p ?o
    }
    ''', timeout=30)
    return {key: int(rows[0][key]['value']) for key in ('total', 'empty', 'whitespace')}


@log_in_out
def getDisjoint(url):
    return _select_count(url, '''
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT DISTINCT (COUNT(?s) AS ?triples) 
    WHERE 
    {?s owl:disjointWith ?o.}
    ''')

@log_in_out
def getAllClasses(url):
    return _select_values(url, """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?s
    WHERE {?s rdf:type owl:Class}
    """, utils.getResultsFromJSONs, utils.getResultsFromXML)
@log_in_out
def getAllProperty(url):
    conditions = ' || '.join('?type = <' + iri + '>' for iri in PROPERTY_TYPES)
    return _select_values(url, _SCHEMA_PREFIXES + '''
    SELECT DISTINCT ?o
    WHERE {
        ?o a ?type
        FILTER (''' + conditions + ''')
    }
    ''', utils.getResultsFromJSONo, utils.getResultsFromXML)


@log_in_out
def getMisplacedClassCount(url):
    """Count the existing misplaced-class condition without returning triples."""
    return _select_count(url, _SCHEMA_PREFIXES + '''
    SELECT (COUNT(*) AS ?triples)
    WHERE {
        ?s ?p ?o
        FILTER (
            (isIRI(?s) && EXISTS {
                VALUES ?type {''' + _PROPERTY_TYPES + '''}
                ?s a ?type
            }) ||
            (isIRI(?o) && EXISTS {
                VALUES ?type {''' + _PROPERTY_TYPES + '''}
                ?o a ?type
            })
        )
    }
    ''', timeout=30)


@log_in_out
def getUntypedSubjectCounts(url):
    """Group candidates for the existing undefined-class heuristic by subject."""
    return _select_bindings(url, '''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT ?s (COUNT(*) AS ?triples)
    WHERE {
        ?s ?p ?o
        FILTER(isIRI(?s))
        FILTER NOT EXISTS { ?s rdf:type ?type }
    }
    GROUP BY ?s
    ''', timeout=30)

@log_in_out
def getAllType(url, subjects=None):
    try:
        restriction = ''
        if subjects is not None:
            subjects = sorted(set(subjects))
            if not subjects:
                return []
            restriction = 'VALUES ?s { ' + ' '.join(rdflib.URIRef(s).n3() for s in subjects) + ' }'
        return _select_values(url, '''
        PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        SELECT DISTINCT ?s
        WHERE {''' + restriction + ''' ?s rdf:type ?o}
        ''', utils.getResultsFromJSONs, utils.getResultsFromXML, timeout=30 if subjects is not None else 300)
    except Exception as e :
        return e
@log_in_out
def getAllTypeO(url):
    return _select_values(url, '''
    PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    SELECT DISTINCT ?o
    WHERE {?s rdf:type ?o}
    ''', utils.getResultsFromJSONo, utils.getResultsFromXML)

@log_in_out
def getSkosMapping(url):
    return _select_count(url, '''
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
def getAllTriplesSPO(url, limit=None):
    """Fetch a bounded preview, or request all triples when limit is None."""
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError('limit must be a positive integer or None')
    query_text = 'SELECT ?s ?p ?o WHERE { ?s ?p ?o }'
    if limit is not None:
        query_text += f' LIMIT {limit}'
    return _select_bindings(url, query_text, timeout=30 if limit is not None else 300)

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
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(300) #5 minutes
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            numBnode = utils.getResultsFromJSONCountInt(results) #BEFORE WITHOUT INT
            return numBnode
        elif isinstance(results,Document):
            numBnode = utils.getResultsFromXMLCount(results)
            return numBnode
        else:
            return False
    except Exception:
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
       PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX void: <http://rdfs.org/ns/void#>

        SELECT ?o
        WHERE {
        VALUES ?type { dcat:Dataset dcat:Distribution void:Dataset }
        VALUES ?prop {  void:dataDump dcat:downloadURL }
        ?dataset a ?type ;
                ?prop ?o .
        }''')
    sparql.setTimeout(300)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            urls = utils.getResultsFromJSON(results)
            return urls
        elif isinstance(results,Document):
            urls = utils.getResultsFromXML(results)
            return urls
        else:
            return False
    except Exception:
        return False

@log_in_out
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

@log_in_out
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

@log_in_out
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

@log_in_out
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

@log_in_out
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
    {?s ?p dcat:Dataset}
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

@log_in_out
def check_acc_feature(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
        PREFIX schema: <https://schema.org/>

        SELECT ?o
        WHERE {
        ?s schema:accessibilityFeature ?o .
        }
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False

@log_in_out
def get_all_metadata_obj(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
        PREFIX void: <http://rdfs.org/ns/void#>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>

        SELECT DISTINCT ?o
        WHERE {
        {
            ?dataset a void:Dataset ;
                   ?p ?o .
        }
        UNION
        {
            ?dataset a dcat:Dataset ;
                    ?p ?o .
        }
        }
        """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False

@log_in_out
def get_version(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX schema: <https://schema.org/>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
    {
        ?dataset a void:Dataset ;
                dcat:hasVersion ?o .
    }
    UNION
    {
        ?dataset a dcat:Dataset ;
                dcat:hasVersion ?o .
    }
    UNION
    {
        ?dataset a void:Dataset ;
                dcterms:hasVersion ?o .
    }
    UNION
    {
        ?dataset a dcat:Dataset ;
                dcterms:hasVersion ?o .
    }
    }
    LIMIT 1
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False
    
@log_in_out
def get_identifier(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX schema: <https://schema.org/>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
        ?dataset a ?type ;
                ?p ?o .
        VALUES ?type { void:Dataset dcat:Dataset }
        VALUES ?p { dcterms:bibliographicCitation dcterms:identifier schema:identifier }
    }
    LIMIT 1
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False

@log_in_out
def get_contact_point(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
        ?dataset a ?type ;
                ?p ?o .
        VALUES ?type { void:Dataset dcat:Dataset }
        VALUES ?p { dcat:contactPoint }
    }
    LIMIT 1
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False    
    
@log_in_out
def get_string_literals(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    # We have to recover it like this because the string with the language tag is not recognized as a string with datatype xsd:string
    #?lang is empty if no lang tag is present or is xsd:string
    query = """
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT ?o (lang(?o) AS ?lang)
    WHERE { 
        ?s ?p ?o .
        FILTER ( isLiteral(?o) && (datatype(?o) = xsd:string || lang(?o) != "") )
    }
                
    """
    try:
        sparql = SPARQLWrapper(endpoint_url)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        # Store triples in list as (object, lang)
        triples_list = []
        for result in results["results"]["bindings"]:
            obj = result["o"]["value"]
            lang = result.get("lang", {}).get("value", "")
            triples_list.append((obj, lang))

        # Count totals
        total_count = len(triples_list)
        lang_filtered_count = sum(1 for _, lang in triples_list if lang and lang != "xsd:string")

        return total_count, lang_filtered_count
    except Exception as e:
        return False
        
@log_in_out
def get_examples(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX schema: <https://schema.org/>

    SELECT DISTINCT ?o
    WHERE {
            ?dataset a void:Dataset ;
                    void:exampleResource ?o .
    } """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False
    

@log_in_out
def get_apis_url(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
        PREFIX void: <http://rdfs.org/ns/void#>
        PREFIX dcat: <http://www.w3.org/ns/dcat#>
        PREFIX dcterms: <http://purl.org/dc/terms/>

        SELECT DISTINCT ?o
        WHERE {
            ?dataset a ?type ;
                    ?p ?o .
            VALUES ?type { void:Dataset dcat:Dataset dcat:Distribution }
            VALUES ?p { void:uriLookupEndpoint dcat:accessURL dcat:endpointURL }
        }
        LIMIT 1
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except:
        return False

@log_in_out
def count_res_with_label(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery('''
        PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX awol: <http://bblfish.net/work/atom-owl/2006-06-06/#>
        PREFIX wdrs: <http://www.w3.org/2007/05/powder-s#>
        PREFIX schema: <http://schema.org/>

        SELECT (COUNT(DISTINCT ?s) AS ?triples)
        WHERE {
        { ?s rdfs:label ?o }
        UNION { ?s foaf:name ?o }
        UNION { ?s skos:prefLabel ?o }
        UNION { ?s dcterms:title ?o }
        UNION { ?s dcterms:description ?o }
        UNION { ?s rdfs:comment ?o }
        UNION { ?s awol:label ?o }
        UNION { ?s dcterms:alternative ?o }
        UNION { ?s skos:altLabel ?o }
        UNION { ?s skos:note ?o }
        UNION { ?s wdrs:text ?o }
        UNION { ?s skosxl:altLabel ?o }
        UNION { ?s skosxl:hiddenLabel ?o }
        UNION { ?s skosxl:prefLabel ?o }
        UNION { ?s skosxl:literalForm ?o }
        UNION { ?s schema:name ?o }
        UNION { ?s schema:description ?o }
        UNION { ?s schema:alternateName ?o }
        }

    ''')
    try:
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
    except Exception as e:
        print(e)
        return False

@log_in_out
def count_res(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery('''
        SELECT (COUNT(DISTINCT ?s) AS ?triples)
        WHERE {
        ?s ?p ?o .
        }''')
    try:
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
    except Exception as e:
        print(e)
        return False

@log_in_out
def getImagesTriples(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery('''
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX schema: <https://schema.org/>

    SELECT ?o
    WHERE {
    ?subject ?predicate ?image .
    FILTER (REGEX(STR(?image), "(?i)\\.(jpg|jpeg|png|gif|svg)$"))
    }
    ''')
    try:
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
    except Exception as e:
        print(e)
        return False

@log_in_out
def getImageIri(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery('''
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX schema: <http://schema.org/>
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX sioc: <http://rdfs.org/sioc/ns#>
    PREFIX exif: <http://www.w3.org/2003/12/exif/ns#>
    PREFIX dcmitype: <http://purl.org/dc/dcmitype/>

    SELECT DISTINCT ?o
    WHERE {
    VALUES ?prop {
        foaf:depiction dcterms:thumbnail foaf:img foaf:thumbnail schema:image schema:photo 
        schema:logo schema:thumbnail schema:thumbnailUrl foaf:image schema:contentUrl 
        dbo:thumbnail dbo:image sioc:avatar wdt:P18 <http://example.org/hasImage> exif:image dcmitype:Image
    }
    ?resource ?prop ?o .
    }''')
    try:
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            value = utils.getResultsFromJSON(results)
            return value
        elif isinstance(results,Document):
            value = utils.getResultsFromXML(results)
            return value
        else:
            return False
    except Exception as e:
        return False

@log_in_out
def hasAltDescription(endpoint_url,iri_to_check):
    sparql = SPARQLWrapper(endpoint_url)
    encoded_iri = quote(iri_to_check, safe="/:#?&=%")
    sparql.setQuery(f"""
    PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX awol: <http://bblfish.net/work/atom-owl/2006-06-06/#>
    PREFIX wdrs: <http://www.w3.org/2007/05/powder-s#>
    PREFIX schema: <http://schema.org/>
    SELECT ?o
    WHERE {{
        VALUES ?prop {{ rdfs:label foaf:name schema:alternateName dcterms:description skos:prefLabel dcterms:alternative skos:altLabel dcterms:title
                     rdfs:comment awol:label dcterms:alternative skos:altLabel skos:note wdrs:text skosxl:altLabel skosxl:hiddenLabel skosxl:prefLabel
                     skosxl:literalForm schema:name schema:description schema:alternateName }}
        <{encoded_iri}> ?prop ?o .}}
        """)
    try:
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            value = utils.getResultsFromJSON(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        elif isinstance(results,Document):
            value = utils.getResultsFromXML(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        else:
            return False, []
    except Exception as e:
        return e

@log_in_out
def fetch_objects(endpoint_url, limit=10000, condition = ()):
    sparql = SPARQLWrapper(endpoint_url)
    offset = 0
    count = 0

    while True:
        query = f"""
        SELECT DISTINCT ?o
        WHERE {{
            ?s ?p ?o .
            FILTER(isIRI(?o))
        }}
        ORDER BY ?o
        LIMIT {limit}
        OFFSET {offset}
        """
        try:
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if not bindings:
                break  # no more results

            for result in bindings:
                o = result["o"]["value"].lower()
                if o.endswith(condition):
                    count += 1
            offset += limit
        
        except Exception as e:
            return count
    return count

@log_in_out
def fetch_subjects(endpoint_url, limit=1000, condition = ()):
    sparql = SPARQLWrapper(endpoint_url)
    offset = 0
    count = 0

    while True:
        query = f"""
        SELECT DISTINCT ?s
        WHERE {{
            ?s ?p ?s .
            FILTER(isIRI(?s))
        }}
        ORDER BY ?s
        LIMIT {limit}
        OFFSET {offset}
        """
        try:
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if not bindings:
                break  # no more results

            for result in bindings:
                o = result["s"]["value"].lower()
                if len(condition) > 0 and o.endswith(condition):
                    count += 1
                elif len(condition) == 0:
                    count += 1
            offset += limit
        except Exception as e:
            return e
    return count

@log_in_out
def fetch_objects_value(endpoint_url, limit=10000, condition = ()):
    sparql = SPARQLWrapper(endpoint_url)
    offset = 0
    values = []

    while True:
        query = f"""
        SELECT DISTINCT ?o
        WHERE {{
            ?s ?p ?o .
            FILTER(isIRI(?o))
        }}
        ORDER BY ?o
        LIMIT {limit}
        OFFSET {offset}
        """
        try:
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if not bindings:
                break  # no more results

            for result in bindings:
                o = result["o"]["value"].lower()
                if o.endswith(condition):
                    values.append(o)
            offset += limit
            
            return values
        except Exception as e:
            return e
    
@log_in_out
def count_audio_objects_sparql(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
        SELECT (COUNT(DISTINCT ?o) AS ?audioCount)
        WHERE {
        ?s ?p ?o .
        FILTER(isIRI(?o)) .
        FILTER(REGEX(STR(?o), "\\\\.(mp3|wav|flac|ogg|m4a|aac|wma|aiff)$", "i"))
        }
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            return int(results["results"]["bindings"][0]["audioCount"]["value"])
        elif isinstance(results,Document):
            value = utils.getResultsFromXMLCount(results)
            return value
        else:
            return False
    except Exception as e:
        return e
    
@log_in_out
def check_video_presence(endpoint_url, limit = 10000):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
        SELECT ?o
        WHERE {
        ?s ?p ?o .
        FILTER(isIRI(?o)) .
        FILTER(REGEX(STR(?o), "\\\\.(mp4|avi|mov|wmv|flv|mkv|webm|mpeg|mpg)$", "i"))
        }
    """
    if limit:
        query += f"LIMIT {limit}"
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            value = utils.getResultsFromJSON(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        elif isinstance(results,Document):
            value = utils.getResultsFromXML(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        else:
            return False, []
    except Exception as e:
        return e, []
    

@log_in_out
def check_audio_presence(endpoint_url, limit = True):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
        SELECT ?o
        WHERE {
        ?s ?p ?o .
        FILTER(isIRI(?o)) .
        FILTER(REGEX(STR(?o), "\\\\.(mp3|wav|flac|ogg|m4a|aac|wma|aiff)$", "i"))
        }
    """
    if limit:
        query += f"LIMIT {limit}"
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            value = utils.getResultsFromJSON(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        elif isinstance(results,Document):
            value = utils.getResultsFromXML(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        else:
            return False, []
    except Exception as e:
        return e, []
    
def get_all_obj_in_meta(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
        ?dataset a ?type ;
                ?p ?o .
        VALUES ?type { void:Dataset dcat:Dataset dcat:Distribution}
    }
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except Exception as e:
        return e
    
@log_in_out
def check_sign_language(endpoint_url, iri_to_check):
    encoded_iri = quote(iri_to_check, safe="/:#?&=%")
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery(f"""
    PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    PREFIX awol: <http://bblfish.net/work/atom-owl/2006-06-06/#>
    PREFIX wdrs: <http://www.w3.org/2007/05/powder-s#>
    PREFIX schema: <http://schema.org/>
    PREFIX dct: <http://purl.org/dc/terms/>
    SELECT ?o
    WHERE {{
        VALUES ?prop {{ rdfs:label foaf:name schema:alternateName dcterms:description skos:prefLabel dcterms:alternative skos:altLabel dcterms:title
                     rdfs:comment awol:label dcterms:alternative skos:altLabel skos:note wdrs:text skosxl:altLabel skosxl:hiddenLabel skosxl:prefLabel
                     skosxl:literalForm schema:name schema:description schema:alternateName schema:inLanguage schema:accessMode schema:accessibilityFeature dct:language}}
        <{encoded_iri}> ?prop ?o .}}
        """)
    try:
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            value = utils.getResultsFromJSON(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        elif isinstance(results,Document):
            value = utils.getResultsFromXML(results)
            if isinstance(value,list) and len(value)>0:
                return True, value
            else:
                return False, []
        else:
            return False, []
    except Exception as e:
        return e, []
    
def getDescription(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    query = """
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX dcterms: <http://purl.org/dc/terms/>

    SELECT DISTINCT ?o
    WHERE {
        ?dataset a ?type ;
                ?p ?o .
        VALUES ?type { void:Dataset dcat:Dataset dcat:Distribution }
        VALUES ?p { dcterms:description }
    }
    """
    try:
        sparql.setQuery(query)
        sparql.setTimeout(300)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except Exception as e:
        return e
    
def get_metadata_languages(endpoint_url):
    sparql = SPARQLWrapper(endpoint_url)
    sparql.setQuery('''
    PREFIX void: <http://rdfs.org/ns/void#>
    PREFIX dcat: <http://www.w3.org/ns/dcat#>
    PREFIX dcterms: <http://purl.org/dc/terms/>
    PREFIX schema: <https://schema.org/>

    SELECT DISTINCT ?o
    WHERE {
        ?dataset a ?type ;
                ?p ?o .
        VALUES ?type { void:Dataset dcat:Dataset dcat:Distribution }
        VALUES ?p { dcterms:language schema:inLanguage }
    }''')
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(300)
    try:
        results = sparql.query().convert()
        if isinstance(results,dict):
            triples = utils.getResultsFromJSON(results)
            return triples
        elif isinstance(results,Document):
            triples = utils.getResultsFromXML(results)
            return triples
        else:
            return False
    except Exception as e:
        return e
