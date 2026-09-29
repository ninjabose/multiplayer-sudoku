import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getRoom, startRoom } from '../api/http'
import { openRoomSocket } from '../api/socket'
import { useChat } from '../chat/ChatContext'
import Board from '../components/Board'
import MusicToggle from '../components/MusicToggle'
import NumberPad from '../components/NumberPad'
import PlayerList from '../components/PlayerList'
import { useUser } from '../userContext'

const ENDED = new Set(['solved', 'given_up', 'abandoned'])

export default function Game() {
  const { joinCode } = useParams()
  const navigate = useNavigate()
  const { username } = useUser()
  const { attachRoom, pushRoomMessage, setRoomChatError } = useChat()
  const name = username
  const socketRef = useRef(null)
  const [room, setRoom] = useState(null)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState(null)
  const [dropped, setDropped] = useState(false)

  const code = (joinCode || '').toUpperCase()
  const ended = room ? ENDED.has(room.status) : false
  const playing = room?.status === 'playing'
  const isHost = room?.host === name
  const inRoom = room?.players?.includes(name)

  useEffect(() => {
    if (!name) {
      navigate('/', { replace: true })
      return undefined
    }

    let cancelled = false
    let socket

    getRoom(code)
      .then((data) => {
        if (cancelled) return
        setRoom(data)
        if (!data.players.includes(name)) {
          setError('You are not in this room. Join from the home page.')
          return
        }
        socket = openRoomSocket(code, name, {
          onState: (state) => {
            setRoom(state)
            setDropped(false)
          },
          onChat: (item) => {
            pushRoomMessage(item)
          },
          onError: (message) => {
            const lower = message.toLowerCase()
            if (
              lower.includes('message') ||
              lower.includes('quickly') ||
              lower.includes('chat')
            ) {
              setRoomChatError(message)
            } else {
              setError(message)
            }
          },
          onDropped: () => setDropped(true),
        })
        socketRef.current = socket
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })

    return () => {
      cancelled = true
      socket?.close()
      socketRef.current = null
    }
  }, [code, name, navigate, pushRoomMessage, setRoomChatError])

  useEffect(() => {
    if (!inRoom) return undefined
    return attachRoom({
      send: (text) => socketRef.current?.sendChat(text),
      canSend: Boolean(inRoom && !ended),
      closed: ended,
    })
  }, [attachRoom, inRoom, ended])

  useEffect(() => {
    function onKey(event) {
      if (!playing || !selected) return
      if (event.target.closest('input, textarea')) return
      if (event.key >= '1' && event.key <= '9') {
        socketRef.current?.setCell(selected.row, selected.col, Number(event.key))
      }
      if (event.key === 'Backspace' || event.key === 'Delete' || event.key === '0') {
        socketRef.current?.setCell(selected.row, selected.col, 0)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [playing, selected])

  const resultCopy = useMemo(() => {
    if (!room) return ''
    const remaining = room.players?.length || 0
    const share = remaining ? Math.floor(room.pot_points / remaining) : 0
    if (room.status === 'solved') {
      return `Solved. ${share} points each for ${remaining} remaining player${remaining === 1 ? '' : 's'}.`
    }
    if (room.status === 'given_up') {
      return 'Gave up. Solution revealed. 0 points awarded.'
    }
    if (room.status === 'abandoned') {
      return 'Game abandoned. 0 points awarded.'
    }
    return ''
  }, [room])

  async function onStart() {
    setError('')
    try {
      const next = await startRoom(code, name)
      setRoom(next)
    } catch (err) {
      setError(err.message)
    }
  }

  function onLeave() {
    socketRef.current?.leave()
    navigate('/')
  }

  function onGiveUp() {
    if (window.confirm('Reveal the solution and award 0 points?')) {
      socketRef.current?.giveUp()
    }
  }

  function enterDigit(value) {
    if (!selected || !playing) return
    socketRef.current?.setCell(selected.row, selected.col, value)
  }

  if (!name) return null

  return (
    <main className="page game-page">
      <header className="game-bar">
        <div>
          <p className="eyebrow">Room</p>
          <h1 className="code-title">{code}</h1>
        </div>
        <div className="meta">
          <span>Level {room?.difficulty ?? '—'}</span>
          <span>{room?.pot_points ?? 0} pts pot</span>
          <span className="status-pill">{room?.status || 'loading'}</span>
        </div>
        <div className="game-bar-actions">
          <MusicToggle />
          <button type="button" className="ghost" onClick={onLeave}>
            Leave
          </button>
        </div>
      </header>

      {error ? <p className="error-banner">{error}</p> : null}
      {dropped ? (
        <p className="error-banner">
          Disconnected. The server counts this as leaving (0 points if the game had started).{' '}
          <Link to="/">Return home</Link>
        </p>
      ) : null}

      {room?.status === 'lobby' ? (
        <section className="lobby">
          <div className="panel">
            <h2>Lobby</h2>
            <p className="muted">
              Share code <strong>{code}</strong> — up to 4 players.
            </p>
            <PlayerList room={room} you={name} />
            {isHost ? (
              <button className="primary" type="button" onClick={onStart} disabled={!inRoom}>
                Start game
              </button>
            ) : (
              <p className="muted">Waiting for the host to start…</p>
            )}
          </div>
        </section>
      ) : null}

      {room && room.status !== 'lobby' ? (
        <section className="play-layout">
          <Board
            puzzle={room.puzzle}
            grid={room.grid}
            solution={room.solution}
            selected={selected}
            onSelect={setSelected}
            ended={ended || !playing}
          />
          <aside className="panel side-panel">
            <PlayerList room={room} you={name} />
            {resultCopy ? <p className="result">{resultCopy}</p> : null}
            {playing ? (
              <>
                <NumberPad
                  disabled={!selected}
                  onDigit={enterDigit}
                  onClear={() => enterDigit(0)}
                />
                <button type="button" className="danger" onClick={onGiveUp}>
                  Give up
                </button>
              </>
            ) : (
              <Link className="primary link-btn" to="/leaderboard">
                View leaderboard
              </Link>
            )}
          </aside>
        </section>
      ) : null}
    </main>
  )
}
