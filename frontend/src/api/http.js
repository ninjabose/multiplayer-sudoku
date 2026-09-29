import { API_BASE } from './config'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data.detail
    throw new Error(typeof detail === 'string' ? detail : 'Request failed')
  }
  return data
}

export function createRoom(name, difficulty) {
  return request('/rooms', {
    method: 'POST',
    body: JSON.stringify({ name, difficulty }),
  })
}

export function joinRoom(code, name) {
  return request(`/rooms/${code.toUpperCase()}/join`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export function startRoom(code, name) {
  return request(`/rooms/${code.toUpperCase()}/start`, {
    method: 'POST',
    body: JSON.stringify({ name }),
  })
}

export function getRoom(code) {
  return request(`/rooms/${code.toUpperCase()}`)
}

export function getLeaderboard() {
  return request('/leaderboard')
}

export function getHealth() {
  return request('/health')
}
