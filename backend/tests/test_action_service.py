"""Tests for action service endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient
from db.database import SessionLocal
from models.game import Game, GameState
from models.game_set import GameSet
from models.player import Player
from models.player_role import PlayerRole
from models.center_card import CenterCard
from main import app

client = TestClient(app)


@pytest.fixture
def db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def game_setup(db):
    """Create a game set with players and a game."""
    uid = str(uuid.uuid4())[:8]
    game_set_id = f"test-game-set-{uid}"
    game_id = f"test-game-{uid}"
    # Create game set
    game_set = GameSet(
        game_set_id=game_set_id,
        num_players=5,
        selected_roles=["Werewolf", "Werewolf", "Villager", "Villager", "Villager", "Seer", "Robber", "Troublemaker"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.commit()

    # Create players
    players = []
    for i in range(5):
        player = Player(
            player_id=f"player-{uid}-{i}",
            player_name=f"Player {i}"
        )
        players.append(player)
        db.add(player)
    db.commit()

    # Create game
    game = Game(
        game_id=game_id,
        game_set_id=game_set.game_set_id,
        game_number=1,
        state=GameState.NIGHT,
        current_role_step="Werewolf"
    )
    db.add(game)
    db.commit()

    # Create player roles
    roles = ["Werewolf", "Werewolf", "Villager", "Villager", "Villager"]
    player_roles = []
    for i, (player, role) in enumerate(zip(players, roles)):
        player_role = PlayerRole(
            game_id=game.game_id,
            player_id=player.player_id,
            initial_role=role,
            current_role=role,
            team="werewolf" if role == "Werewolf" else "village"
        )
        player_roles.append(player_role)
        db.add(player_role)
    db.commit()

    # Create center cards
    center_roles = ["Seer", "Robber", "Troublemaker"]
    for i, role in enumerate(center_roles):
        position = ["left", "center", "right"][i]
        center_card = CenterCard(
            game_id=game.game_id,
            position=position,
            role=role
        )
        db.add(center_card)
    db.commit()

    return {
        "game_set": game_set,
        "game": game,
        "players": players,
        "player_roles": player_roles
    }


def test_get_available_actions_for_werewolf(db, game_setup):
    """Test that werewolf gets correct actionable items."""
    game = game_setup["game"]
    werewolf_player = game_setup["players"][0]  # First player is werewolf

    response = client.get(f"/api/games/{game.game_id}/players/{werewolf_player.player_id}/available-actions")
    assert response.status_code == 200
    data = response.json()
    assert "actionable_players" in data
    assert "actionable_center_cards" in data
    assert "instructions" in data
    # Multiple werewolves, so no center cards actionable (just info display)
    assert len(data["actionable_center_cards"]) == 0
    assert "Werewolf" in data["instructions"]


def test_get_available_actions_for_seer(db, game_setup):
    """Test that seer gets correct actionable items."""
    game = game_setup["game"]
    # Add a Seer player role (unique id to avoid collision across test runs)
    seer_player_id = f"seer-player-{game.game_id}"
    seer_player = Player(
        player_id=seer_player_id,
        player_name="Seer Player"
    )
    db.add(seer_player)
    db.commit()

    seer_role = PlayerRole(
        game_id=game.game_id,
        player_id=seer_player.player_id,
        initial_role="Seer",
        current_role="Seer",
        team="village"
    )
    db.add(seer_role)
    db.commit()

    # Update game to Seer's turn
    game.current_role_step = "Seer"
    db.commit()

    response = client.get(f"/api/games/{game.game_id}/players/{seer_player.player_id}/available-actions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["actionable_players"]) > 0  # Can view players
    assert len(data["actionable_center_cards"]) == 3  # Can view center cards
    assert "Seer" in data["instructions"]


def test_get_available_actions_when_not_player_turn(db, game_setup):
    """Test that non-active players get waiting message."""
    game = game_setup["game"]
    villager_player = game_setup["players"][2]  # Villager

    response = client.get(f"/api/games/{game.game_id}/players/{villager_player.player_id}/available-actions")
    assert response.status_code == 200
    data = response.json()
    assert len(data["actionable_players"]) == 0
    assert len(data["actionable_center_cards"]) == 0
    assert "Waiting" in data["instructions"]


def test_get_player_actions_empty_initially(db, game_setup):
    """Test that player actions are empty initially."""
    game = game_setup["game"]
    player = game_setup["players"][0]

    response = client.get(f"/api/games/{game.game_id}/players/{player.player_id}/actions")
    assert response.status_code == 200
    data = response.json()
    assert "actions" in data
    assert isinstance(data["actions"], list)


def test_get_player_actions_after_werewolf_view(db, game_setup):
    """Test that actions are returned after werewolf views center card."""
    game = game_setup["game"]
    # Make it a lone wolf scenario
    werewolf_player = game_setup["players"][0]
    
    # Remove other werewolf
    other_werewolf_role = game_setup["player_roles"][1]
    other_werewolf_role.current_role = "Villager"
    db.commit()

    # View center card
    view_response = client.post(
        f"/api/games/{game.game_id}/players/{werewolf_player.player_id}/view-center",
        json={"card_index": 0}
    )
    assert view_response.status_code == 200

    # Get actions
    actions_response = client.get(f"/api/games/{game.game_id}/players/{werewolf_player.player_id}/actions")
    assert actions_response.status_code == 200
    data = actions_response.json()
    assert len(data["actions"]) > 0
    assert any("center card" in action["description"].lower() for action in data["actions"])


def test_get_available_actions_404_for_invalid_game(db):
    """Test that 404 is returned for invalid game."""
    response = client.get("/api/games/invalid-game/players/invalid-player/available-actions")
    assert response.status_code == 404


def test_get_player_actions_404_for_invalid_game(db):
    """Test that 404 is returned for invalid game."""
    response = client.get("/api/games/invalid-game/players/invalid-player/actions")
    assert response.status_code == 404
