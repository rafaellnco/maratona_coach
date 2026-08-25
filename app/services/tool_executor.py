"""Execução de tools de tracking sobre o daily log."""

from datetime import date, datetime
from typing import Any

from sqlmodel import Session

from app.services.claude_tools import parse_log_date
from app.services.training_service import (
    get_or_create_daily_log,
    is_training_day,
    query_training_plan,
)

_NULLISH = frozenset({"null", "none", ""})
_FLOAT_FIELDS = frozenset(
    {
        "water_liters",
        "creatine_grams",
        "training_distance_km",
        "training_duration_min",
        "sleep_hours",
        "weight_kg",
    }
)
_INT_FIELDS = frozenset({"knee_pain_level"})


def _coerce_tool_value(field: str, value: Any) -> Any | None:
    """Ignora null JSON serializado como string e normaliza tipos numéricos."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.lower() in _NULLISH:
            return None
        if field in _FLOAT_FIELDS:
            try:
                return float(stripped)
            except ValueError:
                return None
        if field in _INT_FIELDS:
            try:
                return int(float(stripped))
            except ValueError:
                return None
        return stripped
    return value


def apply_daily_log_update(
    session: Session,
    user_id: int,
    tool_input: dict[str, Any],
) -> dict[str, Any]:
    log_date = parse_log_date(tool_input.get("log_date"))
    log = get_or_create_daily_log(session, user_id, log_date)

    if log.water_target_liters is None:
        log.water_target_liters = 3.5 if is_training_day(session, log_date) else 2.5

    field_map: dict[str, str] = {
        "water_liters": "water_liters",
        "magnesium_taken": "magnesium_taken",
        "omega3_taken": "omega3_taken",
        "creatine_taken": "creatine_taken",
        "creatine_grams": "creatine_grams",
        "training_completed": "training_completed",
        "training_distance_km": "training_distance_km",
        "training_duration_min": "training_duration_min",
        "training_notes": "training_notes",
        "knee_pain_level": "knee_pain_level",
        "smoked_today": "smoked_today",
        "smoked_near_training": "smoked_near_training",
        "sleep_hours": "sleep_hours",
        "weight_kg": "weight_kg",
        "notes": "notes",
    }

    updated_fields: list[str] = []
    for input_key, model_attr in field_map.items():
        if input_key not in tool_input:
            continue
        coerced = _coerce_tool_value(input_key, tool_input[input_key])
        if coerced is not None:
            setattr(log, model_attr, coerced)
            updated_fields.append(input_key)

    log.updated_at = datetime.utcnow()
    session.add(log)
    session.flush()

    return {
        "success": True,
        "log_date": str(log_date),
        "updated_fields": updated_fields,
        "current_log": {
            "water_liters": log.water_liters,
            "water_target_liters": log.water_target_liters,
            "magnesium_taken": log.magnesium_taken,
            "omega3_taken": log.omega3_taken,
            "creatine_taken": log.creatine_taken,
            "training_completed": log.training_completed,
            "training_distance_km": log.training_distance_km,
            "knee_pain_level": log.knee_pain_level,
        },
    }


def get_training_plan(session: Session, tool_input: dict[str, Any]) -> dict[str, Any]:
    scope = tool_input.get("scope", "current_week")
    return query_training_plan(
        session,
        scope=str(scope),
        week_number=tool_input.get("week_number"),
        phase_number=tool_input.get("phase_number"),
        weeks_ahead=int(tool_input.get("weeks_ahead") or 2),
        detail_level=str(tool_input.get("detail_level") or "summary"),
    )


def execute_tool(
    session: Session,
    user_id: int,
    tool_name: str,
    tool_input: dict[str, Any],
) -> dict[str, Any]:
    if tool_name == "update_daily_log":
        return apply_daily_log_update(session, user_id, tool_input)
    if tool_name == "get_training_plan":
        return get_training_plan(session, tool_input)
    return {"success": False, "error": f"Tool desconhecida: {tool_name}"}
