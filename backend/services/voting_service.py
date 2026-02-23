"""Service for day voting phase."""
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.vote import Vote


def cast_vote(db: Session, game_id: str, voter_player_id: str, target_player_id: str) -> dict:
    """Record a vote. Transition game to RESULTS when all players have voted."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.DAY_VOTING:
        raise ValueError(f"Game is not in voting phase (state={game.state})")

    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    player_ids_in_game = {pr.player_id for pr in player_roles}
    if voter_player_id not in player_ids_in_game:
        raise ValueError("Voter is not in this game")
    if target_player_id not in player_ids_in_game:
        raise ValueError("Target is not in this game")
    if voter_player_id == target_player_id:
        raise ValueError("Cannot vote for yourself")

    existing = db.query(Vote).filter(
        Vote.game_id == game_id,
        Vote.voter_player_id == voter_player_id
    ).first()
    if existing:
        raise ValueError("Player has already voted")

    vote = Vote(
        game_id=game_id,
        voter_player_id=voter_player_id,
        target_player_id=target_player_id,
    )
    db.add(vote)
    db.commit()
    db.refresh(vote)

    # Check if all players have voted
    vote_count = db.query(Vote).filter(Vote.game_id == game_id).count()
    if vote_count >= len(player_roles):
        game.state = GameState.RESULTS
        db.commit()
        db.refresh(game)

    return {"status": "vote_recorded"}


def get_votes(db: Session, game_id: str) -> dict:
    """Get vote status for a game (votes list, count, total players)."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    total_players = len(player_roles)
    votes = db.query(Vote).filter(Vote.game_id == game_id).all()
    return {
        "votes": [v.to_dict() for v in votes],
        "votes_cast": len(votes),
        "total_players": total_players,
    }
