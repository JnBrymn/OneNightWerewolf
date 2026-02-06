from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import uuid
import enum


class GameState(str, enum.Enum):
    """Enum for game states."""
    NIGHT = "NIGHT"
    DAY_DISCUSSION = "DAY_DISCUSSION"
    DAY_VOTING = "DAY_VOTING"
    RESULTS = "RESULTS"


class Game(Base):
    """Represents a single game instance within a game set."""
    __tablename__ = "games"

    game_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_set_id = Column(String, ForeignKey('game_sets.game_set_id'), nullable=False)
    game_number = Column(Integer, nullable=False)  # Sequence number within game set (1, 2, 3...)
    state = Column(SQLEnum(GameState), nullable=False, default=GameState.NIGHT)
    current_role_step = Column(String, nullable=True)  # Which role is active in night phase
    active_roles = Column(JSON, nullable=True)  # Ordered list of active roles (roles with wake_order) present in this game, ordered by wake_order
    simulated_role_started_at = Column(DateTime(timezone=True), nullable=True)  # When a simulated (center card) role started acting
    simulated_role_duration_seconds = Column(Integer, nullable=True)  # Random duration for simulated role (15-40 seconds)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    game_set = relationship("GameSet", backref="games")
    player_roles = relationship("PlayerRole", back_populates="game")
    center_cards = relationship("CenterCard", back_populates="game")

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "game_id": self.game_id,
            "game_set_id": self.game_set_id,
            "game_number": self.game_number,
            "state": self.state.value if self.state else None,
            "current_role_step": self.current_role_step,
            "active_roles": self.active_roles,
            "simulated_role_started_at": self.simulated_role_started_at.isoformat() if self.simulated_role_started_at else None,
            "simulated_role_duration_seconds": self.simulated_role_duration_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
