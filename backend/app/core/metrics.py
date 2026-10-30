"""
Prometheus metrics registry for the Pre-Authorization service.
Exports: request counts, latencies, agent step counts, token usage, throughput.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, Summary

# ── HTTP metrics ─────────────────────────────────────────────────────────────
http_requests_total = Counter(
    "preauth_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "preauth_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

# ── Agent / run metrics ───────────────────────────────────────────────────────
runs_submitted_total = Counter(
    "preauth_runs_submitted_total",
    "Total pre-auth runs submitted",
    ["admission_type"],
)

runs_completed_total = Counter(
    "preauth_runs_completed_total",
    "Total pre-auth runs completed",
    ["outcome", "prompt_version"],
)

runs_failed_total = Counter(
    "preauth_runs_failed_total",
    "Total pre-auth runs that failed",
    ["reason"],
)

run_duration_seconds = Histogram(
    "preauth_run_duration_seconds",
    "End-to-end run duration in seconds",
    ["outcome"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

agent_steps_total = Counter(
    "preauth_agent_steps_total",
    "Total agent steps executed",
    ["agent_name", "step_type"],
)

tool_calls_total = Counter(
    "preauth_tool_calls_total",
    "Total tool calls made by agents",
    ["tool_name", "status"],
)

# ── Token / cost metrics ─────────────────────────────────────────────────────
tokens_prompt_total = Counter(
    "preauth_tokens_prompt_total",
    "Total prompt tokens consumed",
    ["model"],
)

tokens_completion_total = Counter(
    "preauth_tokens_completion_total",
    "Total completion tokens consumed",
    ["model"],
)

llm_cost_usd_total = Counter(
    "preauth_llm_cost_usd_total",
    "Total LLM cost in USD",
    ["model"],
)

# ── Queue metrics ─────────────────────────────────────────────────────────────
queue_depth = Gauge(
    "preauth_queue_depth",
    "Current number of tasks in the queue",
)

# ── Circuit breaker metrics ───────────────────────────────────────────────────
circuit_breaker_state = Gauge(
    "preauth_circuit_breaker_state",
    "Circuit breaker state: 0=closed, 1=half_open, 2=open",
    ["breaker_name"],
)

# ── Corpus / index metrics ────────────────────────────────────────────────────
corpus_chunk_count = Gauge(
    "preauth_corpus_chunk_count",
    "Number of chunks indexed in the vector store",
)

corpus_last_build_timestamp = Gauge(
    "preauth_corpus_last_build_timestamp_seconds",
    "Unix timestamp of last corpus build",
)

# ── Evaluation metrics ────────────────────────────────────────────────────────
eval_groundedness = Gauge(
    "preauth_eval_groundedness",
    "Latest evaluation groundedness score",
    ["prompt_version"],
)

eval_faithfulness = Gauge(
    "preauth_eval_faithfulness",
    "Latest evaluation faithfulness score",
    ["prompt_version"],
)

eval_context_relevance = Gauge(
    "preauth_eval_context_relevance",
    "Latest evaluation context relevance score",
    ["prompt_version"],
)

# ── Security / guardrail metrics ──────────────────────────────────────────────
guardrail_violations_total = Counter(
    "preauth_guardrail_violations_total",
    "Total guardrail violations detected (injection, toxicity, output)",
    ["violation_type"],
)

quarantined_total = Counter(
    "preauth_quarantined_total",
    "Total requests quarantined by guardrails",
)

# ── Pipeline-level duration (for Grafana SLO panel) ──────────────────────────
pipeline_duration_seconds = Histogram(
    "preauth_pipeline_duration_seconds",
    "Agent pipeline execution duration in seconds",
    ["outcome", "prompt_version"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)
