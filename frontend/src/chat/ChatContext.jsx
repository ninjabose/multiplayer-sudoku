import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { openGlobalSocket } from '../api/globalSocket'
import { useUser } from '../userContext'

const STORAGE_MIN = 'sudoku_chat_minimized'
const STORAGE_TAB = 'sudoku_chat_tab'

const ChatContext = createContext(null)

function loadMinimized() {
  try {
    const stored = window.localStorage.getItem(STORAGE_MIN)
    if (stored === '1') return true
    if (stored === '0') return false
    return window.matchMedia('(max-width: 800px)').matches
  } catch {
    return false
  }
}

function loadTab() {
  try {
    const stored = window.localStorage.getItem(STORAGE_TAB)
    return stored === 'room' ? 'room' : 'global'
  } catch {
    return 'global'
  }
}

export function ChatProvider({ children }) {
  const { username } = useUser()
  const [minimized, setMinimizedState] = useState(loadMinimized)
  const [tab, setTabState] = useState(loadTab)
  const [globalMessages, setGlobalMessages] = useState([])
  const [globalOnline, setGlobalOnline] = useState([])
  const [globalError, setGlobalError] = useState('')
  const [globalSocket, setGlobalSocket] = useState(null)
  const [roomMessages, setRoomMessages] = useState([])
  const [roomError, setRoomError] = useState('')
  const [roomCanSend, setRoomCanSend] = useState(false)
  const [roomClosed, setRoomClosed] = useState(false)
  const [unread, setUnread] = useState({ global: 0, room: 0 })

  const minimizedRef = useRef(minimized)
  const tabRef = useRef(tab)
  const usernameRef = useRef(username)
  const roomSendRef = useRef(null)
  minimizedRef.current = minimized
  tabRef.current = tab
  usernameRef.current = username

  const setMinimized = useCallback((next) => {
    setMinimizedState(next)
    try {
      window.localStorage.setItem(STORAGE_MIN, next ? '1' : '0')
    } catch {
      /* ignore */
    }
    if (!next) {
      setUnread((current) => ({ ...current, [tabRef.current]: 0 }))
    }
  }, [])

  const setTab = useCallback((next) => {
    setTabState(next)
    try {
      window.localStorage.setItem(STORAGE_TAB, next)
    } catch {
      /* ignore */
    }
    if (!minimizedRef.current) {
      setUnread((current) => ({ ...current, [next]: 0 }))
    }
  }, [])

  useEffect(() => {
    if (!username) {
      setGlobalMessages([])
      setGlobalOnline([])
      setGlobalSocket(null)
      setGlobalError('')
      return undefined
    }
    const client = openGlobalSocket(username, {
      onChat: (item) => {
        setGlobalMessages((current) => [...current.slice(-99), item])
        setGlobalError('')
        const incoming = item.username !== usernameRef.current
        if (incoming && (minimizedRef.current || tabRef.current !== 'global')) {
          setUnread((current) => ({ ...current, global: current.global + 1 }))
        }
      },
      onPresence: setGlobalOnline,
      onError: setGlobalError,
      onDropped: () => setGlobalError('Disconnected from global chat'),
    })
    setGlobalSocket(client)
    return () => {
      client.close()
      setGlobalSocket(null)
    }
  }, [username])

  const pushRoomMessage = useCallback((item) => {
    setRoomMessages((current) => [...current.slice(-99), item])
    setRoomError('')
    const incoming = item.username !== usernameRef.current
    if (incoming && (minimizedRef.current || tabRef.current !== 'room')) {
      setUnread((current) => ({ ...current, room: current.room + 1 }))
    }
  }, [])

  const attachRoom = useCallback(({ send, canSend, closed }) => {
    roomSendRef.current = send
    setRoomCanSend(Boolean(canSend))
    setRoomClosed(Boolean(closed))
    if (closed) {
      setRoomMessages([])
      setUnread((current) => ({ ...current, room: 0 }))
    }
    return () => {
      roomSendRef.current = null
      setRoomCanSend(false)
      setRoomClosed(false)
      setRoomMessages([])
      setRoomError('')
      setUnread((current) => ({ ...current, room: 0 }))
    }
  }, [])

  const setRoomChatError = useCallback((message) => {
    setRoomError(message)
  }, [])

  const value = useMemo(
    () => ({
      minimized,
      setMinimized,
      tab,
      setTab,
      unread,
      unreadTotal: unread.global + unread.room,
      username,
      globalMessages,
      globalOnline,
      globalError,
      sendGlobal: (text) => globalSocket?.sendChat(text),
      roomMessages,
      roomError,
      roomCanSend,
      roomClosed,
      sendRoom: (text) => roomSendRef.current?.(text),
      attachRoom,
      pushRoomMessage,
      setRoomChatError,
    }),
    [
      minimized,
      setMinimized,
      tab,
      setTab,
      unread,
      username,
      globalMessages,
      globalOnline,
      globalError,
      globalSocket,
      roomMessages,
      roomError,
      roomCanSend,
      roomClosed,
      attachRoom,
      pushRoomMessage,
      setRoomChatError,
    ],
  )

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export function useChat() {
  const value = useContext(ChatContext)
  if (!value) {
    throw new Error('useChat must be used inside ChatProvider')
  }
  return value
}
