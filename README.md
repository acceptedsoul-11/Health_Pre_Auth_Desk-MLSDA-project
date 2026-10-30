# Health Insurance Pre-Authorization Desk

## Contributors
-PES1UG24AM240
-PES1UG24AM241
-PES1UG24AM251
-PES1UG24AM251

An asynchronous multi-agent pre-authorization service for synthetic health-insurance requests. The system validates a request, retrieves relevant policy clauses, verifies the recommendation, and routes the case to approve-recommended, query-to-hospital, or medical-review.

The system never authorizes an admission automatically. It produces a cited coverage recommendation for a medical officer to review.
<img width="1915" height="932" alt="image" src="https://github.com/user-attachments/assets/4734998f-763f-4041-bda8-a1d506b89f1e" />

# NOTE:(A live demo video will be made available soon,post review.)
## 1. Application overview

| Component | Purpose | URL |
|---|---|---|
| React frontend | Submit requests, view results, and browse seeded records | http://localhost:3000 |
| FastAPI backend | REST API and validation | http://localhost:8000 |
| Swagger UI | Interactive API documentation | http://localhost:8000/api/docs |
| Redis | Queue, fast status polling, and temporary result cache | localhost:6379 |
| PostgreSQL | Durable live run history and feedback when available | localhost:5432 |
| Flower | Celery worker/task monitoring | http://localhost:5555 |
| Prometheus | Metrics collection | http://localhost:9090 |
| Grafana | Performance/operations dashboards | http://localhost:3001 |
| Jaeger | OpenTelemetry trace viewer | http://localhost:16686 |

## 2. Architecture

~~~text
React/Vite frontend
       |
       | POST /api/v1/preauth
       v
FastAPI backend ---------------------- PostgreSQL
       |                                  |
       | Redis/Celery queue                | durable RUN-* history
       v                                  | feedback
Celery agent worker                      |
       |                                  |
       +-- LangGraph pipeline ------------+
           |-- Classifier agent
           |-- Verifier agent
           |-- Self-verification
           |-- FAISS policy retrieval

Prometheus <----- backend / worker metrics
Grafana    <----- Prometheus
Jaeger     <----- OpenTelemetry traces
Flower     <----- Celery worker/task events
~~~

## 3. Prerequisites

- Docker Desktop with the Linux engine running
- Docker Compose v2
- A browser
- At least 6 GB of free memory for the backend, embeddings, databases, and monitoring services

The recommended demo path uses Docker. The backend image installs the Python dependencies and local embedding model.

## 4. First-time Docker setup

Open PowerShell in the project folder:

~~~powershell
cd C:\Users\saira\OneDrive\Desktop\MLSDA_mini
~~~

Create .env only if it does not already exist:

~~~powershell
Copy-Item .env.example .env
~~~

Build and start the complete stack. Use --build after dependency changes, including Flower changes:

~~~powershell
docker compose up -d --build
~~~

Check service state:

~~~powershell
docker compose ps
~~~

Build or refresh the policy index once:

~~~powershell
docker compose run --rm corpus-ingest
~~~

Seed the original 20 dashboard showcase records:

~~~powershell
docker compose exec backend python /app/scripts/seed_demo_data.py
~~~

Open the application:

~~~powershell
Start-Process http://localhost:3000
~~~

## 5. Normal application demo

1. Open http://localhost:3000.
2. Use the Submit page.
3. Enter synthetic patient, policy, hospital, and medical information.
4. Click Submit Pre-Authorization Request.
5. The application returns a RUN-* identifier and opens the live status page.
6. Wait for pending or processing to become completed or failed.
7. Review the recommendation, escalation path, citations, agent steps, and token information.

The Track Status menu lets you revisit a request by Run ID. The Live Records page is reserved for the seeded DEMO-* examples.

<!-- Screenshot slot: docs/screenshots/01-submit-page.png and docs/screenshots/02-live-status-result.png -->

## 6. Manual sample data

Use MANUAL_DEMO_GUIDE.txt for 50 additional synthetic samples. It contains copy/paste PowerShell blocks for submitting one sample at a time.

These records are not inserted into the dashboard seed. Each submitted sample receives its own live RUN-* ID and status page.

<!-- Screenshot slot: docs/screenshots/03-live-records-dashboard.png -->

## 7. Critical cataract demonstration

The reference case is planned cataract surgery under a policy approximately 11 months old. The system must find both the general coverage clause and the separate 24-month waiting-period clause, then route the request to medical review.

