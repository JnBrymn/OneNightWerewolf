# One Night Werewolf

A digital implementation of the One Night Ultimate Werewolf card game.

---

## 🎯 CURRENT STATUS: Step 3 Complete (15% Progress)

**👉 NEXT SESSION: Start with [`START_HERE.md`](START_HERE.md)**

### ✅ What's Working Now
- ✓ Game creation (players, roles, timer configuration)
- ✓ Players join via shareable URL
- ✓ Real-time lobby with player list
- ✓ "Start Game" validation

### 🔜 Next: Step 4 - Game Creation & Role Assignment
Create Game/PlayerRole models, implement role shuffling, role reveal UI.
**See:** `product/implementation_steps.md` - Step 4

**Progress:** 3 of 20 steps complete | 13 tests passing

---

## Quick Start

### Start Both Servers
```bash
./scripts/start_servers.sh
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- Shows unified logs with color-coded prefixes

### Run Tests
```bash
cd backend
uv run pytest tests/ -v
```

### Try the App
1. Open http://localhost:3000
2. Click "Create Game"
3. Set players and roles
4. Copy join URL and share with others
5. Start game when everyone's joined

---

## Project Structure

```
.
├── START_HERE.md              # 👈 Resume work here
├── product/
│   ├── README.md              # Detailed progress tracking
│   ├── implementation_steps.md # 20-step implementation plan
│   ├── product_design.md      # Complete technical design
│   └── instructions.md        # Original game rules
├── backend/                   # FastAPI + SQLite
│   ├── main.py
│   ├── models/                # Database models
│   ├── api/                   # API endpoints
│   ├── db/                    # Database config
│   └── tests/                 # Test suite (13 passing)
├── frontend/                  # Next.js + React
│   └── app/
│       ├── page.tsx           # Landing page
│       ├── create/            # Create game
│       ├── join/              # Join game
│       └── lobby/             # Game lobby
└── scripts/
    └── start_servers.sh       # Start both servers

```

---

## Tech Stack

- **Backend:** FastAPI, SQLite, SQLAlchemy, Pytest
- **Frontend:** Next.js 14 (App Router), React, TypeScript
- **Tools:** uv (Python), npm
- **Deployment:** Configured for Fly.io

---

## Development

### Manual Server Start

**Backend:**
```bash
cd backend
uv run uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Testing
```bash
# Run all tests
cd backend && uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_players.py -v

# With coverage
uv run pytest tests/ -v --cov
```

### Database
- SQLite database: `backend/onw.db`
- Auto-created on first run
- Reset: `rm backend/onw.db` and restart

---

## API Documentation

When servers are running:
- **Interactive API docs:** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

### Key Endpoints
- `POST /api/game-sets` - Create game
- `GET /api/game-sets/{id}` - Get game details
- `POST /api/players` - Create player
- `POST /api/game-sets/{id}/players/{id}/join` - Join game
- `GET /api/game-sets/{id}/players` - List players
- `POST /api/game-sets/{id}/start` - Start game

---

## Implementation Progress

**Completed (3/20):**
1. ✅ Project setup & infrastructure
2. ✅ Game set creation
3. ✅ Player management & lobby

**Next (4-7):**
4. 🔜 Game creation & role assignment
5. ⬜ Night phase infrastructure
6. ⬜ Night phase - Werewolf role
7. ⬜ Night phase - Seer role

**Future (8-20):**
- Night phase roles (Robber, Troublemaker, Drunk, Insomniac)
- Day discussion & voting
- Results & win conditions
- Multi-game scoring
- WebSocket real-time updates
- Chat system
- Additional roles (Minion, Mason, Tanner, Hunter)
- Polish, testing, deployment

**Full plan:** See `product/implementation_steps.md`

---

## Key Features

### Current
- **Shareable Join URLs** - Copy link, share with friends
- **Real-time Lobby** - See players join in real-time (2s polling)
- **Role Validation** - Ensures correct number of roles
- **Player Management** - Can't join twice, can't join full games

### Coming Soon (Step 4)
- Role assignment and reveal
- Night phase with role actions
- Discussion and voting
- Win condition logic

---

## Notes

- **TDD Approach:** Tests written before implementation
- **Player ID:** Stored in browser localStorage
- **Real-time:** Currently polling, WebSocket in Step 15
- **UV Required:** Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## Deployment to Fly.io

```bash
./scripts/deploy_fly.sh
```

Or manually:
```bash
fly auth login
fly apps create onw-app
fly deploy
```

---

## Resources

- **Product Docs:** `product/` directory
- **Demo Guides:** `STEP{1,2,3}_DEMO.md`
- **Quick Start:** `QUICKSTART.md`
- **Resume Work:** `START_HERE.md` 👈

---

**Last Updated:** 2026-02-02
**Next Session:** Pick up with Step 4 (see `START_HERE.md`)
