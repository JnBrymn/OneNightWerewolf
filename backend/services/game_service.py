"""Service for game creation and role assignment."""
import random
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.game_set import GameSet
from models.player_role import PlayerRole
from models.center_card import CenterCard


def start_game(db: Session, game_set_id: str) -> Game:
    """
    Start a new game in the game set.

    This creates a Game instance, shuffles roles, assigns them to players,
    and places 3 cards in the center.

    Args:
        db: Database session
        game_set_id: ID of the game set

    Returns:
        The created Game instance

    Raises:
        ValueError: If game set not found or doesn't have enough players
    """
    # Get the game set with all its players
    game_set = db.query(GameSet).filter(GameSet.game_set_id == game_set_id).first()
    if not game_set:
        raise ValueError(f"Game set {game_set_id} not found")

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
