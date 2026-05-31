import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, Zap, Clock, FileText, Cpu, CheckCircle, AlertTriangle } from 'lucide-react'
import { api } from '../api'

const STAGE_COLORS = {
  guardrails: '#ef4444', query_processing: '#f59e0b', retrieval: '#06b6d4',
  reranking: '#a855f7', generation: '#6366f1', output_validation: '#10b981',
}

export default function QueryPage() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleQuery = async () => {
    if (!query.trim()) return
    setLoading(true); setError(null); setResult(null)
    try {
      const data = await api.query(query)
      setResult(data)
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const totalBreakdown = result?.latency_breakdown ? Object.values(result.latency_breakdown).reduce((a, b) => a + b, 0) : 0

  return (
    <div className="query-container">
      <motion.div className="page-header" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">🔍 Query Engine</h1>
        <p className="page-subtitle">Ask questions about your enterprise knowledge base</p>
      </motion.div>

      <motion.div className="query-input-wrap" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <input className="query-input" value={query} onChange={e => setQuery(e.target.value)}
          placeholder="Ask anything about company policies, technical docs..."
          onKeyDown={e => e.key === 'Enter' && handleQuery()} />
        <button className="query-btn" onClick={handleQuery} disabled={loading || !query.trim()}>
          {loading ? <><div className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> Searching...</>
            : <><Search size={16} /> Search</>}
        </button>
      </motion.div>

      {error && <motion.div className="card" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
        style={{ borderColor: 'var(--danger)', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--danger)' }}>
          <AlertTriangle size={18} /> {error}
        </div>
      </motion.div>}

      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {/* Answer */}
            <div className="answer-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <CheckCircle size={18} color="var(--success)" />
                <span className="card-title">Answer</span>
              </div>
              <div className="answer-text">{result.answer}</div>
              <div className="answer-meta">
                <span className="meta-badge"><Cpu size={12} /> {result.model || 'N/A'}</span>
                <span className="meta-badge"><Clock size={12} /> {result.latency?.toFixed(2)}s</span>
                <span className={`tag ${result.guardrail_status === 'passed' ? 'tag-success' : 'tag-danger'}`}>
                  {result.guardrail_status}
                </span>
                {result.grounding_score != null && (
                  <span className="meta-badge">Grounding: {(result.grounding_score * 100).toFixed(0)}%</span>
                )}
              </div>
            </div>

            {/* Latency Breakdown */}
            {result.latency_breakdown && Object.keys(result.latency_breakdown).length > 0 && (
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="card-title" style={{ marginBottom: 12 }}>⚡ Latency Breakdown</div>
                <div className="latency-bar">
                  {Object.entries(result.latency_breakdown).map(([stage, time]) => (
                    <div key={stage} className="latency-segment"
                      style={{ width: `${Math.max((time / totalBreakdown) * 100, 8)}%`, background: STAGE_COLORS[stage] || '#666' }}>
                      {(time * 1000).toFixed(0)}ms
                    </div>
                  ))}
                </div>
                <div className="latency-legend">
                  {Object.entries(result.latency_breakdown).map(([stage, time]) => (
                    <div key={stage} className="legend-item">
                      <div className="legend-dot" style={{ background: STAGE_COLORS[stage] || '#666' }} />
                      {stage} ({(time * 1000).toFixed(0)}ms)
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Sources */}
            {result.sources?.length > 0 && (
              <div className="card">
                <div className="card-title" style={{ marginBottom: 16 }}>
                  <FileText size={16} style={{ display: 'inline', marginRight: 8 }} />
                  Retrieved Sources ({result.sources.length})
                </div>
                <div className="sources-grid">
                  {result.sources.map((src, i) => (
                    <motion.div key={i} className="source-card" initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                      <div className="source-name"><FileText size={14} /> {src.source || 'Unknown'}</div>
                      <div className="source-content">{src.content}</div>
                      <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>Chunk #{src.chunk_id}</div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
