"""Tests for game service."""
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
from models.center_card import CenterCard
from services.game_service import start_game, get_player_role, _get_team_for_role


def test_start_game_creates_game(db: Session):
    """Test that start_game creates a Game instance."""
    # Create game set
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Add players
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    # Start the game
    game = start_game(db, game_set.game_set_id)

    # Verify game was created
    assert game is not None
    assert game.game_id is not None
    assert game.game_set_id == game_set.game_set_id
    assert game.game_number == 1
    assert game.state == GameState.NIGHT


def test_start_game_assigns_roles_to_players(db: Session):
    """Test that start_game assigns roles to all players."""
    # Create game set
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Add players
    players = []
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)
        players.append(player)

    db.commit()

    # Start the game
    game = start_game(db, game_set.game_set_id)

    # Verify all players have roles
    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game.game_id).all()
    assert len(player_roles) == 3

    # Verify each player has exactly one role
    player_ids = [pr.player_id for pr in player_roles]
    assert len(set(player_ids)) == 3  # All unique

    # Verify all roles are from the selected_roles
    assigned_roles = [pr.initial_role for pr in player_roles]
    for role in assigned_roles:
        assert role in game_set.selected_roles


def test_start_game_creates_center_cards(db: Session):
    """Test that start_game creates 3 center cards."""
    # Create game set
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Add players
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    # Start the game
    game = start_game(db, game_set.game_set_id)

    # Verify 3 center cards were created
    center_cards = db.query(CenterCard).filter(CenterCard.game_id == game.game_id).all()
    assert len(center_cards) == 3

    # Verify positions are correct
    positions = [cc.position for cc in center_cards]
    assert set(positions) == {"left", "center", "right"}

    # Verify all roles are from the selected_roles
    center_roles = [cc.role for cc in center_cards]
    for role in center_roles:
        assert role in game_set.selected_roles


def test_start_game_uses_all_roles(db: Session):
    """Test that start_game uses exactly all roles (no duplicates, none missing)."""
    # Create game set
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Add players
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    # Start the game
    game = start_game(db, game_set.game_set_id)

    # Get all assigned roles
    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game.game_id).all()
    center_cards = db.query(CenterCard).filter(CenterCard.game_id == game.game_id).all()

    assigned_roles = [pr.initial_role for pr in player_roles]
    center_roles = [cc.role for cc in center_cards]
    all_assigned = assigned_roles + center_roles

    # Verify all roles from game_set were used
    assert sorted(all_assigned) == sorted(game_set.selected_roles)


def test_start_game_randomizes_roles(db: Session):
    """Test that start_game randomizes role assignment (run multiple times)."""
    role_assignments = []

    for _ in range(5):  # Run 5 times
        # Create new game set for each iteration
        game_set = GameSet(
            num_players=3,
            selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
            discussion_timer_seconds=300
        )
        db.add(game_set)
        db.flush()

        # Add players
        for i in range(3):
            player = Player(player_name=f"Player{i+1}")
            db.add(player)
            db.flush()
            game_set.players.append(player)

        db.commit()

        # Start the game
        game = start_game(db, game_set.game_set_id)

        # Get first player's role
        player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game.game_id).all()
        first_role = player_roles[0].initial_role
        role_assignments.append(first_role)

    # With 6 different roles and 5 runs, we should see at least 2 different assignments
    # (This isn't a guarantee, but probability of all 5 being same is 1/6^4 = 0.077%)
    assert len(set(role_assignments)) >= 2, "Roles don't appear to be randomized"


def test_start_game_assigns_correct_teams(db: Session):
    """Test that start_game assigns correct teams to roles."""
    # Create game set with specific roles
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Minion", "Villager", "Tanner", "Seer", "Robber"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Add players
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    # Start the game
    game = start_game(db, game_set.game_set_id)

    # Check team assignments
    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game.game_id).all()

    for pr in player_roles:
        if pr.initial_role in ["Werewolf", "Minion"]:
            assert pr.team == "werewolf"
        elif pr.initial_role == "Tanner":
            assert pr.team == "tanner"
        else:
            assert pr.team == "village"


def test_start_game_raises_error_if_not_enough_players(db: Session):
    """Test that start_game raises error if not enough players joined."""
    # Create game set expecting 5 players
    game_set = GameSet(
        num_players=5,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner", "Hunter", "Mason"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Only add 3 players
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    # Should raise error
    with pytest.raises(ValueError, match="Not enough players"):
        start_game(db, game_set.game_set_id)


def test_start_game_raises_error_if_game_set_not_found(db: Session):
    """Test that start_game raises error if game set doesn't exist."""
    with pytest.raises(ValueError, match="not found"):
        start_game(db, "nonexistent-id")


def test_get_player_role_returns_correct_role(db: Session):
    """Test that get_player_role returns the correct PlayerRole."""
    # Create and start a game
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    # Add players
    players = []
    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)
        players.append(player)

    db.commit()

    game = start_game(db, game_set.game_set_id)

    # Get role for first player
    player_role = get_player_role(db, game.game_id, players[0].player_id)

    assert player_role is not None
    assert player_role.player_id == players[0].player_id
    assert player_role.game_id == game.game_id
    assert player_role.initial_role is not None


def test_get_player_role_raises_error_if_not_found(db: Session):
    """Test that get_player_role raises error if player not in game."""
    # Create and start a game
    game_set = GameSet(
        num_players=3,
        selected_roles=["Werewolf", "Villager", "Seer", "Robber", "Minion", "Tanner"],
        discussion_timer_seconds=300
    )
    db.add(game_set)
    db.flush()

    for i in range(3):
        player = Player(player_name=f"Player{i+1}")
        db.add(player)
        db.flush()
        game_set.players.append(player)

    db.commit()

    game = start_game(db, game_set.game_set_id)

    # Try to get role for non-existent player
    with pytest.raises(ValueError, match="not found"):
        get_player_role(db, game.game_id, "nonexistent-player-id")


def test_get_team_for_role():
    """Test _get_team_for_role helper function."""
    assert _get_team_for_role("Werewolf") == "werewolf"
    assert _get_team_for_role("Minion") == "werewolf"
    assert _get_team_for_role("Tanner") == "tanner"
    assert _get_team_for_role("Villager") == "village"
    assert _get_team_for_role("Seer") == "village"
    assert _get_team_for_role("Robber") == "village"
    assert _get_team_for_role("Hunter") == "village"
    assert _get_team_for_role("Mason") == "village"
