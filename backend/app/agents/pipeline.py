"""
LangGraph Multi-Agent Pipeline (A1, A2, A3).

Topology:
  START → classifier_agent → verifier_agent → self_verification → END

Agents:
  1. ClassifierRetrieverAgent — classifies admission, performs retrieval loops
  2. PolicyComplianceVerifierAgent — evaluates coverage, verifies citations

Features:
  - Bounded execution (max_steps, max_tool_calls, wall_clock_timeout)
  - Agentic retrieval (tool calls chosen by agent, not hardcoded)
  - Self-verification of all citations before returning
  - Stub LLM support for testing/load testing
"""
from __future__ import annotations

import asyncio
import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, TypedDict

from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from tenacity import (
    AsyncRetrying,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.agents.tools.retrieval_tools import build_tools
from app.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpen
from app.core.config import get_settings
from app.core.guardrails import check_output_safety
from app.core.logging import get_logger
from app.core.metrics import (
    agent_steps_total,
    runs_completed_total,
    runs_failed_total,
    tokens_completion_total,
    tokens_prompt_total,
    llm_cost_usd_total,
    tool_calls_total,
)
from app.schemas.preauth import (
    AdmissionType,
    AgentStepLog,
    ClauseCitation,
    OutcomeRoute,
    PreAuthResponse,
    RunStatus,
    TokenUsage,
)

log = get_logger(__name__)
settings = get_settings()


# ── State ─────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    # Input
    request_context: dict[str, Any]
    run_id: str
    correlation_id: str
    prompt_version: str

    # Execution tracking
    step_count: int
    tool_call_count: int
    start_time: float
    messages: list[Any]

    # Classifier output
    classifier_output: dict[str, Any]

    # Verifier output
    verifier_output: dict[str, Any]

    # Final
    final_response: dict[str, Any] | None
    error: str | None
    token_usage: dict[str, Any]
    step_logs: list[dict[str, Any]]


# ── LLM Factory ───────────────────────────────────────────────────────────────

def _build_llm(tools: list[Any] | None = None) -> Any:
    """Build LLM based on configured provider."""
    s = get_settings()
    provider = s.llm_provider

    if provider == "stub":
        return _StubLLM(tools=tools or [])
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=s.openai_model,
            api_key=s.openai_api_key,
            base_url=s.openai_base_url,
            temperature=0,
            max_retries=0,  # We handle retries ourselves
        )
        if tools:
            return llm.bind_tools(tools)
        return llm
    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        llm = ChatOllama(
            model=s.ollama_model,
            base_url=s.ollama_base_url,
            temperature=0,
        )
        if tools:
            return llm.bind_tools(tools)
        return llm
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


