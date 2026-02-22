"""Tests for Insomniac, Minion, and Mason night actions (info + acknowledge)."""
import sys
from pathlib import Path

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
    return {
        pid: client.get(f"/api/games/{game_id}/players/{pid}/role").json()["current_role"]
        for pid in player_ids
    }


def test_insomniac_night_info_and_acknowledge(monkeypatch):
    """Insomniac gets current role and acknowledges."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Insomniac", "Villager", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]
    insomniac_id = [pid for pid, r in role_map.items() if r == "Insomniac"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    info = client.get(f"/api/games/{game_id}/players/{insomniac_id}/night-info").json()
    assert info["role"] == "Insomniac"
    assert info["current_role"] == "Insomniac"
    assert info["night_action_completed"] is False

    response = client.post(f"/api/games/{game_id}/players/{insomniac_id}/acknowledge")
    assert response.status_code == 200

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Insomniac" in status["roles_completed"]
    game = client.get(f"/api/games/{game_id}").json()
    assert game["state"] == "DAY_DISCUSSION"


def test_minion_night_info_and_acknowledge(monkeypatch):
    """Minion sees werewolves and acknowledges."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Minion", "Villager", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]
    minion_id = [pid for pid, r in role_map.items() if r == "Minion"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    info = client.get(f"/api/games/{game_id}/players/{minion_id}/night-info").json()
    assert info["role"] == "Minion"
    assert "werewolves" in info
    assert len(info["werewolves"]) == 1
    assert info["werewolves"][0]["player_id"] == werewolf_id

    response = client.post(f"/api/games/{game_id}/players/{minion_id}/acknowledge")
    assert response.status_code == 200

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Minion" in status["roles_completed"]


def test_mason_night_info_other_mason_and_acknowledge(monkeypatch):
    """Two Masons see each other and acknowledge."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Mason", "Mason", "Villager", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    mason_ids = [pid for pid, r in role_map.items() if r == "Mason"]

    info1 = client.get(f"/api/games/{game_id}/players/{mason_ids[0]}/night-info").json()
    assert info1["role"] == "Mason"
    assert info1["other_mason"] is not None
    assert info1["other_mason"]["player_id"] == mason_ids[1]
    assert info1["in_center"] is False

    client.post(f"/api/games/{game_id}/players/{mason_ids[0]}/acknowledge")
    client.post(f"/api/games/{game_id}/players/{mason_ids[1]}/acknowledge")

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Mason" in status["roles_completed"]


def test_mason_in_center(monkeypatch):
    """When only one Mason is a player, other is in center."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Mason", "Villager", "Villager", "Mason", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    mason_id = [pid for pid, r in role_map.items() if r == "Mason"][0]

    info = client.get(f"/api/games/{game_id}/players/{mason_id}/night-info").json()
    assert info["role"] == "Mason"
    assert info["other_mason"] is None
    assert info["in_center"] is True

    client.post(f"/api/games/{game_id}/players/{mason_id}/acknowledge")
    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Mason" in status["roles_completed"]
