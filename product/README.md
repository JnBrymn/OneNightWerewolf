# One Night Werewolf - Development Progress

## Current Status: Step 3 Complete ✅

**Progress: 3/20 steps (15%)**

Last updated: 2026-02-02

---

## What's Working Now

### Backend (FastAPI + SQLite)
✅ **Step 1: Infrastructure**
- Health check endpoint
- Database initialization
- Test framework setup

✅ **Step 2: Game Set Creation**
- `POST /api/game-sets` - Create game with player count, roles, timer
- `GET /api/game-sets/{id}` - Retrieve game set details
- Validation: role count must equal players + 3

✅ **Step 3: Player Management & Lobby**
- `POST /api/players` - Create player
- `POST /api/game-sets/{id}/players/{id}/join` - Join game
- `GET /api/game-sets/{id}/players` - List players with counts
- `POST /api/game-sets/{id}/start` - Start game (validates player count)
- Prevents: duplicate joins, joining full games, starting without enough players

**Tests:** 13 passing tests (5 game set tests + 8 player tests)

### Frontend (Next.js + React)
✅ **Step 1: Landing Page**
- Home page with "Create Game" and "Join Game" buttons

✅ **Step 2: Game Creation**
- `/create` - Form to create game (player count, roles, timer)
- Real-time validation (role count = players + 3)
- Role selection with counters

✅ **Step 3: Join & Lobby**
- `/join` - Join game via shareable URL or manual code entry
- `/lobby/[game_set_id]` - Lobby with:
  - **Copy Join URL button** (shares direct link to join)
  - Real-time player list (polls every 2 seconds)
  - Player avatars/initials
  - Current player highlighted
  - Player count progress (e.g., 2/3)
  - "Start Game" button (enabled when full)
  - Game settings display

**Latest UX Improvement:**
- Changed from sharing game codes to sharing direct join URLs
- Players click the link and just enter their name (no code needed)

---

## How to Run

### Start Servers
```bash
./scripts/start_servers.sh
```

This starts both backend (port 8000) and frontend (port 3000) with color-coded logs.

### Run Tests
```bash
cd backend
uv run pytest tests/ -v
```

### Test the Full Flow
1. **Browser 1**: http://localhost:3000
   - Click "Create Game"
   - Set 3 players, adjust roles
   - Click "Create Game"
   - In lobby, click "📋 Copy Join URL"

2. **Browser 2 & 3**:
   - Paste the URL
   - Enter your name
   - Click "Join Game"

3. **All browsers**:
   - See player list update in real-time
   - When 3/3 players joined, "Start Game" enables

4. **Browser 1**:
   - Click "Start Game"
   - (Currently shows alert - Step 4 will implement actual game)

---

## What's Next: Step 4

**Game Creation & Role Assignment**
- [ ] Create `Game` database model
- [ ] Create `PlayerRole` model (tracks initial and final roles)
- [ ] Create `CenterCard` model (3 hidden cards)
- [ ] Implement role shuffling algorithm
- [ ] Assign N cards to players, 3 to center
- [ ] API endpoint to get player's role
- [ ] Frontend: Role reveal screen (shows your role before night phase)
- [ ] Tests for role assignment

**After Step 4:**
- Players will see their assigned role
- Backend will track initial role state
- Ready to implement night phase actions (Steps 5-10)

---

## Architecture

### Database Models
- **GameSet**: Game configuration (players needed, roles, timer)
- **Player**: Player identity (name, avatar)
- **game_set_players**: Many-to-many join table

**Coming in Step 4:**
- **Game**: Individual game instance
- **PlayerRole**: Role assignment per player per game
- **CenterCard**: The 3 cards in the center

### API Structure
```
/api/health          - Health check
/api/game-sets       - Game set CRUD
/api/players         - Player CRUD
/api/game-sets/{id}/players - Player management
/api/game-sets/{id}/start   - Start game
```

### Frontend Routes
```
/                    - Landing page
/create              - Create game form
/join                - Join game (with optional ?game_set_id=...)
/lobby/[id]          - Game lobby
```

---

## Key Files

### Product Documentation
- `product/instructions.md` - Original game rules
- `product/product_design.md` - Complete technical design
- `product/implementation_steps.md` - 20-step implementation plan
- `product/README.md` - This file (current progress)

### Demo Guides
- `QUICKSTART.md` - Step 1 demo
- `STEP2_DEMO.md` - Step 2 demo
- `STEP3_DEMO.md` - Step 3 demo (most recent)

### Backend
- `backend/main.py` - FastAPI app entry point
- `backend/models/` - Database models
- `backend/api/` - API endpoints
- `backend/tests/` - Test suite
- `backend/db/` - Database configuration

### Frontend
- `frontend/app/page.tsx` - Landing page
- `frontend/app/create/page.tsx` - Create game
- `frontend/app/join/page.tsx` - Join game
- `frontend/app/lobby/[game_set_id]/page.tsx` - Lobby

### Scripts
- `scripts/start_servers.sh` - Start both servers with unified logs

---

## Implementation Plan Summary

**✅ Completed (Steps 1-3):**
1. Project setup & infrastructure
2. Game set creation
3. Player management & lobby

**🔜 Next (Steps 4-7):**
4. Game creation & role assignment
5. Night phase infrastructure
6. Night phase - Werewolf role
7. Night phase - Seer role

**📋 Remaining (Steps 8-20):**
8. Night phase - Robber
9. Night phase - Troublemaker & Drunk
10. Night phase - Insomniac
11. Day discussion phase
12. Voting phase
13. Results & win conditions
14. Multi-game support & scoring
15. WebSocket real-time updates
16. Chat system
17. Additional roles (Minion, Mason, Tanner, Hunter)
18. Polish & error handling
19. Testing & documentation
20. Deployment prep

---

## Notes

- Using TDD approach (tests written before implementation)
- SQLite for database (easy for development, can upgrade to PostgreSQL later)
- Polling for real-time updates (WebSocket in Step 15)
- Player ID stored in localStorage
- Next.js rewrites API calls to backend

---

## Recent Changes (Session 2026-02-02)

1. Implemented Step 2: Game Set Creation
   - Backend: GameSet model, API endpoints, validation, 5 tests
   - Frontend: Create game form with role selection
   - Fixed Next.js API proxy configuration

2. Implemented Step 3: Player Management & Lobby
   - Backend: Player model, join/leave, player list, start game, 8 tests
   - Frontend: Join page, enhanced lobby with real-time updates
   - **UX Improvement**: Changed from game codes to shareable join URLs

3. Infrastructure Improvements
   - Updated `start_servers.sh` to use `uv sync` and show unified logs
   - Fixed Pydantic deprecation warnings
   - Consolidated dependencies in `pyproject.toml`

---

## To Resume Work

1. Review Step 4 in `product/implementation_steps.md`
2. Start servers: `./scripts/start_servers.sh`
3. Run existing tests to ensure everything works
4. Begin implementing Game and PlayerRole models
5. Write tests first (TDD), then implement

Good stopping point! 🌙
