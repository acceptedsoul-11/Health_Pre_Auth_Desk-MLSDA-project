import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import axios from 'axios'

const ADMISSION_TYPES = ['day_care', 'planned_surgical', 'emergency', 'maternity']
const GENDERS = ['male', 'female', 'other']

const today = new Date().toISOString().split('T')[0]

const PRESET_SCENARIOS = [
  {
    name: '🔬 Cataract (11mo wait)',
    data: {
      patient_id: 'PAT-000001',
      full_name: 'Ramesh Kumar',
      date_of_birth: '1965-03-15',
      gender: 'male',
      age_at_admission: 61,
      policy_number: 'SH-CAT-2025-01',
      policy_holder_name: 'Ramesh Kumar',
      policy_inception_date: '2025-11-15',
      policy_expiry_date: '2026-11-14',
      sum_insured_inr: 500000,
      prior_claims_inr: 0,
      hospital_id: 'HOSP-0001',
      hospital_name: 'Apollo Hospitals Chennai',
      is_network_hospital: true,
      city: 'Chennai',
      state: 'Tamil Nadu',
      primary_diagnosis: 'Age-related cataract',
      icd10_code: 'H26.9',
      procedure_name: 'Phacoemulsification with IOL implantation',
      admission_date: today,
      expected_discharge_date: today,
      admission_type: 'day_care',
      estimated_cost_inr: 75000,
      pre_existing_conditions: 'Type 2 Diabetes',
      treating_physician: 'Dr. Priya Venkat',
      free_text_notes: '',
    }
  },
  {
    name: '🚨 Emergency Appendicitis (Waived)',
    data: {
      patient_id: 'PAT-000002',
      full_name: 'Rajesh Verma',
      date_of_birth: '1974-05-12',
      gender: 'male',
      age_at_admission: 52,
      policy_number: 'SH-EMERG-2026-02',
      policy_holder_name: 'Rajesh Verma',
      policy_inception_date: '2026-10-15',
      policy_expiry_date: '2027-10-14',
      sum_insured_inr: 1000000,
      prior_claims_inr: 0,
      hospital_id: 'HOSP-HYD-001',
      hospital_name: 'Apollo Hospitals Jubilee Hills',
      is_network_hospital: true,
      city: 'Hyderabad',
      state: 'Telangana',
      primary_diagnosis: 'Acute appendicitis with perforation',
      icd10_code: 'K35.2',
      procedure_name: 'Emergency Appendicectomy',
      admission_date: today,
      expected_discharge_date: today,
      admission_type: 'emergency',
      estimated_cost_inr: 85000,
      pre_existing_conditions: '',
      treating_physician: 'Dr. Ashok Kumar, MS General Surgery',
      free_text_notes: 'Acute onset severe abdominal pain, emergency surgery indicated.',
    }
  },
  {
    name: '🦵 Knee Replacement (14mo wait)',
    data: {
      patient_id: 'PAT-000003',
      full_name: 'Sunita Deshmukh',
      date_of_birth: '1962-08-20',
      gender: 'female',
      age_at_admission: 64,
      policy_number: 'SH-TKR-2025-03',
      policy_holder_name: 'Sunita Deshmukh',
      policy_inception_date: '2025-08-15',
      policy_expiry_date: '2027-08-14',
      sum_insured_inr: 800000,
      prior_claims_inr: 0,
      hospital_id: 'HOSP-BLR-001',
      hospital_name: 'Manipal Hospital Old Airport Road',
      is_network_hospital: true,
      city: 'Bangalore',
      state: 'Karnataka',
      primary_diagnosis: 'Severe Osteoarthritis of bilateral knee',
      icd10_code: 'M17.0',
      procedure_name: 'Total Knee Arthroplasty (TKR)',
      admission_date: today,
      expected_discharge_date: today,
      admission_type: 'planned_surgical',
      estimated_cost_inr: 350000,
      pre_existing_conditions: 'Hypertension',
      treating_physician: 'Dr. Sanjay Hegde, MS Ortho',
      free_text_notes: '',
    }
  },
  {
    name: '🩹 Hernia Repair (28mo Mature)',
    data: {
      patient_id: 'PAT-000004',
      full_name: 'Vikram Rao',
      date_of_birth: '1978-03-10',
      gender: 'male',
      age_at_admission: 48,
      policy_number: 'SH-HERNIA-2024-04',
      policy_holder_name: 'Vikram Rao',
      policy_inception_date: '2024-06-15',
      policy_expiry_date: '2027-06-14',
      sum_insured_inr: 500000,
      prior_claims_inr: 0,
      hospital_id: 'HOSP-BLR-003',
      hospital_name: 'Fortis Hospital Bannerghatta Road',
      is_network_hospital: true,
      city: 'Bangalore',
      state: 'Karnataka',
      primary_diagnosis: 'Right Inguinal Hernia',
      icd10_code: 'K40.9',
      procedure_name: 'Laparoscopic TEP Hernia Repair',
      admission_date: today,
      expected_discharge_date: today,
      admission_type: 'day_care',
      estimated_cost_inr: 85000,
      pre_existing_conditions: '',
      treating_physician: 'Dr. Praveen Reddy, MS General Surgery',
      free_text_notes: '',
    }
  },
  {
    name: '🧬 Gene Therapy (Exclusion)',
    data: {
      patient_id: 'PAT-000005',
      full_name: 'Amit Sharma',
      date_of_birth: '1988-11-25',
      gender: 'male',
      age_at_admission: 38,
      policy_number: 'SH-EXP-2023-05',
      policy_holder_name: 'Amit Sharma',
      policy_inception_date: '2023-01-01',
      policy_expiry_date: '2027-01-01',
      sum_insured_inr: 1500000,
      prior_claims_inr: 0,
      hospital_id: 'HOSP-HYD-002',
      hospital_name: 'Yashoda Hospitals Somajiguda',
      is_network_hospital: true,
      city: 'Hyderabad',
      state: 'Telangana',
      primary_diagnosis: 'Chronic Unspecified Neuropathy',
      icd10_code: 'G62.9',
      procedure_name: 'Experimental Stem Cell and Gene Replacement Therapy',
      admission_date: today,
      expected_discharge_date: today,
      admission_type: 'planned_surgical',
      estimated_cost_inr: 600000,
      pre_existing_conditions: '',
      treating_physician: 'Dr. Anirudh Sen, MD Neurology',
      free_text_notes: 'Unproven experimental treatment protocol.',
    }
  }
]

