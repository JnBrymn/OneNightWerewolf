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
    roles = {}
    for player_id in player_ids:
        response = client.get(f"/api/games/{game_id}/players/{player_id}/role")
        roles[player_id] = response.json()["current_role"]
    return roles


def test_robber_exchanges_with_player_and_views_new_role(monkeypatch):
    """Robber exchanges with target player and sees their new role."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    # First 3 roles go to players: Werewolf, Seer, Robber
    roles = ["Werewolf", "Seer", "Robber", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    robber_id = [pid for pid, role in role_map.items() if role == "Robber"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    # Advance to Robber phase (Werewolf then Seer complete)
    client.post(f"/api/games/{game_id}/players/{target_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )

    response = client.post(
        f"/api/games/{game_id}/players/{robber_id}/robber-action",
        json={"target_player_id": target_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["new_role"] == "Werewolf"
    assert "message" in data

    # Robber now has Werewolf, target has Robber
    r_after = client.get(f"/api/games/{game_id}/players/{robber_id}/role").json()
    t_after = client.get(f"/api/games/{game_id}/players/{target_id}/role").json()
    assert r_after["current_role"] == "Werewolf"
    assert t_after["current_role"] == "Robber"


def test_robber_action_creates_swap_action_record(monkeypatch):
    """Action record is created with SWAP_PLAYER_TO_PLAYER."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Seer", "Robber", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    robber_id = [pid for pid, role in role_map.items() if role == "Robber"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    client.post(f"/api/games/{game_id}/players/{target_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )

    client.post(
        f"/api/games/{game_id}/players/{robber_id}/robber-action",
        json={"target_player_id": target_id}
    )

    actions_response = client.get(f"/api/games/{game_id}/players/{robber_id}/actions")
    assert actions_response.status_code == 200
    actions = actions_response.json()["actions"]
    swap_actions = [a for a in actions if a["action_type"] == "SWAP_PLAYER_TO_PLAYER"]
    assert len(swap_actions) == 1
    assert "You exchanged cards with" in swap_actions[0]["description"]
    assert "You are now: Werewolf" in swap_actions[0]["description"]


def test_robber_cannot_exchange_with_self(monkeypatch):
    """Robber cannot choose themselves."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Seer", "Robber", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    robber_id = [pid for pid, role in role_map.items() if role == "Robber"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    client.post(f"/api/games/{game_id}/players/{target_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )

    response = client.post(
        f"/api/games/{game_id}/players/{robber_id}/robber-action",
        json={"target_player_id": robber_id}
    )
    assert response.status_code == 400


def test_robber_role_completion_advances_night(monkeypatch):
    """When Robber completes action, night phase advances to next role."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Seer", "Robber", "Villager", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    robber_id = [pid for pid, role in role_map.items() if role == "Robber"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    client.post(f"/api/games/{game_id}/players/{target_id}/acknowledge")
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )

    client.post(
        f"/api/games/{game_id}/players/{robber_id}/robber-action",
        json={"target_player_id": target_id}
    )

    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Robber" in status["roles_completed"]


def test_non_robber_cannot_perform_robber_action(monkeypatch):
    """Only the Robber can call robber-action."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    # Players: Werewolf, Villager, Robber (Seer in center - will be simulated)
    roles = ["Werewolf", "Villager", "Robber", "Seer", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")
    role_map = _get_roles(game_id, player_ids)
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    robber_id = [pid for pid, role in role_map.items() if role == "Robber"][0]

    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    # Seer is in center - mark complete to advance to Robber
    client.post(f"/api/games/{game_id}/night-status/complete", json={"role": "Seer"})

    response = client.post(
        f"/api/games/{game_id}/players/{werewolf_id}/robber-action",
        json={"target_player_id": robber_id}
    )
    assert response.status_code in (400, 403)
