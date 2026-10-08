from API import Aggregator
from QualityDimensions.Accessibility4All import Accessibility4All
from QualityDimensions.Accessibility4VisuallyImpaired import Accessibility4VisuallyImpaired
from QualityDimensions.DeafHearingAccessibility import DeafHearingAccessibility
import utils
import query

class EvaluateHumanCenteredAcc:
    
    def __init__(self, kg_quality):
        self.kg_quality = kg_quality
        self.query_endpoint = getattr(kg_quality.extra, 'queryEndpointUrl', kg_quality.extra.endpointUrl)
        self.data_available = (kg_quality.availability.sparqlEndpoint == 'Available'
                               or (getattr(kg_quality.extra, 'analysisSource', None) == 'rdf_dump'
                                   and bool(self.query_endpoint)))
        self.accessibility4all = Accessibility4All()
        self.accessibility4visuallyimpaired = Accessibility4VisuallyImpaired()
        self.deaf_hearing_accessibility = DeafHearingAccessibility()
        self.search_engine_metadata = self.recover_search_engine_metadata(kg_quality.extra.KGid)
        self.total_resources_in_kg = utils.run_with_timeout(query.fetch_subjects,args=(self.query_endpoint,), timeout=1800)


    def recover_search_engine_metadata(self, kg_identifier):
        metadata = Aggregator.getDataPackage(kg_identifier)
        if metadata == False:
            print(f"Metadata not found for {kg_identifier}")
            
            return False
        return metadata
        
    def evaluate_perceivable(self):
        sparql_endpoint = self.query_endpoint
        void_file_url = self.kg_quality.extra.urlVoid
        resourcesDH = self.kg_quality.extra.other_resources

        image_metadata = self.deaf_hearing_accessibility.image_metadata(sparql_endpoint,void_file_url,resourcesDH)
        
        image = self.accessibility4all.image(sparql_endpoint,self.total_resources_in_kg)
        
        audio_metadata = self.accessibility4visuallyimpaired.audio_meta(sparql_endpoint,void_file_url,resourcesDH)
        
        audio = self.accessibility4visuallyimpaired.audio(sparql_endpoint,self.total_resources_in_kg)

        video_metadata = self.deaf_hearing_accessibility.video_meta(sparql_endpoint,void_file_url,resourcesDH)  

        video = self.deaf_hearing_accessibility.video(sparql_endpoint,self.total_resources_in_kg)

        perceivable_scores_sum = (image_metadata[0] + image[0] + audio_metadata[0] + audio[0] + video_metadata[0] + video[0])

        perceivable_score = perceivable_scores_sum / 6

        return {    
            "image_metadata": {
                "score": image_metadata[0],
                "details": image_metadata[1]},
            "image": {
                "score": image[0],
                "details": image[1]},
            "audio_metadata": {
                "score": audio_metadata[0],
                "details": audio_metadata[1]},
            "audio": {
                "score": audio[0],
                "details": audio[1]},
            "video_metadata": {
                "score": video_metadata[0],
                "details": video_metadata[1]},
            "video": {
                "score": video[0],
                "details": video[1]},
            "perceivable_score" : perceivable_score
        }

    def evaluate_understandable(self):
        sparql_endpoint = self.query_endpoint
        void_file_url = self.kg_quality.extra.urlVoid

        data_lang = self.kg_quality.versatility.languagesQ
        if isinstance(data_lang, list) and len(data_lang) > 0:
            data_lang_score = (1, f"Languages available: {data_lang}")
        elif data_lang == 0:
            data_lang_score = (0, "No language specified")
        elif not self.data_available:
            data_lang_score = (0, "No SPARQL endpoint available")
        else:
            data_lang_score = (0, "Error fetching languages")
        
        metadata_lang = self.accessibility4all.metadata_lang(self.query_endpoint, self.kg_quality.extra.urlVoid)

        if self.data_available:
            labels = self.kg_quality.understendability.numLabel
            if isinstance(labels, int) and labels > 0 and isinstance(self.total_resources_in_kg, int) and self.total_resources_in_kg > 0:
                human_readable_labels_score = ((labels / self.total_resources_in_kg), f"Number of human-readable labels: {labels}")
            elif isinstance(labels, int) and labels == 0:
                human_readable_labels_score = (0, "No human-readable labels found")
            elif isinstance(labels, int):
                human_readable_labels_score = (0, f"Number of human-readable labels: {labels}")
            else:
                human_readable_labels_score = (0, "Error fetching human-readable labels")
        else:
            human_readable_labels_score = (0, "No SPARQL endpoint available")
        
        examples = self.accessibility4all.examples(self.kg_quality.extra.urlVoid, self.query_endpoint, self.search_engine_metadata)

        description_readability = self.accessibility4all.description_readability(sparql_endpoint, void_file_url, Aggregator.getDescription(self.search_engine_metadata))

        understandable_sum = (data_lang_score[0] + metadata_lang[0] + human_readable_labels_score[0] + examples[0] + description_readability[0])

        understandable_score = understandable_sum / 5


        return {
            "metadata_language": {
                "score": metadata_lang[0],
                "details": metadata_lang[1]},
            "data_language": {
                "score": data_lang_score[0],
                "details": data_lang_score[1]},
            "human_readable_labels": {
                "score": human_readable_labels_score[0],
                "details": human_readable_labels_score[1]},
            "examples": { 
                "score": examples[0],
                "details": examples[1]},
            "description_readability": {
                "score": description_readability[0],
                "details": description_readability[1]},
            "understandable_score": understandable_score
        }


    def evaluate_operable(self):
        status_sparql_endpoint = self.kg_quality.availability.sparqlEndpoint
        status_dump1 = self.kg_quality.availability.RDFDumpM
        status_dum2 = self.kg_quality.availability.RDFDumpQ

        contact_person = self.accessibility4all.contact_point(self.search_engine_metadata, self.query_endpoint, self.kg_quality.extra.urlVoid)
        dump_size = self.accessibility4all.dump_size(self.kg_quality.extra.urlVoid, self.query_endpoint, self.kg_quality.extra.KGid)
        
        if status_sparql_endpoint == 'Available':
            auth = (1, f"SPARQL endpoint status: {status_sparql_endpoint}")
        else:
            auth = (0, f"SPARQL endpoint status: {status_sparql_endpoint}")

        dump_format = self.kg_quality.extra.commonMediaType
        if dump_format == True:
            dump_format_score = (1, "Common formats available")
        elif dump_format == False and (status_dump1 == 1 or status_dum2 == True):
            dump_format_score = (0.5, "Dump available but no common formats found")
        else:
            dump_format_score = (0, "No dump provided for the KG")

        licenseMetadata = self.kg_quality.licensing.licenseMetadata
        licenseQuery = self.kg_quality.licensing.licenseQuery
        if licenseMetadata:
            opens_license = self.accessibility4all.open_license(licenseMetadata)
        elif licenseQuery:
            opens_license = self.accessibility4all.open_license(licenseQuery)

        alternative_access_point = self.accessibility4all.alternative_access_point(self.kg_quality.extra.urlVoid, self.kg_quality.extra.endpointUrl, self.kg_quality.extra.KGid)

        operable_sum = (contact_person[0] + dump_size[0] + auth[0] + dump_format_score[0] + opens_license[0] + alternative_access_point[0])
        operable_score = operable_sum / 6

        return {
            "contact_point": {
                "score": contact_person[0],
                "details": contact_person[1]},
            "dump_size": {
                "score": dump_size[0],
                "details": dump_size[1]},
            "authentication": {
                "score": auth[0],
                "details": auth[1]},
            "common_format_availability": {
                "score": dump_format_score[0],
                "details": dump_format_score[1]},
            "open_license": {
                "score": opens_license[0],
                "details": opens_license[1]},
            "alternative_access_point": {
                "score": alternative_access_point[0],
                "details": alternative_access_point[1]},
            "operable_score": operable_score
        }
    
    def evaluate_robust(self):
        versioning = self.accessibility4all.version(self.kg_quality.extra.urlVoid, self.query_endpoint)
        webpage_broken_links = self.accessibility4all.webpage_status(self.search_engine_metadata, self.query_endpoint, self.kg_quality.extra.urlVoid)
        metadata_broken_links_rate = self.accessibility4all.metadata_broken_links_rate(self.search_engine_metadata, self.query_endpoint, self.kg_quality.extra.urlVoid, self.kg_quality.extra.KGid)
        canonical_id = self.accessibility4all.canonical_citation(self.kg_quality.extra.urlVoid, self.query_endpoint, self.search_engine_metadata)

        robust_score = (versioning[0] + webpage_broken_links[0] + metadata_broken_links_rate[0] + canonical_id[0]) / 4

        return {
            "versioning": {
                "score": versioning[0],
                "details": versioning[1]},
            "webpage_broken_links": {
                "score": webpage_broken_links[0],
                "details": webpage_broken_links[1]},
            "metadata_broken_links_rate": {
                "score": metadata_broken_links_rate[0],
                "details": metadata_broken_links_rate[1]},
            "canonical_id": {
                "score": canonical_id[0],
                "details": canonical_id[1]},
            "robust_score": robust_score
        }
    
    def evaluate_access_4_visually_impaired(self):
        sparql_endpoint = self.query_endpoint

        alt_image = self.accessibility4visuallyimpaired.alt_image(sparql_endpoint)
        audio_descriptions = self.deaf_hearing_accessibility.check_audio_description_subtitles(sparql_endpoint)['description_ratio']

        acc_4_4_visually_impaired_score = (alt_image[0] + audio_descriptions[0]) / 2

        return {
            "alt_image": {
                "score": alt_image[0],
                "details": alt_image[1]},
            "audio_descriptions": {
                "score": audio_descriptions[0],
                "details": audio_descriptions[1]},
            "accessibility_for_visually_impaired_score": acc_4_4_visually_impaired_score
        }

    
    def evaluate_access_4_deaf_hearing(self):
        sparql_endpoint = self.query_endpoint
        status_sparql_endpoint = self.kg_quality.availability.sparqlEndpoint

        video_results = self.deaf_hearing_accessibility.check_video_description_subtitles(sparql_endpoint)
        audio_results = self.deaf_hearing_accessibility.check_audio_description_subtitles(sparql_endpoint)

        video_descriptions = video_results['description_ratio']
        sign_lang_video = video_results['sign_language_ratio']
        sign_lang_audio = audio_results['sign_language_ratio']
        captions_video = video_results['subtitle_ratio']
        captions_audio = audio_results['subtitle_ratio']
        transcript_video = video_results['description_ratio']
        transcript_audio = audio_results['description_ratio']

        if self.data_available:
            access_4_deaf_hearing_score = (video_descriptions[0] + sign_lang_video[0] + sign_lang_audio[0] + captions_video[0] + captions_audio[0] + transcript_video[0] + transcript_audio[0]) / 7
        else:
            access_4_deaf_hearing_score = 0

        return {
            "video_descriptions": {
                "score": video_descriptions[0],
                "details": video_descriptions[1]},
            "sign_Lang_video": {
                "score": sign_lang_video[0],
                "details": sign_lang_video[1]},
            "sign_Lang_audio": {
                "score": sign_lang_audio[0],
                "details": sign_lang_audio[1]},
            "captions_video": {
                "score": captions_video[0],
                "details": captions_video[1]},
            "captions_audio": { 
                "score": captions_audio[0],
                "details": captions_audio[1]},
            "transcript_video": {
                "score": transcript_video[0],
                "details": transcript_video[1]},
            "transcript_audio": {  
                "score": transcript_audio[0],
                "details": transcript_audio[1]},
            "accessibility_for_deaf_hearing_score": access_4_deaf_hearing_score
        }
    
    def evaluate_all(self):
        perceivable = self.evaluate_perceivable()
        operable = self.evaluate_operable()
        understandable = self.evaluate_understandable()
        robust = self.evaluate_robust()
        access_4_visually_impaired = self.evaluate_access_4_visually_impaired()
        access_4_deaf_hearing = self.evaluate_access_4_deaf_hearing()

        sum_overall_no_special = (perceivable['perceivable_score'] + operable['operable_score'] + understandable['understandable_score'] + robust['robust_score'] )
        sum_overall_with_special = (perceivable['perceivable_score'] + operable['operable_score'] + understandable['understandable_score'] + robust['robust_score'] + access_4_visually_impaired['accessibility_for_visually_impaired_score'] + access_4_deaf_hearing['accessibility_for_deaf_hearing_score'])
        sum_overall_only_special = (access_4_visually_impaired['accessibility_for_visually_impaired_score'] + access_4_deaf_hearing['accessibility_for_deaf_hearing_score'])

        return {
            "perceivable": perceivable,
            "operable": operable,
            "understandable": understandable,
            "robust": robust,
            "accessibility_for_visually_impaired": access_4_visually_impaired,
            "accessibility_for_deaf_hearing": access_4_deaf_hearing,
            "overall_score_no_special": sum_overall_no_special,
            "overall_score_with_special": sum_overall_with_special,
            "overall_score_only_special": sum_overall_only_special,
            "overall_score_accessibility": (perceivable['perceivable_score'] + operable['operable_score'] + understandable['understandable_score'] + robust['robust_score'] + access_4_visually_impaired['accessibility_for_visually_impaired_score'] + access_4_deaf_hearing['accessibility_for_deaf_hearing_score']) / 6
        }