~~~powershell
$body = @'
{
  "request_id": "REQ-CATARACT-11MO",
  "patient": {"patient_id": "PAT-000001", "full_name": "Ramesh Kumar", "date_of_birth": "1965-03-15", "gender": "male", "age_at_admission": 61},
  "policy": {"policy_number": "SH-123456789", "policy_holder_name": "Ramesh Kumar", "policy_inception_date": "2025-11-15", "policy_expiry_date": "2026-11-14", "sum_insured_inr": 500000, "prior_claims_inr": 0},
  "hospital": {"hospital_id": "HOSP-0001", "hospital_name": "Apollo Hospitals Chennai", "is_network_hospital": true, "city": "Chennai", "state": "Tamil Nadu"},
  "medical": {"primary_diagnosis": "Age-related cataract", "icd10_code": "H26.9", "procedure_name": "Phacoemulsification with IOL implantation", "admission_date": "2026-10-30", "expected_discharge_date": "2026-10-30", "admission_type": "day_care", "estimated_cost_inr": 75000, "pre_existing_conditions": ["Type 2 Diabetes"], "treating_physician": "Dr. Priya Venkat"}
}
'@

$response = Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/preauth -ContentType "application/json" -Body $body
$response | ConvertTo-Json -Depth 10
~~~

Expected outcome: medical-review, with citation SCHIP-WAIT-002.

For the dedicated Section 4.1 browser demonstration, open:

http://localhost:3000/demo

<!-- Screenshot slot: docs/screenshots/04-cataract-critical-case.png -->

## 8. Data storage and request history

When PostgreSQL is available, a live request is inserted into preauth_runs before it is queued. The worker updates it through:

~~~text
pending -> processing -> completed
                         or failed
~~~

The durable row contains the request payload, route, recommendation, escalation reason, citations, agent steps, token usage, prompt version, processing time, and completion time. Reviewer feedback is stored in preauth_feedback.

Redis remains the fast queue/status layer. If PostgreSQL is temporarily unavailable, the request still runs and remains available through Redis for its configured cache lifetime; the backend logs a warning.

The frontend Dashboard reads only DEMO-* records. A manually entered Mumbai or other hospital request is a RUN-* record shown on its status page, not in Live Records.

<!-- Screenshot slot: docs/screenshots/05-feedback-panel.png -->

## 9. Flower worker monitoring

Flower is installed as flower==2.0.1 in the backend image. After dependency changes, rebuild it:

~~~powershell
docker compose up -d --build flower
~~~

Open http://localhost:5555 to see Celery workers, active tasks, and task states.

View container logs:

~~~powershell
docker compose logs -f flower
docker compose logs -f agent-worker
docker compose logs -f backend
~~~

Application logs are structured and emitted to Docker stdout. They are not written to local .log files by default.

<!-- Screenshot slot: docs/screenshots/06-flower-workers.png -->

## 10. Grafana and Prometheus performance metrics

Open http://localhost:3001 and navigate to:

~~~text
Dashboards -> Browse -> Pre-Authorization -> Pre-Authorization Desk — Operations
~~~

The dashboard contains panels for throughput, p50/p95 latency, circuit-breaker state, queue depth, error rate, outcomes, agent tool-call rate, and security events.

The Prometheus datasource is provisioned with UID prometheus, matching the dashboard panels. If Grafana says Datasource prometheus was not found, run:

~~~powershell
docker compose up -d --force-recreate grafana
~~~

Then refresh Grafana. Wait 15–30 seconds after starting services or submitting a request for metrics to appear.

Useful endpoints:

- Prometheus targets: http://localhost:9090/targets
- Backend metrics: http://localhost:8000/metrics
- Backend readiness: http://localhost:8000/readyz

<!-- Screenshot slot: docs/screenshots/07-grafana-operations.png and docs/screenshots/08-prometheus-targets.png -->

## 11. Jaeger traces

Open http://localhost:16686, select preauth-backend or preauth-worker, and search after submitting a request. Use the Run ID or correlation ID to connect a trace to the status page and logs.

<!-- Screenshot slot: docs/screenshots/09-jaeger-trace.png -->

