"""
Pydantic schemas for pre-authorization request/response contracts.
Implements strict validation with field-level error detail (F1, F2, D1).
"""
from __future__ import annotations

import re
from datetime import date, datetime
from enum import Enum
from typing import Annotated, Any
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)


# ── Enumerations ─────────────────────────────────────────────────────────────

class AdmissionType(str, Enum):
    PLANNED_SURGICAL = "planned_surgical"
    DAY_CARE = "day_care"
    EMERGENCY = "emergency"
    MATERNITY = "maternity"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class OutcomeRoute(str, Enum):
    APPROVE_RECOMMENDED = "approve-recommended"
    QUERY_TO_HOSPITAL = "query-to-hospital"
    MEDICAL_REVIEW = "medical-review"


class RunStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


# ── Sub-models ───────────────────────────────────────────────────────────────

class PatientInfo(BaseModel):
    patient_id: Annotated[str, StringConstraints(pattern=r"^PAT-[A-Z0-9]{2,6}-?\d{4,12}$|^PAT-\d{6,12}$")] = Field(
        ..., description="Patient identifier e.g. PAT-000001 or PAT-HYD-001001"
    )
    full_name: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    date_of_birth: date = Field(..., description="Patient date of birth (YYYY-MM-DD)")
    gender: Gender
    age_at_admission: int = Field(..., ge=0, le=130)

    @model_validator(mode="after")
    def validate_age_consistency(self) -> "PatientInfo":
        today = date.today()
        calculated_age = (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )
        if abs(calculated_age - self.age_at_admission) > 1:
            raise ValueError(
                f"age_at_admission ({self.age_at_admission}) is inconsistent "
                f"with date_of_birth (calculated: {calculated_age})"
            )
        return self


class PolicyInfo(BaseModel):
    policy_number: Annotated[
        str, StringConstraints(pattern=r"^[A-Z]{2,6}-[A-Z0-9-]{3,20}$")
    ] = Field(..., description="Policy number e.g. SH-123456789 or SH-HYD-100001")
    policy_holder_name: Annotated[str, StringConstraints(min_length=2, max_length=120)]
    policy_inception_date: date = Field(..., description="Date policy was issued")
    policy_expiry_date: date
    sum_insured_inr: float = Field(..., gt=0, le=100_000_000)
    cumulative_bonus_inr: float = Field(default=0.0, ge=0)
    prior_claims_inr: float = Field(default=0.0, ge=0)

    @model_validator(mode="after")
    def validate_dates(self) -> "PolicyInfo":
        if self.policy_expiry_date <= self.policy_inception_date:
            raise ValueError("policy_expiry_date must be after policy_inception_date")
        return self

    @model_validator(mode="after")
    def validate_claims_within_limit(self) -> "PolicyInfo":
        if self.prior_claims_inr > self.sum_insured_inr + self.cumulative_bonus_inr:
            raise ValueError(
                "prior_claims_inr exceeds total coverage "
                f"({self.sum_insured_inr + self.cumulative_bonus_inr})"
            )
        return self

    @property
    def policy_age_months(self) -> int:
        today = date.today()
        months = (today.year - self.policy_inception_date.year) * 12 + (
            today.month - self.policy_inception_date.month
        )
        return max(months, 0)


class HospitalInfo(BaseModel):
    hospital_id: Annotated[str, StringConstraints(pattern=r"^HOSP-[A-Z0-9-]{2,15}$")]
    hospital_name: Annotated[str, StringConstraints(min_length=2, max_length=200)]
    rohini_id: str | None = Field(None, description="Rohini network ID if applicable")
    is_network_hospital: bool
    city: Annotated[str, StringConstraints(min_length=2, max_length=100)]
    state: Annotated[str, StringConstraints(min_length=2, max_length=100)]


class MedicalDetails(BaseModel):
    primary_diagnosis: Annotated[str, StringConstraints(min_length=3, max_length=300)]
    icd10_code: Annotated[
        str, StringConstraints(pattern=r"^[A-Z]\d{2}(\.\d{1,4})?$")
    ] = Field(..., description="ICD-10 diagnosis code e.g. H26.9")
    procedure_name: Annotated[str, StringConstraints(min_length=3, max_length=300)]
    procedure_code: str | None = Field(
        None, description="CPT or ICD procedure code if available"
    )
    admission_date: date
    expected_discharge_date: date
    admission_type: AdmissionType
    estimated_cost_inr: float = Field(..., gt=0, le=10_000_000)
    pre_existing_conditions: list[str] = Field(default_factory=list, max_length=20)
    treating_physician: Annotated[str, StringConstraints(min_length=2, max_length=120)]

    @model_validator(mode="after")
    def validate_admission_dates(self) -> "MedicalDetails":
        if self.expected_discharge_date < self.admission_date:
            raise ValueError(
                "expected_discharge_date must be >= admission_date"
            )
        days = (self.expected_discharge_date - self.admission_date).days
        if self.admission_type == AdmissionType.DAY_CARE and days > 1:
            raise ValueError(
                "Day-care procedures must have a stay <= 1 day"
            )
        return self

    @field_validator("pre_existing_conditions", mode="before")
    @classmethod
    def sanitize_pec(cls, v: Any) -> list[str]:
        if isinstance(v, list):
            cleaned = []
            for item in v:
                if not isinstance(item, str):
                    raise ValueError("Each pre-existing condition must be a string")
                item = item.strip()
                if len(item) > 200:
                    raise ValueError(
                        f"Pre-existing condition string too long: {item[:40]}..."
                    )
                cleaned.append(item)
            return cleaned
        return v


