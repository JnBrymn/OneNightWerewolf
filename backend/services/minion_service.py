"""Service for Minion night actions: see who the Werewolves are, then acknowledge."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.action import Action, ActionType
from services import night_service


def get_night_info(db: Session, game_id: str, player_id: str) -> dict:
    """Return Minion's night info: list of werewolves. Used by GET night-info dispatcher."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")
    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.current_role != "Minion":
        raise ValueError("Player is not the Minion")
    if game.current_role_step != "Minion":
        raise ValueError("Minion role is not currently active")

    werewolves = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.current_role == "Werewolf"
    ).all()

    other_werewolves = [
        {"player_id": pr.player_id, "player_name": pr.player.player_name if pr.player else None}
        for pr in werewolves
    ]

    return {
        "role": "Minion",
        "werewolves": other_werewolves,
        "night_action_completed": player_role.night_action_completed,
    }


def acknowledge_minion(db: Session, game_id: str, player_id: str) -> dict:
    """Minion acknowledges they've seen the werewolves; create action record and advance."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")
    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)
    if game.current_role_step != "Minion":
        raise ValueError("Minion role is not currently active")

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.current_role != "Minion":
        raise ValueError("Player is not the Minion")

    if not player_role.night_action_completed:
        werewolves = db.query(PlayerRole).filter(
            PlayerRole.game_id == game_id,
            PlayerRole.current_role == "Werewolf"
        ).all()
        for w in werewolves:
            action = Action(
                game_id=game_id,
                player_id=player_id,
                action_type=ActionType.VIEW_CARD,
                source_id=w.player_id,
                target_id=w.player_id,
                source_role="Werewolf",
                target_role="Werewolf"
            )
            db.add(action)
        player_role.night_action_completed = True
        db.commit()

    _complete_minion_role_if_ready(db, game_id)
    return {"status": "ok"}


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    pr = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not pr:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return pr


def _complete_minion_role_if_ready(db: Session, game_id: str) -> None:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Minion":
        return
    roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.current_role == "Minion"
    ).all()
    if roles and all(r.night_action_completed for r in roles):
        night_service.mark_role_complete(db, game_id, "Minion")
