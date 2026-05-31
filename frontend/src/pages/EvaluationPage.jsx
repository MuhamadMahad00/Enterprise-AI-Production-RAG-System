import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { BarChart3, Play, Download, CheckCircle, XCircle, Clock } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar, PolarRadiusAxis } from 'recharts'
import toast from 'react-hot-toast'
import { api } from '../api'

export default function EvaluationPage() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [questionCount, setQuestionCount] = useState(10)

  useEffect(() => {
    api.getReport().then(setReport).catch(() => {})
  }, [])

  const runEvaluation = async () => {
    setRunning(true)
    try {
      toast.loading('Running evaluation...', { id: 'eval' })
      const data = await api.evaluate(questionCount)
      toast.success('Evaluation complete!', { id: 'eval' })
      // Fetch the full report
      const fullReport = await api.getReport()
      setReport(fullReport)
    } catch (e) { toast.error(e.message, { id: 'eval' }) }
    finally { setRunning(false) }
  }

  const ragas = report?.ragas_scores || {}
  const radarData = [
    { metric: 'Faithfulness', score: (ragas.faithfulness || 0) * 100 },
    { metric: 'Relevancy', score: (ragas.answer_relevancy || 0) * 100 },
    { metric: 'Context Recall', score: (ragas.context_recall || 0) * 100 },
  ]

  return (
    <div>
      <motion.div className="page-header" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">📊 RAGAS Evaluation</h1>
        <p className="page-subtitle">Benchmark your RAG pipeline with automated evaluation metrics</p>
      </motion.div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <label style={{ fontSize: 14, color: 'var(--text-secondary)' }}>Questions:
            <select value={questionCount} onChange={e => setQuestionCount(+e.target.value)}
              style={{ marginLeft: 8, padding: '6px 12px', background: 'var(--bg-glass)', border: '1px solid var(--border)',
                borderRadius: 8, color: 'var(--text-primary)', fontSize: 14 }}>
              <option value={5}>5</option><option value={10}>10</option><option value={25}>25</option>
              <option value={50}>50</option><option value={100}>100</option>
            </select>
          </label>
          <button className="btn btn-primary" onClick={runEvaluation} disabled={running}>
            <Play size={16} /> {running ? 'Running...' : 'Run Evaluation'}
          </button>
        </div>
      </div>

      {report && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {/* Summary Stats */}
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Accuracy</div>
              <div className="stat-value" style={{ color: report.accuracy >= 0.7 ? 'var(--success)' : 'var(--warning)' }}>
                {(report.accuracy * 100).toFixed(1)}%
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Avg Latency</div>
              <div className="stat-value">{report.average_latency?.toFixed(2)}s</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">P95 Latency</div>
              <div className="stat-value" style={{ color: report.p95_latency < 3 ? 'var(--success)' : 'var(--danger)' }}>
                {report.p95_latency?.toFixed(2)}s
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">SLA Met</div>
              <div className="stat-value">
                {report.latency_sla_met ? <span style={{ color: 'var(--success)' }}>✅ Yes</span> : <span style={{ color: 'var(--danger)' }}>❌ No</span>}
              </div>
            </div>
          </div>

          {/* RAGAS Scores */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}>RAGAS Scores</div>
              <div className="scores-row">
                {radarData.map(item => (
                  <div key={item.metric} className="score-item">
                    <div className="score-ring" style={{
                      background: `conic-gradient(var(--accent) ${item.score * 3.6}deg, var(--bg-glass) 0deg)`,
                    }}>
                      <div style={{ width: 60, height: 60, borderRadius: '50%', background: 'var(--bg-secondary)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16, fontWeight: 700 }}>
                        {item.score.toFixed(0)}%
                      </div>
                    </div>
                    <div className="score-label">{item.metric}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}>Score Distribution</div>
              <ResponsiveContainer width="100%" height={200}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255,255,255,0.1)" />
                  <PolarAngleAxis dataKey="metric" tick={{ fill: '#8888a0', fontSize: 12 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.3} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Latency Chart */}
          {report.results?.length > 0 && (
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-title" style={{ marginBottom: 16 }}>Latency per Question</div>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={report.results.slice(0, 30).map((r, i) => ({ name: `Q${i + 1}`, latency: r.latency }))}>
                  <XAxis dataKey="name" tick={{ fill: '#8888a0', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#8888a0', fontSize: 10 }} />
                  <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8 }} />
                  <Bar dataKey="latency" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Results Table */}
          <div className="card">
            <div className="card-title" style={{ marginBottom: 16 }}>Detailed Results</div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Question</th><th>Grounded</th><th>Faithfulness</th><th>Relevancy</th><th>Recall</th><th>Latency</th></tr></thead>
                <tbody>
                  {report.results?.slice(0, 50).map((r, i) => (
                    <tr key={i}>
                      <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.question}</td>
                      <td>{r.grounded ? <CheckCircle size={16} color="var(--success)" /> : <XCircle size={16} color="var(--danger)" />}</td>
                      <td><span className={`tag ${r.faithfulness >= 0.7 ? 'tag-success' : 'tag-warning'}`}>{(r.faithfulness * 100).toFixed(0)}%</span></td>
                      <td><span className={`tag ${r.relevancy >= 0.5 ? 'tag-success' : 'tag-warning'}`}>{(r.relevancy * 100).toFixed(0)}%</span></td>
                      <td><span className={`tag ${r.context_recall >= 0.5 ? 'tag-success' : 'tag-warning'}`}>{(r.context_recall * 100).toFixed(0)}%</span></td>
                      <td><Clock size={12} style={{ marginRight: 4 }} />{r.latency?.toFixed(2)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
