import { Route, Routes } from 'react-router-dom'
import './App.css'
import { CaseListPage } from './pages/CaseListPage'
import { CaseWorkspacePage } from './pages/CaseWorkspacePage'

// No shared chrome here on purpose: the case list is a light "lobby" screen
// and owns its own header, while the case workspace is a full-viewport
// console with its own persistent rail. Forcing both through one topbar
// was exactly the kind of generic-SaaS-shell sameness this redesign moved
// away from.
function App() {
  return (
    <Routes>
      <Route path="/" element={<CaseListPage />} />
      <Route path="/cases/:caseId" element={<CaseWorkspacePage />} />
    </Routes>
  )
}

export default App
