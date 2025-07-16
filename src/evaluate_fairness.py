import pandas as pd
import utils 
from API import Aggregator
import json
from QualityDimensions.FAIRness import FAIRness
import query

class EvaluateFAIRness:

    def __init__(self, kg_quality):
        self.kg_quality = kg_quality
        self.fairness = FAIRness()
            
    def evaluate_findability(self):
        available_on_search_engine = Aggregator.check_if_on_lodc_dh(self.kg_quality.extra.KGid)
        
        doi_indication = 1 if Aggregator.getDOI(self.kg_quality.extra.KGid) != False else 0

        self.fairness.f1M = 1 if available_on_search_engine or doi_indication else 0

        try:
            uriDef = float(self.kg_quality.availability.uriDef)
            self.fairness.f1D = uriDef
        except ValueError:
            self.fairness.f1D = 0

        sparql_indication = 1 if self.kg_quality.extra.endpointUrl != '' else 0
        void_indication = 1 if self.kg_quality.extra.urlVoid != '' else 0
        self.fairness.f2aM = 1 if sparql_indication or void_indication else 0

        dump_indication = 1 if self.kg_quality.availability.RDFDumpM in [1, "1"] else 0
        verifiability_info = utils.check_publisher_info(self.kg_quality)
        mediatype_indication = 1 if len(self.kg_quality.extra.metadataMediaType) > 0 else 0
        license = 1 if (self.kg_quality.licensing.licenseMetadata not in [False, 'False', '', '-', '[]']) or (self.kg_quality.licensing.licenseQuery != '-' and len(self.kg_quality.licensing.licenseQuery) > 0) else 0
        vocabs = 1 if self.kg_quality.verifiability.vocabularies not in ['-', '', '[]'] and len(self.kg_quality.verifiability.vocabularies) > 0 else 0

        if available_on_search_engine:
            links = 1 if (self.kg_quality.interlinking.degreeConnection != '-' and isinstance(self.kg_quality.interlinking.degreeConnection,int) and int(self.kg_quality.interlinking.degreeConnection) > 0) else 0
        else:
            links = 1 if (
                (self.kg_quality.interlinking.sameAs not in ['-', '0', ''] and int(self.kg_quality.interlinking.sameAs) > 0) or
                (self.kg_quality.interlinking.skosMapping not in ['-', '0', ''] and int(self.kg_quality.interlinking.skosMapping) > 0)
            ) else 0

        self.fairness.f2bM = round((sparql_indication + doi_indication + dump_indication + verifiability_info + mediatype_indication + license + vocabs + links + void_indication) / 9, 2)

        self.fairness.f3M = doi_indication

        self.fairness.f4M = 1 if available_on_search_engine else utils.find_search_engine_from_keywords(self.kg_quality.extra.KGid)

        self.fairness.f_score = round((self.fairness.f1M + self.fairness.f1D + self.fairness.f2aM + self.fairness.f2bM + self.fairness.f3M + self.fairness.f4M) / 6, 2)

        print("Findability evaluation completed!")

    def evaluate_availability(self):
        sparql_availability = 1 if self.kg_quality.availability.sparqlEndpoint == 'Available' else 0
        dump_availability = 1 if self.kg_quality.availability.RDFDumpM in [1, "1"] else 0
        sparql_or_dump = 1 if sparql_availability == 1 or dump_availability == 1 else 0
        sparql_on_not_interop = utils.check_at_least_sparql_on(self.kg_quality.extra.endpointUrl)

        self.fairness.a1D = 1 if sparql_or_dump == 1 else 0.5 if sparql_or_dump == 0 and sparql_on_not_interop == 1 else 0

        available_on_search_engine = Aggregator.check_if_on_lodc_dh(self.kg_quality.extra.KGid)
        
        if available_on_search_engine:
            self.fairness.a1M = 1
        else:
            void_availability = 1 if self.kg_quality.extra.voidAvailability == 'VoID file available' else 0
            self.fairness.a1M = 1 if sparql_availability == 1 or void_availability == 1 else 0

        uses_https = 1 if self.kg_quality.security.useHTTPS in [True, 'True'] or self.kg_quality.availability.sparqlEndpoint == 'Available' else 0
        no_auth_required = 1 if self.kg_quality.security.requiresAuth in ["False", False, 'True', True] else 0

        self.fairness.a1_2 = round((uses_https + no_auth_required) / 2, 2)

        self.fairness.a2M = 1 if available_on_search_engine else utils.find_search_engine_from_keywords(self.kg_quality.extra.KGid)

        self.fairness.a_score = round((self.fairness.a1D + self.fairness.a1M + self.fairness.a1_2 + self.fairness.a2M) / 4, 2)

        print("Availability evaluation completed!")
    
    def evaluate_reusability(self):

        has_license_metadata = 1 if self.kg_quality.licensing.licenseMetadata not in [False, 'False', '', '-', '[]'] else 0
        has_license_query = 1 if self.kg_quality.licensing.licenseQuery != '-' and len(self.kg_quality.licensing.licenseQuery) > 0 else 0
        has_license_hr = 1 if self.kg_quality.licensing.licenseHR != '-' and self.kg_quality.licensing.licenseHR == True else 0
        self.fairness.r1_1 = 1 if has_license_metadata or has_license_query or has_license_hr else 0

        self.fairness.r1_2 = utils.check_publisher_info(self.kg_quality)

        common_media_type = self.kg_quality.extra.commonMediaType in ['True', True]
        known_semantic_format = any(fmt in self.kg_quality.extra.metadataMediaType for fmt in ['api/sparql', 'rdf', 'RDF'])
        self.fairness.r1_3D = 1 if common_media_type or known_semantic_format else 0

        has_void = self.kg_quality.extra.urlVoid != ''
        has_void_from_endpoint = query.check_void_dcat(self.kg_quality.extra.endpointUrl) != False
        lic_in_meta = 1 if self.kg_quality.licensing.licenseQuery != '-' and len(self.kg_quality.licensing.licenseQuery) > 0 else 0
        self.fairness.r1_3M = 1 if has_void or has_void_from_endpoint or lic_in_meta else 0

        self.fairness.r_score = round((self.fairness.r1_1 + self.fairness.r1_2 + self.fairness.r1_3D + self.fairness.r1_3M) / 4, 2)

        print("Reusability evaluation completed!")

    def evaluate_interoperability(self):
        available_on_search_engine = Aggregator.check_if_on_lodc_dh(self.kg_quality.extra.KGid)

        common_media_type = 1 if self.kg_quality.extra.commonMediaType in ['True', True] else 0
        known_semantic_format = any(fmt in self.kg_quality.extra.metadataMediaType for fmt in ['api/sparql', 'rdf', 'RDF'])
        self.fairness.i1D = 1 if common_media_type or known_semantic_format else 0

        has_void = self.kg_quality.extra.urlVoid != ''
        has_void_from_endpoint = query.check_void_dcat(self.kg_quality.extra.endpointUrl) != False
        lic_in_meta = 1 if self.kg_quality.licensing.licenseQuery != '-' and len(self.kg_quality.licensing.licenseQuery) > 0 else 0
        self.fairness.i1M = 1 if has_void or has_void_from_endpoint else 0

        has_vocab = self.kg_quality.verifiability.vocabularies not in ['-', '', '[]'] and len(self.kg_quality.verifiability.vocabularies) > 0
        self.fairness.i2 = utils.check_if_fair_vocabs(self.kg_quality.verifiability.vocabularies) if has_vocab else 0

        if available_on_search_engine:
            try:
                self.fairness.i3D = 1 if self.kg_quality.interlinking.degreeConnection not in ['-', '', '0'] and int(self.kg_quality.interlinking.degreeConnection) > 0 else 0
            except TypeError:
                self.fairness.i3D = 0
        else:
            sameAs_valid = self.kg_quality.interlinking.sameAs not in ['-', '0', ''] and int(self.kg_quality.interlinking.sameAs) > 0
            skos_valid = self.kg_quality.interlinking.skosMapping not in ['-', '0', ''] and int(self.kg_quality.interlinking.skosMapping) > 0
            self.fairness.i3D = 1 if sameAs_valid or skos_valid else 0

        self.fairness.i_score = round((self.fairness.i1D + self.fairness.i1M + self.fairness.i2 + self.fairness.i3D) / 4, 2)

        print("Interoperability evaluation completed!")

    def calculate_FAIR_score(self):
        self.fairness.fair_score = round(
            float(self.fairness.f_score) + 
            float(self.fairness.a_score) + 
            float(self.fairness.i_score) + 
            float(self.fairness.r_score), 
            2
        )
