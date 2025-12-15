from API import Aggregator
from QualityDimensions.Accessibility4All import Accessibility4All
from QualityDimensions.Accessibility4VisuallyImpaired import Accessibility4VisuallyImpaired
from QualityDimensions.DeafHearingAccessibility import DeafHearingAccessibility
import utils
import query

class EvaluateHumanCenteredAcc:
    
    def __init__(self, kg_quality):
        self.kg_quality = kg_quality
        self.accessibility4all = Accessibility4All()
        self.accessibility4visuallyimpaired = Accessibility4VisuallyImpaired()
        self.deaf_hearing_accessibility = DeafHearingAccessibility()
        self.search_engine_metadata = self.recover_search_engine_metadata(kg_quality.extra.KGid)


    def recover_search_engine_metadata(self, kg_identifier):
        metadata = Aggregator.getDataPackage(kg_identifier)
        if metadata == False:
            print(f"Metadata not found for {kg_identifier}")
            
            return False
        return metadata
        
    def evaluate_perceivable(self):

        status_sparql_endpoint = self.kg_quality.availability.sparqlEndpoint
        sparql_endpoint = self.kg_quality.extra.endpointUrl
        void_file_url = self.kg_quality.extra.urlVoid
        resourcesDH = self.kg_quality.extra.other_resources
        total_resources_in_kg = utils.run_with_timeout(query.fetch_subjects,args=(sparql_endpoint,), timeout=1800)

        image_metadata = self.deaf_hearing_accessibility.image_metadata(sparql_endpoint,void_file_url,resourcesDH)
        
        image = self.accessibility4all.image(sparql_endpoint,total_resources_in_kg)
        
        audio_metadata = self.accessibility4visuallyimpaired.audio_meta(sparql_endpoint,void_file_url,resourcesDH)
        
        audio = self.accessibility4visuallyimpaired.audio(sparql_endpoint,total_resources_in_kg)

        video_metadata = self.deaf_hearing_accessibility.video_meta(sparql_endpoint,void_file_url,resourcesDH)  

        video = self.deaf_hearing_accessibility.video(sparql_endpoint,total_resources_in_kg)

        perceivable_scores_sum = (image_metadata[0] + image[0] + audio_metadata[0] + audio[0] + video_metadata[0] + video[0])
        if status_sparql_endpoint == 'Available':
            perceivable_score = perceivable_scores_sum / 6
        else:
            perceivable_score = perceivable_scores_sum / 3

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
        status_sparql_endpoint = self.kg_quality.availability.sparqlEndpoint
        sparql_endpoint = self.kg_quality.extra.endpointUrl
        void_file_url = self.kg_quality.extra.urlVoid

        data_lang = self.kg_quality.versatility.languagesQ
        if isinstance(data_lang, list) and len(data_lang) > 0:
            data_lang_score = (0, f"Languages available: {data_lang}")
        elif data_lang == 0:
            data_lang_score = (-1, "No language specified")
        elif status_sparql_endpoint != 'Available':
            data_lang_score = (-1, "No SPARQL endpoint available")
        else:
            data_lang_score = (-1, "Error fetching languages")
        
        metadata_lang = self.accessibility4all.metadata_lang(self.kg_quality.extra.endpointUrl, self.kg_quality.extra.urlVoid)

        if status_sparql_endpoint == 'Available':
            triples = self.kg_quality.amountOfData.numTriplesQ
            labels = self.kg_quality.understendability.numLabel
            if isinstance(labels, int) and labels > 0 and isinstance(triples, int) and triples > 0:
                human_readable_labels_score = (-1 + (labels / triples), f"Number of human-readable labels: {labels}")
            elif isinstance(labels, int) and labels == 0:
                human_readable_labels_score = (-1, "No human-readable labels found")
            elif isinstance(labels, int):
                human_readable_labels_score = (-1, f"Number of human-readable labels: {labels}")
            else:
                human_readable_labels_score = (-1, "Error fetching human-readable labels")
        else:
            human_readable_labels_score = (-1, "No SPARQL endpoint available")
        
        examples = self.accessibility4all.examples(self.kg_quality.extra.urlVoid, self.kg_quality.extra.endpointUrl, self.search_engine_metadata)

        description_readability = self.accessibility4all.description_readability(sparql_endpoint, void_file_url, Aggregator.getDescription(self.search_engine_metadata))

        understandable_sum = (data_lang_score[0] + metadata_lang[0] + human_readable_labels_score[0] + examples[0] + description_readability[0])
        if status_sparql_endpoint == 'Available':
            understandable_score = understandable_sum / 5
        else:
            understandable_score = understandable_sum / 3

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

        contact_person = self.accessibility4all.contact_point(self.search_engine_metadata, self.kg_quality.extra.endpointUrl, self.kg_quality.extra.urlVoid)
        dump_size = self.accessibility4all.dump_size(self.kg_quality.extra.urlVoid, self.kg_quality.extra.endpointUrl, self.kg_quality.extra.KGid)
        
        if status_sparql_endpoint == 'Available':
            auth = (0, f"SPARQL endpoint status: {status_sparql_endpoint}")
        else:
            auth = (-1, f"SPARQL endpoint status: {status_sparql_endpoint}")

        dump_format = self.kg_quality.extra.commonMediaType
        if dump_format == True:
            dump_format_score = (0, "Common formats available")
        elif dump_format == False:
            dump_format_score = (-1, "Dump available but no common formats found")
        else:
            dump_format_score = (-1, "No dump provided for the KG")
        
        opens_license = self.accessibility4all.open_license(Aggregator.getLicense(self.search_engine_metadata))
        alternative_access_point = self.accessibility4all.alternative_access_point(self.kg_quality.extra.urlVoid, self.kg_quality.extra.endpointUrl, self.kg_quality.extra.KGid)

        operable_sum = (contact_person[0] + dump_size[0] + auth[0] + dump_format_score[0] + opens_license[0] + alternative_access_point[0])
        if status_sparql_endpoint == 'Available' and (status_dump1 == 1 or status_dum2 == True):
            operable_score = operable_sum / 6
        elif status_sparql_endpoint == 'Available':
            operable_score = operable_sum / 4
        elif status_dump1 == 1 or status_dum2 == True:
            operable_score = operable_sum / 5
        else:
            operable_score = operable_sum / 3

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
        versioning = self.accessibility4all.version(self.kg_quality.extra.urlVoid, self.kg_quality.extra.endpointUrl)
        robots_txt = self.accessibility4all.robots_txt(self.kg_quality.extra.other_resources, self.kg_quality.extra.endpointUrl, self.kg_quality.verifiability.sources.web)
        webpage_broken_links = self.accessibility4all.webpage_status(self.search_engine_metadata)
        metadata_broken_links_rate = self.accessibility4all.metadata_broken_links_rate(self.search_engine_metadata, self.kg_quality.extra.endpointUrl, self.kg_quality.extra.urlVoid, self.kg_quality.extra.KGid)
        canonical_id = self.accessibility4all.canonical_citation(self.kg_quality.extra.urlVoid, self.kg_quality.extra.endpointUrl, self.search_engine_metadata)

        robust_score = (versioning[0] + robots_txt[0] + webpage_broken_links[0] + metadata_broken_links_rate[0] + canonical_id[0]) / 5

        return {
            "versioning": {
                "score": versioning[0],
                "details": versioning[1]},
            "robots_txt": {
                "score": robots_txt[0],
                "details": robots_txt[1]},
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
        sparql_endpoint = self.kg_quality.extra.endpointUrl
        void_file_url = self.kg_quality.extra.urlVoid
        resourcesDH = self.kg_quality.extra.other_resources
        status_sparql_endpoint = self.kg_quality.availability.sparqlEndpoint

        alt_image = self.accessibility4visuallyimpaired.alt_image(sparql_endpoint)
        audio_descriptions = self.deaf_hearing_accessibility.check_audio_description_subtitles(sparql_endpoint)['description_ratio']

        if status_sparql_endpoint == 'Available':
            acc_4_4_visually_impaired_score = (alt_image[0] + audio_descriptions[0]) / 2
        else:
            acc_4_4_visually_impaired_score = 0

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
        sparql_endpoint = self.kg_quality.extra.endpointUrl
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

        if status_sparql_endpoint == 'Available':
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
            "overall_score_only_special": sum_overall_only_special
        }
