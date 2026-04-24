import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ConfigProvider, Layout, Typography } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage'
import NotebookPage from './pages/NotebookPage'

const { Header } = Layout

function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <Header style={{ background: '#fff', borderBottom: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 12, padding: '0 24px' }}>
      {!isHome && (
        <ArrowLeftOutlined onClick={() => navigate('/')} style={{ cursor: 'pointer', fontSize: 16 }} />
      )}
      <Typography.Title level={4} style={{ margin: 0, color: '#1677ff' }}>KnowBase</Typography.Title>
    </Header>
  )
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          <AppHeader />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/notebook/:id" element={<NotebookPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  )
}
