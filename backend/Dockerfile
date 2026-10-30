FROM python:3.11-slim

LABEL maintainer="MLSDA Team"
LABEL description="Health Insurance Pre-Authorization Desk — Backend"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download embedding model at build time (zero API cost)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Ensure corpus directories exist
RUN mkdir -p /app/corpus/processed/faiss_index

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Build corpus index from synthetic corpus on image build
RUN python -c "\
import sys; sys.path.insert(0, '/app'); \
from app.cli.ingest import main; \
from click.testing import CliRunner; \
runner = CliRunner(); \
result = runner.invoke(main, ['--force-rebuild']); \
print(result.output)" || true

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
