import sys
from pathlib import Path

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_player():
    """Test creating a new player."""
    response = client.post("/api/players", json={
        "player_name": "Alice",
        "avatar_url": "https://example.com/avatar.jpg"
    })
    assert response.status_code == 201
    data = response.json()
    assert "player_id" in data
    assert data["player_name"] == "Alice"
    assert data["avatar_url"] == "https://example.com/avatar.jpg"


def test_create_player_without_avatar():
    """Test creating a player without avatar URL."""
    response = client.post("/api/players", json={
        "player_name": "Bob"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["player_name"] == "Bob"
    assert data["avatar_url"] is None


def test_join_game_set():
    """Test a player joining a game set."""
    # First create a game set
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Create a player
    player_response = client.post("/api/players", json={"player_name": "Alice"})
    player_id = player_response.json()["player_id"]

    # Join the game set
    join_response = client.post(f"/api/game-sets/{game_set_id}/players/{player_id}/join")
    assert join_response.status_code == 200
    assert join_response.json()["status"] == "joined"


def test_list_players_in_game_set():
    """Test listing all players in a game set."""
    # Create game set
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Create and join two players
    player1 = client.post("/api/players", json={"player_name": "Alice"}).json()
    player2 = client.post("/api/players", json={"player_name": "Bob"}).json()

    client.post(f"/api/game-sets/{game_set_id}/players/{player1['player_id']}/join")
    client.post(f"/api/game-sets/{game_set_id}/players/{player2['player_id']}/join")

    # List players
    list_response = client.get(f"/api/game-sets/{game_set_id}/players")
    assert list_response.status_code == 200
    data = list_response.json()
    assert len(data["players"]) == 2
    assert data["players"][0]["player_name"] in ["Alice", "Bob"]
    assert data["players"][1]["player_name"] in ["Alice", "Bob"]


def test_cannot_join_game_set_twice():
    """Test that a player cannot join the same game set twice."""
    # Create game set and player
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    player_response = client.post("/api/players", json={"player_name": "Alice"})
    player_id = player_response.json()["player_id"]

    # Join once (should succeed)
    join_response1 = client.post(f"/api/game-sets/{game_set_id}/players/{player_id}/join")
    assert join_response1.status_code == 200

    # Try to join again (should fail)
    join_response2 = client.post(f"/api/game-sets/{game_set_id}/players/{player_id}/join")
    assert join_response2.status_code == 400


def test_cannot_join_full_game_set():
    """Test that a player cannot join a full game set."""
    # Create game set for 3 players
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Seer", "Robber"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Create and join 3 players (fills the game)
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"Player{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")

    # Try to join a 4th player (should fail)
    player4 = client.post("/api/players", json={"player_name": "Player4"}).json()
    join_response = client.post(f"/api/game-sets/{game_set_id}/players/{player4['player_id']}/join")
    assert join_response.status_code == 400
    assert "full" in join_response.json()["detail"].lower()


def test_cannot_start_game_without_enough_players():
    """Test that game cannot start without enough players."""
    # Create game set needing 5 players
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Join only 2 players
    for i in range(2):
        player = client.post("/api/players", json={"player_name": f"Player{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")

    # Try to start game (should fail)
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    assert start_response.status_code == 400
    assert "not enough players" in start_response.json()["detail"].lower()


def test_can_start_game_with_enough_players():
    """Test that game can start when enough players have joined."""
    # Create game set needing 3 players
    game_set_response = client.post("/api/game-sets", json={
        "num_players": 3,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Seer", "Robber"],
        "discussion_timer_seconds": 300
    })
    game_set_id = game_set_response.json()["game_set_id"]

    # Join exactly 3 players
    for i in range(3):
        player = client.post("/api/players", json={"player_name": f"Player{i}"}).json()
        client.post(f"/api/game-sets/{game_set_id}/players/{player['player_id']}/join")

    # Start game (should succeed)
    start_response = client.post(f"/api/game-sets/{game_set_id}/start")
    assert start_response.status_code == 201
    data = start_response.json()
    assert "game_id" in data
    assert data["state"] == "NIGHT"
    assert data["game_number"] == 1
