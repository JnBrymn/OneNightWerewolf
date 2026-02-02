# Quick Start Guide - Step 1 Complete

## What Was Implemented

✅ **Backend Infrastructure**
- FastAPI app with SQLite database
- Health check endpoint at `/health`
- CORS configured for frontend
- Database initialization
- Test infrastructure with pytest

✅ **Frontend Landing Page**
- One Night Werewolf landing page
- "Create Game" and "Join Game" buttons (placeholder)
- Basic styling and layout

✅ **Tests**
- Health check test passes ✓

---

## How to Run

### 1. Run the Tests

```bash
cd backend
uv run pytest tests/test_health.py -v
```

Expected output:
```
tests/test_health.py::test_health_check PASSED
======================== 1 passed in 0.30s =========================
```

### 2. Start Both Servers (Recommended)

From the project root, run:
```bash
./scripts/start_servers.sh
```

This will:
- Check dependencies and sync them
- Start both backend and frontend servers
- Show color-coded logs in the same console:
  - `[BACKEND]` (cyan) for backend logs
  - `[FRONTEND]` (blue) for frontend logs
- Press Ctrl+C to stop both servers

You should see:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Starting One Night Werewolf Servers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Backend:  http://localhost:8000
Frontend: http://localhost:3000
Press Ctrl+C to stop both servers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[BACKEND] INFO:     Uvicorn running on http://0.0.0.0:8000
[FRONTEND] ▲ Next.js 14.0.0
[FRONTEND] - Local:        http://localhost:3000
```

### 3. Test the Backend Health Endpoint

In another terminal:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy"}
```

### 4. View the Application

Open your browser to: **http://localhost:3000**

You should see:
- **One Night Werewolf** title
- Description: "A fast-paced game of deduction and deception"
- Two buttons: "Create Game" and "Join Game"
- "How to Play" section

Clicking the buttons will show "Coming soon!" alerts.

---

### Alternative: Start Servers Manually

If you prefer to run servers in separate terminals:

**Backend (Terminal 1):**
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```

---

## What's Next

Step 2 will implement:
- Game Set creation API
- Database models for GameSet
- Ability to create a game with player count and role selection
- Tests for game set creation

---

## Troubleshooting

**Backend port already in use:**
```bash
# Kill existing process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Frontend port already in use:**
```bash
# Kill existing process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Database issues:**
```bash
# Remove and recreate database
rm backend/onw.db
# Restart backend server (it will recreate the database)
```
