"""Expose only private per-job URLs; there is no public job listing."""
import asyncio
import json
import re
import shutil
from datetime import datetime, timezone
from typing import Literal
from urllib.parse import urlsplit

from fastapi import FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .config import Settings
from .store import AdmissionError, Store


def validate_url(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 2048 or any(c.isspace() for c in value):
        raise HTTPException(422, 'Provide a valid HTTP(S) URL (maximum 2048 characters).')
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment or parsed.port == 0):
            raise ValueError()
    except ValueError:
        raise HTTPException(422, 'Only HTTP(S) URLs without credentials or fragments are accepted.')
    return value


def create_app(settings=None):
    settings = settings or Settings()
    store = Store(settings)
    app = FastAPI(title='KGHeartBeat assessment API', version='1.0.0')
    app.state.store = store
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type', 'Idempotency-Key'],
                       expose_headers=['Location', 'Retry-After', 'Content-Disposition'])

    @app.middleware('http')
    async def private_responses(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        return response

    @app.exception_handler(AdmissionError)
    async def admission_error(request, exc):
        headers = {'Retry-After': str(exc.retry_after)} if exc.retry_after else {}
        return JSONResponse({'error': exc.code}, status_code=exc.status, headers=headers)

    def describe(job):
        def timestamp(value):
            return datetime.fromtimestamp(value, timezone.utc).isoformat() if value else None
        url = f"{settings.public_url}/assessments/{job['id']}"
        output_format = json.loads(job['input']).get('output_format', 'csv')
        return {'id': job['id'], 'status': job['status'], 'status_url': url, 'result_url': url + '/result',
                'output_format': output_format,
                'created_at': timestamp(job['created']), 'started_at': timestamp(job['started']),
                'finished_at': timestamp(job['finished']), 'error': job['error']}

    def accepted(job):
        data = describe(job)
        return JSONResponse(data, status_code=202, headers={'Location': data['status_url']})

    @app.post('/assessments', status_code=202, openapi_extra={
        'requestBody': {'required': True, 'content': {'application/json': {'schema': {
            'type': 'object', 'required': ['type', 'url'], 'additionalProperties': False,
            'properties': {'type': {'type': 'string', 'enum': ['sparql', 'rdf_dump']},
                           'url': {'type': 'string', 'format': 'uri', 'maxLength': 2048},
                           'output_format': {'type': 'string', 'enum': ['csv', 'ttl'], 'default': 'csv'}},
        }}}}})
    async def submit(request: Request, idempotency_key: str | None = Header(default=None)):
        if idempotency_key and not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', idempotency_key):
            raise HTTPException(422, 'Idempotency-Key must contain 16–128 letters, digits, underscores or hyphens.')
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 4096:
                raise HTTPException(413, 'JSON request is too large.')
        try:
            source = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise HTTPException(422, 'Invalid JSON.')
        if (not isinstance(source, dict) or not {'type', 'url'} <= set(source)
                or set(source) - {'type', 'url', 'output_format'} or source['type'] not in ('sparql', 'rdf_dump')):
            raise HTTPException(422, 'Expected {"type": "sparql" or "rdf_dump", "url": "https://..."}.')
        source.setdefault('output_format', 'csv')
        if source['output_format'] not in ('csv', 'ttl'):
            raise HTTPException(422, 'output_format must be csv or ttl.')
        validate_url(source['url'])
        return accepted(store.submit(request.client.host, source, idempotency_key))

    @app.post('/assessments/upload', status_code=202, openapi_extra={
        'requestBody': {'required': True, 'content': {'application/octet-stream': {
            'schema': {'type': 'string', 'format': 'binary'}}}}})
    async def upload(request: Request, filename: str, output_format: Literal['csv', 'ttl'] = 'csv'):
        # The name selects a parser only; it is never used as a filesystem path.
        match = re.search(r'\.(ttl|rdf|xml|nt|nq|trig|n3|jsonld|json)(\.(gz|bz2|xz))?$|\.zip$', filename.lower())
        if len(filename) > 255 or not match:
            raise HTTPException(422, 'Provide a filename with a supported RDF extension, optionally compressed, or .zip.')
        source = {'type': 'upload', 'filename': 'input' + match.group(0), 'output_format': output_format}
        job = store.submit(request.client.host, source, uploading=True)
        directory = settings.state_dir / job['id']
        try:
            directory.mkdir(mode=0o700)
            async def receive():
                total = 0
                with (directory / source['filename']).open('wb') as output:
                    async for chunk in request.stream():
                        total += len(chunk)
                        if total > settings.max_dump_bytes:
                            raise HTTPException(413, 'RDF upload exceeds the configured byte limit.')
                        output.write(chunk)
                if total == 0:
                    raise HTTPException(422, 'RDF upload is empty.')
            await asyncio.wait_for(receive(), timeout=300)
            store.uploaded(job['id'])
        except BaseException as exc:
            shutil.rmtree(directory, ignore_errors=True)
            store.finish(job['id'], 'failed', 'upload_failed')
            if isinstance(exc, TimeoutError):
                raise HTTPException(408, 'Upload did not finish within five minutes.') from exc
            raise
        return accepted(store.get(job['id']))

    def find_job(job_id):
        if not re.fullmatch(r'[A-Za-z0-9_-]{43}', job_id):
            raise HTTPException(404, 'Assessment not found.')
        job = store.get(job_id)
        if not job:
            raise HTTPException(404, 'Assessment not found.')
        return job

    @app.get('/assessments/{job_id}')
    def status(job_id: str):
        return describe(find_job(job_id))

    @app.get('/assessments/{job_id}/result', response_class=Response, responses={200: {'content': {
        'text/csv': {'schema': {'type': 'string', 'format': 'binary'}},
        'text/turtle': {'schema': {'type': 'string', 'format': 'binary'}}}}})
    def result(job_id: str, output_format: Literal['csv', 'ttl'] | None = Query(default=None, alias='format')):
        job = find_job(job_id)
        if job['status'] != 'completed':
            return JSONResponse({'error': 'result_not_available', **describe(job)}, status_code=409)
        saved = json.loads(job['result'])
        if saved.get('schema_version') != 2:
            return JSONResponse({'error': 'legacy_result', 'detail': 'Run a new assessment to download CSV or Turtle.'}, status_code=409)
        extension = output_format or json.loads(job['input']).get('output_format', 'csv')
        filename = datetime.strptime(saved['analysis_date'], '%Y-%m-%d').date().isoformat()
        return Response(saved['files'][extension], media_type='text/csv' if extension == 'csv' else 'text/turtle',
                        headers={'Content-Disposition': f'attachment; filename="{filename}.{extension}"',
                                 'X-Content-Type-Options': 'nosniff'})

    return app
