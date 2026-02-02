from sqlalchemy import Column, String, Integer, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import uuid


class GameSet(Base):
    """Represents a set of games played together with cumulative scoring."""
    __tablename__ = "game_sets"

    game_set_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_by = Column(String, nullable=True)  # User/session ID of creator
    num_players = Column(Integer, nullable=False)
    selected_roles = Column(JSON, nullable=False)  # Array of role names
    discussion_timer_seconds = Column(Integer, nullable=False, default=300)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to players
    players = relationship("Player", secondary="game_set_players", backref="game_sets")

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "game_set_id": self.game_set_id,
            "created_by": self.created_by,
            "num_players": self.num_players,
            "selected_roles": self.selected_roles,
            "discussion_timer_seconds": self.discussion_timer_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
