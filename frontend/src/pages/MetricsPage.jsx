import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Activity, Clock, Cpu, Database, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts'
import { api } from '../api'

const COLORS = ['#6366f1', '#a855f7', '#06b6d4', '#10b981', '#f59e0b', '#ef4444']

export default function MetricsPage() {
  const [health, setHealth] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [breakdown, setBreakdown] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [h, m, b] = await Promise.all([api.health(), api.metrics(), api.latencyBreakdown()])
      setHealth(h); setMetrics(m); setBreakdown(b.entries || [])
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [])

  const latencyTrend = breakdown.slice(-20).map((e, i) => ({ name: `Q${i + 1}`, total: e.total_latency,
    retrieval: e.breakdown?.retrieval || 0, reranking: e.breakdown?.reranking || 0, generation: e.breakdown?.generation || 0 }))

  const modelData = metrics?.models_used ? Object.entries(metrics.models_used).map(([name, count]) => ({ name: name || 'unknown', value: count })) : []

  return (
    <div>
      <motion.div className="page-header" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">📈 System Metrics</h1>
        <p className="page-subtitle">Real-time performance monitoring and health status</p>
      </motion.div>

      <button className="btn btn-outline" onClick={fetchAll} style={{ marginBottom: 24 }}><RefreshCw size={16} /> Refresh</button>

      {loading ? <div className="loader"><div className="spinner" /></div> : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Health Status */}
          {health && (
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">System Status</div>
                <div className="stat-value" style={{ color: health.status === 'healthy' ? 'var(--success)' : 'var(--warning)' }}>
                  {health.status === 'healthy' ? '🟢 Healthy' : '🟡 Degraded'}
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Total Queries</div>
                <div className="stat-value">{metrics?.total_queries || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Avg Latency</div>
                <div className="stat-value">{metrics?.avg_latency?.toFixed(2) || '0'}s</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">P95 Latency</div>
                <div className="stat-value" style={{ color: (metrics?.p95_latency || 0) < 3 ? 'var(--success)' : 'var(--danger)' }}>
                  {metrics?.p95_latency?.toFixed(2) || '0'}s
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Documents</div>
                <div className="stat-value">{health.components?.document_count || 0}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Vector Store</div>
                <div className="stat-value">{health.components?.vector_store ? <CheckCircle size={24} color="var(--success)" /> : <XCircle size={24} color="var(--danger)" />}</div>
              </div>
            </div>
          )}

          {/* Charts */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16, marginBottom: 24 }}>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}>Latency Trend (Stacked)</div>
              {latencyTrend.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={latencyTrend}>
                    <XAxis dataKey="name" tick={{ fill: '#8888a0', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#8888a0', fontSize: 10 }} />
                    <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                    <Bar dataKey="retrieval" stackId="a" fill="#06b6d4" name="Retrieval" radius={[0, 0, 0, 0]} />
                    <Bar dataKey="reranking" stackId="a" fill="#a855f7" name="Reranking" />
                    <Bar dataKey="generation" stackId="a" fill="#6366f1" name="Generation" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>No data yet. Run some queries first.</p>}
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}>Model Usage</div>
              {modelData.length > 0 ? (
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={modelData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}>
                      {modelData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              ) : <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 40 }}>No data yet.</p>}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
                {modelData.map((m, i) => (
                  <div key={i} className="legend-item"><div className="legend-dot" style={{ background: COLORS[i % COLORS.length] }} /> {m.name}: {m.value}</div>
                ))}
              </div>
            </div>
          </div>

          {/* Component Health */}
          {health?.components && (
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}>Component Health</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 }}>
                {Object.entries(health.components).filter(([k]) => typeof health.components[k] === 'boolean').map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 12, background: 'var(--bg-glass)', borderRadius: 10 }}>
                    {val ? <CheckCircle size={16} color="var(--success)" /> : <XCircle size={16} color="var(--danger)" />}
                    <span style={{ fontSize: 13 }}>{key.replace(/_/g, ' ')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
