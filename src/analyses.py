from ctypes import util
from dataclasses import replace
import datetime
from html import entities
from operator import sub
import re
import socket
from string import whitespace
from tabnanny import check
import time
from xml.dom.minidom import Document
from xml.parsers import expat
import json
from rdflib import VOID
import requests
from KnowledgeGraph import KnowledgeGraph
from QualityDimensions.Accuracy import Accuracy
from QualityDimensions.Availability import Availability
from QualityDimensions.Believability import Believability
from QualityDimensions.Completeness import Completeness
from QualityDimensions.Conciseness import Conciseness
from QualityDimensions.Consistency import Consistency
from QualityDimensions.Currency import Currency
from QualityDimensions.Extra import Extra
from QualityDimensions.Interlinking import Interlinking
from QualityDimensions.Interpretability import Interpretability
from QualityDimensions.Licensing import Licensing
from QualityDimensions.Performance import Performance
from QualityDimensions.RepresentationalConciseness import RepresentationalConciseness
from QualityDimensions.RepresentationalConsistency import RepresentationalConsistency
from QualityDimensions.Reputation import Reputation
from QualityDimensions.Security import Security
from QualityDimensions.Understendability import Understendability
from QualityDimensions.Verifiability import Verifiability
from QualityDimensions.Versatility import Versatility
from QualityDimensions.Volatility import Volatility
from Sources import Sources
from bloomfilter import BloomFilter
import utils
from API import Aggregator
from API import LOVAPI
from SPARQLWrapper import *
from SPARQLWrapper import SPARQLExceptions
from urllib.error import HTTPError, URLError
import urllib.request
import query
import numpy
import Graph
import networkx as nx
import VoIDAnalyses
import QualityDimensions.AmountOfData
import ssl
import score
from score import Score
import os
import logging


