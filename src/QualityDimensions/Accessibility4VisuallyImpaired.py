import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import query
import utils
import requests
import VoIDAnalyses

class Accessibility4VisuallyImpaired:
    def __init__(self):
        pass

    def alt_image(self,sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return (0, "No SPARQL endpoint provided")
        else:
            images = query.getImageIri(sparql_endpoint)
            if isinstance(images, list) and len(images) > 0:
                count_with_alt = 0
                for i, img in enumerate(images, 1):
                    res = query.hasAltDescription(sparql_endpoint, img)
                    if isinstance(res, tuple) and len(res) == 2:
                        if res[0]:
                            count_with_alt += 1
                        if i % 50 == 0:
                            print(f"Processed {i}/{len(images)} images...")
                    else:
                        continue
                return (count_with_alt / len(images), "Total number of images recovered: " + str(len(images)))
            if isinstance(images, list) and len(images) == 0:
                return (0, "No images found in the KG")
            else:
                return 0, f"Error fetching images: {images}"
    
    def audio_meta(self, sparql_endpoint, void_file_url, resources):
        return utils.check_metadata_media_type(sparql_endpoint, void_file_url, resources, "audio/")
    
    def audio(self, sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return (0, "No SPARQL endpoint provided")
        else:
            audio_exts = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.aiff')
            audio_count = query.fetch_objects(sparql_endpoint,condition=audio_exts)
            count_all_res = query.count_res(sparql_endpoint)
            if isinstance(audio_count,int) and isinstance(count_all_res,int) and count_all_res > 0:
                ratio = audio_count / count_all_res
                return ratio, audio_count
            else:
                audio_count = query.count_audio_objects_sparql(sparql_endpoint)
                count_all_res = query.count_res(sparql_endpoint)
                if isinstance(audio_count,int) and isinstance(count_all_res,int) and count_all_res > 0:
                    ratio = audio_count / count_all_res
                    return ratio, audio_count
                else:
                    return 0, f"Error counting audio resources: {audio_count}"


    
# Test
if __name__ == "__main__":
    av = Accessibility4VisuallyImpaired()
    sparql_endpoint = "https://dbpedia.org/sparql"
    print(av.audio(sparql_endpoint))
    print(av.alt_image(sparql_endpoint))
    print(av.video(sparql_endpoint))
