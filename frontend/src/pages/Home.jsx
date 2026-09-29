import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createRoom, getHealth, joinRoom } from '../api/http'
import { useUser } from '../userContext'

const LEVELS = [
  { level: 1, points: 20, label: 'Warm-up' },
  { level: 2, points: 40, label: 'Easy' },
  { level: 3, points: 60, label: 'Medium' },
  { level: 4, points: 80, label: 'Hard' },
  { level: 5, points: 100, label: 'Expert' },
]

export default function Home() {
  const navigate = useNavigate()
  const { username, setUsername } = useUser()
  const [name, setName] = useState(username)
  const [difficulty, setDifficulty] = useState(1)
  const [joinCode, setJoinCode] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [apiOk, setApiOk] = useState(null)

  useEffect(() => {
    getHealth()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false))
  }, [])

  function requireName() {
    const trimmed = name.trim()
    if (!trimmed) {
      setError('Enter a username first')
      return null
    }
    if (trimmed.length > 32) {
      setError('Username must be 32 characters or fewer')
      return null
    }
    setUsername(trimmed)
    return trimmed
  }

  async function onCreate(event) {
    event.preventDefault()
    const player = requireName()
    if (!player) return
    setBusy(true)
    setError('')
    try {
      const room = await createRoom(player, difficulty)
      navigate(`/play/${room.join_code}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function onJoin(event) {
    event.preventDefault()
    const player = requireName()
    if (!player) return
    const code = joinCode.trim().toUpperCase()
    if (code.length !== 6) {
      setError('Room code must be 6 characters')
      return
    }
    setBusy(true)
    setError('')
    try {
      await joinRoom(code, player)
      navigate(`/play/${code}`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="page">
      <header className="hero-head">
        <p className="eyebrow">Co-op puzzle</p>
        <h1>Multiplayer Sudoku</h1>
        <p className="lede">
          1–4 players, one shared board. Solve together and split the points.
        </p>
        <p className={`api-status ${apiOk === false ? 'down' : ''}`}>
          {apiOk === null
            ? 'Checking server…'
            : apiOk
              ? 'Server connected'
              : 'Backend is not reachable on port 8000'}
        </p>
        <Link className="text-link" to="/leaderboard">
          View leaderboard →
        </Link>
      </header>

      <section className="panel">
        <label className="field">
          <span>Username</span>
          <input
            value={name}
            maxLength={32}
            autoComplete="username"
            placeholder="Your name"
            onChange={(e) => setName(e.target.value)}
            onBlur={() => {
              if (name.trim()) setUsername(name)
            }}
          />
        </label>
      </section>

      <div className="home-grid">
        <form className="panel" onSubmit={onCreate}>
          <h2>Create game</h2>
          <p className="muted">Pick a difficulty, then share the room code.</p>
          <div className="levels">
            {LEVELS.map((item) => (
              <button
                key={item.level}
                type="button"
                className={`level-btn ${difficulty === item.level ? 'active' : ''}`}
                onClick={() => setDifficulty(item.level)}
              >
                <strong>Lv {item.level}</strong>
                <span>{item.label}</span>
                <span className="points">{item.points} pts</span>
              </button>
            ))}
          </div>
          <button className="primary" type="submit" disabled={busy}>
            Create room
          </button>
        </form>

        <form className="panel" onSubmit={onJoin}>
          <h2>Join game</h2>
          <p className="muted">Enter a 6-character code from the host.</p>
          <label className="field">
            <span>Room code</span>
            <input
              value={joinCode}
              maxLength={6}
              placeholder="ABC123"
              className="code-input"
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            />
          </label>
          <button className="primary" type="submit" disabled={busy}>
            Join room
          </button>
        </form>
      </div>

      {error ? <p className="error-banner">{error}</p> : null}
    </main>
  )
}
