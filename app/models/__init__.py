from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SessionType(str, Enum):
    FOOTBALL = "football"
    RUN_SPECIFIC = "run_specific"
    STRENGTH_MOBILITY = "strength_mobility"
    LONG_RUN = "long_run"
    REST = "rest"
    RACE = "race"


class Weekday(int, Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="Atleta")
    age: int
    gender: Gender
    weight_kg: float
    height_m: float
    is_smoker: bool = Field(default=False)
    injury_notes: str | None = Field(default=None)
    phone_number: str | None = Field(default=None, index=True)
    telegram_chat_id: str | None = Field(default=None, index=True)
    telegram_user_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    goal: Optional["Goal"] = Relationship(back_populates="user")
    daily_logs: list["DailyLog"] = Relationship(back_populates="user")
    messages: list["ConversationMessage"] = Relationship(back_populates="user")


class Goal(SQLModel, table=True):
    __tablename__ = "goals"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    title: str
    target_date: date
    target_time_seconds: int | None = Field(default=None)
    target_pace_per_km_seconds: int | None = Field(default=None)
    distance_km: float = Field(default=21.097)
    description: str | None = Field(default=None)

    user: Optional[User] = Relationship(back_populates="goal")


class TrainingPhase(SQLModel, table=True):
    __tablename__ = "training_phases"

    id: int | None = Field(default=None, primary_key=True)
    name: str
    phase_number: int = Field(index=True)
    start_date: date
    end_date: date
    focus: str
    description: str | None = Field(default=None)

    weeks: list["TrainingWeek"] = Relationship(back_populates="phase")


class TrainingWeek(SQLModel, table=True):
    __tablename__ = "training_weeks"

    id: int | None = Field(default=None, primary_key=True)
    phase_id: int = Field(foreign_key="training_phases.id", index=True)
    week_number: int = Field(index=True)
    start_date: date
    end_date: date
    notes: str | None = Field(default=None)

    phase: Optional["TrainingPhase"] = Relationship(back_populates="weeks")
    sessions: list["TrainingSession"] = Relationship(back_populates="week")


class TrainingSession(SQLModel, table=True):
    __tablename__ = "training_sessions"

    id: int | None = Field(default=None, primary_key=True)
    week_id: int = Field(foreign_key="training_weeks.id", index=True)
    weekday: Weekday
    session_type: SessionType
    title: str
    description: str
    target_distance_km: float | None = Field(default=None)
    target_duration_min: int | None = Field(default=None)
    target_pace_per_km: str | None = Field(default=None)
    is_key_session: bool = Field(default=False)
    sort_order: int = Field(default=0)

    week: Optional["TrainingWeek"] = Relationship(back_populates="sessions")


class DailyLog(SQLModel, table=True):
    __tablename__ = "daily_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    log_date: date = Field(index=True)
    water_liters: float | None = Field(default=None)
    water_target_liters: float | None = Field(default=None)
    magnesium_taken: bool | None = Field(default=None)
    omega3_taken: bool | None = Field(default=None)
    creatine_taken: bool | None = Field(default=None)
    creatine_grams: float | None = Field(default=None)
    training_completed: bool | None = Field(default=None)
    training_distance_km: float | None = Field(default=None)
    training_duration_min: int | None = Field(default=None)
    training_notes: str | None = Field(default=None)
    knee_pain_level: int | None = Field(default=None, ge=0, le=10)
    smoked_today: bool | None = Field(default=None)
    smoked_near_training: bool | None = Field(default=None)
    sleep_hours: float | None = Field(default=None)
    weight_kg: float | None = Field(default=None)
    notes: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="daily_logs")


class ConversationMessage(SQLModel, table=True):
    __tablename__ = "conversation_messages"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    metadata_json: str | None = Field(default=None)

    user: Optional[User] = Relationship(back_populates="messages")


class NotificationLog(SQLModel, table=True):
    __tablename__ = "notification_logs"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    notification_type: str = Field(index=True)
    scheduled_for: datetime
    sent_at: datetime | None = Field(default=None)
    message_content: str
    delivery_status: str = Field(default="simulated")
    created_at: datetime = Field(default_factory=datetime.utcnow)
