"""Temporary Oxigraph SPARQL service for analysing RDF distributions."""
import bz2
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import lzma
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import parse_qs, urlsplit
import zipfile

import requests

from rdf_formats import rdf_media_type


MAX_DUMP_BYTES = int(os.environ.get('KGH_MAX_DUMP_BYTES', 2 * 1024 ** 3))


def rdf_format(name, media_type=None):
    from pyoxigraph import RdfFormat

    media_type = rdf_media_type(name, media_type)
    return RdfFormat.from_media_type(media_type) if media_type else None


def _copy_limited(source, destination, limit):
    total = 0
    while True:
        chunk = source.read(1024 * 1024)
        if not chunk:
            return
        total += len(chunk)
        if total > limit:
            raise ValueError('RDF dump exceeds the configured byte limit')
        destination.write(chunk)


class LocalDumpEndpoint:
    """Own the download, disk-backed store, and loopback server as one context."""

    def __init__(self, source, media_type=None, max_bytes=MAX_DUMP_BYTES):
        self.source = str(source)
        self.media_type = media_type
        self.max_bytes = max_bytes
        self.store = self.server = self.thread = self.temp = None
        self.url = None

    def __enter__(self):
        from pyoxigraph import Store

        self.temp = TemporaryDirectory(prefix='kgheartbeat-oxigraph-')
        try:
            root = Path(self.temp.name)
            download = root / 'download'
            name = self.source
            media_type = self.media_type
            if urlsplit(self.source).scheme in ('http', 'https'):
                with requests.get(self.source, stream=True, timeout=(15, 120)) as response:
                    response.raise_for_status()
                    name = response.url
                    media_type = media_type or response.headers.get('Content-Type')
                    # iter_content decodes HTTP Content-Encoding; file compression is separate.
                    total = 0
                    with download.open('wb') as output:
                        for chunk in response.iter_content(1024 * 1024):
                            total += len(chunk)
                            if total > self.max_bytes:
                                raise ValueError('RDF download exceeds the configured byte limit')
                            output.write(chunk)
            else:
                with open(self.source, 'rb') as source, download.open('wb') as output:
                    _copy_limited(source, output, self.max_bytes)
            self.store = Store(str(root / 'store'))
            self._load(download, name, media_type, root)
            if len(self.store) == 0:
                raise ValueError('RDF dump contains no triples')
            self.server = ThreadingHTTPServer(('127.0.0.1', 0), self._handler())
            self.url = 'http://127.0.0.1:%s/sparql' % self.server.server_port
            self.thread = Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            return self
        except BaseException:
            self.close()
            raise

    def _load(self, download, name, media_type, root):
        base = self.source if urlsplit(self.source).scheme in ('http', 'https') else Path(self.source).resolve().as_uri()
        if zipfile.is_zipfile(download):
            with zipfile.ZipFile(download) as archive:
                members = [item for item in archive.infolist()
                           if not item.is_dir() and rdf_format(item.filename)]
                if not members:
                    raise ValueError('ZIP contains no supported RDF files')
                if sum(item.file_size for item in members) > self.max_bytes:
                    raise ValueError('Expanded RDF dump exceeds the configured byte limit')
                for member in members:
                    with archive.open(member) as source:
                        self.store.bulk_load(source, format=rdf_format(member.filename), base_iri=base)
            return
        with download.open('rb') as source:
            magic = source.read(6)
        opener = (gzip.open if magic.startswith(b'\x1f\x8b') else
                  bz2.open if magic.startswith(b'BZh') else
                  lzma.open if magic.startswith(b'\xfd7zXZ') else None)
        if opener:
            expanded = root / 'expanded'
            with opener(download, 'rb') as source, expanded.open('wb') as output:
                _copy_limited(source, output, self.max_bytes)
            download = expanded
        fmt = rdf_format(name, media_type) or rdf_format(self.source, self.media_type)
        if fmt is None:
            raise ValueError('Cannot identify RDF format for %s' % self.source)
        self.store.bulk_load(path=str(download), format=fmt, base_iri=base)

    def _handler(self):
        store = self.store

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def handle(self):
                try:
                    super().handle()
                except (ConnectionResetError, BrokenPipeError):
                    # A timed-out or cancelled client no longer needs a response.
                    self.close_connection = True

            def do_GET(self):
                self.execute(parse_qs(urlsplit(self.path).query))

            def do_POST(self):
                length = int(self.headers.get('Content-Length', 0))
                if length > 1024 * 1024:
                    self.send_error(413)
                    return
                body = self.rfile.read(length).decode('utf-8')
                params = ({'query': [body]} if self.headers.get_content_type() == 'application/sparql-query'
                          else parse_qs(body))
                self.execute(params)

            def execute(self, params):
                from pyoxigraph import QueryResultsFormat, RdfFormat, QueryTriples

                query_text = params.get('query', [''])[0]
                if not query_text:
                    self.send_error(400, 'A SPARQL query is required')
                    return
                try:
                    # Include named-graph dump data in the existing default-graph queries.
                    result = store.query(query_text, use_default_graph_as_union=True)
                    if isinstance(result, QueryTriples):
                        fmt = RdfFormat.RDF_XML
                    else:
                        accept = self.headers.get('Accept', '')
                        fmt = QueryResultsFormat.JSON if 'json' in accept else QueryResultsFormat.XML
                    payload = result.serialize(format=fmt)
                except (SyntaxError, ValueError) as error:
                    self.send_error(400, str(error))
                    return
                except Exception as error:
                    self.send_error(500, str(error))
                    return
                self.send_response(200)
                self.send_header('Content-Type', fmt.media_type)
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        return Handler

    def close(self):
        if self.server is not None:
            if self.thread is not None:
                self.server.shutdown()
                self.thread.join()
            self.server.server_close()
            self.server = None
        self.thread = None
        self.store = None
        if self.temp is not None:
            self.temp.cleanup()
            self.temp = None

    def __exit__(self, *args):
        self.close()


def try_local_dump(stack, context, candidates):
    """Load candidates already discovered by the aggregator, in priority order."""
    for source, media_type in candidates:
        try:
            endpoint = stack.enter_context(LocalDumpEndpoint(source, media_type))
            context.warning('Analysing RDF dump with local Oxigraph: %s' % source)
            return endpoint
        except ImportError:
            context.warning('RDF dump fallback requires pyoxigraph; install src/requirements.txt')
            return None
        except Exception as error:
            context.warning('Could not load RDF dump %s: %s' % (source, error))
    return None
