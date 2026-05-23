import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAppStore } from '../store/useAppStore'
import DocumentPanel from '../components/document/DocumentPanel'
import ChatPanel from '../components/chat/ChatPanel'
import ReportPanel from '../components/notebook/ReportPanel'

export default function NotebookPage() {
  const { id } = useParams<{ id: string }>()
  const notebookId = Number(id)
  const { setDocuments, setMessages, setActiveNotebook, setAllDocsSelected, notebooks } = useAppStore()
  const [activeTab, setActiveTab] = useState<'chat' | 'report'>('chat')

  useEffect(() => {
    const nb = notebooks.find((n) => n.id === notebookId)
    if (nb) setActiveNotebook(nb)

    setDocuments([])
    setMessages([])

    Promise.all([
      api.getDocuments(notebookId).then((docs) => {
        setDocuments(docs)
        setAllDocsSelected(docs.filter(d => d.status === 'ready').map(d => d.id))
      }),
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
            className={`nb-tab${activeTab === 'report' ? ' active' : ''}`}
            onClick={() => setActiveTab('report')}
          >
            生成报告
          </div>
        </nav>
        <div className="nb-panel">
          {activeTab === 'chat'
            ? <ChatPanel notebookId={notebookId} />
            : <ReportPanel notebookId={notebookId} />
          }
        </div>
      </div>
    </div>
  )
}