## 12. API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /api/v1/preauth | Validate and queue a request |
| GET | /api/v1/preauth/{run_id} | Poll a live result |
| POST | /api/v1/feedback | Submit reviewer feedback |
| GET | /api/v1/feedback/{run_id} | Read feedback |
| GET | /api/v1/demo-runs | Read seeded records only |
| GET | /api/v1/hospitals | Read hospital master data |
| GET | /healthz | Basic health |
| GET | /readyz | Redis, PostgreSQL, and vector-store readiness |
| GET | /metrics | Prometheus metrics |

OpenAPI JSON: http://localhost:8000/api/openapi.json.

## 13. Evaluation suite

The fixed evaluation set contains more than 20 scenarios, including the critical cataract case.

~~~powershell
docker compose exec backend python -m app.cli.evaluate --prompt-version v1
docker compose exec backend python -m app.cli.evaluate --compare
docker compose exec backend python -m app.cli.evaluate --scenario-id EVAL-001-CATARACT-11MO
~~~

## 14. Load testing

The Locust script is in loadtest/locustfile.py.

~~~powershell
pip install locust
cd loadtest
locust -f locustfile.py --host=http://localhost:8000 --headless -u 20 -r 2 --run-time 120s --html=locust_report.html
~~~

Targets:

- Complete run p95 below 5 seconds under the declared test profile
- Status lookup p95 below 200 ms
- Error rate below 1% at 20 concurrent users
  

## 16. Stop and reset commands

Stop containers while keeping volumes:

~~~powershell
docker compose stop
~~~

Remove containers and network while keeping volumes:

~~~powershell
docker compose down
~~~

Full reset. This removes Redis, PostgreSQL, Grafana, Prometheus, and corpus volumes:

~~~powershell
docker compose down -v
~~~

Use down -v only when you intentionally want to clear stored run history, feedback, seeded records, and monitoring history.

## 17. Troubleshooting

Check service state and logs:

~~~powershell
docker compose ps
docker compose logs --tail=100 backend agent-worker flower postgres redis
~~~

If Flower refuses the connection:

~~~powershell
docker compose up -d --build flower
docker compose logs --tail=100 flower
~~~

If Grafana cannot find Prometheus:

~~~powershell
docker compose up -d --force-recreate grafana
~~~

If the frontend opens but API calls fail:

~~~powershell
Invoke-RestMethod http://localhost:8000/healthz
Invoke-RestMethod http://localhost:8000/readyz
~~~

If PostgreSQL is unavailable, live requests still run through Redis/Celery. New runs are persisted to PostgreSQL again once it is healthy.

## 18. Local frontend/backend development

Docker Compose is recommended because it supplies Redis, PostgreSQL, the worker, Flower, Prometheus, Grafana, and Jaeger consistently. For frontend/backend iteration:

~~~powershell
# Terminal 1: dependency services
docker compose up -d redis postgres

# Terminal 2: backend
cd backend
pip install -r requirements.txt
python -m app.cli.ingest --force-rebuild
uvicorn app.main:app --reload --port 8000

# Terminal 3: Celery worker
cd backend
celery -A workers.tasks worker --loglevel=info --queues=preauth

# Terminal 4: frontend
cd frontend
npm install
npm run dev
~~~

The Vite frontend is normally at http://localhost:5173 in this mode.

## 19. Repository structure

~~~text
MLSDA_mini/
├── backend/
│   ├── app/agents/           # LangGraph agents and retrieval tools
│   ├── app/api/v1/           # FastAPI endpoints
│   ├── app/cli/              # Corpus ingest and evaluation CLIs
│   ├── app/core/             # Settings, logging, metrics, guardrails
│   ├── app/db/               # SQLAlchemy models and DB setup
│   ├── app/services/         # Cache, vector store, durable persistence
│   ├── prompts/v1/, v2/      # Versioned prompt artifacts
│   ├── workers/tasks.py      # Celery tasks
│   ├── requirements.txt      # Python dependencies, including Flower
│   └── Dockerfile
├── corpus/                   # Policy corpus and generated index data
├── frontend/                 # React/Vite application
├── infra/grafana/            # Dashboards and datasource provisioning
├── infra/prometheus/         # Prometheus scrape configuration
├── loadtest/                 # Locust scenarios
├── scripts/init_db.sql       # PostgreSQL schema
├── scripts/seed_demo_data.py # Original DEMO-* dashboard records
├── docs/RUNBOOK.md           # Operational runbook
├── MANUAL_DEMO_GUIDE.txt     # 50 manual live samples and commands
├── docker-compose.yml
└── .env.example
~~~

