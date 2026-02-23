"""Service for Mason night actions: see the other Mason (or that they're in center), then acknowledge."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.center_card import CenterCard
from models.action import Action, ActionType
from services import night_service


def get_night_info(db: Session, game_id: str, player_id: str) -> dict:
    """Return Mason's night info: other mason player or in_center. Used by GET night-info dispatcher."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")
    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.current_role != "Mason":
        raise ValueError("Player is not a Mason")
    if game.current_role_step != "Mason":
        raise ValueError("Mason role is not currently active")

    other_masons = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id != player_id,
        PlayerRole.current_role == "Mason"
    ).all()

    mason_in_center = db.query(CenterCard).filter(
        CenterCard.game_id == game_id,
        CenterCard.role == "Mason"
    ).first()

    if other_masons:
        other = other_masons[0]
        return {
            "role": "Mason",
            "other_mason": {"player_id": other.player_id, "player_name": other.player.player_name if other.player else None},
            "in_center": False,
            "night_action_completed": player_role.night_action_completed,
        }
    else:
        return {
            "role": "Mason",
            "other_mason": None,
            "in_center": mason_in_center is not None,
            "night_action_completed": player_role.night_action_completed,
        }


def acknowledge_mason(db: Session, game_id: str, player_id: str) -> dict:
    """Mason acknowledges; create action record and advance."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")
    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)
    if game.current_role_step != "Mason":
        raise ValueError("Mason role is not currently active")

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.initial_role != "Mason":
        raise ValueError("Player is not a Mason (only original Mason acts)")

    if not player_role.night_action_completed:
        other_masons = db.query(PlayerRole).filter(
            PlayerRole.game_id == game_id,
            PlayerRole.player_id != player_id,
            PlayerRole.current_role == "Mason"
        ).all()
        mason_in_center = db.query(CenterCard).filter(
            CenterCard.game_id == game_id,
            CenterCard.role == "Mason"
        ).first()

        if other_masons:
            other = other_masons[0]
            action = Action(
                game_id=game_id,
                player_id=player_id,
                action_type=ActionType.VIEW_CARD,
                source_id=other.player_id,
                target_id=other.player_id,
                source_role="Mason",
                target_role="Mason"
            )
            db.add(action)
        else:
            # Other Mason is in center: use a sentinel for "center"
            action = Action(
                game_id=game_id,
                player_id=player_id,
                action_type=ActionType.VIEW_CARD,
                source_id="center",
                target_id="center",
                source_role="Mason",
                target_role="Mason"
            )
            db.add(action)

        player_role.night_action_completed = True
        db.commit()

    _complete_mason_role_if_ready(db, game_id)
    return {"status": "ok"}


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    pr = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not pr:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return pr


def _complete_mason_role_if_ready(db: Session, game_id: str) -> None:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Mason":
        return
    roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.initial_role == "Mason"
    ).all()
    if roles and all(r.night_action_completed for r in roles):
        night_service.mark_role_complete(db, game_id, "Mason")
