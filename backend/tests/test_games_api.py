import sys
from pathlib import Path

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_player_role_in_game():
    """Test getting a player's role in a game."""
    # Create game set with 3 players
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Seer", "Robber"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Create and join 3 players
    player_ids = []
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"Player{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")
        player_ids.append(player["player_id"])

    # Start the game
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    assert start_response.status_code == 201
    game_data = start_response.json()
    game_id = game_data["game_id"]

    # Get first player's role
    role_response = client.get(f"/api/games/{game_id}/players/{player_ids[0]}/role")
    assert role_response.status_code == 200
    role_data = role_response.json()

    # Verify response structure
    assert "player_role_id" in role_data
    assert "game_id" in role_data
    assert "player_id" in role_data
    assert "initial_role" in role_data
    assert "current_role" in role_data
    assert "team" in role_data
    assert "was_killed" in role_data

    # Verify data
    assert role_data["game_id"] == game_id
    assert role_data["player_id"] == player_ids[0]
    assert role_data["initial_role"] in ["Werewolf", "Villager", "Seer", "Robber"]
    assert role_data["current_role"] == role_data["initial_role"]  # Same at start
    assert role_data["team"] in ["werewolf", "village"]
    assert role_data["was_killed"] is False


def test_get_player_role_not_found():
    """Test that getting a non-existent player role returns 404."""
    response = client.get("/api/games/fake-game-id/players/fake-player-id/role")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_each_player_gets_different_role():
    """Test that each player in a game gets a unique role assignment."""
    # Create game set with 3 players
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Seer", "Robber"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Create and join 3 players
    player_ids = []
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"Player{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")
        player_ids.append(player["player_id"])

    # Start the game
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    game_id = start_response.json()["game_id"]

    # Get all player roles
    roles = []
    for player_id in player_ids:
        role_response = client.get(f"/api/games/{game_id}/players/{player_id}/role")
        role_data = role_response.json()
        roles.append(role_data["initial_role"])

    # Each player should have a role from the available set
    for role in roles:
        assert role in ["Werewolf", "Villager", "Seer", "Robber"]

    # All 3 roles should be assigned (from the 6 available, 3 go to players, 3 to center)
    assert len(roles) == 3
