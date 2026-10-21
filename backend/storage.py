"""SQLite v1: one durable queue, immutable machine output and append-only reviews."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

TERMINAL = {'completed', 'partial', 'failed', 'cancelled', 'interrupted'}


def now():
    return datetime.now(timezone.utc).isoformat()


def record(row):
    if row is None:
        return None
    result = dict(row)
    for key in ('metadata', 'config', 'result', 'evidence'):
        if key in result:
            result[key] = json.loads(result[key])
    return result


class Store:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS uploads(
              id TEXT PRIMARY KEY,name TEXT NOT NULL,path TEXT NOT NULL,sha256 TEXT NOT NULL,
              bytes INTEGER NOT NULL,metadata TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'preparing',
              created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(
              id TEXT PRIMARY KEY,upload_id TEXT NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
              kind TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'queued',config TEXT NOT NULL,
              result TEXT NOT NULL DEFAULT '{}',stage TEXT NOT NULL DEFAULT 'Queued',
              processed INTEGER NOT NULL DEFAULT 0,expected INTEGER NOT NULL DEFAULT 0,
              cancel INTEGER NOT NULL DEFAULT 0,error TEXT,request_id TEXT UNIQUE NOT NULL,
              created TEXT NOT NULL,updated TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS incidents(
              id TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
              kind TEXT NOT NULL,origin TEXT NOT NULL,start REAL NOT NULL,end REAL NOT NULL,
              evidence TEXT NOT NULL,request_id TEXT UNIQUE,created TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews(
              id TEXT PRIMARY KEY,incident_id TEXT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
              decision TEXT NOT NULL,note TEXT NOT NULL,version INTEGER NOT NULL,
              request_id TEXT UNIQUE NOT NULL,created TEXT NOT NULL,
              UNIQUE(incident_id,version));
            CREATE TABLE IF NOT EXISTS artifacts(
              id TEXT PRIMARY KEY,upload_id TEXT NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
              job_id TEXT REFERENCES jobs(id) ON DELETE CASCADE,kind TEXT NOT NULL,path TEXT NOT NULL,
              mime TEXT NOT NULL,name TEXT NOT NULL,created TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS incident_job ON incidents(job_id);
            CREATE INDEX IF NOT EXISTS review_incident ON reviews(incident_id,version);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root/'application.sqlite3', timeout=10)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def query(self, sql, args=()):
        with self.connect() as db:
            return [record(r) for r in db.execute(sql, args).fetchall()]

    def one(self, sql, args=()):
        rows = self.query(sql, args)
        return rows[0] if rows else None

    def add_upload(self, name, path, digest, size, metadata):
        uid = str(uuid4())
        with self.connect() as db:
            db.execute('INSERT INTO uploads(id,name,path,sha256,bytes,metadata,created) VALUES(?,?,?,?,?,?,?)',
                       (uid, name, path, digest, size, json.dumps(metadata), now()))
        return self.upload(uid)

    def upload(self, uid):
        return self.one('SELECT * FROM uploads WHERE id=?', (uid,))

    def job(self, jid):
        return self.one('SELECT * FROM jobs WHERE id=?', (jid,))

    def create_job(self, uid, kind, config, request_id):
        encoded = json.dumps(config, sort_keys=True, allow_nan=False)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = record(db.execute('SELECT * FROM jobs WHERE request_id=?', (request_id,)).fetchone())
            if old:
                if (old['upload_id'], old['kind'], old['config']) != (uid, kind, config):
                    raise ValueError('Request ID already used with different data')
                return old
            jid = str(uuid4())
            db.execute('INSERT INTO jobs(id,upload_id,kind,config,request_id,created,updated) VALUES(?,?,?,?,?,?,?)',
                       (jid, uid, kind, encoded, request_id, now(), now()))
        return self.job(jid)

    def claim(self):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created LIMIT 1").fetchone()
            if row is None:
                return None
            db.execute("UPDATE jobs SET status='running',updated=? WHERE id=?", (now(), row['id']))
            return record(db.execute('SELECT * FROM jobs WHERE id=?', (row['id'],)).fetchone())

    def update_job(self, jid, **fields):
        allowed = {'status', 'result', 'stage', 'processed', 'expected', 'cancel', 'error'}
        if not fields or not fields.keys() <= allowed:
            raise ValueError('Invalid job update')
        values = [json.dumps(v, allow_nan=False) if k == 'result' else v for k, v in fields.items()]
        with self.connect() as db:
            db.execute('UPDATE jobs SET '+','.join(k+'=?' for k in fields)+',updated=? WHERE id=?', (*values, now(), jid))

    def update_upload(self, uid, status, metadata=None):
        with self.connect() as db:
            db.execute('UPDATE uploads SET status=?,metadata=? WHERE id=?',
                       (status, json.dumps(metadata or self.upload(uid)['metadata'], allow_nan=False), uid))

    def recover(self):
        with self.connect() as db:
            db.execute("UPDATE jobs SET status='interrupted',error='Worker stopped. Retry explicitly.',updated=? WHERE status='running'", (now(),))

    def add_artifact(self, uid, kind, path, mime, name, jid=None):
        aid = str(uuid4())
        relative = str(Path(path).resolve().relative_to(self.root))
        with self.connect() as db:
            db.execute('INSERT INTO artifacts VALUES(?,?,?,?,?,?,?,?)', (aid, uid, jid, kind, relative, mime, name, now()))
        return aid

    def incidents(self, jid=None):
        sql = '''SELECT i.*,r.decision,r.note,r.version,r.created AS reviewed_at FROM incidents i
                 LEFT JOIN reviews r ON r.incident_id=i.id AND r.version=(SELECT MAX(version) FROM reviews WHERE incident_id=i.id)'''
        return self.query(sql+(' WHERE i.job_id=?' if jid else '')+' ORDER BY i.start', (jid,) if jid else ())

    def add_incident(self, jid, kind, start, end, evidence, origin='model', request_id=None, initial_review=None):
        iid = str(uuid4())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if request_id:
                old = db.execute('SELECT * FROM incidents WHERE request_id=?', (request_id,)).fetchone()
                if old:
                    if (old['job_id'], old['kind'], old['start'], old['end'], json.loads(old['evidence'])) != (jid, kind, start, end, evidence):
                        raise ValueError('Request ID already used with different data')
                    return old['id']
            db.execute('INSERT INTO incidents VALUES(?,?,?,?,?,?,?,?,?,?)',
                       (iid, jid, kind, origin, start, end, json.dumps(evidence, allow_nan=False), request_id, now()))
            if initial_review:
                db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)', (str(uuid4()), iid, initial_review['decision'], initial_review['note'], 1, request_id, now()))
        return iid

    def review(self, iid, decision, note, expected_version, request_id):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = record(db.execute('SELECT * FROM reviews WHERE request_id=?', (request_id,)).fetchone())
            if old:
                if (old['incident_id'], old['decision'], old['note'], old['version']) != (iid, decision, note, expected_version+1):
                    raise ValueError('Request ID already used with different data')
                return old
            version = db.execute('SELECT COALESCE(MAX(version),0) FROM reviews WHERE incident_id=?', (iid,)).fetchone()[0]
            if version != expected_version:
                raise ValueError('Review changed elsewhere. Reload before saving.')
            rid = str(uuid4())
            db.execute('INSERT INTO reviews VALUES(?,?,?,?,?,?,?)', (rid, iid, decision, note, version+1, request_id, now()))
            return record(db.execute('SELECT * FROM reviews WHERE id=?', (rid,)).fetchone())
