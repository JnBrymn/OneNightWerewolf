"""End-to-end integration tests: full night with swapping/viewing, assert state from every player's perspective."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app
from services import game_service

client = TestClient(app)


def _no_shuffle(items):
    return None


def _start_game_6_players(roles):
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 6,
        "selected_roles": roles,
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]
    player_ids = []
    for i in range(6):
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


def _get_actions(game_id, player_id):
    r = client.get(f"/api/games/{game_id}/players/{player_id}/actions")
    assert r.status_code == 200
    return r.json()["actions"]


def test_full_night_swaps_and_views_correct_state_per_player(monkeypatch):
    """
    Run a full night with Werewolf, Seer, Robber, Troublemaker, Drunk, Insomniac.
    With no shuffle, role order is preserved; player order is from game_set.players.
    Resolve who has which role after start, then: Seer views Werewolf; Robber steals from Werewolf;
    Troublemaker swaps (ex-Werewolf) and Insomniac; Drunk swaps with center; Insomniac acks.
    Assert every player's current_role and actions from their perspective.
    """
    monkeypatch.setattr(game_service.random, "shuffle", _no_shuffle)

    roles = [
        "Werewolf", "Seer", "Robber", "Troublemaker", "Drunk", "Insomniac",
        "Villager", "Villager", "Villager"
    ]
    game_id, player_ids = _start_game_6_players(roles)
    role_map = _get_roles(game_id, player_ids)
    # Resolve who has which initial role (order depends on game_set.players, not join order)
    werewolf_id = next(pid for pid, r in role_map.items() if r == "Werewolf")
    seer_id = next(pid for pid, r in role_map.items() if r == "Seer")
    robber_id = next(pid for pid, r in role_map.items() if r == "Robber")
    troublemaker_id = next(pid for pid, r in role_map.items() if r == "Troublemaker")
    drunk_id = next(pid for pid, r in role_map.items() if r == "Drunk")
    insomniac_id = next(pid for pid, r in role_map.items() if r == "Insomniac")

    client.get(f"/api/games/{game_id}/night-status")

    # Werewolf
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    # Seer views Werewolf
    client.post(
        f"/api/games/{game_id}/players/{seer_id}/seer-action",
        json={"action_type": "view_player", "target_player_id": werewolf_id}
    )
    # Robber steals from Werewolf -> robber becomes Werewolf, werewolf becomes Robber
    client.post(
        f"/api/games/{game_id}/players/{robber_id}/robber-action",
        json={"target_player_id": werewolf_id}
    )
    # Troublemaker swaps (ex-Werewolf, now Robber) and Insomniac
    client.post(
        f"/api/games/{game_id}/players/{troublemaker_id}/troublemaker-action",
        json={"player1_id": werewolf_id, "player2_id": insomniac_id}
    )
    # Drunk swaps with center 0
    client.post(
        f"/api/games/{game_id}/players/{drunk_id}/drunk-action",
        json={"card_index": 0}
    )
    # Insomniac sees current card (now Robber after Troublemaker swap) and acknowledges
    info = client.get(f"/api/games/{game_id}/players/{insomniac_id}/night-info").json()
    assert info["current_role"] == "Robber"
    ack = client.post(f"/api/games/{game_id}/players/{insomniac_id}/acknowledge")
    assert ack.status_code == 200

    game = client.get(f"/api/games/{game_id}").json()
    assert game["state"] == "DAY_DISCUSSION"

    # ---- Final roles (from every player's perspective) ----
    roles_after = _get_roles(game_id, player_ids)
    # After chain: ex-Werewolf has Insomniac, Seer unchanged, Robber has Werewolf, Troublemaker unchanged, Drunk has Villager, Insomniac has Robber
    assert roles_after[werewolf_id] == "Insomniac"
    assert roles_after[seer_id] == "Seer"
    assert roles_after[robber_id] == "Werewolf"
    assert roles_after[troublemaker_id] == "Troublemaker"
    assert roles_after[drunk_id] == "Villager"
    assert roles_after[insomniac_id] == "Robber"

    # ---- Each player's actions (what they learned) ----
    actions_werewolf = _get_actions(game_id, werewolf_id)
    assert len(actions_werewolf) == 0

    actions_seer = _get_actions(game_id, seer_id)
    assert any("You viewed" in a["description"] and "Werewolf" in a["description"] for a in actions_seer)

    actions_robber = _get_actions(game_id, robber_id)
    assert any(a["action_type"] == "SWAP_PLAYER_TO_PLAYER" and "You are now: Werewolf" in a["description"] for a in actions_robber)

    actions_troublemaker = _get_actions(game_id, troublemaker_id)
    assert any(a["action_type"] == "SWAP_TWO_PLAYERS" and "You swapped" in a["description"] for a in actions_troublemaker)

    actions_drunk = _get_actions(game_id, drunk_id)
    assert any("don't know your new role" in a["description"] for a in actions_drunk)

    actions_insomniac = _get_actions(game_id, insomniac_id)
    assert any("Your current role is: Robber" in a["description"] for a in actions_insomniac)
