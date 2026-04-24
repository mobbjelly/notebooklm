import { useRef, useState } from 'react'
import { api } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'

const STATUS_TAG: Record<string, { cls: string; label: string }> = {
  pending:    { cls: 'tag tag-default',     label: '等待中' },
  processing: { cls: 'tag tag-processing',  label: '解析中' },
  ready:      { cls: 'tag tag-success',     label: '已就绪' },
  failed:     { cls: 'tag tag-error',       label: '失败'   },
}

function FileIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  )
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14H6L5 6" />
      <path d="M10 11v6M14 11v6M9 6V4h6v2" />
    </svg>
  )
}

export default function DocumentPanel({ notebookId }: { notebookId: number }) {
  const { documents, setDocuments } = useAppStore()
  const [urlInput, setUrlInput] = useState('')
  const [urlLoading, setUrlLoading] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [toast, setToast] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2200)
  }

  const handleFiles = async (files: FileList | File[]) => {
    for (const file of Array.from(files)) {
      try {
        const doc = await api.uploadFile(notebookId, file)
        setDocuments([doc, ...useAppStore.getState().documents])
        showToast(`${file.name} 上传成功`)
      } catch (e: any) {
        showToast(e.message)
      }
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files)
  }

  const handleAddUrl = async () => {
    if (!urlInput.trim()) return
    setUrlLoading(true)
    try {
      const doc = await api.addUrl(notebookId, urlInput.trim())
      setDocuments([doc, ...documents])
      setUrlInput('')
      showToast('URL 添加成功')
    } catch (e: any) {
      showToast(e.message)
    } finally {
      setUrlLoading(false)
    }
  }

  const handleDelete = async (docId: number) => {
    await api.deleteDocument(notebookId, docId)
    setDocuments(documents.filter((d) => d.id !== docId))
    showToast('已删除')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '16px 16px 8px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.6px' }}>
          来源
        </span>
        <button className="btn btn-primary btn-sm" onClick={() => fileInputRef.current?.click()}>
          + 添加来源
        </button>
      </div>

      {/* Upload zone */}
      <div className="sidebar-search">
        <div
          className="upload-zone"
          style={dragging ? { borderColor: 'var(--accent)', background: 'var(--accent-light)' } : {}}
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
        >
          <div style={{ fontSize: 20, marginBottom: 4 }}>☁️</div>
          <div>拖拽或点击上传</div>
          <div style={{ fontSize: 12, marginTop: 2, opacity: 0.7 }}>PDF · Word · TXT · Markdown</div>
        </div>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
      </div>

      {/* URL input */}
      <div className="url-row">
        <input
          className="input"
          placeholder="输入网页 URL"
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleAddUrl()}
        />
        <button className="btn btn-ghost btn-sm" style={{ flexShrink: 0 }} disabled={urlLoading} onClick={handleAddUrl}>
          {urlLoading ? '…' : '添加'}
        </button>
      </div>

      <hr className="divider" />

      {/* Source list */}
      <div className="source-list">
        {documents.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, padding: '24px 0' }}>暂无来源</div>
        )}
        {documents.map((doc) => {
          const status = STATUS_TAG[doc.status] ?? STATUS_TAG.pending
          return (
            <div key={doc.id} className="source-item">
              <div className="source-item-icon"><FileIcon /></div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="source-item-name">{doc.name}</div>
                <span className={status.cls}>{status.label}</span>
              </div>
              <button
                className="btn-icon source-item-delete"
                style={{ color: 'var(--danger)' }}
                title="删除"
                onClick={() => handleDelete(doc.id)}
              >
                <TrashIcon />
              </button>
            </div>
          )
        })}
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'absolute', bottom: 16, left: '50%', transform: 'translateX(-50%)',
          background: '#1a1a1a', color: '#fff', padding: '8px 16px',
          borderRadius: 'var(--radius-pill)', fontSize: 12, zIndex: 500,
          whiteSpace: 'nowrap', pointerEvents: 'none',
        }}>
          {toast}
        </div>
      )}
    </div>
  )
}
