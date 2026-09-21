"""Evidence-based, cumulative five-star Open Data assessment.

Unknown evidence never awards a star. The rating is a verified lower bound,
not a claim that unobserved publication routes or links do not exist.
"""
import json
import ipaddress
import re
from urllib.parse import urlsplit


CRITERIA = ('open_web', 'structured_data', 'open_format', 'uri_identification', 'external_links')
CSV_COLUMNS = (
    'Five-star Open Web', 'Five-star Structured data', 'Five-star Open format',
    'Five-star URI identification', 'Five-star External links',
    'Five-star rating', 'Five-star assessment status', 'Five-star evidence',
)


def criterion(status='unknown', details='Not assessed', **evidence):
    return dict(status=status, details=details, **evidence)


class FiveStar:
    def __init__(self, criteria=None, checked_at=None):
        self.criteria = {name: criterion() for name in CRITERIA}
        if criteria:
            self.criteria.update(criteria)
        self.checked_at = checked_at
        self.stars = 0
        for name in CRITERIA:
            if self.criteria[name]['status'] != 'pass':
                break
            self.stars += 1
        # A known failed prerequisite fixes the ceiling only when every earlier
        # requirement passed. Otherwise the exact rating is still unresolved.
        self.status = ('complete' if self.stars == 5 or
                       self.criteria[CRITERIA[self.stars]]['status'] == 'fail'
                       else 'incomplete')

    def to_dict(self):
        return {'stars': self.stars, 'status': self.status,
                'rating_basis': 'highest_consecutive_verified_level',
                'checked_at': self.checked_at, 'criteria': self.criteria}

    def csv_values(self):
        return [self.criteria[name]['status'] for name in CRITERIA] + [
            self.stars, self.status, json.dumps(self.to_dict(), ensure_ascii=False)]

    def getFiveStar(self):
        return f'-5-star Open Data\n   Stars:{self.stars}/5 ({self.status})\n'


def from_csv(row):
    """Do not retrospectively assign ratings to historical or malformed rows."""
    raw = row.get(CSV_COLUMNS[-1], row.get('FiveStar_Evidence', ''))
    if raw:
        try:
            data = json.loads(raw)
            criteria = data['criteria']
            if not all(criteria[name]['status'] in ('pass', 'fail', 'unknown') for name in CRITERIA):
                raise ValueError('Invalid criterion status')
            return FiveStar({name: criteria[name] for name in CRITERIA}, data.get('checked_at')).to_dict()
        except (ValueError, TypeError, KeyError):
            pass
    return FiveStar().to_dict()


def web_uri(value):
    try:
        parsed = urlsplit(str(value))
        return parsed.scheme in ('http', 'https') and bool(parsed.hostname)
    except ValueError:
        return False


def license_status(value):
    """Small explicit allowlist; unknown licenses require review, not rejection."""
    if not isinstance(value, str) or not web_uri(value):
        return 'unknown'
    parsed = urlsplit(value.strip())
    host = parsed.hostname.removeprefix('www.')
    path = parsed.path.rstrip('/').lower()
    if host == 'creativecommons.org':
        if re.fullmatch(r'/publicdomain/(zero|mark)/1\.0', path):
            return 'pass'
        if re.fullmatch(r'/licenses/by(-sa)?/(1\.0|2\.0|2\.5|3\.0|4\.0)', path):
            return 'pass'
        if re.fullmatch(r'/licenses/by-(nc|nd|nc-sa|nc-nd)/[0-9.]+', path):
            return 'fail'
    if host == 'opendatacommons.org' and re.fullmatch(r'/licenses/(pddl|by|odbl)(/1\.0)?', path):
        return 'pass'
    if host == 'opendefinition.org' and path in ('/licenses/odc-by', '/licenses/odc-pddl', '/licenses/odc-odbl', '/licenses/cc-zero'):
        return 'pass'
    return 'unknown'


def public_web_uri(value):
    if not web_uri(value):
        return False
    host = urlsplit(str(value)).hostname.lower()
    if host == 'localhost' or host.endswith(('.localhost', '.local')):
        return False
    try:
        return ipaddress.ip_address(host).is_global
    except ValueError:
        return True


