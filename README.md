# Multiplayer Sudoku

A learning project: cooperative Sudoku for 1–4 players, with a React + Vite client and a FastAPI server. Players share one board over WebSockets, split points when they solve a puzzle, and can use room chat plus a simple global lobby chat.

This is **not production-ready**. There is no authentication, live games live in a single server process’s memory, and disconnects are treated as leaving the game.

## Features

- Create or join a room with a 6-character code
- Five difficulty levels (20–100 point pots)
- Shared 9×9 board with real-time cell updates
- Give up (reveal solution, 0 points) and leave (0 points for that player)
- SQLite leaderboard (name, points, games played)
- Optional background music (off by default; local original loop)
- Room chat on the existing game WebSocket
- Global chat on a separate WebSocket for currently connected usernames

## Architecture

Two apps:

1. **Frontend** (`frontend/`) — React UI. It never generates puzzles or awards points.
2. **Backend** (`backend/`) — FastAPI. It owns rooms, the board, scoring, and chat validation.

**HTTP** is used to create/join/start rooms and to read the leaderboard. **WebSockets** carry live board updates, room chat, and global chat.

### Why the server is authoritative for game state

Clients send *intentions* (`set_cell`, `give_up`, `leave`). The server checks rules (clues locked, game still playing, identity taken from the socket), updates `room.grid`, and broadcasts a `state` payload. That prevents two browsers from disagreeing on the board and keeps scoring honest.

### Why live rooms remain in memory

V1/V2 is a single-process learning app. An in-memory `RoomManager` is enough for a handful of games. Restarting the API drops lobbies and in-progress boards. Finished scores survive in SQLite. A future production setup would persist rooms or use a shared store plus a pub/sub layer so multiple workers could run.

### Why SQLite is used

SQLite stores **players** (totals), **games**, and **game_players** (per-game awards). It is a local file, zero extra services, and fine for a leaderboard on one machine. Chat is **not** stored there.

### Why WebSockets are used

HTTP polling would lag and hammer the server. A socket per player in a room lets the server push one `state` object after each move. Chat uses the same room socket so we do not add Redis or a second realtime stack for in-game talk.

### Room chat vs global chat

| | Room chat | Global chat |
|---|---|---|
| Endpoint | `/ws/rooms/{join_code}?name=` | `/ws/global?name=` |
| Who | Players already in that room | Anyone connected with a username |
| Lifetime | Lobby + playing; closed when the game ends | Until that user disconnects from global chat |
| Storage | RAM only; gone when the room is dropped | RAM only |
| Game state | Cannot change the board | Cannot change rooms or boards |

Both validate length, strip control characters, take **username from the server connection**, and apply a simple per-user rate limit (5 messages / 5 seconds).

### How disconnects are handled

Closing the **room** socket (tab close, navigation, network drop) is the same as **leave**: 0 points if the game had started, `games_played` incremented, others continue. The last leaver abandons the game. Closing **global** chat only removes that user from the global presence list.

## Technology stack

- React 19, Vite 8, React Router
- FastAPI, Uvicorn, SQLAlchemy 2, SQLite
- pytest + Starlette TestClient

## Project structure

```
backend/app/           FastAPI app, models, rooms, scoring, chat
backend/tests/         Backend tests
frontend/src/          React pages, components, API/WS clients
frontend/public/audio/ Original looping ambient WAV
```

## How to run the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs  
SQLite file: `backend/sudoku.db` (created on first run)

## How to run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173/ with the backend already running.

## Environment variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | Backend | `sqlite:///./sudoku.db` | SQLAlchemy URL |
| `VITE_API_URL` | Frontend | `http://127.0.0.1:8000` | REST base |
| `VITE_WS_URL` | Frontend | `ws://127.0.0.1:8000` | WebSocket base |

Frontend env vars must be set at **dev server / build** time (`frontend/.env` is gitignored).

## API overview

| Method | Path | Body | Notes |
|---|---|---|---|
| GET | `/health` | | `{ "ok": true }` |
| POST | `/rooms` | `{ "name", "difficulty": 1-5 }` | Create lobby |
| POST | `/rooms/{code}/join` | `{ "name" }` | Max 4; lobby only |
| POST | `/rooms/{code}/start` | `{ "name" }` | Host only |
| GET | `/rooms/{code}` | | Public room snapshot (no solution unless given up) |
| GET | `/leaderboard` | | `name`, `points`, `games_played` |

Identity is a display name only (1–32 characters). There are no passwords.

## WebSocket overview

### Room: `ws://127.0.0.1:8000/ws/rooms/{join_code}?name=`

Client → server:

```json
{ "type": "set_cell", "row": 0, "col": 0, "value": 5 }
{ "type": "give_up" }
{ "type": "leave" }
{ "type": "chat", "message": "hello" }
```

Server → client:

```json
{ "type": "state", "status": "playing", "grid": [], "puzzle": [], "players": [], "...": "..." }
{ "type": "chat", "username": "alice", "message": "hello", "timestamp": "..." }
{ "type": "error", "message": "..." }
```

`value` 0 clears a cell. Clue cells cannot be changed. Winning requires the grid to match the generated solution.

### Global: `ws://127.0.0.1:8000/ws/global?name=`

```json
{ "type": "chat", "message": "hello" }
```

```json
{ "type": "presence", "users": ["alice", "bob"] }
{ "type": "chat", "username": "alice", "message": "hello", "timestamp": "..." }
{ "type": "error", "message": "..." }
```

## Game / scoring rules

- Levels 1–5 award pots of 20, 40, 60, 80, 100 points
- On a correct solve, remaining players split the pot with **integer division**
- Give up: solution is revealed, remaining players get 0, game counted
- A player who leaves or disconnects during play gets 0 and a game played; others keep going
- If nobody remains, the game is `abandoned`

## Chat behavior

- Max 200 characters after trim; empty messages rejected
- Rate limit: 5 messages per 5 seconds per user (per room, or globally)
- Username on a chat event is always the connected socket name
- Room chat stops after solve / give up / abandon
- Nothing is written to SQLite for chat

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Run from the `backend/` directory so `pytest.ini` can put `app` on `PYTHONPATH`.

## Known limitations (V1/V2)

- No accounts, sessions, or anti-spoofing beyond “you must already be in the room”
- One API process; no horizontal scale
- In-progress games vanish on restart
- Disconnect during play is leave (no reconnect token)
- Chat is ephemeral and lightly rate-limited, not moderated
- Music is a short original loop; browsers may require a click before playback
- Integer leftover points from splits are discarded

## Future improvements

- Auth and stable player IDs
- Reconnect / spectate
- Postgres + Redis (or similar) for multi-worker rooms
- Unique-solution puzzle generation
- Pencil marks, undo, notes
- Chat persistence and moderation tools

## License

See [LICENSE](LICENSE) (MIT placeholder).
