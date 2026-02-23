"""Service for day discussion phase (timer and transition to voting)."""
from datetime import datetime
from sqlalchemy.orm import Session
from models.game import Game, GameState
from models.game_set import GameSet
from models.player_role import PlayerRole
from models.vote_now import VoteNow


def _vote_now_majority(total_players: int) -> int:
    """Number of 'vote now' requests needed for majority (> half)."""
    return (total_players // 2) + 1


def get_discussion_status(db: Session, game_id: str, player_id: str | None = None) -> dict:
    """
    Get discussion timer status. If game is DAY_DISCUSSION and timer expired,
    transition to DAY_VOTING. Optionally include vote-now counts when player_id given.
    """
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")

    if game.state == GameState.DAY_VOTING or game.state == GameState.RESULTS:
        out = {"time_remaining_seconds": 0, "state": game.state.value}
        if player_id:
            out["vote_now_count"] = 0
            out["total_players"] = 0
            out["vote_now_majority"] = 0
            out["current_player_voted_now"] = False
        return out

    if game.state != GameState.DAY_DISCUSSION:
        raise ValueError(f"Game is not in discussion phase (state={game.state})")

    total_players = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).count()
    vote_now_count = db.query(VoteNow).filter(VoteNow.game_id == game_id).count()
    majority = _vote_now_majority(total_players)
    current_player_voted_now = False
    if player_id:
        current_player_voted_now = (
            db.query(VoteNow).filter(
                VoteNow.game_id == game_id,
                VoteNow.player_id == player_id,
            ).first() is not None
        )

    game_set = db.query(GameSet).filter(GameSet.game_set_id == game.game_set_id).first()
    if not game_set:
        raise ValueError("Game set not found")
    timer_seconds = game_set.discussion_timer_seconds

    started_at = game.discussion_started_at
    if not started_at:
        game.discussion_started_at = datetime.utcnow()
        db.commit()
        db.refresh(game)
        started_at = game.discussion_started_at

    now = datetime.utcnow()
    elapsed = (now - started_at).total_seconds() if started_at else 0
    remaining = max(0, int(timer_seconds - elapsed))

    if remaining <= 0:
        game.state = GameState.DAY_VOTING
        db.commit()
        db.refresh(game)
        out = {"time_remaining_seconds": 0, "state": GameState.DAY_VOTING.value}
        if player_id:
            out["vote_now_count"] = vote_now_count
            out["total_players"] = total_players
            out["vote_now_majority"] = majority
            out["current_player_voted_now"] = current_player_voted_now
        return out

    out = {
        "time_remaining_seconds": remaining,
        "state": GameState.DAY_DISCUSSION.value,
    }
    if player_id:
        out["vote_now_count"] = vote_now_count
        out["total_players"] = total_players
        out["vote_now_majority"] = majority
        out["current_player_voted_now"] = current_player_voted_now
    return out


def record_vote_now(db: Session, game_id: str, player_id: str) -> dict:
    """Record that this player wants to vote now. If majority reached, transition to DAY_VOTING."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise ValueError(f"Game {game_id} not found")
    if game.state != GameState.DAY_DISCUSSION:
        raise ValueError("Game is not in discussion phase")

    player_roles = db.query(PlayerRole).filter(PlayerRole.game_id == game_id).all()
    total_players = len(player_roles)
    if not any(pr.player_id == player_id for pr in player_roles):
        raise ValueError("Player not in this game")

    existing = db.query(VoteNow).filter(
        VoteNow.game_id == game_id,
        VoteNow.player_id == player_id,
    ).first()
    if not existing:
        db.add(VoteNow(game_id=game_id, player_id=player_id))
        db.commit()

    vote_now_count = db.query(VoteNow).filter(VoteNow.game_id == game_id).count()
    majority = _vote_now_majority(total_players)
    if vote_now_count >= majority:
        game.state = GameState.DAY_VOTING
        db.commit()
        db.refresh(game)

    return {
        "status": "ok",
        "vote_now_count": vote_now_count,
        "total_players": total_players,
        "vote_now_majority": majority,
        "state": game.state.value,
    }


def check_discussion_timer_and_maybe_transition(db: Session, game_id: str) -> None:
    """If game is DAY_DISCUSSION and timer expired, transition to DAY_VOTING. No-op otherwise."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game or game.state != GameState.DAY_DISCUSSION:
        return
    try:
        get_discussion_status(db, game_id)
    except ValueError:
        pass
