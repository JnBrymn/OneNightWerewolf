"""Tests for voting phase."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app
from services import game_service

client = TestClient(app)


def _game_to_day_voting():
    """Get a game in DAY_VOTING (short discussion timer, then sleep)."""
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Insomniac", "Villager", "Villager", "Villager", "Villager"],
        "discussion_timer_seconds": 5
    })
    game_set_id = game_set_response.json()["game_set_id"]
    player_ids = []
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"P{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")
        player_ids.append(player["player_id"])
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    game_id = start_response.json()["game_id"]
    client.get(f"/api/games/{game_id}/night-status")
    role_map = {pid: client.get(f"/api/games/{game_id}/players/{pid}/role").json()["current_role"] for pid in player_ids}
    werewolf_id = next(pid for pid, r in role_map.items() if r == "Werewolf")
    insomniac_id = next(pid for pid, r in role_map.items() if r == "Insomniac")
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    client.get(f"/api/games/{game_id}/players/{insomniac_id}/night-info")
    client.post(f"/api/games/{game_id}/players/{insomniac_id}/acknowledge")
    import time
    time.sleep(6)
    client.get(f"/api/games/{game_id}")
    game = client.get(f"/api/games/{game_id}").json()
    assert game["state"] == "DAY_VOTING"
    return game_id, player_ids


def test_player_can_vote(monkeypatch):
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, player_ids = _game_to_day_voting()
    voter_id = player_ids[0]
    target_id = player_ids[1]
    response = client.post(
        f"/api/games/{game_id}/players/{voter_id}/vote",
        json={"target_player_id": target_id},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "vote_recorded"


def test_player_cannot_vote_twice(monkeypatch):
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, player_ids = _game_to_day_voting()
    voter_id = player_ids[0]
    target_id = player_ids[1]
    client.post(
        f"/api/games/{game_id}/players/{voter_id}/vote",
        json={"target_player_id": target_id},
    )
    response = client.post(
        f"/api/games/{game_id}/players/{voter_id}/vote",
        json={"target_player_id": player_ids[2]},
    )
    assert response.status_code == 400


def test_get_vote_status(monkeypatch):
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, player_ids = _game_to_day_voting()
    response = client.get(f"/api/games/{game_id}/votes")
    assert response.status_code == 200
    data = response.json()
    assert "votes" in data
    assert "votes_cast" in data
    assert "total_players" in data
    assert data["total_players"] == 3
    assert data["votes_cast"] == 0


def test_auto_transition_after_all_votes(monkeypatch):
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, player_ids = _game_to_day_voting()
    # Vote: 0 -> 1, 1 -> 0, 2 -> 0 (so player 0 gets 2 votes and dies)
    client.post(f"/api/games/{game_id}/players/{player_ids[0]}/vote", json={"target_player_id": player_ids[1]})
    client.post(f"/api/games/{game_id}/players/{player_ids[1]}/vote", json={"target_player_id": player_ids[0]})
    client.post(f"/api/games/{game_id}/players/{player_ids[2]}/vote", json={"target_player_id": player_ids[0]})
    response = client.get(f"/api/games/{game_id}")
    assert response.json()["state"] == "RESULTS"
