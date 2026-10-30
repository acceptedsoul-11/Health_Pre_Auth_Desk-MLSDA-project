"""
Agent Tools — The three required tools available to LangGraph agents.
Each tool is a proper LangChain BaseTool with typed inputs and outputs.

Tools:
  1. corpus_search      — vector similarity retrieval
  2. lookup_clause_by_id — exact clause lookup
  3. lookup_request_fields — extract fields from the current pre-auth request
"""
from __future__ import annotations

import json
from typing import Any, Type

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.metrics import tool_calls_total

log = get_logger(__name__)


# ── Tool 1: Corpus Search ─────────────────────────────────────────────────────

class CorpusSearchInput(BaseModel):
    query: str = Field(
        ...,
        description=(
            "Natural language query to search the insurance policy corpus. "
            "Be specific about what clause or provision you are looking for."
        ),
    )
    top_k: int = Field(
        default=6,
        description="Number of top results to return (1-10)",
        ge=1,
        le=10,
    )


class CorpusSearchTool(BaseTool):
    """
    Search the Star Health Insurance Policy corpus using vector similarity.
    Returns relevant policy clauses with clause IDs, titles, and excerpts.
    Use this to find applicable coverage clauses, exclusions, and waiting periods.
    """

    name: str = "corpus_search"
    description: str = (
        "Search the Star Health Insurance Policy corpus for relevant clauses, "
        "exclusions, waiting periods, and coverage provisions. "
        "Returns clause IDs, titles, text excerpts, and relevance scores. "
        "Always search for BOTH general coverage AND specific disease/procedure waiting periods. "
        "Use multiple searches: one broad (e.g. 'cataract surgery coverage') and one specific "
        "(e.g. 'cataract 24 month waiting period specific disease')."
    )
    args_schema: Type[BaseModel] = CorpusSearchInput
    return_direct: bool = False

    def _run(self, query: str, top_k: int = 6) -> str:
        """Synchronous wrapper (required by BaseTool)."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._arun(query=query, top_k=top_k)
        )

    async def _arun(self, query: str, top_k: int = 6) -> str:
        from app.services.vector_store import get_vector_store
        try:
            store = get_vector_store()
            results = store.search(query=query, top_k=top_k)
            tool_calls_total.labels(tool_name="corpus_search", status="success").inc()
            log.info("tool_corpus_search", query=query[:80], results=len(results))

            output = []
            for i, r in enumerate(results, 1):
                output.append(
                    f"[{i}] clause_id={r.get('clause_id', 'N/A')} | "
                    f"score={r.get('relevance_score', 0):.3f}\n"
                    f"  title: {r.get('title', 'N/A')}\n"
                    f"  doc: {r.get('doc_title', 'N/A')} (page {r.get('page', '?')})\n"
                    f"  text: {r.get('text', '')[:600]}\n"
                )
            return "\n".join(output) if output else "No relevant clauses found."
        except Exception as exc:
            tool_calls_total.labels(tool_name="corpus_search", status="error").inc()
            log.error("tool_corpus_search_error", error=str(exc))
            return f"Error performing corpus search: {exc}"


# ── Tool 2: Lookup Clause by ID ───────────────────────────────────────────────

class LookupClauseInput(BaseModel):
    clause_id: str = Field(
        ...,
        description=(
            "The exact clause identifier to look up (e.g. 'SCHIP-WAIT-002', "
            "'SCHIP-COV-001', 'DCP-OPHTH-001'). Use corpus_search first to "
            "discover clause IDs, then use this tool for the full text."
        ),
    )


class LookupClauseTool(BaseTool):
    """
    Retrieve the full text of a specific policy clause by its identifier.
    Use after corpus_search to get complete clause text for citation verification.
    """

    name: str = "lookup_clause_by_id"
    description: str = (
        "Retrieve the complete text of a specific insurance policy clause by its "
        "clause_id. Use this to get the full clause for accurate citation and "
        "cross-referencing. Call this for every clause you intend to cite in your "
        "final recommendation to ensure groundedness."
    )
    args_schema: Type[BaseModel] = LookupClauseInput
    return_direct: bool = False

    def _run(self, clause_id: str) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._arun(clause_id=clause_id)
        )

    async def _arun(self, clause_id: str) -> str:
        from app.services.vector_store import get_vector_store
        try:
            store = get_vector_store()
            result = store.lookup_by_clause_id(clause_id)
            tool_calls_total.labels(tool_name="lookup_clause_by_id", status="success").inc()

            if result is None:
                log.warning("tool_lookup_clause_not_found", clause_id=clause_id)
                return (
                    f"Clause '{clause_id}' not found in the indexed corpus. "
                    "This procedure or provision may not be covered by the indexed policy, "
                    "or the clause_id may be incorrect. Consider escalating to medical review."
                )

            log.info("tool_lookup_clause", clause_id=clause_id, found=True)
            return (
                f"clause_id: {result.get('clause_id')}\n"
                f"title: {result.get('title')}\n"
                f"document: {result.get('doc_title')} (page {result.get('page', '?')})\n"
                f"source: {result.get('source')}\n"
                f"full_text:\n{result.get('text', '')}"
            )
        except Exception as exc:
            tool_calls_total.labels(tool_name="lookup_clause_by_id", status="error").inc()
            log.error("tool_lookup_clause_error", error=str(exc))
            return f"Error looking up clause: {exc}"


# ── Tool 3: Lookup Request Fields ─────────────────────────────────────────────

class LookupRequestFieldsInput(BaseModel):
    fields: list[str] = Field(
        ...,
        description=(
            "List of field names to extract from the pre-authorization request. "
            "Available fields: 'policy_age_months', 'admission_type', 'diagnosis', "
            "'icd10_code', 'procedure_name', 'estimated_cost_inr', 'sum_insured_inr', "
            "'pre_existing_conditions', 'patient_age', 'policy_number', 'hospital_name', "
            "'is_network_hospital', 'policy_inception_date', 'admission_date'."
        ),
    )


class LookupRequestFieldsTool(BaseTool):
    """
    Extract specific fields from the current pre-authorization request payload.
    Use this to retrieve patient demographics, policy details, and medical information
    needed for coverage evaluation.
    """

    name: str = "lookup_request_fields"
    description: str = (
        "Extract specific fields from the current pre-authorization request. "
        "Use to get policy age, diagnosis codes, procedure names, sum insured, "
        "pre-existing conditions, and other request attributes needed for coverage analysis."
    )
    args_schema: Type[BaseModel] = LookupRequestFieldsInput
    return_direct: bool = False

    # Injected at runtime
    request_context: dict[str, Any] = Field(default_factory=dict)

    def _run(self, fields: list[str]) -> str:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(fields=fields))

    async def _arun(self, fields: list[str]) -> str:
        try:
            ctx = self.request_context
            results = {}
            for field_name in fields:
                value = self._extract_field(field_name, ctx)
                results[field_name] = value

            tool_calls_total.labels(tool_name="lookup_request_fields", status="success").inc()
            log.info("tool_lookup_fields", fields=fields)
            return json.dumps(results, indent=2, default=str)
        except Exception as exc:
            tool_calls_total.labels(tool_name="lookup_request_fields", status="error").inc()
            log.error("tool_lookup_fields_error", error=str(exc))
            return f"Error extracting request fields: {exc}"

    def _extract_field(self, field_name: str, ctx: dict[str, Any]) -> Any:
        """Map field names to request context values."""
        policy = ctx.get("policy", {})
        patient = ctx.get("patient", {})
        medical = ctx.get("medical", {})
        hospital = ctx.get("hospital", {})

        mapping = {
            "policy_age_months": ctx.get("policy_age_months"),
            "admission_type": medical.get("admission_type"),
            "diagnosis": medical.get("primary_diagnosis"),
            "icd10_code": medical.get("icd10_code"),
            "procedure_name": medical.get("procedure_name"),
            "estimated_cost_inr": medical.get("estimated_cost_inr"),
            "sum_insured_inr": policy.get("sum_insured_inr"),
            "pre_existing_conditions": medical.get("pre_existing_conditions", []),
            "patient_age": patient.get("age_at_admission"),
            "policy_number": policy.get("policy_number"),
            "hospital_name": hospital.get("hospital_name"),
            "is_network_hospital": hospital.get("is_network_hospital"),
            "policy_inception_date": str(policy.get("policy_inception_date", "")),
            "admission_date": str(medical.get("admission_date", "")),
            "prior_claims_inr": policy.get("prior_claims_inr", 0),
            "cumulative_bonus_inr": policy.get("cumulative_bonus_inr", 0),
        }
        return mapping.get(field_name, f"<field '{field_name}' not available>")


def build_tools(request_context: dict[str, Any]) -> list[BaseTool]:
    """Build the complete tool set with injected request context."""
    return [
        CorpusSearchTool(),
        LookupClauseTool(),
        LookupRequestFieldsTool(request_context=request_context),
    ]
