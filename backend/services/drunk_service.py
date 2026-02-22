"""Service for Drunk night actions: swap with a center card (no looking)."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.center_card import CenterCard
from models.action import Action, ActionType
from services import night_service

CENTER_POSITIONS = ["left", "center", "right"]


def perform_drunk_action(
    db: Session,
    game_id: str,
    player_id: str,
    card_index: int
) -> dict:
    """
    Drunk exchanges their card with a center card; they do not look at the new card.

    Args:
        db: Database session
        game_id: ID of the game
        player_id: ID of the Drunk
        card_index: 0, 1, or 2 for left/center/right

    Returns:
        {"message": "You exchanged your card with center card [position]. You don't know your new role."}
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    if game.current_role_step != "Drunk":
        raise ValueError("Drunk role is not currently active")

    drunk_role = _get_player_role(db, game_id, player_id)
    if drunk_role.current_role != "Drunk":
        raise ValueError("Player is not the Drunk")

    if drunk_role.night_action_completed:
        raise ValueError("Drunk has already performed their action")

    if card_index not in (0, 1, 2):
        raise ValueError("card_index must be 0, 1, or 2")

    position = CENTER_POSITIONS[card_index]
    center_card = db.query(CenterCard).filter(
        CenterCard.game_id == game_id,
        CenterCard.position == position
    ).first()
    if not center_card:
        raise ValueError(f"Center card at index {card_index} not found")

    drunk_old = drunk_role.current_role
    center_old = center_card.role

    action = Action(
        game_id=game_id,
        player_id=player_id,
        action_type=ActionType.SWAP_PLAYER_TO_CENTER,
        source_id=player_id,
        target_id=str(card_index),
        source_role=drunk_old,
        target_role=center_old
    )
    db.add(action)

    drunk_role.night_action_completed = True
    _complete_drunk_role_if_ready(db, game_id)  # Must run while player still has current_role Drunk

    drunk_role.current_role = center_old
    center_card.role = drunk_old
    db.commit()

    card_label = ["Left", "Center", "Right"][card_index]
    return {"message": f"You exchanged your card with center card {card_label}. You don't know your new role."}


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    pr = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not pr:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return pr


def _complete_drunk_role_if_ready(db: Session, game_id: str) -> None:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Drunk":
        return
    roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.current_role == "Drunk"
    ).all()
    if roles and all(r.night_action_completed for r in roles):
        night_service.mark_role_complete(db, game_id, "Drunk")
