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

    def _check_metadata(self, sparql_endpoint, void_file_url, resources, media_type):
        # Check Search Engine Metadata resources
        for res in resources:
            path = res.get('path', '')
            if path and utils.is_url(path):
                try:
                    response = requests.head(path, timeout=10, allow_redirects=True)
                    if media_type in response.headers.get('Content-Type', ''):
                        return 1, path
                except requests.RequestException:
                    continue

        # Check VoID file
        if utils.is_url(void_file_url):
            void_file = VoIDAnalyses.parseVoID(void_file_url)
            objects = VoIDAnalyses.get_all_obj(void_file)
            for obj in objects:
                if utils.is_url(obj):
                    try:
                        response = requests.hea
                        d(obj, timeout=10, allow_redirects=True)
                        if media_type in response.headers.get('Content-Type', ''):
                            return 1, obj
                    except requests.RequestException:
                        continue

        # Check SPARQL endpoint
        if utils.is_url(sparql_endpoint):
            objects = query.get_all_obj_in_meta(sparql_endpoint)
            for obj in objects:
                if utils.is_url(obj):
                    try:
                        response = requests.head(obj, timeout=10, allow_redirects=True)
                        if media_type in response.headers.get('Content-Type', ''):
                            return 1, obj
                    except requests.RequestException:
                        continue

        return 0, f"No {media_type} metadata found"

    def alt_image(self,sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return (0, "No SPARQL endpoint provided")
        else:
            images = query.getImageIri(sparql_endpoint)
            if isinstance(images, list) and len(images) > 0:
                count_with_alt = 0
                for i, img in enumerate(images, 1):
                    if query.hasAltDescription(sparql_endpoint, img):
                        count_with_alt += 1
                    if i % 50 == 0:
                        print(f"Processed {i}/{len(images)} images...")
                return (count_with_alt / len(images), len(images))
            if isinstance(images, list) and len(images) == 0:
                return (0, "No images found in the KG")
    
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
                
    def video(self, sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return (0, "No SPARQL endpoint provided")
        else:
            video_exts = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm','.mpeg', '.mpg')
            video_count = query.fetch_objects(sparql_endpoint,condition=video_exts)
            if isinstance(video_count,int):
                if video_count > 0:
                    return 1, video_count
                else: 
                    return 0, "No video resources found in the KG"
            else:
                video_count = query.check_video_presence(sparql_endpoint)
                if isinstance(video_count,bool):
                    return int(video_count), video_count
                else:
                    return 0, f"Error counting video resources: {video_count}"
    
    def image_metadata(self, sparql_endpoint, void_file_url, resources):
        return self._check_metadata(sparql_endpoint, void_file_url, resources, "image/")

    def audio_meta(self, sparql_endpoint, void_file_url, resources):
        return self._check_metadata(sparql_endpoint, void_file_url, resources, "audio/")

    def video_meta(self, sparql_endpoint, void_file_url, resources):
        return self._check_metadata(sparql_endpoint, void_file_url, resources, "video/")
    
# Test
if __name__ == "__main__":
    av = Accessibility4VisuallyImpaired()
    sparql_endpoint = "https://dbpedia.org/sparql"
    print(av.audio(sparql_endpoint))
    print(av.alt_image(sparql_endpoint))
    print(av.video(sparql_endpoint))
