"""
Prometheus metrics missing from the guardrails module.
Adds: preauth_guardrail_violations_total, preauth_quarantined_total
"""
# This file extends the existing metrics.py with guardrail-specific counters.
# Import from app.core.metrics to use.

# NOTE: These are already declared in metrics.py. This module is intentionally
# empty — it documents that guardrail metrics are in core/metrics.py.
