from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
import uuid


class PlayerRole(Base):
    """Represents a player's role in a specific game."""
    __tablename__ = "player_roles"

    player_role_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey('games.game_id'), nullable=False)
    player_id = Column(String, ForeignKey('players.player_id'), nullable=False)
    initial_role = Column(String, nullable=False)  # Role at start of night
    current_role = Column(String, nullable=False)  # Role after night actions (can change)
    team = Column(String, nullable=True)  # village, werewolf, tanner
    was_killed = Column(Boolean, default=False)  # Died during voting
    night_action_completed = Column(Boolean, default=False)  # Action/acknowledgment done for night role
    role_revealed = Column(Boolean, default=False)  # Player has acknowledged seeing their initial role

    # Relationships
    game = relationship("Game", back_populates="player_roles")
    player = relationship("Player")

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "player_role_id": self.player_role_id,
            "game_id": self.game_id,
            "player_id": self.player_id,
            "initial_role": self.initial_role,
            "current_role": self.current_role,
            "team": self.team,
            "was_killed": self.was_killed,
            "night_action_completed": self.night_action_completed,
            "role_revealed": getattr(self, "role_revealed", False),
        }
