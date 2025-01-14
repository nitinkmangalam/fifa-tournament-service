from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator


# Enums for validation
class MatchType(str, Enum):
    ONE_V_ONE = "1v1"
    TWO_V_TWO = "2v2"


class MatchStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class MatchResult(str, Enum):
    TEAM1 = "Team1"
    TEAM2 = "Team2"
    DRAW = "Draw"


# Player models
class PlayerBase(BaseModel):
    player_name: str


class PlayerCreate(PlayerBase):
    pass


class Player(PlayerBase):
    player_id: int
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    clean_sheets: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Match models
class MatchBase(BaseModel):
    round: str
    match_type: MatchType
    team1_player1_id: int
    team1_player2_id: Optional[int] = None
    team2_player1_id: int
    team2_player2_id: Optional[int] = None
    match_date: datetime
    scheduled_date: Optional[datetime] = None

    @field_validator("team1_player2_id", "team2_player2_id")
    @classmethod
    def validate_2v2_players(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        if "match_type" in info.data:
            if info.data["match_type"] == MatchType.TWO_V_TWO and v is None:
                raise ValueError("2v2 matches require both players for each team")
            if info.data["match_type"] == MatchType.ONE_V_ONE and v is not None:
                raise ValueError("1v1 matches should not have second players")
        return v


class ScheduledMatch(MatchBase):
    status: MatchStatus = MatchStatus.SCHEDULED


class CompletedMatch(MatchBase):
    team1_goals: int
    team2_goals: int
    status: MatchStatus = MatchStatus.COMPLETED

    @field_validator("team1_goals", "team2_goals")
    @classmethod
    def validate_goals(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Goals cannot be negative")
        return v


class MatchCreate(BaseModel):
    round: str
    match_type: MatchType
    team1_player1_id: int
    team1_player2_id: Optional[int] = None
    team2_player1_id: int
    team2_player2_id: Optional[int] = None
    match_date: datetime
    scheduled_date: Optional[datetime] = None
    team1_goals: Optional[int] = None
    team2_goals: Optional[int] = None
    status: Optional[MatchStatus] = None

    model_config = ConfigDict(extra="allow")

    @field_validator("team1_player2_id", "team2_player2_id")
    @classmethod
    def validate_2v2_players(cls, v: Optional[int], info: ValidationInfo) -> Optional[int]:
        if "match_type" in info.data:
            if info.data["match_type"] == MatchType.TWO_V_TWO and v is None:
                raise ValueError("2v2 matches require both players for each team")
            if info.data["match_type"] == MatchType.ONE_V_ONE and v is not None:
                raise ValueError("1v1 matches should not have second players")
        return v

    @field_validator("scheduled_date")
    @classmethod
    def set_scheduled_date(cls, v: Optional[datetime], info: ValidationInfo) -> datetime:
        return v or info.data.get("match_date")

    @field_validator("match_date")
    @classmethod
    def validate_match_date(cls, v: datetime) -> datetime:
        if v < datetime.now():
            raise ValueError("Match date cannot be in the past")
        return v

    @field_validator("status")
    @classmethod
    def determine_status_from_goals(cls, v: Optional[MatchStatus], info: ValidationInfo) -> MatchStatus:
        has_goals = (
            "team1_goals" in info.data
            and "team2_goals" in info.data
            and info.data["team1_goals"] is not None
            and info.data["team2_goals"] is not None
        )
        return MatchStatus.COMPLETED if has_goals else MatchStatus.SCHEDULED

    @field_validator("team1_goals", "team2_goals")
    @classmethod
    def validate_goals(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Goals cannot be negative")
        return v

    def dict(self, *args, **kwargs):
        data = super().dict(*args, **kwargs)
        has_goals = data.get("team1_goals") is not None and data.get("team2_goals") is not None
        data["status"] = MatchStatus.COMPLETED if has_goals else MatchStatus.SCHEDULED
        return data


class Match(BaseModel):
    id: int
    round: str
    match_type: MatchType
    team1_player1_id: int
    team1_player2_id: Optional[int] = None
    team2_player1_id: int
    team2_player2_id: Optional[int] = None
    match_date: datetime
    scheduled_date: datetime
    team1_goals: Optional[int] = None
    team2_goals: Optional[int] = None
    status: MatchStatus
    result: Optional[MatchResult] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Match Statistics model
class MatchStats(BaseModel):
    id: int
    match_id: int
    player_id: int
    goals: int = 0
    clean_sheet: bool = False
    points: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Update Score model
class ScoreUpdate(BaseModel):
    team1_goals: int
    team2_goals: int

    @field_validator("team1_goals", "team2_goals")
    @classmethod
    def validate_goals(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Goals cannot be negative")
        return v
