#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
PLAYERS="${PLAYERS:-3}"
ROLES_CSV="${ROLES_CSV:-}"  # Optional: comma-separated roles, length must equal PLAYERS+3

python - <<'PY'
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError

backend = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
frontend = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
players = int(os.environ.get("PLAYERS", "3"))
roles_csv = os.environ.get("ROLES_CSV", "").strip()


def _read_json(resp):
    body = resp.read().decode("utf-8")
    if not body:
        return {}
    return json.loads(body)


def post(path, payload=None):
    url = f"{backend}{path}"
    data = b"" if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req) as resp:
            return _read_json(resp)
    except HTTPError as e:
        details = e.read().decode("utf-8")
        raise RuntimeError(f"POST {url} failed: {e.code} {details}")


def get(path):
    url = f"{backend}{path}"
    req = Request(url)
    try:
        with urlopen(req) as resp:
            return _read_json(resp)
    except HTTPError as e:
        details = e.read().decode("utf-8")
        raise RuntimeError(f"GET {url} failed: {e.code} {details}")


if roles_csv:
    roles = [r.strip() for r in roles_csv.split(",") if r.strip()]
else:
    # Default 3 players + 3 center cards
    roles = ["Werewolf", "Werewolf", "Villager", "Seer", "Robber", "Villager"]

if len(roles) != players + 3:
    raise RuntimeError(
        f"Role count must equal players + 3. Got players={players}, roles={len(roles)}"
    )

# Create game set
payload = {
    "num_players": players,
    "selected_roles": roles,
    "discussion_timer_seconds": 300
}

game_set = post("/api/game-sets", payload)
game_set_id = game_set["game_set_id"]

# Create players and join
player_ids = []
for i in range(players):
    player = post("/api/players", {"player_name": f"Player{i+1}"})
    player_id = player["player_id"]
    post(f"/api/game-sets/{game_set_id}/players/{player_id}/join")
    player_ids.append(player_id)

# Start game
started = post(f"/api/game-sets/{game_set_id}/start")
game_id = started["game_id"]

print("Game created:")
print(f"  game_set_id: {game_set_id}")
print(f"  game_id:     {game_id}")
print("\nPlayer URLs:")
for idx, pid in enumerate(player_ids, start=1):
    role = get(f"/api/games/{game_id}/players/{pid}/role")
    role_name = role.get("current_role")
    print(f"  Player {idx} ({role_name}): {frontend}/game/{game_id}?player_id={pid}")
PY
