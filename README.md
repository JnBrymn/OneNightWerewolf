# One Night Werewolf

A digital implementation of the One Night Ultimate Werewolf card game. Built with Next.js (frontend) and FastAPI (backend).

## Documentation

- **Product Design**: See `product/product_design.md` for game rules, UI/UX specs, and architecture
- **Implementation Steps**: See `product/implementation_steps.md` for the development roadmap

## Quick Start

Start both servers:
```bash
./scripts/start_servers.sh
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Scripts

- **`start_servers.sh`** - Starts both backend and frontend dev servers with dependency checks
- **`deploy_fly.sh`** - Deploys the app to Fly.io (checks auth, creates app if needed)
- **`dev_seed_game.py`** - Creates a test game (random 3-player by default). Use `--players` (CSV of roles for player 1..N) and `--center` (CSV of 3 center roles, left to right) to fix setup; roles can be lowercase or short codes (e.g. `w,s,v`). Run `python scripts/dev_seed_game.py --help` for details.
- **`start_prod.sh`** - Production startup script for Fly.io (runs both servers)

## Development

Backend:
```bash
cd backend
uv run uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm run dev
```

Tests:
```bash
cd backend
uv run pytest tests/ -v
```

## API Docs

When the backend is running:
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Deployment

Deploy to Fly.io:
```bash
./scripts/deploy_fly.sh
```
