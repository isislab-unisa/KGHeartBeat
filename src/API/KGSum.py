"""Run KGSum's source locally, without depending on its hosted API."""
import bz2
import gzip
import io
import logging
import lzma
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import json
import math
from urllib.parse import unquote, urlsplit

import requests

from rdf_formats import rdf_media_type


class KGSumAPI:
    def __init__(self, source_dir=None, python=None, timeout=1800):
        self.source_dir = Path(source_dir or os.environ.get('KGH_KGSUM_PATH') or
                               Path(__file__).resolve().parents[3] / 'KGSum').expanduser().absolute()
        self.python = python or os.environ.get('KGH_KGSUM_PYTHON') or str(self.source_dir / '.venv/bin/python')
        self.timeout = timeout
        self.last_error = None

    def create_KG_profile(self, kg_sparql_url=None, kg_rdf_url=None):
        """Return Turtle from KGSum's Python functions; failure is non-fatal."""
        self.last_error = None
        try:
            if not kg_sparql_url and not kg_rdf_url:
                return None
            if not (self.source_dir / 'src/generate_profile.py').is_file():
                raise ValueError('Set KGH_KGSUM_PATH to a KGSum checkout (see docs/local-profiles.md)')
            timeout = float(os.environ.get('KGH_KGSUM_TIMEOUT_SECONDS', self.timeout))
            if not math.isfinite(timeout) or timeout <= 0:
                raise ValueError('KGSum timeout must be positive and finite')
            with tempfile.TemporaryDirectory(prefix='kgh-profile-') as directory:
                directory = Path(directory)
                request = {'endpoint': str(kg_sparql_url)} if kg_sparql_url else {}
                if not kg_sparql_url:
                    filename, content, _ = self._read_dump(str(kg_rdf_url))
                    (directory / 'dump').mkdir()
                    dump = directory / 'dump' / (Path(filename).name or 'graph.ttl')
                    dump.write_bytes(content)
                    request['file'] = str(dump)
                request_path, output_path = directory / 'input.json', directory / 'output.json'
                request_path.write_text(json.dumps(request), encoding='utf-8')
                command = [self.python, str(Path(__file__).with_name('kgsum_runner.py')),
                           str(self.source_dir), str(request_path), str(output_path)]
                # Keep the assessment worker's process group so its deadline also
                # kills KGSum. Batch runs get a group for timeout cleanup.
                own_group = os.name == 'posix' and not os.environ.get('KGH_KGSUM_NETWORK_GUARD')
                with (directory / 'runtime.log').open('w+b') as log:
                    with subprocess.Popen(command, cwd=self.source_dir, stdout=log,
                                          stderr=log, start_new_session=own_group) as process:
                        try:
                            code = process.wait(timeout=timeout)
                        except subprocess.TimeoutExpired:
                            if own_group:
                                os.killpg(process.pid, signal.SIGKILL)
                            else:
                                process.kill()
                            process.wait()
                            raise ValueError('Local KGSum profiling timed out')
                    if code:
                        # A bounded tail provides actionable runtime errors.
                        log.seek(0, 2)
                        log.seek(max(0, log.tell() - 2000))
                        raise ValueError('Local KGSum failed: ' + log.read().decode('utf-8', errors='replace'))
                profile = json.loads(output_path.read_text(encoding='utf-8'))
                if not isinstance(profile, str) or not profile.strip():
                    raise ValueError('Local KGSum did not return a Turtle profile')
                return profile
        except (requests.RequestException, OSError, ValueError, EOFError, lzma.LZMAError) as exc:
            self.last_error = str(exc)
            logging.getLogger(__name__).warning('Failed to create local KGSum profile: %s', exc)
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
