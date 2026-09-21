"""SQLite admission transactions enforce the global slot and rolling IP quota."""
import hashlib
import hmac
import ipaddress
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager


class AdmissionError(Exception):
    def __init__(self, code, status, retry_after=0):
        self.code, self.status, self.retry_after = code, status, retry_after


class Store:
    def __init__(self, settings):
        self.settings = settings
        settings.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = settings.state_dir / 'jobs.sqlite3'
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, ip_hash TEXT NOT NULL, request_key TEXT UNIQUE,
                    input TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL,
                    started REAL, finished REAL, error TEXT, result TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS single_active_job ON jobs ((1))
                    WHERE status IN ('uploading', 'queued', 'running');
                CREATE INDEX IF NOT EXISTS ip_quota ON jobs (ip_hash, created);
            ''')
            db.execute('INSERT OR IGNORE INTO settings VALUES (?, ?)', ('ip_secret', secrets.token_hex(32)))
            self.secret = db.execute("SELECT value FROM settings WHERE key='ip_secret'").fetchone()[0].encode()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def ip_hash(self, address):
        ip = ipaddress.ip_address(address)
        if getattr(ip, 'ipv4_mapped', None):
            ip = ip.ipv4_mapped
        # IPv6 privacy addresses within the same /64 share a quota.
        identity = str(ipaddress.ip_network(f'{ip}/64', strict=False)) if ip.version == 6 else str(ip)
        return hmac.new(self.secret, identity.encode(), hashlib.sha256).hexdigest()

    def submit(self, address, source, request_key=None, uploading=False, now=None):
        now = time.time() if now is None else now
        ip_hash = self.ip_hash(address)
        encoded = json.dumps(source, sort_keys=True)
        key = hashlib.sha256(f'{ip_hash}:{request_key}'.encode()).hexdigest() if request_key else None
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if key:
                previous = db.execute('SELECT * FROM jobs WHERE request_key=?', (key,)).fetchone()
                if previous:
                    if previous['input'] != encoded:
                        raise AdmissionError('idempotency_conflict', 409)
                    return dict(previous)
            if db.execute("SELECT 1 FROM jobs WHERE status IN ('uploading','queued','running')").fetchone():
                raise AdmissionError('assessment_busy', 409, 30)
            recent = db.execute('SELECT created FROM jobs WHERE ip_hash=? AND created>? ORDER BY created',
                                (ip_hash, now - 86400)).fetchall()
            if len(recent) >= self.settings.submissions_per_day:
                raise AdmissionError('ip_limit_exceeded', 429, max(1, int(recent[0]['created'] + 86400 - now) + 1))
            job_id = secrets.token_urlsafe(32)
            db.execute('INSERT INTO jobs (id,ip_hash,request_key,input,status,created) VALUES (?,?,?,?,?,?)',
                       (job_id, ip_hash, key, encoded, 'uploading' if uploading else 'queued', now))
            return dict(db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone())

    def get(self, job_id):
        with self.connect() as db:
            row = db.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
            return dict(row) if row else None

    def uploaded(self, job_id):
        with self.connect() as db:
            db.execute("UPDATE jobs SET status='queued' WHERE id=? AND status='uploading'", (job_id,))

    def claim(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM jobs WHERE status='queued'").fetchone()
            if row:
                db.execute("UPDATE jobs SET status='running',started=? WHERE id=?", (time.time(), row['id']))
                return dict(row)

    def finish(self, job_id, status, error=None, result=None):
        assert status in ('completed', 'failed', 'timed_out')
        with self.connect() as db:
            db.execute("UPDATE jobs SET status=?,finished=?,error=?,result=? WHERE id=? AND status IN ('running','uploading')",
                       (status, time.time(), error, result, job_id))

    def recover(self):
        # Only call while holding the worker lock, also inherited by its child.
        with self.connect() as db:
            interrupted = [dict(row) for row in db.execute("SELECT * FROM jobs WHERE status='running'")]
            db.execute("UPDATE jobs SET status='failed',finished=?,error='worker_interrupted' WHERE status='running'",
                       (time.time(),))
            return interrupted

    def expire_uploads(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            cutoff = time.time() - 360
            expired = [dict(row) for row in db.execute("SELECT * FROM jobs WHERE status='uploading' AND created<?", (cutoff,))]
            db.execute("UPDATE jobs SET status='failed',finished=?,error='upload_interrupted' WHERE status='uploading' AND created<?",
                       (time.time(), cutoff))
            return expired