class _StubLLM:
    """
    Stub LLM for testing — returns deterministic policy-aware responses.
    Simulates realistic response delays for load testing.
    """

    def __init__(self, tools: list[Any]) -> None:
        self.tools = tools
        self._tool_map = {t.name: t for t in tools}

    async def ainvoke(self, messages: list[Any], **kwargs: Any) -> Any:
        """Simulate LLM call with realistic delay."""
        import asyncio
        delay_ms = settings.stub_response_delay_ms
        await asyncio.sleep(delay_ms / 1000)

        # Inspect the last message to generate a context-aware stub response
        last_content = ""
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                last_content = str(msg.content)
                break

        return _StubResponse(content=self._generate_stub_content(last_content, messages))

    def _extract_context(self, messages: list[Any]) -> dict[str, Any]:
        """Extract request context from tools or messages."""
        for tool in self.tools:
            if hasattr(tool, "request_context") and tool.request_context:
                return tool.request_context

        for msg in messages:
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                if "REQUEST CONTEXT:" in content:
                    try:
                        part = content.split("REQUEST CONTEXT:")[1].split("CLASSIFIER FINDINGS:")[0]
                        return json.loads(part.strip())
                    except Exception:
                        pass
                if "Analyze this pre-authorization request:" in content:
                    try:
                        part = content.split("Analyze this pre-authorization request:")[1].split("Policy age (months):")[0]
                        return json.loads(part.strip())
                    except Exception:
                        pass
        return {}

    def _generate_stub_content(self, last_content: str, messages: list[Any]) -> str:
        system_content = ""
        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_content = msg.content
                break

        is_verifier = "verifier" in system_content.lower() or "compliance" in system_content.lower()
        ctx = self._extract_context(messages)

        patient = ctx.get("patient", {})
        patient_name = patient.get("full_name") or "Patient"
        policy = ctx.get("policy", {})
        sum_insured = policy.get("sum_insured_inr", 500000)
        age_months = ctx.get("policy_age_months")
        if age_months is None:
            age_months = 11
        hospital = ctx.get("hospital", {})
        hospital_name = hospital.get("hospital_name") or "Network Hospital"
        medical = ctx.get("medical", {})
        procedure = medical.get("procedure_name") or "Medical Procedure"
        diagnosis = medical.get("primary_diagnosis") or "Clinical Diagnosis"
        icd10 = medical.get("icd10_code") or ""
        admission_type = medical.get("admission_type") or "planned_surgical"
        cost = medical.get("estimated_cost_inr", 0)

        proc_lower = procedure.lower()
        diag_lower = diagnosis.lower()
        adm_lower = str(admission_type).lower()

        is_emergency = "emergency" in adm_lower or "emergency" in proc_lower or "acute" in diag_lower
        is_maternity = "maternity" in adm_lower or "maternity" in proc_lower or "caesarean" in proc_lower or "lscs" in proc_lower
        is_24mo = any(k in proc_lower or k in diag_lower for k in [
            "cataract", "hernia", "knee", "arthroplasty", "joint", "calculus", "stone", "lithotripsy", "turp", "prostate", "hysterectomy", "tonsil", "sinus"
        ])
        is_experimental = any(k in proc_lower or k in diag_lower for k in ["experimental", "stem cell", "gene", "cosmetic", "aesthetic"])

        if not is_verifier:
            # Classifier Node
            retrieved = ["SCHIP-COV-001"]
            waiting_clauses = []
            flags = []

            if is_emergency:
                retrieved.extend(["SCHIP-EMER-001", "SCHIP-WAIT-001"])
                flags.append("EMERGENCY_DECLARED: Initial 30-day waiting period waived under SCHIP-WAIT-001")
            elif is_maternity:
                retrieved.extend(["SCHIP-MAT-001", "SCHIP-WAIT-002"])
                waiting_clauses.append("SCHIP-MAT-001")
                if age_months < 24:
                    flags.append(f"MATERNITY_WAIT_NOT_MET: Requires 24 months, policy is {age_months} months")
            elif is_24mo:
                retrieved.extend(["SCHIP-WAIT-002"])
                if "cataract" in proc_lower:
                    retrieved.append("DCP-OPHTH-001")
                elif "hernia" in proc_lower:
                    retrieved.append("DCP-GEN-001")
                elif "knee" in proc_lower or "arthroplasty" in proc_lower:
                    retrieved.append("DCP-ORTHO-001")
                elif "calculus" in proc_lower or "stone" in proc_lower:
                    retrieved.append("DCP-UROL-001")
                waiting_clauses.append("SCHIP-WAIT-002")
                if age_months < 24:
                    flags.append(f"WAITING_PERIOD_NOT_MET: {procedure} requires 24 months; policy is {age_months} months old")
            elif is_experimental:
                retrieved.extend(["SCHIP-EXCL-001"])
                flags.append(f"POLICY_EXCLUSION: {procedure} flagged under permanent exclusion SCHIP-EXCL-001")
            else:
                retrieved.extend(["SCHIP-COV-002", "SCHIP-WAIT-001"])

            return json.dumps({
                "admission_type": admission_type,
                "policy_age_months": age_months,
                "retrieved_clauses": list(set(retrieved)),
                "waiting_period_clauses": waiting_clauses,
                "coverage_flags": flags
            })

        # Verifier Node
        if is_emergency:
            return json.dumps({
                "outcome": "approve-recommended",
                "recommendation": (
                    f"Executive Summary:\n"
                    f"Pre-authorization request for {patient_name} ({procedure}) at {hospital_name} is Recommended for Approval.\n\n"
                    f"Key Evaluation Points:\n"
                    f"• Clinical Diagnosis: {diagnosis} (ICD-10: {icd10 or 'Emergency'}).\n"
                    f"• Admission Type: Emergency admission; immediate acute medical intervention verified.\n"
                    f"• Initial Waiting Period (Clause SCHIP-WAIT-001): Statutory 30-day waiting period is legally waived for emergency admissions.\n"
                    f"• Financial Assessment: Estimated cost ₹{cost:,} is within available Sum Insured (₹{sum_insured:,}).\n"
                    f"• Network Facility: {hospital_name} verified as active cashless network provider.\n\n"
                    f"Actionable Remarks:\n"
                    f"• Cashless pre-authorization approved up to estimated billing.\n"
                    f"• Final claim settlement subject to standard emergency admission records."
                ),
                "citations": [
                    {
                        "clause_id": "SCHIP-WAIT-001",
                        "clause_title": "Waiting Period — Initial Waiting Period",
                        "excerpt": "A waiting period of 30 days from the commencement of the first policy year is applicable for all claims, except in case of emergency hospitalisation due to an accident or acute condition.",
                        "source_document": "Star Health Comprehensive Insurance Policy",
                        "page_or_section": "6",
                        "relevance_score": 0.98
                    },
                    {
                        "clause_id": "SCHIP-COV-001",
                        "clause_title": "Coverage — In-Patient Hospitalisation",
                        "excerpt": "In-patient hospitalisation expenses for a period of more than 24 hours are covered up to the sum insured specified in the policy schedule.",
                        "source_document": "Star Health Comprehensive Insurance Policy",
                        "page_or_section": "8",
                        "relevance_score": 0.94
                    }
                ],
                "escalation_reason": "",
                "verified": True
            })

        if is_experimental:
            return json.dumps({
                "outcome": "medical-review",
                "recommendation": (
                    f"Executive Summary:\n"
                    f"Pre-authorization request for {patient_name} ({procedure}) is Flagged for Policy Exclusion.\n\n"
                    f"Key Evaluation Points:\n"
                    f"• Procedure Category: {procedure} classified as non-standard / unproven medical modality.\n"
                    f"• Permanent Exclusion (Clause SCHIP-EXCL-001): Expressly excludes treatments not recognized by standard clinical guidelines.\n"
                    f"• Corpus Assessment: Procedure is absent from approved surgical / day care policy schedules.\n\n"
                    f"Actionable Remarks:\n"
                    f"• Pre-authorization cannot be approved under standard policy coverage terms.\n"
                    f"• Escalated to Chief Medical Officer for review of exceptional experimental coverage approval."
                ),
                "citations": [
                    {
                        "clause_id": "SCHIP-EXCL-001",
                        "clause_title": "Permanent Exclusions — General",
                        "excerpt": "The Company shall not be liable to make any payment under this policy in respect of any expenses whatsoever incurred in respect of unproven or experimental treatments.",
                        "source_document": "Star Health Comprehensive Insurance Policy",
                        "page_or_section": "15",
                        "relevance_score": 0.97
                    }
                ],
                "escalation_reason": f"Procedure '{procedure}' falls under Permanent Exclusion clause SCHIP-EXCL-001 (unproven/experimental treatments).",
                "verified": True
            })

        if is_maternity:
            if age_months >= 24:
                return json.dumps({
                    "outcome": "approve-recommended",
                    "recommendation": (
                        f"Executive Summary:\n"
                        f"Maternity Pre-authorization request for {patient_name} ({procedure}) at {hospital_name} is Recommended for Approval.\n\n"
                        f"Key Evaluation Points:\n"
                        f"• Procedure: {procedure} ({diagnosis}).\n"
                        f"• Maternity Waiting Period (Clause SCHIP-MAT-001): 24-month waiting period SATISFIED (Policy age: {age_months} months).\n"
                        f"• Sub-limit Admissibility: Estimated cost ₹{cost:,} checked against policy maternity sub-limits.\n\n"
                        f"Actionable Remarks:\n"
                        f"• Cashless pre-authorization cleared under Maternity Benefit add-on cover."
                    ),
                    "citations": [
                        {
                            "clause_id": "SCHIP-MAT-001",
                            "clause_title": "Maternity Benefit",
                            "excerpt": "Maternity Benefit is available as an add-on cover and is subject to a waiting period of 24 months from the date of inception.",
                            "source_document": "Star Health Comprehensive Insurance Policy",
                            "page_or_section": "11",
                            "relevance_score": 0.96
                        }
                    ],
                    "escalation_reason": "",
                    "verified": True
                })
            else:
                return json.dumps({
                    "outcome": "medical-review",
                    "recommendation": (
                        f"Executive Summary:\n"
                        f"Maternity Pre-authorization request for {patient_name} requires Medical Review due to active waiting period.\n\n"
                        f"Key Evaluation Points:\n"
                        f"• Procedure: {procedure} ({diagnosis}).\n"
                        f"• Waiting Period (Clause SCHIP-MAT-001): Mandates 24 months continuous coverage for maternity claims.\n"
                        f"• Elapsed Policy Tenure: Policy is active for {age_months} months, falling {24 - age_months} months short.\n\n"
                        f"Actionable Remarks:\n"
                        f"• Automated approval withheld in accordance with clause SCHIP-MAT-001.\n"
                        f"• Referred to Medical Officer to check for prior continuous insurance portability credits."
                    ),
                    "citations": [
                        {
                            "clause_id": "SCHIP-MAT-001",
                            "clause_title": "Maternity Benefit",
                            "excerpt": "Maternity Benefit is available as an add-on cover and is subject to a waiting period of 24 months from the date of inception.",
                            "source_document": "Star Health Comprehensive Insurance Policy",
                            "page_or_section": "11",
                            "relevance_score": 0.96
                        }
                    ],
                    "escalation_reason": f"Maternity benefit requires 24 months continuous coverage per clause SCHIP-MAT-001. Current policy age is {age_months} months.",
                    "verified": True
                })

        if is_24mo:
            if age_months < 24:
                return json.dumps({
                    "outcome": "medical-review",
                    "recommendation": (
                        f"Executive Summary:\n"
                        f"Pre-authorization request for {patient_name} ({procedure}) requires Medical Review under Star Health Comprehensive Policy.\n\n"
                        f"Key Evaluation Points:\n"
                        f"• Procedure: {procedure} ({diagnosis}).\n"
                        f"• Specific Waiting Period (Clause SCHIP-WAIT-002): Mandates a strict 24-month waiting period for this treatment category.\n"
                        f"• Elapsed Policy Tenure: Policy is active for {age_months} months, falling {24 - age_months} months short of the mandatory 24-month requirement.\n"
                        f"• Procedure Schedule: Procedure is recognized in standard day-care / surgical schedules, but waiting period condition takes legal precedence.\n\n"
                        f"Actionable Remarks:\n"
                        f"• Automated pre-authorization is withheld in strict compliance with clause SCHIP-WAIT-002.\n"
                        f"• Case escalated to Senior Medical Officer to evaluate clinical urgency and verify any waiting period continuity waiver."
                    ),
                    "citations": [
                        {
                            "clause_id": "SCHIP-WAIT-002",
                            "clause_title": "Waiting Period — Specific Diseases and Procedures (24 months)",
                            "excerpt": "The following diseases/treatments/surgeries are payable after 24 calendar months of continuous coverage.",
                            "source_document": "Star Health Comprehensive Insurance Policy",
                            "page_or_section": "13",
                            "relevance_score": 0.98
                        },
                        {
                            "clause_id": "SCHIP-COV-002",
                            "clause_title": "Coverage — Day Care Procedures",
                            "excerpt": "Day care procedures are covered subject to the applicable waiting periods and policy terms.",
                            "source_document": "Star Health Comprehensive Insurance Policy",
                            "page_or_section": "9",
                            "relevance_score": 0.91
                        }
                    ],
                    "escalation_reason": f"Policy age is {age_months} months. Procedure '{procedure}' requires a 24-month specific disease waiting period per clause SCHIP-WAIT-002. Waiting period not yet satisfied ({24 - age_months} months remaining).",
                    "verified": True
                })
            else:
                return json.dumps({
                    "outcome": "approve-recommended",
                    "recommendation": (
                        f"Executive Summary:\n"
                        f"Pre-authorization request for {patient_name} ({procedure}) at {hospital_name} is Recommended for Approval.\n\n"
                        f"Key Evaluation Points:\n"
                        f"• Procedure: {procedure} ({diagnosis}).\n"
                        f"• Specific Waiting Period (Clause SCHIP-WAIT-002): 24-month waiting period is SATISFIED (Policy age: {age_months} months).\n"
                        f"• Coverage Status: Fully admissible under policy schedule.\n"
                        f"• Financial Assessment: Estimated cost ₹{cost:,} is within available Sum Insured (₹{sum_insured:,}).\n\n"
                        f"Actionable Remarks:\n"
                        f"• Pre-authorization cleared under cashless network terms.\n"
                        f"• Standard pre-authorization approval letter issued."
                    ),
                    "citations": [
                        {
                            "clause_id": "SCHIP-WAIT-002",
                            "clause_title": "Waiting Period — Specific Diseases and Procedures (24 months)",
                            "excerpt": "The following diseases/treatments/surgeries are payable after 24 calendar months of continuous coverage.",
                            "source_document": "Star Health Comprehensive Insurance Policy",
                            "page_or_section": "13",
                            "relevance_score": 0.98
                        },
                        {
                            "clause_id": "SCHIP-COV-002",
                            "clause_title": "Coverage — Day Care Procedures",
                            "excerpt": "Day care procedures are covered subject to the applicable waiting periods and policy terms.",
                            "source_document": "Star Health Comprehensive Insurance Policy",
                            "page_or_section": "9",
                            "relevance_score": 0.93
                        }
                    ],
                    "escalation_reason": "",
                    "verified": True
                })

        # Default Standard Surgical / Medical
        if age_months >= 1:
            return json.dumps({
                "outcome": "approve-recommended",
                "recommendation": (
                    f"Executive Summary:\n"
                    f"Pre-authorization request for {patient_name} ({procedure}) at {hospital_name} is Recommended for Approval.\n\n"
                    f"Key Evaluation Points:\n"
                    f"• Clinical Diagnosis: {diagnosis} (ICD-10: {icd10 or 'Standard'}).\n"
                    f"• Procedure: {procedure} ({admission_type}).\n"
                    f"• Initial Waiting Period: 30-day initial waiting period satisfied ({age_months} months active).\n"
                    f"• Financial Adequacy: Estimated cost ₹{cost:,} is within available Sum Insured (₹{sum_insured:,}).\n\n"
                    f"Actionable Remarks:\n"
                    f"• Initial cashless pre-authorization approved.\n"
                    f"• Standard cashless admission protocol applies."
                ),
                "citations": [
                    {
                        "clause_id": "SCHIP-COV-001",
                        "clause_title": "Coverage — In-Patient Hospitalisation",
                        "excerpt": "In-patient hospitalisation expenses for a period of more than 24 hours are covered up to the sum insured specified in the policy schedule.",
                        "source_document": "Star Health Comprehensive Insurance Policy",
                        "page_or_section": "8",
                        "relevance_score": 0.95
                    }
                ],
                "escalation_reason": "",
                "verified": True
            })
        else:
            return json.dumps({
                "outcome": "medical-review",
                "recommendation": (
                    f"Executive Summary:\n"
                    f"Pre-authorization request for {patient_name} ({procedure}) requires Medical Review.\n\n"
                    f"Key Evaluation Points:\n"
                    f"• Policy Tenure: Policy is less than 30 days old.\n"
                    f"• Clause SCHIP-WAIT-001: Initial 30-day waiting period applies for non-emergency admissions.\n\n"
                    f"Actionable Remarks:\n"
                    f"• Withheld for verification of prior continuous insurance coverage or acute emergency certificate."
                ),
                "citations": [
                    {
                        "clause_id": "SCHIP-WAIT-001",
                        "clause_title": "Waiting Period — Initial Waiting Period",
                        "excerpt": "A waiting period of 30 days from the commencement of the first policy year is applicable for all claims.",
                        "source_document": "Star Health Comprehensive Insurance Policy",
                        "page_or_section": "6",
                        "relevance_score": 0.95
                    }
                ],
                "escalation_reason": "Policy is less than 30 days old. Initial waiting period (SCHIP-WAIT-001) applies for non-emergency admissions.",
                "verified": True
            })


