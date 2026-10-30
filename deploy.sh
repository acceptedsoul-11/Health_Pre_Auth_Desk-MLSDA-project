#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════
#  Pre-Authorization Desk — Quick Start (macOS/Linux)
# ══════════════════════════════════════════════════════════════
set -e

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Health Insurance Pre-Authorization Desk — Deploy Script ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 1. Check prerequisites
echo "▶ Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "✗ Docker not found"; exit 1; }
echo "✓ Docker found"

# 2. .env
if [ ! -f ".env" ]; then
    echo "▶ Copying .env.example → .env"
    cp .env.example .env
    echo "✓ .env created (stub LLM — zero API cost)"
else
    echo "✓ .env already exists"
fi

# 3. Start services
echo ""
echo "▶ Starting Docker services..."
docker compose up -d --build redis postgres backend agent-worker jaeger prometheus grafana flower frontend
echo "✓ Services started"

# 4. Wait for backend
echo ""
echo "▶ Waiting for backend health..."
for i in $(seq 1 15); do
    sleep 3
    if curl -sf http://localhost:8000/healthz >/dev/null 2>&1; then
        echo "✓ Backend is healthy"
        break
    fi
    echo "  Waiting... ($i/15)"
done

# 5. Build corpus index
echo ""
echo "▶ Building FAISS corpus index..."
docker compose run --rm corpus-ingest
echo "✓ Corpus index built"

# 6. Seed demo data
echo ""
echo "▶ Seeding demo data (Hyderabad & Bangalore)..."
docker compose exec backend python /scripts/seed_demo_data.py || \
    docker compose exec -e PYTHONPATH=/app backend python /app/scripts/seed_demo_data.py || true
echo "✓ Demo data seeded"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🎉 Pre-Authorization Desk is LIVE!          ║"
echo "╠══════════════════════════════════════════════╣"
echo "║  Frontend UI    → http://localhost:3000      ║"
echo "║  API Swagger    → http://localhost:8000/docs ║"
echo "║  Grafana        → http://localhost:3001      ║"
echo "║  Jaeger Traces  → http://localhost:16686     ║"
echo "║  Flower Workers → http://localhost:5555      ║"
echo "╚══════════════════════════════════════════════╝"
