import React, { useState } from 'react'
import { motion } from 'framer-motion'
import axios from 'axios'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

const CATARACT_PAYLOAD = {
  patient: {
    patient_id: "PAT-000001",
    full_name: "Ramesh Kumar",
    date_of_birth: "1965-03-15",
    gender: "male",
    age_at_admission: 61,
  },
  policy: {
    policy_number: "SH-123456789",
    policy_holder_name: "Ramesh Kumar",
    policy_inception_date: "2025-11-15",
    policy_expiry_date: "2026-11-14",
    sum_insured_inr: 500000,
    prior_claims_inr: 0,
  },
  hospital: {
    hospital_id: "HOSP-0001",
    hospital_name: "Apollo Hospitals Chennai",
    is_network_hospital: true,
    city: "Chennai",
    state: "Tamil Nadu",
  },
  medical: {
    primary_diagnosis: "Age-related cataract",
    icd10_code: "H26.9",
    procedure_name: "Phacoemulsification with IOL implantation",
    admission_date: new Date().toISOString().split('T')[0],
    expected_discharge_date: new Date().toISOString().split('T')[0],
    admission_type: "day_care",
    estimated_cost_inr: 75000,
    pre_existing_conditions: ["Type 2 Diabetes"],
    treating_physician: "Dr. Priya Venkat",
  },
}

const EXPECTED_FLOW = [
  {
    step: 1,
    agent: 'Classifier Agent',
    action: 'Extract request fields',
    detail: 'Policy age: 11 months | Procedure: Cataract Surgery | ICD-10: H26.9',
    color: '#14b8a6',
  },
  {
    step: 2,
    agent: 'Classifier Agent',
    action: 'Broad corpus search',
    query: '"cataract surgery coverage ophthalmology"',
    result: 'Finds SCHIP-COV-002 (Day Care Coverage) — general cover exists',
    color: '#14b8a6',
  },
  {
    step: 3,
    agent: 'Classifier Agent',
    action: 'Specific waiting period search',
    query: '"cataract 24 month waiting period specific disease"',
    result: 'CRITICAL: Finds SCHIP-WAIT-002 — 24-month waiting period for cataract surgery',
    color: '#818cf8',
    critical: true,
  },
  {
    step: 4,
    agent: 'Classifier Agent',
    action: 'Full clause retrieval',
    detail: 'Calls lookup_clause_by_id("SCHIP-WAIT-002") — retrieves complete clause text',
    color: '#14b8a6',
  },
  {
    step: 5,
    agent: 'Verifier Agent',
    action: 'Cross-reference policy age vs waiting period',
    detail: 'Policy age: 11 months < Required: 24 months → WAITING PERIOD NOT MET',
    color: '#f43f5e',
    critical: true,
  },
  {
    step: 6,
    agent: 'Self-Verification',
    action: 'Verify all citations against source',
    detail: 'SCHIP-WAIT-002 excerpt verified ✓ | SCHIP-COV-002 excerpt verified ✓',
    color: '#10b981',
  },
  {
    step: 7,
    agent: 'Pipeline Output',
    action: 'Route to medical-review',
    detail: 'Escalation reason: 24-month specific disease waiting period not satisfied (11 months elapsed)',
    color: '#f43f5e',
    critical: true,
  },
]

