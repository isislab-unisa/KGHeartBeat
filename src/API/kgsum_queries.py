"""Bound KGSum endpoint queries and retain statistics that do complete.

The count queries follow KGSum's async_select_remote_statistics at the pinned
revision documented in local-profiles.md (MIT, see kgsum-LICENSE.txt).
"""
import asyncio
import logging
import xml.etree.ElementTree as ET


def configure_remote_queries(remote, timeout=15):
    original_fetch = remote._fetch_query
    logger = logging.getLogger(__name__)

    async def fetch(session, endpoint, query, timeout=timeout, max_retries=1):
        # Upstream tries multiple protocols, formats and retries. A server-side
        # failure on an expensive count must not consume the entire profile job.
        return await asyncio.wait_for(
            original_fetch(session, endpoint, query, min(timeout, query_timeout), max_retries=1),
            timeout=query_timeout,
        )

    query_timeout = timeout
    remote._fetch_query = fetch
    cache = {}

    async def collect(endpoint, uri_regex_pattern):
        iri_filter = 'FILTER(isIRI(?s))'
        if uri_regex_pattern:
            pattern = remote._escape_sparql_string(uri_regex_pattern)
            iri_filter += f' FILTER(REGEX(STR(?s), "{pattern}"))'
        queries = {
            'triples': ['SELECT (COUNT(*) AS ?value) WHERE { ?s ?p ?o . }'],
            'entities': [
                f'SELECT (COUNT(DISTINCT ?s) AS ?value) WHERE {{ ?s ?p ?o . {iri_filter} }}',
                f'SELECT (COUNT(DISTINCT ?s) AS ?value) WHERE {{ ?s a ?class . {iri_filter} }}',
            ],
            'distinctSubjects': [
                'SELECT (COUNT(DISTINCT ?s) AS ?value) WHERE { ?s ?p ?o . FILTER(isIRI(?s) || isBlank(?s)) }'],
            'distinctObjects': [
                'SELECT (COUNT(DISTINCT ?o) AS ?value) WHERE { ?s ?p ?o . FILTER(isIRI(?o) || isBlank(?o) || isLiteral(?o)) }'],
            'classes': [
                'SELECT (COUNT(DISTINCT ?class) AS ?value) WHERE { ?s a ?class . FILTER(isIRI(?class)) }'],
        }

        async def count(session, key, alternatives):
            for query in alternatives:
                try:
                    response = await fetch(session, endpoint, query)
                    root = ET.fromstring(response)
                    node = root.find('.//{http://www.w3.org/2005/sparql-results#}binding[@name="value"]/*')
                    value = int(node.text) if node is not None else 0
                    if value > 0:
                        return key, value
                except Exception as exc:
                    logger.warning('Skipping unavailable profile statistic %s for %s: %s',
                                   key, endpoint, str(exc) or type(exc).__name__)
            return key, None

        async with remote.aiohttp.ClientSession() as session:
            results = await asyncio.gather(*(count(session, key, values) for key, values in queries.items()))
        return {key: value for key, value in results if value is not None}

    async def statistics(endpoint, timeout=120, uri_regex_pattern=None):
        key = (endpoint, uri_regex_pattern)
        if key not in cache:
            cache[key] = asyncio.create_task(collect(endpoint, uri_regex_pattern))
        return dict(await cache[key])

    remote.async_select_remote_statistics = statistics
