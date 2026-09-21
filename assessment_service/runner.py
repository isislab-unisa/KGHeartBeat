"""One isolated assessment. Invoked by the worker, never by an HTTP request."""
import json
import os
from pathlib import Path
import resource
import signal
import sys
from datetime import datetime, timezone

from .network import install_network_guard, validate_public_url
from .exports import export_assessment


def run(directory):
    memory = int(os.environ['KGH_MEMORY_BYTES'])
    cpu = int(os.environ['KGH_TIMEOUT_SECONDS'])
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_FSIZE, (int(os.environ['KGH_DISK_BYTES']),) * 2)
    # Retain a wall-clock deadline even if the supervising worker is killed.
    def deadline(signum, frame):
        os.killpg(os.getpgrp(), signal.SIGKILL)
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(cpu)
    source = json.loads((directory / 'input.json').read_text())
    install_network_guard()
    if source['type'] != 'upload':
        validate_public_url(source['url'])
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from analyses import analysis_session
    from evaluate_fairness import EvaluateFAIRness
    from evaluate_human_centered_acc import EvaluateHumanCenteredAcc
    from score import Score

    date = datetime.now(timezone.utc).date().isoformat()
    target = ({'sparql_endpoint': source['url']} if source['type'] == 'sparql' else
              {'rdf_dump': str(directory / source['filename']) if source['type'] == 'upload' else source['url']})
    # KGSum is a remote service; uploaded private files must not be sent to it.
    with analysis_session(date, **target, triple_limit=int(os.environ['KGH_TRIPLE_LIMIT']),
                          include_profile=source['type'] != 'upload') as kg:
        score = Score(kg, 20)
        total, normalized = score.getWeightedDimensionScore(1)
        kg.extra.score, kg.extra.normalizedScore = round(float(total), 3), round(float(normalized), 3)
        kg.extra.scoreObj = score
        evaluation = EvaluateFAIRness(kg)
        evaluation.evaluate_findability()
        evaluation.evaluate_availability()
        evaluation.evaluate_interoperability()
        evaluation.evaluate_reusability()
        evaluation.calculate_FAIR_score()
        kg.fairness = evaluation.fairness
        kg.human_accessibility = EvaluateHumanCenteredAcc(kg).evaluate_all()

    result = export_assessment(kg, date, directory)
    temporary = directory / 'result.tmp'
    temporary.write_text(json.dumps(result, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temporary.replace(directory / 'result.json')


if __name__ == '__main__':
    run(Path(sys.argv[1]).resolve())
