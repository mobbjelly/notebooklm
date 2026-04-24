import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAppStore } from '../store/useAppStore'

export default function HomePage() {
  const navigate = useNavigate()
  const { notebooks, setNotebooks } = useAppStore()
  const [showModal, setShowModal] = useState(false)
  const [newName, setNewName] = useState('')
  const [creating, setCreating] = useState(false)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    api.getNotebooks().then(setNotebooks).catch(console.error)
  }, [])

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2500)
  }

  const handleCreate = async () => {
    const name = newName.trim()
    if (!name) return
    setCreating(true)
    try {
      const nb = await api.createNotebook({ name })
      setNotebooks([nb, ...notebooks])
      setShowModal(false)
      setNewName('')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    await api.deleteNotebook(id)
    setNotebooks(notebooks.filter((n) => n.id !== id))
    showToast('已删除')
  }

  const handleShare = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const nb = await api.shareNotebook(id)
    const url = `${window.location.origin}/shared/${nb.share_token}`
    await navigator.clipboard.writeText(url)
    showToast('分享链接已复制')
  }

  return (
    <div style={{ flex: 1 }}>
      <div className="home-container">
        <div className="home-header">
          <h1 className="home-title">我的笔记本</h1>
          <button className="btn btn-primary" onClick={() => setShowModal(true)}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
            创建笔记本
          </button>
        </div>

        {notebooks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📓</div>
            <div className="empty-state-text">还没有笔记本，点击右上角新建一个吧</div>
          </div>
        ) : (
          <div className="notebook-grid">
            {notebooks.map((nb) => (
              <div
                key={nb.id}
                className="notebook-card"
                onClick={() => navigate(`/notebook/${nb.id}`)}
              >
                <div className="notebook-card-icon">📚</div>
                <div className="notebook-card-title">{nb.name}</div>
                <div className="notebook-card-desc">{nb.description || '暂无描述'}</div>
                <div className="notebook-card-footer">
                  <span className="notebook-card-meta">{nb.doc_count} 个文档</span>
                  <div className="notebook-card-actions">
                    <button
                      className="btn-icon"
                      title="分享"
                      onClick={(e) => handleShare(nb.id, e)}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="18" cy="5" r="3" /><circle cx="6" cy="12" r="3" /><circle cx="18" cy="19" r="3" />
                        <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" /><line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                      </svg>
                    </button>
                    <button
                      className="btn-icon"
                      title="删除"
                      onClick={(e) => handleDelete(nb.id, e)}
                      style={{ color: 'var(--danger)' }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" /><path d="M19 6l-1 14H6L5 6" />
                        <path d="M10 11v6M14 11v6M9 6V4h6v2" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-box" onClick={(e) => e.stopPropagation()}>
            <h2 className="modal-title">新建笔记本</h2>
            <input
              className="input"
              placeholder="笔记本名称"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              autoFocus
            />
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => { setShowModal(false); setNewName('') }}>取消</button>
              <button className="btn btn-primary" disabled={!newName.trim() || creating} onClick={handleCreate}>
                {creating ? '创建中…' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
          background: '#1a1a1a', color: '#fff', padding: '10px 20px',
          borderRadius: 'var(--radius-pill)', fontSize: 13, zIndex: 2000,
          boxShadow: 'var(--shadow-md)', pointerEvents: 'none',
        }}>
          {toast}
        </div>
      )}
    </div>
  )
}
