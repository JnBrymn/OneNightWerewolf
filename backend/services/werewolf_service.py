"""Service for Werewolf night actions."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.center_card import CenterCard
from models.action import Action, ActionType
from services import night_service

CENTER_POSITIONS = ["left", "center", "right"]


def get_night_info(db: Session, game_id: str, player_id: str) -> dict:
    """Get role-specific night info for a player."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    player_role = _get_player_role(db, game_id, player_id)
    info = {"role": player_role.current_role}

    if player_role.initial_role != "Werewolf":
        return info

    werewolf_roles = _get_werewolf_roles(db, game_id)
    is_lone_wolf = len(werewolf_roles) == 1
    other_werewolves = []

    if not is_lone_wolf:
        for role in werewolf_roles:
            if role.player_id != player_id:
                other_werewolves.append({
                    "player_id": role.player_id,
                    "player_name": role.player.player_name if role.player else None,
                })

    info.update({
        "is_lone_wolf": is_lone_wolf,
        "other_werewolves": other_werewolves,
        "night_action_completed": player_role.night_action_completed,
    })
    return info


def view_center_card(db: Session, game_id: str, player_id: str, card_index: int) -> dict:
    """Allow a lone werewolf to view a center card."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    if game.current_role_step != "Werewolf":
        raise ValueError("Werewolf role is not currently active")

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.initial_role != "Werewolf":
        raise ValueError("Player is not a Werewolf (only original Werewolf acts)")

    werewolf_roles = _get_werewolf_roles(db, game_id)
    if len(werewolf_roles) != 1:
        raise ValueError("Center card viewing is only available to a lone Werewolf")

    if player_role.night_action_completed:
        raise ValueError("Werewolf has already viewed a center card")

    if card_index not in [0, 1, 2]:
        raise ValueError("card_index must be 0, 1, or 2")

    position = CENTER_POSITIONS[card_index]
    center_card = db.query(CenterCard).filter(
        CenterCard.game_id == game_id,
        CenterCard.position == position
    ).first()

    if not center_card:
        raise ValueError("Center card not found")

    # Create action record
    action = Action(
        game_id=game_id,
        player_id=player_id,
        action_type=ActionType.VIEW_CARD,
        source_id=str(card_index),  # Center card index
        target_id=str(card_index),
        source_role=center_card.role,
        target_role=center_card.role
    )
    db.add(action)

    player_role.night_action_completed = True
    db.commit()

    _complete_werewolf_role_if_ready(db, game_id)

    return {"role": center_card.role}


def acknowledge_werewolf(db: Session, game_id: str, player_id: str) -> dict:
    """Acknowledge werewolf info for multi-werewolf games."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state != GameState.NIGHT:
        raise ValueError(f"Game {game_id} is not in NIGHT state")

    if game.current_role_step is None:
        night_service.initialize_night_phase(db, game_id)
        db.refresh(game)

    if game.current_role_step != "Werewolf":
        raise ValueError("Werewolf role is not currently active")

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.initial_role != "Werewolf":
        raise ValueError("Player is not a Werewolf (only original Werewolf acts)")

    if not player_role.night_action_completed:
        # Create action records for each other werewolf this player sees
        werewolf_roles = _get_werewolf_roles(db, game_id)
        for other_role in werewolf_roles:
            if other_role.player_id != player_id:
                # Create VIEW_CARD action for each other werewolf
                action = Action(
                    game_id=game_id,
                    player_id=player_id,
                    action_type=ActionType.VIEW_CARD,
                    source_id=other_role.player_id,
                    target_id=other_role.player_id,
                    source_role="Werewolf",
                    target_role="Werewolf"
                )
                db.add(action)
        
        player_role.night_action_completed = True
        db.commit()

    _complete_werewolf_role_if_ready(db, game_id)

    return {"status": "ok"}


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not player_role:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return player_role


def _get_werewolf_roles(db: Session, game_id: str) -> list[PlayerRole]:
    return db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.current_role == "Werewolf"
    ).all()


def _complete_werewolf_role_if_ready(db: Session, game_id: str) -> None:
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Werewolf":
        return

    werewolf_roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.initial_role == "Werewolf"
    ).all()
    if not werewolf_roles:
        return

    if all(role.night_action_completed for role in werewolf_roles):
        night_service.mark_role_complete(db, game_id, "Werewolf")
