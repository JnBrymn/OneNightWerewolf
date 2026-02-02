# Step 3 Complete: Player Management & Lobby

## What Was Implemented

✅ **Backend:**
- `Player` database model with many-to-many relationship to GameSet
- `POST /api/players` - Create player
- `GET /api/players/{player_id}` - Get player details
- `POST /api/game-sets/{game_set_id}/players/{player_id}/join` - Join game
- `GET /api/game-sets/{game_set_id}/players` - List players in game
- `POST /api/game-sets/{game_set_id}/start` - Start game (validates player count)
- 8 tests covering all player operations

✅ **Frontend:**
- `/join` page - Enter game code and player name
- Updated `/lobby/[game_set_id]` page with:
  - Game code display with copy button
  - Real-time player list (polls every 2 seconds)
  - Player avatars or initials
  - Current player highlighted
  - Player count progress
  - "Start Game" button (enabled when enough players)
  - Game settings display
- Updated landing page with working "Join Game" button
- Player ID stored in localStorage

---

## How to Test

### 1. Run the Tests
```bash
cd backend
uv run pytest tests/test_players.py -v
```

Expected output:
```
tests/test_players.py::test_create_player PASSED
tests/test_players.py::test_create_player_without_avatar PASSED
tests/test_players.py::test_join_game_set PASSED
tests/test_players.py::test_list_players_in_game_set PASSED
tests/test_players.py::test_cannot_join_game_set_twice PASSED
tests/test_players.py::test_cannot_join_full_game_set PASSED
tests/test_players.py::test_cannot_start_game_without_enough_players PASSED
tests/test_players.py::test_can_start_game_with_enough_players PASSED
======================== 8 passed in 0.36s =========================
```

### 2. Start Both Servers
```bash
./scripts/start_servers.sh
```

### 3. Test Backend with curl

**Create a player:**
```bash
curl -X POST http://localhost:8000/api/players \
  -H "Content-Type: application/json" \
  -d '{"player_name": "Alice", "avatar_url": "https://i.pravatar.cc/150?img=1"}'
```

Expected response:
```json
{
  "player_id": "abc123...",
  "user_id": null,
  "player_name": "Alice",
  "avatar_url": "https://i.pravatar.cc/150?img=1",
  "created_at": "2026-02-01T..."
}
```

**Create a game set (save the game_set_id):**
```bash
curl -X POST http://localhost:8000/api/game-sets \
  -H "Content-Type: application/json" \
  -d '{"num_players": 3, "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Seer", "Robber"], "discussion_timer_seconds": 180}'
```

**Join the game (use IDs from above):**
```bash
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/players/{player_id}/join
```

Expected: `{"status": "joined", ...}`

**List players:**
```bash
curl http://localhost:8000/api/game-sets/{game_set_id}/players
```

Expected:
```json
{
  "players": [{"player_id": "...", "player_name": "Alice", ...}],
  "current_count": 1,
  "required_count": 3
}
```

**Try to start (should fail - not enough players):**
```bash
curl -X POST http://localhost:8000/api/game-sets/{game_set_id}/start
```

Expected: `400 {"detail": "Not enough players. Need 3, have 1"}`

### 4. Test Frontend - Full Flow

Open **3 different browser windows** (or use incognito/different browsers) to simulate 3 players:

**Browser 1 (Host):**
1. Go to http://localhost:3000
2. Click **"Create Game"**
3. Set players to 3
4. Adjust roles (need 6 total)
5. Click **"Create Game"**
6. You're in the lobby - see game code (e.g., "20072c41")
7. Click **"Copy Full Code"** button
8. See yourself in the players list (highlighted green)
9. "Start Game" button is disabled - "Waiting for Players..."

**Browser 2 (Player 2):**
1. Go to http://localhost:3000
2. Click **"Join Game"**
3. Paste the full game code from Browser 1
4. Enter name: "Bob"
5. Click **"Join Game"**
6. You're in the lobby
7. See 2 players: Host and yourself (you're highlighted)
8. See "Waiting for 1 more player(s)..."

**Browser 1 (Host) - Check update:**
- Player list automatically updates (every 2 seconds)
- Now shows 2 players
- Still shows "Waiting for 1 more player(s)..."

**Browser 3 (Player 3):**
1. Go to http://localhost:3000
2. Click **"Join Game"**
3. Enter same game code
4. Enter name: "Charlie"
5. Click **"Join Game"**
6. You're in the lobby
7. See all 3 players

**All Browsers - Check updates:**
- All 3 browsers now show 3/3 players
- Green "Start Game" button enabled
- No more "Waiting..." message

**Browser 1 (Host) - Start the game:**
1. Click **"Start Game"**
2. See alert: "Game started! Game ID: mock-game-id"
   (In Step 4, this will redirect to the actual game)

---

## What's Next

**Step 4: Game Creation & Role Assignment**
- Create `Game` and `PlayerRole` models
- Implement role shuffling and assignment algorithm
- Assign N cards to players, 3 to center
- Create `CenterCard` model for the 3 hidden cards
- Role reveal UI for each player
- Store initial roles (before night phase swaps)

---

## Files Changed/Created

### Backend:
- `backend/models/player.py` - Player model and game_set_players association table
- `backend/models/game_set.py` - Added players relationship
- `backend/models/schemas.py` - Added PlayerCreate and PlayerResponse
- `backend/api/players.py` - Player endpoints
- `backend/api/game_sets.py` - Added join, list players, start game endpoints
- `backend/tests/test_players.py` - 8 tests
- `backend/main.py` - Added players router

### Frontend:
- `frontend/app/join/page.tsx` - Join game page
- `frontend/app/lobby/[game_set_id]/page.tsx` - Complete lobby with player list and polling
- `frontend/app/page.tsx` - Enabled Join Game button

---

## Key Features

**Backend:**
- Prevents duplicate joins (same player can't join twice)
- Prevents joining full games
- Validates player count before starting
- Many-to-many relationship (players can join multiple game sets)

**Frontend:**
- Real-time player updates via polling (2-second interval)
- Current player highlighted in green
- Avatar support (shows initial if no avatar)
- Game code copy to clipboard
- Disabled "Start Game" until enough players
- localStorage persistence of player ID

---

## Progress

**Completed: 3/20 steps (15%)**

Steps 1-3: ✅ Infrastructure, Game Sets, Players & Lobby
Next: Step 4 - Role Assignment
