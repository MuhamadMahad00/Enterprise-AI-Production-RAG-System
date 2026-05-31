import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { Brain, Search, FileText, BarChart3, Shield, Activity, Settings } from 'lucide-react'
import QueryPage from './pages/QueryPage'
import DocumentsPage from './pages/DocumentsPage'
import EvaluationPage from './pages/EvaluationPage'
import GuardrailsPage from './pages/GuardrailsPage'
import MetricsPage from './pages/MetricsPage'
import './App.css'

const navItems = [
  { path: '/', icon: Search, label: 'Query Engine' },
  { path: '/documents', icon: FileText, label: 'Documents' },
  { path: '/evaluation', icon: BarChart3, label: 'Evaluation' },
  { path: '/guardrails', icon: Shield, label: 'Guardrails' },
  { path: '/metrics', icon: Activity, label: 'Metrics' },
]

export default function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: { background: '#1a1a2e', color: '#f0f0f5', border: '1px solid rgba(255,255,255,0.08)' }
      }} />
      <div className="app-layout">
        <aside className="sidebar">
          <div className="sidebar-logo">
            <Brain size={24} />
            <span>RAG System</span>
          </div>
          <nav>
            {navItems.map(({ path, icon: Icon, label }) => (
              <NavLink key={path} to={path} end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                <Icon size={18} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
          <div style={{ marginTop: 'auto', padding: '16px', borderTop: '1px solid var(--border)' }}>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>AI Production RAG v1.0</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>Teyzix Core Internship</div>
          </div>
        </aside>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<QueryPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
            <Route path="/guardrails" element={<GuardrailsPage />} />
            <Route path="/metrics" element={<MetricsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
