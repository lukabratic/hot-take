import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { useAuthSync } from './hooks/useAuthSync'
import { Layout } from './components/common/Layout'
import { ProtectedRoute } from './components/common/ProtectedRoute'
import { Home } from './pages/Home'
import { Play } from './pages/Play'
import { Reveal } from './pages/Reveal'
import { Leaderboard } from './pages/Leaderboard'
import { Debate } from './pages/Debate'
import { Profile } from './pages/Profile'

function AppContent() {
  useAuthSync()

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/play/:mode" element={<Play />} />
        <Route path="/reveal/:rankingId" element={<Reveal />} />
        <Route path="/leaderboard" element={<Leaderboard />} />
        <Route path="/debate" element={<Debate />} />
        <Route path="/debate/:sessionId" element={<Debate />} />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  )
}

export default App
