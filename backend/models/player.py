from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import uuid


# Association table for many-to-many relationship between players and game sets
game_set_players = Table(
    'game_set_players',
    Base.metadata,
    Column('game_set_id', String, ForeignKey('game_sets.game_set_id'), primary_key=True),
    Column('player_id', String, ForeignKey('players.player_id'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now())
)


class Player(Base):
    """Represents a player identity (persistent across game sets)."""
    __tablename__ = "players"

    player_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # User/session ID
    player_name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "player_id": self.player_id,
            "user_id": self.user_id,
            "player_name": self.player_name,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
