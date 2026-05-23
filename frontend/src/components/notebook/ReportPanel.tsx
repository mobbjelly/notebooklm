import { useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'
import { api, type ReportResult, type ReportStatus } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'

function RefreshIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
    </svg>
  )
}

function ReportIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="8" y1="13" x2="16" y2="13" />
      <line x1="8" y1="17" x2="16" y2="17" />
      <line x1="8" y1="9" x2="10" y2="9" />
    </svg>
  )
}

function RichReportText({ text }: { text: string }) {
  return (
    <div className="report-markdown">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
      >
        {text}
      </ReactMarkdown>
    </div>
  )
}

export default function ReportPanel({ notebookId }: { notebookId: number }) {
  const { documents } = useAppStore()
  const [result, setResult] = useState<ReportResult | null>(null)
  const [status, setStatus] = useState<ReportStatus>('idle')
  const [error, setError] = useState<string | null>(null)

  const readyCount = documents.filter((d) => d.status === 'ready').length
  const generating = status === 'generating'

  const applyState = (state: { status: ReportStatus; result: ReportResult | null; error: string | null }) => {
    setStatus(state.status)
    setResult(state.result)
    setError(state.error)
  }

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const state = await api.getReport(notebookId)
        if (!cancelled) applyState(state)
      } catch (e: any) {
        if (!cancelled) setError(e.message ?? '报告状态获取失败')
      }
    }

    load()
    return () => { cancelled = true }
  }, [notebookId])

  useEffect(() => {
    if (!generating) return

    let cancelled = false
    const timer = window.setInterval(async () => {
      try {
        const state = await api.getReport(notebookId)
        if (!cancelled) applyState(state)
      } catch (e: any) {
        if (!cancelled) setError(e.message ?? '报告状态获取失败')
      }
    }, 2000)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [generating, notebookId])

  const handleGenerate = async () => {
    setError(null)
    try {
      const state = await api.triggerReport(notebookId)
      applyState(state)
    } catch (e: any) {
      setStatus('failed')
      setError(e.message ?? '报告生成失败')
    }
  }

  const handleCancel = async () => {
    setError(null)
    try {
      const state = await api.cancelReport(notebookId)
      applyState(state)
    } catch (e: any) {
      setError(e.message ?? '取消生成失败')
    }
  }

  return (
    <div className="report-panel">
      <div className="analysis-header">
        <h2 className="analysis-title">生成报告</h2>
        <div className="report-actions">
          {generating && (
            <button className="btn btn-ghost" onClick={handleCancel}>取消生成</button>
          )}
          <button
            className="btn btn-primary"
            disabled={generating || readyCount < 1}
            onClick={handleGenerate}
          >
            {result ? <RefreshIcon /> : <ReportIcon />}
            {generating ? '生成中…' : result ? '重新生成' : '生成报告'}
          </button>
        </div>
      </div>

      {readyCount < 1 && (
        <p className="analysis-notice">需要至少 1 个已就绪的文档才能生成报告</p>
      )}

      {error && <p className="report-error">{error}</p>}

      {generating && (
        <div className="analysis-loading">
          <div className="spinner" />
          <span>正在生成报告，请稍候…你可以切换到其他 tab，生成会在后台继续。</span>
        </div>
      )}

      {!generating && result && (
        <article className="report-card">
          <header className="report-header">
            <h1>{result.title}</h1>
            <RichReportText text={result.executive_summary} />
          </header>

          <div className="report-sections">
            {(result.sections ?? []).map((section, i) => (
              <section key={i} className="report-section">
                <h3>{section.heading}</h3>
                <RichReportText text={section.content} />
              </section>
            ))}
          </div>

          <div className="report-lists">
            <div>
              <h3>关键结论</h3>
              <ul className="analysis-list">
                {(result.key_takeaways ?? []).map((item, i) => <li key={i}><RichReportText text={item} /></li>)}
              </ul>
            </div>
            <div>
              <h3>后续建议</h3>
              <ul className="analysis-list">
                {(result.next_steps ?? []).map((item, i) => <li key={i}><RichReportText text={item} /></li>)}
              </ul>
            </div>
          </div>
        </article>
      )}

      {!generating && !result && readyCount >= 1 && (
        <div className="empty-state">
          <div className="empty-state-icon">📄</div>
          <div className="empty-state-text">点击「生成报告」按钮生成一份综合报告</div>
        </div>
      )}
    </div>
  )
}
