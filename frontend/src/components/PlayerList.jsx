export default function PlayerList({ room, you }) {
  const players = room?.players || []
  const connected = new Set(room?.connected || [])

  return (
    <ul className="player-list">
      {players.map((name) => (
        <li key={name} className="player-row">
          <span className={`dot ${connected.has(name) ? 'online' : 'idle'}`} />
          <span className="player-name">
            {name}
            {name === you ? ' (you)' : ''}
          </span>
          {name === room.host ? <span className="pill">Host</span> : null}
        </li>
      ))}
    </ul>
  )
}
