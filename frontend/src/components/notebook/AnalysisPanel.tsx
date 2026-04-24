import { useEffect, useState } from 'react'
import { api, type AnalysisResult } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'

function RefreshIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  )
}

function LabIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v11l-5 5a1 1 0 0 0 .707 1.707H19.293A1 1 0 0 0 20 19l-5-5V3" />
    </svg>
  )
}

export default function AnalysisPanel({ notebookId }: { notebookId: number }) {
  const { documents } = useAppStore()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)

  const readyCount = documents.filter((d) => d.status === 'ready').length

  useEffect(() => {
    api.getAnalysis(notebookId).then((r) => setResult(r.result)).catch(console.error)
  }, [notebookId])

  const handleAnalyze = async () => {
    setLoading(true)
    try {
      const r = await api.triggerAnalysis(notebookId)
      setResult(r.result)
    } catch (e: any) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="analysis-panel">
      <div className="analysis-header">
        <h2 className="analysis-title">多文档关联分析</h2>
        <button
          className="btn btn-primary"
          disabled={loading || readyCount < 2}
          onClick={handleAnalyze}
        >
          {result ? <RefreshIcon /> : <LabIcon />}
          {result ? '重新分析' : '开始分析'}
        </button>
      </div>

      {readyCount < 2 && (
        <p className="analysis-notice">需要至少 2 个已就绪的文档才能进行关联分析</p>
      )}

      {loading && (
        <div className="analysis-loading">
          <div className="spinner" />
          <span>正在分析中，请稍候…</span>
        </div>
      )}

      {!loading && result && (
        <div className="analysis-grid">
          <div className="analysis-card">
            <div className="analysis-card-title">共同主题</div>
            <div className="analysis-card-tags">
              {(result.common_themes ?? []).map((t, i) => (
                <span key={i} className="tag tag-blue">{t}</span>
              ))}
            </div>
          </div>

          <div className="analysis-card">
            <div className="analysis-card-title">主要差异</div>
            <ul className="analysis-list">
              {(result.differences ?? []).map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="analysis-card">
            <div className="analysis-card-title">知识盲点</div>
            <ul className="analysis-list">
              {(result.blind_spots ?? []).map((item, i) => (
                <li key={i} style={{ color: 'var(--warning)' }}>{item}</li>
              ))}
            </ul>
          </div>

          <div className="analysis-card">
            <div className="analysis-card-title">综合见解</div>
            <p className="analysis-synthesis">{result.synthesis}</p>
          </div>
        </div>
      )}

      {!loading && !result && readyCount >= 2 && (
        <div className="empty-state">
          <div className="empty-state-icon">🔬</div>
          <div className="empty-state-text">点击「开始分析」按钮生成关联分析</div>
        </div>
      )}
    </div>
  )
}
