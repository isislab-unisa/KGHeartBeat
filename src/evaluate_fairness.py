import pandas as pd
import utils 
from API import Aggregator
import json
from QualityDimensions.FAIRness import FAIRness

class EvaluateFAIRness:

    def __init__(self, kg_quality):
        self.kg_quality = kg_quality
        self.fairness = FAIRness ()
            
    def evaluate_findability(self):
        
        available_on_search_engine = Aggregator.check_if_on_lodc_dh(self.kg_quality.extra.KGid)
        if available_on_search_engine: # For those not manually picked, the data are in the LOD Cloud for sure
            self.fairness.f1M = 1
        else:
            doi_indication = Aggregator.getDOI(self.kg_quality.extra.KGid)
            if doi_indication != False:
                self.fairness.f1M = 1
            else:
                self.fairness.f1M = 0
                    
        try:
            uriDef = float(self.kg_quality.availability.uriDef)
            self.fairness.f1D = uriDef
        except ValueError:
            self.fairness.f1D = 0

        if available_on_search_engine:
            self.fairness.f2aM = 1
        else:
            sparql_indication = lambda: 1 if self.kg_quality.extra.endpointUrl != '' else 0
            void_indication = lambda: 1 if self.kg_quality.extra.urlVoid != '' else 0
            self.fairness.f2aM = lambda: 1 if sparql_indication == 1 or void_indication == 1 else 0

        
        sparql_indication = lambda: 1 if self.kg_quality.extra.endpointUrl != '' else 0 
        doi_indication = lambda: 1 if Aggregator.getDOI(self.kg_quality.extra.KGid) != False else 0
        dump_indication = lambda: 1 if self.kg_quality.availability.RDFDumpM in [1,"1"] else 0
        verifiability_info = utils.check_publisher_info(self.kg_quality)
        mediatype_indication = 1 if len(self.kg_quality.extra.metadataMediaType) > 0 else 0
        license = 1 if (self.kg_quality.licensing.licenseMetadata not in [False, 'False','','-','[]']) or (self.kg_quality.licensing.licenseQuery != '-' and len(self.kg_quality.licensing.licenseQuery) > 0) else 0
        vocabs = 1 if self.kg_quality.verifiability.vocabularies not in ['-','','[]'] and len(self.kg_quality.verifiability.vocabularies) > 0 else 0
        if available_on_search_engine:
            links = 1 if (self.kg_quality.interlinking.degreeConnection != '-' and int(self.kg_quality.interlinking.degreeConnection) > 0) else 0
        else:
            links = 1 if (self.kg_quality.interlinking.sameAs not in ['-','0',''] and int(self.kg_quality.interlinking.sameAs) > 0) or (self.kg_quality.interlinking.skosMapping not in ['-','0',''] and int(self.kg_quality.interlinking.skosMapping) > 0) else 0
        void_indication = lambda: 1 if self.kg_quality.extra.urlVoid != '' else 0

        self.fairness.f2bM = ((sparql_indication + doi_indication + dump_indication + verifiability_info + mediatype_indication + license + vocabs + links + void_indication) / 9).round(2)

        self.fairness.f3M = lambda: 1 if Aggregator.getDOI(self.kg_quality.extra.KGid) != False else 0

        if available_on_search_engine:
            self.fairness.f4M = 1
        else:
            self.fairness.f4M = utils.find_search_engine_from_keywords(self.kg_quality.extra.KGid)
        
        self.fairness.f_score = ((self.fairness.f1M + self.fairness.f1D + self.fairness.f2aM + self.fairness.f2bM + self.fairness.f3M + self.fairness.f4M) / 6).round(2)

        print("Findability evaluation completed!")


    def evaluate_availability(self):

        sparql_availability = self.quality_data["Sparql endpoint"].apply(lambda x: 1 if x == 'Available' else 0)
        dump_availability = self.quality_data["Availability of RDF dump (metadata)"].apply(lambda x: 1 if x in [1,"1"] else 0) # No consideration about the mediatype of the available dummp
        self.fairness_evaluation["A1-D Working access point(s)"] = (
            (sparql_availability == 1) | (dump_availability == 1)
        ).astype(int)


        if self.manually_picked:
            sparql_metadata = self.quality_data["SPARQL endpoint URL"].apply(utils.check_meta_in_sparql)
            void_availability = self.quality_data["Availability VoID file"].apply(lambda x: 1 if x == 'VoID file available' else 0)
            self.fairness_evaluation["A1-M Metadata availability via working primary sources"].apply(lambda x: 1 if sparql_metadata == 1 or void_availability == 1 else 0)
        else:
            self.fairness_evaluation["A1-M Metadata availability via working primary sources"] = 1

        
        self.fairness_evaluation["A1.2 Authentication & HTTPS support"] = self.quality_data.apply(
            lambda row: (0 if row["Use HTTPS"] in [False, 'False'] and 'https' in row['SPARQL endpoint URL'] else 1)  +  (1 if row["Requires authentication"] in ["False", False, True, 'True'] else 0) / 2,
            axis=1) 

        if not self.manually_picked:
            self.fairness_evaluation["A2-M Registered in search engines"] = 1
        else:
            self.fairness_evaluation["A2-M Registered in search engines"] = self.quality_data.apply(utils.find_search_engine_from_keywords,axis=1)
        
        self.fairness_evaluation["A score"] = (self.fairness_evaluation[["A1-D Working access point(s)", "A1-M Metadata availability via working primary sources", "A1.2 Authentication & HTTPS support", "A2-M Registered in search engines"]].sum(axis=1) / 4).round(2)
        print("Availability evaluation completed!")
    
    def evaluate_reusability(self):

        self.fairness_evaluation['R1.1 Machine- or human-readable license retrievable via any primary source'] = self.quality_data.apply(
            lambda row: 1 if (
                pd.notna(row['License machine redeable (metadata)']) and row['License machine redeable (metadata)'] not in ['-', '']
            ) or (
                pd.notna(row['License machine redeable (query)']) and row['License machine redeable (query)'] not in ['-', '']
            ) or (
                row['License human redeable'] in [True, 'True']
            ) else 0,
            axis=1
        )

        self.fairness_evaluation['R1.2 Publisher information, such as authors, contributors, publishers, and sources'] = self.quality_data.apply(utils.check_publisher_info,axis=1)
        
        # If the media type is is standard and open (SW standard), in this community also this format is common accepted. If not, we have to check if the data are in a standard format only for the community
        self.fairness_evaluation['R1.3-D Data organized in a standardized way'] = self.quality_data.apply(
            lambda row: 1 if row['Availability of a common accepted Media Type'] in ['True', True] 
            else (1 if 'api/sparql' or 'rdf' in row['metadata-media-type'] else row['metadata-media-type']),
            axis=1
        )

        self.fairness_evaluation['R1.3-M Metadata are described with VoID/DCAT predicates'] = self.quality_data['License machine redeable (query)'].apply(lambda x: 1 if x not in ['-',''] and pd.notna(x) else 0)

        self.fairness_evaluation["R score"] = (self.fairness_evaluation[["R1.1 Machine- or human-readable license retrievable via any primary source", "R1.2 Publisher information, such as authors, contributors, publishers, and sources", "R1.3-D Data organized in a standardized way", "R1.3-M Metadata are described with VoID/DCAT predicates"]].sum(axis=1) / 4).round(2)

        print("Reusability evaluation completed!")

    def evaluate_interoperability(self):

        self.fairness_evaluation['I1-D Standard & open representation format'] = self.quality_data.apply(
            lambda row: 1 if row['Availability of a common accepted Media Type'] in ['True', True] 
            else (1 if 'api/sparql' or 'rdf' in row['metadata-media-type'].lower() else 0),
            axis=1
        )

        self.fairness_evaluation['I1-M Metadata are described with VoID/DCAT predicates'] = self.quality_data['License machine redeable (query)'].apply(lambda x: 1 if x not in ['-',''] and pd.notna(x) else 0)

        self.fairness_evaluation['I2 Use of FAIR vocabularies'] = self.quality_data['Vocabularies'].apply(utils.check_if_fair_vocabs)

        if not self.manually_picked:
            self.fairness_evaluation['I3-D Degree of connection'] = self.quality_data['Degree of connection'].apply(lambda x: 1 if (x != '-' and pd.notna(x) and int(x) > 0 ) else 0)
        else:
            self.fairness_evaluation['I3-D Degree of connection'] = self.quality_data.apply(
                lambda row: 1 if row['Number of samAs chains'] not in ['-', 0,'0'] and pd.notna(row['Number of samAs chains'])
                else (1 if row['SKOS mapping properties'] not in ['-', 0,'0'] and pd.notna(row['SKOS mapping properties']) else 0),
                axis=1
            )

        self.fairness_evaluation['I score'] = (self.fairness_evaluation[["I1-D Standard & open representation format", "I1-M Metadata are described with VoID/DCAT predicates", "I2 Use of FAIR vocabularies", "I3-D Degree of connection"]].sum(axis=1).round(2) / 4).round(2)
        print("Interoperability evaluation completed!")

    def calculate_FAIR_score(self):
        self.fairness_evaluation["FAIR score"] = self.fairness_evaluation[["F score", "A score", "I score", "R score"]].sum(axis=1).round(2)

    def initialize_output_file(self):
        output_df = pd.DataFrame({
            "KG id": self.quality_data["KG id"],             
            "KG name": self.quality_data["KG name"], 
            "KG SPARQL endpoint": self.quality_data['KG id'].apply(utils.get_sparql_url),
            "RDF dump link" : self.quality_data["URL for download the dataset"],
            "Ontology": self.quality_data['KG id'].apply(utils.check_if_ontology)
        })

        return output_df

    def save_file(self):
        self.fairness_evaluation.to_csv(self.output_file_path,index=False)

fairness = EvaluateFAIRness('../data/quality_data/LOD-Cloud_no_refined.csv','../data/fairness_evaluation/CHe-Cloud_no_refined.csv')
fairness.evaluate_findability()
fairness.evaluate_availability()
fairness.evaluate_interoperability()
fairness.evaluate_reusability()
fairness.calculate_FAIR_score()
fairness.save_file()