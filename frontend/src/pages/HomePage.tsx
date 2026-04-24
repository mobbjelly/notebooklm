import { useEffect } from 'react'
import { Button, Card, Input, Modal, Typography, Empty, Spin, message } from 'antd'
import { PlusOutlined, BookOutlined, DeleteOutlined, ShareAltOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAppStore } from '../store/useAppStore'

const { Title, Text } = Typography

export default function HomePage() {
  const navigate = useNavigate()
  const { notebooks, setNotebooks } = useAppStore()

  useEffect(() => {
    api.getNotebooks().then(setNotebooks).catch(console.error)
  }, [])

  const handleCreate = () => {
    Modal.confirm({
      title: '新建笔记本',
      content: <Input id="nb-name-input" placeholder="笔记本名称" />,
      onOk: async () => {
        const name = (document.getElementById('nb-name-input') as HTMLInputElement).value.trim()
        if (!name) return
        const nb = await api.createNotebook({ name })
        setNotebooks([nb, ...notebooks])
      },
    })
  }

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    await api.deleteNotebook(id)
    setNotebooks(notebooks.filter((n) => n.id !== id))
    message.success('已删除')
  }

  const handleShare = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const nb = await api.shareNotebook(id)
    const url = `${window.location.origin}/shared/${nb.share_token}`
    await navigator.clipboard.writeText(url)
    message.success('分享链接已复制到剪贴板')
  }

  return (
    <div style={{ maxWidth: 900, margin: '40px auto', padding: '0 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <Title level={2} style={{ margin: 0 }}>我的笔记本</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建笔记本</Button>
      </div>

      {notebooks.length === 0 ? (
        <Empty description="还没有笔记本，点击右上角新建一个吧" />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 16 }}>
          {notebooks.map((nb) => (
            <Card
              key={nb.id}
              hoverable
              onClick={() => navigate(`/notebook/${nb.id}`)}
              actions={[
                <ShareAltOutlined key="share" onClick={(e) => handleShare(nb.id, e)} title="分享" />,
                <DeleteOutlined key="delete" onClick={(e) => handleDelete(nb.id, e)} title="删除" />,
              ]}
            >
              <Card.Meta
                avatar={<BookOutlined style={{ fontSize: 24, color: '#1677ff' }} />}
                title={nb.name}
                description={
                  <>
                    <Text type="secondary">{nb.description || '暂无描述'}</Text>
                    <br />
                    <Text type="secondary" style={{ fontSize: 12 }}>{nb.doc_count} 个文档</Text>
                  </>
                }
              />
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
