"""Service for night phase orchestration."""
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.center_card import CenterCard

# Official wake order from One Night Ultimate Werewolf
NIGHT_WAKE_ORDER = [
    "Doppelganger",
    "Werewolf",
    "Minion",
    "Mason",
    "Seer",
    "Robber",
    "Troublemaker",
    "Drunk",
    "Insomniac",
]


def _is_role_assigned_to_player(db: Session, game_id: str, role: str) -> bool:
    """Check if a role is assigned to any player (vs being in center cards). Uses initial_role so e.g. Insomniac is still 'assigned' even if that player was swapped."""
    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.initial_role == role
    ).first()
    return player_role is not None


def initialize_night_phase(db: Session, game_id: str) -> dict:
    """
    Initialize the night phase for a game.

    Sets the current role to the first role in active_roles (which includes all action roles
    from both players and center cards).

    Args:
        db: Database session
        game_id: ID of the game

    Returns:
        Dictionary with night phase status

    Raises:
        ValueError: If game not found or not in NIGHT state
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    # Use active_roles from game (includes all action roles from players + center cards)
    if not game.active_roles:
        # Fallback: calculate active roles if not set
        player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
        center_cards = db.query(CenterCard).filter(CenterCard.game_id == game_id).all()
        all_roles = set([pr.current_role for pr in player_roles] + [cc.role for cc in center_cards])
        active_roles = [role for role in NIGHT_WAKE_ORDER if role in all_roles]
        game.active_roles = active_roles
        db.commit()
        db.refresh(game)

    # Find the first role in active_roles
    current_role = game.active_roles[0] if game.active_roles else None

    # Set the current role in the game
    game.current_role_step = current_role
    
    # If this role is not assigned to a player (it's in center), start simulation
    if current_role and not _is_role_assigned_to_player(db, game_id, current_role):
        game.simulated_role_started_at = datetime.utcnow()
        game.simulated_role_duration_seconds = random.randint(15, 40)
    
    db.commit()
    db.refresh(game)

    return {
        "game_id": game_id,
        "current_role": current_role,
        "roles_completed": [],
        "roles_in_game": game.active_roles or [],
    }


def check_and_advance_simulated_role(db: Session, game_id: str) -> bool:
    """
    Check if a simulated role (center card role) has completed its time and advance it.
    
    Returns:
        True if a simulated role was advanced, False otherwise
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.state != GameState.NIGHT:
        return False
    
    if not game.current_role_step or not game.simulated_role_started_at:
        return False
    
    # Check if current role is assigned to a player (if so, it's not simulated)
    if _is_role_assigned_to_player(db, game_id, game.current_role_step):
        return False
    
    # Check if simulation time has elapsed
    elapsed = (datetime.utcnow() - game.simulated_role_started_at).total_seconds()
    if elapsed >= game.simulated_role_duration_seconds:
        # Auto-complete this simulated role
        mark_role_complete(db, game_id, game.current_role_step)
        return True
    
    return False


def get_night_status(db: Session, game_id: str) -> dict:
    """
    Get the current night phase status.

    Args:
        db: Database session
        game_id: ID of the game

    Returns:
        Dictionary with:
        - current_role: The role currently acting (or None if night is over)
        - roles_completed: List of roles that have completed their actions
        - roles_in_game: List of all active roles (from active_roles)

    Raises:
        ValueError: If game not found
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    # Check and advance simulated roles if needed
    check_and_advance_simulated_role(db, game_id)
    db.refresh(game)

    # Use active_roles from game (includes all action roles)
    active_roles = game.active_roles or []

    # Calculate completed roles by checking which roles come before current_role
    roles_completed = []
    if game.current_role_step:
        current_index = active_roles.index(game.current_role_step) if game.current_role_step in active_roles else -1
        if current_index > 0:
            roles_completed = active_roles[:current_index]
    else:
        # If current_role_step is None, all roles are complete
        roles_completed = active_roles

    return {
        "current_role": game.current_role_step,
        "roles_completed": roles_completed,
        "roles_in_game": active_roles,
    }


def mark_role_complete(db: Session, game_id: str, role: str) -> dict:
    """
    Mark a role as complete and advance to the next role in active_roles.

    Args:
        db: Database session
        game_id: ID of the game
        role: The role that completed its action

    Returns:
        Dictionary with:
        - status: "ok"
        - next_role: The next role to act (or None if night phase is over)
        - game_state: New game state if night phase ended

    Raises:
        ValueError: If game not found, role is not current, or game not in NIGHT state
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step != role:
        raise ValueError(
            f"Cannot mark role '{role}' complete - it is not the current role. "
            f"Current role is '{game.current_role_step}'"
        )

    # Use active_roles from game (includes all action roles from players + center cards)
    active_roles = game.active_roles or []
    
    # Find the next role in active_roles
    try:
        current_role_index = active_roles.index(role)
        next_role = active_roles[current_role_index + 1] if current_role_index + 1 < len(active_roles) else None
    except ValueError:
        # Role not in active_roles (shouldn't happen, but handle gracefully)
        next_role = None

    # Clear simulation fields
    game.simulated_role_started_at = None
    game.simulated_role_duration_seconds = None

    # Update game state
    if next_role:
        # Move to next role
        game.current_role_step = next_role
        
        # If next role is not assigned to a player (it's in center), start simulation
        if not _is_role_assigned_to_player(db, game_id, next_role):
            game.simulated_role_started_at = datetime.utcnow()
            game.simulated_role_duration_seconds = random.randint(15, 40)
        
        db.commit()
        db.refresh(game)

        return {
            "status": "ok",
            "next_role": next_role,
        }
    else:
        # Night phase is over, transition to day
        game.current_role_step = None
        game.state = GameState.DAY_DISCUSSION
        game.discussion_started_at = datetime.utcnow()
        db.commit()
        db.refresh(game)

        return {
            "status": "ok",
            "next_role": None,
            "game_state": GameState.DAY_DISCUSSION.value,
        }
