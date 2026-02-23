"""Service for Seer night actions."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.center_card import CenterCard
from models.action import Action, ActionType
from services import night_service

CENTER_POSITIONS = ["left", "center", "right"]


def perform_seer_action(
    db: Session,
    game_id: str,
    player_id: str,
    action_type: str,
    target_player_id: str = None,
    card_indices: list[int] = None
) -> dict:
    """
    Perform Seer action: view one player OR view two center cards.
    
    Args:
        db: Database session
        game_id: ID of the game
        player_id: ID of the Seer player
        action_type: Either "view_player" or "view_center"
        target_player_id: Required if action_type is "view_player"
        card_indices: Required if action_type is "view_center" (must be exactly 2 indices)
    
    Returns:
        For view_player: {"role": "Werewolf"}
        For view_center: {"roles": ["Villager", "Robber"]}
    
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

    if game.current_role_step != "Seer":
        raise ValueError("Seer role is not currently active")

    player_role = _get_player_role(db, game_id, player_id)
    if player_role.initial_role != "Seer":
        raise ValueError("Player is not a Seer (only original Seer acts)")

    if player_role.night_action_completed:
        raise ValueError("Seer has already performed their action")

    if action_type == "view_player":
        if not target_player_id:
            raise ValueError("target_player_id is required for view_player action")
        
        if target_player_id == player_id:
            raise ValueError("Seer cannot view their own card")

        # Get target player's role
        target_role = _get_player_role(db, game_id, target_player_id)
        
        # Create action record
        action = Action(
            game_id=game_id,
            player_id=player_id,
            action_type=ActionType.VIEW_CARD,
            source_id=target_player_id,
            target_id=target_player_id,
            source_role=target_role.current_role,
            target_role=target_role.current_role
        )
        db.add(action)
        
        player_role.night_action_completed = True
        db.commit()
        
        _complete_seer_role_if_ready(db, game_id)
        
        return {"role": target_role.current_role}
    
    elif action_type == "view_center":
        if not card_indices:
            raise ValueError("card_indices is required for view_center action")
        
        if len(card_indices) != 2:
            raise ValueError("Seer must view exactly two center cards")
        
        if len(set(card_indices)) != 2:
            raise ValueError("Seer must view two different center cards")
        
        for idx in card_indices:
            if idx not in [0, 1, 2]:
                raise ValueError("card_indices must be 0, 1, or 2")

        # Get center cards
        viewed_roles = []
        for card_index in sorted(card_indices):
            position = CENTER_POSITIONS[card_index]
            center_card = db.query(CenterCard).filter(
                CenterCard.game_id == game_id,
                CenterCard.position == position
            ).first()
            
            if not center_card:
                raise ValueError(f"Center card at index {card_index} not found")
            
            # Create separate action record for each center card viewed
            action = Action(
                game_id=game_id,
                player_id=player_id,
                action_type=ActionType.VIEW_CARD,
                source_id=str(card_index),
                target_id=str(card_index),
                source_role=center_card.role,
                target_role=center_card.role
            )
            db.add(action)
            viewed_roles.append(center_card.role)
        
        player_role.night_action_completed = True
        db.commit()
        
        _complete_seer_role_if_ready(db, game_id)
        
        return {"roles": viewed_roles}
    
    else:
        raise ValueError(f"Invalid action_type: {action_type}. Must be 'view_player' or 'view_center'")


def _get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not player_role:
        raise ValueError(f"Player {player_id} not found in game {game_id}")
    return player_role


def _complete_seer_role_if_ready(db: Session, game_id: str) -> None:
    """Mark Seer role as complete if all Seers have acted."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.current_role_step != "Seer":
        return

    seer_roles = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.initial_role == "Seer"
    ).all()
    
    if not seer_roles:
        return

    if all(role.night_action_completed for role in seer_roles):
        night_service.mark_role_complete(db, game_id, "Seer")
