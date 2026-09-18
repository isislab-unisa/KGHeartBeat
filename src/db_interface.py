from datetime import date
from ExternalLink import ExternalLink
import utils
import os
from dotenv import load_dotenv

useDB = False
try: 
    import pymongo
    load_dotenv()
    DB_CONNECTION_STRING = os.getenv("MONGO_DB_CONNECTION_STRING")
except:
    DB_CONNECTION_STRING = ''

class DBinterface():
    def __init__(self):
        self.client = pymongo.MongoClient(DB_CONNECTION_STRING)
        self.db = self.client["KGHeartbeatDB"]
        self.collection = self.db['quality_analysis_data'] 
    
    def insert_quality_data(self,kg_quality,score):
        today_date = date.today()
        today_date_str = today_date.strftime("%Y-%m-%d")

        filter_query = {'kg_id' : kg_quality.extra.KGid}
        results = self.collection.find(filter_query).sort("analysis_date",pymongo.DESCENDING)
        try:
            most_recent_document = results[0]
        except:
            most_recent_document = None

        #This is done for performance reason, we only store in the most recent analysis all the triples for a specific quality metric, in the old analysis we save only the number 
        #This is necessary to avoid inserting or deleting unnecessary values if they were not available during the last analysis
        if(most_recent_document is not None):
            #void_status = most_recent_document['Accessibility'][0]['Availability']["voidAvailability"]
            sparql_status = most_recent_document['Accessibility'][0]['Availability']["sparqlEndpoint"]
            if most_recent_document and (sparql_status == 'Available'): #or void_status == 'VoID file available'):
                old_uri_regex = utils.to_list(most_recent_document['Representational'][2]['Understandability']['regexUri'])
                old_serializationFormats = utils.to_list(most_recent_document['Representational'][4]['Versatility']['serializationFormats'])
                old_publishers = utils.to_list(most_recent_document['Trust'][2]['Verifiability']['publisher'])
                old_new_vocabs = utils.to_list(most_recent_document['Representational'][1]['Representational-consistency']['newVocab'])
                old_new_terms = utils.to_list(most_recent_document['Representational'][1]['Representational-consistency']['useNewTerms'])
                old_license_q = utils.to_list(most_recent_document['Accessibility'][1]['Licensing']['licenseQuery'])
                old_vocabs = utils.to_list(most_recent_document['Trust'][2]['Verifiability']['vocabularies'])
                old_vocabs2 = utils.to_list(most_recent_document['Representational'][2]['Understandability']['vocabularies'])
                old_history = utils.to_list(most_recent_document['Dataset dynamicity'][0]['Currency']['historicalUp'])
                
                #needed to grant compatibility for the splitted csv
                try: 
                    newvalues = { "$set": {
                    'Representational.2.Understandability.regexUri': len(old_uri_regex) if len(old_uri_regex) > 1 else most_recent_document['Representational'][2]['Understandability']['regexUri'],
                    'Representational.4.Versatility.serializationFormats': len(old_serializationFormats) if len(old_serializationFormats) > 1 else most_recent_document['Representational'][4]['Versatility']['serializationFormats'],
                    'Trust.2.Verifiability.publisher':  len(old_publishers) if len(old_publishers) > 1 else most_recent_document['Trust'][2]['Verifiability']['publisher'],
                    'Representational.1.Representational-consistency.newVocab' : len(old_new_vocabs) if len(old_new_vocabs) > 1 else most_recent_document['Representational'][1]['Representational-consistency']['newVocab'],
                    'Representational.1.Representational-consistency.useNewTerms' : len(old_new_terms) if len(old_new_terms) > 1 else most_recent_document['Representational'][1]['Representational-consistency']['old_new_terms'],
                    'Accessibility.1.Licensing.licenseQuery' : len(old_license_q) if len(old_license_q) > 1 else most_recent_document['Accessibility'][1]['Licensing']['licenseQuery'],
                    'Trust.2.Verifiability.vocabularies' : len(old_vocabs) if len(old_vocabs) > 1 else most_recent_document['Trust'][2]['Verifiability']['vocabularies'],
                    'Dataset dynamicity.0.Currency.historicalUp' : len(old_history) if len(old_history) > 1 else most_recent_document['Dataset dynamicity'][0]['Currency']['historicalUp'],
                    'Representational.2.Understandability.vocabularies' : len(old_vocabs2) if len(old_vocabs2) > 1 else most_recent_document['Representational'][2]['Understandability']['vocabularies']

                    }}

                    self.collection.update_one({'kg_id' : kg_quality.extra.KGid, 'analysis_date' : most_recent_document['analysis_date']}, newvalues)
                except KeyError:
                    pass
                except Exception as e:
                    pass



        availability_dict = kg_quality.availability.__dict__
        availability_dict['voidAvailability'] = kg_quality.extra.voidAvailability

        obj_to_store = {
            "kg_id" : kg_quality.extra.KGid,
            "kg_name": kg_quality.believability.title,
            "dataset_source": getattr(kg_quality.extra, 'datasetSource', 'unknown'),
            "analysis_date" : today_date_str,
            "Accessibility": [{"Availability" : availability_dict},{"Licensing" : kg_quality.licensing.__dict__}, {"Interlinking" :kg_quality.interlinking.to_dict()}, 
                              {"Security" : kg_quality.security.__dict__}, {"Performance" : kg_quality.performance.__dict__}],
            "Intrinsic": [{"Accuracy" : kg_quality.accuracy.__dict__}, {"Consistency" : kg_quality.consistency.__dict__}, {"Conciseness" : kg_quality.conciseness.__dict__}],
            "Trust": [{"Reputation" : kg_quality.reputation.to_dict()}, {"Believability" : kg_quality.believability.__dict__}, {"Verifiability" : kg_quality.verifiability.to_dict()}],
            "Dataset dynamicity" : [{"Currency" : kg_quality.currency.to_dict()}, {"Volatility" : kg_quality.volatility.to_dict()}],
            "Contextual": [{"Completeness" : kg_quality.completeness.__dict__}, {"Amount of data" : kg_quality.amountOfData.__dict__}],
            "Representational" : [{"Representational-conciseness" : kg_quality.rConciseness.__dict__}, {"Representational-consistency" : kg_quality.rConsistency.__dict__}, {"Understandability" : kg_quality.understendability.__dict__}, 
                                  {"Interpretability" : kg_quality.interpretability.__dict__}, {"Versatility" : kg_quality.versatility.__dict__}],
            "Score": {"dimensionNumber" : score.dimensionNumber, "totalScore" : score.totalScore, "normalizedScore" : score.normalizedScore, "availabilityScoreValue" : score.availabilityScoreValue,
                        "licensingScoreValue" : score.licensingScoreValue , "interlinkingScoreValue" : score.interlinkingScoreValue, "performanceScoreValue" : score.performanceScoreValue, "accuracyScoreValue" : score.accuracyScoreValue,
                        "consistencyScoreValue" : score.consistencyScoreValue, "concisenessScoreValue" : score.concisenessScoreValue, "verifiabilityScoreValue" : score.verifiabilityScoreValue,  "reputationScoreValue" : score.reputationScoreValue, 
                        "believabilityScoreValue" : score.believabilityScoreValue, "currencyScoreValue" : score.currencyScoreValue, "volatilityScoreValue" : score.volatilityScoreValue, "completenessScoreValue": score.completenessScoreValue,
                "amountScoreValue" : score.amountScoreValue , "repConsScoreValue" : score.repConsScoreValue, "repConcScoreValue" : score.repConcScoreValue, "understScoreValue" : score.understScoreValue,
                "interpretabilityScoreValue" : score.interpretabilityScoreValue, "versatilityScoreValue" : score.versatilityScoreValue, "securityScoreValue" : score.securityScoreValue },
            "Extra":{"sparql_link" : kg_quality.extra.endpointUrl,"rdf_dump_link" : kg_quality.extra.downloadUrl, "external_links": ExternalLink.getListExLinks(kg_quality.interlinking.externalLinks)}
        }

        try:
            print(obj_to_store)
            result = self.collection.insert_one(obj_to_store)
            self.client.close()
            return result
        except:
            self.client.close()
            return