def _licenses(value):
    return value if isinstance(value, (list, tuple)) else [value]


def calculate(context, kg, all_triples=None, query_available=False, public_endpoint=False):
    """Reuse observations and perform at most three bounded, timed queries."""
    import query

    checks = {}
    errors = []

    def observe(label, callback):
        try:
            return context.timed(label, 'Five-star Open Data', callback)
        except Exception as error:
            errors.append(f'{label}: {error}')
            context.warning(f'Five-star Open Data | {label} | {error}')
            return None

    rows = all_triples if isinstance(all_triples, list) else []
    basis = 'existing triple retrieval'
    if not rows and query_available:
        configured_limit = getattr(context, 'triple_limit', None)
        sample_limit = min(100, configured_limit) if type(configured_limit) is int else 100
        rows = observe('Five-star RDF sample', lambda: query.getAllTriplesSPO(context.access_url, limit=sample_limit)) or []
        basis = f'bounded RDF sample (up to {sample_limit} triples)'
    rows = rows if isinstance(rows, list) else []
    rdf_observed = bool(rows)

    # The old licenseQuery may describe an arbitrary resource. Query explicit
    # dataset declarations instead and retain the subjects for inspection.
    licenses = [v for v in _licenses(kg.licensing.licenseMetadata) if isinstance(v, str) and web_uri(v)]
    declarations = []
    if query_available:
        declarations = observe('Five-star dataset licenses', lambda: query.getFiveStarDatasetLicenses(context.access_url)) or []
        if isinstance(declarations, list):
            licenses.extend(row['o']['value'] for row in declarations if 'o' in row)
    statuses = [license_status(value) for value in licenses]
    license_result = (statuses[0] if statuses and len(set(statuses)) == 1 else 'unknown')

    source = getattr(kg.extra, 'rdfDumpSource', None)
    source = str(source) if source is not None else None
    # Parsing a local file is not proof of publication on the Web.
    web_access = public_endpoint or (rdf_observed and public_web_uri(source))
    if not web_access and getattr(kg.extra, 'analysisSource', '') != 'rdf_dump':
        downloads = getattr(kg.extra, 'downloadUrl', [])
        web_access = (isinstance(downloads, list) and any(public_web_uri(url) for url in downloads)
                      and (kg.availability.RDFDumpM is True or kg.availability.RDFDumpM == 1
                           or kg.availability.RDFDumpQ is True))
    checks['open_web'] = criterion(
        'fail' if license_result == 'fail' else 'pass' if web_access and license_result == 'pass' else 'unknown',
        'Public data access and recognized open dataset license are both required.',
        web_access=bool(web_access), license_status=license_result, licenses=licenses,
        dataset_license_declarations=declarations, public_endpoint=bool(public_endpoint), dump_source=source)
    for name in ('structured_data', 'open_format'):
        checks[name] = criterion('pass' if rdf_observed else 'unknown',
                                 'Successfully retrieved RDF statements.' if rdf_observed else 'No RDF statements retrieved.',
                                 basis=basis, observed_triples=len(rows))

    subjects = list(dict.fromkeys(row.get('s', {}).get('value') for row in rows
                    if row.get('s', {}).get('type') == 'uri' and web_uri(row['s']['value'])))
    checks['uri_identification'] = criterion('pass' if subjects else 'unknown',
        'HTTP(S) subject identifiers observed; this is an existence check, not a coverage or dereferenceability guarantee.',
        basis=basis, examples=subjects[:5])

    # Explicit semantic mappings across URI authorities are an operational proxy
    # for links to another dataset. Counts or vocabulary reuse alone do not pass.
    mappings = observe('Five-star external mappings', lambda: query.getFiveStarExternalLinks(context.access_url)) if query_available else None
    checks['external_links'] = criterion('pass' if isinstance(mappings, list) and mappings else 'unknown',
        'Explicit semantic mappings between HTTP(S) identifiers with different authorities; same-authority datasets and other predicates require further evidence.',
        examples=mappings if isinstance(mappings, list) else [],
        method='bounded cross-authority mapping query; target availability not tested')
    if errors:
        for check in checks.values():
            check['query_errors'] = errors
    return FiveStar(checks, context.analysis_date)
