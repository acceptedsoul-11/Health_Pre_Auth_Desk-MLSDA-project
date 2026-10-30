"""
Star Health Insurance Corpus — Synthetic policy text for RAG indexing.
This represents the key clauses from the Star Comprehensive Health Insurance Policy.
In production, replace with the actual PDF loaded via the ingestion CLI.

Sections are tagged with structured metadata for clause-level citation.
"""

CORPUS_DOCUMENTS = [
    {
        "doc_id": "STAR-COMP-001",
        "title": "Star Health Comprehensive Insurance Policy",
        "source": "Star Health and Allied Insurance Co. Ltd.",
        "version": "2024-25",
        "sections": [
            {
                "clause_id": "SCHIP-DEF-001",
                "title": "Definitions — Illness",
                "page": "4",
                "text": (
                    "Illness means a sickness or a disease or pathological condition "
                    "leading to the failure of normal physiological function and requires "
                    "medical treatment. (a) Acute condition — Acute condition is a disease, "
                    "illness or injury that is likely to respond quickly to treatment which aims "
                    "to return the person to his or her state of health immediately before "
                    "suffering the disease/illness/injury which leads to full recovery. "
                    "(b) Chronic condition — A chronic condition is defined as a disease, illness, "
                    "or injury that has one or more of the following characteristics: it needs "
                    "ongoing or long-term monitoring through consultations, examinations, check-ups, "
                    "and/or tests; it needs ongoing or long-term control or relief of symptoms; "
                    "it requires rehabilitation for the patient or for the patient to be specially "
                    "trained to cope with it; it continues indefinitely; it recurs or is likely to recur."
                ),
            },
            {
                "clause_id": "SCHIP-DEF-002",
                "title": "Definitions — Pre-Existing Disease (PED)",
                "page": "5",
                "text": (
                    "Pre-Existing Disease means any condition, ailment, injury or disease: "
                    "(a) That is/are diagnosed by a physician within 48 months prior to the "
                    "effective date of the policy issued by the insurer, or "
                    "(b) For which medical advice or treatment was recommended by, or received "
                    "from, a physician within 48 months prior to the effective date of the "
                    "policy issued by the insurer."
                ),
            },
            {
                "clause_id": "SCHIP-COV-001",
                "title": "Coverage — In-Patient Hospitalisation",
                "page": "8",
                "text": (
                    "The Company will pay the Medical Expenses incurred by the Insured Person "
                    "during an Inpatient Hospitalisation in a Hospital for a minimum period of "
                    "24 consecutive hours. Medical expenses include room rent, ICU charges, "
                    "surgeon's fees, anaesthetist's fees, medical practitioner's fees, "
                    "consultants' fees, nursing charges, and cost of medicines, drugs and "
                    "consumables. The policy covers all surgical procedures including but not "
                    "limited to general surgery, orthopaedic surgery, cardiac surgery, "
                    "neurosurgery, oncology procedures, ophthalmological procedures, "
                    "ear-nose-throat procedures, gynaecological procedures, and urological "
                    "procedures, subject to the terms, conditions, and exclusions of this policy."
                ),
            },
            {
                "clause_id": "SCHIP-COV-002",
                "title": "Coverage — Day Care Procedures",
                "page": "9",
                "text": (
                    "Day Care Treatment means medical treatment and/or surgical procedure which "
                    "is undertaken under general or local anaesthesia in a hospital/day care "
                    "centre in less than 24 hours because of technological advancement, and "
                    "which would have otherwise required a hospitalisation of more than 24 hours. "
                    "The Company will reimburse Day Care Treatment expenses for procedures listed "
                    "in the Day Care Procedures List appended to this policy. Cataract surgery "
                    "including Phacoemulsification with IOL implantation is covered as a Day Care "
                    "procedure subject to the applicable waiting periods and policy terms."
                ),
            },
            {
                "clause_id": "SCHIP-WAIT-001",
                "title": "Waiting Period — Initial Waiting Period",
                "page": "12",
                "text": (
                    "Initial Waiting Period: A waiting period of 30 days from the commencement "
                    "of the first policy year is applicable for all claims except for accidental "
                    "injuries. This means no claims shall be admissible during the first 30 days "
                    "from the policy start date, except claims arising out of accidents. "
                    "This initial waiting period does not apply on renewal of the policy."
                ),
            },
            {
                "clause_id": "SCHIP-WAIT-002",
                "title": "Waiting Period — Specific Diseases and Procedures (24 months)",
                "page": "13",
                "text": (
                    "Specific Disease Waiting Period: The following diseases/treatments/surgeries "
                    "are payable after 24 calendar months of continuous coverage from the date "
                    "of inception of the first policy issued by the Company, provided the insured "
                    "person has been continuously insured without any break: "
                    "1. Cataract surgery (both eyes), including Phacoemulsification with IOL "
                    "implantation — 24 months waiting period. "
                    "2. Benign Prostatic Hypertrophy (BPH) — 24 months waiting period. "
                    "3. Hernia of all types — 24 months waiting period. "
                    "4. Fistula-in-ano, piles, sinuses — 24 months waiting period. "
                    "5. Hydrocele — 24 months waiting period. "
                    "6. Gastric and Duodenal Ulcer — 24 months waiting period. "
                    "7. Uterine Fibroids — 24 months waiting period. "
                    "8. Kidney Stone / Calculus — 24 months waiting period. "
                    "9. Joint replacement surgery — 24 months waiting period. "
                    "10. Varicose veins and varicose ulcers — 24 months waiting period. "
                    "The above waiting periods do not apply if the condition is accidental in nature."
                ),
            },
            {
                "clause_id": "SCHIP-WAIT-003",
                "title": "Waiting Period — Pre-Existing Diseases (48 months)",
                "page": "14",
                "text": (
                    "Pre-Existing Disease Waiting Period: Benefits in respect of Pre-Existing "
                    "Diseases (PED), as defined in this policy, shall be admissible only after "
                    "48 continuous months of coverage from the date of inception of the first "
                    "policy issued by the Company. Continuous coverage means the policy has been "
                    "renewed without any break. If there is a break in coverage of more than "
                    "90 days, the waiting period restarts. "
                    "For the purpose of this clause, Diabetes Mellitus (Type 1 and Type 2), "
                    "Hypertension, Thyroid disorders, Asthma, and other chronic conditions that "
                    "are disclosed at policy inception shall be treated as Pre-Existing Diseases."
                ),
            },
            {
                "clause_id": "SCHIP-EXCL-001",
                "title": "Permanent Exclusions — General",
                "page": "16",
                "text": (
                    "The Company shall not be liable to make any payment under this policy in "
                    "respect of any expenses whatsoever incurred in connection with or in respect "
                    "of the following: "
                    "1. Any condition directly or indirectly caused by or associated with any "
                    "communicable disease. "
                    "2. Treatment of Mental Illness, stress, or psychological disorders. "
                    "3. Cosmetic or aesthetic treatments of any description, plastic surgery other "
                    "than as may be necessitated due to an accident or illness. "
                    "4. Treatment for self-inflicted injury or suicide attempts. "
                    "5. Expenses arising from war, invasion, hostilities, civil war, revolution. "
                    "6. Hormone replacement therapy. "
                    "7. Dental treatment or surgery of any kind, unless requiring hospitalisation. "
                    "8. Spectacles, contact lenses, hearing aids. "
                    "9. Vitamins and tonics, unless certified as essential for treatment of injury "
                    "or illness. "
                    "10. Experimental or unproven treatments not recognised by established "
                    "medical practice."
                ),
            },
            {
                "clause_id": "SCHIP-EXCL-002",
                "title": "Exclusions — Investigation and Management",
                "page": "17",
                "text": (
                    "The Company shall not be liable for: "
                    "1. Any diagnostic expenses which are not related or not incidental to the "
                    "current diagnosis and treatment. "
                    "2. Rest cure, rehabilitation, and respite care. "
                    "3. OPD treatment (unless specifically covered under an OPD add-on rider). "
                    "4. Non-allopathic treatment unless specifically included under the policy."
                ),
            },
            {
                "clause_id": "SCHIP-MAT-001",
                "title": "Maternity Benefit",
                "page": "20",
                "text": (
                    "Maternity Benefit is available as an add-on cover and is subject to a "
                    "waiting period of 24 months from the date of inception of the first policy. "
                    "The benefit covers expenses for normal delivery, caesarean section, and "
                    "complications of childbirth up to the maternity sub-limit specified in the "
                    "schedule. Newborn baby expenses are covered from birth up to 90 days under "
                    "this clause, subject to the overall sum insured."
                ),
            },
            {
                "clause_id": "SCHIP-EMER-001",
                "title": "Emergency Hospitalisation",
                "page": "22",
                "text": (
                    "Emergency Hospitalisation means hospitalisation that is sudden, unexpected, "
                    "and occurs due to an accidental injury or an acute illness that requires "
                    "immediate medical attention. The initial waiting period of 30 days does "
                    "not apply to Emergency Hospitalisation. The specific disease waiting periods "
                    "do not apply if the condition is an acute emergency requiring immediate "
                    "intervention. The Company will honour Cashless facility at network hospitals "
                    "for emergency admissions subject to policy terms."
                ),
            },
            {
                "clause_id": "SCHIP-CLAIM-001",
                "title": "Pre-Authorisation Process",
                "page": "24",
                "text": (
                    "For planned hospitalisations, the Insured Person must obtain pre-authorisation "
                    "from the Company at least 48 hours prior to admission. The request for "
                    "pre-authorisation must be submitted through the treating hospital's "
                    "insurance desk. The Company shall respond within 2 hours for emergency "
                    "cases and within 4 hours for planned cases. Pre-authorisation is granted "
                    "based on the policy terms, coverage eligibility, and applicable waiting "
                    "periods. Grant of pre-authorisation does not guarantee final settlement; "
                    "the claim will be processed upon discharge based on actual expenses incurred."
                ),
            },
            {
                "clause_id": "SCHIP-SUM-001",
                "title": "Sum Insured and Sub-limits",
                "page": "26",
                "text": (
                    "The total liability of the Company in any one Policy Year shall not exceed "
                    "the Sum Insured as stated in the Policy Schedule. Sub-limits applicable: "
                    "Room Rent: 1% of Sum Insured per day (waived for plans above INR 5 lakh). "
                    "ICU Charges: 2% of Sum Insured per day (waived for plans above INR 5 lakh). "
                    "Cataract Surgery: INR 40,000 per eye (for plans below INR 5 lakh), "
                    "No sub-limit for plans of INR 5 lakh and above. "
                    "Ambulance charges: Up to INR 2,000 per hospitalisation."
                ),
            },
            {
                "clause_id": "SCHIP-RENEW-001",
                "title": "Renewal Terms and Continuity",
                "page": "30",
                "text": (
                    "The policy is renewable annually. Renewal is guaranteed subject to the "
                    "following conditions: (a) Renewal premium is paid before the due date or "
                    "within the grace period of 30 days. (b) There is no fraud or misrepresentation. "
                    "Continuity of waiting periods: On renewal without break, the waiting periods "
                    "already served under the previous policy shall be credited. The 30-day "
                    "initial waiting period, 24-month specific disease waiting period, and "
                    "48-month PED waiting period shall be calculated from the date of first "
                    "inception of the policy with continuous renewals."
                ),
            },
        ],
    },
    {
        "doc_id": "STAR-DCP-001",
        "title": "Star Health Day Care Procedures List",
        "source": "Star Health and Allied Insurance Co. Ltd.",
        "version": "2024-25",
        "sections": [
            {
                "clause_id": "DCP-OPHTH-001",
                "title": "Day Care Procedures — Ophthalmology",
                "page": "2",
                "text": (
                    "Ophthalmology Day Care Procedures (covered subject to applicable "
                    "waiting periods and policy terms): "
                    "1. Cataract surgery — Phacoemulsification with IOL implantation "
                    "(ICD-10: H25, H26). Subject to 24-month specific disease waiting period. "
                    "2. Laser photocoagulation for diabetic retinopathy. "
                    "3. Vitrectomy. "
                    "4. Strabismus correction surgery. "
                    "5. LASIK/PRK for refractive error correction — EXCLUDED (cosmetic). "
                    "6. Glaucoma drainage procedures — Trabeculectomy. "
                    "7. Corneal transplant (keratoplasty). "
                    "8. Pterygium excision. "
                    "9. Chalazion excision. "
                    "10. Dacryocystectomy."
                ),
            },
            {
                "clause_id": "DCP-ORTHO-001",
                "title": "Day Care Procedures — Orthopaedics",
                "page": "3",
                "text": (
                    "Orthopaedic Day Care Procedures: "
                    "1. Arthroscopy — diagnostic and therapeutic. "
                    "2. Carpal tunnel release. "
                    "3. Trigger finger release. "
                    "4. Removal of implants (K-wires, plates, screws). "
                    "5. Ganglion excision. "
                    "6. Fasciotomy. "
                    "Note: Joint replacement surgeries (hip, knee, shoulder) are in-patient "
                    "procedures subject to 24-month waiting period and are NOT day care."
                ),
            },
            {
                "clause_id": "DCP-UROL-001",
                "title": "Day Care Procedures — Urology",
                "page": "4",
                "text": (
                    "Urology Day Care Procedures: "
                    "1. Cystoscopy — diagnostic and therapeutic. "
                    "2. Ureteroscopy with lithotripsy for kidney stones (subject to 24-month wait). "
                    "3. ESWL (Extra-corporeal Shock Wave Lithotripsy). "
                    "4. Circumcision. "
                    "5. Hydrocele repair (subject to 24-month waiting period). "
                    "6. Varicocele repair. "
                    "7. Vasectomy."
                ),
            },
            {
                "clause_id": "DCP-GEN-001",
                "title": "Day Care Procedures — General Surgery",
                "page": "5",
                "text": (
                    "General Surgery Day Care Procedures: "
                    "1. Hernia repair — inguinal, umbilical, incisional (subject to 24-month wait). "
                    "2. Haemorrhoidectomy / Piles treatment (subject to 24-month wait). "
                    "3. Fistulectomy (subject to 24-month wait). "
                    "4. Appendicectomy (emergency — no waiting period). "
                    "5. Lipoma excision. "
                    "6. Sebaceous cyst excision. "
                    "7. Anal fissure treatment. "
                    "8. Pilonidal sinus excision (subject to 24-month wait)."
                ),
            },
        ],
    },
]


def get_all_clauses() -> list[dict]:
    """Return flat list of all clause dicts with parent document metadata."""
    clauses = []
    for doc in CORPUS_DOCUMENTS:
        for section in doc["sections"]:
            clause = {
                **section,
                "doc_id": doc["doc_id"],
                "doc_title": doc["title"],
                "source": doc["source"],
                "version": doc["version"],
            }
            clauses.append(clause)
    return clauses
