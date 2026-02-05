"""Tests for night phase orchestration."""
import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.game_set import GameSet
from models.player import Player
from models.player_role import PlayerRole
from services.game_service import start_game
from services.night_service import (
    initialize_night_phase,
    get_night_status,
    mark_role_complete,
    NIGHT_WAKE_ORDER
)


@pytest.fixture
def sample_game(db: Session):
    """Create a sample game with players and roles for testing."""
    # Create game set
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Seer", "Robber", "Villager", "Villager", "Villager"],
        discussion_timer_seconds=600
    )
    db.add(game_set)
    db.flush()

    # Create players
    players = []
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        players.append(player)

        # Join game set
        game_set.players.append(player)

    db.commit()
    db.refresh(game_set)

    # Start game
    game = start_game(db, game_set.game_set_id)

    return game


def test_get_night_status(db: Session, sample_game: Game):
    """Test getting the current night phase status."""
    # Initialize night phase
    initialize_night_phase(db, sample_game.game_id)

    # Get night status
    status = get_night_status(db, sample_game.game_id)

    assert status is not None
    assert "current_role" in status
    assert "roles_completed" in status
    assert "roles_in_game" in status
    assert isinstance(status["roles_completed"], list)
    assert len(status["roles_completed"]) == 0  # Nothing completed yet


def test_night_phase_wake_order(db: Session, sample_game: Game):
    """Test that night phase follows correct wake order."""
    # Initialize night phase
    initialize_night_phase(db, sample_game.game_id)

    # Get initial status
    status = get_night_status(db, sample_game.game_id)

    # Should start with first role in wake order that's in the game
    assert status["current_role"] in status["roles_in_game"]

    # The first role should be from the wake order
    # Find the first role in wake order that's actually in the game
    expected_first_role = None
    for role in NIGHT_WAKE_ORDER:
        if role in status["roles_in_game"]:
            expected_first_role = role
            break

    assert status["current_role"] == expected_first_role


def test_mark_role_complete_advances_to_next(db: Session, sample_game: Game):
    """Test that marking a role complete advances to the next role."""
    # Initialize night phase
    initialize_night_phase(db, sample_game.game_id)

    # Get initial status
    initial_status = get_night_status(db, sample_game.game_id)
    current_role = initial_status["current_role"]

    # Mark current role as complete
    result = mark_role_complete(db, sample_game.game_id, current_role)

    assert result["status"] == "ok"
    assert "next_role" in result or "game_state" in result  # Either next role or game ended

    # Get updated status
    updated_status = get_night_status(db, sample_game.game_id)

    # Current role should have changed (unless it was the last role)
    assert current_role in updated_status["roles_completed"]

    # If there are more roles, current_role should be different
    if result.get("next_role"):
        assert updated_status["current_role"] != current_role
        assert updated_status["current_role"] == result["next_role"]


def test_cannot_mark_role_complete_out_of_order(db: Session, sample_game: Game):
    """Test that you cannot mark a role complete if it's not the current role."""
    # Initialize night phase
    initialize_night_phase(db, sample_game.game_id)

    # Get initial status
    status = get_night_status(db, sample_game.game_id)
    current_role = status["current_role"]

    # Try to mark a different role as complete
    roles_in_game = status["roles_in_game"]
    other_role = None
    for role in roles_in_game:
        if role != current_role:
            other_role = role
            break

    if other_role:
        # Should raise an error
        with pytest.raises(ValueError, match="not the current role"):
            mark_role_complete(db, sample_game.game_id, other_role)


def test_night_phase_ends_after_all_roles(db: Session, sample_game: Game):
    """Test that night phase transitions to DAY_DISCUSSION after all roles complete."""
    # Initialize night phase
    initialize_night_phase(db, sample_game.game_id)

    # Get all roles in game
    status = get_night_status(db, sample_game.game_id)
    roles_in_game = status["roles_in_game"]

    # Complete all roles in sequence
    for _ in range(len(roles_in_game)):
        status = get_night_status(db, sample_game.game_id)
        current_role = status["current_role"]

        if current_role:  # If there's still a role to complete
            mark_role_complete(db, sample_game.game_id, current_role)

    # Check game state
    db.refresh(sample_game)
    assert sample_game.state == GameState.DAY_DISCUSSION
    assert sample_game.current_role_step is None


def test_roles_not_in_game_are_skipped(db: Session):
    """Test that roles not assigned to any player are skipped in wake order."""
    # Create a game with specific roles (no Robber)
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Seer", "Villager", "Villager", "Villager", "Villager"],
        discussion_timer_seconds=600
    )
    db.add(game_set)
    db.flush()

    # Create and add players
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    # Start game
    game = start_game(db, game_set.game_set_id)

    # Initialize night phase
    initialize_night_phase(db, game.game_id)

    # Get status
    status = get_night_status(db, game.game_id)

    # Robber should not be in roles_in_game
    assert "Robber" not in status["roles_in_game"]

    # Werewolf and Seer should be in roles_in_game
    # (They might be in center, but we still call them in wake order)
    # Actually, let's check that we only include roles that players have
    # For now, the service should track which roles are actually assigned
