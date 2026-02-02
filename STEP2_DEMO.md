# Step 2 Complete: Game Set Creation

## What Was Implemented

✅ **Backend:**
- `GameSet` database model
- Pydantic schemas with validation (role count, valid roles)
- `POST /api/game-sets` - Create game set
- `GET /api/game-sets/{game_set_id}` - Get game set details
- 5 tests covering creation, validation, and retrieval

✅ **Frontend:**
- `/create` page with full game setup form
  - Player count slider (3-10)
  - Discussion timer slider (1-10 minutes)
  - Role selection with counters
  - Real-time validation (total roles = players + 3)
- `/lobby/[game_set_id]` page showing game details
- Updated landing page with working "Create Game" button

---

## How to Test

### 1. Run the Tests
```bash
cd backend
uv run pytest tests/test_game_sets.py -v
```

Expected output:
```
tests/test_game_sets.py::test_create_game_set PASSED
tests/test_game_sets.py::test_create_game_set_invalid_role_count PASSED
tests/test_game_sets.py::test_create_game_set_invalid_role PASSED
tests/test_game_sets.py::test_get_game_set PASSED
tests/test_game_sets.py::test_get_nonexistent_game_set PASSED
======================== 5 passed in 0.35s =========================
```

### 2. Start Both Servers
```bash
./scripts/start_servers.sh
```

### 3. Test Backend with curl

**Create a game set:**
```bash
curl -X POST http://localhost:8000/api/game-sets \
  -H "Content-Type: application/json" \
  -d '{
    "num_players": 5,
    "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
    "discussion_timer_seconds": 300
  }'
```

Expected response:
```json
{
  "game_set_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_by": null,
  "num_players": 5,
  "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
  "discussion_timer_seconds": 300,
  "created_at": "2026-02-01T12:34:56.789Z",
  "updated_at": null,
  "ended_at": null
}
```

**Get a game set (use game_set_id from above):**
```bash
curl http://localhost:8000/api/game-sets/{game_set_id}
```

**Test validation (should fail - wrong role count):**
```bash
curl -X POST http://localhost:8000/api/game-sets \
  -H "Content-Type: application/json" \
  -d '{
    "num_players": 5,
    "selected_roles": ["Werewolf", "Villager"],
    "discussion_timer_seconds": 300
  }'
```

Expected: 422 validation error

### 4. Test Frontend

Open browser to: **http://localhost:3000**

**Test Flow:**
1. Click "Create Game" button
2. See Create Game form with:
   - Player count slider (default: 5)
   - Discussion timer slider (default: 5:00)
   - Role selection grid
   - Role counter showing "Total: 8 / Required: 8" (green)
3. Adjust player count to 6 (required roles becomes 9)
   - Counter turns red: "Need 1 more role(s)"
4. Add 1 more Villager role
   - Counter turns green: "✓ Role count is correct!"
5. Click "Create Game" button
6. Redirected to `/lobby/{game_set_id}` showing:
   - Game Code (first 8 chars of game_set_id)
   - Players Needed: 6
   - Discussion Time: 5:00
   - Roles in Game: Werewolf x2, Villager x4, Seer x1, Robber x1, Troublemaker x1
   - "Coming Soon" message for Step 3

### 5. Test the Full API Flow

You can also check the auto-generated API docs:

**http://localhost:8000/docs**

This shows all endpoints with interactive testing!

---

## What's Next

**Step 3: Player Management & Lobby**
- Player creation
- Join game functionality
- Lobby with player list
- Start game button (when enough players joined)
- Real-time player updates (polling for now, WebSocket later)

---

## Files Changed/Created

### Backend:
- `backend/models/game_set.py` - GameSet database model
- `backend/models/schemas.py` - Pydantic schemas with validation
- `backend/api/game_sets.py` - Game set API endpoints
- `backend/tests/test_game_sets.py` - 5 tests for game set functionality
- `backend/main.py` - Added game_sets router

### Frontend:
- `frontend/app/create/page.tsx` - Create game form page
- `frontend/app/lobby/[game_set_id]/page.tsx` - Lobby page
- `frontend/app/page.tsx` - Updated landing page with working Create button

---

## Notes

- Role validation ensures only valid roles can be selected
- Total role count must equal players + 3 (enforced both frontend and backend)
- Discussion timer between 1-10 minutes
- Game set ID is a UUID generated automatically
- All timestamps are ISO 8601 format
