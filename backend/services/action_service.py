"""Service for action-related operations."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.action import Action, ActionType
from models.center_card import CenterCard
from models.player import Player
from services import werewolf_service


def get_available_actions(db: Session, game_id: str, player_id: str) -> dict:
    """
    Get which players/center cards are actionable for the current player.
    
    Returns:
        {
            "actionable_players": [{"player_id": "...", "player_name": "..."}, ...],
            "actionable_center_cards": [0, 1, 2],  # indices
            "instructions": "..."
        }
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not player_role:
        raise ValueError(f"Player {player_id} not found in game {game_id}")

    actionable_players = []
    actionable_center_cards = []
    instructions = ""

    # Only provide actions during NIGHT state
    if game.state != GameState.NIGHT:
        return {
            "actionable_players": [],
            "actionable_center_cards": [],
            "instructions": "No actions available outside of night phase."
        }

    # Check if it's this player's turn: only the player whose *initial* role matches
    # the current step gets to act (so e.g. Robber who stole Insomniac doesn't act at Insomniac step).
    if game.current_role_step != player_role.initial_role:
        return {
            "actionable_players": [],
            "actionable_center_cards": [],
            "instructions": f"Waiting for {game.current_role_step} to complete their action..."
        }

    # Role-specific action logic: use the step (role currently acting), not player's current card
    current_role = game.current_role_step

    if current_role == "Werewolf":
        # Check if lone wolf or multiple werewolves
        werewolf_roles = db.query(PlayerRole).filter(
            PlayerRole.game_id == game_id,
            PlayerRole.current_role == "Werewolf"
        ).all()
        
        if len(werewolf_roles) == 1:
            # Lone wolf: can view center cards
            actionable_center_cards = [0, 1, 2]
            instructions = "You are the lone Werewolf. Choose one center card to view."
        else:
            # Multiple werewolves: no action needed, just info display
            instructions = "You are a Werewolf. Look for other Werewolves."
    
    elif current_role == "Seer":
        # Seer can view one player OR two center cards
        # Get all other players
        all_players = db.query(PlayerRole).filter(
            PlayerRole.game_id == game_id,
            PlayerRole.player_id != player_id
        ).all()
        actionable_players = [
            {"player_id": pr.player_id, "player_name": pr.player.player_name if pr.player else None}
            for pr in all_players
        ]
        actionable_center_cards = [0, 1, 2]
        instructions = "You are the Seer. View one player's card OR two center cards."
    
    elif current_role == "Robber":
        # Robber can exchange with another player
        all_players = db.query(PlayerRole).filter(
            PlayerRole.game_id == game_id,
            PlayerRole.player_id != player_id
        ).all()
        actionable_players = [
            {"player_id": pr.player_id, "player_name": pr.player.player_name if pr.player else None}
            for pr in all_players
        ]
        instructions = "You are the Robber. Choose a player to rob (exchange cards)."
    
    elif current_role == "Troublemaker":
        # Troublemaker can exchange two other players
        all_players = db.query(PlayerRole).filter(
            PlayerRole.game_id == game_id,
            PlayerRole.player_id != player_id
        ).all()
        actionable_players = [
            {"player_id": pr.player_id, "player_name": pr.player.player_name if pr.player else None}
            for pr in all_players
        ]
        instructions = "You are the Troublemaker. Choose two players to swap (without looking)."
    
    elif current_role == "Drunk":
        # Drunk can exchange with center card
        actionable_center_cards = [0, 1, 2]
        instructions = "You are the Drunk. Choose a center card to exchange with (without looking)."
    
    elif current_role == "Insomniac":
        # Insomniac just views their own card (no action needed)
        instructions = "You are the Insomniac. Check your current card."
    
    elif current_role == "Minion":
        # Minion sees werewolves (no action needed)
        instructions = "You are the Minion. See who the Werewolves are."
    
    elif current_role == "Mason":
        # Mason sees other Mason (no action needed)
        instructions = "You are a Mason. Look for the other Mason."
    
    else:
        # Villager, Tanner, Hunter - no night actions
        instructions = f"You are a {current_role}. No night action required."

    return {
        "actionable_players": actionable_players,
        "actionable_center_cards": actionable_center_cards,
        "instructions": instructions
    }