const defaultForm = PRESET_SCENARIOS[0].data

export default function SubmitPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState(defaultForm)
  const [submitting, setSubmitting] = useState(false)

  const update = (field) => (e) => {
    const val = e.target.type === 'checkbox' ? e.target.checked
      : e.target.type === 'number' ? Number(e.target.value)
      : e.target.value
    setForm(f => ({ ...f, [field]: val }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const payload = {
        patient: {
          patient_id: form.patient_id,
          full_name: form.full_name,
          date_of_birth: form.date_of_birth,
          gender: form.gender,
          age_at_admission: form.age_at_admission,
        },
        policy: {
          policy_number: form.policy_number,
          policy_holder_name: form.policy_holder_name,
          policy_inception_date: form.policy_inception_date,
          policy_expiry_date: form.policy_expiry_date,
          sum_insured_inr: form.sum_insured_inr,
          prior_claims_inr: form.prior_claims_inr,
        },
        hospital: {
          hospital_id: form.hospital_id,
          hospital_name: form.hospital_name,
          is_network_hospital: form.is_network_hospital,
          city: form.city,
          state: form.state,
        },
        medical: {
          primary_diagnosis: form.primary_diagnosis,
          icd10_code: form.icd10_code,
          procedure_name: form.procedure_name,
          admission_date: form.admission_date,
          expected_discharge_date: form.expected_discharge_date,
          admission_type: form.admission_type,
          estimated_cost_inr: form.estimated_cost_inr,
          pre_existing_conditions: form.pre_existing_conditions
            ? form.pre_existing_conditions.split(',').map(s => s.trim()).filter(Boolean)
            : [],
          treating_physician: form.treating_physician,
        },
        free_text_notes: form.free_text_notes || null,
      }

      const res = await axios.post('/api/v1/preauth', payload)
      const { run_id } = res.data
      toast.success(`Submitted! Run ID: ${run_id}`)
      navigate(`/status/${run_id}`)
    } catch (err) {
      const detail = err.response?.data?.detail
      if (typeof detail === 'object') {
        toast.error(`Validation error: ${JSON.stringify(detail).slice(0, 100)}`)
      } else {
        toast.error(detail || err.message)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: 8 }}>
            Submit Pre-Authorization Request
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>
            Submit a live pre-authorization request to run through the multi-agent AI verification pipeline.
            Choose a preset scenario below or enter custom medical and policy details.
          </p>
        </div>

        {/* Quick-Load Presets */}
        <div style={{
          marginBottom: 28, padding: '18px 22px', borderRadius: 14,
          background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(20,184,166,0.3)',
          boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
        }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#14b8a6', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>⚡</span> Quick-Load Demo Scenarios (One-Click Live Run):
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            {PRESET_SCENARIOS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  setForm(preset.data)
                  toast.success(`Loaded: ${preset.name}`)
                }}
                style={{
                  fontSize: '0.82rem',
                  fontWeight: 600,
                  padding: '8px 14px',
                  borderRadius: 8,
                  borderColor: 'rgba(255,255,255,0.12)',
                  background: 'rgba(255,255,255,0.03)',
                  color: '#f1f5f9',
                  transition: 'all 0.2s ease',
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.borderColor = '#14b8a6'
                  e.currentTarget.style.background = 'rgba(20,184,166,0.12)'
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.12)'
                  e.currentTarget.style.background = 'rgba(255,255,255,0.03)'
                }}
              >
                {preset.name}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gap: 20 }}>

            {/* Patient Section */}
            <Section title="Patient Information" icon="👤">
              <Grid2>
                <Field label="Patient ID" value={form.patient_id} onChange={update('patient_id')} placeholder="PAT-000001" />
                <Field label="Full Name" value={form.full_name} onChange={update('full_name')} />
                <Field label="Date of Birth" type="date" value={form.date_of_birth} onChange={update('date_of_birth')} />
                <Select label="Gender" value={form.gender} onChange={update('gender')} options={GENDERS} />
                <Field label="Age at Admission" type="number" value={form.age_at_admission} onChange={update('age_at_admission')} />
              </Grid2>
            </Section>

            {/* Policy Section */}
            <Section title="Policy Details" icon="📋">
              <Grid2>
                <Field label="Policy Number" value={form.policy_number} onChange={update('policy_number')} placeholder="SH-XXXXXXXXX" />
                <Field label="Policy Holder Name" value={form.policy_holder_name} onChange={update('policy_holder_name')} />
                <Field label="Policy Inception Date" type="date" value={form.policy_inception_date} onChange={update('policy_inception_date')} />
                <Field label="Policy Expiry Date" type="date" value={form.policy_expiry_date} onChange={update('policy_expiry_date')} />
                <Field label="Sum Insured (₹)" type="number" value={form.sum_insured_inr} onChange={update('sum_insured_inr')} />
                <Field label="Prior Claims (₹)" type="number" value={form.prior_claims_inr} onChange={update('prior_claims_inr')} />
              </Grid2>
            </Section>

            {/* Hospital Section */}
            <Section title="Hospital Details" icon="🏥">
              <Grid2>
                <Field label="Hospital ID" value={form.hospital_id} onChange={update('hospital_id')} placeholder="HOSP-0001" />
                <Field label="Hospital Name" value={form.hospital_name} onChange={update('hospital_name')} />
                <Field label="City" value={form.city} onChange={update('city')} />
                <Field label="State" value={form.state} onChange={update('state')} />
                <div className="form-field" style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingTop: 8 }}>
                  <input
                    type="checkbox"
                    id="network"
                    checked={form.is_network_hospital}
                    onChange={update('is_network_hospital')}
                    style={{ width: 18, height: 18, accentColor: '#14b8a6' }}
                  />
                  <label htmlFor="network" style={{ fontSize: '0.875rem', color: '#f0f4ff', cursor: 'pointer' }}>
                    Network Hospital
                  </label>
                </div>
              </Grid2>
            </Section>

            {/* Medical Section */}
            <Section title="Medical Details" icon="🩺">
              <Grid2>
                <Field label="Primary Diagnosis" value={form.primary_diagnosis} onChange={update('primary_diagnosis')} />
                <Field label="ICD-10 Code" value={form.icd10_code} onChange={update('icd10_code')} placeholder="H26.9" />
                <Field label="Procedure Name" value={form.procedure_name} onChange={update('procedure_name')} />
                <Select label="Admission Type" value={form.admission_type} onChange={update('admission_type')} options={ADMISSION_TYPES} />
                <Field label="Admission Date" type="date" value={form.admission_date} onChange={update('admission_date')} />
                <Field label="Expected Discharge Date" type="date" value={form.expected_discharge_date} onChange={update('expected_discharge_date')} />
                <Field label="Estimated Cost (₹)" type="number" value={form.estimated_cost_inr} onChange={update('estimated_cost_inr')} />
                <Field label="Treating Physician" value={form.treating_physician} onChange={update('treating_physician')} />
              </Grid2>
              <div className="form-field" style={{ marginTop: 12 }}>
                <label className="form-label">Pre-Existing Conditions (comma-separated)</label>
                <input
                  className="form-input"
                  value={form.pre_existing_conditions}
                  onChange={update('pre_existing_conditions')}
                  placeholder="e.g. Type 2 Diabetes, Hypertension"
                />
              </div>
              <div className="form-field" style={{ marginTop: 12 }}>
                <label className="form-label">Additional Clinical Notes</label>
                <textarea
                  className="form-textarea"
                  value={form.free_text_notes}
                  onChange={update('free_text_notes')}
                  rows={3}
                  placeholder="Optional clinical notes..."
                  style={{ resize: 'vertical' }}
                />
              </div>
            </Section>

          </div>

          <motion.button
            type="submit"
            className="btn btn-primary"
            disabled={submitting}
            whileHover={{ scale: submitting ? 1 : 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{ marginTop: 24, width: '100%', justifyContent: 'center', padding: '14px 32px', fontSize: '1rem' }}
          >
            {submitting ? (
              <><span className="spinner" style={{ borderTopColor: 'white' }} /> Processing...</>
            ) : (
              <>'⚕' Submit for Pre-Authorization Analysis</>
            )}
          </motion.button>
        </form>
      </motion.div>
    </div>
  )
}

function Section({ title, icon, children }) {
  return (
    <div className="glass-card" style={{ padding: '20px 24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
        <span style={{ fontSize: '1.1rem' }}>{icon}</span>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#14b8a6' }}>{title}</h2>
      </div>
      {children}
    </div>
  )
}

function Grid2({ children }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16 }}>
      {children}
    </div>
  )
}

function Field({ label, type = 'text', value, onChange, placeholder }) {
  return (
    <div className="form-field">
      <label className="form-label">{label}</label>
      <input
        className="form-input"
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={type !== 'number' || value !== ''}
      />
    </div>
  )
}

function Select({ label, value, onChange, options }) {
  return (
    <div className="form-field">
      <label className="form-label">{label}</label>
      <select className="form-select" value={value} onChange={onChange}>
        {options.map(o => <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>)}
      </select>
    </div>
  )
}
