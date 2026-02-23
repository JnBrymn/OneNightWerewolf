"""VoteNow model: players requesting to skip discussion and go to voting."""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from db.database import Base
import uuid


class VoteNow(Base):
    """A player's request to start voting now (during day discussion)."""
    __tablename__ = "vote_now"
    __table_args__ = (UniqueConstraint("game_id", "player_id", name="uq_vote_now_game_player"),)

    vote_now_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.game_id"), nullable=False)
    player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
