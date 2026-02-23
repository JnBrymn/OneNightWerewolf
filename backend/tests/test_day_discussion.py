"""Tests for Day Discussion phase (timer and transition to voting)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app
from services import game_service

client = TestClient(app)


def _start_game_to_day_discussion(discussion_timer_seconds=300):
    """Start a game and advance to DAY_DISCUSSION (Werewolf + Insomniac only for speed)."""
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Insomniac", "Villager", "Villager", "Villager", "Villager"],
        "discussion_timer_seconds": discussion_timer_seconds
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
    game = client.get(f"/api/games/{game_id}").json()
    assert game["state"] == "DAY_DISCUSSION"
    return game_id, player_ids


def test_discussion_timer_starts(monkeypatch):
    """Discussion status returns positive time remaining when in DAY_DISCUSSION."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, _ = _start_game_to_day_discussion()
    response = client.get(f"/api/games/{game_id}/discussion-status")
    assert response.status_code == 200
    data = response.json()
    assert data["time_remaining_seconds"] > 0
    assert data["time_remaining_seconds"] <= 300
    assert data["state"] == "DAY_DISCUSSION"


def test_discussion_timer_countdown(monkeypatch):
    """Time remaining decreases over time."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, _ = _start_game_to_day_discussion()
    r1 = client.get(f"/api/games/{game_id}/discussion-status")
    time1 = r1.json()["time_remaining_seconds"]
    time.sleep(2)
    r2 = client.get(f"/api/games/{game_id}/discussion-status")
    time2 = r2.json()["time_remaining_seconds"]
    assert time2 <= time1
    assert time1 - time2 >= 1


def test_auto_transition_to_voting(monkeypatch):
    """When discussion timer expires, game transitions to DAY_VOTING."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, _ = _start_game_to_day_discussion(discussion_timer_seconds=5)
    time.sleep(6)
    response = client.get(f"/api/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["state"] == "DAY_VOTING"


def test_discussion_status_404_when_not_in_discussion():
    """discussion-status returns 404 when game is not in DAY_DISCUSSION."""
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Villager", "Villager", "Villager", "Villager", "Villager"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"P{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    game_id = start_response.json()["game_id"]
    response = client.get(f"/api/games/{game_id}/discussion-status")
    assert response.status_code == 404


def test_vote_now_majority_transitions_to_voting(monkeypatch):
    """When majority of players post vote-now, game transitions to DAY_VOTING."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, player_ids = _start_game_to_day_discussion()
    # 3 players: majority = 2
    r1 = client.post(f"/api/games/{game_id}/players/{player_ids[0]}/vote-now")
    assert r1.status_code == 200
    assert r1.json()["state"] == "DAY_DISCUSSION"
    r2 = client.post(f"/api/games/{game_id}/players/{player_ids[1]}/vote-now")
    assert r2.status_code == 200
    assert r2.json()["state"] == "DAY_VOTING"
    game = client.get(f"/api/games/{game_id}").json()
    assert game["state"] == "DAY_VOTING"


def test_discussion_status_includes_vote_now_when_player_id_given(monkeypatch):
    """discussion-status with player_id returns vote_now fields."""
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    game_id, player_ids = _start_game_to_day_discussion()
    res = client.get(f"/api/games/{game_id}/discussion-status?player_id={player_ids[0]}")
    assert res.status_code == 200
    data = res.json()
    assert "vote_now_count" in data
    assert "total_players" in data
    assert "vote_now_majority" in data
    assert data["current_player_voted_now"] is False
    client.post(f"/api/games/{game_id}/players/{player_ids[0]}/vote-now")
    res2 = client.get(f"/api/games/{game_id}/discussion-status?player_id={player_ids[0]}")
    assert res2.json()["current_player_voted_now"] is True
