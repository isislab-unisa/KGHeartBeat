import datetime
import re
from rdflib import DCAT, Graph, URIRef, Namespace
from rdflib.namespace import DC, DCTERMS, DOAP, FOAF, SKOS, OWL, RDF, RDFS, VOID, XMLNS, XSD


def parseVoID(url):
    g = Graph()
    fmt = 'ttl' if url.lower().endswith('.ttl') else None
    g.parse(url, format=fmt)
    return g

def parseVoIDTtl(url):
    g = Graph()
    g.parse(url,format='ttl')
    return g

def printVoID(graph):
    for s,p,o in graph:
        print(s,p,o)

def getVocabularies(graph):
    vocabularies = []
    for s, p, o in graph:
        if p == VOID.vocabulary:
            o = str(o)
            vocabularies.append(o)
    newVocabularies = []
    [newVocabularies.append(x) for x in vocabularies if x not in newVocabularies] #DUPLICATE REMOVAL IF PRESENT
    return(newVocabularies)

def getCreationDate(graph):
    date = []
    for s,p,o in graph:
        if p == DCTERMS.created or DCTERMS.issued:
            o = str(o)
            match = re.search(r'\d{4}-\d{2}-\d{2}', o)
            if match is not None:
                o = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
                date.append(o)
    if len(date) > 0:       
        return min(date)
    else:
        return 'absent'

def getModificationDate(graph):
    date = []
    for s,p,o in graph:
        if p == DCTERMS.modified:
            o = str(o)
            match = re.search(r'\d{4}-\d{2}-\d{2}', o)
            if match is not None:
                o = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
                date.append(o)
    if len(date) > 0:       
        return max(date)
    else:
        return 'absent'

def getDataDump(graph):
    for s,p,o in graph:
        if p == VOID.dataDump or p == DCAT.downloadURL:
            o = str(o)
            return o
    return 'absent'

def getLicense(graph):
    for s,p,o in graph:
        if p == DCTERMS.license:
            o = str(o)
            return o
    return 'absent'

def getCreators(graph):
    creators = []
    for s,p,o in graph:
        if p == DCTERMS.creator or DC.creator:
            o = str(o)
            creators.append(o)
    if len(creators) > 0:       
        return creators
    else:
        return 'absent'

def getPublishers(graph):
    publishers = []
    for s,p,o in graph:
        if p == DCTERMS.publisher or p == DC.publisher:
            o = str(o)
            publishers.append(o)
    if len(publishers) > 0:       
        return publishers
    else:
        return 'absent'

def getContributors(graph):
    contributors = []
    for s,p,o in graph:
        if p == DCTERMS.contributor or p == DC.contributor:
            o = str(o)
            contributors.append(o)
    if len(contributors) > 0:       
        return contributors
    else:
        return 'absent'

def getNumEntities(graph):
    for s,p,o in graph:
        if p == VOID.entities:
            o = str(o)
            if o != '':       
                return o
            else:
                return 'absent'
    return 'information abaout entities absent'

def getFrequency(graph):
    for s,p,o in graph:
        if p == DCTERMS.Frequency or p == DCTERMS.accrualPeriodicity:
            o = str(o)
            if o != '':       
                return o
            
    return 'absent'

def getUriRegex(graph):
    regex = []
    for s,p,o in graph:
        if p == VOID.uriRegexPattern or VOID.uriSpace:
            o = str(o)
            regex.append(o)
    if len(regex) > 0:       
        return regex
    else:
        return 'absent'

def getSerializationFormats(graph):
    formats = []
    for s,p,o in graph:
        if p == VOID.feature or DCAT.mediaType or DCTERMS.format:
            o = str(o)
            formats.append(o)
    if len(formats) > 0:       
        return formats
    else:
        return 'absent'

def getLanguage(graph):
    formats = []
    for s,p,o in graph:
        if p == DCTERMS.language or DC.language:
            o = str(o)
            formats.append(o)
    if len(formats) > 0:       
        return formats
    else:
        return 'absent'

def getDistinctO(graph):
    objects = []
    for s,p,o in graph:
        if p == VOID.distinctObjects:
            o = str(o)
            objects.append(o)
    if len(objects) > 0:       
        return objects
    else:
        return 'absent'

def getDistinctS(graph):
    subjects = []
    for s,p,o in graph:
        if p == VOID.distinctSubjects:
            o = str(o)
            subjects.append(o)
    if len(subjects) > 0:       
        return subjects
    else:
        return 'absent'

def getProperties(graph):
    properties = []
    for s,p,o in graph:
        if p == VOID.properties:
            o = str(o)
            properties.append(o)
    if len(properties) > 0:       
        return properties
    else:
        return 'absent'

def getClasses(graph):
    classes = []
    for s,p,o in graph:
        if p == VOID.classes:
            o = str(o)
            classes.append(o)
    if len(classes) > 0:       
        return classes
    else:
        return 'absent'
    
def check_acc_feature(graph):
    schema = Namespace("https://schema.org/")
    if (None, schema.accessibilityFeature, None) in graph:
        return True
    else:
        return False
    
def get_all_obj(graph):
    objects = []
    for s,p,o in graph:
        o = str(o)
        objects.append(o)
    return objects

def get_version(graph):
    for s,p,o in graph:
        if p == DCAT.hasVersion or DCTERMS.hasVersion:
            o = str(o)
            return o
    return False

def get_identifier(graph):
    schema = Namespace("https://schema.org/")
    for s,p,o in graph:
        if p == DCTERMS.identifier or p == schema.identifier or DCTERMS.bibliographicCitation:
            o = str(o)
            return o
    return False

def get_contact_point(graph):
    for s,p,o in graph:
        if p == DCAT.contactPoint:
            o = str(o)
            return o
    return False

def getExamples(graph):
    examples = []
    for s,p,o in graph:
        if p == VOID.exampleResource:
            o = str(o)
            examples.append(o)
    if len(examples) > 0:       
        return examples
    else:
        return False

def getSparqlEndpoint(graph):
    for s,p,o in graph:
        if p == VOID.sparqlEndpoint:
            o = str(o)
            return o
    return False

def getAccessPoint(graph):
    for s,p,o in graph:
        if p == VOID.uriLookupEndpoint or p == DCAT.accessURL or p == DCAT.endpointURL:
            o = str(o)
            return o
    return False