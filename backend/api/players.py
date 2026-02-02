from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.player import Player
from models.schemas import PlayerCreate, PlayerResponse

router = APIRouter(prefix="/api/players", tags=["players"])


@router.post("", response_model=PlayerResponse, status_code=201)
def create_player(player_data: PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player."""
    player = Player(
        player_name=player_data.player_name,
        avatar_url=player_data.avatar_url,
        user_id=player_data.user_id,
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: str, db: Session = Depends(get_db)):
    """Get a player by ID."""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player
