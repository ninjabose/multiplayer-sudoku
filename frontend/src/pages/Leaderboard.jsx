import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLeaderboard } from '../api/http'

export default function Leaderboard() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    getLeaderboard()
      .then(setRows)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main className="page">
      <header className="hero-head">
        <p className="eyebrow">Standings</p>
        <h1>Leaderboard</h1>
        <Link className="text-link" to="/">
          ← Back home
        </Link>
      </header>

      {error ? <p className="error-banner">{error}</p> : null}

      <section className="panel table-wrap">
        <table className="board-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Player</th>
              <th>Points</th>
              <th>Games</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={4} className="muted">
                  No games recorded yet.
                </td>
              </tr>
            ) : (
              rows.map((row, index) => (
                <tr key={row.name}>
                  <td>{index + 1}</td>
                  <td>{row.name}</td>
                  <td>{row.points}</td>
                  <td>{row.games_played}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </main>
  )
}
