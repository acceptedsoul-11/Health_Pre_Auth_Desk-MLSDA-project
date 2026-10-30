import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import toast from 'react-hot-toast'

const OUTCOME_CONFIG = {
  'approve-recommended': { label: 'Approve Recommended', color: '#10b981', bg: 'rgba(16,185,129,0.12)', icon: '✅' },
  'query-to-hospital': { label: 'Query to Hospital', color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', icon: '❓' },
  'medical-review': { label: 'Medical Review Required', color: '#f43f5e', bg: 'rgba(244,63,94,0.12)', icon: '🚨' },
}

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: '#f59e0b', spinner: true },
  processing: { label: 'Processing', color: '#06b6d4', spinner: true },
  completed: { label: 'Completed', color: '#10b981', spinner: false },
  failed: { label: 'Failed', color: '#f43f5e', spinner: false },
}

export default function StatusPage() {
  const { runId: paramRunId } = useParams()
  const navigate = useNavigate()
  const [runId, setRunId] = useState(paramRunId || '')
  const [inputRunId, setInputRunId] = useState(paramRunId || '')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [polling, setPolling] = useState(false)
  const [feedback, setFeedback] = useState({ submitted: false, satisfactory: null, reason: '' })

  const fetchStatus = useCallback(async (id) => {
    if (!id) return
    try {
      const res = await axios.get(`/api/v1/preauth/${id}`)
      setData(res.data)
      return res.data.status
    } catch (err) {
      if (err.response?.status === 404) {
        toast.error('Run not found')
        setData(null)
      }
      return null
    }
  }, [])

  // Auto-poll while pending/processing
  useEffect(() => {
    if (!runId) return
    setLoading(true)
    fetchStatus(runId).then((status) => {
      setLoading(false)
      if (status === 'pending' || status === 'processing') {
        setPolling(true)
      }
    })
  }, [runId, fetchStatus])

  useEffect(() => {
    if (!polling || !runId) return
    const interval = setInterval(async () => {
      const status = await fetchStatus(runId)
      if (status === 'completed' || status === 'failed') {
        setPolling(false)
        clearInterval(interval)
        if (status === 'completed') toast.success('Analysis complete!')
        else toast.error('Processing failed')
      }
    }, 2500)
    return () => clearInterval(interval)
  }, [polling, runId, fetchStatus])

  const handleSearch = (e) => {
    e.preventDefault()
    const trimmed = inputRunId.trim()
    if (!trimmed) return
    setRunId(trimmed)
    setData(null)
    navigate(`/status/${trimmed}`)
  }

  const submitFeedback = async (satisfactory) => {
    try {
      await axios.post('/api/v1/feedback', {
        run_id: runId,
        satisfactory,
        reason: feedback.reason || null,
      })
      setFeedback(f => ({ ...f, submitted: true, satisfactory }))
      toast.success('Feedback submitted. Thank you!')
    } catch {
      toast.error('Failed to submit feedback')
    }
  }

  const statusCfg = data ? STATUS_CONFIG[data.status] || STATUS_CONFIG.pending : null
  const outcomeCfg = data?.outcome ? OUTCOME_CONFIG[data.outcome] : null

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: 24 }}>
          Track Pre-Authorization
        </h1>

        {/* Search */}
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: 12, marginBottom: 32 }}>
          <input
            className="form-input"
            value={inputRunId}
            onChange={e => setInputRunId(e.target.value)}
            placeholder="Enter Run ID (e.g. RUN-ABC123...)"
            style={{ flex: 1, fontSize: '0.9rem' }}
          />
          <button type="submit" className="btn btn-primary">Track</button>
        </form>

        {/* Loading skeleton */}
        {loading && (
          <div style={{ display: 'grid', gap: 16 }}>
            {[1,2,3].map(i => (
              <div key={i} className="skeleton" style={{ height: 80, borderRadius: 12 }} />
            ))}
          </div>
        )}

        {/* Result */}
        <AnimatePresence>
          {data && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              style={{ display: 'grid', gap: 16 }}
            >
              {/* Status Header */}
              <div className="glass-card" style={{ padding: 24 }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
                  <div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>Run ID</div>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.9rem', color: '#14b8a6', letterSpacing: '0.05em' }}>{data.run_id}</div>
                  </div>
                  <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '6px 14px', borderRadius: 100,
                      background: `${statusCfg?.color}20`,
                      border: `1px solid ${statusCfg?.color}50`,
                      color: statusCfg?.color,
                      fontSize: '0.8rem', fontWeight: 600,
                    }}>
                      {statusCfg?.spinner && <span className="spinner" style={{ borderTopColor: statusCfg.color, width: 14, height: 14 }} />}
                      {statusCfg?.label}
                    </div>
                    {outcomeCfg && (
                      <div style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '6px 14px', borderRadius: 100,
                        background: outcomeCfg.bg,
                        border: `1px solid ${outcomeCfg.color}50`,
                        color: outcomeCfg.color,
                        fontSize: '0.8rem', fontWeight: 700,
                      }}>
                        {outcomeCfg.icon} {outcomeCfg.label}
                      </div>
                    )}
                  </div>
                </div>

                {data.processing_time_ms && (
                  <div style={{ marginTop: 12, fontSize: '0.75rem', color: '#475569' }}>
                    ⏱ Processed in {(data.processing_time_ms / 1000).toFixed(1)}s
                    {data.prompt_version && ` · Prompt: ${data.prompt_version}`}
                    {data.correlation_id && ` · Trace: ${data.correlation_id.slice(0, 8)}`}
                  </div>
                )}
              </div>

              {/* Recommendation */}
              {data.recommendation && (
                <RecommendationCard data={data} outcomeCfg={outcomeCfg} />
              )}

              {/* Citations */}
              {data.citations?.length > 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#14b8a6', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Policy Citations ({data.citations.length})
                  </h3>
                  <div style={{ display: 'grid', gap: 12 }}>
                    {data.citations.map((c, i) => (
                      <CitationCard key={i} citation={c} />
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Steps */}
              {data.agent_steps?.length > 0 && (
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#14b8a6', marginBottom: 16, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Agent Reasoning Trace ({data.agent_steps.length} steps)
                  </h3>
                  <div style={{ display: 'grid', gap: 8 }}>
                    {data.agent_steps.map((s, i) => (
                      <StepCard key={i} step={s} />
                    ))}
                  </div>
                </div>
              )}

              {/* Token Usage */}
              {data.token_usage && (
                <div className="glass-card" style={{ padding: 20 }}>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#94a3b8', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Token Usage
                  </h3>
                  <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                    <Metric label="Prompt Tokens" value={data.token_usage.prompt_tokens} />
                    <Metric label="Completion Tokens" value={data.token_usage.completion_tokens} />
                    <Metric label="Total Tokens" value={data.token_usage.total_tokens} />
                    <Metric label="Est. Cost" value={`$${(data.token_usage.estimated_cost_usd || 0).toFixed(4)}`} />
                  </div>
                </div>
              )}

              {/* Feedback */}
              {data.status === 'completed' && !feedback.submitted && (
                <div className="glass-card" style={{ padding: 24 }}>
                  <h3 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#94a3b8', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Was this recommendation helpful?
                  </h3>
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
                    <button className="btn btn-ghost" onClick={() => submitFeedback(true)} style={{ color: '#10b981', borderColor: 'rgba(16,185,129,0.4)' }}>
                      👍 Yes, Satisfactory
                    </button>
                    <button className="btn btn-ghost" onClick={() => submitFeedback(false)} style={{ color: '#f43f5e', borderColor: 'rgba(244,63,94,0.4)' }}>
                      👎 No, Needs Review
                    </button>
                    <input
                      className="form-input"
                      style={{ flex: 1, minWidth: 200 }}
                      placeholder="Optional reason..."
                      value={feedback.reason}
                      onChange={e => setFeedback(f => ({ ...f, reason: e.target.value }))}
                    />
                  </div>
                </div>
              )}

              {feedback.submitted && (
                <div style={{ padding: '12px 20px', borderRadius: 12, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', color: '#34d399', fontSize: '0.875rem' }}>
                  ✓ Feedback recorded. Thank you for improving the system.
                </div>
              )}

            </motion.div>
          )}
        </AnimatePresence>

        {!runId && !loading && (
          <div style={{ textAlign: 'center', padding: '60px 0', color: '#475569' }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
            <p>Enter a Run ID to track your pre-authorization request</p>
            <p style={{ fontSize: '0.8rem', marginTop: 8 }}>
              Run IDs are returned immediately after submission
            </p>
          </div>
        )}
      </motion.div>
    </div>
  )
}

function CitationCard({ citation }) {
  return (
    <div style={{
      padding: '14px 16px', borderRadius: 10,
      background: 'rgba(255,255,255,0.03)',
      border: `1px solid ${citation.verified ? 'rgba(16,185,129,0.3)' : 'rgba(244,63,94,0.3)'}`,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
        <div>
          <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#14b8a6', marginRight: 8 }}>
            {citation.clause_id}
          </span>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#e2e8f0' }}>
            {citation.clause_title}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexShrink: 0 }}>
          <span style={{ fontSize: '0.7rem', color: citation.verified ? '#10b981' : '#f43f5e' }}>
            {citation.verified ? '✓ Verified' : '✗ Unverified'}
          </span>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
            {(citation.relevance_score * 100).toFixed(0)}% match
          </span>
        </div>
      </div>
      <p style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic', lineHeight: 1.5 }}>
        "{citation.excerpt}"
      </p>
      <div style={{ marginTop: 6, fontSize: '0.7rem', color: '#475569' }}>
        {citation.source_document} {citation.page_or_section && `· p.${citation.page_or_section}`}
      </div>
    </div>
  )
}

function StepCard({ step }) {
  const [expanded, setExpanded] = useState(false)
  const isToolCall = step.action === 'tool_call'
  return (
    <div
      style={{
        padding: '10px 14px', borderRadius: 8,
        background: isToolCall ? 'rgba(129,140,248,0.05)' : 'rgba(20,184,166,0.04)',
        border: `1px solid ${isToolCall ? 'rgba(129,140,248,0.2)' : 'rgba(20,184,166,0.15)'}`,
        cursor: 'pointer',
      }}
      onClick={() => setExpanded(e => !e)}
    >
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <span style={{ fontSize: '0.7rem', color: '#475569', minWidth: 20 }}>#{step.step_index}</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: isToolCall ? '#818cf8' : '#14b8a6' }}>
          {step.agent_name}
        </span>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>→</span>
        <span style={{ fontSize: '0.8rem', color: '#e2e8f0', flex: 1 }}>
          {isToolCall ? `🔧 ${step.tool_called}` : '💬 LLM Response'}
        </span>
        <span style={{ fontSize: '0.65rem', color: '#475569' }}>{expanded ? '▲' : '▼'}</span>
      </div>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden', marginTop: 10 }}
          >
            {step.tool_input && (
              <div className="code-block" style={{ marginBottom: 8 }}>
                Input: {JSON.stringify(step.tool_input, null, 2)}
              </div>
            )}
            {step.tool_output && (
              <div className="code-block">Output: {step.tool_output.slice(0, 500)}</div>
            )}
            {step.reasoning && !isToolCall && (
              <div className="code-block">{step.reasoning.slice(0, 500)}</div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function Metric({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: '0.7rem', color: '#475569', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#14b8a6' }}>{value || 0}</div>
    </div>
  )
}

function RecommendationCard({ data, outcomeCfg }) {
  const text = data.recommendation || ''
  const escalationReason = data.escalation_reason

  // Helper to highlight clause codes like SCHIP-WAIT-002, SCHIP-COV-001, etc.
  const highlightClauseCodes = (str) => {
    if (!str) return str
    const parts = str.split(/([A-Z]{3,5}-[A-Z0-9]+-[0-9]+)/g)
    return parts.map((part, idx) => {
      if (/^[A-Z]{3,5}-[A-Z0-9]+-[0-9]+$/.test(part)) {
        return (
          <span
            key={idx}
            style={{
              padding: '2px 8px',
              margin: '0 3px',
              borderRadius: 6,
              background: 'rgba(20, 184, 166, 0.18)',
              border: '1px solid rgba(20, 184, 166, 0.45)',
              color: '#2dd4bf',
              fontFamily: 'monospace',
              fontSize: '0.85em',
              fontWeight: 700,
              letterSpacing: '0.03em',
              display: 'inline-block',
            }}
          >
            {part}
          </span>
        )
      }
      return part
    })
  }

  // Parse lines into structured sections
  const lines = text.split('\n').map(l => l.trim()).filter(Boolean)
  const sections = []
  let current = null

  lines.forEach(line => {
    if (/^(Executive Summary|Summary|Primary Assessment):?/i.test(line)) {
      if (current) sections.push(current)
      current = {
        title: 'Executive Summary',
        icon: '📋',
        badgeColor: '#06b6d4',
        items: []
      }
      const rest = line.replace(/^(Executive Summary|Summary|Primary Assessment):?\s*/i, '').trim()
      if (rest) current.items.push(rest)
    } else if (/^(Key Evaluation Points|Evaluation Points|Key Points|Key Findings):?/i.test(line)) {
      if (current) sections.push(current)
      current = {
        title: 'Key Evaluation Points',
        icon: '🔍',
        badgeColor: '#14b8a6',
        items: []
      }
      const rest = line.replace(/^(Key Evaluation Points|Evaluation Points|Key Points|Key Findings):?\s*/i, '').trim()
      if (rest) current.items.push(rest)
    } else if (/^(Actionable Remarks|Remarks|Recommendations?|Next Steps):?/i.test(line)) {
      if (current) sections.push(current)
      current = {
        title: 'Actionable Remarks & Next Steps',
        icon: '📌',
        badgeColor: '#818cf8',
        items: []
      }
      const rest = line.replace(/^(Actionable Remarks|Remarks|Recommendations?|Next Steps):?\s*/i, '').trim()
      if (rest) current.items.push(rest)
    } else {
      if (!current) {
        current = {
          title: 'Clinical & Policy Assessment',
          icon: '📋',
          badgeColor: '#14b8a6',
          items: []
        }
      }
      const cleanLine = line.replace(/^[•\-\*]\s*/, '').trim()
      if (cleanLine) current.items.push(cleanLine)
    }
  })
  if (current) sections.push(current)

  const isStructured = sections.length > 1 || (sections[0]?.items?.length > 1)

  return (
    <div className="glass-card" style={{ padding: 26, position: 'relative', overflow: 'hidden' }}>
      {/* Background glow */}
      <div style={{
        position: 'absolute', top: -40, right: -40, width: 220, height: 220,
        background: outcomeCfg ? outcomeCfg.color : '#14b8a6',
        filter: 'blur(90px)', opacity: 0.09, pointerEvents: 'none', borderRadius: '50%'
      }} />

      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 9,
            background: 'linear-gradient(135deg, rgba(20,184,166,0.35), rgba(6,182,212,0.18))',
            border: '1px solid rgba(20,184,166,0.45)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 17
          }}>
            🤖
          </div>
          <div>
            <h3 style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.04em', margin: 0, textTransform: 'uppercase' }}>
              AI Pre-Authorization Analysis
            </h3>
            <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Multi-Agent Verification · Star Health Comprehensive Policy Corpus
            </span>
          </div>
        </div>

        {outcomeCfg && (
          <div style={{
            padding: '6px 14px', borderRadius: 20,
            background: outcomeCfg.bg,
            border: `1px solid ${outcomeCfg.color}60`,
            color: outcomeCfg.color,
            fontSize: '0.78rem', fontWeight: 700,
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <span>{outcomeCfg.icon}</span>
            <span>{outcomeCfg.label}</span>
          </div>
        )}
      </div>

      {/* Render sections */}
      {isStructured ? (
        <div style={{ display: 'grid', gap: 16 }}>
          {sections.map((sec, sIdx) => (
            <div key={sIdx} style={{
              background: 'rgba(15, 23, 42, 0.45)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              borderRadius: 12,
              padding: '16px 20px',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                fontSize: '0.8rem', fontWeight: 700,
                color: sec.badgeColor,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                marginBottom: 12,
              }}>
                <span>{sec.icon}</span>
                <span>{sec.title}</span>
              </div>

              {sec.items.length === 1 && !sec.title.includes('Key') ? (
                <p style={{ color: '#e2e8f0', lineHeight: 1.7, fontSize: '0.92rem', margin: 0 }}>
                  {highlightClauseCodes(sec.items[0])}
                </p>
              ) : (
                <div style={{ display: 'grid', gap: 9 }}>
                  {sec.items.map((item, iIdx) => (
                    <div key={iIdx} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 10,
                      background: 'rgba(255, 255, 255, 0.02)',
                      padding: '10px 14px',
                      borderRadius: 8,
                      border: '1px solid rgba(255, 255, 255, 0.04)',
                    }}>
                      <span style={{ color: sec.badgeColor, fontSize: '0.85rem', marginTop: 2, flexShrink: 0 }}>
                        {sec.title.includes('Remarks') ? '✔' : '•'}
                      </span>
                      <span style={{ color: '#e2e8f0', fontSize: '0.88rem', lineHeight: 1.6 }}>
                        {highlightClauseCodes(item)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div style={{
          background: 'rgba(15, 23, 42, 0.5)',
          border: '1px solid rgba(20, 184, 166, 0.2)',
          borderRadius: 12,
          padding: '18px 20px',
        }}>
          <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#14b8a6', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 10 }}>
            📋 Clinical Evaluation Summary
          </div>
          <p style={{ color: '#e2e8f0', lineHeight: 1.7, fontSize: '0.92rem', margin: 0 }}>
            {highlightClauseCodes(text)}
          </p>
        </div>
      )}

      {/* Escalation Reason Banner */}
      {escalationReason && (
        <div style={{
          marginTop: 18,
          padding: '16px 20px',
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(244,63,94,0.12), rgba(244,63,94,0.04))',
          border: '1px solid rgba(244,63,94,0.35)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 16 }}>🚨</span>
            <strong style={{ fontSize: '0.85rem', color: '#fca5a5', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Primary Escalation Driver & Regulatory Constraint
            </strong>
          </div>
          <p style={{ margin: 0, fontSize: '0.88rem', color: '#fecdd3', lineHeight: 1.6, paddingLeft: 26 }}>
            {highlightClauseCodes(escalationReason)}
          </p>
        </div>
      )}
    </div>
  )
}
