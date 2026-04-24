import { useRef, useState, useEffect } from 'react'
import { chatStream } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'
import type { Citation } from '../../api/client'

function SendIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  )
}

export default function ChatPanel({ notebookId }: { notebookId: number }) {
  const { messages, documents, streamingText, appendStreamChunk, commitStreamMessage } = useAppStore()
  const [input, setInput] = useState('')
  const [selectedDoc, setSelectedDoc] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const handleSend = () => {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setLoading(true)

    const userMsg = {
      id: Date.now(),
      role: 'user' as const,
      content: q,
      citations: null,
      created_at: new Date().toISOString(),
    }
    useAppStore.getState().setMessages([...messages, userMsg])

    const docId = selectedDoc ? Number(selectedDoc) : null
    chatStream(
      notebookId,
      q,
      docId,
      (chunk) => appendStreamChunk(chunk),
      (citations) => {
        commitStreamMessage(citations.length ? JSON.stringify(citations) : null)
        setLoading(false)
      },
      () => {
        commitStreamMessage(null)
        setLoading(false)
      },
    )
  }

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
  }

  const readyDocs = documents.filter((d) => d.status === 'ready')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="chat-messages">
        {messages.length === 0 && !streamingText && (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '60px 0', fontSize: 14 }}>
            向 AI 提问，探索你的文档
          </div>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} citations={msg.citations} />
        ))}
        {streamingText && (
          <MessageBubble role="assistant" content={streamingText} citations={null} streaming />
        )}
        {loading && !streamingText && (
          <div className="chat-row assistant">
            <div className="chat-bubble assistant" style={{ padding: '12px 16px' }}>
              <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                {[0, 0.15, 0.3].map((d, i) => (
                  <span key={i} style={{
                    width: 7, height: 7, borderRadius: '50%', background: 'var(--text-muted)',
                    animation: `blink 1.2s ${d}s ease-in-out infinite`,
                    display: 'inline-block',
                  }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-inputbar">
        {readyDocs.length > 0 && (
          <div>
            <select
              className="chat-scope-select"
              value={selectedDoc}
              onChange={(e) => setSelectedDoc(e.target.value)}
            >
              <option value="">全部文档</option>
              {readyDocs.map((d) => (
                <option key={d.id} value={String(d.id)}>{d.name}</option>
              ))}
            </select>
          </div>
        )}
        <div className="chat-inputbar-row">
          <textarea
            ref={textareaRef}
            className="input"
            placeholder="输入问题，Shift+Enter 换行"
            value={input}
            onChange={handleTextareaChange}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
            rows={1}
            style={{ flex: 1, minHeight: 40, maxHeight: 140 }}
          />
          <button
            className="btn btn-primary"
            style={{ padding: '9px 14px', flexShrink: 0 }}
            disabled={!input.trim() || loading}
            onClick={handleSend}
          >
            <SendIcon />
          </button>
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ role, content, citations, streaming }: {
  role: 'user' | 'assistant'
  content: string
  citations: string | null
  streaming?: boolean
}) {
  const isUser = role === 'user'
  const parsedCitations: Citation[] = citations ? JSON.parse(citations) : []

  return (
    <div className={`chat-row ${role}`}>
      <div className={`chat-bubble ${role}`}>
        {content}
        {streaming && <span className="chat-cursor">▌</span>}
        {parsedCitations.length > 0 && (
          <div className="chat-citations">
            <span className="chat-citations-label">来源：</span>
            {parsedCitations.map((c, i) => (
              <span key={i} className="tag tag-default" style={{ fontSize: 11 }}>{c.doc_name}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
