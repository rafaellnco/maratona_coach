from datetime import date, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str


class WhatsAppGenericPayload(BaseModel):
    """Payload genérico para integrações WhatsApp."""

    from_number: str = Field(..., alias="from")
    to_number: str | None = Field(default=None, alias="to")
    body: str
    message_id: str | None = None
    timestamp: datetime | None = None

    model_config = {"populate_by_name": True}


class TwilioWhatsAppPayload(BaseModel):
    """Payload Twilio WhatsApp webhook."""

    MessageSid: str | None = None
    AccountSid: str | None = None
    From: str
    To: str | None = None
    Body: str
    NumMedia: str | None = None


class CoachResponse(BaseModel):
    reply: str
    daily_log_updated: bool = False
    tools_executed: list[str] = Field(default_factory=list)


class DailyLogRead(BaseModel):
    log_date: date
    water_liters: float | None
    water_target_liters: float | None
    magnesium_taken: bool | None
    omega3_taken: bool | None
    creatine_taken: bool | None
    training_completed: bool | None
    training_distance_km: float | None
    knee_pain_level: int | None
    notes: str | None


class TrainingSessionRead(BaseModel):
    weekday: int
    session_type: str
    title: str
    description: str
    target_distance_km: float | None
    target_duration_min: int | None
    target_pace_per_km: str | None


class UserProfileRead(BaseModel):
    name: str
    age: int
    gender: str
    weight_kg: float
    height_m: float
    is_smoker: bool
    injury_notes: str | None


class SimulatedNotification(BaseModel):
    notification_type: str
    message: str
    scheduled_for: datetime
    delivery_status: str
