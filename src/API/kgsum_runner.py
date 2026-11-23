"""Bridge executed using KGSum's own Python environment and source checkout.

Never import KGSum into the assessment process: both projects have modules named
``src`` and ``config``, as well as incompatible dependency versions.
"""
import asyncio
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys


def main():
    source, request_path, output_path = map(Path, sys.argv[1:])
    if os.environ.get('KGH_KGSUM_NETWORK_GUARD') == '1':
        guard_path = Path(__file__).resolve().parents[2] / 'assessment_service/network.py'
        spec = importlib.util.spec_from_file_location('kgh_network_guard', guard_path)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        guard.install_network_guard()
    # Replace inherited KGHeartbeat import paths before importing KGSum.
    heartbeat = Path(__file__).resolve().parents[1]
    sys.path = [str(source)] + [p for p in sys.path if p and Path(p).resolve() not in
                               {heartbeat, heartbeat.parent, Path(__file__).resolve().parent}]
    from config import Config
    Config.init_configuration()
    # LOV enrichment produces classification features. Keep profiling limited
    # to graph extraction, without model inference, NLP or external LOV queries.
    Config.QUERY_LOV = False
    os.environ.setdefault('LOCAL_ENDPOINT_LOV', 'urn:kgheartbeat:lov-disabled')
    # The upstream generate_profile module eagerly imports its ML pipeline.
    # Use its independent extractors and a copy of its RDF serializer instead.
    sys.path.insert(1, str(Path(__file__).resolve().parent))
    from kgsum_rdf import profile_to_rdf
    request = json.loads(request_path.read_text(encoding='utf-8'))
    if request.get('endpoint'):
        from src import dataset_preparation_remote as remote
        from kgsum_queries import configure_remote_queries
        query_timeout = float(os.environ.get('KGH_KGSUM_QUERY_TIMEOUT_SECONDS', '15'))
        if not math.isfinite(query_timeout) or query_timeout <= 0:
            raise ValueError('KGSum query timeout must be positive and finite')
        configure_remote_queries(remote, timeout=query_timeout)
        profile = asyncio.run(remote.process_endpoint_full_inplace(request['endpoint']))
    elif request.get('file'):
        from src.dataset_preparation import process_file_full_inplace
        profile = process_file_full_inplace(request['file'])
    else:
        raise ValueError('An endpoint or RDF file is required')
    if not isinstance(profile, dict) or not profile or 'error' in profile:
        raise RuntimeError(f'KGSum profile generation failed: {profile}')
    # An unlabelled RDF file can have no title, endpoint or id in KGSum's raw
    # extraction. Give it an identity independent of the temporary filename.
    if not profile.get('id'):
        if request.get('endpoint'):
            profile['id'] = request['endpoint']
        else:
            digest = hashlib.sha256()
            with Path(request['file']).open('rb') as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b''):
                    digest.update(chunk)
            profile['id'] = 'sha256:' + digest.hexdigest()
    turtle = profile_to_rdf(profile, rdf_format='turtle')
    output_path.write_text(json.dumps(turtle), encoding='utf-8')


if __name__ == '__main__':
    main()
