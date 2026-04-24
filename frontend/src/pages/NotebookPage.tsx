import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Layout, Tabs } from 'antd'
import { api } from '../api/client'
import { useAppStore } from '../store/useAppStore'
import DocumentPanel from '../components/document/DocumentPanel'
import ChatPanel from '../components/chat/ChatPanel'
import AnalysisPanel from '../components/notebook/AnalysisPanel'

const { Sider, Content } = Layout

export default function NotebookPage() {
  const { id } = useParams<{ id: string }>()
  const notebookId = Number(id)
  const { setDocuments, setMessages, setActiveNotebook, notebooks } = useAppStore()

  useEffect(() => {
    const nb = notebooks.find((n) => n.id === notebookId)
    if (nb) setActiveNotebook(nb)

    Promise.all([
      api.getDocuments(notebookId).then(setDocuments),
      api.getChatHistory(notebookId).then(setMessages),
    ]).catch(console.error)
  }, [notebookId])

  return (
    <Layout style={{ height: '100vh' }}>
      <Sider width={320} theme="light" style={{ borderRight: '1px solid #f0f0f0', overflow: 'auto' }}>
        <DocumentPanel notebookId={notebookId} />
      </Sider>
      <Content>
        <Tabs
          defaultActiveKey="chat"
          style={{ height: '100%' }}
          tabBarStyle={{ padding: '0 16px', margin: 0 }}
          items={[
            { key: 'chat', label: 'AI 对话', children: <ChatPanel notebookId={notebookId} /> },
            { key: 'analysis', label: '关联分析', children: <AnalysisPanel notebookId={notebookId} /> },
          ]}
        />
      </Content>
    </Layout>
  )
}
