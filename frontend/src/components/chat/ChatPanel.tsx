import { useRef, useState, useEffect } from 'react'
import { Input, Button, Select, Typography, Tag, Spin } from 'antd'
import { SendOutlined } from '@ant-design/icons'
import { chatStream } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'
import type { Citation } from '../../api/client'

const { Text } = Typography

export default function ChatPanel({ notebookId }: { notebookId: number }) {
  const { messages, documents, streamingText, appendStreamChunk, commitStreamMessage } = useAppStore()
  const [input, setInput] = useState('')
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const handleSend = () => {
    const q = input.trim()
    if (!q || loading) return
    setInput('')
    setLoading(true)

    // 立即显示用户消息
    const userMsg = { id: Date.now(), role: 'user' as const, content: q, citations: null, created_at: new Date().toISOString() }
    useAppStore.getState().setMessages([...messages, userMsg])

    chatStream(
      notebookId,
      q,
      selectedDoc,
      (chunk) => appendStreamChunk(chunk),
      (citations) => {
        commitStreamMessage(citations.length ? JSON.stringify(citations) : null)
        setLoading(false)
      },
      (err) => {
        commitStreamMessage(null)
        setLoading(false)
      },
    )
  }

  const readyDocs = documents.filter((d) => d.status === 'ready')

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* 消息列表 */}
      <div style={{ flex: 1, overflow: 'auto', padding: '16px 24px' }}>
        {messages.map((msg) => (
          <MessageBubble key={msg.id} role={msg.role} content={msg.content} citations={msg.citations} />
        ))}
        {streamingText && (
          <MessageBubble role="assistant" content={streamingText} citations={null} streaming />
        )}
        <div ref={bottomRef} />
      </div>

      {/* 输入栏 */}
      <div style={{ borderTop: '1px solid #f0f0f0', padding: '12px 24px', display: 'flex', gap: 8, alignItems: 'flex-end' }}>
        <Select
          allowClear
          placeholder="全部文档"
          style={{ width: 160 }}
          value={selectedDoc}
          onChange={setSelectedDoc}
          options={readyDocs.map((d) => ({ value: d.id, label: d.name }))}
        />
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); handleSend() } }}
          placeholder="输入问题，Shift+Enter 换行"
          autoSize={{ minRows: 1, maxRows: 5 }}
          style={{ flex: 1 }}
        />
        <Button type="primary" icon={<SendOutlined />} onClick={handleSend} loading={loading} />
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
    <div style={{ marginBottom: 16, display: 'flex', flexDirection: isUser ? 'row-reverse' : 'row', gap: 8 }}>
      <div
        style={{
          maxWidth: '75%',
          padding: '10px 14px',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
          background: isUser ? '#1677ff' : '#f5f5f5',
          color: isUser ? '#fff' : 'inherit',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {content}
        {streaming && <span style={{ opacity: 0.5 }}>▌</span>}
        {parsedCitations.length > 0 && (
          <div style={{ marginTop: 8, borderTop: '1px solid #ddd', paddingTop: 6 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>来源：</Text>
            {parsedCitations.map((c, i) => (
              <Tag key={i} style={{ fontSize: 11, margin: '2px' }}>{c.doc_name}</Tag>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
