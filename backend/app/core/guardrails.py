"""
Guardrails: prompt injection defense, toxicity filtering, output safety.
Applied to all free-text input fields before agent pipeline runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

# ── Injection attack patterns ────────────────────────────────────────────────
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"forget\s+(everything|all)",
        r"you\s+are\s+(now\s+)?(a\s+)?(?:an?\s+)?(?:evil|malicious|different|new)",
        r"jailbreak",
        r"dan\s+mode",
        r"developer\s+mode",
        r"system\s*:\s*",
        r"<\s*system\s*>",
        r"<\s*/?\s*prompt\s*>",
        r"\[\[.{0,80}\]\]",   # double bracket commands
        r"disregard\s+(your\s+)?(?:ethics|guidelines|rules|training)",
        r"pretend\s+(you\s+are|to\s+be)",
        r"roleplay\s+as",
        r"override\s+(safety|guardrails)",
        r"print\s+(your\s+)?system\s+prompt",
        r"reveal\s+(your\s+)?(prompt|instructions|context)",
        r"exfiltrate",
        r"base64\s+decode",
        r"eval\s*\(",
        r"exec\s*\(",
    ]
]

# ── Unauthorized determination patterns (output filter) ──────────────────────
_UNAUTHORIZED_OUTPUT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"\b(I\s+)?approve\s+this\s+claim\b",
        r"\bclaim\s+is\s+(hereby\s+)?approved\b",
        r"\bauthori[sz]ed\s+for\s+payment\b",
        r"\bpayment\s+approved\b",
        r"\bsettle\s+this\s+claim\b",
        r"\bimmediately\s+approve\b",
    ]
]

# ── Simple toxicity word list (production: use a model) ──────────────────────
_TOXIC_TERMS: frozenset[str] = frozenset(
    {
        "fraud", "bribe", "corrupt", "fake", "forged", "fabricated",
        "scam", "cheat", "lie", "illegal",
    }
)


@dataclass
class GuardrailResult:
    passed: bool
    violations: list[str] = field(default_factory=list)


def check_injection(text: str | None) -> GuardrailResult:
    """Detect prompt injection attempts in free-text fields."""
    if not text:
        return GuardrailResult(passed=True)
    violations: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            violations.append(
                f"Potential injection attempt detected: '{match.group()[:60]}'"
            )
    passed = len(violations) == 0
    if not passed:
        log.warning("injection_attempt_detected", violations=violations)
    return GuardrailResult(passed=passed, violations=violations)


def check_toxicity(text: str | None, threshold: float | None = None) -> GuardrailResult:
    """Lightweight toxicity check. In production, swap for a model-based detector."""
    if not text:
        return GuardrailResult(passed=True)
    settings = get_settings()
    threshold = threshold or settings.toxicity_threshold
    text_lower = text.lower()
    found = [t for t in _TOXIC_TERMS if t in text_lower]
    # Simple heuristic: proportion of toxic terms vs total words
    word_count = max(len(text_lower.split()), 1)
    score = len(found) / word_count
    passed = score < threshold
    violations = (
        [f"Toxicity score {score:.2f} exceeded threshold {threshold:.2f}: {found}"]
        if not passed
        else []
    )
    if not passed:
        log.warning("toxicity_detected", score=score, terms=found)
    return GuardrailResult(passed=passed, violations=violations)


def check_output_safety(text: str) -> GuardrailResult:
    """Prevent unauthorized approval determinations in agent outputs."""
    violations: list[str] = []
    for pattern in _UNAUTHORIZED_OUTPUT_PATTERNS:
        match = pattern.search(text)
        if match:
            violations.append(
                f"Unauthorized determination phrase detected: '{match.group()[:80]}'"
            )
    passed = len(violations) == 0
    if not passed:
        log.error("unauthorized_output_blocked", violations=violations)
    return GuardrailResult(passed=passed, violations=violations)


def run_all_input_guardrails(
    free_text: str | None,
    *,
    skip_toxicity: bool = False,
) -> GuardrailResult:
    """Run the complete input guardrail chain and emit Prometheus metrics."""
    settings = get_settings()
    all_violations: list[str] = []

    if settings.enable_injection_defense:
        inj = check_injection(free_text)
        if not inj.passed:
            try:
                from app.core.metrics import guardrail_violations_total
                guardrail_violations_total.labels(violation_type="injection").inc()
            except Exception:
                pass
        all_violations.extend(inj.violations)

    if settings.enable_toxicity_filter and not skip_toxicity:
        tox = check_toxicity(free_text)
        if not tox.passed:
            try:
                from app.core.metrics import guardrail_violations_total
                guardrail_violations_total.labels(violation_type="toxicity").inc()
            except Exception:
                pass
        all_violations.extend(tox.violations)

    passed = len(all_violations) == 0
    if not passed:
        try:
            from app.core.metrics import quarantined_total
            quarantined_total.inc()
        except Exception:
            pass

    return GuardrailResult(passed=passed, violations=all_violations)
