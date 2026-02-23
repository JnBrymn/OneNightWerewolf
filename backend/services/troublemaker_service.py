"""Service for Troublemaker night actions: swap two other players' cards (no looking)."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.action import Action, ActionType
from services import night_service


def perform_troublemaker_action(
    db: Session,
    game_id: str,
    player_id: str,
    player1_id: str,
    player2_id: str
) -> dict:
    """
    Troublemaker swaps two other players' cards without looking.

    Args:
        db: Database session
        game_id: ID of the game
        player_id: ID of the Troublemaker
        player1_id: First player whose card is swapped
        player2_id: Second player whose card is swapped

    Returns:
        {"message": "You swapped [name1] and [name2]."}
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    if game.current_role_step != "Troublemaker":
        raise ValueError("Troublemaker role is not currently active")

    troublemaker_role = _get_player_role(db, game_id, player_id)
    if troublemaker_role.initial_role != "Troublemaker":
        raise ValueError("Player is not the Troublemaker (only original Troublemaker acts)")

    if troublemaker_role.night_action_completed:
        raise ValueError("Troublemaker has already performed their action")

    if player1_id == player2_id:
        raise ValueError("Must choose two different players")
    if player1_id == player_id or player2_id == player_id:
        raise ValueError("Troublemaker cannot swap their own card; choose two other players")

    p1_role = _get_player_role(db, game_id, player1_id)
    p2_role = _get_player_role(db, game_id, player2_id)

    # Swap only current_role (cards). Completion stays with the player so only original role-holders act later.
    r1, r2 = p1_role.current_role, p2_role.current_role
    p1_role.current_role = r2
    p2_role.current_role = r1

    action = Action(
        game_id=game_id,
        player_id=player_id,
        action_type=ActionType.SWAP_TWO_PLAYERS,
        source_id=player1_id,
        target_id=player2_id,
        source_role=r1,
        target_role=r2
    )
    db.add(action)

    troublemaker_role.night_action_completed = True
    db.commit()

    _complete_troublemaker_role_if_ready(db, game_id)

    return {"message": f"You swapped the cards of the two players."}


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    pr = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not pr:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return pr


def _complete_troublemaker_role_if_ready(db: Session, game_id: str) -> None:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Troublemaker":
        return
    roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.initial_role == "Troublemaker"
    ).all()
    if roles and all(r.night_action_completed for r in roles):
        night_service.mark_role_complete(db, game_id, "Troublemaker")
