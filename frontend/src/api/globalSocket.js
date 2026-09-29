import { WS_BASE } from './config'

export function openGlobalSocket(name, handlers) {
  const url = `${WS_BASE}/ws/global?name=${encodeURIComponent(name)}`
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
    if (message.type === 'presence') {
      handlers.onPresence?.(message.users || [])
      return
    }
    if (message.type === 'chat') {
      handlers.onChat?.(message)
    }
  }

  ws.onclose = () => {
    if (!intentionalClose) handlers.onDropped?.()
  }

  return {
    sendChat(text) {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'chat', message: text }))
      }
    },
    close() {
      intentionalClose = true
      ws.close()
    },
  }
}
