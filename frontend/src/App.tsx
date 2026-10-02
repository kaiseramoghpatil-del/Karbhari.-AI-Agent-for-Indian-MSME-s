import { Route, Routes } from 'react-router-dom'
import './App.css'
import { CaseListPage } from './pages/CaseListPage'
import { CaseWorkspacePage } from './pages/CaseWorkspacePage'

// Each page renders its own Backdrop and Chrome (the film-style top bar):
// the lobby is a marketing-grade landing, the workspace a full-viewport
// console with a persistent rail.
function App() {
  return (
    <Routes>
      <Route path="/" element={<CaseListPage />} />
      <Route path="/cases/:caseId" element={<CaseWorkspacePage />} />
    </Routes>
  )
}

export default App
