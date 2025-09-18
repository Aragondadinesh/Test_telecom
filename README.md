# Packet Capture Microservices (Scapy -> RabbitMQ -> Parser -> Postgres -> FastAPI -> React)
This reference project demonstrates a **microservices** approach to packet capture and protocol analysis. Services are decoupled via **RabbitMQ** (messaging) and **Postgres** (storage).

## Architecture (high level)
- **sniffer**: captures packets (Scapy) and publishes packet metadata as JSON to RabbitMQ (exchange `packets`).
- **parser**: consumes messages from RabbitMQ, performs deeper parsing/enrichment and inserts rows into Postgres.
- **postgres**: persistent storage for parsed packets.
- **backend**: FastAPI service that reads Postgres and exposes REST APIs for UI / automation.
- **frontend**: React single-page app (served static) that polls backend for packets and stats.
- **rabbitmq**: message broker decoupling capture from processing.

This design gives you microservices benefits: independent scaling (run multiple parsers), resilience (broker buffers bursts), and easier testing/CI.

## Quick start (Linux recommended)
1. Build and start everything (requires Docker Engine):
   ```bash
   docker compose up --build
   ```
   Notes:
   - The **sniffer** runs with `network_mode: host` and `privileged: true` so it can open raw sockets and capture host traffic — this works best on Linux hosts. If running on Mac/Windows, host networking doesn't behave the same; consider running the sniffer on the host machine (outside Docker) and point it at RabbitMQ. citeturn0search16turn0search4
   - RabbitMQ management UI: http://localhost:15672 (guest/guest)
   - Frontend: http://localhost:3000
   - Backend docs: http://localhost:8000/docs

2. Stop everything:
   ```bash
   docker compose down
   ```

## Why RabbitMQ (vs Kafka)?
- RabbitMQ is lightweight and easy to run in docker-compose for demos and supports flexible routing and many consumer patterns. Kafka is higher-throughput and more suitable for production-scale streaming pipelines, but is more complex to set up. Choose Kafka if you expect extremely high message rates and need retention/replay semantics. citeturn0search9turn0search13

## Security & operational notes
- Packet capture requires privileges; containerized capture typically requires `--privileged` or `--cap-add=NET_RAW --cap-add=NET_ADMIN` plus `--net=host`. Use caution — only run on networks you own or have permission to analyze. citeturn0search0turn0search16
- This demo uses Postgres for storage (more robust than SQLite when multiple parser workers run).
- Consider adding payload redaction, TLS inspection limitations, and RBAC/auth on the backend for production.

## Next improvements you can add
- Use Kafka if you need replay and very high throughput.
- Add flow reassembly and complete TCP stream reconstruction in parser workers.
- Add authentication, pagination, retention, and retention policies in the backend.
- Add observability (Prometheus + Grafana) and container healthchecks.

## File list
- docker-compose.yml
- sniffer/ (Dockerfile, capture.py)
- parser/ (Dockerfile, parser.py)
- backend/ (Dockerfile, app/main.py)
- frontend/ (Dockerfile, public/index.html)

Enjoy — download the ZIP and run locally (Linux recommended).
