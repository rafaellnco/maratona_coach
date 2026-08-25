"""Endpoints auxiliares para consulta de estado (debug/admin)."""

from datetime import date

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.database import get_session
from app.schemas import DailyLogRead, TrainingSessionRead, UserProfileRead
from app.services.training_service import (
    format_week_plan,
    get_current_training_week,
    get_or_create_daily_log,
    get_primary_user,
    get_today_sessions,
    get_user_goal,
    get_week_sessions,
)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/profile", response_model=UserProfileRead)
def get_profile(session: Session = Depends(get_session)) -> UserProfileRead:
    user = get_primary_user(session)
    return UserProfileRead(
        name=user.name,
        age=user.age,
        gender=user.gender.value,
        weight_kg=user.weight_kg,
        height_m=user.height_m,
        is_smoker=user.is_smoker,
        injury_notes=user.injury_notes,
    )


@router.get("/today")
def get_today(session: Session = Depends(get_session)) -> dict:
    user = get_primary_user(session)
    week = get_current_training_week(session)
    sessions = get_today_sessions(session)
    log = get_or_create_daily_log(session, user.id)  # type: ignore[arg-type]
    goal = get_user_goal(session, user.id)  # type: ignore[arg-type]

    return {
        "date": str(date.today()),
        "goal": goal.title if goal else None,
        "week_number": week.week_number if week else None,
        "sessions": [
            TrainingSessionRead(
                weekday=s.weekday.value,
                session_type=s.session_type.value,
                title=s.title,
                description=s.description,
                target_distance_km=s.target_distance_km,
                target_duration_min=s.target_duration_min,
                target_pace_per_km=s.target_pace_per_km,
            )
            for s in sessions
        ],
        "daily_log": DailyLogRead(
            log_date=log.log_date,
            water_liters=log.water_liters,
            water_target_liters=log.water_target_liters,
            magnesium_taken=log.magnesium_taken,
            omega3_taken=log.omega3_taken,
            creatine_taken=log.creatine_taken,
            training_completed=log.training_completed,
            training_distance_km=log.training_distance_km,
            knee_pain_level=log.knee_pain_level,
            notes=log.notes,
        ),
    }


@router.get("/week-plan")
def get_week_plan(session: Session = Depends(get_session)) -> dict:
    week = get_current_training_week(session)
    if not week:
        return {"message": "Sem plano para a data actual."}
    sessions = get_week_sessions(session, week.id)  # type: ignore[arg-type]
    return {
        "week_number": week.week_number,
        "start_date": str(week.start_date),
        "end_date": str(week.end_date),
        "formatted": format_week_plan(session, week),
        "sessions_count": len(sessions),
    }
