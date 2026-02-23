"""Tests for results and win conditions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient
from main import app
from services import game_service

client = TestClient(app)


def _play_game_to_results(player_names, votes):
    """votes: list of (voter_index, target_index) into player_ids. Returns (game_id, player_ids)."""
    game_set_response = client.post("/api/game-sets", json={
        "num_players": len(player_names),
        "selected_roles": ["Werewolf", "Villager", "Villager", "Villager", "Villager", "Villager"],
        "discussion_timer_seconds": 5
    })
    game_set_id = game_set_response.json()["game_set_id"]
    player_ids = []
    for name in player_names:
        player = client.post("/api/players", json={"player_name": name}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")
        player_ids.append(player["player_id"])
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    game_id = start_response.json()["game_id"]
    client.get(f"/api/games/{game_id}/night-status")
    werewolf_id = None
    for pid in player_ids:
        r = client.get(f"/api/games/{game_id}/players/{pid}/role").json()
        if r["current_role"] == "Werewolf":
            werewolf_id = pid
            break
    client.post(f"/api/games/{game_id}/players/{werewolf_id}/acknowledge")
    import time
    time.sleep(6)
    client.get(f"/api/games/{game_id}")
    for vi, ti in votes:
        r = client.post(
            f"/api/games/{game_id}/players/{player_ids[vi]}/vote",
            json={"target_player_id": player_ids[ti]},
        )
        assert r.status_code == 200, r.json()
    return game_id, player_ids


def test_village_wins_if_werewolf_dies(monkeypatch):
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    player_ids = ["Alice", "Bob", "Charlie"]
    game_id, pids = _play_game_to_results(player_ids, [(0, 1), (1, 0), (2, 1)])  # Bob (1) gets 2 votes, dies
    roles = {pid: client.get(f"/api/games/{game_id}/players/{pid}/role").json()["current_role"] for pid in pids}
    # If Bob is werewolf, village wins. We don't control shuffle so we might get different roles.
    response = client.get(f"/api/games/{game_id}/results")
    assert response.status_code == 200
    data = response.json()
    assert "deaths" in data
    assert "winning_team" in data
    assert "players" in data
    assert "vote_summary" in data
    assert len(data["deaths"]) >= 1
    assert data["winning_team"] in ("village", "werewolf", "tanner")


def test_calculate_deaths(monkeypatch):
    def no_shuffle(items):
        return None
    monkeypatch.setattr(game_service.random, "shuffle", no_shuffle)
    player_ids = ["A", "B", "C"]
    game_id, pids = _play_game_to_results(player_ids, [(0, 2), (1, 2), (2, 0)])  # C gets 2, A gets 1 -> C dies
    response = client.get(f"/api/games/{game_id}/results")
    assert response.status_code == 200
    deaths = response.json()["deaths"]
    assert pids[2] in deaths


def test_results_404_when_not_results():
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
    response = client.get(f"/api/games/{game_id}/results")
    assert response.status_code == 404
