import { useEffect, useState } from 'react'
import {
  disableMusic,
  enableMusic,
  isMusicPlaying,
  loadMusicPreference,
} from '../audio/music'

export default function MusicToggle() {
  const [playing, setPlaying] = useState(false)
  const [hint, setHint] = useState('')

  useEffect(() => {
    setPlaying(isMusicPlaying())
  }, [])

  async function toggle() {
    setHint('')
    if (isMusicPlaying()) {
      disableMusic()
      setPlaying(false)
      return
    }
    try {
      await enableMusic()
      setPlaying(true)
    } catch {
      setPlaying(false)
      setHint('Click again to start music (browser blocked autoplay).')
    }
  }

  const preferred = loadMusicPreference()

  return (
    <div className="music-wrap">
      <button
        type="button"
        className={`music-btn ${playing ? 'on' : ''}`}
        onClick={toggle}
        aria-pressed={playing}
        title="Background music is off until you enable it"
      >
        {playing ? 'Music on' : preferred ? 'Play music' : 'Music off'}
      </button>
      {hint ? <span className="music-hint">{hint}</span> : null}
    </div>
  )
}
