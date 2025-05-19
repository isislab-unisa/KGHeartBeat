import base64
import csv
from datetime import date, datetime
from email import header, utils
from http.client import HTTPConnection
from pathlib import Path
from pydoc import pager
import re
from statistics import median
import string
import time
import pandas as pd
import utils
import requests
from ExternalLink import ExternalLink
from MetricsOutput import MetricsOutput
from QualityDimensions.AmountOfData import AmountOfData
from QualityDimensions.Availability import Availability
from QualityDimensions.Believability import Believability
from QualityDimensions.Completeness import Completeness
from QualityDimensions.Conciseness import Conciseness
from QualityDimensions.Consistency import Consistency
from QualityDimensions.Currency import Currency
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
import os.path
class OutputCSV(MetricsOutput):
    def __init__(self, kgQuality,idList):
        super().__init__(kgQuality,idList)

    def writeHeader(filename,include_dimensions = False):
        if include_dimensions == False:
            header = ['KG id','KG name','Sparql endpoint','SPARQL endpoint URL','Availability of RDF dump (metadata)','Availability of RDF dump (query)','URL for download the dataset','Inactive links','Age of data','Modification date','Percentage of data updated','Time elapsed since last modification','Historical updates','Languages (query)','Languages (metadata)','Serialization formats','Availability for download (query)','Availability for download (metadata)',
                    'Use HTTPS','Requires authentication','Average length of URIs (subject)','Standard deviation lenght URIs (subject)','Min length URIs (subject)','25th percentile length URIs (subject)','Median length URIs (subject)','75th percentile length URIs (subject)','Max length URIs (subject)','Average length of URIs (predicate)','Standard deviation lenght URIs (predicate)','Min length URIs (predicate)','25th percentile length URIs (predicate)','Median length URIs (predicate)','75th percentile length URIs (predicate)','Max length URIs (predicate)','Average length of URIs (object)','Standard deviation lenght URIs (object)','Min length URIs (object)','25th percentile length URIs (object)','Median length URIs (object)','75th percentile length URIs (object)','Max length URIs (object)','Use RDF structures','License machine redeable (metadata)','License machine redeable (query)','License human redeable','Minimum latency','25th percentile latency','Median latency','75th percentile latency','Maximum latency','Average latency','Standard deviation of latency','Minimum throughput','25th percentile throughput','Median throughput','75th percentile throughput','Maximum throughput','Average throughput',' Standard deviation of throughput',' Number of triples (metadata)','Number of triples (query)','Number of entities','Number of entities counted with regex','Number of property',
                    'Dataset update frequency','Degree of connection','Clustering coefficient','Centrality','Number of samAs chains','External links','PageRank','Description','Dataset URL','Is on a trusted provider list','Trust value','Vocabularies','Author (query)','Author (metadata)','Contributor','Publisher','Sources','Signed',' Number of triples','Number of triples linked','Interlinking completeness','New vocabularies defined in the dataset','New terms defined in the dataset','Number of labels/comments present on the data',' Percentage of triples with labels','Regex uri','Presence of example','Number of blank nodes','Uses RDF structures',
                    'Deprecated classes/properties used','Entities as member of disjoint class','Triples with misplaced property problem','Triples with misplaced class problem','Ontology Hijacking problem','Undefined class used without declaration','Undefined properties used without declaration','Extensional conciseness','Intensional conciseness','Triples with empty annotation problem','Triples with white space in annotation(at the beginning or at the end)','Triples with malformed data type literals problem','Functional properties with inconsistent values','Invalid usage of inverse-functional properties','Number of triples updated','Score','Normalized score','Limited','Offline dumps','Url file VoID','Availability VoID file','MinTPNoOff','MeanTPNoOff','MaxTPNoOff','sdTPNoOff','URIs Deferenceability',
                    'Availability score', 'Licensing score','Interlinking score','Performance score','Accuracy score','Consistency score','Conciseness score','Verifiability score','Reputation score','Believability score', 'Currency score','Volatility score','Completeness score','Amount of data score',
                    'Representational-Consistency score','Representational-Conciseness score','Understandability score','Interpretability score','Versatility score','Security score','SKOS mapping properties','U1-value','CS2-value','IN3-value','RC1-value','RC2-value','IN4-value','metadata-media-type','Availability of a common accepted Media Type','U5-value','PE2-value','PE3-value',
                    'F1-M Unique and persistent ID','F1-D URIs dereferenceability','F2a-M - Metadata availability via standard primary sources','F2b-M Metadata availability for all the attributes covered in the FAIR score computation', 'F3-M Data referrable via a DOI','F4-M Metadata registered in a searchable engine','F score','A1-D Working access point(s)','A1-M Metadata availability via working primary sources','A1.2 Authentication & HTTPS support','A2-M Registered in search engines','A score','R1.1 Machine- or human-readable license retrievable via any primary source','R1.2 Publisher information such as authors-contributors-publishers and sources','R1.3-D Data organized in a standardized way','R1.3-M Metadata are described with VoID/DCAT predicates','R score','I1-D Standard & open representation format','I1-M Metadata are described with VoID/DCAT predicates','I2 Use of FAIR vocabularies','I3-D Degree of connection','I score','FAIR score']
        else:
           header = ['kg_id','kg_name','Availability_Sparql-endpoint','Extra_SPARQL_endpoint_URL','Availability_Availability-of-RDF-dump-(metadata)','Availability_Availability-of-RDF-dump-(query)','Extra_URL-for-download-the-dataset','Availability_Inactive-links','Currency_Age-of-data','Currency_Modification-date','Currency_Percentage-of-data-updated','Currency_Time-elapsed-since-last-modification','Currency_Historical-updates','Versatility_Languages-(query)','Versatility_Languages-(metadata)','Versatility_Serialization-formats','Versatility_Availability-for-download-(query)','Versatility_Availability-for-download-(metadata)','Security_Use-HTTPS',
                     'Security_Requires-authentication','Representational-Conciseness_Average-length-of-URIs-(subject)','Representational-Conciseness_Standard-deviation-lenght-URIs-(subject)','Representational-Conciseness_Min-length-URIs-(subject)',
                     'Representational-Conciseness_25th-percentile-length-URIs-(subject)','Representational-Conciseness_Median-length-URIs-(subject)','Representational-Conciseness_75th-percentile-length-URIs-(subject)','Representational-Conciseness_Max-length-URIs-(subject)','Representational-Conciseness_Average-length-of-URIs-(predicate)','Representational-Conciseness_Standard-deviation-lenght-URIs-(predicate)',
                     'Representational-Conciseness_Min-length-URIs-(predicate)','Representational-Conciseness_25th-percentile-length-URIs-(predicate)','Representational-Conciseness_Median-length-URIs-(predicate)','Representational-Conciseness_75th-percentile-length-URIs-(predicate)','Representational-Conciseness_Max-length-URIs-(predicate)','Representational-Conciseness_Average-length-of-URIs-(object)','Representational-Conciseness_Standard-deviation-lenght-URIs-(object)','Representational-Conciseness_Min-length-URIs-(object)','Representational-Conciseness_25th-percentile-length-URIs-(object)','Median-length-URIs-(object)','Representational-Conciseness_75th-percentile-length-URIs-(object)','Representational-Conciseness_Max-length-URIs-(object)','Representational-Conciseness_Use-RDF-structures','License_License-machine-redeable-(metadata)','License-machine-redeable-(query)','License_License-human-redeable','Performance_Minimum-latency','Performance_25th-percentile-latency','Performance_Median-latency','Performance_75th-percentile-latency','Performance_Maximum-latency','Performance_Average-latency','Performance_Standard-deviation-of-latency','Performance_Minimum-throughput','Performance_25th-percentile-throughput',
                     'Performance_Median-throughput','Performance_75th-percentile-throughput','Performance_Maximum-throughput','Performance_Average-throughput','Performance_Standard-deviation-of-throughput','Amount-of-data_Number-of-triples-(metadata)','Amount-of-data_Number-of-triples-(query)','Amount-of-data_Number-of-entities','Amount-of-data_Number-of-entities-counted-with-regex','Amount-of-data_Number-of-property','Volatility_Dataset-update-frequency','Interlinking_Degree-of-connection','Interlinking_Clustering-coefficient','Interlinking_Centrality','Interlinking_Number-of-samAs-chains','Interlinking_External-links','Reputation_PageRank','Believability_Description','Believability_Dataset-URL','Believability_Is-on-a-trusted-provider-list','Believability_Trust-value','Verifiability_Vocabularies','Verifiability_Author-(query)','Verifiability_Author-(metadata)','Verifiability_Contributor','Verifiability_Publisher','Verifiability_Sources','Verifiability_Signed','Completeness_Number-of-triples','Completeness_Number-of-triples-linked','Completeness_Interlinking-completeness','Interoperability_New-vocabularies-defined-in-the-dataset','Interoperability_New-terms-defined-in-the-dataset','Understandability_Number-of-labels/comments-present-on-the-data','Understandability_Percentage-of-triples-with-labels','Understandability_Regex-uri','Understandability_Presence-of-example','Interpretability_Number-of-blank-nodes','Interpretability_Uses-RDF-structures','Consistency_Deprecated-classes/properties-used','Consistency_Entities-as-member-of-disjoint-class','Consistency_Triples-with-misplaced-property-problem','Consistency_Triples-with-misplaced-class-problem','Consistency_Ontology-Hijacking-problem','Consistency_Undefined-class-used-without-declaration','Consistency_Undefined-properties-used-without-declaration','Conciseness_Extensional-conciseness','Conciseness_Intensional-conciseness','Accuracy_Triples-with-empty-annotation-problem','Accuracy_Triples-with-white-space-in-annotation(at-the-beginning-or-at-the-end)','Accuracy_Triples-with-malformed-data-yype-literals-problem','Accuracy_Functional-properties-with-inconsistent-values','Accuracy_Invalid-usage-of-inverse-functional-properties','Extra_Number-of-triples-updated','Score','Normalized-score','Extra_Limited','Extra_Offline-dumps','Extra_Url-file-VoID','Extra_Availability-VoID-file','Extra_MinTPNoOff','Extra_MeanTPNoOff','Extra_MaxTPNoOff','Extra_sdTPNoOff','Extra_URIs-Deferenceability','Availability-score','Licensing-score','Interlinking-score','Performance-score','Accuracy-score','Consistency-score','Conciseness-score','Verifiability-score','Reputation-score','Believability-score',
                     'Currency-score','Volatility-score','Completeness-score','Amount-of-data-score','Representational-Consistency-score','Representational-Conciseness-score','Understandability-score','Interpretability-score','Versatility-score','Security-score','Interlinking_SKOS-mapping-properties', 'Extra_U1-value','Extra_CS2-value','Extra_IN3-value','Extra_RC1-value','Extra_RC2-value','Extra_IN4-value','Extra_metadata-media-type','Extra_Availability-of-a-common-accepted-Media-Type','Extra_U5-value','Extra_PE2-value','Extra_PE3-value']

        here = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(here,'../Analysis results')
        if include_dimensions == False:
            save_path = os.path.join(save_path, filename+".csv")
        else:
            save_path = os.path.join(save_path, filename+"_with_dimensions.csv")
        with open(save_path, 'w', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)

    def writeRow(self,filename,include_dimensions = False):
        here = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(here,'../Analysis results')
        if include_dimensions == False:
            save_path = os.path.join(save_path, filename+".csv")
        else:
            save_path = os.path.join(save_path, filename+"_with_dimensions.csv")
        with open(save_path, 'a', encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            if include_dimensions == False:
                data = [self.kgQuality.extra.KGid.replace(',',';'),self.kgQuality.believability.title,self.kgQuality.availability.sparqlEndpoint,self.kgQuality.extra.endpointUrl,self.kgQuality.availability.RDFDumpM,self.kgQuality.availability.RDFDumpQ,self.kgQuality.extra.downloadUrl,self.kgQuality.availability.inactiveLinks,self.kgQuality.currency.creationDate,self.kgQuality.currency.modificationDate,self.kgQuality.currency.percentageUpData,self.kgQuality.currency.timePassed,self.kgQuality.currency.historicalUp,self.kgQuality.versatility.languagesQ,self.kgQuality.versatility.languagesM,self.kgQuality.versatility.serializationFormats,self.kgQuality.versatility.availabilityDownloadQ,self.kgQuality.versatility.availabilityDownloadM,
                        self.kgQuality.security.useHTTPS,self.kgQuality.security.requiresAuth,self.kgQuality.rConciseness.urisLenghtSA,self.kgQuality.rConciseness.urisLenghtSSd,self.kgQuality.rConciseness.minLengthS,self.kgQuality.rConciseness.percentile25LengthS,self.kgQuality.rConciseness.medianLenghtS,self.kgQuality.rConciseness.percentile75LengthS,self.kgQuality.rConciseness.maxLengthS,self.kgQuality.rConciseness.urisLenghtPA,self.kgQuality.rConciseness.urisLenghtPSd,self.kgQuality.rConciseness.minLengthP,self.kgQuality.rConciseness.percentile25LengthP,self.kgQuality.rConciseness.medianLenghtP,self.kgQuality.rConciseness.percentile75LengthP,self.kgQuality.rConciseness.maxLengthP,self.kgQuality.rConciseness.urisLenghtOA,self.kgQuality.rConciseness.urisLenghtOSd,self.kgQuality.rConciseness.minLengthO,self.kgQuality.rConciseness.percentile25LengthO,self.kgQuality.rConciseness.medianLenghtO,self.kgQuality.rConciseness.percentile75LengthO,self.kgQuality.rConciseness.maxLengthO,self.kgQuality.rConciseness.RDFStructures,self.kgQuality.licensing.licenseMetadata,self.kgQuality.licensing.licenseQuery,self.kgQuality.licensing.licenseHR,self.kgQuality.performance.minLatency,self.kgQuality.performance.percentile25L,self.kgQuality.performance.medianL,self.kgQuality.performance.percentile75L,self.kgQuality.performance.maxLatency,self.kgQuality.performance.averageLatency,self.kgQuality.performance.sDLatency,self.kgQuality.performance.minThroughput,self.kgQuality.performance.percentile25T,self.kgQuality.performance.medianT,self.kgQuality.performance.percentile75T,self.kgQuality.performance.maxThroughput,self.kgQuality.performance.averageThroughput,self.kgQuality.performance.sDThroughput,
                        self.kgQuality.amountOfData.numTriplesM,self.kgQuality.amountOfData.numTriplesQ,self.kgQuality.amountOfData.numEntities,self.kgQuality.amountOfData.entitiesRe,self.kgQuality.amountOfData.numProperty,self.kgQuality.volatility.frequency,self.kgQuality.interlinking.degreeConnection,self.kgQuality.interlinking.clustering,self.kgQuality.interlinking.centrality,self.kgQuality.interlinking.sameAs,ExternalLink.getListExLinks(self.kgQuality.interlinking.externalLinks),
                        self.kgQuality.reputation.pageRank,self.kgQuality.believability.description,self.kgQuality.believability.URI,self.kgQuality.believability.reliableProvider,self.kgQuality.believability.trustValue,self.kgQuality.verifiability.vocabularies,self.kgQuality.verifiability.authorQ,self.kgQuality.verifiability.authorM,self.kgQuality.verifiability.contributor,self.kgQuality.verifiability.publisher,"Web:"+str(self.kgQuality.verifiability.sources.web)+" Name:"+ str(self.kgQuality.verifiability.sources.name)+" Email:"+ str(self.kgQuality.verifiability.sources.email),self.kgQuality.verifiability.sign,self.kgQuality.completeness.numTriples,self.kgQuality.completeness.numTriplesL,self.kgQuality.completeness.interlinkingC,self.kgQuality.rConsistency.newVocab,self.kgQuality.rConsistency.useNewTerms,self.kgQuality.understendability.numLabel,self.kgQuality.understendability.percentageLabel,self.kgQuality.understendability.regexUri,self.kgQuality.understendability.example,
                        self.kgQuality.interpretability.numBN,self.kgQuality.interpretability.RDFStructures,self.kgQuality.consistency.deprecated,self.kgQuality.consistency.disjointClasses,self.kgQuality.consistency.triplesMP,self.kgQuality.consistency.triplesMC,self.kgQuality.consistency.oHijacking,self.kgQuality.consistency.undefinedClass,self.kgQuality.consistency.undefinedProperties,self.kgQuality.conciseness.exC,self.kgQuality.conciseness.intC,self.kgQuality.accuracy.emptyAnn,self.kgQuality.accuracy.wSA,self.kgQuality.accuracy.malformedDataType,self.kgQuality.accuracy.FPvalue,self.kgQuality.accuracy.IFPvalue,self.kgQuality.extra.numTriplesUpdated,self.kgQuality.extra.score,self.kgQuality.extra.normalizedScore,self.kgQuality.extra.limited,self.kgQuality.extra.offlineDumps,self.kgQuality.extra.urlVoid,self.kgQuality.extra.voidAvailability,self.kgQuality.extra.minTPNoOff,self.kgQuality.extra.meanTPNoOff,self.kgQuality.extra.maxTPNoOff,self.kgQuality.extra.devSNoOff,self.kgQuality.availability.uriDef,
                        self.kgQuality.extra.scoreObj.availabilityScoreValue,self.kgQuality.extra.scoreObj.licensingScoreValue,self.kgQuality.extra.scoreObj.interlinkingScoreValue,self.kgQuality.extra.scoreObj.performanceScoreValue,self.kgQuality.extra.scoreObj.accuracyScoreValue,self.kgQuality.extra.scoreObj.consistencyScoreValue,self.kgQuality.extra.scoreObj.concisenessScoreValue,self.kgQuality.extra.scoreObj.verifiabilityScoreValue,self.kgQuality.extra.scoreObj.reputationScoreValue,self.kgQuality.extra.scoreObj.believabilityScoreValue,self.kgQuality.extra.scoreObj.currencyScoreValue,self.kgQuality.extra.scoreObj.volatilityScoreValue,
                        self.kgQuality.extra.scoreObj.completenessScoreValue,self.kgQuality.extra.scoreObj.amountScoreValue,self.kgQuality.extra.scoreObj.repConsScoreValue,self.kgQuality.extra.scoreObj.repConcScoreValue,self.kgQuality.extra.scoreObj.understScoreValue,self.kgQuality.extra.scoreObj.interpretabilityScoreValue,self.kgQuality.extra.scoreObj.versatilityScoreValue,self.kgQuality.extra.scoreObj.securityScoreValue,self.kgQuality.interlinking.skosMapping,self.kgQuality.extra.scoreObj.labelValue, self.kgQuality.extra.scoreObj.misplacedValue, self.kgQuality.extra.scoreObj.undefValue, self.kgQuality.extra.scoreObj.uriValue, self.kgQuality.extra.scoreObj.rdfValue, self.kgQuality.extra.scoreObj.blankValue, self.kgQuality.extra.metadataMediaType, self.kgQuality.extra.commonMediaType,self.kgQuality.extra.scoreObj.vocabsValue,self.kgQuality.extra.scoreObj.tpValue,self.kgQuality.extra.scoreObj.latencyValue,
                        self.kgQuality.fairness.f1M,self.kgQuality.fairness.f1D, self.kgQuality.fairness.f2aM, self.kgQuality.fairness.f2bM, self.kgQuality.fairness.f3M, self.kgQuality.fairness.f4M, self.kgQuality.fairness.f_score, self.kgQuality.fairness.a1D, self.kgQuality.fairness.a1M, self.kgQuality.fairness.a1_2, self.kgQuality.fairness.a2M,self.kgQuality.fairness.a_score,self.kgQuality.fairness.r1_1,self.kgQuality.fairness.r1_2, self.kgQuality.fairness.r1_3D,self.kgQuality.fairness.r1_3M, self.kgQuality.fairness.r_score, self.kgQuality.fairness.i1D, self.kgQuality.fairness.i1M, self.kgQuality.fairness.i2, self.kgQuality.fairness.i3D, self.kgQuality.fairness.i_score, self.kgQuality.fairness.fair_score]
            else:
                data = [self.kgQuality.extra.KGid.replace(',',';'),self.kgQuality.believability.title,self.kgQuality.availability.sparqlEndpoint,self.kgQuality.extra.endpointUrl,self.kgQuality.availability.RDFDumpM,self.kgQuality.availability.RDFDumpQ,utils.if_list_return_int(self.kgQuality.extra.downloadUrl),self.kgQuality.availability.inactiveLinks,self.kgQuality.currency.creationDate,self.kgQuality.currency.modificationDate,self.kgQuality.currency.percentageUpData,self.kgQuality.currency.timePassed,utils.if_list_return_int(self.kgQuality.currency.historicalUp),self.kgQuality.versatility.languagesQ,self.kgQuality.versatility.languagesM,self.kgQuality.versatility.serializationFormats,self.kgQuality.versatility.availabilityDownloadQ,self.kgQuality.versatility.availabilityDownloadM,
                        self.kgQuality.security.useHTTPS,self.kgQuality.security.requiresAuth,self.kgQuality.rConciseness.urisLenghtSA,self.kgQuality.rConciseness.urisLenghtSSd,self.kgQuality.rConciseness.minLengthS,self.kgQuality.rConciseness.percentile25LengthS,self.kgQuality.rConciseness.medianLenghtS,self.kgQuality.rConciseness.percentile75LengthS,self.kgQuality.rConciseness.maxLengthS,self.kgQuality.rConciseness.urisLenghtPA,self.kgQuality.rConciseness.urisLenghtPSd,self.kgQuality.rConciseness.minLengthP,self.kgQuality.rConciseness.percentile25LengthP,self.kgQuality.rConciseness.medianLenghtP,self.kgQuality.rConciseness.percentile75LengthP,self.kgQuality.rConciseness.maxLengthP,self.kgQuality.rConciseness.urisLenghtOA,self.kgQuality.rConciseness.urisLenghtOSd,self.kgQuality.rConciseness.minLengthO,self.kgQuality.rConciseness.percentile25LengthO,self.kgQuality.rConciseness.medianLenghtO,self.kgQuality.rConciseness.percentile75LengthO,self.kgQuality.rConciseness.maxLengthO,self.kgQuality.rConciseness.RDFStructures,self.kgQuality.licensing.licenseMetadata,self.kgQuality.licensing.licenseQuery,self.kgQuality.licensing.licenseHR,self.kgQuality.performance.minLatency,self.kgQuality.performance.percentile25L,self.kgQuality.performance.medianL,self.kgQuality.performance.percentile75L,self.kgQuality.performance.maxLatency,self.kgQuality.performance.averageLatency,self.kgQuality.performance.sDLatency,self.kgQuality.performance.minThroughput,self.kgQuality.performance.percentile25T,self.kgQuality.performance.medianT,self.kgQuality.performance.percentile75T,self.kgQuality.performance.maxThroughput,self.kgQuality.performance.averageThroughput,self.kgQuality.performance.sDThroughput,
                        self.kgQuality.amountOfData.numTriplesM,self.kgQuality.amountOfData.numTriplesQ,self.kgQuality.amountOfData.numEntities,self.kgQuality.amountOfData.entitiesRe,self.kgQuality.amountOfData.numProperty,utils.if_list_return_int(self.kgQuality.volatility.frequency),self.kgQuality.interlinking.degreeConnection,self.kgQuality.interlinking.clustering,self.kgQuality.interlinking.centrality,self.kgQuality.interlinking.sameAs,ExternalLink.getListExLinks(self.kgQuality.interlinking.externalLinks),
                        self.kgQuality.reputation.pageRank,self.kgQuality.believability.description,self.kgQuality.believability.URI,self.kgQuality.believability.reliableProvider,self.kgQuality.believability.trustValue,utils.if_list_return_int(self.kgQuality.verifiability.vocabularies),utils.if_list_return_int(self.kgQuality.verifiability.authorQ),self.kgQuality.verifiability.authorM,utils.if_list_return_int(self.kgQuality.verifiability.contributor),utils.if_list_return_int(self.kgQuality.verifiability.publisher),"Web:"+str(self.kgQuality.verifiability.sources.web)+" Name:"+ str(self.kgQuality.verifiability.sources.name)+" Email:"+ str(self.kgQuality.verifiability.sources.email),self.kgQuality.verifiability.sign,self.kgQuality.completeness.numTriples,self.kgQuality.completeness.numTriplesL,self.kgQuality.completeness.interlinkingC,utils.if_list_return_int(self.kgQuality.rConsistency.newVocab),utils.if_list_return_int(self.kgQuality.rConsistency.useNewTerms),self.kgQuality.understendability.numLabel,self.kgQuality.understendability.percentageLabel,utils.if_list_return_int(self.kgQuality.understendability.regexUri),self.kgQuality.understendability.example,
                        self.kgQuality.interpretability.numBN,self.kgQuality.interpretability.RDFStructures,self.kgQuality.consistency.deprecated,self.kgQuality.consistency.disjointClasses,self.kgQuality.consistency.triplesMP,self.kgQuality.consistency.triplesMC,self.kgQuality.consistency.oHijacking,self.kgQuality.consistency.undefinedClass,self.kgQuality.consistency.undefinedProperties,self.kgQuality.conciseness.exC,self.kgQuality.conciseness.intC,self.kgQuality.accuracy.emptyAnn,self.kgQuality.accuracy.wSA,self.kgQuality.accuracy.malformedDataType,self.kgQuality.accuracy.FPvalue,self.kgQuality.accuracy.IFPvalue,self.kgQuality.extra.numTriplesUpdated,self.kgQuality.extra.score,self.kgQuality.extra.normalizedScore,self.kgQuality.extra.limited,utils.if_list_return_int(self.kgQuality.extra.offlineDumps),self.kgQuality.extra.urlVoid,self.kgQuality.extra.voidAvailability,self.kgQuality.extra.minTPNoOff,self.kgQuality.extra.meanTPNoOff,self.kgQuality.extra.maxTPNoOff,self.kgQuality.extra.devSNoOff,self.kgQuality.availability.uriDef,
                        self.kgQuality.extra.scoreObj.availabilityScoreValue,self.kgQuality.extra.scoreObj.licensingScoreValue,self.kgQuality.extra.scoreObj.interlinkingScoreValue,self.kgQuality.extra.scoreObj.performanceScoreValue,self.kgQuality.extra.scoreObj.accuracyScoreValue,self.kgQuality.extra.scoreObj.consistencyScoreValue,self.kgQuality.extra.scoreObj.concisenessScoreValue,self.kgQuality.extra.scoreObj.verifiabilityScoreValue,self.kgQuality.extra.scoreObj.reputationScoreValue,self.kgQuality.extra.scoreObj.believabilityScoreValue,self.kgQuality.extra.scoreObj.currencyScoreValue,self.kgQuality.extra.scoreObj.volatilityScoreValue,
                        self.kgQuality.extra.scoreObj.completenessScoreValue,self.kgQuality.extra.scoreObj.amountScoreValue,self.kgQuality.extra.scoreObj.repConsScoreValue,self.kgQuality.extra.scoreObj.repConcScoreValue,self.kgQuality.extra.scoreObj.understScoreValue,self.kgQuality.extra.scoreObj.interpretabilityScoreValue,self.kgQuality.extra.scoreObj.versatilityScoreValue,self.kgQuality.extra.scoreObj.securityScoreValue,self.kgQuality.interlinking.skosMapping, self.kgQuality.extra.scoreObj.labelValue, self.kgQuality.extra.scoreObj.misplacedValue, self.kgQuality.extra.scoreObj.undefValue, self.kgQuality.extra.scoreObj.uriValue, self.kgQuality.extra.scoreObj.rdfValue, self.kgQuality.extra.scoreObj.blankValue, self.kgQuality.extra.metadataMediaType, self.kgQuality.extra.commonMediaType,self.kgQuality.extra.scoreObj.vocabsValue,self.kgQuality.extra.scoreObj.tpValue,self.kgQuality.extra.scoreObj.latencyValue]

            writer.writerow(data)
    
    def normalizeScore(filename):
        here = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(here,'./Analysis results')
        save_path = os.path.join(save_path, filename+".csv")
        df = pd.read_csv(save_path)
        df_min_max_scaled = df.copy()
        column = 'Score' 
        listNormalized = df_min_max_scaled[column].tolist()
        for i in range(len(listNormalized)):
            score = listNormalized[i]
            percentage = (score * 100)/2.65
            normalizedScore = float("%.2f"%percentage)
            if normalizedScore > 100.00:
                normalizedScore = 100.00
            listNormalized[i] = normalizedScore
        for i in range(df.shape[0]):
            df.at[i,"Normalized score"] = listNormalized[i]
        df.to_csv(save_path,index=False)
        #print(listNormalized)
        '''
        with open(save_path,'w',encoding='UTF8', newline='') as f:
            writer = csv.writer(f)
            for i in range(df.shape[0]):
                row = df.iloc[i]
                lst = row.tolist()
                lst[len(lst)-1] = listNormalized[i]
                print(lst[len(lst)-1])
                writer.writerow(lst)
        '''

    def split(idList):
        here = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(here,'./Graphs Visualization JS/CSVforJS')
        analysisR = os.path.join(here,'./Analysis results')
        p = Path(analysisR)
        files = list(p.glob('*.csv'))
        fileNames = []
        idNameLi = []
        for i in range(len(idList)):
            newFilename = re.sub(r'[\\/*?:"<>|]',"",idList[i])
            remove_punctuation_map = dict((ord(char), None) for char in '\/*?:"<>|')
            newFilename = newFilename.translate(remove_punctuation_map)
            remove_punctuation_map = dict((ord(char), None) for char in string.punctuation)
            newFilename = newFilename.translate(remove_punctuation_map)
            newFilename = newFilename.replace(" ","")
            if '_' in idList[i]:
                newFilename = newFilename + '_'
            completeName = os.path.join(save_path, newFilename+".csv")
            fileNames.append(newFilename)
            with open(completeName,'w',newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(['Date','SPARQL endpoint','RDF dump','License Machine-Redeable','License Human-Redeable','KG name','Description','Url','Reliable','Trust value'
                                ,'Degree of connection','Clustring coefficient','Centrality','Number of sameAs chains','Number of triples','KGid','Min latency','25th percentile latency','Median latency','75th percentile latency','Max latency',
                                'Min TP','25th percentile TP','Median TP','75th percentile TP','Max TP','Requires auth','Use HTTPS','Serialization formats','Languages','Link SPARQL endpoint','Link for download the dataset','Number of void label',
                                'Number of whitespace label','Number of malformed datatype','Labels','Disjoint class','Undefined class','Undefined property','Deprecated class/property','Ontology hijacking','Misplaced property','Misplaced class',
                                'PageRank','Vocabularies','Authors','Publishers','Contributors','Sources','Signed','Dataset update frequency','Age of data','Modification date','Num. triples updated','Time since last modification',
                                'Extensional conciseness','Intensional conciseness','Interlinking completeness','Number of triples linked','Number of entities','Number of property','Min length URIs (subject)','25th percentile length URIs (subject)','Median length URIs (subject)','75th percentile length URIs (subject)','Max length URIs (subject)'
                                ,'Min length URIs (predicate)','25th percentile length URIs (predicate)','Median length URIs (predicate)','75th percentile length URIs (predicate)','Max length URIs (predicate)','Min length URIs (object)','25th percentile length URIs (object)','Median length URIs (object)','75th percentile length URIs (object)','Max length URIs (object)',
                                'New vocabularies defined','New terms defined','Number of label','Uri regex','Presence of example','Number of blank nodes','RDF structures','HistoricalUp','Score','Normalized score','FP','IFP','Limited','License MR','Inactive links'])
                idForTxt = ''
                nameForTxt = ''
                files.sort()
                for f in files:
                    file_name = f.stem
                    filename = str(file_name)
                    print(filename)
                    df = pd.read_csv(f)
                    df = df[df['KG id'] == '%s'%idList[i]]
                    count = df.shape[0]   #GET THE NUMBER OF ROW FOUNDED WITH THE KG ID 
                    if count == 1:
                        
                        endpoint = df.iloc[0]['Sparql endpoint']  #SEARCH FOR THE COLUMN WITH NAME SPARQL ENPOINT AND GET THE VALUE
                        endpoint = str(endpoint)
                        endpoint = endpoint.replace(',',';')
                        if endpoint == 'Available':   #FORMATTING DATA FOR HIGHCHART
                            endpoint = 1
                        if endpoint == 'endpoint offline':
                            endpoint = 0
                        if endpoint == 'endpoint absent':
                            endpoint = -1
                        
                        rdfDumpQ = df.iloc[0]['Availability of RDF dump (query)']
                        rdfDumpM = df.iloc[0]['Availability of RDF dump (metadata)']
                        if (rdfDumpQ != 'True' and rdfDumpQ != True) and (rdfDumpM == 0):
                            dump = 0
                        elif rdfDumpM == -1 or rdfDumpQ == 'absent':
                            dump = -1
                        else:
                            dump = 1
                        
                        licenseMRM= df.iloc[0]['License machine redeable (metadata)']
                        licenseMRQ = df.iloc[0]['License machine redeable (query)']
                        licenseHR = df.iloc[0]['License human redeable']
                        licenseMRM = (str(licenseMRM).replace(',',';')).replace("\r", "").replace("\n", "")
                        licenseMRQ = (str(licenseMRQ).replace(',',';')).replace("\r", "").replace("\n", "")

                        if isinstance(licenseHR,str):
                            if 'EndPointInternalError' in licenseHR or 'endpoint offline' in  licenseHR or 'endpoint absent' in licenseHR:
                                licenseHR = '-'
                            if 'Could not' in licenseHR:
                                licenseHR = 'Query fails on endpoint'
                        
                        name = df.iloc[0]['KG name']
                        description = df.iloc[0]['Description']
                        url = df.iloc[0]['Dataset URL']
                        provList = df.iloc[0]['Is on a trusted provider list']
                        trustValue = df.iloc[0]['Trust value']

                        name = str(name)
                        name = name.replace(',','-')
                        name = name.replace("\r", "").replace("\n", "")
                        description = str(description)
                        description = description.replace(',','-')
                        description = description.replace("\r", "").replace("\n", "")
                        url = str(url)
                        url = url.replace(',','-')
                        url = url.replace("\r", "").replace("\n", "")
                        provList = str(provList)
                        provList = provList.replace(',','-')
                        provList = provList.replace("\r", "").replace("\n", "")
                        trustValue = str(trustValue)
                        trustValue = trustValue.replace(',','.')
                        trustValue = trustValue.replace("\r", "").replace("\n", "")

                        dC = df.iloc[0]['Degree of connection']
                        ccl = df.iloc[0]['Clustering coefficient']
                        ccl = str(ccl).replace("\r", "").replace("\n", "")
                        ccl = ccl.replace(',','.')
                        centrlity = df.iloc[0]['Centrality']
                        centrlity = str(centrlity)
                        centrlity = centrlity.replace(',','.').replace("\r", "").replace("\n", "")
                        sameAs = df.iloc[0]['Number of samAs chains']
                        numTriples = df.iloc[0]['Number of triples (query)']
                        try:
                            numTriples = int(numTriples)
                        except:
                            numTriples = df.iloc[0][' Number of triples (metadata)']
                        try:
                            numTriples = int(numTriples)
                        except:
                            numTriples = '-'
                        try:
                            sameAs = int(sameAs)
                        except:
                            sameAs = '-'

                        minL = df.iloc[0]['Minimum latency']
                        minL = str(minL)
                        minL = minL.replace(',','.').replace("\r", "").replace("\n", "")
                        percentile25L = df.iloc[0]['25th percentile latency']
                        medianL = df.iloc[0]['Median latency']
                        percentile75L = df.iloc[0]['75th percentile latency']
                        percentile25L = str(percentile25L)
                        percentile25L = percentile25L.replace(',','.').replace("\r", "").replace("\n", "")
                        medianL = str(medianL)
                        medianL = medianL.replace(',','.').replace("\r", "").replace("\n", "")
                        percentile75L = str(percentile75L)
                        percentile75L = percentile75L.replace(',','.').replace("\r", "").replace("\n", "")
                        maxL = df.iloc[0]['Maximum latency']
                        maxL = str(maxL)
                        maxL = maxL.replace(',','.').replace("\r", "").replace("\n", "")
                        minT = df.iloc[0]['Minimum throughput']
                        minT = str(minT)
                        minT = minT.replace(',','.').replace("\r", "").replace("\n", "")
                        maxT = df.iloc[0]['Maximum throughput']
                        maxT = str(maxT)
                        maxT = maxT.replace(',','.').replace("\r", "").replace("\n", "")
                        percentile25T = df.iloc[0]['25th percentile throughput']
                        medianT = df.iloc[0]['Median throughput']
                        percentile75T = df.iloc[0]['75th percentile throughput']
                        percentile25T = str(percentile25T)
                        percentile25T = percentile25T.replace(',','.').replace("\r", "").replace("\n", "")
                        medianT = str(medianT)
                        medianT = medianT.replace(',','.').replace("\r", "").replace("\n", "")
                        percentile75T = str(percentile75T)
                        percentile75T = percentile75T.replace(',','.').replace("\r", "").replace("\n", "")

                        if minL == 'endpoint offline':
                            minL = '-'
                        if maxL == 'endpoint offline':
                            maxL = '-'
                        if percentile25L == 'endpoint offline':
                            percentile25L = '-'
                        if percentile75L == 'endpoint offline':
                            percentile75L = '-'
                        if medianL == 'endpoint offline':
                            medianL = '-'
                        if percentile25T == 'endpoint offline':
                            percentile25T = '-'
                        if percentile75T == 'endpoint offline':
                            percentile75T = '-'
                        if medianT == 'endpoint offline':
                            medianT = '-'
                        if minT == 'endpoint offline':
                            minT = '-'
                        if maxT == 'endpoint offline':
                            maxT = '-'
                        
                        auth = df.iloc[0]['Requires authentication']
                        https = df.iloc[0]['Use HTTPS']

                        if https == 'endpoint offline' or https == 'endpoint absent':
                            https = '-'
                        if auth == 'endpoint offline' or auth == 'endpoint absent':
                            auth = '-'

                        try:
                            voidLabel = df.iloc[0]['Triples with empty annotation problem']
                            voidLabel = float(voidLabel.replace(',','.'))
                            voidLabel = (str(voidLabel)).replace(',','.').replace("\r", "").replace("\n", "")
                        except ValueError:
                            voidLabel = '-'
                        
                        try:
                            whitespaceLabel = df.iloc[0]['Triples with white space in annotation(at the beginning or at the end)']
                            whitespaceLabel = float(whitespaceLabel.replace(',','.'))
                            whitespaceLabel = str((whitespaceLabel)).replace(',','.').replace("\r", "").replace("\n", "")
                        except ValueError:
                            whitespaceLabel = '-'
                        
                        try:
                            datatypeProblem = df.iloc[0]['Triples with malformed data type literals problem']
                            datatypeProblem = float(datatypeProblem.replace(',','.'))
                            datatypeProblem = str((datatypeProblem)).replace(',','.').replace("\r", "").replace("\n", "")
                        except ValueError:
                            datatypeProblem = '-'
                        
                        labels = df.iloc[0]['Number of labels/comments present on the data']

                        
                        numDisjoint = df.iloc[0]['Entities as member of disjoint class']
                        undefClass = df.iloc[0]['Undefined class used without declaration']
                        undefProp = df.iloc[0]['Undefined properties used without declaration']
                        deprecated = df.iloc[0]['Deprecated classes/properties used']
                        hijacking = df.iloc[0]['Ontology Hijacking problem']
                        misplacedP = df.iloc[0]['Triples with misplaced property problem']
                        misplacedC = df.iloc[0]['Triples with misplaced class problem']
                        
                        try:
                            misplacedP = float(misplacedP)
                            misplacedP = str(misplacedP)
                            misplacedP = misplacedP.replace(',','.').replace("\r", "").replace("\n", "")     
                        except:
                            misplacedP = '-'
                        
                        try:
                            misplacedC = float(misplacedC)
                            misplacedC = str(misplacedC)
                            misplacedC = misplacedC.replace(',','.').replace("\r", "").replace("\n", "")    
                        except:
                            misplacedC = '-'

                        try:
                            undefClass = float(undefClass)
                            undefClass = str(undefClass)
                            undefClass = undefClass.replace(',','.').replace("\r", "").replace("\n", "")         
                        except:
                            undefClass = '-'
                        
                        try:
                            undefProp = float(undefProp)
                            undefProp = str(undefProp)
                            undefProp = undefProp.replace(',','.').replace("\r", "").replace("\n", "")         
                        except:
                            undefProp = '-'
                        
                        try:
                            deprecated = float(deprecated)
                            deprecated = str(deprecated)
                            deprecated = deprecated.replace(',','.').replace("\r", "").replace("\n", "")         
                        except:
                            deprecated = '-'
                        
                        try:
                            numDisjoint = float(numDisjoint)
                            numDisjoint = str(numDisjoint)
                            numDisjoint = numDisjoint.replace(',','.').replace("\r", "").replace("\n", "")         
                        except:
                            numDisjoint = '-'
                        

                        pagerank = df.iloc[0]['PageRank']
                        try:
                            pagerank = str(pagerank)
                            pagerank = pagerank.replace(',','.').replace("\r", "").replace("\n", "")
                            pagerank = float(pagerank)
                        except:
                            pagerank = '-'
                        
                        vocabularies = df.iloc[0]['Vocabularies']
                        if vocabularies != 'endpoint offline' and vocabularies != 'endpoint absent' and not 'Could' in vocabularies and not 'Error' in vocabularies and vocabularies != '[]':
                            vocabularies = vocabularies.replace('[','').replace("\r", "").replace("\n", "")
                            vocabularies = vocabularies.replace(']','')
                            vocabularies = vocabularies.replace("'","")
                            vocabularies = vocabularies.replace(',',';')
                        elif vocabularies == '[]':
                            vocabularies = 'Not indicated'
                        
                        author = df.iloc[0]['Author (metadata)']
                        if author == 'False':
                            author = df.iloc[0]['Author (query)']
                            if author != 'endpoint offline' and author != 'endpoint absent' and not 'Could' in author and not 'Error' in author and author != '[]':
                                author = author.replace('[','').replace("\r", "").replace("\n", "")
                                author = author.replace(']','')
                                author = author.replace("'","")
                                author = author.replace(',',';')
                            elif author == '[]':
                                author = 'Not indicated'
                        else:
                            author = str(author)
                            author = author.replace(',',';')

                        publisher = df.iloc[0]['Publisher']
                        publisher = str(publisher)
                        if publisher == '[]':
                            publisher = 'Not indicated'
                        else:
                            publisher = publisher.replace('[','')
                            publisher = publisher.replace(']','')
                            publisher = publisher.replace("'","")
                            publisher = publisher.replace(',',';').replace("\r", "").replace("\n", "")


                        contributor = df.iloc[0]['Contributor']
                        contributor = str(contributor)
                        if contributor == '[]':
                            contributor = 'Not indicated'
                        else:
                            contributor = contributor.replace('[','')
                            contributor = contributor.replace(']','')
                            contributor = contributor.replace("'","")
                            contributor = contributor.replace(',',';').replace("\r", "").replace("\n", "")
                        
                        
                        sources = df.iloc[0]['Sources']
                        sources = str(sources)
                        sources = sources.replace(',',';').replace("\r", "").replace("\n", "")

                        
                        signed = df.iloc[0]['Signed']     
                        
                        
                        creationDate = df.iloc[0]['Age of data']
                        if creationDate == 'absent':
                            creationDate = 'Not indicated'
                        else:
                            try:
                                datetime.strptime(creationDate,'%Y-%m-%d')
                            except:
                                creationDate = '-'
                        
                        modificationDate = df.iloc[0]['Modification date']
                        if modificationDate == 'absent':
                            modificationDate = 'Not indicated'
                        else:
                            try:
                                datetime.strptime(modificationDate,'%Y-%m-%d')
                            except:
                                modificationDate = '-'
                        
                        triplesUpdated = df.iloc[0]['Number of triples updated']
                        
                        try:
                            triplesUpdated = int(triplesUpdated)
                        except:
                            triplesUpdated = 'insufficient data'
                        
                        
                        lastModification = df.iloc[0]['Time elapsed since last modification']
                        try:
                            lastModification = int(lastModification)
                        except:
                            lastModification = 'insufficient data'
                        
                        frequency = df.iloc[0]['Dataset update frequency']
                        frequency = str(frequency)
                        if frequency == '[]':
                            frequency = 'not indicated'
                        else:
                            frequency = str(frequency)
                            frequency = frequency.replace(',',';')
                            frequency = frequency.replace('[','')
                            frequency = frequency.replace(']','')
                            frequency = frequency.replace("'",'').replace("\r", "").replace("\n", "")
                            
                        exC = df.iloc[0]['Extensional conciseness']
                        intC = df.iloc[0]['Intensional conciseness']

                        interCompl = df.iloc[0]['Interlinking completeness']
                        numTriplesLinked = df.iloc[0]['Number of triples linked']

                        numEntities = df.iloc[0]['Number of entities']
                        try:
                            numEntities = int(numEntities)
                        except:
                            numEntities = df.iloc[0]['Number of entities counted with regex']

                        numProperty = df.iloc[0]['Number of property']

                        minLS = df.iloc[0]['Min length URIs (subject)']
                        percentile25LS = df.iloc[0]['25th percentile length URIs (subject)']
                        medianLS = df.iloc[0]['Median length URIs (subject)']
                        percentile75LS = df.iloc[0]['75th percentile length URIs (subject)']
                        maxLS = df.iloc[0]['Max length URIs (subject)']
                        minLS = str(minLS)
                        percentile25LS = str(percentile25LS)
                        medianLS = str(medianLS)
                        percentile75LS = str(percentile75LS)
                        maxLS = str(maxLS)
                        minLS = minLS.replace(',','.')
                        percentile25LS = percentile25LS.replace(',','.').replace("\r", "").replace("\n", "")
                        medianLS = medianLS.replace(',','.')
                        percentile75LS = percentile75LS.replace(',','.').replace("\r", "").replace("\n", "")
                        maxLS = maxLS.replace(',','.')


                        minLP = df.iloc[0]['Min length URIs (predicate)']
                        percentile25LP = df.iloc[0]['25th percentile length URIs (predicate)']
                        medianLP = df.iloc[0]['Median length URIs (predicate)']
                        percentile75LP = df.iloc[0]['75th percentile length URIs (predicate)']
                        maxLP = df.iloc[0]['Max length URIs (predicate)']
                        minLP = str(minLP)
                        percentile25LP = str(percentile25LP)
                        medianLP = str(medianLP)
                        percentile75LP = str(percentile75LP)
                        maxLP = str(maxLP)
                        minLP = minLP.replace(',','.')
                        percentile25LP = percentile25LP.replace(',','.').replace("\r", "").replace("\n", "")
                        medianLP = medianLP.replace(',','.')
                        percentile75LP = percentile75LP.replace(',','.').replace("\r", "").replace("\n", "")
                        maxLP = maxLP.replace(',','.')

                        minLO = df.iloc[0]['Min length URIs (object)']
                        percentile25LO = df.iloc[0]['25th percentile length URIs (object)']
                        medianLO = df.iloc[0]['Median length URIs (object)']
                        percentile75LO = df.iloc[0]['75th percentile length URIs (object)']
                        maxLO = df.iloc[0]['Max length URIs (object)']
                        minLO = str(minLO)
                        percentile25LO = str(percentile25LO)
                        medianLO = str(medianLO)
                        percentile75LO = str(percentile75LO)
                        maxLO = str(maxLO)
                        minLO = minLO.replace(',','.')
                        percentile25LO = percentile25LO.replace(',','.').replace("\r", "").replace("\n", "")
                        medianLO = medianLO.replace(',','.').replace("\r", "").replace("\n", "")
                        percentile75LO = percentile75LO.replace(',','.').replace("\r", "").replace("\n", "")
                        maxLO = maxLO.replace(',','.').replace("\r", "").replace("\n", "")

                        newVocabs = df.iloc[0]['New vocabularies defined in the dataset']
                        if newVocabs == '[]':
                            newVocabs = 'No new vocabulary defined'
                        else:
                            newVocabs = newVocabs.replace('[','')
                            newVocabs = newVocabs.replace(']','')
                            newVocabs = newVocabs.replace("'","")
                            newVocabs = newVocabs.replace(',',';').replace("\r", "").replace("\n", "")
            
                        newTerms = df.iloc[0]['New terms defined in the dataset']
                        if newTerms == '[]':
                            newTerms = 'No new term defined'
                        else:
                            newTerms = newTerms.replace('[','')
                            newTerms = newTerms.replace(']','')
                            newTerms = newTerms.replace("'","")
                            newTerms = newTerms.replace(',',';').replace("\r", "").replace("\n", "")

                        numLabel = df.iloc[0]['Number of labels/comments present on the data']
                        regexUri = df.iloc[0]['Regex uri']
                        regexUri = str(regexUri)
                        if regexUri == '[]':
                                regexUri = 'No regex provided'
                        else:
                            regexUri = regexUri.replace('[','')
                            regexUri = regexUri.replace(']','')
                            regexUri = regexUri.replace("'","")
                            regexUri = regexUri.replace(',',';').replace("\r", "").replace("\n", "")
                        
                        example = df.iloc[0]['Presence of example']

                        blankNodes = df.iloc[0]['Number of blank nodes']
                        try:
                            blankNodes = int(blankNodes)
                        except:
                            blankNodes = str(blankNodes).replace("\r", "").replace("\n", "")
                        
                        rdfS = df.iloc[0]['Uses RDF structures']
                        formats = df.iloc[0]['Serialization formats']
                        formats = str(formats)
                        if formats == '[]':
                            'No serialization format found'
                        else:
                            formats = formats.replace('[','')
                            formats = formats.replace(']','')
                            formats = formats.replace("'","")
                            formats = formats.replace(',',';').replace("\r", "").replace("\n", "")
                        
                        languages = df.iloc[0]['Languages (query)']
                        languages = str(languages)
                        if languages == '[]':
                            'No language indicated'
                        else:
                            languages = languages.replace('[','')
                            languages = languages.replace(']','')
                            languages = languages.replace("'","")
                            languages = languages.replace(',',';').replace("\r", "").replace("\n", "")
                        
                        linkSparql = df.iloc[0]['SPARQL endpoint URL']
                        linkSparql = str(linkSparql)
                        if linkSparql == '':
                            linkSparql = 'Not provided'
                        
                        linkDump = df.iloc[0]['URL for download the dataset']
                        linkDump = str(linkDump)
                        if linkDump == '[]':
                            linkDump = 'Not provided'
                        else:
                            linkDump = linkDump.replace('[','')
                            linkDump = linkDump.replace(']','')
                            linkDump = linkDump.replace("'","")
                            linkDump = linkDump.replace(',',';').replace("\r", "").replace("\n", "")
                        
                        
                        historicalUp = df.iloc[0]["Historical updates"]
                        historicalUp = str(historicalUp)
                        if historicalUp == '[]':
                            historicalUp = 'Insufficient data'
                        else:
                            historicalUp = historicalUp.replace('[','')
                            historicalUp = historicalUp.replace(']','')
                            historicalUp = historicalUp.replace("'","")
                            historicalUp = historicalUp.replace(',',';').replace("\r", "").replace("\n", "")
                        
                        try:
                            FPvalue = df.iloc[0]['Functional properties with inconsistent values']
                            FPvalue = float(FPvalue.replace(',','.'))
                            FPvalue = str((FPvalue)).replace(',','.').replace("\r", "").replace("\n", "")
                        except:
                            FPvalue = '-'
                        
                        try:
                            IFPvalue = df.iloc[0]['Invalid usage of inverse-functional properties']
                            IFPvalue = float(IFPvalue.replace(',','.'))
                            IFPvalue = str((IFPvalue)).replace(',','.').replace("\r", "").replace("\n", "")
                        except:
                            IFPvalue = '-'
                    
                        score = str(df.iloc[0]['Score'])
                        normalizedS = str(df.iloc[0]['Normalized score'])
                        normalizedS = normalizedS.replace(',','.')
                        score = score.replace(',','.')   
                        limited = df.iloc[0]['Limited']

                        try:
                            inactiveLinks = df.iloc[0]['Inactive links']
                        except:
                            inactiveLinks = '-'

                        idForTxt = newFilename
                        nameForTxt = name

                        try:
                            urisDef = df.iloc[0]['URIs Deferenceability']
                        except:
                            urisDef = '-' 

                        writer.writerow([filename,endpoint,dump,licenseMRM,licenseHR,name,description,url,provList,trustValue,dC,ccl,centrlity,sameAs,numTriples,newFilename,minL,percentile25L,medianL,percentile75L,maxL,
                                        minT,percentile25T,medianT,percentile75T,maxT,auth,https,formats,languages,linkSparql,linkDump,voidLabel,whitespaceLabel,datatypeProblem,labels,numDisjoint,undefClass,undefProp,deprecated,hijacking,misplacedP,misplacedC,
                                        pagerank,vocabularies,author,publisher,contributor,sources,signed,frequency,creationDate,modificationDate,triplesUpdated,lastModification,exC,intC,interCompl,numTriplesLinked,numEntities,numProperty,
                                        minLS,percentile25LS,medianLS,percentile75LS,maxLS,minLP,percentile25LP,medianLP,percentile75LP,maxLP,minLO,percentile25LO,medianLO,percentile75LO,maxLO,newVocabs,newTerms,numLabel,regexUri,example,blankNodes,rdfS,historicalUp,score,normalizedS,FPvalue,IFPvalue,limited,licenseMRQ,inactiveLinks,urisDef])
                #USED TO NOT LOAD ALL CSV IN THE JS VISUALIZATION
                idname = idForTxt + ' ' + nameForTxt + ' ' + normalizedS
                idNameLi.append(idname)


        #STORE THE TXT FILE WITH THE ID OF KNOWLEDGE GRAPH ANALYZED (FOR JS)
        save_path = os.path.join(here,'./docs')
        completeName = os.path.join(save_path, "KGid.txt")
        fileNames.sort()
        with open(completeName,'w', encoding="utf-8") as f:
            for idname in idNameLi:
                f.write(idname)
                f.write('\n')
    
        try:
            utils.enableNewData()
        except:
            pass
'''
    def pushCSV():
        here = os.path.dirname(os.path.abspath(__file__))
        csvJS = os.path.join(here,'./Graphs Visualization JS/CSVforJS')
        p = Path(csvJS)
        files = list(p.glob('*.csv'))
        headers =  {'Authorization' : 'token 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'}

        for file in files:
            filename = str(file.stem)
            save_path = os.path.join(here,'./Graphs Visualization JS/CSVforJS')
            save_path = os.path.join(save_path, filename+".csv")    
            fullName = filename + '.csv'
            
            r = requests.get('https://api.github.com/repos/GabrieleT0/KG-Quality-analysis-visualization/contents/CSVforJS/%s'%fullName,headers=headers)
            result = r.json()
            sha = result.get('sha')

            data = {'message': 'committing file', 'sha': sha, 'branch': 'main'}
            try:
                r = requests.delete('https://api.github.com/repos/GabrieleT0/KG-Quality-analysis-visualization/contents/CSVforJS/%s'%fullName,headers=headers,json=data)
                print(r.status_code)
                print(r.json())
                print("%s DELETED"%filename)
            except Exception as e:
                print("%s ERROR %s"%(filename,e))

        for file in files:
            filename = str(file.stem)
            save_path = os.path.join(here,'./Graphs Visualization JS/CSVforJS')
            save_path = os.path.join(save_path, filename+".csv")    
            fullName = filename + '.csv'
            with open(save_path,'rb') as csv:
                content = str(base64.b64encode(csv.read()), encoding='utf8')
                data = {'message': 'committing file', 'content': content}
                try:
                    r = requests.put('https://api.github.com/repos/GabrieleT0/KG-Quality-analysis-visualization/contents/CSVforJS/%s'%fullName,headers=headers,json=data)
                    print(r.status_code)
                    print(r.json())
                    print("%s CREATED"%filename)
                except Exception as e:
                    print("%s ERROR %s"%(filename,e))
    
    def pushKGid():
        here = os.path.dirname(os.path.abspath(__file__))
        save_path = os.path.join(here,'./Graphs Visualization JS')
        save_path = os.path.join(save_path,'KGid.txt')
        headers =  {'Authorization' : 'token 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'}
        r = requests.get('https://api.github.com/repos/GabrieleT0/KG-Quality-analysis-visualization/contents/KGid.txt',headers=headers)
        result = r.json()
        sha = result.get('sha')
        
        
        data = {'message': 'committing file','sha': sha, 'branch': 'main'}
        try:
            r = requests.delete('https://api.github.com/repos/GabrieleT0/KG-Quality-analysis-visualization/contents/KGid.txt',headers=headers,json=data)
            print(r.status_code)
            print(r.json())
            print("KGid.txt DELETED")
        except Exception as e:
            print("KGid.txt ERROR %s"%e)
        
        with open(save_path,'rb') as f:
            content = str(base64.b64encode(f.read()), encoding='utf8')
            data = {'message': 'committing file', 'content': content}
            try:
                r = requests.put('https://api.github.com/repos/GabrieleT0/KG-Quality-analysis-visualization/contents/KGid.txt',headers=headers,json=data)
                print(r.status_code)
                print(r.json())
                print("KGid.txt CREATED")
            except Exception as e:
                print("KGid.txt DELETED %s"%e)
'''

