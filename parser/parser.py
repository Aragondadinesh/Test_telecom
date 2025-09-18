import os, json, time
import pika
from sqlalchemy import create_engine, Column, Integer, Float, String, Text, MetaData, Table
from sqlalchemy.exc import OperationalError

RABBIT_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBIT_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBIT_PASS = os.environ.get('RABBITMQ_PASS', 'guest')

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'packetsdb')
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'pktuser')
POSTGRES_PASS = os.environ.get('POSTGRES_PASS', 'pktpass')

DB_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASS}@{POSTGRES_HOST}/{POSTGRES_DB}'

def setup_db(engine):
    meta = MetaData()
    packets = Table('packets', meta,
        Column('id', Integer, primary_key=True),
        Column('ts', Float),
        Column('src', String(64)),
        Column('dst', String(64)),
        Column('proto', String(32)),
        Column('src_port', Integer),
        Column('dst_port', Integer),
        Column('length', Integer),
        Column('info', Text),
    )
    meta.create_all(engine)
    return packets

def connect_db():
    engine = create_engine(DB_URL, pool_pre_ping=True)
    # retry until db ready
    for i in range(30):
        try:
            conn = engine.connect()
            conn.close()
            return engine
        except OperationalError:
            time.sleep(1)
    raise RuntimeError('could not connect to postgres')

def main():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange='packets', exchange_type='fanout', durable=False)
    q = ch.queue_declare(queue='', exclusive=True)
    q_name = q.method.queue
    ch.queue_bind(exchange='packets', queue=q_name)
    engine = connect_db()
    packets_tbl = setup_db(engine)

    def callback(ch, method, properties, body):
        try:
            data = json.loads(body)
            ins = packets_tbl.insert().values(
                ts=data.get('ts'),
                src=data.get('src'),
                dst=data.get('dst'),
                proto=data.get('proto'),
                src_port=data.get('src_port'),
                dst_port=data.get('dst_port'),
                length=data.get('length'),
                info=data.get('info')
            )
            with engine.begin() as conn:
                conn.execute(ins)
        except Exception as e:
            print('parser error', e)

    ch.basic_consume(queue=q_name, on_message_callback=callback, auto_ack=True)
    print('[parser] waiting for messages')
    ch.start_consuming()

if __name__ == '__main__':
    main()