export default function DemoPage() {
  const navigate = useNavigate()
  const [running, setRunning] = useState(false)
  const [runId, setRunId] = useState(null)
  const [visibleSteps, setVisibleSteps] = useState(0)

  const runDemo = async () => {
    setRunning(true)
    setVisibleSteps(0)
    setRunId(null)

    // Animate steps
    for (let i = 1; i <= EXPECTED_FLOW.length; i++) {
      await new Promise(r => setTimeout(r, 600))
      setVisibleSteps(i)
    }

    try {
      const res = await axios.post('/api/v1/preauth', CATARACT_PAYLOAD)
      const { run_id } = res.data
      setRunId(run_id)
      toast.success(`Section 4.1 test submitted! Run ID: ${run_id}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || err.message)
    } finally {
      setRunning(false)
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

        {/* Header */}
        <div className="glass-card" style={{
          padding: '28px 32px', marginBottom: 32,
          background: 'linear-gradient(135deg, rgba(244,63,94,0.06), rgba(129,140,248,0.04))',
          borderColor: 'rgba(244,63,94,0.2)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
            <span style={{ fontSize: 28 }}>🔬</span>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Section 4.1 — Cataract Test Case</h1>
          </div>
          <p style={{ color: '#94a3b8', lineHeight: 1.7, marginBottom: 16 }}>
            <strong style={{ color: '#f0f4ff' }}>Scenario:</strong> "Planned cataract surgery. The policy was issued eleven months ago."
          </p>
          <div style={{
            padding: '12px 16px', borderRadius: 8,
            background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.3)',
            fontSize: '0.85rem', color: '#fbbf24',
          }}>
            ⚠️ A naive search matches general surgical cover (SCHIP-COV-001). The agent must independently
            discover the <strong>24-month specific waiting period</strong> clause (SCHIP-WAIT-002) and
            cross-reference it against the 11-month policy age to trigger escalation.
          </div>
        </div>

        {/* Payload Preview */}
        <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
          <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#94a3b8', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
            Test Payload
          </h3>
          <div className="code-block">
            {JSON.stringify(CATARACT_PAYLOAD, null, 2)}
          </div>
        </div>

        {/* Run Button */}
        <motion.button
          className="btn btn-primary"
          onClick={runDemo}
          disabled={running}
          whileHover={{ scale: running ? 1 : 1.02 }}
          style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '1rem', marginBottom: 32 }}
        >
          {running
            ? <><span className="spinner" style={{ borderTopColor: 'white' }} /> Running Section 4.1 Demo...</>
            : '▶ Run Cataract Test Case (Section 4.1)'}
        </motion.button>

        {/* Agent Flow Visualization */}
        {visibleSteps > 0 && (
          <div className="glass-card" style={{ padding: 24, marginBottom: 24 }}>
            <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#14b8a6', marginBottom: 20, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Agent Reasoning Flow
            </h3>
            <div style={{ display: 'grid', gap: 10 }}>
              {EXPECTED_FLOW.slice(0, visibleSteps).map((s, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  style={{
                    padding: '14px 16px', borderRadius: 10,
                    background: s.critical ? `${s.color}10` : 'rgba(255,255,255,0.03)',
                    border: `1px solid ${s.color}${s.critical ? '50' : '25'}`,
                  }}
                >
                  <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{
                      width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                      background: s.color, display: 'flex', alignItems: 'center',
                      justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, color: 'white',
                    }}>{s.step}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', gap: 10, marginBottom: 4, flexWrap: 'wrap' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 700, color: s.color }}>{s.agent}</span>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#e2e8f0' }}>{s.action}</span>
                        {s.critical && <span style={{ fontSize: '0.65rem', background: `${s.color}25`, color: s.color, padding: '2px 8px', borderRadius: 100 }}>CRITICAL</span>}
                      </div>
                      {s.query && <div style={{ fontSize: '0.75rem', color: '#818cf8', fontFamily: 'monospace', marginBottom: 4 }}>Query: {s.query}</div>}
                      <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>{s.result || s.detail}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )}

        {/* Final Outcome */}
        {visibleSteps >= EXPECTED_FLOW.length && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass-card"
            style={{
              padding: 24, marginBottom: 24,
              background: 'rgba(244,63,94,0.06)',
              borderColor: 'rgba(244,63,94,0.4)',
            }}
          >
            <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
              <span style={{ fontSize: 24 }}>🚨</span>
              <div>
                <h3 style={{ color: '#f43f5e', fontWeight: 700, marginBottom: 4 }}>OUTCOME: medical-review</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.875rem', lineHeight: 1.7 }}>
                  The agent correctly identified that while cataract surgery is generally covered (SCHIP-COV-002),
                  the <strong style={{ color: '#fca5a5' }}>specific 24-month waiting period</strong> clause (SCHIP-WAIT-002)
                  takes precedence. With only 11 months of policy tenure, the request is escalated to medical review —
                  the system <strong style={{ color: '#fca5a5' }}>never automatically authorizes</strong>.
                </p>
              </div>
            </div>
            {runId && (
              <button
                className="btn btn-primary"
                onClick={() => navigate(`/status/${runId}`)}
                style={{ marginTop: 8 }}
              >
                View Full Analysis → Run ID: {runId}
              </button>
            )}
          </motion.div>
        )}

      </motion.div>
    </div>
  )
}
