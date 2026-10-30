"""
Synthetic Data Seeder — Hospitals in Hyderabad & Bangalore + Policy Numbers.
Populates Redis with pre-loaded demo runs for immediate live usage.
Run: python scripts/seed_demo_data.py
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

HYDERABAD_HOSPITALS = [
    {"hospital_id": "HOSP-HYD-001", "hospital_name": "Apollo Hospitals Jubilee Hills", "rohini_id": "ROH-HYD-10001", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-002", "hospital_name": "Yashoda Hospitals Somajiguda", "rohini_id": "ROH-HYD-10002", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-003", "hospital_name": "KIMS Hospital Secunderabad", "rohini_id": "ROH-HYD-10003", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-004", "hospital_name": "Care Hospitals Banjara Hills", "rohini_id": "ROH-HYD-10004", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-005", "hospital_name": "Star Hospitals Nanakramguda", "rohini_id": "ROH-HYD-10005", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-006", "hospital_name": "Fernandez Hospital Bogulkunta", "rohini_id": "ROH-HYD-10006", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-007", "hospital_name": "Gleneagles Global Hospitals LB Nagar", "rohini_id": "ROH-HYD-10007", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-008", "hospital_name": "Medicover Hospitals Hitec City", "rohini_id": "ROH-HYD-10008", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-009", "hospital_name": "Basavatarakam Cancer Hospital", "rohini_id": None, "is_network_hospital": False, "city": "Hyderabad", "state": "Telangana"},
    {"hospital_id": "HOSP-HYD-010", "hospital_name": "Nizam's Institute of Medical Sciences (NIMS)", "rohini_id": "ROH-HYD-10010", "is_network_hospital": True, "city": "Hyderabad", "state": "Telangana"},
]

BANGALORE_HOSPITALS = [
    {"hospital_id": "HOSP-BLR-001", "hospital_name": "Manipal Hospital Old Airport Road", "rohini_id": "ROH-BLR-20001", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-002", "hospital_name": "Narayana Health City Bommasandra", "rohini_id": "ROH-BLR-20002", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-003", "hospital_name": "Fortis Hospital Bannerghatta Road", "rohini_id": "ROH-BLR-20003", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-004", "hospital_name": "Columbia Asia Hospital Hebbal", "rohini_id": "ROH-BLR-20004", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-005", "hospital_name": "Aster CMI Hospital Hebbal", "rohini_id": "ROH-BLR-20005", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-006", "hospital_name": "BGS Gleneagles Global Hospital Kengeri", "rohini_id": "ROH-BLR-20006", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-007", "hospital_name": "Sakra World Hospital Devarabisanahalli", "rohini_id": "ROH-BLR-20007", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-008", "hospital_name": "Sparsh Hospital Infantry Road", "rohini_id": "ROH-BLR-20008", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-009", "hospital_name": "NIMHANS Hosur Road", "rohini_id": None, "is_network_hospital": False, "city": "Bangalore", "state": "Karnataka"},
    {"hospital_id": "HOSP-BLR-010", "hospital_name": "St. John's Medical College Hospital", "rohini_id": "ROH-BLR-20010", "is_network_hospital": True, "city": "Bangalore", "state": "Karnataka"},
]

ALL_HOSPITALS = HYDERABAD_HOSPITALS + BANGALORE_HOSPITALS

# ── Synthetic Patient & Policy Records ───────────────────────────────────────

DEMO_RECORDS: list[dict[str, Any]] = [
    # ── Hyderabad Records ────────────────────────────────────────────────────
    {
        "record_id": "DEMO-HYD-001",
        "label": "Cataract (11mo) — Apollo Jubilee Hills [CRITICAL TEST]",
        "patient": {
            "patient_id": "PAT-HYD-001001",
            "full_name": "Ramachandra Rao",
            "date_of_birth": "1958-04-10",
            "gender": "male",
            "age_at_admission": 68,
        },
        "policy": {
            "policy_number": "SH-HYD-100001",
            "policy_holder_name": "Ramachandra Rao",
            "policy_inception_date": (date.today() - timedelta(days=335)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=30)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[0],
        "medical": {
            "primary_diagnosis": "Age-related nuclear cataract",
            "icd10_code": "H26.9",
            "procedure_name": "Phacoemulsification with IOL implantation",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 78000,
            "pre_existing_conditions": ["Type 2 Diabetes Mellitus"],
            "treating_physician": "Dr. Sudhir Rao, MS Ophthalmology",
        },
        "expected_outcome": "medical-review",
        "note": "Section 4.1 — 11-month policy, cataract 24-month wait not met",
    },
    {
        "record_id": "DEMO-HYD-002",
        "label": "Knee Replacement — Yashoda Somajiguda",
        "patient": {
            "patient_id": "PAT-HYD-001002",
            "full_name": "Vijayalakshmi Reddy",
            "date_of_birth": "1955-09-22",
            "gender": "female",
            "age_at_admission": 71,
        },
        "policy": {
            "policy_number": "SH-HYD-100002",
            "policy_holder_name": "Vijayalakshmi Reddy",
            "policy_inception_date": (date.today() - timedelta(days=900)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=100)).isoformat(),
            "sum_insured_inr": 1000000,
            "cumulative_bonus_inr": 100000,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[1],
        "medical": {
            "primary_diagnosis": "Osteoarthritis of bilateral knee",
            "icd10_code": "M17.0",
            "procedure_name": "Total knee arthroplasty right knee",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=7)).isoformat(),
            "admission_type": "planned_surgical",
            "estimated_cost_inr": 420000,
            "pre_existing_conditions": ["Hypertension", "Type 2 Diabetes"],
            "treating_physician": "Dr. Ravi Shankar, MS Ortho FRCS",
        },
        "expected_outcome": "medical-review",
        "note": "Joint replacement — 24-month wait met (30 months). PED diabetes/hypertension — 48-month wait met.",
    },
    {
        "record_id": "DEMO-HYD-003",
        "label": "Emergency Appendicitis — KIMS Secunderabad",
        "patient": {
            "patient_id": "PAT-HYD-001003",
            "full_name": "Mohammed Irfan",
            "date_of_birth": "1995-12-15",
            "gender": "male",
            "age_at_admission": 30,
        },
        "policy": {
            "policy_number": "SH-HYD-100003",
            "policy_holder_name": "Mohammed Irfan",
            "policy_inception_date": (date.today() - timedelta(days=20)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=345)).isoformat(),
            "sum_insured_inr": 300000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[2],
        "medical": {
            "primary_diagnosis": "Acute appendicitis with perforation",
            "icd10_code": "K35.2",
            "procedure_name": "Emergency appendicectomy",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=3)).isoformat(),
            "admission_type": "emergency",
            "estimated_cost_inr": 65000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Ashok Kumar, MS General Surgery",
        },
        "expected_outcome": "approve-recommended",
        "note": "Emergency — initial waiting period waived. No specific wait for appendicectomy.",
    },
    {
        "record_id": "DEMO-HYD-004",
        "label": "Laparoscopic Hernia — Care Hospitals Banjara Hills",
        "patient": {
            "patient_id": "PAT-HYD-001004",
            "full_name": "Srinivas Goud",
            "date_of_birth": "1972-06-30",
            "gender": "male",
            "age_at_admission": 54,
        },
        "policy": {
            "policy_number": "SH-HYD-100004",
            "policy_holder_name": "Srinivas Goud",
            "policy_inception_date": (date.today() - timedelta(days=550)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=180)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[3],
        "medical": {
            "primary_diagnosis": "Right inguinal hernia",
            "icd10_code": "K40.9",
            "procedure_name": "Laparoscopic Total Extra-Peritoneal (TEP) hernia repair",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 95000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Praveen Reddy, MS General Surgery",
        },
        "expected_outcome": "medical-review",
        "note": "Hernia — 24-month wait NOT met (18 months). Escalate.",
    },
    {
        "record_id": "DEMO-HYD-005",
        "label": "Cataract (26mo) — Star Hospitals Nanakramguda",
        "patient": {
            "patient_id": "PAT-HYD-001005",
            "full_name": "Pushpalatha Devi",
            "date_of_birth": "1950-02-14",
            "gender": "female",
            "age_at_admission": 76,
        },
        "policy": {
            "policy_number": "SH-HYD-100005",
            "policy_holder_name": "Pushpalatha Devi",
            "policy_inception_date": (date.today() - timedelta(days=790)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=200)).isoformat(),
            "sum_insured_inr": 1000000,
            "cumulative_bonus_inr": 50000,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[4],
        "medical": {
            "primary_diagnosis": "Senile cataract both eyes",
            "icd10_code": "H25.9",
            "procedure_name": "Bilateral phacoemulsification with IOL",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 140000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Venugopal, DNB Ophthalmology",
        },
        "expected_outcome": "approve-recommended",
        "note": "Cataract — 24-month wait SATISFIED (26 months). Approve.",
    },
    {
        "record_id": "DEMO-HYD-006",
        "label": "Maternity Caesarean — Fernandez Hospital",
        "patient": {
            "patient_id": "PAT-HYD-001006",
            "full_name": "Anuradha Sharma",
            "date_of_birth": "1993-07-28",
            "gender": "female",
            "age_at_admission": 33,
        },
        "policy": {
            "policy_number": "SH-HYD-100006",
            "policy_holder_name": "Anuradha Sharma",
            "policy_inception_date": (date.today() - timedelta(days=760)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=240)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[5],
        "medical": {
            "primary_diagnosis": "Term pregnancy with previous LSCS",
            "icd10_code": "O34.2",
            "procedure_name": "Elective Lower Segment Caesarean Section (LSCS)",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=4)).isoformat(),
            "admission_type": "maternity",
            "estimated_cost_inr": 180000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Shailaja Rao, MD OBG",
        },
        "expected_outcome": "approve-recommended",
        "note": "Maternity — 24-month wait met (25 months). Approve.",
    },
    {
        "record_id": "DEMO-HYD-007",
        "label": "TURP (BPH) — Gleneagles LB Nagar",
        "patient": {
            "patient_id": "PAT-HYD-001007",
            "full_name": "Narahari Prasad",
            "date_of_birth": "1953-11-05",
            "gender": "male",
            "age_at_admission": 73,
        },
        "policy": {
            "policy_number": "SH-HYD-100007",
            "policy_holder_name": "Narahari Prasad",
            "policy_inception_date": (date.today() - timedelta(days=1100)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=120)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 25000,
            "prior_claims_inr": 45000,
        },
        "hospital": HYDERABAD_HOSPITALS[6],
        "medical": {
            "primary_diagnosis": "Benign Prostatic Hypertrophy with LUTS",
            "icd10_code": "N40.1",
            "procedure_name": "Transurethral Resection of Prostate (TURP)",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=3)).isoformat(),
            "admission_type": "planned_surgical",
            "estimated_cost_inr": 110000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Suresh Babu, MCh Urology",
        },
        "expected_outcome": "approve-recommended",
        "note": "BPH TURP — 24-month wait met (36 months). Sum insured sufficient after prior claims.",
    },
    {
        "record_id": "DEMO-HYD-008",
        "label": "Diabetic Retinopathy Laser — Medicover Hitec City",
        "patient": {
            "patient_id": "PAT-HYD-001008",
            "full_name": "Krishnaiah Naidu",
            "date_of_birth": "1965-08-18",
            "gender": "male",
            "age_at_admission": 61,
        },
        "policy": {
            "policy_number": "SH-HYD-100008",
            "policy_holder_name": "Krishnaiah Naidu",
            "policy_inception_date": (date.today() - timedelta(days=1500)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=200)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 120000,
        },
        "hospital": HYDERABAD_HOSPITALS[7],
        "medical": {
            "primary_diagnosis": "Proliferative diabetic retinopathy",
            "icd10_code": "H36.0",
            "procedure_name": "Pan-retinal photocoagulation laser",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 35000,
            "pre_existing_conditions": ["Type 2 Diabetes Mellitus (12 years)"],
            "treating_physician": "Dr. Anand Kumar, FRCS Ophthalmology",
        },
        "expected_outcome": "approve-recommended",
        "note": "PED diabetes — 48-month wait met (50 months). Laser PRP covered.",
    },
    {
        "record_id": "DEMO-HYD-009",
        "label": "Kidney Stone ESWL — NIMS Hyderabad",
        "patient": {
            "patient_id": "PAT-HYD-001009",
            "full_name": "Padma Latha",
            "date_of_birth": "1975-03-25",
            "gender": "female",
            "age_at_admission": 51,
        },
        "policy": {
            "policy_number": "SH-HYD-100009",
            "policy_holder_name": "Padma Latha",
            "policy_inception_date": (date.today() - timedelta(days=400)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=250)).isoformat(),
            "sum_insured_inr": 300000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[9],
        "medical": {
            "primary_diagnosis": "Right ureteric calculus 8mm",
            "icd10_code": "N20.1",
            "procedure_name": "Extracorporeal Shock Wave Lithotripsy (ESWL)",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 28000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Rammohan, MS MCh Urology",
        },
        "expected_outcome": "medical-review",
        "note": "Kidney stone — 24-month wait NOT met (13 months). Escalate.",
    },
    {
        "record_id": "DEMO-HYD-010",
        "label": "CABG Cardiac Surgery — Apollo Jubilee Hills",
        "patient": {
            "patient_id": "PAT-HYD-001010",
            "full_name": "Raghavendran Iyer",
            "date_of_birth": "1960-01-14",
            "gender": "male",
            "age_at_admission": 66,
        },
        "policy": {
            "policy_number": "SH-HYD-100010",
            "policy_holder_name": "Raghavendran Iyer",
            "policy_inception_date": (date.today() - timedelta(days=1200)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=165)).isoformat(),
            "sum_insured_inr": 2000000,
            "cumulative_bonus_inr": 200000,
            "prior_claims_inr": 0,
        },
        "hospital": HYDERABAD_HOSPITALS[0],
        "medical": {
            "primary_diagnosis": "Triple vessel coronary artery disease",
            "icd10_code": "I25.1",
            "procedure_name": "Coronary Artery Bypass Grafting (CABG x3)",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=10)).isoformat(),
            "admission_type": "planned_surgical",
            "estimated_cost_inr": 950000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Ravi Mohan, MCh CTVS",
        },
        "expected_outcome": "approve-recommended",
        "note": "CABG — no specific wait, 30-day initial wait met. Large sum insured sufficient.",
    },
    # ── Bangalore Records ─────────────────────────────────────────────────────
    {
        "record_id": "DEMO-BLR-001",
        "label": "Arthroscopy Knee — Manipal Old Airport Rd",
        "patient": {
            "patient_id": "PAT-BLR-002001",
            "full_name": "Manjunath Swamy",
            "date_of_birth": "1985-06-10",
            "gender": "male",
            "age_at_admission": 41,
        },
        "policy": {
            "policy_number": "SH-BLR-200001",
            "policy_holder_name": "Manjunath Swamy",
            "policy_inception_date": (date.today() - timedelta(days=900)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=170)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 50000,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[0],
        "medical": {
            "primary_diagnosis": "Medial meniscal tear left knee",
            "icd10_code": "M23.21",
            "procedure_name": "Arthroscopic partial medial meniscectomy",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 115000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Sanjay Hegde, MS Ortho FRCS",
        },
        "expected_outcome": "approve-recommended",
        "note": "Arthroscopy — no specific waiting period. 30-day initial wait met. Approve.",
    },
    {
        "record_id": "DEMO-BLR-002",
        "label": "Cataract (11mo) — Narayana Health City [CRITICAL TEST]",
        "patient": {
            "patient_id": "PAT-BLR-002002",
            "full_name": "Geetha Bai",
            "date_of_birth": "1952-11-20",
            "gender": "female",
            "age_at_admission": 74,
        },
        "policy": {
            "policy_number": "SH-BLR-200002",
            "policy_holder_name": "Geetha Bai",
            "policy_inception_date": (date.today() - timedelta(days=335)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=30)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[1],
        "medical": {
            "primary_diagnosis": "Posterior subcapsular cataract both eyes",
            "icd10_code": "H26.9",
            "procedure_name": "Phacoemulsification with foldable IOL",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 82000,
            "pre_existing_conditions": ["Type 2 Diabetes", "Hypertension"],
            "treating_physician": "Dr. Padmaja Rao, DO DNB Ophthalmology",
        },
        "expected_outcome": "medical-review",
        "note": "Section 4.1 variant — Bangalore. 11-month policy, cataract 24-month wait not met.",
    },
    {
        "record_id": "DEMO-BLR-003",
        "label": "Emergency Trauma — Fortis Bannerghatta",
        "patient": {
            "patient_id": "PAT-BLR-002003",
            "full_name": "Arjun Shetty",
            "date_of_birth": "1998-04-05",
            "gender": "male",
            "age_at_admission": 28,
        },
        "policy": {
            "policy_number": "SH-BLR-200003",
            "policy_holder_name": "Arjun Shetty",
            "policy_inception_date": (date.today() - timedelta(days=45)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=320)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[2],
        "medical": {
            "primary_diagnosis": "Road traffic accident — closed fracture tibia fibula",
            "icd10_code": "S82.2",
            "procedure_name": "Intramedullary nailing tibia",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=5)).isoformat(),
            "admission_type": "emergency",
            "estimated_cost_inr": 220000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Vivek Nair, MS Ortho",
        },
        "expected_outcome": "approve-recommended",
        "note": "Emergency trauma — initial wait waived. Accidental injury: specific waits N/A.",
    },
    {
        "record_id": "DEMO-BLR-004",
        "label": "Piles Haemorrhoidectomy — Columbia Asia Hebbal",
        "patient": {
            "patient_id": "PAT-BLR-002004",
            "full_name": "Suresh Kumaraswamy",
            "date_of_birth": "1978-09-15",
            "gender": "male",
            "age_at_admission": 48,
        },
        "policy": {
            "policy_number": "SH-BLR-200004",
            "policy_holder_name": "Suresh Kumaraswamy",
            "policy_inception_date": (date.today() - timedelta(days=450)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=280)).isoformat(),
            "sum_insured_inr": 300000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[3],
        "medical": {
            "primary_diagnosis": "Grade III haemorrhoids",
            "icd10_code": "K64.2",
            "procedure_name": "Stapled haemorrhoidopexy",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 55000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Mahesh Kini, MS General Surgery",
        },
        "expected_outcome": "medical-review",
        "note": "Piles — 24-month wait NOT met (15 months). Escalate.",
    },
    {
        "record_id": "DEMO-BLR-005",
        "label": "Lung Resection Oncology — Aster CMI Hebbal",
        "patient": {
            "patient_id": "PAT-BLR-002005",
            "full_name": "Devika Nair",
            "date_of_birth": "1962-07-30",
            "gender": "female",
            "age_at_admission": 64,
        },
        "policy": {
            "policy_number": "SH-BLR-200005",
            "policy_holder_name": "Devika Nair",
            "policy_inception_date": (date.today() - timedelta(days=1800)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=100)).isoformat(),
            "sum_insured_inr": 2000000,
            "cumulative_bonus_inr": 400000,
            "prior_claims_inr": 200000,
        },
        "hospital": BANGALORE_HOSPITALS[4],
        "medical": {
            "primary_diagnosis": "Non-small cell lung cancer stage II",
            "icd10_code": "C34.1",
            "procedure_name": "Video-assisted thoracoscopic lobectomy (VATS)",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=7)).isoformat(),
            "admission_type": "planned_surgical",
            "estimated_cost_inr": 850000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Ramesh Bhat, MCh CT Surgery",
        },
        "expected_outcome": "approve-recommended",
        "note": "Oncology — no specific wait. 5-year policy. Sum insured + NCB covers cost.",
    },
    {
        "record_id": "DEMO-BLR-006",
        "label": "Non-Network Hospital CABG — BGS Kengeri",
        "patient": {
            "patient_id": "PAT-BLR-002006",
            "full_name": "Hanumanthappa G",
            "date_of_birth": "1957-03-12",
            "gender": "male",
            "age_at_admission": 69,
        },
        "policy": {
            "policy_number": "SH-BLR-200006",
            "policy_holder_name": "Hanumanthappa G",
            "policy_inception_date": (date.today() - timedelta(days=1000)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=300)).isoformat(),
            "sum_insured_inr": 1000000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": {**BANGALORE_HOSPITALS[5], "is_network_hospital": False},
        "medical": {
            "primary_diagnosis": "Double vessel CAD — unstable angina",
            "icd10_code": "I20.0",
            "procedure_name": "CABG double vessel on-pump",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=8)).isoformat(),
            "admission_type": "emergency",
            "estimated_cost_inr": 780000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Nagaraj Urs, MCh CTVS",
        },
        "expected_outcome": "query-to-hospital",
        "note": "Non-network hospital — emergency CABG covered but reimbursement process needed.",
    },
    {
        "record_id": "DEMO-BLR-007",
        "label": "Varicose Veins — Sakra World Devarabisanahalli",
        "patient": {
            "patient_id": "PAT-BLR-002007",
            "full_name": "Preethi Ramesh",
            "date_of_birth": "1982-05-19",
            "gender": "female",
            "age_at_admission": 44,
        },
        "policy": {
            "policy_number": "SH-BLR-200007",
            "policy_holder_name": "Preethi Ramesh",
            "policy_inception_date": (date.today() - timedelta(days=600)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=200)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[6],
        "medical": {
            "primary_diagnosis": "Bilateral varicose veins GSV system",
            "icd10_code": "I83.9",
            "procedure_name": "Endovenous laser ablation bilateral",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 70000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Krishnapriya Nair, MS Vascular Surgery",
        },
        "expected_outcome": "medical-review",
        "note": "Varicose veins — 24-month wait NOT met (20 months). Escalate.",
    },
    {
        "record_id": "DEMO-BLR-008",
        "label": "Sports Medicine Shoulder — Sparsh Infantry Rd",
        "patient": {
            "patient_id": "PAT-BLR-002008",
            "full_name": "Rohit Rao",
            "date_of_birth": "1990-10-08",
            "gender": "male",
            "age_at_admission": 36,
        },
        "policy": {
            "policy_number": "SH-BLR-200008",
            "policy_holder_name": "Rohit Rao",
            "policy_inception_date": (date.today() - timedelta(days=730)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=270)).isoformat(),
            "sum_insured_inr": 1000000,
            "cumulative_bonus_inr": 100000,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[7],
        "medical": {
            "primary_diagnosis": "Rotator cuff tear — supraspinatus complete",
            "icd10_code": "M75.1",
            "procedure_name": "Arthroscopic rotator cuff repair",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=1)).isoformat(),
            "admission_type": "planned_surgical",
            "estimated_cost_inr": 180000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Tarun Kumar, MS Ortho Sports Medicine",
        },
        "expected_outcome": "approve-recommended",
        "note": "Rotator cuff — no specific wait. 24-month policy. Approve.",
    },
    {
        "record_id": "DEMO-BLR-009",
        "label": "Hydrocele (28mo) — St. John's Medical College",
        "patient": {
            "patient_id": "PAT-BLR-002009",
            "full_name": "Anthony Pinto",
            "date_of_birth": "1975-08-22",
            "gender": "male",
            "age_at_admission": 51,
        },
        "policy": {
            "policy_number": "SH-BLR-200009",
            "policy_holder_name": "Anthony Pinto",
            "policy_inception_date": (date.today() - timedelta(days=860)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=200)).isoformat(),
            "sum_insured_inr": 300000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[9],
        "medical": {
            "primary_diagnosis": "Primary hydrocele left side",
            "icd10_code": "N43.3",
            "procedure_name": "Lord's procedure hydrocele repair",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": date.today().isoformat(),
            "admission_type": "day_care",
            "estimated_cost_inr": 38000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Francis D'Souza, MS Urology",
        },
        "expected_outcome": "approve-recommended",
        "note": "Hydrocele — 24-month wait met (28 months). Approve.",
    },
    {
        "record_id": "DEMO-BLR-010",
        "label": "Gallbladder — Narayana Health (Initial Wait)",
        "patient": {
            "patient_id": "PAT-BLR-002010",
            "full_name": "Kavitha Subramaniam",
            "date_of_birth": "1980-12-11",
            "gender": "female",
            "age_at_admission": 45,
        },
        "policy": {
            "policy_number": "SH-BLR-200010",
            "policy_holder_name": "Kavitha Subramaniam",
            "policy_inception_date": (date.today() - timedelta(days=15)).isoformat(),
            "policy_expiry_date": (date.today() + timedelta(days=350)).isoformat(),
            "sum_insured_inr": 500000,
            "cumulative_bonus_inr": 0,
            "prior_claims_inr": 0,
        },
        "hospital": BANGALORE_HOSPITALS[1],
        "medical": {
            "primary_diagnosis": "Symptomatic cholelithiasis",
            "icd10_code": "K80.2",
            "procedure_name": "Laparoscopic cholecystectomy",
            "admission_date": date.today().isoformat(),
            "expected_discharge_date": (date.today() + timedelta(days=1)).isoformat(),
            "admission_type": "planned_surgical",
            "estimated_cost_inr": 95000,
            "pre_existing_conditions": [],
            "treating_physician": "Dr. Ananda Rao, MS General Surgery",
        },
        "expected_outcome": "medical-review",
        "note": "Policy only 15 days old — 30-day initial waiting period not met.",
    },
]


# Additional records are kept separate from DEMO_RECORDS on purpose.  They are
# used by scripts/create_manual_demo_guide.py for live, manually submitted
# requests and must not appear in the pre-seeded dashboard list.
_ADDITIONAL_CASES: list[dict[str, Any]] = [
    {
        "diagnosis": "Acute appendicitis",
        "icd10": "K35.8",
        "procedure": "Laparoscopic appendicectomy",
        "admission_type": "emergency",
        "cost": 72000,
        "stay": 3,
        "conditions": [],
        "doctor": "Dr. Anil Menon, MS General Surgery",
        "tenure_days": 420,
        "outcome": "approve-recommended",
        "note": "Emergency admission — initial waiting period waived; no specific procedure wait applies.",
        "age": 29,
        "gender": "male",
    },
    {
        "diagnosis": "Symptomatic gallstones",
        "icd10": "K80.2",
        "procedure": "Laparoscopic cholecystectomy",
        "admission_type": "planned_surgical",
        "cost": 110000,
        "stay": 2,
        "conditions": ["Dyslipidemia"],
        "doctor": "Dr. Meera Iyer, MS General Surgery",
        "tenure_days": 760,
        "outcome": "approve-recommended",
        "note": "Policy tenure exceeds the applicable waiting period; network cashless pathway available.",
        "age": 43,
        "gender": "female",
    },
    {
        "diagnosis": "Lumbar disc prolapse",
        "icd10": "M51.2",
        "procedure": "Lumbar microdiscectomy",
        "admission_type": "planned_surgical",
        "cost": 265000,
        "stay": 4,
        "conditions": ["Chronic low back pain"],
        "doctor": "Dr. Nikhil Bhat, MS Orthopaedics",
        "tenure_days": 610,
        "outcome": "medical-review",
        "note": "Spinal procedure requires review of imaging, conservative treatment history, and medical necessity.",
        "age": 49,
        "gender": "male",
    },
    {
        "diagnosis": "Acute myocardial infarction",
        "icd10": "I21.9",
        "procedure": "Coronary angioplasty with stent",
        "admission_type": "emergency",
        "cost": 385000,
        "stay": 5,
        "conditions": ["Hypertension", "Type 2 Diabetes"],
        "doctor": "Dr. Farah Khan, DM Cardiology",
        "tenure_days": 90,
        "outcome": "medical-review",
        "note": "Emergency cardiac admission; verify policy activation, disclosure history, and clinical records.",
        "age": 61,
        "gender": "female",
    },
    {
        "diagnosis": "Ureteric calculus",
        "icd10": "N20.0",
        "procedure": "Ureteroscopy with laser lithotripsy",
        "admission_type": "day_care",
        "cost": 135000,
        "stay": 1,
        "conditions": [],
        "doctor": "Dr. Vivek Rangan, MCh Urology",
        "tenure_days": 480,
        "outcome": "approve-recommended",
        "note": "Day-care urology procedure; policy tenure and hospital network status are satisfactory.",
        "age": 37,
        "gender": "male",
    },
    {
        "diagnosis": "Benign prostatic hyperplasia",
        "icd10": "N40.1",
        "procedure": "Transurethral resection of prostate",
        "admission_type": "planned_surgical",
        "cost": 175000,
        "stay": 3,
        "conditions": ["Hypertension"],
        "doctor": "Dr. Suresh Rao, MCh Urology",
        "tenure_days": 530,
        "outcome": "medical-review",
        "note": "Review age-specific disease waiting period and prior conservative management before approval.",
        "age": 67,
        "gender": "male",
    },
    {
        "diagnosis": "Uterine leiomyoma",
        "icd10": "D25.9",
        "procedure": "Laparoscopic hysterectomy",
        "admission_type": "planned_surgical",
        "cost": 220000,
        "stay": 3,
        "conditions": ["Iron deficiency anaemia"],
        "doctor": "Dr. Shalini Joseph, MD Obstetrics and Gynaecology",
        "tenure_days": 810,
        "outcome": "approve-recommended",
        "note": "Waiting period is satisfied; obtain routine pre-operative reports and admission estimate.",
        "age": 46,
        "gender": "female",
    },
    {
        "diagnosis": "Community-acquired pneumonia",
        "icd10": "J18.9",
        "procedure": "Inpatient pneumonia management",
        "admission_type": "emergency",
        "cost": 88000,
        "stay": 4,
        "conditions": ["Asthma"],
        "doctor": "Dr. Ritu Sharma, MD Pulmonary Medicine",
        "tenure_days": 24,
        "outcome": "medical-review",
        "note": "Policy is within the initial 30-day period; emergency admission requires clinical validation.",
        "age": 34,
        "gender": "female",
    },
    {
        "diagnosis": "Fracture of neck of femur",
        "icd10": "S72.0",
        "procedure": "Hip fracture fixation",
        "admission_type": "emergency",
        "cost": 310000,
        "stay": 7,
        "conditions": ["Osteoporosis"],
        "doctor": "Dr. Ajay Kulkarni, MS Orthopaedics",
        "tenure_days": 365,
        "outcome": "query-to-hospital",
        "note": "Non-network admission — request emergency certificate, implant details, discharge summary, and original bills.",
        "age": 74,
        "gender": "female",
    },
    {
        "diagnosis": "Retinal detachment",
        "icd10": "H33.2",
        "procedure": "Pars plana vitrectomy",
        "admission_type": "planned_surgical",
        "cost": 190000,
        "stay": 2,
        "conditions": ["Type 2 Diabetes"],
        "doctor": "Dr. Kavya Nair, DNB Ophthalmology",
        "tenure_days": 690,
        "outcome": "medical-review",
        "note": "Ophthalmic surgery requires retinal imaging, operative plan, and confirmation of covered indication.",
        "age": 58,
        "gender": "male",
    },
]

_HYDERABAD_NAMES = [
    "Anusha Varma", "Bhaskar Naidu", "Charan Reddy", "Deepa Mallik", "Eshwar Rao",
    "Fathima Begum", "Girish Babu", "Harini Prasad", "Ishaan Mehta", "Jahnavi Rao",
    "Karthik Goud", "Lavanya Sethi", "Manoj Pillai", "Nandini Shah", "Omkar Reddy",
    "Pranavi Rao", "Qasim Ali", "Rakesh Varma", "Sneha Nair", "Tarun Kumar",
    "Uma Mahesh", "Varun Chandra", "Wasim Ahmed", "Yamini Goud", "Zoya Khan",
]

_BANGALORE_NAMES = [
    "Aditi Menon", "Bharat Shetty", "Chaitanya Rao", "Divya Hegde", "Elvin D'Souza",
    "Gautham Iyer", "Hema Srinivas", "Imran Khan", "Jyothi Nair", "Kiran Bhat",
    "Lekha Prasad", "Madhav Gowda", "Nisha Thomas", "Omar Farooq", "Pooja Reddy",
    "Raghav Joshi", "Sahana Murthy", "Tejas Kulkarni", "Usha Pai", "Vikram Das",
    "Waseem Ahmed", "Xavier Fernandes", "Yashaswini Rao", "Zubin Mathew", "Aarav Kapoor",
]


def _build_additional_demo_records() -> list[dict[str, Any]]:
    """Create 50 deterministic records for the dashboard demo (25 per city)."""
    today = date.today()
    records: list[dict[str, Any]] = []
    city_configs = [
        ("HYD", "Hyderabad", "Telangana", HYDERABAD_HOSPITALS, _HYDERABAD_NAMES),
        ("BLR", "Bangalore", "Karnataka", BANGALORE_HOSPITALS, _BANGALORE_NAMES),
    ]

    for city_code, city, state, hospitals, names in city_configs:
        for offset, name in enumerate(names, start=11):
            case = _ADDITIONAL_CASES[(offset - 11) % len(_ADDITIONAL_CASES)]
            outcome = case["outcome"]
            hospital = hospitals[8] if outcome == "query-to-hospital" else hospitals[(offset - 11) % 9]
            admission_date = today + timedelta(days=(offset - 11) % 5)
            birth_year = today.year - case["age"]
            birth_date = date(birth_year, ((offset - 11) % 12) + 1, ((offset * 3) % 27) + 1)
            record_id = f"DEMO-{city_code}-{offset:03d}"

            records.append({
                "record_id": record_id,
                "label": f"{case['procedure']} — {hospital['hospital_name']}",
                "patient": {
                    "patient_id": f"PAT-{city_code}-001{offset:03d}",
                    "full_name": name,
                    "date_of_birth": birth_date.isoformat(),
                    "gender": case["gender"],
                    "age_at_admission": case["age"],
                },
                "policy": {
                    "policy_number": f"SH-{city_code}-10{offset:04d}",
                    "policy_holder_name": name,
                    "policy_inception_date": (today - timedelta(days=case["tenure_days"])).isoformat(),
                    "policy_expiry_date": (today + timedelta(days=180 + (offset * 7))).isoformat(),
                    "sum_insured_inr": 300000 if offset % 3 == 0 else 500000,
                    "cumulative_bonus_inr": 50000 if offset % 4 == 0 else 0,
                    "prior_claims_inr": 0 if offset % 5 else 45000,
                },
                "hospital": hospital,
                "medical": {
                    "primary_diagnosis": case["diagnosis"],
                    "icd10_code": case["icd10"],
                    "procedure_name": case["procedure"],
                    "admission_date": admission_date.isoformat(),
                    "expected_discharge_date": (admission_date + timedelta(days=case["stay"])).isoformat(),
                    "admission_type": case["admission_type"],
                    "estimated_cost_inr": case["cost"] + ((offset % 4) * 5000),
                    "pre_existing_conditions": case["conditions"],
                    "treating_physician": case["doctor"],
                },
                "expected_outcome": outcome,
                "note": case["note"],
            })

    return records


def seed_redis(host: str = "localhost", port: int = 6379, password: str = "") -> None:
    """Seed Redis with demo pre-computed results for immediate display."""
    import redis

    r = redis.Redis(host=host, port=port, password=password or None, decode_responses=True)
    try:
        r.ping()
        print("✓ Connected to Redis")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("  Saving records to JSON file instead...")
        _save_to_json()
        return

    seeded = 0
    for record in DEMO_RECORDS:
        run_id = f"DEMO-{record['record_id']}"
        outcome = record["expected_outcome"]

        # Build synthetic result
        citations = _build_citations(outcome, record["medical"]["icd10_code"])
        result = {
            "run_id": run_id,
            "request_id": f"REQ-{record['record_id']}",
            "status": "completed",
            "outcome": outcome,
            "recommendation": _build_recommendation(record, outcome),
            "citations": citations,
            "escalation_reason": record["note"] if outcome == "medical-review" else None,
            "admission_type_classified": record["medical"]["admission_type"],
            "token_usage": {
                "prompt_tokens": 450,
                "completion_tokens": 380,
                "total_tokens": 830,
                "estimated_cost_usd": 0.0,
                "model": "stub",
            },
            "prompt_version": "v1",
            "correlation_id": f"seed-{record['record_id']}",
            "processing_time_ms": 850.0,
            "policy_age_months": _calc_months(record["policy"]["policy_inception_date"]),
            "hospital": record["hospital"]["hospital_name"],
            "procedure": record["medical"]["procedure_name"],
            "label": record["label"],
        }

        # Store in Redis (result + status)
        r.setex(
            f"preauth:result:{run_id}",
            86400 * 30,
            json.dumps({"run_id": run_id, "status": "completed", "result": result}),
        )
        r.setex(
            f"preauth:status:{run_id}",
            86400 * 30,
            json.dumps({"run_id": run_id, "status": "completed"}),
        )
        seeded += 1
        print(f"  ✓ {run_id}: {record['label'][:55]} → {outcome}")

    print(f"\n✅ Seeded {seeded}/{len(DEMO_RECORDS)} records into Redis")
    _save_to_json()


def _calc_months(inception_date_str: str) -> int:
    d = date.fromisoformat(inception_date_str)
    today = date.today()
    return max((today.year - d.year) * 12 + (today.month - d.month), 0)


def _build_citations(outcome: str, icd10: str) -> list[dict]:
    base = []
    if "H26" in icd10 or "H25" in icd10:
        base.append({
            "clause_id": "SCHIP-WAIT-002",
            "clause_title": "Waiting Period — Specific Diseases and Procedures (24 months)",
            "excerpt": "Cataract surgery (both eyes), including Phacoemulsification with IOL implantation — 24 months waiting period.",
            "source_document": "Star Health Comprehensive Insurance Policy",
            "page_or_section": "13",
            "relevance_score": 0.98,
            "verified": True,
        })
        base.append({
            "clause_id": "SCHIP-COV-002",
            "clause_title": "Coverage — Day Care Procedures",
            "excerpt": "Cataract surgery including Phacoemulsification with IOL implantation is covered as a Day Care procedure subject to the applicable waiting periods.",
            "source_document": "Star Health Comprehensive Insurance Policy",
            "page_or_section": "9",
            "relevance_score": 0.91,
            "verified": True,
        })
    elif outcome == "approve-recommended":
        base.append({
            "clause_id": "SCHIP-COV-001",
            "clause_title": "Coverage — In-Patient Hospitalisation",
            "excerpt": "The Company will pay the Medical Expenses incurred by the Insured Person during an Inpatient Hospitalisation.",
            "source_document": "Star Health Comprehensive Insurance Policy",
            "page_or_section": "8",
            "relevance_score": 0.87,
            "verified": True,
        })
    return base


def _build_recommendation(record: dict, outcome: str) -> str:
    name = record["patient"]["full_name"]
    procedure = record["medical"]["procedure_name"]
    hospital = record["hospital"]["hospital_name"]
    months = _calc_months(record["policy"]["policy_inception_date"])
    policy_no = record["policy"]["policy_number"]

    if outcome == "approve-recommended":
        return (
            f"Pre-authorization recommended for {name} (Policy: {policy_no}). "
            f"Procedure: {procedure} at {hospital}. "
            f"Policy tenure of {months} months satisfies all applicable waiting periods. "
            f"No conflicts identified. Cashless facility may be provided at network hospital."
        )
    elif outcome == "medical-review":
        return (
            f"Pre-authorization for {name} (Policy: {policy_no}) requires medical review. "
            f"Procedure: {procedure} at {hospital}. "
            f"Note: {record['note']}. "
            f"Policy tenure: {months} months. Request escalated to medical review panel."
        )
    else:
        return (
            f"Pre-authorization query raised for {name} (Policy: {policy_no}). "
            f"Procedure: {procedure} at {hospital} (non-network). "
            f"Please provide discharge summary and bills for reimbursement processing."
        )


def _save_to_json() -> None:
    out_path = Path(__file__).resolve().parent.parent / "corpus" / "demo_records.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "run_id": f"DEMO-{r['record_id']}",
                    "label": r["label"],
                    "hospital": r["hospital"]["hospital_name"],
                    "city": r["hospital"]["city"],
                    "policy_number": r["policy"]["policy_number"],
                    "patient": r["patient"]["full_name"],
                    "procedure": r["medical"]["procedure_name"],
                    "expected_outcome": r["expected_outcome"],
                    "note": r["note"],
                }
                for r in DEMO_RECORDS
            ],
            f,
            indent=2,
        )
    print(f"  JSON saved to: {out_path}")


if __name__ == "__main__":
    import os
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_password = os.getenv("REDIS_PASSWORD", "")
    print(f"\n🌱 Seeding demo data — {len(DEMO_RECORDS)} records")
    print(f"   Hyderabad hospitals: {len(HYDERABAD_HOSPITALS)}")
    print(f"   Bangalore hospitals: {len(BANGALORE_HOSPITALS)}")
    print(f"   Redis: {redis_host}:{redis_port}\n")
    seed_redis(host=redis_host, port=redis_port, password=redis_password)
