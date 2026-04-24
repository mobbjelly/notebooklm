import { useState } from 'react'
import { Upload, Input, Button, List, Tag, Tooltip, message, Divider, Typography } from 'antd'
import { InboxOutlined, LinkOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { api } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'

const { Dragger } = Upload
const { Text } = Typography

const STATUS_COLOR: Record<string, string> = {
  pending: 'default',
  processing: 'processing',
  ready: 'success',
  failed: 'error',
}

const STATUS_LABEL: Record<string, string> = {
  pending: '等待中',
  processing: '解析中',
  ready: '已就绪',
  failed: '失败',
}

export default function DocumentPanel({ notebookId }: { notebookId: number }) {
  const { documents, setDocuments } = useAppStore()
  const [urlInput, setUrlInput] = useState('')
  const [urlLoading, setUrlLoading] = useState(false)

  const handleUpload = async (file: File) => {
    try {
      const doc = await api.uploadFile(notebookId, file)
      setDocuments([doc, ...documents])
      message.success(`${file.name} 上传成功，正在解析...`)
    } catch (e: any) {
      message.error(e.message)
    }
    return false  // 阻止 antd 默认上传行为
  }

  const handleAddUrl = async () => {
    if (!urlInput.trim()) return
    setUrlLoading(true)
    try {
      const doc = await api.addUrl(notebookId, urlInput.trim())
      setDocuments([doc, ...documents])
      setUrlInput('')
      message.success('URL 添加成功，正在抓取解析...')
    } catch (e: any) {
      message.error(e.message)
    } finally {
      setUrlLoading(false)
    }
  }

  const handleDelete = async (docId: number) => {
    await api.deleteDocument(notebookId, docId)
    setDocuments(documents.filter((d) => d.id !== docId))
    message.success('已删除')
  }

  return (
    <div style={{ padding: 16 }}>
      <Typography.Title level={5} style={{ marginBottom: 12 }}>文档</Typography.Title>

      <Dragger
        multiple
        showUploadList={false}
        beforeUpload={(file) => { handleUpload(file); return false }}
        accept=".pdf,.docx,.txt,.md"
        style={{ marginBottom: 12 }}
      >
        <p className="ant-upload-drag-icon"><InboxOutlined /></p>
        <p style={{ fontSize: 13 }}>拖拽或点击上传 PDF / Word / TXT / Markdown</p>
      </Dragger>

      <Input.Group compact style={{ marginBottom: 16, display: 'flex' }}>
        <Input
          prefix={<LinkOutlined />}
          placeholder="输入网页 URL"
          value={urlInput}
          onChange={(e) => setUrlInput(e.target.value)}
          onPressEnter={handleAddUrl}
          style={{ flex: 1 }}
        />
        <Button type="primary" loading={urlLoading} onClick={handleAddUrl}>添加</Button>
      </Input.Group>

      <Divider style={{ margin: '8px 0' }} />

      <List
        dataSource={documents}
        locale={{ emptyText: '暂无文档' }}
        renderItem={(doc) => (
          <List.Item
            style={{ padding: '8px 4px' }}
            actions={[
              <Tooltip title="删除" key="del">
                <DeleteOutlined onClick={() => handleDelete(doc.id)} style={{ color: '#ff4d4f', cursor: 'pointer' }} />
              </Tooltip>,
            ]}
          >
            <List.Item.Meta
              avatar={<FileTextOutlined />}
              title={<Text ellipsis style={{ maxWidth: 180 }}>{doc.name}</Text>}
              description={
                <Tag color={STATUS_COLOR[doc.status]}>{STATUS_LABEL[doc.status]}</Tag>
              }
            />
          </List.Item>
        )}
      />
    </div>
  )
}
