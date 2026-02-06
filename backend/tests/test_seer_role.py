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


def test_seer_can_view_one_player(monkeypatch):
    """Test that Seer can view one player's card."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Seer", "Werewolf", "Villager", "Robber", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]

    # Advance to Seer phase (complete Werewolf first)
    werewolf_id = target_id
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    # Seer views a player
    response = client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )
    assert response.status_code == 200
    assert "role" in response.json()
    assert response.json()["role"] == "Werewolf"

    # Check that Seer role is complete
    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Seer" in status["roles_completed"]


def test_seer_can_view_two_center_cards(monkeypatch):
    """Test that Seer can view two center cards."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Seer", "Werewolf", "Villager", "Robber", "Troublemaker", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    # Advance to Seer phase (complete Werewolf first)
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    # Seer views two center cards
    response = client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_center", "card_indices": [0, 1]}
    )
    assert response.status_code == 200
    assert "roles" in response.json()
    assert len(response.json()["roles"]) == 2

    # Check that Seer role is complete
    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Seer" in status["roles_completed"]


def test_seer_cannot_view_three_center_cards(monkeypatch):
    """Test that Seer cannot view three center cards."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Seer", "Werewolf", "Villager", "Robber", "Troublemaker", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    # Advance to Seer phase
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    # Seer tries to view three center cards (should fail - validation error)
    response = client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_center", "card_indices": [0, 1, 2]}
    )
    assert response.status_code == 422  # Validation error from Pydantic


def test_seer_action_marks_role_complete(monkeypatch):
    """Test that Seer action marks the role as complete."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Seer", "Werewolf", "Villager", "Robber", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]

    # Advance to Seer phase
    werewolf_id = target_id
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    # Perform seer action
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )

    # Check that Seer is complete
    status = client.get(f"/api/games/{game_id}/night-status").json()
    assert "Seer" in status["roles_completed"]


def test_non_seer_cannot_perform_seer_action(monkeypatch):
    """Test that a non-Seer cannot perform Seer action."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Werewolf", "Villager", "Seer", "Robber", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    target_id = [pid for pid, role in role_map.items() if role == "Villager"][0]

    # Werewolf tries to perform Seer action (should fail)
    response = client.post(
        f"/api/games/{game_id}/players/{werewolf_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": target_id}
    )
    assert response.status_code == 403 or response.status_code == 400


def test_seer_cannot_view_self(monkeypatch):
    """Test that Seer cannot view their own card."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Seer", "Werewolf", "Villager", "Robber", "Villager", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    # Advance to Seer phase
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    # Seer tries to view themselves (should fail)
    response = client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": seer_id}
    )
    assert response.status_code == 400


def test_seer_viewing_two_center_cards_creates_two_actions(monkeypatch):
    """Test that viewing two center cards creates two separate action records."""
    def no_shuffle(items):
        return None

    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)

    roles = ["Seer", "Werewolf", "Villager", "Robber", "Troublemaker", "Villager"]
    game_id, player_ids = _start_game_with_roles(roles)

    client.get(f"/api/games/{game_id}/night-status")

    role_map = _get_roles(game_id, player_ids)
    seer_id = [pid for pid, role in role_map.items() if role == "Seer"][0]

    # Advance to Seer phase
    werewolf_id = [pid for pid, role in role_map.items() if role == "Werewolf"][0]
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")

    # Seer views two center cards
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_center", "card_indices": [0, 1]}
    )

    # Check that two actions were created
    actions_response = client.get(f"/api/games/{game_id}/players/{seer_id}/actions")
    assert actions_response.status_code == 200
    actions = actions_response.json()["actions"]
    
    # Should have two VIEW_CARD actions for center cards
    center_card_actions = [a for a in actions if a["action_type"] == "VIEW_CARD" and "center card" in a["description"].lower()]
    assert len(center_card_actions) == 2
