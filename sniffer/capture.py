import os, time, json
from scapy.all import sniff, IP, IPv6, TCP, UDP, ICMP
import pika

RABBIT_HOST = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
RABBIT_USER = os.environ.get('RABBITMQ_USER', 'guest')
RABBIT_PASS = os.environ.get('RABBITMQ_PASS', 'guest')
IFACE = os.environ.get('IFACE', 'any')
BPF_FILTER = os.environ.get('FILTER', '')

def make_conn():
    creds = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=creds, heartbeat=60)
    return pika.BlockingConnection(params)

def init_exchange(ch):
    ch.exchange_declare(exchange='packets', exchange_type='fanout', durable=False)

def pkt_to_dict(pkt):
    rec = {
        'ts': time.time(),
        'src': None, 'dst': None, 'proto': None,
        'src_port': None, 'dst_port': None, 'length': len(pkt), 'info': pkt.summary()
    }
    try:
        if IP in pkt:
            rec['src'] = pkt[IP].src
            rec['dst'] = pkt[IP].dst
            if TCP in pkt:
                rec['proto'] = 'TCP'
                rec['src_port'] = int(pkt[TCP].sport); rec['dst_port'] = int(pkt[TCP].dport)
            elif UDP in pkt:
                rec['proto'] = 'UDP'
                rec['src_port'] = int(pkt[UDP].sport); rec['dst_port'] = int(pkt[UDP].dport)
            elif ICMP in pkt:
                rec['proto'] = 'ICMP'
            else:
                rec['proto'] = str(pkt[IP].proto)
        elif IPv6 in pkt:
            rec['src'] = pkt[IPv6].src; rec['dst'] = pkt[IPv6].dst; rec['proto'] = 'IPv6'
        else:
            rec['proto'] = pkt.lastlayer().name if pkt.lastlayer() else 'OTHER'
    except Exception as e:
        rec['info'] += f' | parse_error={e}'
    return rec

def on_packet(pkt):
    try:
        d = pkt_to_dict(pkt)
        body = json.dumps(d)
        ch.basic_publish(exchange='packets', routing_key='', body=body)
    except Exception as e:
        print('publish error', e)

if __name__ == '__main__':
    print('[sniffer] starting, connecting to rabbitmq at', RABBIT_HOST)
    conn = make_conn()
    ch = conn.channel()
    init_exchange(ch)
    print('[sniffer] sniffing interface=', IFACE, 'filter=', BPF_FILTER)
    sniff(iface=None if IFACE=='any' else IFACE, filter=BPF_FILTER or None, store=False, prn=on_packet)
