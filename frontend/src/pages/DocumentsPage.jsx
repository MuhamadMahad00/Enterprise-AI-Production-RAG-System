import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import { FileText, Upload, RefreshCw, Trash2, HardDrive } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../api'

export default function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)
  const [reindexing, setReindexing] = useState(false)
  const [dragOver, setDragOver] = useState(false)

  const fetchDocs = useCallback(async () => {
    try { const data = await api.listDocuments(); setDocs(data.documents || []) }
    catch { toast.error('Failed to load documents') }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const handleUpload = async (files) => {
    for (const file of files) {
      try {
        await api.upload(file)
        toast.success(`Uploaded: ${file.name}`)
      } catch { toast.error(`Failed: ${file.name}`) }
    }
    fetchDocs()
  }

  const handleReindex = async () => {
    setReindexing(true)
    try {
      const result = await api.reindex()
      toast.success(`Re-indexed: ${result.chunks_created} chunks from ${result.documents_processed} docs`)
    } catch (e) { toast.error(e.message) }
    finally { setReindexing(false) }
  }

  const handleIngest = async () => {
    try {
      const result = await api.ingest({})
      toast.success(`Ingested: ${result.chunks_created} chunks`)
    } catch (e) { toast.error(e.message) }
  }

  return (
    <div>
      <motion.div className="page-header" initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="page-title">📄 Document Management</h1>
        <p className="page-subtitle">Upload, manage, and re-index your document corpus</p>
      </motion.div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <button className="btn btn-primary" onClick={handleIngest}><HardDrive size={16} /> Ingest Documents</button>
        <button className="btn btn-outline" onClick={handleReindex} disabled={reindexing}>
          <RefreshCw size={16} className={reindexing ? 'spinning' : ''} />
          {reindexing ? 'Re-indexing...' : 'Re-index All'}
        </button>
      </div>

      {/* Upload Zone */}
      <motion.div className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files) }}
        onClick={() => { const input = document.createElement('input'); input.type = 'file'; input.multiple = true;
          input.accept = '.txt,.pdf,.md'; input.onchange = e => handleUpload(e.target.files); input.click() }}>
        <Upload size={40} color="var(--text-muted)" />
        <p style={{ marginTop: 16, fontSize: 15, color: 'var(--text-secondary)' }}>
          Drag & drop files here or click to browse
        </p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 8 }}>Supports .txt, .pdf, .md files</p>
      </motion.div>

      {/* Documents List */}
      <div className="card" style={{ marginTop: 24 }}>
        <div className="card-header">
          <span className="card-title">Indexed Documents ({docs.length})</span>
        </div>
        {loading ? <div className="loader"><div className="spinner" /></div> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Filename</th><th>Type</th><th>Size</th></tr></thead>
              <tbody>
                {docs.map((doc, i) => (
                  <motion.tr key={doc.filename} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
                    <td><div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><FileText size={16} color="var(--accent)" /> {doc.filename}</div></td>
                    <td><span className="tag tag-info">{doc.type}</span></td>
                    <td>{(doc.size_bytes / 1024).toFixed(1)} KB</td>
                  </motion.tr>
                ))}
                {docs.length === 0 && <tr><td colSpan={3} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 40 }}>No documents found</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
