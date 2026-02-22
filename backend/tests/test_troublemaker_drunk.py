"""Tests for Troublemaker and Drunk night actions."""
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


def test_troublemaker_swaps_two_other_players(monkeypatch):
    """Troublemaker swaps two other players' cards (no looking)."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Troublemaker", "Drunk", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    troublemaker_id = [pid for pid, r in role_map.items() if r == "Troublemaker"][0]
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]
    drunk_id = [pid for pid, r in role_map.items() if r == "Drunk"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    response = client.post(
        f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
        json={"player1_id": werewolf_id, "player2_id": drunk_id}
    )
    assert response.status_code == 200

    role_map_after = _get_roles(game_id, player_ids)
    assert role_map_after[werewolf_id] == "Drunk"
    assert role_map_after[drunk_id] == "Werewolf"
    assert role_map_after[troublemaker_id] == "Troublemaker"


def test_troublemaker_cannot_swap_self(monkeypatch):
    """Troublemaker must choose two other players."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Troublemaker", "Drunk", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    troublemaker_id = [pid for pid, r in role_map.items() if r == "Troublemaker"][0]
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    response = client.post(
        f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
        json={"player1_id": troublemaker_id, "player2_id": werewolf_id}
    )
    assert response.status_code == 400


def test_troublemaker_advances_night(monkeypatch):
    """Troublemaker completion advances to Drunk."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Troublemaker", "Drunk", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    troublemaker_id = [pid for pid, r in role_map.items() if r == "Troublemaker"][0]
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]
    drunk_id = [pid for pid, r in role_map.items() if r == "Drunk"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
        json={"player1_id": werewolf_id, "player2_id": drunk_id}
    )

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Troublemaker" in status["roles_completed"]
    assert status["current_role"] == "Drunk"


def test_drunk_swaps_with_center(monkeypatch):
    """Drunk exchanges card with center (no looking)."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Troublemaker", "Drunk", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    troublemaker_id = [pid for pid, r in role_map.items() if r == "Troublemaker"][0]
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]
    drunk_id = [pid for pid, r in role_map.items() if r == "Drunk"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
        json={"player1_id": werewolf_id, "player2_id": drunk_id}
    )
    # After Troublemaker swap, the player who now has the Drunk role performs drunk action
    role_map_after_tm = _get_roles(game_id, player_ids)
    current_drunk_id = [pid for pid, r in role_map_after_tm.items() if r == "Drunk"][0]

    response = client.post(
        f"/api/games/{game_id}/players/{current_drunk_id}/drunk-action",
        json={"card_index": 0}
    )
    assert response.status_code == 200
    assert "don't know your new role" in response.json().get("message", "")

    role_after = client.get(f"/api/games/{game_id}/players/{current_drunk_id}/role").json()
    assert role_after["current_role"] == "Villager"


def test_drunk_advances_night_to_insomniac_or_day(monkeypatch):
    """Drunk completion advances night (to Insomniac if in game, else DAY_DISCUSSION)."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Troublemaker", "Drunk", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)
    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    troublemaker_id = [pid for pid, r in role_map.items() if r == "Troublemaker"][0]
    werewolf_id = [pid for pid, r in role_map.items() if r == "Werewolf"][0]
    drunk_id = [pid for pid, r in role_map.items() if r == "Drunk"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
        json={"player1_id": werewolf_id, "player2_id": drunk_id}
    )
    role_map_after_tm = _get_roles(game_id, player_ids)
    current_drunk_id = [pid for pid, r in role_map_after_tm.items() if r == "Drunk"][0]
    client.post(
        f"/api/games/{game_id}/players/{current_drunk_id}/drunk-action",
        json={"card_index": 0}
    )

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Drunk" in status["roles_completed"]
    game = client.get(f"/api/games/{game_id}").json()
    assert game["state"] == "DAY_DISCUSSION"
