"""API endpoints for games."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models.game import Game, GameState
from models.player_role import PlayerRole
from models.schemas import (
    NightStatusCompleteRequest,
    ViewCenterRequest,
    SeerActionRequest,
    RobberActionRequest,
    TroublemakerActionRequest,
    DrunkActionRequest,
)
from services import (
    game_service,
    night_service,
    werewolf_service,
    action_service,
    seer_service,
    robber_service,
    troublemaker_service,
    drunk_service,
    minion_service,
    mason_service,
    insomniac_service,
)

router = APIRouter(prefix="/api/games", tags=["games"])

@router.get("/{game_id}")
def get_game(game_id: str, db: Session = Depends(get_db)):
    """Get a game by ID."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check and advance simulated roles if needed (when in NIGHT state)
    if game.state == GameState.NIGHT:
        night_service.check_and_advance_simulated_role(db, game_id)
        db.refresh(game)
    
    return game.to_dict()


@router.get("/{game_id}/players/{player_id}/role")
def get_player_role(game_id: str, player_id: str, db: Session = Depends(get_db)):
    """Get a player's role in a specific game."""
    try:
        player_role = game_service.get_player_role(db, game_id, player_id)
        return player_role.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{game_id}/night-status")
def get_night_status(game_id: str, db: Session = Depends(get_db)):
    """Get the current night phase status."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.current_role_step is None and game.state == GameState.NIGHT:
        try:
            night_service.initialize_night_phase(db, game_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    try:
        # This will also check and advance simulated roles if needed
        return night_service.get_night_status(db, game_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{game_id}/night-status/complete")
def mark_night_role_complete(
    game_id: str,
    payload: NightStatusCompleteRequest,
    db: Session = Depends(get_db)
):
    """Mark a night role as complete and advance the wake order."""
    try:
        return night_service.mark_role_complete(db, game_id, payload.role)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _get_player_current_role(db: Session, game_id: str, player_id: str) -> str | None:
    pr = db.query(PlayerRole).filter(
        PlayerRole.game_id == game_id,
        PlayerRole.player_id == player_id
    ).first()
    return pr.current_role if pr else None


@router.get("/{game_id}/players/{player_id}/night-info")
def get_night_info(game_id: str, player_id: str, db: Session = Depends(get_db)):
    """Get role-specific night info for a player (Werewolf, Minion, Mason, Insomniac)."""
    role = _get_player_current_role(db, game_id, player_id)
    if not role:
        raise HTTPException(status_code=404, detail="Player not found in game")
    try:
        if role == "Werewolf":
            return werewolf_service.get_night_info(db, game_id, player_id)
        if role == "Minion":
            return minion_service.get_night_info(db, game_id, player_id)
        if role == "Mason":
            return mason_service.get_night_info(db, game_id, player_id)
        if role == "Insomniac":
            return insomniac_service.get_night_info(db, game_id, player_id)
        raise HTTPException(status_code=400, detail=f"Night info not available for role {role}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/view-center")
def view_center_card(
    game_id: str,
    player_id: str,
    payload: ViewCenterRequest,
    db: Session = Depends(get_db)
):
    """Lone werewolf views a center card."""
    try:
        return werewolf_service.view_center_card(db, game_id, player_id, payload.card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/acknowledge")
def acknowledge_night_info(game_id: str, player_id: str, db: Session = Depends(get_db)):
    """Acknowledge night info (Werewolf, Minion, Mason, Insomniac). Dispatches by current role step."""
    game = db.query(Game).filter(Game.game_id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    step = game.current_role_step
    try:
        if step == "Werewolf":
            return werewolf_service.acknowledge_werewolf(db, game_id, player_id)
        if step == "Minion":
            return minion_service.acknowledge_minion(db, game_id, player_id)
        if step == "Mason":
            return mason_service.acknowledge_mason(db, game_id, player_id)
        if step == "Insomniac":
            return insomniac_service.acknowledge_insomniac(db, game_id, player_id)
        raise HTTPException(status_code=400, detail=f"Acknowledge not applicable for role step {step}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{game_id}/players/{player_id}/available-actions")
def get_available_actions(game_id: str, player_id: str, db: Session = Depends(get_db)):
    """Get which players/center cards are actionable for the current player."""
    try:
        return action_service.get_available_actions(db, game_id, player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{game_id}/players/{player_id}/actions")
def get_player_actions(game_id: str, player_id: str, db: Session = Depends(get_db)):
    """Get all accrued actions visible to the player."""
    try:
        return action_service.get_player_actions(db, game_id, player_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{game_id}/players/{player_id}/seer-action")
def perform_seer_action(
    game_id: str,
    player_id: str,
    payload: SeerActionRequest,
    db: Session = Depends(get_db)
):
    """Perform Seer action: view one player OR view two center cards."""
    try:
        return seer_service.perform_seer_action(
            db,
            game_id,
            player_id,
            payload.action_type,
            payload.target_player_id,
            payload.card_indices
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/robber-action")
def perform_robber_action(
    game_id: str,
    player_id: str,
    payload: RobberActionRequest,
    db: Session = Depends(get_db)
):
    """Perform Robber action: exchange cards with another player and view new role."""
    try:
        return robber_service.perform_robber_action(
            db,
            game_id,
            player_id,
            payload.target_player_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/troublemaker-action")
def perform_troublemaker_action(
    game_id: str,
    player_id: str,
    payload: TroublemakerActionRequest,
    db: Session = Depends(get_db)
):
    """Perform Troublemaker action: swap two other players' cards (no looking)."""
    try:
        return troublemaker_service.perform_troublemaker_action(
            db, game_id, player_id, payload.player1_id, payload.player2_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{game_id}/players/{player_id}/drunk-action")
def perform_drunk_action(
    game_id: str,
    player_id: str,
    payload: DrunkActionRequest,
    db: Session = Depends(get_db)
):
    """Perform Drunk action: swap with a center card (no looking)."""
    try:
        return drunk_service.perform_drunk_action(db, game_id, player_id, payload.card_index)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
