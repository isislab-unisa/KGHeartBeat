"""Store only the current KGSum profile for each knowledge graph."""
import json
import logging
from pathlib import Path
import string

from API.KGSum import KGSumAPI
from result_paths import results_dir


RESULTS_DIR = results_dir()


def normalize_kg_id(kg_id):
    # Match the identifiers used by the historical CSV-to-JSON exporter.
    return str(kg_id).translate(str.maketrans('', '', string.punctuation)).replace(' ', '')


def create_profile(kg_id, analysis_date, sparql_endpoint=None, rdf_dump=None, results_dir=RESULTS_DIR):
    """Overwrite the previous result, including on failure, so it cannot become stale."""
    profile = None
    try:
        profile = KGSumAPI().create_KG_profile(kg_sparql_url=sparql_endpoint, kg_rdf_url=rdf_dump)
    except Exception:
        logging.getLogger(__name__).exception('Could not create KGSum profile for %s', kg_id)
    try:
        record = {
            'kg_id': normalize_kg_id(kg_id),
            'analysis_date': str(analysis_date),
            'profile': profile,
        }
        path = Path(results_dir) / 'profile' / (record['kg_id'] + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(path)
    except Exception:
        logging.getLogger(__name__).exception('Could not save KGSum profile for %s', kg_id)


def load_profile(kg_id, analysis_date, results_dir=RESULTS_DIR):
    """Only return a profile produced for this exact analysis date."""
    path = Path(results_dir) / 'profile' / (normalize_kg_id(kg_id) + '.json')
    try:
        record = json.loads(path.read_text(encoding='utf-8'))
        if record['analysis_date'] == str(analysis_date):
            return record['profile']
    except FileNotFoundError:
        pass
    except (OSError, ValueError, KeyError, TypeError):
        logging.getLogger(__name__).warning('Could not read KGSum profile %s', path)
    return None
