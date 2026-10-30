"""
Locust Load Testing Script (D6).
Tests the Pre-Authorization REST API with stub LLM for isolating system performance.

SLO Declarations (pre-test):
  - p95 end-to-end latency for POST /preauth: < 5 seconds
  - p95 end-to-end latency for GET /preauth/{id}: < 200ms
  - Error rate: < 1% under 20 concurrent users
  - Throughput target: > 5 RPS sustained

Usage:
  locust -f loadtest/locustfile.py --host=http://localhost:8000
  locust -f loadtest/locustfile.py --host=http://localhost:8000 --headless -u 20 -r 2 --run-time 120s
"""
from __future__ import annotations

import json
import random
import time
from datetime import date, timedelta

from locust import HttpUser, task, between, events
from locust.env import Environment

# ── SLO Declarations ─────────────────────────────────────────────────────────
SLO_P95_SUBMIT_MS = 5000   # 5 seconds
SLO_P95_POLL_MS = 200      # 200ms
SLO_ERROR_RATE = 0.01      # 1%
SLO_MIN_RPS = 5.0          # 5 RPS

# ── Test payload generator ────────────────────────────────────────────────────

POLICY_PREFIXES = ["SH", "SCHIP", "SHI"]
ICDCODES = ["H26.9", "K40.9", "N20.1", "M17.1", "K64.9", "H25.9", "I25.1"]
PROCEDURES = [
    "Phacoemulsification with IOL implantation",
    "Laparoscopic hernioplasty",
    "Ureteroscopy with laser lithotripsy",
    "Total knee replacement",
    "Haemorrhoidectomy",
    "CABG",
    "Arthroscopic meniscectomy",
]
ADMISSION_TYPES = ["day_care", "planned_surgical", "emergency", "maternity"]

def _random_date_str(days_ago_min: int = 0, days_ago_max: int = 365) -> str:
    delta = random.randint(days_ago_min, days_ago_max)
    d = date.today() - timedelta(days=delta)
    return d.isoformat()

def _build_payload(scenario: str = "random") -> dict:
    """Build a realistic pre-auth payload."""
    prefix = random.choice(POLICY_PREFIXES)
    policy_num = f"{prefix}-{random.randint(100000000, 999999999)}"
    patient_num = random.randint(1000, 999999)

    # Vary policy age to test different waiting period scenarios
    if scenario == "cataract_11mo":
        inception_days_ago = 335  # ~11 months
        icd = "H26.9"
        procedure = "Phacoemulsification with IOL implantation"
        admission_type = "day_care"
    elif scenario == "cataract_25mo":
        inception_days_ago = 760  # ~25 months
        icd = "H25.9"
        procedure = "Phacoemulsification with IOL implantation"
        admission_type = "day_care"
    elif scenario == "emergency":
        inception_days_ago = random.randint(10, 30)
        icd = "S72.9"
        procedure = "Open reduction internal fixation"
        admission_type = "emergency"
    else:
        inception_days_ago = random.randint(30, 1000)
        icd = random.choice(ICDCODES)
        procedure = random.choice(PROCEDURES)
        admission_type = random.choice(ADMISSION_TYPES)

    inception = date.today() - timedelta(days=inception_days_ago)
    expiry = inception + timedelta(days=365)
    admission_date = date.today().isoformat()

    return {
        "patient": {
            "patient_id": f"PAT-{patient_num:06d}",
            "full_name": f"Test Patient {patient_num}",
            "date_of_birth": "1970-01-01",
            "gender": random.choice(["male", "female"]),
            "age_at_admission": 54,
        },
        "policy": {
            "policy_number": policy_num,
            "policy_holder_name": f"Test Patient {patient_num}",
            "policy_inception_date": inception.isoformat(),
            "policy_expiry_date": expiry.isoformat(),
            "sum_insured_inr": random.choice([300000, 500000, 1000000]),
            "prior_claims_inr": 0,
        },
        "hospital": {
            "hospital_id": f"HOSP-{random.randint(1, 50):04d}",
            "hospital_name": f"Test Hospital {random.randint(1, 50)}",
            "is_network_hospital": random.choice([True, False]),
            "city": "Mumbai",
            "state": "Maharashtra",
        },
        "medical": {
            "primary_diagnosis": f"Test diagnosis for {procedure}",
            "icd10_code": icd,
            "procedure_name": procedure,
            "admission_date": admission_date,
            "expected_discharge_date": admission_date,
            "admission_type": admission_type,
            "estimated_cost_inr": random.randint(30000, 500000),
            "pre_existing_conditions": random.choices(
                ["Type 2 Diabetes", "Hypertension", ""],
                k=random.randint(0, 1)
            ) if random.random() > 0.6 else [],
            "treating_physician": f"Dr. Test Physician {random.randint(1, 20)}",
        },
    }


