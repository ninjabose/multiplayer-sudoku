import ChatPanel from './ChatPanel'
import { useChat } from '../chat/ChatContext'

export default function ChatDock() {
  const chat = useChat()
  const {
    minimized,
    setMinimized,
    tab,
    setTab,
    unread,
    unreadTotal,
    username,
    globalMessages,
    globalOnline,
    globalError,
    sendGlobal,
    roomMessages,
    roomError,
    roomCanSend,
    roomClosed,
    sendRoom,
  } = chat

  if (minimized) {
    return (
      <button
        type="button"
        className="chat-fab"
        onClick={() => setMinimized(false)}
        aria-label={unreadTotal ? `Open chat, ${unreadTotal} unread` : 'Open chat'}
      >
        <span>💬 Chat</span>
        {unreadTotal > 0 ? <span className="chat-badge">{unreadTotal}</span> : null}
      </button>
    )
  }

  const showingRoom = tab === 'room'
  const messages = showingRoom ? roomMessages : globalMessages
  const error = showingRoom ? roomError : globalError
  const placeholder = showingRoom ? 'Message this room' : 'Message everyone online'
  const sendDisabled = showingRoom
    ? !roomCanSend || roomClosed
    : !username
  const notice = showingRoom
    ? roomClosed
      ? 'Room chat ended with the game.'
      : roomCanSend
        ? null
        : 'Join a game to use room chat.'
    : username
      ? null
      : 'Enter a username to join global chat.'

  return (
    <>
      <button
        type="button"
        className="chat-backdrop"
        aria-label="Close chat"
        onClick={() => setMinimized(true)}
      />
      <aside className="chat-dock" aria-label="Chat">
        <header className="chat-dock-head">
          <h2>Chat</h2>
          <div className="chat-tabs" role="tablist">
            <button
              type="button"
              role="tab"
              aria-selected={!showingRoom}
              className={!showingRoom ? 'active' : ''}
              onClick={() => setTab('global')}
            >
              Global
              {unread.global > 0 ? <span className="chat-badge small">{unread.global}</span> : null}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={showingRoom}
              className={showingRoom ? 'active' : ''}
              onClick={() => setTab('room')}
            >
              Room
              {unread.room > 0 ? <span className="chat-badge small">{unread.room}</span> : null}
            </button>
          </div>
          <button
            type="button"
            className="chat-min"
            onClick={() => setMinimized(true)}
            aria-label="Minimize chat"
          >
            –
          </button>
        </header>
        {showingRoom ? null : (
          <p className="muted chat-online">
            Online: {globalOnline.length ? globalOnline.join(', ') : 'none'}
          </p>
        )}
        {notice ? <p className="muted chat-notice">{notice}</p> : null}
        <ChatPanel
          messages={messages}
          error={error}
          disabled={sendDisabled}
          placeholder={placeholder}
          onSend={showingRoom ? sendRoom : sendGlobal}
        />
      </aside>
    </>
  )
}
