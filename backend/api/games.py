"""API endpoints for games."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from services import game_service

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("/{game_id}/players/{player_id}/role")
def get_player_role(game_id: str, player_id: str, db: Session = Depends(get_db)):
    """Get a player's role in a specific game."""
    try:
        player_role = game_service.get_player_role(db, game_id, player_id)
        return player_role.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
