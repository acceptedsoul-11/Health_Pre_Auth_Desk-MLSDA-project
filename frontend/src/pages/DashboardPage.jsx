import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const OUTCOME_COLOR = {
  'approve-recommended': { bg: 'rgba(16,185,129,0.12)', border: 'rgba(16,185,129,0.4)', text: '#34d399', icon: '✅', label: 'Approve' },
  'query-to-hospital':   { bg: 'rgba(245,158,11,0.12)', border: 'rgba(245,158,11,0.4)',  text: '#fbbf24', icon: '❓', label: 'Query'   },
  'medical-review':      { bg: 'rgba(244,63,94,0.12)',  border: 'rgba(244,63,94,0.4)',   text: '#fb7185', icon: '🚨', label: 'Review'  },
}

const CITY_COLOR = { Hyderabad: '#14b8a6', Bangalore: '#818cf8' }

export default function DashboardPage() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')   // all | Hyderabad | Bangalore
  const [outcomeFilter, setOutcomeFilter] = useState('all')
  const [search, setSearch] = useState('')

  useEffect(() => {
    axios.get('/api/v1/demo-runs')
      .then(r => { setRuns(r.data.runs || []); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = runs.filter(r => {
    const city = r.hospital || ''
    const matchCity = filter === 'all' || city.toLowerCase().includes(filter.toLowerCase())
    const matchOutcome = outcomeFilter === 'all' || r.outcome === outcomeFilter
    const matchSearch = !search || (r.label || '').toLowerCase().includes(search.toLowerCase())
      || (r.patient || '').toLowerCase().includes(search.toLowerCase())
      || (r.policy_number || r.run_id || '').toLowerCase().includes(search.toLowerCase())
    return matchCity && matchOutcome && matchSearch
  })

  // Stats
  const total = runs.length
  const approved = runs.filter(r => r.outcome === 'approve-recommended').length
  const reviews  = runs.filter(r => r.outcome === 'medical-review').length
  const queries  = runs.filter(r => r.outcome === 'query-to-hospital').length
  const hyd = runs.filter(r => (r.hospital || '').toLowerCase().includes('hyderabad') || (r.hospital || '').toLowerCase().match(/apollo|yashoda|kims|care hospital|star hospital|fernandez|gleneagles|medicover|nims/i)).length
  const blr = total - hyd

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>

        {/* Header */}
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: 6 }}>Live Demo Dashboard</h1>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
            Pre-seeded records from hospitals in Hyderabad &amp; Bangalore — click any row to view full analysis
          </p>
        </div>

        {/* Stats Row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 14, marginBottom: 28 }}>
          {[
            { label: 'Total Records', value: total, color: '#14b8a6' },
            { label: 'Hyderabad', value: hyd, color: '#14b8a6' },
            { label: 'Bangalore', value: blr, color: '#818cf8' },
            { label: 'Approve Rec.', value: approved, color: '#10b981' },
            { label: 'Medical Review', value: reviews, color: '#f43f5e' },
            { label: 'Query Sent', value: queries, color: '#f59e0b' },
          ].map(s => (
            <motion.div key={s.label} whileHover={{ y: -2 }} className="glass-card" style={{ padding: '16px 20px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: s.color }}>{loading ? '—' : s.value}</div>
              <div style={{ fontSize: '0.72rem', color: '#94a3b8', marginTop: 4 }}>{s.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Filters */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          <input
            className="form-input"
            style={{ flex: '1 1 220px', maxWidth: 300, fontSize: '0.85rem' }}
            placeholder="Search by name, policy no., hospital…"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
          {['all', 'Hyderabad', 'Bangalore'].map(c => (
            <button key={c} onClick={() => setFilter(c)} className="btn"
              style={{
                background: filter === c ? (c === 'Bangalore' ? 'rgba(129,140,248,0.2)' : 'rgba(20,184,166,0.2)') : 'rgba(255,255,255,0.04)',
                border: `1px solid ${filter === c ? (c === 'Bangalore' ? '#818cf8' : '#14b8a6') : 'rgba(255,255,255,0.08)'}`,
                color: filter === c ? (c === 'Bangalore' ? '#818cf8' : '#14b8a6') : '#94a3b8',
                padding: '8px 16px', fontSize: '0.8rem',
              }}>
              {c === 'all' ? '🌍 All Cities' : c === 'Hyderabad' ? '🏙 Hyderabad' : '🌆 Bangalore'}
            </button>
          ))}
          {['all', 'approve-recommended', 'medical-review', 'query-to-hospital'].map(o => {
            const cfg = OUTCOME_COLOR[o] || { text: '#94a3b8', border: 'rgba(255,255,255,0.08)', bg: 'transparent', label: 'All Outcomes' }
            return (
              <button key={o} onClick={() => setOutcomeFilter(o)} className="btn"
                style={{
                  background: outcomeFilter === o ? cfg.bg : 'rgba(255,255,255,0.04)',
                  border: `1px solid ${outcomeFilter === o ? cfg.border : 'rgba(255,255,255,0.08)'}`,
                  color: outcomeFilter === o ? cfg.text : '#94a3b8',
                  padding: '8px 14px', fontSize: '0.78rem',
                }}>
                {o === 'all' ? '📋 All Outcomes' : `${cfg.icon} ${cfg.label}`}
              </button>
            )
          })}
        </div>

        {/* Table */}
        {loading ? (
          <div style={{ display: 'grid', gap: 10 }}>
            {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 64, borderRadius: 10 }} />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="glass-card" style={{ padding: 40, textAlign: 'center', color: '#475569' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>🔍</div>
            <p>No records match your filters</p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: 8 }}>
            {filtered.map((r, i) => {
              const cfg = OUTCOME_COLOR[r.outcome] || OUTCOME_COLOR['medical-review']
              const city = (r.hospital || '').includes('Hyderabad') || (r.hospital || '').match(/Apollo|Yashoda|KIMS|Care Hospital|Star Hospital|Fernandez|Gleneagles|Medicover|NIMS/i)
                ? 'Hyderabad' : 'Bangalore'
              return (
                <motion.div
                  key={r.run_id || i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  onClick={() => navigate(`/status/${r.run_id}`)}
                  style={{
                    padding: '14px 18px',
                    borderRadius: 10,
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(255,255,255,0.07)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    display: 'grid',
                    gridTemplateColumns: '1fr auto',
                    gap: 12,
                    alignItems: 'center',
                  }}
                  whileHover={{ borderColor: cfg.border, background: cfg.bg }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4, flexWrap: 'wrap' }}>
                      <span style={{
                        fontSize: '0.68rem', fontWeight: 700, padding: '2px 8px', borderRadius: 100,
                        background: `${CITY_COLOR[city]}20`, color: CITY_COLOR[city],
                        border: `1px solid ${CITY_COLOR[city]}40`, flexShrink: 0,
                      }}>{city}</span>
                      <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f0f4ff', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {r.label || r.run_id}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem', color: '#94a3b8', flexWrap: 'wrap' }}>
                      <span>🏥 {r.hospital}</span>
                      {r.policy_number && <span>📋 {r.policy_number}</span>}
                      {r.patient && <span>👤 {r.patient}</span>}
                      {r.procedure && <span>🩺 {(r.procedure || '').slice(0, 45)}</span>}
                      {r.policy_age_months !== undefined && (
                        <span style={{ color: r.policy_age_months < 24 ? '#fbbf24' : '#34d399' }}>
                          ⏱ {r.policy_age_months} months
                        </span>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 4, flexShrink: 0 }}>
                    <div style={{
                      padding: '4px 10px', borderRadius: 100, fontSize: '0.72rem', fontWeight: 700,
                      background: cfg.bg, border: `1px solid ${cfg.border}`, color: cfg.text,
                    }}>
                      {cfg.icon} {cfg.label}
                    </div>
                    <span style={{ fontSize: '0.65rem', color: '#475569', fontFamily: 'monospace' }}>
                      {r.run_id?.slice(0, 18)}
                    </span>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Legend */}
        <div style={{ marginTop: 24, padding: '14px 18px', borderRadius: 10, background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', fontSize: '0.75rem', color: '#475569' }}>
          💡 Click any record to view the full AI agent analysis, clause citations, and reasoning trace.
          Records marked ⏱ &lt;24 months are cataract/specific-disease waiting period test cases.
        </div>
      </motion.div>
    </div>
  )
}
