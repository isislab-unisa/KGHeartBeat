"""Small client for KGSum's SPARQL and RDF-file profiling endpoints."""
import bz2
import gzip
import logging
import lzma
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests

from rdf_formats import rdf_media_type


class KGSumAPI:
    def __init__(self, base_url='http://www.isislab.it:12280/kgsum', timeout=(15, 1800)):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

    def create_KG_profile(self, kg_sparql_url=None, kg_rdf_url=None):
        """Return the JSON or Turtle profile; failures must not stop quality analysis."""
        try:
            if kg_sparql_url:
                response = requests.post(
                    f'{self.base_url}/api/v1/profile/sparql',
                    json={'endpoint': kg_sparql_url, 'format': 'ttl'},
                    timeout=self.timeout,
                )
            elif kg_rdf_url:
                filename, content, media_type = self._read_dump(str(kg_rdf_url))
                response = requests.post(
                    f'{self.base_url}/api/v1/profile/file',
                    params={'format': 'ttl'},
                    files={'file': (filename, content, media_type)},
                    timeout=self.timeout,
                )
            else:
                return None
            response.raise_for_status()
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError:
                return response.text
        except (requests.RequestException, OSError, ValueError, EOFError, lzma.LZMAError) as exc:
            logging.getLogger(__name__).warning('Failed to create KGSum profile: %s', exc)
            return None

    def _read_dump(self, source):
        media_type = None
        if urlsplit(source).scheme in ('http', 'https'):
            response = requests.get(source, timeout=(15, 600))
            response.raise_for_status()
            content = response.content
            filename = unquote(urlsplit(response.url).path).rsplit('/', 1)[-1] or 'graph.ttl'
            media_type = response.headers.get('Content-Type')
        else:
            path = Path(source)
            filename, content = path.name, path.read_bytes()
        for suffix, decompress in (('.gz', gzip.decompress), ('.bz2', bz2.decompress), ('.xz', lzma.decompress)):
            if filename.lower().endswith(suffix):
                filename, content = filename[:-len(suffix)], decompress(content)
                break
        if not content:
            raise ValueError('RDF dump is empty')
        return filename, content, rdf_media_type(filename, media_type) or 'application/octet-stream'
