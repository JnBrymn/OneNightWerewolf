import sys
from pathlib import Path

# Add parent directory to path so we can import main
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_game_set():
    """Test creating a new game set."""
    response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    assert response.status_code == 201
    data = response.json()
    assert "game_set_id" in data
    assert data["num_players"] == 5
    assert len(data["selected_roles"]) == 8
    assert data["discussion_timer_seconds"] == 300


def test_create_game_set_invalid_role_count():
    """Test that creating a game set with wrong number of roles fails."""
    response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Villager"],  # Only 2 roles, need 8
        "discussion_timer_seconds": 300
    })
    assert response.status_code == 422  # Validation error


def test_create_game_set_invalid_role():
    """Test that creating a game set with invalid role fails."""
    response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "InvalidRole", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    assert response.status_code == 422  # Validation error


def test_get_game_set():
    """Test retrieving a game set by ID."""
    # First create a game set
    create_response = client.post("/api/game-sets", json={
        "num_players": 5,
        "selected_roles": ["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        "discussion_timer_seconds": 300
    })
    assert create_response.status_code == 201
    game_set_id = create_response.json()["game_set_id"]

    # Now get it
    get_response = client.get(f"/api/game-sets/{game_set_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["game_set_id"] == game_set_id
    assert data["num_players"] == 5


def test_get_nonexistent_game_set():
    """Test that getting a non-existent game set returns 404."""
    response = client.get("/api/game-sets/nonexistent-id")
    assert response.status_code == 404
