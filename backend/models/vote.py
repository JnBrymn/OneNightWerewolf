"""Vote model for day voting phase."""
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from db.database import Base
import uuid


class Vote(Base):
    """A player's vote for who to kill (target) in a game."""
    __tablename__ = "votes"

    vote_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey("games.game_id"), nullable=False)
    voter_player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
    target_player_id = Column(String, ForeignKey("players.player_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "vote_id": self.vote_id,
            "voter_id": self.voter_player_id,
            "target_id": self.target_player_id,
        }
