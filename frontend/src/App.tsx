import { Link, Route, Routes } from 'react-router-dom'
import './App.css'
import { CaseListPage } from './pages/CaseListPage'
import { CaseWorkspacePage } from './pages/CaseWorkspacePage'

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="home-link">
          <span className="brand-mark">क</span>
          <div className="brand-text">
            <h1>KARBHARI</h1>
            <p>Working Capital Guardian</p>
          </div>
        </Link>
      </header>

      <main className="main">
        <Routes>
          <Route path="/" element={<CaseListPage />} />
          <Route path="/cases/:caseId" element={<CaseWorkspacePage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
