const NAME_KEY = 'sudoku_username'

export function saveName(name) {
  sessionStorage.setItem(NAME_KEY, name.trim())
}

export function loadName() {
  return sessionStorage.getItem(NAME_KEY) || ''
}