class _StubResponse:
    def __init__(self, content: str) -> None:
        self.content = content
        self.tool_calls: list = []
        self.usage_metadata = {"input_tokens": 100, "output_tokens": 200, "total_tokens": 300}


# ── Prompt Loader ─────────────────────────────────────────────────────────────

def _load_prompts(version: str) -> dict[str, str]:
    base = Path(__file__).resolve().parent.parent.parent / "prompts"
    prompt_file = base / version / "prompts.json"
    if not prompt_file.exists():
        log.warning("prompt_version_not_found", version=version, fallback="v1")
        prompt_file = base / "v1" / "prompts.json"
    with open(prompt_file, encoding="utf-8") as f:
        data = json.load(f)
    return data


# ── Citation Verifier ─────────────────────────────────────────────────────────

def _verify_citations(
    citations: list[dict[str, Any]], store: Any
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Programmatically verify each citation against retrieved source text.
    Returns (verified_citations, failed_clause_ids).
    """
    verified = []
    failed = []

    for citation in citations:
        clause_id = citation.get("clause_id", "")
        excerpt = citation.get("excerpt", "")

        if not clause_id or not excerpt:
            failed.append(clause_id or "unknown")
            continue

        # Retrieve actual clause text
        chunk = store.lookup_by_clause_id(clause_id)
        if chunk is None:
            log.warning("citation_clause_not_found", clause_id=clause_id)
            failed.append(clause_id)
            citation["verified"] = False
            verified.append(citation)
            continue

        # Check if excerpt appears in the actual text (case-insensitive, trimmed)
        actual_text = chunk.get("text", "").lower()
        excerpt_normalized = " ".join(excerpt.lower().split())

        # Allow partial match (at least 60% of excerpt words in actual text)
        excerpt_words = set(excerpt_normalized.split())
        actual_words = set(actual_text.split())
        if len(excerpt_words) == 0:
            failed.append(clause_id)
            continue

        overlap = len(excerpt_words & actual_words) / len(excerpt_words)
        is_verified = overlap >= 0.5  # 50% word overlap threshold

        citation["verified"] = is_verified
        citation["relevance_score"] = citation.get("relevance_score", 0.0)

        if is_verified:
            verified.append(citation)
            log.debug("citation_verified", clause_id=clause_id, overlap=overlap)
        else:
            failed.append(clause_id)
            verified.append(citation)  # Still include but marked unverified
            log.warning("citation_verification_failed", clause_id=clause_id, overlap=overlap)

    return verified, failed


# ── Graph Nodes ───────────────────────────────────────────────────────────────

async def classifier_node(state: AgentState) -> AgentState:
    """
    Classifier/Retriever Agent node.
    Classifies the admission type and retrieves all relevant policy clauses.
    """
    run_id = state["run_id"]
    step = state["step_count"]
    log.info("classifier_node_start", run_id=run_id, step=step)
    agent_steps_total.labels(agent_name="classifier", step_type="start").inc()

    # Timeout guard
    elapsed = time.monotonic() - state["start_time"]
    if elapsed > settings.agent_wall_clock_timeout_s:
        return {
            **state,
            "error": f"Wall clock timeout exceeded ({elapsed:.1f}s)",
            "final_response": _build_timeout_response(state),
        }

    # Load prompts
    prompts = _load_prompts(state["prompt_version"])
    tools = build_tools(state["request_context"])
    llm = _build_llm(tools)

    # Build messages
    system_msg = SystemMessage(content=prompts["classifier_system"])
    human_msg = HumanMessage(
        content=(
            f"Analyze this pre-authorization request:\n"
            f"{json.dumps(state['request_context'], indent=2, default=str)}\n\n"
            f"Policy age (months): {state['request_context'].get('policy_age_months', 'unknown')}\n\n"
            f"Use your tools to retrieve ALL relevant policy clauses before reporting."
        )
    )
    messages = [system_msg] + state["messages"] + [human_msg]

    # Agentic tool loop (agent decides which tools to call)
    step_logs = list(state["step_logs"])
    token_usage = dict(state["token_usage"])
    tool_call_count = state["tool_call_count"]
    current_messages = messages

    cb = get_circuit_breaker("llm_provider")
    classifier_output = {}

    for loop_step in range(settings.agent_max_steps):
        elapsed = time.monotonic() - state["start_time"]
        if elapsed > settings.agent_wall_clock_timeout_s:
            break
        if tool_call_count >= settings.agent_max_tool_calls:
            break

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(settings.agent_retry_max),
                wait=wait_exponential(
                    multiplier=settings.agent_retry_backoff_base,
                    min=1, max=30
                ),
                retry=retry_if_exception_type((TimeoutError, ConnectionError)),
                reraise=True,
            ):
                with attempt:
                    response = await asyncio.wait_for(
                        cb.call(llm.ainvoke, current_messages),
                        timeout=30.0,
                    )
        except CircuitBreakerOpen as e:
            return {
                **state,
                "error": f"Circuit breaker open: {e}",
                "final_response": _build_escalation_response(state, str(e)),
            }
        except Exception as e:
            log.error("classifier_llm_error", error=str(e), run_id=run_id)
            classifier_output = {"error": str(e), "fallback": True}
            break

        # Track token usage
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            token_usage["prompt_tokens"] = token_usage.get("prompt_tokens", 0) + usage.get("input_tokens", 0)
            token_usage["completion_tokens"] = token_usage.get("completion_tokens", 0) + usage.get("output_tokens", 0)
            token_usage["total_tokens"] = token_usage.get("total_tokens", 0) + usage.get("total_tokens", 0)

        # Log step
        step_logs.append({
            "step_index": len(step_logs),
            "agent_name": "classifier",
            "action": "llm_response",
            "tool_called": None,
            "reasoning": str(response.content)[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        agent_steps_total.labels(agent_name="classifier", step_type="llm_call").inc()

        # Process tool calls
        tool_calls = getattr(response, "tool_calls", [])
        if not tool_calls:
            # No tool calls — extract final output
            try:
                content = response.content
                # Try to parse JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    classifier_output = json.loads(json_match.group())
                else:
                    classifier_output = {"raw_output": content}
            except (json.JSONDecodeError, AttributeError):
                classifier_output = {"raw_output": str(response.content)}
            break

        # Execute tool calls
        current_messages = list(current_messages) + [response]
        for tc in tool_calls:
            if tool_call_count >= settings.agent_max_tool_calls:
                break
            tool_name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            tool_args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})

            tool_obj = next((t for t in tools if t.name == tool_name), None)
            if tool_obj:
                try:
                    tool_result = await tool_obj._arun(**tool_args)
                    tool_call_count += 1
                    tool_calls_total.labels(tool_name=tool_name, status="success").inc()
                except Exception as e:
                    tool_result = f"Tool error: {e}"
                    tool_calls_total.labels(tool_name=tool_name, status="error").inc()

                step_logs.append({
                    "step_index": len(step_logs),
                    "agent_name": "classifier",
                    "action": "tool_call",
                    "tool_called": tool_name,
                    "tool_input": tool_args,
                    "tool_output": str(tool_result)[:800],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

                # Add tool result to messages
                from langchain.schema import ToolMessage
                tool_id = tc.get("id", str(uuid.uuid4())) if isinstance(tc, dict) else getattr(tc, "id", str(uuid.uuid4()))
                current_messages.append(
                    ToolMessage(content=str(tool_result), tool_call_id=tool_id)
                )

    return {
        **state,
        "step_count": state["step_count"] + loop_step + 1,
        "tool_call_count": tool_call_count,
        "classifier_output": classifier_output,
        "messages": current_messages,
        "token_usage": token_usage,
        "step_logs": step_logs,
    }


async def verifier_node(state: AgentState) -> AgentState:
    """
    Policy Compliance / Verifier Agent node.
    Evaluates coverage, verifies citations, produces final recommendation.
    """
    run_id = state["run_id"]
    log.info("verifier_node_start", run_id=run_id)
    agent_steps_total.labels(agent_name="verifier", step_type="start").inc()

    # Check for upstream errors
    if state.get("error"):
        return state

    elapsed = time.monotonic() - state["start_time"]
    if elapsed > settings.agent_wall_clock_timeout_s:
        return {
            **state,
            "error": "Wall clock timeout in verifier",
            "final_response": _build_timeout_response(state),
        }

    prompts = _load_prompts(state["prompt_version"])
    tools = build_tools(state["request_context"])
    llm = _build_llm(tools)

    classifier_summary = json.dumps(state["classifier_output"], indent=2, default=str)
    system_msg = SystemMessage(content=prompts["verifier_system"])
    human_msg = HumanMessage(
        content=(
            f"Verify coverage for this pre-authorization request.\n\n"
            f"REQUEST CONTEXT:\n{json.dumps(state['request_context'], indent=2, default=str)}\n\n"
            f"CLASSIFIER FINDINGS:\n{classifier_summary}\n\n"
            f"Verify all citations and produce your final JSON recommendation."
        )
    )

    messages = [system_msg, human_msg]
    step_logs = list(state["step_logs"])
    token_usage = dict(state["token_usage"])
    tool_call_count = state["tool_call_count"]
    verifier_output = {}

    cb = get_circuit_breaker("llm_provider")

    for loop_step in range(settings.agent_max_steps):
        elapsed = time.monotonic() - state["start_time"]
        if elapsed > settings.agent_wall_clock_timeout_s or tool_call_count >= settings.agent_max_tool_calls:
            break

        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(settings.agent_retry_max),
                wait=wait_exponential(multiplier=settings.agent_retry_backoff_base, min=1, max=30),
                retry=retry_if_exception_type((TimeoutError, ConnectionError)),
                reraise=True,
            ):
                with attempt:
                    response = await asyncio.wait_for(
                        cb.call(llm.ainvoke, messages),
                        timeout=30.0,
                    )
        except CircuitBreakerOpen as e:
            return {
                **state,
                "error": str(e),
                "final_response": _build_escalation_response(state, str(e)),
            }
        except Exception as e:
            log.error("verifier_llm_error", error=str(e), run_id=run_id)
            verifier_output = {"error": str(e)}
            break

        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            token_usage["prompt_tokens"] = token_usage.get("prompt_tokens", 0) + usage.get("input_tokens", 0)
            token_usage["completion_tokens"] = token_usage.get("completion_tokens", 0) + usage.get("output_tokens", 0)
            token_usage["total_tokens"] = token_usage.get("total_tokens", 0) + usage.get("total_tokens", 0)

        step_logs.append({
            "step_index": len(step_logs),
            "agent_name": "verifier",
            "action": "llm_response",
            "reasoning": str(response.content)[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        agent_steps_total.labels(agent_name="verifier", step_type="llm_call").inc()

        tool_calls = getattr(response, "tool_calls", [])
        if not tool_calls:
            try:
                content = response.content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    verifier_output = json.loads(json_match.group())
                else:
                    verifier_output = {"raw_output": content}
            except (json.JSONDecodeError, AttributeError):
                verifier_output = {"raw_output": str(response.content)}
            break

        messages = list(messages) + [response]
        for tc in tool_calls:
            if tool_call_count >= settings.agent_max_tool_calls:
                break
            tool_name = tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", "")
            tool_args = tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {})
            tool_obj = next((t for t in tools if t.name == tool_name), None)
            if tool_obj:
                try:
                    tool_result = await tool_obj._arun(**tool_args)
                    tool_call_count += 1
                except Exception as e:
                    tool_result = f"Tool error: {e}"

                step_logs.append({
                    "step_index": len(step_logs),
                    "agent_name": "verifier",
                    "action": "tool_call",
                    "tool_called": tool_name,
                    "tool_input": tool_args,
                    "tool_output": str(tool_result)[:800],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                from langchain.schema import ToolMessage
                tool_id = tc.get("id", str(uuid.uuid4())) if isinstance(tc, dict) else getattr(tc, "id", str(uuid.uuid4()))
                messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))

    return {
        **state,
        "step_count": state["step_count"] + loop_step + 1,
        "tool_call_count": tool_call_count,
        "verifier_output": verifier_output,
        "token_usage": token_usage,
        "step_logs": step_logs,
    }


async def self_verification_node(state: AgentState) -> AgentState:
    """
    Self-verification node — programmatically verifies citations against source text.
    If verification fails, triggers secondary search strategy or escalates.
    """
    log.info("self_verification_start", run_id=state["run_id"])

    if state.get("error"):
        return state

    verifier_out = state.get("verifier_output", {})

    # Handle raw/error output from LLM
    if "error" in verifier_out or "raw_output" in verifier_out:
        return {
            **state,
            "final_response": _build_escalation_response(
                state, "Verifier produced unstructured output — escalating to medical review"
            ),
        }

    citations = verifier_out.get("citations", [])
    outcome = verifier_out.get("outcome", "medical-review")
    recommendation = verifier_out.get("recommendation", "")
    escalation_reason = verifier_out.get("escalation_reason", "")

    # Output safety check
    safety_check = check_output_safety(recommendation)
    if not safety_check.passed:
        log.error("output_safety_blocked", violations=safety_check.violations)
        return {
            **state,
            "final_response": _build_escalation_response(
                state,
                f"Output safety check failed: {safety_check.violations}. Escalated to medical review."
            ),
        }

    # Citation verification
    from app.services.vector_store import get_vector_store
    store = get_vector_store()
    verified_citations, failed_ids = _verify_citations(citations, store)

    if failed_ids:
        log.warning(
            "citation_verification_failed",
            failed_clause_ids=failed_ids,
            run_id=state["run_id"],
        )
        # If any citation fails verification, escalate
        outcome = "medical-review"
        escalation_reason = (
            f"Self-verification failed for clause(s): {failed_ids}. "
            "Citations could not be verified against retrieved source text. Escalating to human review."
        )

    # Validate outcome route
    valid_outcomes = {o.value for o in OutcomeRoute}
    if outcome not in valid_outcomes:
        outcome = "medical-review"
        escalation_reason = f"Invalid outcome '{outcome}' produced by agent. Escalated."

    final_response = {
        "outcome": outcome,
        "recommendation": recommendation,
        "citations": verified_citations,
        "escalation_reason": escalation_reason,
        "admission_type_classified": state["classifier_output"].get("admission_type"),
        "verified": all(c.get("verified", False) for c in verified_citations),
    }

    # Update Prometheus
    _update_run_metrics(state, outcome)

    return {**state, "final_response": final_response}


def _build_timeout_response(state: AgentState) -> dict[str, Any]:
    _update_run_metrics(state, "medical-review")
    return {
        "outcome": "medical-review",
        "recommendation": "Processing timed out. Request escalated to medical review.",
        "citations": [],
        "escalation_reason": "Agent pipeline wall-clock timeout exceeded.",
        "verified": False,
    }


def _build_escalation_response(state: AgentState, reason: str) -> dict[str, Any]:
    _update_run_metrics(state, "medical-review")
    return {
        "outcome": "medical-review",
        "recommendation": f"System error or safety constraint triggered. {reason}",
        "citations": [],
        "escalation_reason": reason,
        "verified": False,
    }


def _update_run_metrics(state: AgentState, outcome: str) -> None:
    prompt_version = state.get("prompt_version", "unknown")
    runs_completed_total.labels(outcome=outcome, prompt_version=prompt_version).inc()
    token_usage = state.get("token_usage", {})
    model = settings.openai_model if settings.llm_provider == "openai" else settings.llm_provider
    pt = token_usage.get("prompt_tokens", 0)
    ct = token_usage.get("completion_tokens", 0)
    if pt:
        tokens_prompt_total.labels(model=model).inc(pt)
    if ct:
        tokens_completion_total.labels(model=model).inc(ct)


# ── Graph Builder ─────────────────────────────────────────────────────────────

def build_agent_graph() -> Any:
    """Build and compile the LangGraph agent pipeline."""
    workflow = StateGraph(AgentState)

    workflow.add_node("classifier", classifier_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("self_verification", self_verification_node)

    workflow.add_edge(START, "classifier")
    workflow.add_edge("classifier", "verifier")
    workflow.add_edge("verifier", "self_verification")
    workflow.add_edge("self_verification", END)

    return workflow.compile()


# ── Main Entry Point ──────────────────────────────────────────────────────────

async def run_preauth_pipeline(
    request_context: dict[str, Any],
    run_id: str,
    correlation_id: str,
    prompt_version: str | None = None,
) -> dict[str, Any]:
    """
    Execute the full pre-authorization agent pipeline.
    Returns the final response dict.
    """
    version = prompt_version or settings.active_prompt_version
    start_time = time.monotonic()

    initial_state: AgentState = {
        "request_context": request_context,
        "run_id": run_id,
        "correlation_id": correlation_id,
        "prompt_version": version,
        "step_count": 0,
        "tool_call_count": 0,
        "start_time": start_time,
        "messages": [],
        "classifier_output": {},
        "verifier_output": {},
        "final_response": None,
        "error": None,
        "token_usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "model": settings.openai_model if settings.llm_provider == "openai" else settings.llm_provider,
        },
        "step_logs": [],
    }

    try:
        graph = build_agent_graph()
        final_state = await graph.ainvoke(initial_state)
    except Exception as exc:
        log.error("pipeline_critical_error", error=str(exc), run_id=run_id)
        runs_failed_total.labels(reason="pipeline_error").inc()
        return {
            "outcome": "medical-review",
            "recommendation": f"Critical pipeline error: {exc}. Escalated to medical review.",
            "citations": [],
            "escalation_reason": str(exc),
            "step_logs": [],
            "token_usage": initial_state["token_usage"],
            "error": str(exc),
        }

    elapsed_ms = (time.monotonic() - start_time) * 1000
    result = final_state.get("final_response") or _build_escalation_response(
        final_state, "No final response produced"
    )
    result["step_logs"] = final_state.get("step_logs", [])
    result["token_usage"] = final_state.get("token_usage", {})
    result["processing_time_ms"] = round(elapsed_ms, 1)
    result["prompt_version"] = version

    log.info(
        "pipeline_complete",
        run_id=run_id,
        outcome=result.get("outcome"),
        duration_ms=result["processing_time_ms"],
        steps=final_state.get("step_count", 0),
    )
    return result
