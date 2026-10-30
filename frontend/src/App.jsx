import React from 'react'
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import SubmitPage from './pages/SubmitPage.jsx'
import StatusPage from './pages/StatusPage.jsx'
import DemoPage from './pages/DemoPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'

const navLinks = [
  { to: '/', label: '📝 Submit', exact: true },
  { to: '/dashboard', label: '🏥 Live Records' },
  { to: '/status', label: '🔍 Track Status' },
  { to: '/demo', label: '🔬 Cataract Demo' },
]

export default function App() {
  return (
    <Router>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        {/* ── Nav ──────────────────────────────────────────────── */}
        <nav style={{
          position: 'sticky', top: 0, zIndex: 100,
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          background: 'rgba(10,15,30,0.85)',
        }}>
          <div style={{
            maxWidth: 1200, margin: '0 auto', padding: '0 24px',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            height: 64,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: 'linear-gradient(135deg, #14b8a6, #06b6d4)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 18, fontWeight: 800, color: 'white',
              }}>⚕</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '0.95rem', color: '#f0f4ff' }}>
                  Pre-Auth Desk
                </div>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                  Star Health · AI-Powered
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 4 }}>
              {navLinks.map(link => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.exact}
                  style={({ isActive }) => ({
                    padding: '8px 16px',
                    borderRadius: 8,
                    textDecoration: 'none',
                    fontSize: '0.875rem',
                    fontWeight: 500,
                    transition: 'all 0.2s',
                    background: isActive ? 'rgba(20,184,166,0.15)' : 'transparent',
                    color: isActive ? '#14b8a6' : '#94a3b8',
                    border: isActive ? '1px solid rgba(20,184,166,0.3)' : '1px solid transparent',
                  })}
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
          </div>
        </nav>

        {/* ── Routes ────────────────────────────────────────────── */}
        <main style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<SubmitPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/status" element={<StatusPage />} />
            <Route path="/status/:runId" element={<StatusPage />} />
            <Route path="/demo" element={<DemoPage />} />
          </Routes>
        </main>

        {/* ── Footer ────────────────────────────────────────────── */}
        <footer style={{
          borderTop: '1px solid rgba(255,255,255,0.06)',
          background: 'rgba(10,15,30,0.85)',
          padding: '16px 24px',
          textAlign: 'center',
          fontSize: '0.85rem',
          color: '#94a3b8',
          letterSpacing: '0.01em',
        }}>
          Built as a part of MLSDA Mini project-PES1UG24AM240,PES1UG24AM241,PES1UG24AM251,PES1UG24AM253
        </footer>

        <Toaster
          position="bottom-right"
          toastOptions={{
            style: {
              background: 'rgba(13,21,38,0.95)',
              border: '1px solid rgba(20,184,166,0.3)',
              color: '#f0f4ff',
              backdropFilter: 'blur(20px)',
            },
          }}
        />
      </div>
    </Router>
  )
}
