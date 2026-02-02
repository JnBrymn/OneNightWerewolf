from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base
import uuid


class CenterCard(Base):
    """Represents one of the three center cards in a game."""
    __tablename__ = "center_cards"

    center_card_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id = Column(String, ForeignKey('games.game_id'), nullable=False)
    position = Column(String, nullable=False)  # "left", "center", "right"
    role = Column(String, nullable=False)  # The role card in this position

    # Relationships
    game = relationship("Game", back_populates="center_cards")

    def to_dict(self):
        """Convert model to dictionary for API responses."""
        return {
            "center_card_id": self.center_card_id,
            "game_id": self.game_id,
            "position": self.position,
            "role": self.role,
        }
