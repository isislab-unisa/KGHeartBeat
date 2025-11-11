import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils
import query
import utils


class DeafHearingAccessibility:
    def __init__(self):
        return
    
    def image_metadata(self, sparql_endpoint, void_file_url, resources):
        utils.run_with_timeout(utils.check_metadata_media_type,args=(sparql_endpoint, void_file_url, resources, "image/",), timeout=15)

    def video_meta(self, sparql_endpoint, void_file_url, resources):
        utils.run_with_timeout(utils.check_metadata_media_type,args=(sparql_endpoint, void_file_url, resources, "video/",), timeout=15)
    
    def video(self, sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return (0, "No SPARQL endpoint provided")
        else:
            video_exts = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm','.mpeg', '.mpg')
            video_count = query.fetch_objects(sparql_endpoint,condition=video_exts)
            total_resources_in_kg = query.count_res(sparql_endpoint)
            if isinstance(video_count,int) and isinstance(total_resources_in_kg,int) and total_resources_in_kg > 0:
                    return 1, f"Number of videos: {video_count}"
            else:
                video_bool, videos_num = query.check_video_presence(sparql_endpoint)
                total_resources_in_kg = query.count_res(sparql_endpoint)
                if isinstance(videos_num,list) and isinstance(total_resources_in_kg,int) and total_resources_in_kg > 0:
                    return (videos_num / total_resources_in_kg), f"Number of videos: {videos_num}"
                else:
                    return 0, f"Error counting video resources: {videos_num}"

    def check_video_description_subtitles(self, sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return {
                "description_ratio": (0, "No SPARQL endpoint provided"),
                "subtitle_ratio": (0, "No SPARQL endpoint provided"),
                "sign_language_ratio": (0, "No SPARQL endpoint provided"),
            }
        else:
            count_desc = 0
            count_sub = 0
            count_sign = 0
            video_exts = ('.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm','.mpeg', '.mpg')
            videos = query.fetch_objects_value(sparql_endpoint,condition=video_exts)
            if not isinstance(videos, list) or not len(videos) > 0:
                _, videos = query.check_video_presence(sparql_endpoint, limit = False)

            if isinstance(videos, list) and len(videos) > 0:
                for video in videos:
                    sub = False
                    desc = False
                    sign_lang = False
                    _, texts = query.hasAltDescription(sparql_endpoint, video)
                    if len(texts) > 0:
                        for text in texts:
                            if utils.is_subtitle(text):
                                sub = True
                            else:
                                desc = True
                            if utils.check_sign_lang_string(text):
                                sign_lang = True
                        if sub:
                            count_sub += 1
                        if desc:
                            count_desc += 1
                        if sign_lang:
                            count_sign += 1
                description_ratio = count_desc / len(videos) if len(videos) > 0 else 0
                subtitle_ratio = count_sub / len(videos) if len(videos) > 0 else 0
                sign_language_ratio = count_sign / len(videos) if len(videos) > 0 else 0
                return {
                    "description_ratio": (description_ratio, f"Number of videos: {len(videos)}"),
                    "subtitle_ratio": (subtitle_ratio, f"Number of videos: {len(videos)}"),
                    "sign_language_ratio": (sign_language_ratio, f"Number of videos: {len(videos)}"),
                }
            else:
                return {
                    "description_ratio": (0, f"No video resources found in the KG: {videos}"),
                    "subtitle_ratio": (0, f"No video resources found in the KG: {videos}"),
                    "sign_language_ratio": (0, f"No video resources found in the KG: {videos}"),
                }

    def check_audio_description_subtitles(self, sparql_endpoint):
        if not utils.is_url(sparql_endpoint):
            return {
                "description_ratio": (0, "No SPARQL endpoint provided"),
                "subtitle_ratio": (0, "No SPARQL endpoint provided"),
                "sign_language_ratio": (0, "No SPARQL endpoint provided"),
            }
        else:
            count_desc = 0
            count_sub = 0
            count_sign = 0
            audio_exts = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.aiff')
            audios = query.fetch_objects_value(sparql_endpoint,condition=audio_exts)
            if not isinstance(audios, list) or not len(audios) > 0:
                _, audios = query.check_audio_presence(sparql_endpoint, limit = False)

            if isinstance(audios, list) and len(audios) > 0:
                for audio in audios:
                    sub = False
                    desc = False
                    sign_lang = False
                    _, texts = query.hasAltDescription(sparql_endpoint, audio)
                    if len(texts) > 0:
                        for text in texts:
                            if utils.is_subtitle(text):
                                sub = True
                            else:
                                desc = True
                            if utils.check_sign_lang_string(text):
                                sign_lang = True
                        if sub:
                            count_sub += 1
                        if desc:
                            count_desc += 1
                        if sign_lang:
                            count_sign += 1
                description_ratio = count_desc / len(audios) if len(audios) > 0 else 0
                subtitle_ratio = count_sub / len(audios) if len(audios) > 0 else 0
                sign_language_ratio = count_sign / len(audios) if len(audios) > 0 else 0
                return {
                    "description_ratio": (description_ratio, f"Number of audios: {len(audios)}"),
                    "subtitle_ratio": (subtitle_ratio, f"Number of audios: {len(audios)}"),
                    "sign_language_ratio": (sign_language_ratio, f"Number of audios: {len(audios)}"),
                }
            else:
                return {
                    "description_ratio": (0, f"No audio resources found in the KG: {audios}"),
                    "subtitle_ratio": (0, f"No audio resources found in the KG: {audios}"),
                    "sign_language_ratio": (0, f"No audio resources found in the KG: {audios}"),
                }

# Test
if __name__ == "__main__":
    av = DeafHearingAccessibility()
    sparql_endpoint = "https://dbpedia.org/sparql"
    print(av.video(sparql_endpoint))
    print(av.video_meta(sparql_endpoint, None, None))
    print(av.image_metadata(sparql_endpoint, None, None))
    print(av.check_video_description_subtitles(sparql_endpoint))
    print(av.check_audio_description_subtitles(sparql_endpoint))