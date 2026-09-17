"""RDF format recognition shared by catalog discovery and the local loader."""
from urllib.parse import urlsplit


_EXTENSIONS = {
    'rdf': 'application/rdf+xml', 'owl': 'application/rdf+xml',
    'ttl': 'text/turtle', 'nt': 'application/n-triples',
    'nq': 'application/n-quads', 'trig': 'application/trig',
    'n3': 'text/n3', 'jsonld': 'application/ld+json',
}
_ALIASES = {
    'application/x-ntriples': 'application/n-triples',
    'application/x-nquads': 'application/n-quads',
    'application/turtle': 'text/turtle', 'rdf/turtle': 'text/turtle',
    'text/rdf+n3': 'text/n3', 'turtle': 'text/turtle',
    'n-triples': 'application/n-triples', 'n-quads': 'application/n-quads',
    'rdf/xml': 'application/rdf+xml', 'json-ld': 'application/ld+json',
}


def rdf_media_type(name, media_type=None):
    path = urlsplit(str(name)).path.lower()
    for suffix in ('.gz', '.bz2', '.xz'):
        if path.endswith(suffix):
            path = path[:-len(suffix)]
    extension_type = _EXTENSIONS.get(path.rsplit('.', 1)[-1])
    hint = media_type.split(';')[0].strip().lower() if isinstance(media_type, str) else ''
    return (extension_type or _EXTENSIONS.get(hint) or _ALIASES.get(hint)
            or (hint if hint in _EXTENSIONS.values() else None))
