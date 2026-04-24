import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage'
import NotebookPage from './pages/NotebookPage'

function AppHeader() {
  const navigate = useNavigate()
  const location = useLocation()
  const isHome = location.pathname === '/'

  return (
    <header className="app-header">
      {!isHome && (
        <button className="app-header-back" onClick={() => navigate('/')} title="返回">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
      )}
      <span className="app-header-logo">KnowBase</span>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-root">
        <AppHeader />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/notebook/:id" element={<NotebookPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
