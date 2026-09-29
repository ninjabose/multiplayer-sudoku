const STORAGE_KEY = 'sudoku_music_enabled'
export const MUSIC_TRACK = '/audio/ambient.wav'
const VOLUME = 0.12

let audio

function getAudio() {
  if (!audio) {
    audio = new Audio(MUSIC_TRACK)
    audio.loop = true
    audio.preload = 'auto'
    audio.volume = VOLUME
  }
  return audio
}

export function loadMusicPreference() {
  return window.localStorage.getItem(STORAGE_KEY) === '1'
}

export function isMusicPlaying() {
  return Boolean(audio && !audio.paused)
}

export async function enableMusic() {
  const el = getAudio()
  await el.play()
  window.localStorage.setItem(STORAGE_KEY, '1')
}

export function disableMusic() {
  const el = getAudio()
  el.pause()
  window.localStorage.setItem(STORAGE_KEY, '0')
}
