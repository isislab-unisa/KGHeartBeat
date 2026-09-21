"""Single-host Linux worker with inherited filesystem and abstract socket locks."""
import errno
import fcntl
import json
import logging
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time

from .config import Settings
from .store import Store

ROOT = Path(__file__).resolve().parents[1]
MAX_RESULT_BYTES = 16 * 1024**2


def acquire_host_lock():
    # flock on bind/virtiofs aliases can refer to different kernel lock domains.
    # An abstract socket is independent of filesystem mounts and remains bound
    # while the analysis child holds its inherited descriptor.
    guard = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        guard.bind('\0kgheartbeat-assessment-worker')
    except OSError as error:
        guard.close()
        if error.errno == errno.EADDRINUSE:
            raise SystemExit('Another assessment worker or child holds the host lock.') from error
        raise
    return guard


def reject_legacy_workers():
    # During upgrades, old workers have only the filesystem lock. Do not run
    # recovery alongside them, even when they use another mount of this repo.
    for entry in Path('/proc').glob('[0-9]*/cmdline'):
        if entry.parent.name == str(os.getpid()):
            continue
        try:
            args = entry.read_bytes().split(b'\0')
        except FileNotFoundError:
            continue
        if any(module in args for module in
               (b'assessment_service.worker', b'assessment_service.runner')):
            raise SystemExit('An existing assessment worker or child is still running; stop it before restarting.')


def cleanup_job_files(settings, job):
    directory = settings.state_dir / job['id']
    shutil.rmtree(directory / 'tmp', ignore_errors=True)
    source = json.loads(job['input'])
    if source['type'] == 'upload':
        (directory / source['filename']).unlink(missing_ok=True)
    for name in ('result.json', 'result.tmp'):
        (directory / name).unlink(missing_ok=True)
    # Download bytes are persisted in SQLite; avoid retaining a second copy.
    for pattern in ('????-??-??.csv', '????-??-??.ttl', '????-??-??_with_dimensions.csv'):
        for path in directory.glob(pattern):
            path.unlink(missing_ok=True)


def directory_size(directory):
    total = 0
    for path in directory.rglob('*'):
        try:
            if path.is_file():
                total += path.stat().st_size
        except FileNotFoundError:
            pass
    return total


def execute(store, job, lock_fd, command=None, poll_seconds=1, host_lock_fd=None):
    settings = store.settings
    directory = settings.state_dir / job['id']
    directory.mkdir(exist_ok=True, mode=0o700)
    temporary = directory / 'tmp'
    temporary.mkdir(exist_ok=True)
    (directory / 'input.json').write_text(job['input'])
    env = dict(os.environ, KGH_RESULTS_DIR=str(directory), TMPDIR=str(temporary),
               KGH_MEMORY_BYTES=str(settings.memory_bytes), KGH_TIMEOUT_SECONDS=str(settings.timeout_seconds),
               KGH_DISK_BYTES=str(settings.disk_bytes), KGH_MAX_DUMP_BYTES=str(settings.max_dump_bytes),
               KGH_TRIPLE_LIMIT=str(settings.triple_limit), OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    env['PYTHONPATH'] = str(ROOT) + os.pathsep + env.get('PYTHONPATH', '')
    # Proxies could bypass destination checks in the Python network guard.
    for key in list(env):
        if key.lower() in ('http_proxy', 'https_proxy', 'all_proxy'):
            del env[key]
    process = None
    status, error, result = 'failed', 'assessment_failed', None
    try:
        with (directory / 'worker.log').open('wb') as log:
            process = subprocess.Popen(command or [sys.executable, '-m', 'assessment_service.runner', str(directory)],
                                       cwd=directory, env=env, stdout=log, stderr=log, start_new_session=True,
                                       pass_fds=(lock_fd,) + ((host_lock_fd,) if host_lock_fd is not None else ()))
            deadline = time.monotonic() + settings.timeout_seconds
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    status, error = 'timed_out', 'assessment_timeout'
                    break
                if directory_size(directory) > settings.disk_bytes:
                    error = 'disk_limit_exceeded'
                    break
                time.sleep(poll_seconds)
            else:
                if process.returncode == 0:
                    output = directory / 'result.json'
                    if output.stat().st_size > MAX_RESULT_BYTES:
                        raise ValueError('Result exceeds 16 MiB')
                    result = output.read_text(encoding='utf-8')
                    parsed = json.loads(result)
                    if (not isinstance(parsed, dict) or parsed.get('schema_version') != 2
                            or not isinstance(parsed.get('files'), dict)
                            or any(not isinstance(parsed['files'].get(ext), str) or not parsed['files'][ext]
                                   for ext in ('csv', 'ttl'))):
                        raise ValueError('Invalid assessment result')
                    status, error = 'completed', None
    except Exception:
        logging.exception('Assessment %s failed', job['id'])
    finally:
        if process:
            # Kill all analysis subprocesses BEFORE releasing the database slot.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
        store.finish(job['id'], status, error, result)
        cleanup_job_files(settings, job)


def main():
    if sys.platform != 'linux':
        raise SystemExit('Run the assessment worker on Linux.')
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    store = Store(settings)
    logging.info('Assessment worker database: %s', store.path)
    def stop(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, stop)
    with acquire_host_lock() as host_lock, (settings.state_dir / 'worker.lock').open('a') as lock:
        reject_legacy_workers()
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another worker or its assessment child still holds the worker lock.')
        for job in store.recover():
            cleanup_job_files(settings, job)
        try:
            while True:
                for job in store.expire_uploads():
                    cleanup_job_files(settings, job)
                job = store.claim()
                if job:
                    execute(store, job, lock.fileno(), host_lock_fd=host_lock.fileno())
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            logging.info('Worker stopped.')


if __name__ == '__main__':
    main()
