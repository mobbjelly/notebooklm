import { useEffect, useState } from 'react'
import { Button, Card, List, Typography, Spin, Empty, Tag } from 'antd'
import { ExperimentOutlined, ReloadOutlined } from '@ant-design/icons'
import { api, type AnalysisResult } from '../../api/client'
import { useAppStore } from '../../store/useAppStore'

const { Title, Text, Paragraph } = Typography

export default function AnalysisPanel({ notebookId }: { notebookId: number }) {
  const { documents } = useAppStore()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(false)

  const readyCount = documents.filter((d) => d.status === 'ready').length

  useEffect(() => {
    api.getAnalysis(notebookId).then((r) => setResult(r.result)).catch(console.error)
  }, [notebookId])

  const handleAnalyze = async () => {
    setLoading(true)
    try {
      const r = await api.triggerAnalysis(notebookId)
      setResult(r.result)
    } catch (e: any) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 800, margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0 }}>多文档关联分析</Title>
        <Button
          type="primary"
          icon={result ? <ReloadOutlined /> : <ExperimentOutlined />}
          loading={loading}
          disabled={readyCount < 2}
          onClick={handleAnalyze}
        >
          {result ? '重新分析' : '开始分析'}
        </Button>
      </div>

      {readyCount < 2 && (
        <Text type="secondary">需要至少 2 个已就绪的文档才能进行关联分析</Text>
      )}

      {loading && <Spin tip="正在分析中，请稍候..." style={{ display: 'block', marginTop: 40 }} />}

      {!loading && result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card title="共同主题">
            {(result.common_themes ?? []).map((t, i) => <Tag key={i} color="blue" style={{ marginBottom: 6 }}>{t}</Tag>)}
          </Card>
          <Card title="主要差异">
            <List
              dataSource={result.differences ?? []}
              renderItem={(item) => <List.Item><Text>• {item}</Text></List.Item>}
              size="small"
            />
          </Card>
          <Card title="知识盲点">
            <List
              dataSource={result.blind_spots ?? []}
              renderItem={(item) => <List.Item><Text type="warning">• {item}</Text></List.Item>}
              size="small"
            />
          </Card>
          <Card title="综合见解">
            <Paragraph>{result.synthesis}</Paragraph>
          </Card>
        </div>
      )}

      {!loading && !result && readyCount >= 2 && <Empty description="点击「开始分析」按钮生成关联分析" />}
    </div>
  )
}
