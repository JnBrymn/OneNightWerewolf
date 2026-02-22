from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import uuid
import enum


class ActionType(str, enum.Enum):
    """Enum for action types."""
    SWAP_PLAYER_TO_PLAYER = "SWAP_PLAYER_TO_PLAYER"
    SWAP_PLAYER_TO_CENTER = "SWAP_PLAYER_TO_CENTER"
    SWAP_TWO_PLAYERS = "SWAP_TWO_PLAYERS"  # Troublemaker swaps two other players
    VIEW_CARD = "VIEW_CARD"


class Action(Base):
    """Represents a night phase action performed by a player."""
    __tablename__ = "actions"

    action_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey('games.game_id'), nullable=False)
    player_id = Column(String, ForeignKey('players.player_id'), nullable=False)
    action_type = Column(SQLEnum(ActionType), nullable=False)
    source_id = Column(String, nullable=False)  # player_id or "0"/"1"/"2" for center cards
    target_id = Column(String, nullable=True)  # player_id or "0"/"1"/"2" for center cards, or "" for VIEW_CARD
    source_role = Column(String, nullable=False)  # Role of source card
    target_role = Column(String, nullable=True)  # Role of target card, or None for VIEW_CARD
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    game = relationship("Game", backref="actions")
    player = relationship("Player", backref="actions")

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "action_id": self.action_id,
            "game_id": self.game_id,
            "player_id": self.player_id,
            "action_type": self.action_type.value if self.action_type else None,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source_role": self.source_role,
            "target_role": self.target_role,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
