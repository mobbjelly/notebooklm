import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAppStore } from '../store/useAppStore'
import DocumentPanel from '../components/document/DocumentPanel'
import ChatPanel from '../components/chat/ChatPanel'
import AnalysisPanel from '../components/notebook/AnalysisPanel'

export default function NotebookPage() {
  const { id } = useParams<{ id: string }>()
  const notebookId = Number(id)
  const { setDocuments, setMessages, setActiveNotebook, notebooks } = useAppStore()
  const [activeTab, setActiveTab] = useState<'chat' | 'analysis'>('chat')

  useEffect(() => {
    const nb = notebooks.find((n) => n.id === notebookId)
    if (nb) setActiveNotebook(nb)

    Promise.all([
      api.getDocuments(notebookId).then(setDocuments),
      api.getChatHistory(notebookId).then(setMessages),
    ]).catch(console.error)
  }, [notebookId])

  return (
    <div className="notebook-page">
      {/* Left sidebar */}
      <aside className="nb-sidebar">
        <DocumentPanel notebookId={notebookId} />
      </aside>

      {/* Right content */}
      <div className="nb-content">
        <nav className="nb-tabbar">
          <div
            className={`nb-tab${activeTab === 'chat' ? ' active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            AI 对话
          </div>
          <div
            className={`nb-tab${activeTab === 'analysis' ? ' active' : ''}`}
            onClick={() => setActiveTab('analysis')}
          >
            关联分析
          </div>
        </nav>
        <div className="nb-panel">
          {activeTab === 'chat'
            ? <ChatPanel notebookId={notebookId} />
            : <AnalysisPanel notebookId={notebookId} />
          }
        </div>
      </div>
    </div>
  )
}
