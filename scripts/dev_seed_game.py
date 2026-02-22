#!/usr/bin/env python3
"""
Seed a dev game via API, then optionally overwrite DB with specific player roles and center cards.

Two parameters:
  --players   CSV of roles for player 1, player 2, ... player N (N = number of roles in list).
  --center    CSV of the 3 center card roles, left to right.

If neither is given: random 3-player game. If only one is given: error (both required for fixed setup).

Role names: lowercase (werewolf, seer, villager, ...) or short codes (w, s, v, ...).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import webbrowser
from pathlib import Path

# Run from repo root; backend is backend/
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# DB path same as backend/db/database.py (sqlite:///./onw.db -> backend/onw.db)
DB_PATH = BACKEND_DIR / "onw.db"

# One alias per role; same first letter as name, two letters when needed for uniqueness
ROLE_ALIASES = {
    "Werewolf": "w",
    "Villager": "v",
    "Seer": "s",
    "Robber": "r",
    "Troublemaker": "tr",
    "Minion": "mi",
    "Mason": "ma",
    "Drunk": "d",
    "Insomniac": "i",
    "Tanner": "ta",
    "Hunter": "h",
}
CANONICAL_ROLES = list(ROLE_ALIASES.keys())
SHORT_CODES = {alias: role for role, alias in ROLE_ALIASES.items()}

# Wake order for active_roles (must match backend)
WAKE_ORDER = [
    "Doppelganger", "Werewolf", "Minion", "Mason", "Seer",
    "Robber", "Troublemaker", "Drunk", "Insomniac",
]


def _roles_help_text() -> str:
    """List all roles and their alias for error messages."""
    return "Valid roles and aliases:\n" + "\n".join(f"  {r}: {a}" for r, a in ROLE_ALIASES.items())


def normalize_role(token: str) -> str:
    """Convert a token (lowercase name or short code) to canonical role name."""
    t = token.strip().lower()
    if not t:
        raise ValueError("Empty role token")
    if t in SHORT_CODES:
        return SHORT_CODES[t]
    # Lowercase full name -> title case
    canonical = t.title()
    if canonical not in CANONICAL_ROLES:
        raise ValueError(
            f"Unknown role: {token!r} (normalized to {canonical!r})\n{_roles_help_text()}"
        )
    return canonical


def normalize_roles(tokens: list[str]) -> list[str]:
    return [normalize_role(t) for t in tokens]


def team_for_role(role: str) -> str:
    if role in ("Werewolf", "Minion"):
        return "werewolf"
    if role == "Tanner":
        return "tanner"
    return "village"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seed a dev game. Use --players and --center to fix roles; else random 3-player game.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--players",
        type=str,
        default="",
        metavar="R1,R2,...",
        help="CSV of roles for player 1 through N (lowercase or short codes: w, s, v, ...).",
    )
    parser.add_argument(
        "--center",
        type=str,
        default="",
        metavar="C1,C2,C3",
        help="CSV of the 3 center card roles, left to right. Required if --players is set.",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default=os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/"),
        help="Backend base URL",
    )
    parser.add_argument(
        "--frontend",
        type=str,
        default=os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/"),
        help="Frontend base URL for printing player links",
    )
    args = parser.parse_args()

    has_players = bool(args.players.strip())
    has_center = bool(args.center.strip())

    if has_center and not has_players:
        print("Error: --center requires --players (player roles must be specified).", file=sys.stderr)
        return 1
    if has_players and not has_center:
        print("Error: --players requires --center (exactly 3 center roles).", file=sys.stderr)
        return 1

    if has_players and has_center:
        player_tokens = [p.strip() for p in args.players.split(",") if p.strip()]
        center_tokens = [c.strip() for c in args.center.split(",") if c.strip()]
        if len(center_tokens) != 3:
            print("Error: --center must have exactly 3 roles (left, center, right).", file=sys.stderr)
            return 1
        try:
            player_roles = normalize_roles(player_tokens)
            center_roles = normalize_roles(center_tokens)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        num_players = len(player_roles)
        full_roles = player_roles + center_roles
    else:
        player_roles = None
        center_roles = None
        full_roles = None
        num_players = 3

    # Create game via API
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError

    def post(path: str, payload: dict | None = None) -> dict:
        url = f"{args.backend}{path}"
        data = b"" if payload is None else json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as e:
            body = e.read().decode("utf-8")
            raise RuntimeError(f"POST {url} failed: {e.code} {body}")

    def get(path: str) -> dict:
        url = f"{args.backend}{path}"
        req = Request(url)
        try:
            with urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except HTTPError as e:
            body = e.read().decode("utf-8")
            raise RuntimeError(f"GET {url} failed: {e.code} {body}")

    if full_roles is None:
        roles = ["Werewolf", "Werewolf", "Villager", "Seer", "Robber", "Villager"]
        if num_players != 3:
            roles = ["Werewolf", "Villager"] * max(0, (num_players + 3) // 2)
            roles = (roles + ["Villager"])[: num_players + 3]
    else:
        roles = full_roles

    payload = {
        "num_players": num_players,
        "selected_roles": roles,
        "discussion_timer_seconds": 300,
    }
    game_set = post("/api/game-sets", payload)
    game_set_id = game_set["game_set_id"]

    player_ids = []
    for i in range(num_players):
        player = post("/api/players", {"player_name": f"Player{i + 1}"})
        pid = player["player_id"]
        post(f"/api/game-sets/{game_set_id}/players/{pid}/join")
        player_ids.append(pid)

    started = post(f"/api/game-sets/{game_set_id}/start")
    game_id = started["game_id"]

    if player_roles is not None and center_roles is not None:
        # Overwrite DB: player roles and center cards
        if not DB_PATH.exists():
            print(f"Error: Database not found at {DB_PATH}. Start the backend once to create it.", file=sys.stderr)
            return 1

        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Load all models so relationship chain resolves (player -> game_set_players; GameSet -> game_set_players; Game -> GameSet)
        from models import player  # noqa: F401
        from models.game_set import GameSet  # noqa: F401
        from models.game import Game
        from models.player_role import PlayerRole
        from models.center_card import CenterCard

        engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            game = db.query(Game).filter(Game.game_id == game_id).first()
            if not game:
                print("Error: Game not found in DB.", file=sys.stderr)
                return 1

            # Player order: same as join order (player_ids)
            for i, pid in enumerate(player_ids):
                pr = db.query(PlayerRole).filter(
                    PlayerRole.game_id == game_id,
                    PlayerRole.player_id == pid,
                ).first()
                if not pr:
                    continue
                role = player_roles[i]
                pr.initial_role = role
                pr.current_role = role
                pr.team = team_for_role(role)

            # Center: left, center, right
            positions = ["left", "center", "right"]
            for i, pos in enumerate(positions):
                cc = db.query(CenterCard).filter(
                    CenterCard.game_id == game_id,
                    CenterCard.position == pos,
                ).first()
                if cc:
                    cc.role = center_roles[i]

            # Recompute active_roles on game (roles that wake up, in wake order)
            all_roles_in_game = set(player_roles) | set(center_roles)
            active_roles = [r for r in WAKE_ORDER if r in all_roles_in_game]
            game.active_roles = active_roles

            db.commit()
        finally:
            db.close()

    print("Game created:")
    print(f"  game_set_id: {game_set_id}")
    print(f"  game_id:     {game_id}")
    print("\nPlayer URLs:")
    urls = []
    for idx, pid in enumerate(player_ids, start=1):
        role_info = get(f"/api/games/{game_id}/players/{pid}/role")
        role_name = role_info.get("current_role", "?")
        url = f"{args.frontend}/game/{game_id}?player_id={pid}"
        urls.append(url)
        print(f"  Player {idx} ({role_name}): {url}")
    for url in urls:
        webbrowser.open(url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
