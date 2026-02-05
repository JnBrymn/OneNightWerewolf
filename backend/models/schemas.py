from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime


class PlayerCreate(BaseModel):
    """Schema for creating a new player."""
    player_name: str = Field(..., min_length=1, max_length=50, description="Player name")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    user_id: Optional[str] = Field(None, description="User/session ID")


class PlayerResponse(BaseModel):
    """Schema for player API responses."""
    model_config = ConfigDict(from_attributes=True)

    player_id: str
    user_id: Optional[str]
    player_name: str
    avatar_url: Optional[str]
    created_at: Optional[datetime]


class GameSetCreate(BaseModel):
    """Schema for creating a new game set."""
    num_players: int = Field(..., ge=3, le=10, description="Number of players (3-10)")
    selected_roles: List[str] = Field(..., min_length=1, description="List of role names")
    discussion_timer_seconds: int = Field(default=300, ge=60, le=600, description="Discussion time limit in seconds")
    created_by: Optional[str] = Field(None, description="Creator user/session ID")

    @field_validator('selected_roles')
    @classmethod
    def validate_role_count(cls, v, info):
        """Ensure number of cards = number of players + 3."""
        num_players = info.data.get('num_players')
        if num_players and len(v) != num_players + 3:
            raise ValueError(f'Number of roles must equal num_players + 3 (expected {num_players + 3}, got {len(v)})')
        return v

    @field_validator('selected_roles')
    @classmethod
    def validate_roles(cls, v):
        """Ensure all roles are valid."""
        valid_roles = {
            'Werewolf', 'Villager', 'Seer', 'Robber', 'Troublemaker',
            'Drunk', 'Insomniac', 'Minion', 'Mason', 'Tanner', 'Hunter'
        }
        for role in v:
            if role not in valid_roles:
                raise ValueError(f'Invalid role: {role}')
        return v


class GameSetResponse(BaseModel):
    """Schema for game set API responses."""
    model_config = ConfigDict(from_attributes=True)

    game_set_id: str
    created_by: Optional[str]
    num_players: int
    selected_roles: List[str]
    discussion_timer_seconds: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    ended_at: Optional[datetime]


class NightStatusCompleteRequest(BaseModel):
    """Schema for marking a night role complete."""
    role: str = Field(..., min_length=1, description="Role name to mark complete")


class ViewCenterRequest(BaseModel):
    """Schema for viewing a center card (lone werewolf)."""
    card_index: int = Field(..., ge=0, le=2, description="Center card index (0-2)")
