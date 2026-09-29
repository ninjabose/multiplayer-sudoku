import { createContext, useContext } from 'react'

export const UserContext = createContext({
  username: '',
  setUsername: () => {},
})

export function useUser() {
  return useContext(UserContext)
}
