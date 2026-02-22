import sys
from pathlib import Path

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app
from services import game_service

client = TestClient(app)


def _start_game_with_roles(roles):
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": roles,
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    player_ids = []
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"Player{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")
        player_ids.append(player["player_id"])

    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    game_id = start_response.json()["game_id"]

    return game_id, player_ids


def _get_roles(game_id, player_ids):
    roles = {}
    for player_id in player_ids:
        response = client.get(f"/api/games/{game_id}/players/{player_id}/role")
        roles[player_id] = response.json()["current_role"]
    return roles


def test_werewolf_sees_other_werewolves(monkeypatch):
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Werewolf", "Villager", "Seer", "Robber", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    werewolves = [pid for pid, role in role_map.items() if role == "Werewolf"]

    assert len(werewolves) == 2

    response = client.get(f"/api/games/{game_id}/players/{werewolves[0]}/night-info")
    assert response.status_code == 200

    data = response.json()
    assert data["role"] == "Werewolf"
    assert data["is_lone_wolf"] is False
    assert len(data["other_werewolves"]) == 1
    assert data["other_werewolves"][0]["player_id"] == werewolves[1]


def test_lone_wolf_can_view_center(monkeypatch):
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Villager", "Seer", "Robber", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]

    response = client.post(
        f"/api/games/{game_id}/players/{werewolf_id}/view-center",
        json={"card_index": 0}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "Robber"

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert status["current_role"] == "Seer"


def test_werewolf_acknowledge_completes_role(monkeypatch):
    """When all werewolves acknowledge, night advances to the next role (Seer is in this game)."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Werewolf", "Villager", "Seer", "Robber", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    werewolves = [pid for pid, role in role_map.items() if role == "Werewolf"]

    for werewolf_id in werewolves:
        response = client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
        assert response.status_code == 200

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Werewolf" in status["roles_completed"]
    assert status["current_role"] == "Seer"