def get_player_actions(db: Session, game_id: str, player_id: str) -> dict:
    """
    Get all accrued actions visible to the player.
    
    Returns:
        {
            "actions": [
                {
                    "action_type": "VIEW_CARD",
                    "description": "You are a Werewolf. Your fellow werewolves are: Alice, Bob"
                },
                ...
            ]
        }
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    if not player_role:
        raise ValueError(f"Player {player_id} not found in game {game_id}")

    actions = []
    # For "do we add werewolf info" we care about player's current role (what they see)
    current_role = player_role.current_role

    # Get actions from database
    db_actions = db.query(Action).filter(
        Action.game_id == game_id,
        Action.player_id == player_id
    ).order_by(Action.timestamp).all()

    # Collect werewolf-fellow VIEW_CARDs so we can emit one combined description
    werewolf_fellow_target_ids = []

    for action in db_actions:
        if action.action_type == ActionType.VIEW_CARD:
            if action.target_id in ("0", "1", "2"):
                # Viewed center card
                card_label = ["Left", "Center", "Right"][int(action.target_id)]
                actions.append({
                    "action_type": "VIEW_CARD",
                    "description": f"You viewed center card {card_label}. The card is: {action.target_role}"
                })
            elif action.target_id == "center":
                # Mason: other Mason is in center
                actions.append({
                    "action_type": "VIEW_CARD",
                    "description": "The other Mason is in the center."
                })
            elif action.source_id == action.target_id == player_id:
                # Insomniac: viewed own card
                actions.append({
                    "action_type": "VIEW_CARD",
                    "description": f"Your current role is: {action.target_role}"
                })
            elif (current_role == "Werewolf" and action.source_role == "Werewolf"
                  and action.target_role == "Werewolf" and action.target_id != player_id):
                # Werewolf viewing fellow werewolf(s) — aggregate, don't emit "You viewed X's card"
                werewolf_fellow_target_ids.append(action.target_id)
            else:
                # Viewed another player's card
                target_player = db.query(Player).filter(Player.player_id == action.target_id).first()
                target_name = target_player.player_name if target_player else action.target_id
                actions.append({
                    "action_type": "VIEW_CARD",
                    "description": f"You viewed {target_name}'s card. It is: {action.target_role}"
                })
        elif action.action_type == ActionType.SWAP_PLAYER_TO_PLAYER:
            target_player = db.query(Player).filter(Player.player_id == action.target_id).first()
            target_name = target_player.player_name if target_player else action.target_id
            actions.append({
                "action_type": "SWAP_PLAYER_TO_PLAYER",
                "description": f"You exchanged cards with {target_name}. You are now: {action.target_role}"
            })
        elif action.action_type == ActionType.SWAP_TWO_PLAYERS:
            p1 = db.query(Player).filter(Player.player_id == action.source_id).first()
            p2 = db.query(Player).filter(Player.player_id == action.target_id).first()
            n1 = p1.player_name if p1 else action.source_id
            n2 = p2.player_name if p2 else action.target_id
            actions.append({
                "action_type": "SWAP_TWO_PLAYERS",
                "description": f"You swapped the cards of {n1} and {n2}."
            })
        elif action.action_type == ActionType.SWAP_PLAYER_TO_CENTER:
            card_label = ["Left", "Center", "Right"][int(action.target_id)]
            actions.append({
                "action_type": "SWAP_PLAYER_TO_CENTER",
                "description": f"You exchanged your card with center card {card_label}. You don't know your new role."
            })

    # Emit one description for multiple werewolves (werewolf-fellow VIEW_CARDs collected above)
    if werewolf_fellow_target_ids:
        names = []
        for tid in werewolf_fellow_target_ids:
            p = db.query(Player).filter(Player.player_id == tid).first()
            names.append(p.player_name if p else tid)
        if len(names) == 1:
            actions.append({
                "action_type": "VIEW_CARD",
                "description": f"There are 2 werewolves, the other is {names[0]}."
            })
        else:
            actions.append({
                "action_type": "VIEW_CARD",
                "description": f"You are a Werewolf. Your fellow werewolves are: {', '.join(names)}"
            })

    # Also add role-specific info that might not be in actions table yet
    # (for werewolf, minion, mason - info display roles)
    # Note: For werewolves, actions are created when they acknowledge, so we should have them in db_actions
    # But if we don't have actions yet and it's their turn, we can add info
    if current_role == "Werewolf" and game.state == GameState.NIGHT and game.current_role_step == "Werewolf":
        # Check if we have werewolf actions already
        has_werewolf_actions = any(
            a.action_type == ActionType.VIEW_CARD and a.source_role == "Werewolf"
            for a in db_actions
        )
        if not has_werewolf_actions:
            try:
                night_info = werewolf_service.get_night_info(db, game_id, player_id)
                if night_info.get("is_lone_wolf"):
                    # Lone wolf - no info to add, they need to choose center card
                    pass
                else:
                    other_werewolves = night_info.get("other_werewolves", [])
                    if other_werewolves:
                        names = [w.get("player_name") or w.get("player_id") for w in other_werewolves]
                        actions.append({
                            "action_type": "INFO",
                            "description": f"You are a Werewolf. Your fellow werewolves are: {', '.join(names)}"
                        })
                    else:
                        actions.append({
                            "action_type": "INFO",
                            "description": "You are a Werewolf. There are no other werewolves in the game."
                        })
            except ValueError:
                pass  # Role not active yet

    return {
        "actions": actions
    }
