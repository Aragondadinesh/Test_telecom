from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os, time
from sqlalchemy import create_engine, text

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'packetsdb')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'pktuser')
POSTGRES_PASS = os.environ.get('POSTGRES_PASS', 'pktpass')

DB_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}/{POSTGRES_DB}'
engine = create_engine(DB_URL, pool_pre_ping=True)

app = FastAPI(title='Packet API (microservices)')

@app.get('/packets')
def list_packets(limit: int = 100, offset: int = 0):
    with engine.connect() as conn:
        rows = conn.execute(text('SELECT id, ts, src, dst, proto, src_port, dst_port, length, info FROM packets ORDER BY id DESC LIMIT :lim OFFSET :off'), {'lim': limit, 'off': offset}).fetchall()
        return [dict(r) for r in rows]

@app.get('/stats')
def stats():
    with engine.connect() as conn:
        rows = conn.execute(text('SELECT COALESCE(proto,\'UNKNOWN\') as proto, COUNT(*) as cnt FROM packets GROUP BY proto ORDER BY cnt DESC LIMIT 50')).fetchall()
        return { r['proto']: r['cnt'] for r in rows }

@app.post('/clear')
def clear():
    with engine.connect() as conn:
        conn.execute(text('DELETE FROM packets'))
        conn.commit()
    return {'status':'ok'}
