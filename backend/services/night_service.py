"""Service for night phase orchestration."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole

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


def initialize_night_phase(db: Session, game_id: str) -> dict:
    """
    Initialize the night phase for a game.

    Sets the current role to the first role in the wake order that exists in the game.

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

    # Get all roles assigned to players in this game
    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    roles_in_game = set([pr.current_role for pr in player_roles])

    # Find the first role in wake order that's actually in the game
    current_role = None
    for role in NIGHT_WAKE_ORDER:
        if role in roles_in_game:
            current_role = role
            break

    # Set the current role in the game
    game.current_role_step = current_role
    db.commit()
    db.refresh(game)

    return {
        "game_id": game_id,
        "current_role": current_role,
        "roles_completed": [],
        "roles_in_game": list(roles_in_game),
    }


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
        - roles_in_game: List of all roles assigned to players

    Raises:
        ValueError: If game not found
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    # Get all roles in the game
    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    roles_in_game = set([pr.current_role for pr in player_roles])

    # Calculate completed roles by checking which roles come before current_role
    roles_completed = []
    if game.current_role_step:
        for role in NIGHT_WAKE_ORDER:
            if role == game.current_role_step:
                break
            if role in roles_in_game:
                roles_completed.append(role)
    else:
        # If current_role_step is None, all roles are complete
        roles_completed = [role for role in NIGHT_WAKE_ORDER if role in roles_in_game]

    return {
        "current_role": game.current_role_step,
        "roles_completed": roles_completed,
        "roles_in_game": list(roles_in_game),
    }


def mark_role_complete(db: Session, game_id: str, role: str) -> dict:
    """
    Mark a role as complete and advance to the next role in the wake order.

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

    # Get all roles in the game
    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    roles_in_game = set([pr.current_role for pr in player_roles])

    # Find the next role in wake order
    current_role_index = NIGHT_WAKE_ORDER.index(role)
    next_role = None

    for i in range(current_role_index + 1, len(NIGHT_WAKE_ORDER)):
        candidate_role = NIGHT_WAKE_ORDER[i]
        if candidate_role in roles_in_game:
            next_role = candidate_role
            break

    # Update game state
    if next_role:
        # Move to next role
        game.current_role_step = next_role
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
        db.commit()
        db.refresh(game)

        return {
            "status": "ok",
            "next_role": None,
            "game_state": GameState.DAY_DISCUSSION.value,
        }