def analyses(analysis_date,idKG = None,nameKG = None, sparql_endpoint = None):
    
    utils.skipCheckSSL() #IGNORE THE ERROR  [SSL: CERTIFICATE_VERIFY_FAILED] 
    available = False
    isHTML = False
    absent = False
    restricted = False
    void = False
    internalError = False
    queryNotSupported = False
    availableDump = '-'

    if (idKG):
        metadata = Aggregator.getDataPackage(idKG)
        if nameKG == '':
            nameKG = Aggregator.getNameKG(metadata)
        accessUrl = Aggregator.getSPARQLEndpoint(idKG)
    elif sparql_endpoint:
        accessUrl = sparql_endpoint
        try:
            nameKG = query.get_kg_name(accessUrl)
        except:
            nameKG = ''
        try:
            idKG = query.get_kg_id(accessUrl)
        except:
            idKG = ''
        metadata = None
        if idKG == '':
            try:
                idKG = query.get_kg_url(accessUrl)
            except:
                idKG = ''

    if idKG == '' or idKG == False:
        idKG = sparql_endpoint
    if nameKG == '' or nameKG == False:
        nameKG = sparql_endpoint

    #Set log format
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(kg_id)s | %(kg_name)s | %(message)s')
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(levelname)s | %(kg_id)s | %(kg_name)s | %(message)s')

    #Set format also for the root logger, to follow the same format also for the log on console
    root_logger = logging.getLogger()
    root_logger.handlers[0].setFormatter(formatter) 
    
    #Logger configuration
    logger = logging.getLogger('KG analysis')
    logger.setLevel(logging.DEBUG)
    
    #Handler to write log on file
    here = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(here,'../Analysis results')
    save_path = os.path.join(save_path, analysis_date+".log")
    file_handler = logging.FileHandler(save_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    #Handler to write log on console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    
    logger.handlers = []
    logger.addHandler(file_handler)

    kg_info = {"kg_id": f"{idKG}", "kg_name" : f"{nameKG}" }
    logger.info('Analysis started...',extra=kg_info)

    logger.info(f"SPARQL endpoint link: {accessUrl}",extra=kg_info)
    endpoint = ''
    start_analysis = time.time()
    if accessUrl == False: #CHECK IF THE SPARQL END POINT LINK IS IN THE METADATA
        endpoint = '-'
        logger.warning('SPARQL endpoint missing in the metadata',extra=kg_info)
        absent = True
        available = False
    else:
        try:
            result = query.checkEndPoint(accessUrl)
            if isinstance(result,bytes):
                newUrl = utils.checkRedirect(accessUrl) #IF WE GET HTML IN THE RESPONSE, CHECK IF THE ENDPOINT IS NOW AT ANOTHER ADDRESS
                result = query.checkEndPoint(newUrl)
                if isinstance(result,bytes):
                     endpoint = '-'
                     logger.warning('The result from the SPARQL endpoint is not structured data (HTML data returned)',extra=kg_info)
                     available = False
                else:
                    endpoint = 'Available'
                    available = True
                    accessUrl = newUrl
            else:
                endpoint = 'Available'
                available = True
        except(HTTPError,URLError,SPARQLExceptions.EndPointNotFound,socket.gaierror) as response: #IF THERE IS ONE OF THESE EXCEPTION, ENDPOINT IS OFFLINE
            endpoint = '-'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
        except SPARQLExceptions.EndPointInternalError as response: #QUERY NOT SUPPORTED
            endpoint = '-'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
        except(json.JSONDecodeError, SPARQLExceptions.QueryBadFormed,expat.ExpatError) as response: # NO AUTOMATICALLY (?), Error decoding the response
            endpoint = '-'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
        except(SPARQLExceptions.Unauthorized) as response: #RESTRICTED ACCCESS TO THE ENDPOINT
            endpoint = 'Restricted access to the endpoint'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
            restricted = True
        except Exception as error:
            logger.warning('Availability | SPARQL endpoint availability | ' + str(error),extra=kg_info)
            endpoint = 'offline'
            available = False
        
    
    if available == False and absent == False:  
        try: 
            newUrl = utils.checkRedirect(accessUrl) #TEST OF ACCESS TO THE ENDPOINT IN CASE OF REDIRECT ON ADDRESS
            if newUrl != accessUrl:
                result = query.checkEndPoint(newUrl)
                if isinstance(result,Document) or isinstance(result,dict):
                    accessUrl = newUrl
                    available = True
                    endpoint = 'Available'
        except(HTTPError,URLError,SPARQLExceptions.EndPointNotFound,socket.gaierror) as response: 
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
        except SPARQLExceptions.EndPointInternalError as response:
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info) 
            endpoint = '-'
        except(json.JSONDecodeError, SPARQLExceptions.QueryBadFormed,expat.ExpatError) as response:
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            endpoint = '-'
            available = False
        except(SPARQLExceptions.Unauthorized) as response:
            endpoint = 'restricted access to the endpoint'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
            restricted = True
        except Exception as error:
            logger.warning('Availability | SPARQL endpoint availability | ' + str(error),extra=kg_info)
            endpoint = 'offline'
            available = False
    
    #GET THE SOURCE OF THE DATASET
    sources = Aggregator.getSource(metadata)
    if sources == False:
        sourcesC = Sources('absent','absent','absent')
    else:
        sourcesC = Sources(sources.get('web','Absent'),sources.get('name','Absent'),sources.get('email','Absent'))
    if sourcesC.web == 'Absent':
        kg_uri = query.get_kg_url(accessUrl)
        if kg_uri:
            sourcesC.web = kg_uri
    if available == False and absent == False and sourcesC.web != 'absent': #TRY TO ACCESS AT THE SPARQL ENDPOINT ADDING \sparql AT THE END OF THE DATASET URL
        try:
            newUrl = sourcesC.web + '/sparql'
            result = query.checkEndPoint(newUrl)
            if isinstance(result,Document) or isinstance(result,dict):
                accessUrl = newUrl
                available = True
                endpoint = 'Available'
                logger.info(f"SPARQL endpoint link: {accessUrl}",extra=kg_info)
        except(HTTPError,URLError,SPARQLExceptions.EndPointNotFound,socket.gaierror) as response: #IF THERE IS ONE OF THESE EXCEPTION, ENDPOINT IS OFFLINE
            endpoint = '-'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
        except SPARQLExceptions.EndPointInternalError as response: #QUERY NOT SUPPORTED
            endpoint = '-'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
        except(json.JSONDecodeError, SPARQLExceptions.QueryBadFormed,expat.ExpatError) as response: # NO AUTOMATICALLY (?), Error decoding the response
            endpoint = '-'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
        except(SPARQLExceptions.Unauthorized) as response: #RESTRICTED ACCCESS TO THE ENDPOINT
            endpoint = 'Restricted access to the endpoint'
            logger.warning('Availability | SPARQL endpoint availability | ' + str(response),extra=kg_info)
            available = False
            restricted = True
        except Exception as error:
            logger.warning('Availability | SPARQL endpoint availability | ' + str(error),extra=kg_info)
            endpoint = 'offline'
            available = False
    end_analysis = time.time()
    utils.write_time(nameKG,end_analysis-start_analysis,'SPARQL endpoint availability check','Availability',analysis_date)
    
    #GET NUMBERS OF TRIPLES FROM METADATA
    triplesM = Aggregator.getTriples(metadata)
    try:
        triplesM = int(triplesM)
    except ValueError:
        triplesM = 0
     
    #GET OTHER RESOURCES OF THE DATASET
    resourcesDH = Aggregator.getOtherResources(idKG)
    
    #CHECK THE AVAILABILITY OF THE URL IN THE RESOURCES LIST AND ADDING A FIELD STATUS. STATUS = ACTIVE IF THE URL IS ONLINE, STATUS = OFFLINE IF THE URL IS OFFLINE
    resourcesDH = utils.insertAvailability(resourcesDH)

    #CHECK AVAILABILITY FOR DOWNLOAD OF THE DATASET
    downloadUrl = [] 
    offlineDump = []
    availableDownload = utils.checkAvailabilityForDownload(resourcesDH)
    downloadUrl = downloadUrl + utils.getLinkDownload(resourcesDH)
    offlineDump = offlineDump + utils.getLinkOfflineDump(resourcesDH)

    otResources = utils.toObjectResources(resourcesDH) #CREATING A LIST OF RESOURCES OBJECT

    metadata_media_type = utils.extract_media_type(resourcesDH)
    
    #CHECK THE AVAILABILITY OF VOID FILE
    start_analysis = time.time()
    urlV = utils.getUrlVoID(otResources)
    voidStatus = ''
    void = False
    if utils.is_valid_void_url(urlV):
        if isinstance(urlV,str):
            try:
                voidFile = VoIDAnalyses.parseVoID(urlV)
                void = True
                voidStatus = 'VoID file available'
            except:
                try:
                    voidFile = VoIDAnalyses.parseVoIDTtl(urlV)
                    void = True
                    voidStatus = 'VoID file available'
                except:
                    void = False 
                    voidStatus = 'VoID file offline'
        if void == False and not isinstance(urlV,str) and sourcesC.web != 'absent' and sourcesC.web != 'Absent':
            urlV = sourcesC.web + '/.well-known/void'
            try:
                voidFile = VoIDAnalyses.parseVoID(urlV)
                void = True
                voidStatus = 'VoID file available'
                logger.info(f"VoID file link: {urlV}",extra=kg_info)
            except:
                try:
                    voidFile = VoIDAnalyses.parseVoIDTtl(urlV)
                    void = True
                    voidStatus = 'VoID file available'
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        voidStatus = 'VoID file absent'
                    else:
                        void = False
                        voidStatus = 'VoID file offline'
                except urllib.error.URLError as e:
                    voidStatus = 'VoID file absent'
                except Exception as e:
                    void = False
                    voidStatus = 'VoID file offline'
        if not isinstance(urlV,str):
            voidStatus = 'VoID file absent'
    else:
        voidStatus = 'VoID file absent'
    logger.info(f"VoID file link: {urlV}",extra=kg_info)
    end_analysis = time.time()
    utils.write_time(nameKG,end_analysis-start_analysis,'VoID file availability check', 'Availability',analysis_date)

    logger.info(f"SPARQL endpoint availability: {available}",extra=kg_info)

    if available == True:    #IF ENDOPOINT IS ONLINE WE GET ALL NECESSARY INFORMATION FROM THE ENDPOINT

        start_analysis = time.time()
         #TRY TO GET ALL TRIPLES (IMPORTANT FOR CALCULATING VARIOUS METRICS)
        allTriples = []
        try:
            allTriples = query.getAllTriplesSPO(accessUrl)
        except:
            logger.warning('Impossible to recover all the triples in the KG',extra=kg_info)
            allTriples = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Recovery of all triples', 'Extra',analysis_date)
        
        #GET LATENCY (MIN-MAX-AVERAGE)
        try:
            start_analysis = time.time()
            latency = query.testLatency(accessUrl)     
            sumLatency = sum(latency)
            av = sumLatency/len(latency)
            minL = min(latency)
            maxL = max(latency)
            standardDeviation = numpy.std(latency)
            sumLatency = str(sumLatency)
            percentile25L = numpy.percentile(latency,25)
            percentile75L = numpy.percentile(latency,75)
            medianL = numpy.median(latency)
            av = "%.3f"%av
            av = str(av)
            minL = "%.3f"%minL
            minL = str(minL)
            maxL = "%.3f"%maxL
            maxL = str(maxL)
            standardDeviation = "%.3f"%standardDeviation
            standardDeviation = str(standardDeviation)
            sumLatency = sumLatency.replace('.',',')
            av = av.replace('.',',')
            minL = minL.replace('.',',')
            maxL = maxL.replace('.',',')
            standardDeviation = standardDeviation.replace('.',',')
            percentile25L = "%.3f"%percentile25L
            medianL = "%.3f"%medianL
            percentile75L = "%.3f"%percentile75L
            percentile25L = str(percentile25L)
            percentile75L = str(percentile75L)
            medianL = str(medianL)
            percentile25L = percentile25L.replace('.',',')
            percentile75L = percentile75L.replace('.',',')
            medianL = medianL.replace('.',',')
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Total latancy measurement', 'Performance',analysis_date)
           
        except urllib.error.HTTPError as response:
            logger.warning(f'Performance | Latency | {str(response)}',extra=kg_info)
            responseStr = '-'
            av = responseStr
            minL = responseStr
            maxL = responseStr
            standardDeviation = responseStr
            percentile25L = responseStr
            percentile75L = responseStr
            medianL = responseStr
        except SPARQLExceptions.QueryBadFormed:
            logger.warning('Performance | Latency | Query bad formed',extra=kg_info)
            responseStr = '-'
            av = responseStr
            minL = responseStr
            maxL = responseStr
            standardDeviation = responseStr
            percentile25L = responseStr
            percentile75L = responseStr
            medianL = responseStr
        except SPARQLExceptions.EndPointInternalError:
            logger.warning('Performance | Latency | SPARQL endpoint internal error',extra=kg_info)
            responseStr = '-'
            av = responseStr
            minL = responseStr
            maxL = responseStr
            standardDeviation = responseStr
            percentile25L = responseStr
            percentile75L = responseStr
            medianL = responseStr
        except Exception as error:
            logger.error('Performance | Latency | ' + str(error),extra=kg_info)
            responseStr = '-'
            av = responseStr
            minL = responseStr
            maxL = responseStr
            standardDeviation = responseStr
            percentile25L = responseStr
            percentile75L = responseStr
            medianL = responseStr

        #GET THE TRIPLES WITH A QUERY
        start_analysis = time.time()
        try:
            triplesQuery = query.getNumTripleQuery(accessUrl)   
        except urllib.error.HTTPError as response:
            logger.warning(f'Error while counting the number of triples: {str(response)}',extra=kg_info)
            triplesQuery = '-'
        except(SPARQLExceptions.QueryBadFormed,SPARQLExceptions.EndPointInternalError) as response:
            logger.warning(f'Error while counting the number of triples: {str(response)}',extra=kg_info)
            triplesQuery = '-'
        except Exception as error:
            logger.warning(f'Error while counting the number of triples: {str(error)}',extra=kg_info)
            triplesQuery = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Number of triples check', 'Amount of data',analysis_date)

        #CHECK IF RESULTS FROM SPARQL ENDPOINT IS LIMITED
        if isinstance(allTriples,list) and isinstance(triplesQuery,int):
            if len(allTriples) < triplesQuery:
                limited = True
                logger.warning(f'The number of triples that can be retrieved from the sparql endpoint is limited',extra=kg_info)
            else:
                limited = False
        else:
            limited = 'impossible to verify'

        #CHECK IF NEW TERMS ARE DECLARED IN THE DATASET
        newTermsD = []
        triplesO = []
        try:
            start_analysis = time.time()
            objectList = []
            triplesO = query.getAllTypeO(accessUrl)
            newTermsD = LOVAPI.searchTermsList(triplesO)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'New terms check', 'Interoperability',analysis_date)
        except Exception as error:
            logger.warning(f'Representational-consistency | Reuse of terms | {str(error)}',extra=kg_info)
            newTermsD = '-'

        #GET THE LANGUAGE OF KG
        start_analysis = time.time()
        try:
            languages = query.getLangugeSupported(accessUrl)  
        except urllib.error.HTTPError as response:
            languages = response
        except (SPARQLExceptions.QueryBadFormed,SPARQLExceptions.EndPointNotFound) as response:
            logger.warning(f'Versatility | Languages | Query not supported or endpoint not found',extra=kg_info)
            languages = '-'
        except Exception as error:
            logger.warning(f'Versatility | Languages | {str(error)}',extra=kg_info)
            languages = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Languages check','Versatility',analysis_date)

        #GET THE NUMBER OF THE BLANK NODE
        start_analysis = time.time()
        try:
            numBlankNode = query.numBlankNode(accessUrl)  
        except urllib.error.HTTPError as response:
            logger.warning(f'Interpretability | Number of blank nodes | HTTP error',extra=kg_info)
            numBlankNode = '-'  
        except (SPARQLExceptions.QueryBadFormed,SPARQLExceptions.EndPointInternalError) as response:    
            logger.warning(f'Interpretability | Number of blank nodes | {str(response)}',extra=kg_info)
            numBlankNode = '-'
        except Exception as error:
            logger.warning(f'Interpretability | Number of blank nodes | {str(error)}',extra=kg_info)
            numBlankNode = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Number of blank nodes check', 'Interpretability',analysis_date)
        
        #CHECK IF SPARQL ENDPOINT USE HTTPS
        try:
            start_analysis = time.time()
            sec_access_url = accessUrl.replace('http','https')
            isSecure = query.checkEndPoint(sec_access_url)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check HTTPS', 'Security',analysis_date)
            if isinstance(isSecure,Document) or isinstance(isSecure,dict):
                isSecure = True  
        except:  #IF WE GET A SPARQL QUERY ON URL WITH HTTPS AND GET AN EXCEPTION THEN ENDPOINT ISN'T AVAILABLE ON HTTPS
            isSecure = False

        #CHECK IF IT USES RDF STRUCTURES   
        start_analysis = time.time()
        try:
            RDFStructures = query.checkRDFDataStructures(accessUrl)
        except Exception as error:
            logger.warning(f'Representational-conciseness | Use of RDF structures | {str(error)}',extra=kg_info)
            RDFStructures = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'RDF structures check','Interpretability',analysis_date) 
        
        #CHECK IF THERE ARE DIFFERENT SERIALISATION FORMATS
        start_analysis = time.time()
        try:
            formats = query.checkSerialisationFormat(accessUrl)   #CHECK IF THE LINK IS ONLINE
        except Exception as error:
            logger.warning(f'Versatility | Serialization formats | {str(error)}',extra=kg_info)
            formats = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Serialization formats check', 'Versatility',analysis_date) 

        #CHECK FOR DOWNLOAD LINKS FOR THE DATASET WITH DCAT PREDICATE
        dcat_links = []
        try:
            other_download_links = query.get_download_link(accessUrl)
            for link in other_download_links:
                status = utils.checkAvailabilityResource(link)
                if status == True:
                    dcat_links.append(link)
        except Exception as error:
            logger.warning('Versatility | Languages | Download links, error during query with the dcat:downloadURL predicate',extra=kg_info)
        
        #CHECK IF IN THE DATASET IS INDICATED THE LINK TO DONWLOAD THE DATASET
        start_analysis = time.time()
        try:
            urlList = query.checkDataDump(accessUrl)
            if isinstance(urlList,list):
                availableDump = utils.checkAvailabilityListResources(urlList)
                urlsDump = utils.getActiveDumps(urlList)
                urlsInactive = utils.getInactiveDumps(urlList)
                downloadUrl = downloadUrl + urlsDump
                offlineDump = offlineDump + urlsInactive
            else:
                availableDump = 'absent'
        except Exception as error:
            logger.warning(f'Availability | RDF dump| {str(error)}',extra=kg_info)
            availableDump = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'RDF dump link check','Availability',analysis_date) 
        
        #CHEK IF THERE IS AN INDICATION OF A LICENSE MACHINE REDEABLE
        start_analysis = time.time()
        try:
            licenseMr = query.checkLicenseMR2(accessUrl)
            if isinstance(licenseMr,list):
                licenseMr = licenseMr[0]
        except Exception as error:
            licenseMr = '-'
            logger.warning(f'Licensing | Machine-redeable license | {str(error)}',extra=kg_info)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'MR license check','License',analysis_date) 
        
        #CHECK IF THERE IS AN INDICATION OF A LICENSE HUMAN REDEABLE
        start_analysis = time.time()
        try:
            licenseHr = query.checkLicenseHR(accessUrl)
        except (SPARQLExceptions.QueryBadFormed,SPARQLExceptions.EndPointInternalError) as response:
            licenseHr = '-'
            logger.warning(f'Licensing | Human-redeable license | {str(response)}',extra=kg_info)
        except Exception as error:
            licenseHr = '-'
            logger.warning(f'Licensing | Human-redeable license | {str(error)}',extra=kg_info)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'HR license check', 'License',analysis_date) 

        #CHECK NUMBER OF PROPERTY
        start_analysis = time.time()
        try:
            numProperty = query.numberOfProperty(accessUrl)
        except Exception as error:
            numProperty = '-'
            logger.warning(f'Amount of data | Number of properties | {str(error)}',extra=kg_info)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Number of property check','Amount of data',analysis_date) 
        
        #GET NUMBER OF TRIPLES WITH LABEL
        start_analysis = time.time()
        try:
            numLabel = query.getNumLabel(accessUrl)
        except Exception as error:
            numLabel = '-'
            logger.warning(f'Amount of data | Number of labels | {str(error)}',extra=kg_info)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Number of label check','Understandability',analysis_date) 
        
        #GET THE REGEX OF THE URLs USED
        start_analysis = time.time()
        regex = []
        try:
            regex = query.checkUriRegex(accessUrl)
        except Exception as error:
            logger.warning(f'Understandability | URIs regex | {str(error)}',extra=kg_info)
            regex = '-'
        
        #CHECK IF IS INDICATED A URI SPACE INSTEAD OF A REGEX AND WE TRAFORM IT TO REGEX
        try:    
            pattern = query.checkUriPattern(accessUrl)  
            if isinstance(pattern,list):
                for i in range(len(pattern)): 
                    newRegex = utils.trasforrmToRegex(pattern[i])
                    regex.append(newRegex)
        except Exception as error:
            logger.warning(f'Understandability | URIs regex | {str(error)}',extra=kg_info)
            pattern = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'URI regex check', 'Understandability',analysis_date) 
        
        #GET THE VOCABULARIES OF THE KG
        start_analysis = time.time()
        try:
            vocabularies = query.getVocabularies(accessUrl)
        except Exception as error:
            logger.warning(f'Understandability | Vocabularies | {str(error)}',extra=kg_info)
            vocabularies = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Vocabs check', 'Understandability',analysis_date) 
        
        #GET THE AUTHOR OF THE DATASET WITH A QUERY
        start_analysis = time.time()
        try:
            authorQ = query.getCreator(accessUrl)
        except Exception as error:
            logger.warning(f'Verifiability | Verifiying publisher information | {str(error)}',extra=kg_info)
            authorQ = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Authors check', 'Verifiability',analysis_date) 

        #GET THE PUBLISHERS OF THE DATASET
        start_analysis = time.time()
        try:
            publisher = query.getPublisher(accessUrl)
        except Exception as error:
            publisher = '-'
            logger.warning(f'Verifiability | Verifiying publisher information | {str(error)}',extra=kg_info)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Publishers check', 'Verifiability',analysis_date)

        #GET THE THROUGHPUT
        try:
            start_analysis = time.time()
            countList = utils.getThroughput(accessUrl)
            minThroughput = min(countList)
            maxThroughput = max(countList)
            sumThroughput = sum(countList)
            averageThroughput = sumThroughput/len(countList)
            standardDeviationT = numpy.std(countList)
            percentile25T = numpy.percentile(countList,25)
            percentile75T = numpy.percentile(countList,75)
            medianT = numpy.median(countList)
            percentile25T = str(percentile25T)
            percentile25T = percentile25T.replace('.',',')
            percentile75T = str(percentile75T)
            percentile75T = percentile75T.replace('.',',')
            medianT = str(medianT)
            medianT = medianT.replace('.',',')
            standardDeviationT = str(standardDeviationT)
            standardDeviationT = standardDeviationT.replace('.',',')
            averageThroughput = str(averageThroughput)
            averageThroughput = averageThroughput.replace('.',',')
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Throughput check', 'Performance',analysis_date)
        except Exception as error:
            logger.warning(f'Performance | High Throughput | {str(error)}',extra=kg_info)
            errorResponse = '-'
            minThroughput = errorResponse
            maxThroughput = errorResponse
            averageThroughput = errorResponse
            standardDeviationT = errorResponse
            percentile25T = errorResponse
            percentile75T = errorResponse
            medianT = errorResponse

        #GET THE THROUGHPUT NO OFFSET
        try:
            countListNoOff = utils.getThroughputNoOff(accessUrl)
            minThroughputNoOff = min(countListNoOff)
            maxThroughputNoOff = max(countListNoOff)
            sumThroughputNoOff = sum(countListNoOff)
            averageThroughputNoOff = sumThroughput/len(countListNoOff)
            standardDeviationTNoOff = numpy.std(countListNoOff)
            standardDeviationTNoOff = str(standardDeviationT)
            standardDeviationTNoOff = standardDeviationT.replace('.',',')
            averageThroughputNoOff = str(averageThroughput)
            averageThroughputNoOff = averageThroughput.replace('.',',')
        except Exception as error:
            logger.warning(f'Performance | High Throughput | {str(error)}',extra=kg_info)
            errorResponseNoOff = '-'
            minThroughputNoOff = errorResponseNoOff
            maxThroughputNoOff = errorResponseNoOff
            averageThroughputNoOff = errorResponseNoOff
            standardDeviationTNoOff = errorResponseNoOff


       #GET NUMBER OF ENTITIES
        start_analysis = time.time()
        try:
            numEntities = query.getNumEntities(accessUrl)
        except Exception as error:
            logger.warning(f'Amount of data | Scope | {str(error)}',extra=kg_info)
            numEntities = '-'

        #GET NUMBER OF ENTITIES WITH REGEX
        try:
            if len(regex) > 0:
                entitiesRe = 0
                for i in range(len(regex)):
                    entitiesRe = entitiesRe + query.getNumEntitiesRegex(accessUrl,regex[i])
            else:
                entitiesRe = '-'
                logger.warning(f'Amount of data | Scope | Insufficient data',extra=kg_info)
        except Exception as error:
            logger.warning(f'Amount of data | Scope | {str(error)}',extra=kg_info)
            etitiesRe = '-'
        
        if not(isinstance(entitiesRe,int)) or entitiesRe == 0: #IF CONTROL WITH SPARQL ENDPOINT FAILS WE COUNT THE ENTITY BY RECOVERING ALL THE TRIPLES
            try:
                start_analysis = time.time()
                if isinstance(allTriples,list) and isinstance(regex,list):
                    if len(regex) > 0:
                        entitiesRe = 0
                        for i in range(len(regex)):
                            r = regex[i]
                            for j in range(len(allTriples)):
                                s = allTriples[j].get('s')
                                valueS = s.get('value')
                                if utils.checkString(r,valueS) == True:
                                    entitiesRe = entitiesRe + 1
                        entitiesRe = str(entitiesRe)
                        entitiesRe = entitiesRe + f" (out of {len(allTriples )} triples considered)"
                    else:
                        logger.warning(f'Amount of data | Scope | Insufficient data',extra=kg_info)
                        entitiesRe = '-'
                else:
                    entitiesRe = '-'
                    logger.warning(f'Amount of data | Scope | Insufficient data',extra=kg_info)
                end_analysis = time.time()
                utils.write_time(nameKG,end_analysis-start_analysis,'Check the number of entities', 'Amount of data',analysis_date)
            except Exception as error:
                logger.warning(f'Amount of data | Scope | {str(error)}',extra=kg_info)
                entitiesRe = '-'
    
        #GET THE CONTRIBUTORS OF THE DATASET
        start_analysis = time.time()
        try:
            contributors = query.getContributors(accessUrl)
        except Exception as error:
            logger.warning(f'Verifiability | Verifiying publisher information | {str(error)}',extra=kg_info)
            contributors = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Contribs. check', 'Verifiability',analysis_date)
        
        #GET THE NUMBER OF sameAs CHAINS
        start_analysis = time.time()
        try:
            numberSameAs = query.getSameAsChains(accessUrl)
        except Exception as error:
            logger.warning(f'Interlinking | sameAs chains | {str(error)}',extra=kg_info)
            numberSameAs = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'sameAs chians check', 'Interlinking',analysis_date)
        
        #GET THE NUMBER OF SKOS-Mapping properties
        start_analysis = time.time()
        try:
            numberSkosMapping = query.getSkosMapping(accessUrl)
        except Exception as error:
            logger.warning(f'Interlinking | SKOS Mapping properties | {str(error)}',extra=kg_info)
            numberSkosMapping = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'skos check', 'Interlinking',analysis_date)
        
        #GET THE NUMBER OF SKOS-Mapping properties
        start_analysis = time.time()
        try:
            numberSkosMapping = query.getSkosMapping(accessUrl)
        except Exception as error:
            logger.warning(f'Interlinking | SKOS Mapping properties | {str(error)}',extra=kg_info)
            numberSkosMapping = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'skos check', 'Interlinking',analysis_date)
        
        #GET THE DATASET UPDATE FREQUENCY
        start_analysis = time.time()
        try:
            frequency = query.getFrequency(accessUrl)
        except Exception as error:
            logger.warning(f'Volatility | Timeliness frequency | {str(error)}',extra=kg_info)
            frequency = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'dataset update frequency check', 'Timeliness',analysis_date)
        
        #GET THE CREATION DATE
        start_analysis = time.time()
        try:
            creationDate = query.getCreationDateMin(accessUrl)
            if creationDate == False or creationDate == '':
                creationDate = query.getCreationDate(accessUrl)
        except:
            try:
                creationDate = query.getCreationDate(accessUrl)
            except Exception as error:
                logger.warning(f'Currency | Age of data | {str(error)}',extra=kg_info)
                creationDate = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Creation date check', 'Currency',analysis_date)

        #GET THE LAST MODIFICATION DATE OF THE DATASET
        start_analysis = time.time()
        try:
            modificationDate = query.getModificationDateMax(accessUrl)
            if modificationDate == False or modificationDate == '':
                modificationDate = query.getModificationDate(accessUrl)
        except:
            try:
                modificationDate = query.getModificationDate(accessUrl)
            except Exception as error:
                logger.warning(f'Currency | Specification of the modification date of statements | {error}',extra=kg_info)
                modificationDate = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Modification date check', 'Currency',analysis_date)

        #GET HISTORICAL UPDATES
        historicalUp = []
        try:
            historicalUp = []
            dateUpdates = query.getDateUpdates(accessUrl)
            if isinstance(dateUpdates,list):
                newL = list(set(dateUpdates))
                newL.sort(key=lambda date: datetime.datetime.strptime(date,"%Y-%m-%d"))
                for i in newL:
                    i = str(i)
                    num = query.getNumUpdatedData(accessUrl,i)
                    valueUp = f"{i}|{num}"
                    valueUp = valueUp.strip()
                    historicalUp.append(valueUp)                    
        except Exception as error:
            logger.warning(f'Currency | Update history | {str(error)}',extra=kg_info)
            historicalUp = '-'

        #GET THE NUMBER OF TRIPLES UPDATED
        try:
            numTriplesUpdated = query.getNumUpdatedData(accessUrl,modificationDate)
        except Exception as error:
            logger.warning(f'Currency | Number of triples updated | {str(error)}',extra=kg_info)
            numTriplesUpdated = '-'

        #URI LENGHT CALCULATION (SUBJECT)
        start_analysis = time.time()
        try:
            lenghtList = []
            logger.info(f'Calculating the URIs length...',extra=kg_info)
            for i in range(len(allTriples)):
                s = allTriples[i].get('s')
                uri = s.get('value')
                if utils.validateURI(uri) == True:
                    lenghtList.append(len(uri))  
            sumLenghts = sum(lenghtList)
            avLenghts = sumLenghts/len(lenghtList) 
            avLenghts = str(avLenghts)
            avLenghts = avLenghts.replace('.',',')
            avLenghts = avLenghts + f" (out of {len(allTriples)} triples considered)"
            standardDeviationL = numpy.std(lenghtList)
            standardDeviationL = str(standardDeviationL)
            standardDeviationL = standardDeviationL.replace('.',',')
            minLenghtS = min(lenghtList)
            maxLenghtS = max(lenghtList)
            medianLenghtS = numpy.median(lenghtList)
            percentile25LenghtS = numpy.percentile(lenghtList,25)
            percentile75LenghtS = numpy.percentile(lenghtList,75)
            minLenghtS = str(minLenghtS)
            maxLenghtS = str(maxLenghtS)
            medianLenghtS = str(medianLenghtS)
            percentile25LenghtS = str(percentile25LenghtS)
            percentile75LenghtS = str(percentile75LenghtS)
            minLenghtS = minLenghtS.replace('.',',')
            maxLenghtS = maxLenghtS.replace('.',',')
            medianLenghtS = medianLenghtS.replace('.',',')
            percentile25LenghtS = percentile25LenghtS.replace('.',',')
            percentile75LenghtS = percentile75LenghtS.replace('.',',')
        except Exception as error:
            logger.warning(f'Representational-conciseness | Keeping URI short | {str(error)}',extra=kg_info)
            errorMessage = '-'
            standardDeviationL = errorMessage
            avLenghts = errorMessage
            minLenghtS = errorMessage
            maxLenghtS = errorMessage
            medianLenghtS = errorMessage
            percentile25LenghtS = errorMessage
            percentile75LenghtS = errorMessage

        #URI LENGHT CALCULATION (OBJECT)
        allUri = []
        try:
            uriListO = query.getAllObject(accessUrl)
            lenghtListO = []
            for i in range(len(uriListO)):
                uriO = uriListO[i]
                if utils.validateURI(uriO) == True:
                    lenghtListO.append(len(uriO))
            sumLenghtsO = sum(lenghtListO)
            avLenghtsO = sumLenghtsO/len(lenghtListO) 
            avLenghtsO = str(avLenghtsO)
            avLenghtsO = avLenghtsO.replace('.',',')
            avLenghtsO = avLenghtsO+f" (out of {len(uriListO)} triples considered)"
            standardDeviationLO = numpy.std(lenghtListO)
            standardDeviationLO = str(standardDeviationLO)
            standardDeviationLO = standardDeviationLO.replace('.',',')
            minLenghtO = min(lenghtListO)
            maxLenghtO = max(lenghtListO)
            medianLenghtO = numpy.median(lenghtListO)
            percentile25LenghtO = numpy.percentile(lenghtListO,25)
            percentile75LenghtO = numpy.percentile(lenghtListO,75)
            minLenghtO = str(minLenghtO)
            maxLenghtO = str(maxLenghtO)
            medianLenghtO = str(medianLenghtO)
            percentile25LenghtO = str(percentile25LenghtO)
            percentile75LenghtO = str(percentile75LenghtO)
            minLenghtO = minLenghtO.replace('.',',')
            maxLenghtO = maxLenghtO.replace('.',',')
            medianLenghtO = medianLenghtO.replace('.',',')
            percentile25LenghtO = percentile25LenghtO.replace('.',',')
            percentile75LenghtO = percentile75LenghtO.replace('.',',')
        except Exception as error:
            logger.warning(f'Representational-conciseness | Keeping URI short | {str(error)}',extra=kg_info)
            errorMessage = '-'
            uriListO = errorMessage
            avLenghtsO = errorMessage
            standardDeviationLO = errorMessage
            minLenghtO = errorMessage
            maxLenghtO = errorMessage
            medianLenghtO = errorMessage
            percentile25LenghtO = errorMessage
            percentile75LenghtO = errorMessage

        #URI LENGHT CALCULATION (PREDICATE)
        try:
            uriListP = query.getAllPredicate2(accessUrl)
            lenghtListP = []
            for i in range(len(uriListP)):
                uriP = uriListP[i]
                if utils.validateURI(uriP) == True:
                    lenghtListP.append(len(uriP))
            sumLenghtsP = sum(lenghtListP)
            avLenghtsP = sumLenghtsP/len(lenghtListP) 
            avLenghtsP = str(avLenghtsP)
            avLenghtsP = avLenghtsP.replace('.',',')
            avLenghtsP = avLenghtsP+f" (out of {len(uriListP)} triples considered)"
            standardDeviationLP = numpy.std(lenghtListP)
            standardDeviationLP = str(standardDeviationLP)
            standardDeviationLP = standardDeviationLP.replace('.',',')
            minLenghtP = min(lenghtListP)
            maxLenghtP = max(lenghtListP)
            medianLenghtP = numpy.median(lenghtListP)
            percentile25LenghtP = numpy.percentile(lenghtListP,25)
            percentile75LenghtP = numpy.percentile(lenghtListP,75)
            minLenghtP = str(minLenghtP)
            maxLenghtP = str(maxLenghtP)
            medianLenghtP = str(medianLenghtP)
            percentile25LenghtP = str(percentile25LenghtP)
            percentile75LenghtP = str(percentile75LenghtP)
            minLenghtP = minLenghtP.replace('.',',')
            maxLenghtP = maxLenghtP.replace('.',',')
            medianLenghtP = medianLenghtP.replace('.',',')
            percentile25LenghtP = percentile25LenghtP.replace('.',',')
            percentile75LenghtP = percentile75LenghtP.replace('.',',')

        except Exception as error:
            logger.warning(f'Representational-conciseness | Keeping URI short | {str(error)}',extra=kg_info)
            errorMessage = '-'
            uriListP = errorMessage
            avLenghtsP = errorMessage
            standardDeviationLP = errorMessage
            minLenghtP = errorMessage
            maxLenghtP = errorMessage
            medianLenghtP = errorMessage
            percentile25LenghtP = errorMessage
            percentile75LenghtP = errorMessage
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'URIs length', 'Rep.Conc.',analysis_date)

        #A LIST OF ALL URIs IS REQUIRED TO CALCULATE THE SCORE
        if isinstance(allTriples,list) and isinstance(uriListP,list) and isinstance(uriListO,list):
            uriListS = []
            for i in range(len(allTriples)):
                s = allTriples[i].get('s')
                uri = s.get('value')
                uriListS.append(uri)
            allUri = uriListO + uriListP + uriListS
        
        #CHECK IF EXISTING VOCABULARIES ARE RE-USED IN THE DATASET
        try:
            start_analysis = time.time()
            newVocab = []
            if isinstance(vocabularies,list):
                for i in range(len(vocabularies)):
                    vocab = vocabularies[i]
                    result = LOVAPI.findVocabulary(vocab)
                    if result == False:
                        newVocab.append(vocab)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'New vocabularies check','Interoperability',analysis_date)
        except Exception as error:
            logger.warning(f'Representational-consistency | re-use of existing terms | {str(error)}',extra=kg_info)
            newVocab = '-'
        
        #CHECK USE OF DEPRECATED CLASSES AND PROPERTIES
        start_analysis = time.time()
        try:
            deprecated = query.getDeprecated(accessUrl)
        except Exception as error:
            logger.warning(f'Consistency| Use of members of deprecated classes or properties| {str(error)}',extra=kg_info)
            deprecated = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Deprecated classes/propertiers check', 'Consistency',analysis_date)

        #CHECK FOR FUNCTIONAL PROPERTIES WITH INCONSISTENT VALUE
        try:
            start_analysis = time.time()
            violationFP = []
            triplesFP = query.getFP(accessUrl)
            for triple in triplesFP:
                s = triple.get('s')
                subject1 = s.get('value')
                o = triple.get('o')
                obj1 = o.get('value')
                for triple2 in triplesFP:
                    s = triple2.get('s')
                    subject2 = s.get('value')
                    o = triple2.get('o')
                    obj2 = o.get('value')
                    if subject1 == subject2 and obj1 != obj2:
                        violationFP.append(triple)
            FPvalue = 1.0 - (len(violationFP)/triplesQuery)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Functional Property','Accuracy',analysis_date)
        except Exception as error:
            logger.warning(f'Accuracy | Functional property violation | {str(error)}',extra=kg_info)
            FPvalue = '-'
        
        #CHECK FOR INVALID USAGE OF INVERSE-FUNCTIONAL PROPERTIES
        try:
            start_analysis = time.time()
            violationIFP = []
            triplesIFP = query.getIFP(accessUrl)
            for triple in triplesIFP:
                s = triple.get('s')
                subject1 = s.get('value')
                o = triple.get('o')
                obj1 = o.get('value')
                for triple2 in triplesIFP:
                    s = triple2.get('s')
                    subject2 = s.get('value')
                    o = triple2.get('o')
                    obj2 = o.get('value')
                    if obj1 == obj2 and subject1 != subject2:
                        violationIFP.append(triple)
            IFPvalue = 1.0 - (len(violationIFP)/triplesQuery)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Inverse Functional Property', 'Accuracy',analysis_date)
        except Exception as error:
            logger.warning(f'Accuracy | Inverse functional property violation | {str(error)}',extra=kg_info)
            IFPvalue = '-'
        
        #CHECK IF THERE ARE EMPTY ANNOTATION AS LABEL/COMMENT
        labels = []
        try:
            start_analysis = time.time()
            labels = query.getLabel(accessUrl)
            emptyAnnotation = 0
            for i in range(len(labels)):
                obj = labels[i]
                if utils.validateURI(obj) == False:
                    if obj == '':
                        emptyAnnotation = emptyAnnotation + 1
            emptyAnnotation = 1.0 - (emptyAnnotation/len(labels))
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Empty annotation labels', 'Accuracy',analysis_date)
        except Exception as error:
            logger.warning(f'Accuracy | Empty annotation labels | {str(error)}',extra=kg_info)
            emptyAnnotation = '-'
        
        #CHECK IF TRIPLES HAVE A WHITE SPACE ANNOTATION PROBLEM
        try:
            start_analysis = time.time()
            wSP = []
            for i in range(len(labels)):
                obj = labels[i]
                if utils.validateURI(obj) == False:
                    if obj != obj.strip():
                        wSP.append(obj)
            numWSP = 1.0 - (len(wSP)/len(labels))
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check White space in annotation', 'Accuracy',analysis_date)
        except Exception as error:
            logger.warning(f'Accuracy | White space in annotation | {str(error)}',extra=kg_info)
            numWSP = '-'

        #CHECK IF TRIPLES HAVE A MALFORMED DATA TYPE LITERALS PROBLEM
        try:
            start_analysis = time.time()
            malformedTriples = []
            if isinstance(allTriples,list):
                for i in range(len(allTriples)):
                    obj = allTriples[i].get('o')
                    value = obj.get('value')
                    if utils.validateURI(value) == False:
                        dataType = obj.get('datatype')
                        if isinstance(dataType,str):
                            regex = utils.getRegex(dataType)
                            if regex is not None:
                                result = utils.checkString(regex,value)
                                if result == False:
                                    malformedTriples.append(obj)
                numMalformedTriples = 1.0 - (len(malformedTriples)/len(allTriples))
                end_analysis = time.time()
                utils.write_time(nameKG,end_analysis-start_analysis,'Check Datatype consistency', 'Accuracy',analysis_date)
            else:
                logger.warning(f'Accuracy | Datatype consistency| Error executing query on SPARQL endpoint ',extra=kg_info)
                numMalformedTriples = '-'
        except Exception as error:
            logger.warning(f'Accuracy | Datatype consistency| {str(error)}',extra=kg_info)
            numMalformedTriples = '-'

        #CHECK FOR ENTITIES MEMBER OF A DISJOINT CLASS
        start_analysis = time.time()
        try:
            numDisjoint = query.getDisjoint(accessUrl)
        except Exception as error:
            logger.warning(f'Consistency | Entities as members of disjoint classes | {str(error)}',extra=kg_info)
            numDisjoint = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Disjoint class check','Consistency',analysis_date)
        
        #CHECK FOR TRIPLES WITH MISPLACED PROPERTY PROBLEM
        classes = []
        try:
            start_analysis = time.time()
            misplacedProperty = []
            classes = query.getAllClasses(accessUrl)
            if isinstance(classes,list):
                for predicate in query.getAllPredicate(accessUrl):
                    result = utils.validateURI(predicate)
                    if result == True:
                        classes.sort()
                        r = utils.binarySearch(classes,0,len(classes)-1,predicate)
                        if r != -1:
                            misplacedProperty.append(predicate)
                        #for j in range(len(classes)):
                            #if p == classes[j]:
                                #misplacedProperty.append(p)
            else:
                misplacedProperty = 'insufficient data'
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Misplaced properties','Consistency',analysis_date)
        except Exception as error:
            logger.warning(f'Consistency | Misplaced properties | {str(error)}',extra=kg_info)
            misplacedProperty = '-'

        #CHECK FOR TRIPLES WITH MISPLACED CLASS PROBLEM
        properties = []
        try:
            start_analysis = time.time()
            misplacedClass = []
            properties = query.getAllProperty(accessUrl)
            found = False
            if isinstance(allTriples,list) and isinstance(properties,list):
                properties.sort()
                for i in range(len(allTriples)):
                    o = allTriples[i].get('o')
                    valueO = o.get('value')
                    s = allTriples[i].get('s')
                    valueS = s.get('value')
                    result = utils.validateURI(valueS)
                    if result == True:
                        r = utils.binarySearch(properties,0,len(properties)-1,valueS)
                        if r != -1:
                            found = True
                    resultO = utils.validateURI(valueO)
                    if found == False and resultO == True:
                        r2 = utils.binarySearch(properties,0,len(properties)-1,valueO)
                        if r2 != -1:
                            found = True
                    if found == True:
                        misplacedClass.append(valueS)
                        found = False
            else:
                logger.warning(f'Consistency | Misplaced classes | Impossible to recover all information to calculate this metric',extra=kg_info)
                misplacedClass = '-'
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Misplaced classes', 'Consistency',analysis_date)
        except TimeoutError as error:
            logger.warning(f'Consistency | Misplaced classes | {str(error)}',extra=kg_info)
            misplacedClass = '-'
        except Exception as error:
            logger.warning(f'Consistency | Misplaced classes | {str(error)}',extra=kg_info)
            misplacedClass = '-'
        
        #CHECK THE TRIPLES WITH ONTOLOGY HIJACKING PROBLEM
        allType = []
        try:
            start_analysis = time.time()
            allType = query.getAllType(accessUrl)
            triplesOH = False
            if isinstance(allType,list):
                triplesOH = LOVAPI.searchTermsList(allType)
                if len(triplesOH) > 0:
                    hijacking = True
                else:
                    hijacking = False
            else:
                logger.warning(f'Consistency | Ontology hijacking | Impossible to retrieve the terms defined in the dataset',extra=kg_info)
                hijacking = '-'
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Ontology hijacking', 'Consistency',analysis_date)
        except Exception as error:
            logger.warning(f'Consistency | Ontology hijacking | {str(error)}',extra=kg_info)
            hijacking = '-'
        
        #CHECK USE OF UNDEFINED CLASS
        try:
            start_analysis = time.time()
            toSearch = []
            found = False
            for i in range(len(allTriples)):
                s = allTriples[i].get('s')
                s = s.get('value')
                allType.sort()
                r = utils.binarySearch(allType,0,len(allType)-1,s)
                if r != -1:
                    found = True
                    break
                #for j in range(len(rdfTS)):
                    #sType = rdfTS[j]
                    #if s == sType:
                        #found = True
                        #break
                if found == False:
                    result = utils.validateURI(s)
                    if result == True:
                        toSearch.append(s)
                found = False
            undClasses = LOVAPI.searchTermsList(toSearch)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Invalid usage of undefined classes', 'Consistency',analysis_date)
        except Exception as error:
            logger.warning(f'Consistency | Invalid usage of undefined classes and properties | {str(error)}',extra=kg_info)
            undClasses = '-'
        
        #CHECK USE OF UNDEFINED PROPERTY
        try:
            start_analysis = time.time()
            toSearch = []
            found = False
            for predicate in query.getAllPredicate(accessUrl):
                properties.sort()
                r = utils.binarySearch(properties,0,len(properties)-1,predicate)
                if r != -1:
                    found = True
                    break
                #for j in range(len(listP)):
                    #p2 = listP[j]
                    #if p == p2:
                        #found = True
                        #break
                if found == False:
                    result = utils.validateURI(predicate)
                    if result == True:
                        toSearch.append(predicate)
                found = False
            undProperties = LOVAPI.searchTermsList(toSearch)
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Invalid usage of undefined properties','Consistency',analysis_date)
        except Exception as error:
            logger.warning(f'Consistency | Invalid usage of undefined classes and properties | {str(error)}',extra=kg_info)
            undProperties = '-'

        #CALCULATION OF THE EXTENSIONAL CONCISENESS
        try:
            start_analysis = time.time()
            tripleList = []
            duplicate = []
            if isinstance(allTriples,list):
                if len(allTriples)> 0:    
                    for i in range(len(allTriples)):
                        s = allTriples[i].get('s')
                        p = allTriples[i].get('p')
                        o = allTriples[i].get('o')
                        subject = s.get('value')
                        predicate = p.get('value')
                        object = o.get('value')
                        triple = subject + predicate + object
                        tripleList.append(triple)
                    bloomF = BloomFilter(len(tripleList),0.05)
                    logger.info(f'Bloom filter parameter: \n -Size of bit array: {str(bloomF.size)}\n -False positive Probability:{str(bloomF.fp_prob)}\n -Number of hash functions:{str(bloomF.hash_count)}',extra=kg_info)
                    for i in range(len(tripleList)):
                        found = bloomF.check(tripleList[i])
                        if found == False:
                            bloomF.add(tripleList[i])
                        elif found == True:
                            duplicate.append(tripleList[i])

                    if len(allTriples) > 0:
                        exC = 1.0 - (len(duplicate)/len(allTriples)) # From: Evaluating the Quality of the LOD Cloud: An Empirical Investigation (Ruben Verborgh)
                        exC = str(exC)
                        exC = exC + f" (out of {len(allTriples)} triples considered)"
                    else:
                        logger.warning(f'Conciseness | Extensional conciseness | Insufficient data to compute the metric',extra=kg_info)
                        exC = '-'
                else:
                    logger.warning(f'Consistency | Invalid usage of undefined classes and properties | No triples retrieved from the endpoint',extra=kg_info)
                    exC = '-'
            else:
                logger.warning(f'Conciseness | Extensional conciseness | Insufficient data to compute the metric',extra=kg_info)
                exC = '-'
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Extensional conciseness', 'Conciseness',analysis_date)
        except Exception as error:
            logger.warning(f'Conciseness | Extensional conciseness | {str(error)}',extra=kg_info)
            exC = '-'
        
        #CALCULATION OF INTENSIONAL CONCISENESS
        try:
            start_analysis = time.time()
            triplePropList = []
            duplicateP = []
            count = 0
            for prop in query.getAllPropertySP(accessUrl):
                s = prop.get('s')
                p = prop.get('p')
                subP = s.get('value')
                predP = p.get('value')
                tripleProp = subP + predP
                triplePropList.append(tripleProp)
                count = count+1
            bloomF2 = BloomFilter(len(triplePropList),0.05)
            for j in range(len(triplePropList)):
                found = bloomF2.check(triplePropList[j])
                if found == False:
                    bloomF2.add(triplePropList[j])
                elif found == True:
                    duplicateP.append(triplePropList[j])
            
            if count > 0:
                intC = 1.0 - (len(duplicateP)/count)
                intC = str(intC)
                intC = intC + f" (out of {count} triples considered)"
            else:
                logger.warning(f'Conciseness | Intensional conciseness | Insufficient data to compute the metric',extra=kg_info)
                intC = '-'
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check Intensional conciseness', 'Conciseness',analysis_date)
        except Exception as error:
            logger.warning(f'Conciseness | Intensional conciseness | {str(error)}',extra=kg_info)
            intC = '-'
        
        #CHECK IF THERE IS A SIGNATURE ON THE KG
        try:
            start_analysis = time.time()
            sign = query.getSign(accessUrl)
            if isinstance(sign,int):
                if sign > 0:
                    signedKG = True
                else:
                    signedKG = False
            else:
                signedKG = False
        except Exception as error:
            logger.warning(f'Verifiability | Verifying usage of digital signatures | {str(error)}',extra=kg_info)
            signedKG = '-'
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Sign check', 'Security',analysis_date)

        #CHECK THE URIs DEFERENTIABILITY (TEST MADE ON 5000 TRIPLES SELECTED RANDOMLY)
        try:
            start_analysis = time.time()
            defCount = 0
            uriCount = 0
            uris = query.getUris(accessUrl) #QUERY THAT GET 5000 RANDOM URI FROM THE ENDPOINT 
            for uri in uris:
                if utils.validateURI(uri) == True:
                    uriCount = uriCount + 1
                    try:
                        response = requests.get(uri,headers={"Accept":"application/rdf+xml"},stream=True,timeout=2)
                        if response.status_code == 200:
                            defCount = defCount +1
                    except:
                        continue
            if uriCount > 0:        
                defValue = defCount / uriCount
            else:
                logger.warning(f'Availability | Derefereaceability of the URI | No URIs retrieved from the endpoint',extra=kg_info)
                defValue = '-'
            end_analysis = time.time()
            utils.write_time(nameKG,end_analysis-start_analysis,'Check URIs Dereferenciability', 'Availability',analysis_date)
        except: #IF QUERY FAILS (BECUASE SPARQL 1.1 IS NOT SUPPORTED) TRY TO CHECK THE DEFERETIABILITY BY FILTERING THE TRIPLES RECOVERED FOR OTHER CALCULATION (IF THEY ARE BEEN RECOVERED)
            try:
                start_analysis = time.time()
                uriCount = 0
                defCount = 0
                for i in range(10):
                    s = allTriples[i].get('s')
                    value = s.get('value')
                    if utils.validateURI(value):
                        uriCount = uriCount + 1
                        try:
                            response = requests.get(value,headers={"Accept":"application/rdf+xml"},stream=True,timeout=2)
                            if response.status_code == 200:
                                defCount = defCount +1
                        except:
                            continue
                if uriCount > 0:
                    defValue = defCount / uriCount
                else:
                    logger.warning(f'Availability | Derefereaceability of the URI | No URIs retrieved from the endpoint',extra=kg_info)
                    defValue = '-'
                end_analysis = time.time()
                utils.write_time(nameKG,end_analysis-start_analysis,'Check URIs Dereferenciability','Availability',analysis_date)
            except Exception as error:
                logger.warning(f'Availability | Derefereaceability of the URI | {str(error)}',extra=kg_info)
                defValue = '-'
                
    #IF SPARQL ENDPOINT ISN'T AVAILABLE WE SKIP ALL TEST WITH THE SPARQL QUERY
    else:
        if restricted == True:
            errorMessage = '-'
            logger.warning(f'Availability | Accessibility of the SPARQL endpoint | Restricted access to the endpoint, only metrics that can ben calculated with the metadata will be computed',extra=kg_info)
            accessUrl = ''
        elif isHTML == True:
            errorMessage = 'Warning the result of endpoint is HTML'
            logger.warning(f"Availability | Accessibility of the SPARQL endpoint | The result format from the SPARQL endpoint aren't structured data, only metrics that can ben calculated with the metadata will be computed",extra=kg_info)
        elif absent == True:
            errorMessage = '-'
            logger.warning(f"Availability | Accessibility of the SPARQL endpoint | No SPARQL endpoint indicated, only metrics that can ben calculated with the metadata will be computed",extra=kg_info)
        else:
            logger.warning(f"Availability | Accessibility of the SPARQL endpoint | SPARQL endpoint offline, only metrics that can ben calculated with the metadata will be computed",extra=kg_info)
            errorMessage = '-'

    #GET THE LICENSE 
    license = Aggregator.getLicense(metadata)

    #GET THE AUTHOR OF THE DATASET
    author = Aggregator.getAuthor(metadata)
    
    #CHECK FOR INACTIVE LINKS
    inactiveLink = False
    for i in range(len(otResources)):
        if otResources[i].status == 'offline':
            inactiveLink = True
    
    #CHECK FOR THE EXAMPLE
    example = False
    for j in range(len(otResources)):
        if isinstance(otResources[j].format,str):
            if 'example' in otResources[j].format:
                example = True
        if isinstance(otResources[j].title,str):
            if 'example' in otResources[j].title:
                example = True

    #GET EXTERNAL LINKS OF THE DATASET
    start_analysis = time.time()
    externalLinks = Aggregator.getExternalLinks(idKG)
    exLinksObj = utils.toObjectExternalLinks(externalLinks)
    triplesL = 0
    for i in range(len(exLinksObj)):
        link = exLinksObj[i]
        value = link.value
        value = str(link.value)
        value = re.sub("[^\d\.]", "",value)
        try:
            value = int(value)
            triplesL = triplesL + value
        except:
            continue
    end_analysis = time.time()
    utils.write_time(nameKG,end_analysis-start_analysis,'Calculation of interlinking completeness', 'Completeness',analysis_date)
    
    if sparql_endpoint is None:
        #READIUNG THE GRAPH OF KG 
        here = os.path.dirname(os.path.abspath(__file__))
        gFile = os.path.join(here,'GraphOfKG.gpickle')
        graph = nx.read_gpickle(gFile)

        #PAGERANK CALCULATION
        start_analysis = time.time()
        pageRank = Graph.getPageRank(graph,idKG)
        pageRank = str(pageRank)
        pageRank = pageRank.replace('.',',')
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Calculation of the PageRank', 'Reputation',analysis_date)

        #CALCULATION OF THE DEGREE OF CONNECTION
        start_analysis = time.time()
        degree = Graph.getDegreeOfConnection(graph,idKG)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Calculation of Degree of Connection', 'Interlinking',analysis_date)
        
        #CALCULATION OF THE CENTRALITY
        start_analysis = time.time()
        centrality = Graph.getCentrality(graph,idKG)
        if isinstance(centrality,float):
            centrality = "%.3f"%centrality
            centrality = str(centrality)
            centrality = centrality.replace('.',',')
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Calculation of Centrality', 'Interlinking',analysis_date)

        #CALCULATION OF CLUSTERING COEFFICIENT
        start_analysis = time.time()
        clusteringCoefficient = Graph.getClusteringCoefficient(graph,idKG)
        if isinstance(clusteringCoefficient,float):
            clusteringCoefficient = "%.3f"%clusteringCoefficient
            clusteringCoefficient = str(clusteringCoefficient)
            clusteringCoefficient = clusteringCoefficient.replace('.',',')
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Calculation of Clustering coefficient', 'Interlinking',analysis_date)
    else:
        pageRank = '-'
        degree = '-'
        centrality = '-'
        clusteringCoefficient = '-'


    #GET THE DESCRIPTION OF THE CONTENT OF KG
    description = Aggregator.getDescription(metadata)    
    if available != True:  #IF ENDPOINT ISN'T AVAILABLE, WE TRY TO OBTAIN SOME INFO FROM THE VoID FILE IF IS INDICATED IN THE METADATA AND IS ONLINE
        if void == True:
            try:
                voidFile = VoIDAnalyses.parseVoID(urlV)
                if void is not None:
                    void = True
                    vocabularies = VoIDAnalyses.getVocabularies(voidFile)
                    creationDate = VoIDAnalyses.getCreationDate(voidFile)
                    modificationDate = VoIDAnalyses.getModificationDate(voidFile)
                    availableDump = VoIDAnalyses.getDataDump(voidFile)
                    licenseMr = VoIDAnalyses.getLicense(voidFile)
                    authorQ = VoIDAnalyses.getCreators(voidFile)
                    publisher = VoIDAnalyses.getPublishers(voidFile)
                    numEntities = VoIDAnalyses.getNumEntities(voidFile)
                    frequency = VoIDAnalyses.getFrequency(voidFile)
                    contributors = VoIDAnalyses.getContributors(voidFile)
                    regex = VoIDAnalyses.getUriRegex(voidFile)
                    formats = VoIDAnalyses.getSerializationFormats(voidFile)
                    languages = VoIDAnalyses.getLanguage(voidFile)
                else:
                    void = False
            except:
                try:
                    voidFile = VoIDAnalyses.parseVoIDTtl(urlV)
                    if void is not None:
                        void = True
                        vocabularies = VoIDAnalyses.getVocabularies(voidFile)
                        creationDate = VoIDAnalyses.getCreationDate(voidFile)
                        modificationDate = VoIDAnalyses.getModificationDate(voidFile)
                        availableDump = VoIDAnalyses.getDataDump(voidFile)
                        licenseMr = VoIDAnalyses.getLicense(voidFile)
                        authorQ = VoIDAnalyses.getCreators(voidFile)
                        publisher = VoIDAnalyses.getPublishers(voidFile)
                        numEntities = VoIDAnalyses.getNumEntities(voidFile)
                        frequency = VoIDAnalyses.getFrequency(voidFile)
                        contributors = VoIDAnalyses.getContributors(voidFile)
                        regex = VoIDAnalyses.getUriRegex(voidFile)
                        formats = VoIDAnalyses.getSerializationFormats(voidFile)
                        languages = VoIDAnalyses.getLanguage(voidFile)
                    else:
                        void = False
                except:
                    void = False
        else:
            void = False           
    else:
        void = False
    
    #CHECK IF EXISTING VOCABULARIES ARE RE-USED IN THE DATASET
    try:
        start_analysis = time.time()
        newVocab = []
        if isinstance(vocabularies,list):
            for i in range(len(vocabularies)):
                vocab = vocabularies[i]
                result = LOVAPI.findVocabulary(vocab)
                if result == False:
                    newVocab.append(vocab)
        end_analysis = time.time()
        utils.write_time(nameKG,end_analysis-start_analysis,'Check the re-using of existing vocabs', 'Interoperability',analysis_date)
    except Exception as error:
        logger.warning(f"Representational-consistency | Re-use of existing terms | Impossible to recover the vocabularies in the KG",extra=kg_info)
        newVocab = '-'

    #GET THE LANGUAGE OF THE KG FROM THE METADATA
    try:
        languageM = Aggregator.getExtrasLanguage(idKG)
    except Exception as error:
        logger.warning(f"Versatility | Usage of multiple languages | {str(error)}",extra=kg_info)
        languageM = '-'

    #CHECK IF THE KG IS IN A LIST OF RELIABLE PROVIDERS
    try:
        providers = ['wikipedia','government','bioportal','bio2RDF','academic']
        keywords = Aggregator.getKeywords(idKG)
        if any(x in keywords for x in providers):
            believable = True
        else:
            believable = False
    except Exception as error:
        logger.warning(f"Believability | Trust value | {str(error)}",extra=kg_info)
        believable = '-' 

    if sources == False:
        sourcesC = Sources('absent','absent','absent')
    else:
        sourcesC = Sources(sources.get('web','Absent'),sources.get('name','Absent'),sources.get('email','Absent'))

    start_analysis = time.time()
    valueN = 0
    valueD = 0
    valueUrl = 0
    valuePr = 0
    if isinstance(nameKG,str):
        if nameKG != '' and nameKG != 'Absent' and nameKG != 'absent':
            valueN = 1
    if isinstance(description,str):
        if description != '' and description != False and description != 'Absent':
            valueD = 1
    if isinstance(sourcesC.web,str):
        if sourcesC.web != '' and sourcesC.web !='Absent' and sourcesC.web != 'absent':
            valueUrl = 1

    if believable == True:
        valuePr = 1
    
    if valueN == 0 and valueD == 0 and valueUrl == 0 and valuePr == 0:
        trustValue = -1

    trustValue = (valueN+valueD+valueUrl+valuePr)/4
    trustValue = str(trustValue)
    trustValue = trustValue.replace('.',',')
    
    if idKG == False:
        idKG = ''
    if accessUrl == False:
        accessUrl = ''
    if nameKG == False:
        nameKG = ''
    
    end_analysis = time.time()
    utils.write_time(nameKG,end_analysis-start_analysis,'Calculation of trust value', 'Believability',analysis_date)

    #CHECK IF THE DUMP IS ALSO IN A STANDARD MEDIA-TYPE FOR A KG
    if availableDownload == 1 or availableDump == True:
        common_formats_availability = utils.check_common_acceppted_format(metadata_media_type)
    else:
        common_formats_availability = 'No dump available'
    
    if available == True:
        availability = Availability(endpoint,availableDownload,availableDump,inactiveLink,defValue)
        performance = Performance(minL,maxL,av,standardDeviation,percentile25L,percentile75L,medianL,minThroughput,maxThroughput,averageThroughput,standardDeviationT,percentile25T,percentile75T,medianT)
        amount = QualityDimensions.AmountOfData.AmountOfData(triplesM,triplesQuery,numEntities,numProperty,entitiesRe)
        volatility = Volatility(frequency)
        licensing = Licensing(license,licenseMr,licenseHr)
        verifiability = Verifiability(vocabularies,authorQ,author,contributors,publisher,sourcesC,signedKG)
        versatility = Versatility(languages,languageM,formats,endpoint,availableDump,availableDownload)
        security = Security(isSecure,restricted)
        rConciseness = RepresentationalConciseness(avLenghts,standardDeviationL,minLenghtS,percentile25LenghtS,medianLenghtS,percentile75LenghtS,maxLenghtS,avLenghtsO,standardDeviationLO,minLenghtO,percentile25LenghtO,medianLenghtO,percentile75LenghtO,maxLenghtO,avLenghtsP,standardDeviationLP,minLenghtP,percentile25LenghtP,medianLenghtP,percentile75LenghtP,maxLenghtP,RDFStructures)
        rConsistency = RepresentationalConsistency(newVocab,newTermsD)
        interpretability = Interpretability(numBlankNode,RDFStructures)
        interlinking = Interlinking(degree,clusteringCoefficient,centrality,numberSameAs,exLinksObj,numberSkosMapping)
        conciseness = Conciseness(exC,intC)
        accuracy = Accuracy(emptyAnnotation,numWSP,numMalformedTriples,FPvalue,IFPvalue)
        if isinstance(numDisjoint,int):
            try:
                numEntities = int(numEntities)
                if numEntities > 0 and numEntities > numDisjoint:
                    disjointValue = numDisjoint/numEntities
                else:
                    logger.warning(f"Consistency | Entities as members of disjoint classes | Insufficent data to compute the metric",extra=kg_info)
                    disjointValue = '-'
            except Exception as error:
                logger.warning(f"Consistency | Entities as members of disjoint classes | {str(error)}",extra=kg_info)
                disjointValue = '-'
            
            if isinstance(disjointValue,str):
                try:
                    entitiesRe = int(entitiesRe)
                    if entitiesRe > 0 and entitiesRe > numDisjoint:
                        disjointValue = numDisjoint/entitiesRe
                    else:
                        logger.warning(f"Consistency | Entities as members of disjoint classes | Insufficent data to compute the metric",extra=kg_info)
                        disjointValue = '-'
                except Exception as error:
                    logger.warning(f"Consistency | Entities as members of disjoint classes | {str(error)}",extra=kg_info)
                    disjointValue = '-'

            if isinstance(classes,list) and isinstance(properties,list):
                if len(classes) + len(properties) > 0 :
                    deprecatedV = 1.0 - (len(deprecated)/(len(classes) + len(properties)))
                else:
                    logger.warning(f"Consistecy | Use of members of deprecated classes or properties | Insufficient data",extra=kg_info)
                    deprecatedV = '-'
            else:
                logger.warning(f"Consistecy | Use of members of deprecated classes or properties | Insufficient data",extra=kg_info)
                deprecatedV = '-'
            
            if isinstance(triplesQuery,int):
                if triplesQuery > 0:
                    if isinstance(undClasses,list):
                        undefCV = 1.0 - (len(undClasses)/triplesQuery)
                    else:
                        undefCV = 'Unable to retrieve classes from the endpoint'
                    if isinstance(undProperties,list):
                        undefPV = 1.0 - (len(undProperties)/triplesQuery)
                    else:
                        undefPV = 'Unable to retrieve properties from the endpoint'
                    if isinstance(misplacedClass,list):
                        mispCV = 1.0 - (len(misplacedClass)/triplesQuery)
                    else:
                        mispCV = 'Unable to retrieve properties from the endpoint'
                    if isinstance(misplacedProperty,list):
                        mispPV = 1.0 - (len(misplacedProperty)/triplesQuery)
                    else:
                        mispPV = 'Unable to retrieve properties from the endpoint'
                    consistency = Consistency(deprecatedV,disjointValue,mispPV,mispCV,hijacking,undefCV,undefPV)
                else:
                    consistency = Consistency(deprecatedV,disjointValue,'insufficient data','insufficient data',hijacking,'insufficient data','insufficient data')
            else:
                consistency = Consistency(deprecatedV,disjointValue,'insufficient data','insufficient data',hijacking,'insufficient data','insufficient data')
        else:
            if isinstance(classes,list) and isinstance(properties,list):
                if len(classes) + len(properties) > 0 :
                    if isinstance(deprecated,list):
                        deprecatedV = 1.0 - (len(deprecated)/(len(classes) + len(properties)))
                    else:
                        deprecatedV = 'insufficient data'
                else:
                    deprecatedV = 'insufficient data'
            else:
                    deprecatedV = 'insufficient data'

            if isinstance(triplesQuery,int):
                if triplesQuery > 0:
                    if isinstance(undClasses,list):
                        undefCV = 1.0 - (len(undClasses)/triplesQuery)
                    else:
                        undefCV = '-'
                        logger.warning(f"Consistecy | Invalid usage of undefined classes and properties | Unable to retrieve classes from the endpoint",extra=kg_info)
                    if isinstance(undProperties,list):
                        undefPV = 1.0 - (len(undProperties)/triplesQuery)
                    else:
                        undefPV = '-'
                        logger.warning(f"Consistecy | Invalid usage of undefined classes and properties | Unable to retrieve properties from the endpoint",extra=kg_info)
                    if isinstance(misplacedClass,list):
                        mispCV = 1.0 - (len(misplacedClass)/triplesQuery)
                    else:
                        logger.warning(f"Consistecy | Misplaced classes or properties | Unable to retrieve classes from the endpoint",extra=kg_info)
                        mispCV = '-'
                    if isinstance(misplacedProperty,list):
                        mispPV = 1.0 - (len(misplacedProperty)/triplesQuery)
                    else:
                        logger.warning(f"Consistecy | Misplaced classes or properties | Unable to retrieve properties from the endpoint",extra=kg_info)
                        mispPV = '-'
                    consistency = Consistency(deprecatedV,'insufficient data',mispPV,mispCV,hijacking,undefCV,undefPV)
                else:
                    consistency = Consistency(deprecatedV,'insufficient data','insufficient data','insufficient data',hijacking,'insufficient data','insufficient data')
            else:
                consistency = Consistency(deprecatedV,'insufficient data','insufficient data','insufficient data',hijacking,'insufficient data','insufficient data')
        
        if isinstance(triplesQuery,int) and isinstance(numTriplesUpdated,int):
            percentageUp = (numTriplesUpdated/triplesQuery) * 100
            percentageUp = str(percentageUp)
            percentageUp = percentageUp +"%"
        elif isinstance(triplesM,int) and isinstance(numTriplesUpdated,int):
            if triplesM > 0:
                percentageUp = (numTriplesUpdated/triplesM) * 100
                percentageUp = str(percentageUp)
                percentageUp = percentageUp +"%"
            else:
                logger.warning(f"Currency | Update history | Insufficient data to compute this metric",extra=kg_info)
                percentageUp = '-'
        else:
            logger.warning(f"Currency | Update history | Insufficient data to compute this metric",extra=kg_info)
            percentageUp = '-'
        if isinstance(triplesQuery,int) and isinstance(triplesL,int) and triplesQuery > 0 and triplesQuery >= triplesL:
            iCompleteness = (triplesL/triplesQuery)
            iCompleteness = "%.2f"%iCompleteness
            completeness = Completeness(triplesQuery,triplesL,iCompleteness)
        else:
            completeness = Completeness(triplesQuery,triplesL,"insufficient data")
        if isinstance(numLabel,int) and isinstance(triplesQuery,int) and triplesQuery > 0: 
            percentageLabel = (numLabel/triplesQuery) * 100
            percentageLabel = "%.2f"%percentageLabel
            percentageLabel = str(percentageLabel)
            percentageLabel = percentageLabel + "%"
            understendability = Understendability(numLabel,percentageLabel,regex,vocabularies,example,nameKG,description,sourcesC.web)
        elif isinstance(numLabel,int) and isinstance(triplesM,int) and triplesM > 0:
            percentageLabel = (numLabel/triplesM) * 100
            percentageLabel = "%.2f"%percentageLabel
            percentageLabel = str(percentageLabel)
            percentageLabel = percentageLabel + "%"
            understendability = Understendability(numLabel,percentageLabel,regex,vocabularies,example,nameKG,description,sourcesC.web) 
        else:
            understendability = Understendability(numLabel,'insufficient data',regex,vocabularies,example,nameKG,description,sourcesC.web)
        if isinstance(creationDate,str) and isinstance(modificationDate,str):
            try:
                creationDate = datetime.datetime.strptime(creationDate, "%Y-%m-%d").date()
                today = datetime.date.today()
                ageOfData = (today - creationDate).days
                todayFormatted = today.strftime("%Y-%m-%d")
                todayDate =  datetime.datetime.strptime(todayFormatted, "%Y-%m-%d").date()
                modificationDate = datetime.datetime.strptime(modificationDate, "%Y-%m-%d").date()
                delta = (todayDate - modificationDate).days
                currency = Currency(ageOfData,modificationDate,percentageUp,delta,historicalUp)
            except:
                logger.warning(f"Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | Insufficient data to compute this metric",extra=kg_info)
                currency = Currency(creationDate,modificationDate,percentageUp,'-',historicalUp)
        else:
            logger.warning(f"Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | Insufficient data to compute this metric",extra=kg_info)
            currency = Currency(creationDate,modificationDate,percentageUp,'-',historicalUp)
    elif void == True:
        availability = Availability(endpoint,availableDownload,availableDump,inactiveLink,errorMessage)
        performance = Performance(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        amount = QualityDimensions.AmountOfData.AmountOfData(triplesM,errorMessage,numEntities,errorMessage,errorMessage)
        volatility = Volatility(frequency)
        licensing = Licensing(license,licenseMr,errorMessage)
        verifiability = Verifiability(vocabularies,authorQ,author,contributors,publisher,sourcesC,errorMessage)
        versatility = Versatility(errorMessage,languageM,formats,errorMessage,availableDump,availableDownload)
        security = Security(errorMessage,errorMessage)
        rConciseness = RepresentationalConciseness(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        rConsistency = RepresentationalConsistency(newVocab,errorMessage)
        understendability = Understendability(errorMessage,'-',regex,errorMessage,example,nameKG,description,sourcesC.web)
        interpretability = Interpretability(errorMessage,errorMessage)
        interlinking = Interlinking(degree,clusteringCoefficient,centrality,errorMessage,exLinksObj,errorMessage)
        if isinstance(creationDate,str) and isinstance(modificationDate,str):
            try:
                creationDate = datetime.datetime.strptime(creationDate, "%Y-%m-%d").date()
                today = datetime.date.today()
                ageOfData = (today - creationDate).days
                todayFormatted = today.strftime("%Y-%m-%d")
                todayDate =  datetime.datetime.strptime(todayFormatted, "%Y-%m-%d").date()
                modificationDate = datetime.datetime.strptime(modificationDate, "%Y-%m-%d").date()
                delta = (todayDate - modificationDate).days
                currency = Currency(ageOfData,modificationDate,'insufficient data',delta,'insufficient data')
            except Exception as error:
                logger.warning(f"Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | {str(error)}",extra=kg_info)
                currency = Currency(creationDate,modificationDate,'-','-','-')
        else:
            logger.warning(f"Currency | Use of dates as the point in time of the last verification of a statement represented by dcterms:modified | No triples with dcterms:modified predicate",extra=kg_info)
            currency = Currency(creationDate,modificationDate,'-','-','-')
        consistency = Consistency(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        conciseness = Conciseness(errorMessage,errorMessage)
        accuracy = Accuracy(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        if isinstance(triplesM,int) and isinstance(triplesL,int) and triplesM > 0 and triplesM >= triplesL:
            iCompleteness = (triplesL/triplesM)
            iCompleteness = "%.2f"%iCompleteness
            completeness = Completeness(triplesM,triplesL,iCompleteness)
        else:
            completeness = Completeness(triplesM,triplesL,0)
    else:
        availability = Availability(endpoint,availableDownload,errorMessage,inactiveLink,errorMessage)
        performance = Performance(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        amount = QualityDimensions.AmountOfData.AmountOfData(triplesM,errorMessage,errorMessage,errorMessage,errorMessage)
        volatility = Volatility(errorMessage)
        licensing = Licensing(license,errorMessage,errorMessage)
        verifiability = Verifiability(errorMessage,errorMessage,author,errorMessage,errorMessage,sourcesC,errorMessage)
        versatility = Versatility(errorMessage,languageM,errorMessage,errorMessage,errorMessage,availableDownload)
        security = Security(errorMessage,errorMessage)
        rConciseness = RepresentationalConciseness(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        rConsistency = RepresentationalConsistency(errorMessage,errorMessage)
        understendability = Understendability(errorMessage,'-',errorMessage,errorMessage,example,nameKG,description,sourcesC.web)
        interpretability = Interpretability(errorMessage,errorMessage)
        interlinking = Interlinking(degree,clusteringCoefficient,centrality,errorMessage,exLinksObj,errorMessage)
        currency = Currency(errorMessage,errorMessage,'-','-','-')
        consistency = Consistency(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        conciseness = Conciseness(errorMessage,errorMessage)
        accuracy = Accuracy(errorMessage,errorMessage,errorMessage,errorMessage,errorMessage)
        if isinstance(triplesM,int) and isinstance(triplesL,int) and triplesM > 0 and triplesM >= triplesL:
            iCompleteness = (triplesL/triplesM)
            iCompleteness = "%.2f"%iCompleteness
            completeness = Completeness(triplesM,triplesL,iCompleteness)
        else:
            completeness = Completeness(triplesM,triplesL,0)

    reputation = Reputation(exLinksObj,pageRank)
    believability = Believability(nameKG,description,sourcesC.web,believable,trustValue)
    
    downloadUrl = list(dict.fromkeys(downloadUrl))
    
    #PREPARING DATA FOR SCORE CALCULATION
    if available == True:
            downloadUrl = downloadUrl + dcat_links
            if isinstance(allTriples,list):
                uriListS = []
                for triple in allTriples:
                    if len(allTriples) > 0: #CREATING A LIST OF ALL SUBJECTS
                        s = triple.get('s')
                        value = s.get('value')
                        uriListS.append(value)
                if isinstance(numTriplesUpdated,int):
                    extra = Extra(idKG,accessUrl,downloadUrl,numTriplesUpdated,classes,properties,allUri,triplesO,uriListS,undProperties,undClasses,misplacedClass,misplacedProperty,deprecated,0,limited,offlineDump,urlV,voidStatus,minThroughputNoOff,averageThroughputNoOff,maxThroughputNoOff,standardDeviationTNoOff,0,None,metadata_media_type,common_formats_availability) #EXTRA OBJ CONTAINS ALL INFORMATION FOR SCORE CALCULATION AND OTHER USEFUL INFORMATION
                else:
                    logger.warning(f"Currency | Update history | Insufficient data to compute this metric",extra=kg_info)
                    extra = Extra(idKG,accessUrl,downloadUrl,'-',classes,properties,allUri,triplesO,uriListS,undProperties,undClasses,misplacedClass,misplacedProperty,deprecated,0,limited,offlineDump,urlV,voidStatus,minThroughputNoOff,averageThroughputNoOff,maxThroughputNoOff,standardDeviationTNoOff,0,None,metadata_media_type,common_formats_availability)
            else:
                uriListS = []
                logger.warning(f"Currency | Update history | Insufficient data to compute this metric",extra=kg_info)
                extra = Extra(idKG,accessUrl,downloadUrl,'-',classes,properties,allUri,triplesO,uriListS,undProperties,undClasses,misplacedClass,misplacedProperty,deprecated,0,limited,offlineDump,urlV,voidStatus,minThroughputNoOff,averageThroughputNoOff,maxThroughputNoOff,standardDeviationTNoOff,0,None,metadata_media_type,common_formats_availability)
    else:
        classes = []
        properties = []
        allUriCount = 0
        triplesO = []
        uriListS = []
        logger.warning(f"Currency | Update history | Insufficient data to compute this metric",extra=kg_info)
        extra = Extra(idKG,accessUrl,downloadUrl,'-',classes,properties,allUriCount,triplesO,0,errorMessage,errorMessage,errorMessage,errorMessage,errorMessage,0,errorMessage,offlineDump,urlV,voidStatus,errorMessage,errorMessage,errorMessage,errorMessage,0,None,metadata_media_type,common_formats_availability)

    KGQ = KnowledgeGraph(availability,currency,versatility,security,rConciseness,licensing,performance,amount,volatility,interlinking,consistency,reputation,believability,verifiability,completeness,rConsistency,understendability,interpretability,conciseness,accuracy,extra)

    return KGQ