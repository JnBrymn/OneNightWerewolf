# One Night Werewolf

A digital implementation of the One Night Ultimate Werewolf card game.

## Quick Start

Start both servers:
```bash
./scripts/start_servers.sh
```
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Manual Start

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

## Tests

Backend tests:
```bash
cd backend
uv run pytest tests/ -v
```

Run a specific test file:
```bash
uv run pytest tests/test_players.py -v
```

## API Docs

When the backend is running:
- Interactive docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Deployment (Fly.io)

```bash
./scripts/deploy_fly.sh
```

Or manually:
```bash
fly auth login
fly apps create onw-app
fly deploy
```
