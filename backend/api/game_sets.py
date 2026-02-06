from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.database import get_db
from models.game_set import GameSet
from models.player import Player, game_set_players
from models.schemas import GameSetCreate, GameSetResponse, PlayerResponse
from services import game_service

router = APIRouter(prefix="/api/game-sets", tags=["game-sets"])


@router.post("", response_model=GameSetResponse, status_code=201)
def create_game_set(game_set_data: GameSetCreate, db: Session = Depends(get_db)):
    """Create a new game set."""
    game_set = GameSet(
        num_players=game_set_data.num_players,
        selected_roles=game_set_data.selected_roles,
        discussion_timer_seconds=game_set_data.discussion_timer_seconds,
        created_by=game_set_data.created_by,
    )
    db.add(game_set)
    db.commit()
    db.refresh(game_set)
    return game_set


@router.get("/{game_set_id}", response_model=GameSetResponse)
def get_game_set(game_set_id: str, db: Session = Depends(get_db)):
    """Get a game set by ID."""
    game_set = db.query(GameSet).filter(GameSet.game_set_id == game_set_id).first()
    if not game_set:
        raise HTTPException(status_code=404, detail="Game set not found")
    return game_set


@router.post("/{game_set_id}/players/{player_id}/join")
def join_game_set(game_set_id: str, player_id: str, db: Session = Depends(get_db)):
    """Add a player to a game set."""
    # Check game set exists
    game_set = db.query(GameSet).filter(GameSet.game_set_id == game_set_id).first()
    if not game_set:
        raise HTTPException(status_code=404, detail="Game set not found")

    # Check player exists
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Check if player already joined
    if player in game_set.players:
        raise HTTPException(status_code=400, detail="Player already joined this game set")

    # Check if game set is full
    if len(game_set.players) >= game_set.num_players:
        raise HTTPException(status_code=400, detail="Game set is full")

    # Add player to game set
    game_set.players.append(player)
    db.commit()

    return {"status": "joined", "player_id": player_id, "game_set_id": game_set_id}


@router.get("/{game_set_id}/players")
def list_players(game_set_id: str, db: Session = Depends(get_db)):
    """List all players in a game set."""
    game_set = db.query(GameSet).filter(GameSet.game_set_id == game_set_id).first()
    if not game_set:
        raise HTTPException(status_code=404, detail="Game set not found")

    return {
        "players": [player.to_dict() for player in game_set.players],
        "current_count": len(game_set.players),
        "required_count": game_set.num_players
    }


@router.get("/{game_set_id}/active-game")
def get_active_game_endpoint(game_set_id: str, db: Session = Depends(get_db)):
    """Get the current active game for a game set, if one exists."""
    game_set = db.query(GameSet).filter(GameSet.game_set_id == game_set_id).first()
    if not game_set:
        raise HTTPException(status_code=404, detail="Game set not found")
    
    active_game = game_service.get_active_game(db, game_set_id)
    if not active_game:
        raise HTTPException(status_code=404, detail="No active game found")
    
    return active_game.to_dict()


@router.post("/{game_set_id}/start", status_code=201)
def start_game_endpoint(game_set_id: str, db: Session = Depends(get_db)):
    """Start a new game in a game set. Returns existing active game if one already exists."""
    try:
        game = game_service.start_game(db, game_set_id)
        return game.to_dict()
    except ValueError as e:
        # Convert ValueError from service to appropriate HTTP error
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
