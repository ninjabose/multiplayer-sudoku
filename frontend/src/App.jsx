import { useMemo, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import { loadName, saveName } from './api/session'
import { ChatProvider } from './chat/ChatContext.jsx'
import ChatDock from './components/ChatDock.jsx'
import MusicToggle from './components/MusicToggle.jsx'
import Game from './pages/Game.jsx'
import Home from './pages/Home.jsx'
import Leaderboard from './pages/Leaderboard.jsx'
import { UserContext } from './userContext.js'

export default function App() {
  const [username, setUsernameState] = useState(loadName)

  const value = useMemo(
    () => ({
      username,
      setUsername(next) {
        const trimmed = String(next || '').trim().slice(0, 32)
        saveName(trimmed)
        setUsernameState(trimmed)
      },
    }),
    [username],
  )

  return (
    <UserContext.Provider value={value}>
      <ChatProvider>
        <div className="app-shell">
          <div className="app-tools">
            <MusicToggle />
          </div>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/play/:joinCode" element={<Game />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
          </Routes>
        </div>
        <ChatDock />
      </ChatProvider>
    </UserContext.Provider>
  )
}
