"""Small client for KGSum's SPARQL and RDF-file profiling endpoints."""
import bz2
import gzip
import io
import logging
import lzma
import os
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
        # Web workers supply a byte budget; preserve the historical CLI behavior
        # when this setting is absent.
        if os.environ.get('KGH_MAX_DUMP_BYTES'):
            return self._read_dump_limited(source, int(os.environ['KGH_MAX_DUMP_BYTES']))
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

    def _read_dump_limited(self, source, limit):
        if limit <= 0:
            raise ValueError('Dump byte limit must be positive')
        media_type = None
        if urlsplit(source).scheme in ('http', 'https'):
            with requests.get(source, stream=True, timeout=(15, 600)) as response:
                response.raise_for_status()
                content = bytearray()
                for chunk in response.iter_content(1024 * 1024):
                    if len(content) + len(chunk) > limit:
                        raise ValueError('Profile dump download exceeds the byte limit')
                    content.extend(chunk)
                filename = unquote(urlsplit(response.url).path).rsplit('/', 1)[-1] or 'graph.ttl'
                media_type = response.headers.get('Content-Type')
        else:
            path = Path(source)
            filename = path.name
            with path.open('rb') as handle:
                content = handle.read(limit + 1)
            if len(content) > limit:
                raise ValueError('Profile dump exceeds the byte limit')
        for suffix, opener in (('.gz', gzip.GzipFile), ('.bz2', bz2.BZ2File), ('.xz', lzma.LZMAFile)):
            if filename.lower().endswith(suffix):
                stream = io.BytesIO(content)
                with (opener(fileobj=stream) if suffix == '.gz' else opener(stream)) as expanded:
                    content = expanded.read(limit + 1)
                if len(content) > limit:
                    raise ValueError('Expanded profile dump exceeds the byte limit')
                filename = filename[:-len(suffix)]
                break
        if not content:
            raise ValueError('RDF dump is empty')
        return filename, bytes(content), rdf_media_type(filename, media_type) or 'application/octet-stream'