# ── Main request schema ───────────────────────────────────────────────────────

class PreAuthRequest(BaseModel):
    """
    Pre-authorization submission payload.
    All fields are strictly validated before any agent pipeline is triggered.
    """

    request_id: str = Field(
        default_factory=lambda: f"REQ-{uuid4().hex[:12].upper()}"
    )
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    patient: PatientInfo
    policy: PolicyInfo
    hospital: HospitalInfo
    medical: MedicalDetails

    callback_url: str | None = Field(
        None, description="Optional webhook URL for async completion notification"
    )
    free_text_notes: Annotated[
        str | None, StringConstraints(max_length=2000)
    ] = Field(None, description="Additional clinical notes (guardrail-scanned)")

    @field_validator("callback_url", mode="before")
    @classmethod
    def validate_callback_url(cls, v: Any) -> str | None:
        if v is None:
            return None
        pattern = re.compile(
            r"^https?://"
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"
            r"localhost|"
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
            r"(?::\d+)?(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        if not pattern.match(str(v)):
            raise ValueError("callback_url must be a valid HTTP/HTTPS URL")
        return str(v)

    class Config:
        json_schema_extra = {
            "example": {
                "patient": {
                    "patient_id": "PAT-000001",
                    "full_name": "Ramesh Kumar",
                    "date_of_birth": "1965-03-15",
                    "gender": "male",
                    "age_at_admission": 61,
                },
                "policy": {
                    "policy_number": "SH-123456789",
                    "policy_holder_name": "Ramesh Kumar",
                    "policy_inception_date": "2025-11-01",
                    "policy_expiry_date": "2026-10-31",
                    "sum_insured_inr": 500000,
                    "prior_claims_inr": 0,
                },
                "hospital": {
                    "hospital_id": "HOSP-0001",
                    "hospital_name": "Apollo Hospitals Chennai",
                    "is_network_hospital": True,
                    "city": "Chennai",
                    "state": "Tamil Nadu",
                },
                "medical": {
                    "primary_diagnosis": "Age-related cataract",
                    "icd10_code": "H26.9",
                    "procedure_name": "Phacoemulsification with IOL implantation",
                    "admission_date": "2026-10-30",
                    "expected_discharge_date": "2026-10-30",
                    "admission_type": "day_care",
                    "estimated_cost_inr": 75000,
                    "pre_existing_conditions": ["Type 2 Diabetes"],
                    "treating_physician": "Dr. Priya Venkat",
                },
            }
        }


# ── Response schemas ──────────────────────────────────────────────────────────

class ClauseCitation(BaseModel):
    clause_id: str
    clause_title: str
    excerpt: str
    source_document: str
    page_or_section: str | None = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    verified: bool = Field(default=False)


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: str = ""


class AgentStepLog(BaseModel):
    step_index: int
    agent_name: str
    action: str
    tool_called: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: str | None = None
    reasoning: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PreAuthResponse(BaseModel):
    run_id: str
    request_id: str
    status: RunStatus
    outcome: OutcomeRoute | None = None
    recommendation: str | None = None
    citations: list[ClauseCitation] = Field(default_factory=list)
    escalation_reason: str | None = None
    admission_type_classified: AdmissionType | None = None
    agent_steps: list[AgentStepLog] = Field(default_factory=list)
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    prompt_version: str = "v1"
    correlation_id: str = ""
    processing_time_ms: float | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class PreAuthSubmitResponse(BaseModel):
    run_id: str
    status: RunStatus = RunStatus.PENDING
    poll_url: str
    estimated_wait_s: int = 30
    correlation_id: str = ""


class FeedbackRequest(BaseModel):
    run_id: str
    satisfactory: bool
    reason: str | None = Field(None, max_length=1000)
    reviewer_id: str | None = Field(None, max_length=100)


class QuarantineRecord(BaseModel):
    request_id: str
    quarantined_at: datetime = Field(default_factory=datetime.utcnow)
    validation_errors: list[dict[str, Any]]
    raw_payload: dict[str, Any]
    correlation_id: str = ""
