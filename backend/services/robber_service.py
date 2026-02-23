"""Service for Robber night actions."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.action import Action, ActionType
from services import night_service


def perform_robber_action(
    db: Session,
    game_id: str,
    player_id: str,
    target_player_id: str
) -> dict:
    """
    Perform Robber action: exchange cards with target player and view new role.

    Args:
        db: Database session
        game_id: ID of the game
        player_id: ID of the Robber player
        target_player_id: ID of the player to rob (exchange with)

    Returns:
        {"new_role": "...", "message": "You are now the ..."}

    Raises:
        ValueError: If validation fails
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    if game.current_role_step != "Robber":
        raise ValueError("Robber role is not currently active")

    robber_role = _get_player_role(db, game_id, player_id)
    if robber_role.initial_role != "Robber":
        raise ValueError("Player is not a Robber (only original Robber acts)")

    if robber_role.night_action_completed:
        raise ValueError("Robber has already performed their action")

    if target_player_id == player_id:
        raise ValueError("Robber cannot exchange with themselves")

    target_role = _get_player_role(db, game_id, target_player_id)
    new_role = target_role.current_role

    # Collect all original Robbers (by initial_role) before swap so we can check completion
    robbers_in_game = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.initial_role == "Robber"
    ).all()

    # Swap current_role between Robber and target
    robber_old_role = robber_role.current_role
    target_old_role = target_role.current_role
    robber_role.current_role = target_old_role
    target_role.current_role = robber_old_role

    # Create action record (for Robber: source=robber, target=victim; target_role = role robber received)
    action = Action(
        game_id=game_id,
        player_id=player_id,
        action_type=ActionType.SWAP_PLAYER_TO_PLAYER,
        source_id=player_id,
        target_id=target_player_id,
        source_role="Robber",
        target_role=new_role
    )
    db.add(action)

    robber_role.night_action_completed = True
    db.commit()

    # All players who were Robbers at start of step must have completed (we just completed for this one)
    if all(r.night_action_completed for r in robbers_in_game):
        night_service.mark_role_complete(db, game_id, "Robber")

    return {
        "new_role": new_role,
        "message": f"You are now the {new_role}."
    }


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not player_role:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return player_role
