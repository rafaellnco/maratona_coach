"""Testes básicos do Maratona Coach."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.main import app
from app.models import Goal, TrainingWeek, User
from app.seed.initial_data import PLAN_START, RACE_DATE, TOTAL_WEEKS, seed_database


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_seed_data(session: Session):
    user = session.exec(select(User)).first()
    assert user is not None
    assert user.age == 24
    assert user.is_smoker is True

    goal = session.exec(select(Goal)).first()
    assert goal is not None
    assert goal.target_date == RACE_DATE

    weeks = session.exec(select(TrainingWeek)).all()
    assert len(weeks) == TOTAL_WEEKS
    assert weeks[0].start_date == PLAN_START


def test_today_endpoint(client: TestClient):
    response = client.get("/api/today")
    assert response.status_code == 200
    data = response.json()
    assert "daily_log" in data
    assert "sessions" in data


def test_webhook_demo_mode(client: TestClient):
    response = client.post(
        "/webhook/whatsapp",
        json={"from": "whatsapp:+351912345678", "body": "olá"},
    )
    assert response.status_code == 200
    assert len(response.json()["reply"]) > 0


def test_tool_executor(session: Session):
    from app.services.tool_executor import execute_tool
    from app.services.training_service import get_primary_user, get_or_create_daily_log

    user = get_primary_user(session)
    result = execute_tool(
        session,
        user.id,  # type: ignore[arg-type]
        "update_daily_log",
        {
            "training_distance_km": 10.0,
            "training_completed": True,
            "magnesium_taken": True,
        },
    )
    assert result["success"] is True
    log = get_or_create_daily_log(session, user.id)  # type: ignore[arg-type]
    assert log.training_distance_km == 10.0
    assert log.magnesium_taken is True


def test_tool_executor_ignores_null_string(session: Session):
    from app.services.tool_executor import execute_tool
    from app.services.training_service import get_primary_user, get_or_create_daily_log

    user = get_primary_user(session)
    log = get_or_create_daily_log(session, user.id)  # type: ignore[arg-type]
    log.sleep_hours = 7.5
    session.add(log)
    session.commit()

    result = execute_tool(
        session,
        user.id,  # type: ignore[arg-type]
        "update_daily_log",
        {"sleep_hours": "null", "notes": "paintball amanhã"},
    )
    assert result["success"] is True
    assert "sleep_hours" not in result["updated_fields"]
    assert "notes" in result["updated_fields"]

    session.refresh(log)
    assert log.sleep_hours == 7.5
    assert log.notes == "paintball amanhã"


def test_get_training_plan_tool(session: Session):
    from app.services.tool_executor import execute_tool
    from app.services.training_service import get_primary_user

    user = get_primary_user(session)

    full = execute_tool(
        session,
        user.id,  # type: ignore[arg-type]
        "get_training_plan",
        {"scope": "full", "detail_level": "summary"},
    )
    assert full["success"] is True
    assert full["total_weeks"] == 14
    assert "PLANO COMPLETO" in full["plan"]

    week8 = execute_tool(
        session,
        user.id,  # type: ignore[arg-type]
        "get_training_plan",
        {"scope": "week", "week_number": 8, "detail_level": "detailed"},
    )
    assert week8["success"] is True
    assert week8["week_number"] == 8
    assert "Longão" in week8["plan"] or "Intervalos" in week8["plan"]

    phase2 = execute_tool(
        session,
        user.id,  # type: ignore[arg-type]
        "get_training_plan",
        {"scope": "phase", "phase_number": 2},
    )
    assert phase2["success"] is True
    assert "Construção" in phase2["plan"]


def test_week_plan_endpoint(client: TestClient):
    response = client.get("/api/week-plan")
    assert response.status_code == 200
    # Pode estar fora do plano se data actual != Jun-Set 2026
    data = response.json()
    assert "formatted" in data or "message" in data


def test_telegram_parse_update():
    from app.services.telegram_service import TelegramService

    service = TelegramService()
    incoming = service.parse_update(
        {
            "update_id": 1,
            "message": {
                "message_id": 10,
                "from": {"id": 999, "first_name": "Rafael", "is_bot": False},
                "chat": {"id": 999, "type": "private"},
                "text": "corri 10km",
            },
        }
    )
    assert incoming is not None
    assert incoming.chat_id == "999"
    assert incoming.text == "corri 10km"


def test_telegram_sanitize():
    from app.services.telegram_service import TelegramService

    text = TelegramService.sanitize_text("**Olá** treino `hoje`")
    assert "**" not in text
    assert "Olá" in text


def test_telegram_webhook_start(client: TestClient, monkeypatch):
    sent: list[tuple[str, str]] = []

    async def fake_send(self, chat_id: str, text: str) -> bool:
        sent.append((chat_id, text))
        return True

    monkeypatch.setenv("TELEGRAM_ALLOWED_USER_ID", "")
    from app.config import get_settings

    get_settings.cache_clear()

    monkeypatch.setattr(
        "app.services.telegram_service.TelegramService.send_message",
        fake_send,
    )

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 1,
            "message": {
                "message_id": 1,
                "from": {"id": 12345, "first_name": "Rafael"},
                "chat": {"id": 12345, "type": "private"},
                "text": "/start",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert len(sent) == 1
    assert "Maratona Coach" in sent[0][1]


def test_telegram_mode_auto_polling():
    from app.config import Settings

    settings = Settings(
        telegram_mode="auto",
        public_base_url="",
        telegram_webhook_url="",
    )
    assert settings.resolved_telegram_mode == "polling"
    assert settings.telegram_webhook_url_resolved == ""


def test_telegram_mode_webhook_from_public_base_url():
    from app.config import Settings

    settings = Settings(
        telegram_mode="auto",
        public_base_url="https://abc.justrunmy.app/",
        telegram_webhook_url="",
    )
    assert settings.resolved_telegram_mode == "webhook"
    assert settings.telegram_webhook_url_resolved == "https://abc.justrunmy.app/webhook/telegram"
