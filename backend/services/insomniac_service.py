"""Service for Insomniac night actions: view own current card at end of night, then acknowledge."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.action import Action, ActionType
from services import night_service


def get_night_info(db: Session, game_id: str, player_id: str) -> dict:
    """Return Insomniac's current role (after all night swaps). Used by GET night-info dispatcher."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")
    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.current_role != "Insomniac":
        raise ValueError("Player is not the Insomniac")
    if game.current_role_step != "Insomniac":
        raise ValueError("Insomniac role is not currently active")

    return {
        "role": "Insomniac",
        "current_role": player_role.current_role,
        "night_action_completed": player_role.night_action_completed,
    }


def acknowledge_insomniac(db: Session, game_id: str, player_id: str) -> dict:
    """Insomniac acknowledges they've seen their card; create action record and advance."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")
    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)
    if game.current_role_step != "Insomniac":
        raise ValueError("Insomniac role is not currently active")

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.current_role != "Insomniac":
        raise ValueError("Player is not the Insomniac")

    if not player_role.night_action_completed:
        action = Action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.VIEW_CARD,
            source_id=player_id,
            target_id=player_id,
            source_role=player_role.current_role,
            target_role=player_role.current_role
        )
        db.add(action)
        player_role.night_action_completed = True
        db.commit()

    _complete_insomniac_role_if_ready(db, game_id)
    return {"status": "ok"}


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    pr = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not pr:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return pr


def _complete_insomniac_role_if_ready(db: Session, game_id: str) -> None:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Insomniac":
        return
    roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.current_role == "Insomniac"
    ).all()
    if roles and all(r.night_action_completed for r in roles):
        night_service.mark_role_complete(db, game_id, "Insomniac")
