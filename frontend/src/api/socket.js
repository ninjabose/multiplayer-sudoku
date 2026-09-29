import { WS_BASE } from './config'

export function openRoomSocket(joinCode, name, handlers) {
  const url = `${WS_BASE}/ws/rooms/${encodeURIComponent(
    joinCode,
  )}?name=${encodeURIComponent(name)}`

  const ws = new WebSocket(url)
  let intentionalClose = false

  ws.onmessage = (event) => {
    let message
    try {
      message = JSON.parse(event.data)
    } catch {
      handlers.onError?.('Invalid server message')
      return
    }
    if (message.type === 'error') {
      handlers.onError?.(message.message)
      return
    }
    if (message.type === 'chat') {
      handlers.onChat?.(message)
      return
    }
    handlers.onState?.(message)
  }

  ws.onclose = () => {
    if (!intentionalClose) {
      handlers.onDropped?.()
    }
  }

  ws.onerror = () => {
    handlers.onError?.('WebSocket connection error')
  }

  return {
    setCell(row, col, value) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'set_cell', row, col, value }))
      }
    },
    sendChat(text) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'chat', message: text }))
      }
    },
    giveUp() {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'give_up' }))
      }
    },
    leave() {
      intentionalClose = true
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'leave' }))
      }
      ws.close()
    },
    close() {
      intentionalClose = true
      ws.close()
    },
  }
}
