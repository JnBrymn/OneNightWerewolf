"""Service for game creation and role assignment."""
import random
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.game_set import GameSet
from models.player_role import PlayerRole
from models.center_card import CenterCard

# Official wake order from One Night Ultimate Werewolf (instructions.md)
# This should eventually come from the roles table ordered by wake_order
WAKE_ORDER = [
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


def start_game(db: Session, game_set_id: str) -> Game:
    """
    Start a new game in the game set.

    This creates a Game instance, shuffles roles, assigns them to players,
    and places 3 cards in the center.

    If an active game already exists (not ended, not in RESULTS state),
    returns that game instead of creating a duplicate.

    Args:
        db: Database session
        game_set_id: ID of the game set

    Returns:
        The created Game instance or existing active game

    Raises:
        ValueError: If game set not found or doesn't have enough players
    """
    # Get the game set with all its players
    game_set = db.query(GameSet).filter(GameSet.game_set_id == game_set_id).first()
    if not game_set:
        raise ValueError(f"Game set {game_set_id} not found")

    # Check if there's already an active game (not ended, not in RESULTS)
    # This prevents multiple games from being created simultaneously
    existing_active_game = db.query(Game).filter(
        Game.game_set_id == game_set_id,
        Game.ended_at.is_(None),
        Game.state != GameState.RESULTS
    ).order_by(Game.created_at.desc()).first()

    if existing_active_game:
        # Return the existing active game instead of creating a duplicate
        return existing_active_game

    # Get all players in this game set
    players = game_set.players

    # Validate we have enough players
    if len(players) < game_set.num_players:
        raise ValueError(
            f"Not enough players joined. Expected {game_set.num_players}, "
            f"but only {len(players)} have joined"
        )

    # Get the selected roles from game set
    roles = game_set.selected_roles
    if not roles or len(roles) != game_set.num_players + 3:
        raise ValueError(
            f"Invalid role configuration. Expected {game_set.num_players + 3} roles, "
            f"but got {len(roles) if roles else 0}"
        )

    # Calculate game number (count existing games + 1)
    existing_games_count = len(game_set.games) if game_set.games else 0
    game_number = existing_games_count + 1

    # Create the game
    game = Game(
        game_set_id=game_set_id,
        game_number=game_number,
        state=GameState.NIGHT,
        current_role_step=None  # Will be set when night phase starts
    )
    db.add(game)
    db.flush()  # Get the game_id

    # Shuffle roles
    shuffled_roles = roles.copy()
    random.shuffle(shuffled_roles)

    # Assign roles to players (first N roles)
    player_roles = shuffled_roles[:game_set.num_players]
    for i, player in enumerate(players):
        role = player_roles[i]
        team = _get_team_for_role(role)

        player_role = PlayerRole(
            game_id=game.game_id,
            player_id=player.player_id,
            initial_role=role,
            current_role=role,  # Same as initial at start
            team=team,
            was_killed=False
        )
        db.add(player_role)

    # Put remaining 3 roles in center
    center_roles = shuffled_roles[game_set.num_players:]
    positions = ["left", "center", "right"]

    for i, role in enumerate(center_roles):
        center_card = CenterCard(
            game_id=game.game_id,
            position=positions[i],
            role=role
        )
        db.add(center_card)

    # Create ordered list of active roles (roles with wake_order) in this game
    # Get all unique roles from player roles and center cards
    all_roles_in_game = set(player_roles + center_roles)
    
    # Only include roles that have wake_order (active roles that wake up at night)
    # Order them according to wake_order sequence
    active_roles = []
    
    for role in WAKE_ORDER:
        if role in all_roles_in_game:
            active_roles.append(role)
    
    # Set the active roles on the game
    game.active_roles = active_roles

    db.commit()
    db.refresh(game)

    return game


def _get_team_for_role(role: str) -> str:
    """
    Get the team for a given role.

    Args:
        role: The role name

    Returns:
        Team name: "werewolf", "village", or "tanner"
    """
    werewolf_team = ["Werewolf", "Minion"]
    tanner_team = ["Tanner"]

    if role in werewolf_team:
        return "werewolf"
    elif role in tanner_team:
        return "tanner"
    else:
        return "village"


def get_active_game(db: Session, game_set_id: str) -> Game | None:
    """
    Get the current active game for a game set.

    An active game is one that hasn't ended and is not in RESULTS state.

    Args:
        db: Database session
        game_set_id: ID of the game set

    Returns:
        The active Game instance, or None if no active game exists
    """
    return db.query(Game).filter(
        Game.game_set_id == game_set_id,
        Game.ended_at.is_(None),
        Game.state != GameState.RESULTS
    ).order_by(Game.created_at.desc()).first()


def get_player_role(db: Session, game_id: str, player_id: str) -> PlayerRole:
    """
    Get a player's role in a specific game.

    Args:
        db: Database session
        game_id: ID of the game
        player_id: ID of the player

    Returns:
        The PlayerRole instance

    Raises:
        ValueError: If player role not found
    """
    player_role = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()

    if not player_role:
        raise ValueError(f"Player {player_id} not found in game {game_id}")

    return player_role
