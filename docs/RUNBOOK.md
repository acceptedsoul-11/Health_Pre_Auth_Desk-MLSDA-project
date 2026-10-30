# Operational Runbooks
## Health Insurance Pre-Authorization Desk

---

## Runbook 1 — LLM Provider Circuit Breaker Open

### Symptoms
- All `/api/v1/preauth` submissions complete immediately with `outcome: "medical-review"`
- Escalation reason contains: `"Circuit breaker 'llm_provider' is OPEN"`
- Prometheus metric `preauth_circuit_breaker_state{breaker_name="llm_provider"}` = 2
- Grafana shows `preauth_runs_failed_total` spike with `reason="circuit_breaker_open"`

### Confirmation Steps
```bash
# 1. Check circuit breaker state via API
curl http://localhost:8000/api/v1/admin/circuit-breaker-status
# Expected: {"llm_provider": {"state": "open", "failures": 5}}

# 2. Check LLM provider logs
docker compose logs agent-worker --tail 50 | grep "circuit_breaker"

# 3. Check provider-side status
# For OpenAI: https://status.openai.com
# For Ollama: curl http://localhost:11434/api/tags
```

### Recovery Procedure
```bash
# Option A — Wait for automatic recovery (CB_RECOVERY_TIMEOUT_S default: 60s)
# The breaker transitions OPEN → HALF-OPEN → CLOSED automatically.

# Option B — Manual reset (immediate)
curl -X DELETE http://localhost:8000/api/v1/admin/circuit-breaker/llm_provider/reset

# Option C — Switch to stub provider temporarily
# Edit .env: LLM_PROVIDER=stub
docker compose restart backend agent-worker

# Option D — Scale to more workers to dilute failures
docker compose --scale agent-worker=3 up -d
```

### Root Cause & Prevention
- **Root Cause**: LLM provider rate limit, timeout, or outage
- **Prevention**: Implement exponential backoff (already configured via `AGENT_RETRY_*` settings)
- **Monitor**: Set alert on `preauth_circuit_breaker_state > 1` in Grafana

---

## Runbook 2 — Redis Queue Backlog / Worker Stall

### Symptoms
- `/api/v1/preauth/{run_id}` returns `status: "pending"` for > 5 minutes
- Celery Flower UI (`http://localhost:5555`) shows tasks stuck in `RECEIVED` state
- `preauth_queue_depth` Prometheus gauge is increasing steadily
- No `preauth_runs_completed_total` increments in Grafana

### Confirmation Steps
```bash
# 1. Check worker health
docker compose ps agent-worker
docker compose logs agent-worker --tail 30

# 2. Check Redis connectivity from worker
docker compose exec agent-worker redis-cli -h redis -a ${REDIS_PASSWORD} ping

# 3. Check queue depth directly
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} LLEN celery

# 4. Check Flower for stalled workers
open http://localhost:5555

# 5. Check if workers are processing
docker compose exec agent-worker celery -A workers.tasks inspect active
```

### Recovery Procedure
```bash
# Step 1 — Restart stalled workers
docker compose restart agent-worker

# Step 2 — Scale workers to clear backlog
docker compose --scale agent-worker=3 up -d

# Step 3 — If Redis is corrupt, flush queue (CAUTION: discards pending tasks)
# WARNING: Only if workers are confirmed dead and tasks must be re-submitted
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} DEL celery

# Step 4 — Check Redis memory
docker compose exec redis redis-cli -a ${REDIS_PASSWORD} INFO memory
# If maxmemory exceeded: increase REDIS maxmemory in docker-compose.yml

# Step 5 — For persistent stall, restart full stack
docker compose down && docker compose up -d
```

### Root Cause & Prevention
- **Root Cause A**: Worker OOM killed — increase `resources.limits.memory` in docker-compose.yml
- **Root Cause B**: FAISS index loading too slow — pre-build index with `docker compose run corpus-ingest`
- **Root Cause C**: Redis maxmemory eviction — set `maxmemory-policy allkeys-lru` (already configured)
- **Prevention**: Alert on `preauth_queue_depth > 20` sustained for > 2 minutes

---

## Incident Log

### Incident #001 — 2024-10-30 — FAISS Index Not Found on Cold Start

**Severity**: Medium  
**Duration**: ~8 minutes  
**Discovery**: Health check `/readyz` returning `degraded` on first `docker compose up`

**Symptoms**:
- `vector_store_loaded` log line absent from backend startup
- All pre-auth responses returning `"Processing timed out"` immediately
- Backend logs showed: `INFO faiss_index_not_found path=/app/corpus/processed/faiss_index/index.faiss`

**Root Cause**:
The FAISS index is built at Docker image build time inside the `Dockerfile` via:
```
RUN python -c "from app.cli.ingest import main; ..."
```
However, this writes to `/app/corpus/processed/faiss_index` which is **overridden** by the named Docker volume `corpus_data` mounted at runtime. The volume was empty on first start, so the index was lost.

**Fix Applied**:
1. Added a `corpus-ingest` service in `docker-compose.yml` as a one-shot init container
2. Modified the backend to call `_build_in_memory()` as a fallback when index file not found
3. Added startup log: `"building_in_memory_index"` to distinguish fallback from loaded index

**Resolution**:
```bash
# Run the ingestion service once after first docker compose up
docker compose run --rm corpus-ingest

# Or use the --build flag to force rebuild
docker compose up --build -d
```

**Prevention**:
- Added `corpus-ingest` profile to docker-compose for explicit first-run
- Backend now has in-memory fallback that always works without a pre-built index
- Document `docker compose run corpus-ingest` as first-run step in README

---

## Scaling Reference

### Scale agent workers for throughput testing
```bash
docker compose --scale agent-worker=3 up -d
```

### Monitor scaling impact
```bash
# Watch throughput in real-time
watch -n 2 'curl -s http://localhost:9090/api/v1/query?query=rate\(preauth_runs_completed_total[1m]\)'

# Or use Grafana dashboard at http://localhost:3001
```

### Load test with Locust
```bash
pip install locust
cd loadtest
locust -f locustfile.py --host=http://localhost:8000 --headless \
  -u 20 -r 2 --run-time 120s --html=report.html
```