# ── User Classes ──────────────────────────────────────────────────────────────

class PreAuthUser(HttpUser):
    """Simulates a hospital insurance desk clerk submitting pre-auth requests."""
    wait_time = between(1, 3)
    run_ids: list[str] = []

    @task(5)
    def submit_random(self) -> None:
        payload = _build_payload("random")
        with self.client.post(
            "/api/v1/preauth",
            json=payload,
            name="/api/v1/preauth [POST]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 202:
                run_id = resp.json().get("run_id")
                if run_id:
                    self.run_ids.append(run_id)
                resp.success()
            elif resp.status_code == 429:
                resp.success()  # Rate limit expected under load
            else:
                resp.failure(f"Unexpected status: {resp.status_code}")

    @task(2)
    def submit_cataract_11mo(self) -> None:
        """Section 4.1 critical test case — should always get medical-review."""
        payload = _build_payload("cataract_11mo")
        with self.client.post(
            "/api/v1/preauth",
            json=payload,
            name="/api/v1/preauth [POST-cataract]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (202, 429):
                resp.success()
            else:
                resp.failure(f"Unexpected: {resp.status_code}")

    @task(3)
    def poll_status(self) -> None:
        if not self.run_ids:
            return
        run_id = random.choice(self.run_ids[-10:])  # Poll recent runs
        with self.client.get(
            f"/api/v1/preauth/{run_id}",
            name="/api/v1/preauth/{run_id} [GET]",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected: {resp.status_code}")

    @task(1)
    def check_health(self) -> None:
        self.client.get("/healthz", name="/healthz")

    @task(1)
    def submit_malformed(self) -> None:
        """Test boundary validation — should return 422, not crash."""
        with self.client.post(
            "/api/v1/preauth",
            json={"invalid": "payload", "missing": "all_required_fields"},
            name="/api/v1/preauth [POST-malformed]",
            catch_response=True,
        ) as resp:
            if resp.status_code == 422:
                resp.success()  # Expected — validation worked
            elif resp.status_code == 429:
                resp.success()
            else:
                resp.failure(f"Expected 422, got: {resp.status_code}")


class HeavyLoadUser(HttpUser):
    """Simulates burst load for stress testing."""
    wait_time = between(0.1, 0.5)

    @task
    def burst_submit(self) -> None:
        payload = _build_payload("emergency")
        self.client.post(
            "/api/v1/preauth",
            json=payload,
            name="/api/v1/preauth [BURST]",
        )


# ── SLO Check Hook ────────────────────────────────────────────────────────────

@events.quitting.add_listener
def on_locust_quit(environment: Environment, **kwargs):
    stats = environment.stats
    print("\n" + "="*60)
    print("SLO Verification Report")
    print("="*60)

    for name, stat in stats.entries.items():
        p95 = stat.get_response_time_percentile(0.95)
        error_rate = stat.fail_ratio

        if "POST" in str(name) and "malformed" not in str(name):
            slo_met = p95 <= SLO_P95_SUBMIT_MS
            print(f"\nEndpoint: {name}")
            print(f"  p95 latency: {p95:.0f}ms (SLO: {SLO_P95_SUBMIT_MS}ms) → {'✅ PASS' if slo_met else '❌ FAIL'}")
            print(f"  Error rate: {error_rate:.1%} (SLO: {SLO_ERROR_RATE:.1%}) → {'✅ PASS' if error_rate <= SLO_ERROR_RATE else '❌ FAIL'}")

    total_rps = stats.total.current_rps
    print(f"\nThroughput: {total_rps:.1f} RPS (SLO: {SLO_MIN_RPS} RPS) → {'✅ PASS' if total_rps >= SLO_MIN_RPS else '⚠️  CHECK'}")
    print("="*60)
