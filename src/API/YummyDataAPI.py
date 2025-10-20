import requests
import json
import os
abs_path = os.path.dirname(os.path.abspath(__file__))


def getSPARQLEndpointURLs():
    yummy_url = 'https://yummydata.org/api/endpoint/search'

    try:
        response = requests.get(yummy_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            endpoint_urls = [el.get("endpoint_url") for el in data if "endpoint_url" in el]
            return endpoint_urls
        else:
            print(f"YummyData responded with status {response.status_code}")
            return []
    except Exception as e:
        print(f"Connection to YummyData API failed: {e}")
        return []