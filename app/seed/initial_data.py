"""Popula a base de dados com perfil, meta e plano de treino de 14 semanas."""

from datetime import date, timedelta

from sqlmodel import Session, select

from app.models import (
    Gender,
    Goal,
    SessionType,
    TrainingPhase,
    TrainingSession,
    TrainingWeek,
    User,
    Weekday,
)

PLAN_START = date(2026, 6, 8)
RACE_DATE = date(2026, 9, 13)
TOTAL_WEEKS = 14

PHASES: list[dict[str, object]] = [
    {
        "name": "Fase 1 — Base",
        "phase_number": 1,
        "weeks": (1, 4),
        "focus": "Construir base aeróbica e adaptação articular",
        "description": "Volume moderado, ritmos confortáveis, foco em consistência.",
    },
    {
        "name": "Fase 2 — Construção",
        "phase_number": 2,
        "weeks": (5, 8),
        "focus": "Aumentar volume e introduzir estímulos de ritmo",
        "description": "Longões progressivos, treinos de limiar e intervalos curtos.",
    },
    {
        "name": "Fase 3 — Pico",
        "phase_number": 3,
        "weeks": (9, 12),
        "focus": "Simular condições de prova e consolidar ritmo-alvo",
        "description": "Volume máximo controlado, treinos a ritmo de meia (5:40/km).",
    },
    {
        "name": "Fase 4 — Tapering",
        "phase_number": 4,
        "weeks": (13, 14),
        "focus": "Reduzir fadiga e chegar fresco à prova",
        "description": "Descarga progressiva mantendo estímulos curtos de qualidade.",
    },
]

WEEKDAY_NAMES = {
    Weekday.MONDAY: "Segunda",
    Weekday.WEDNESDAY: "Quarta",
    Weekday.THURSDAY: "Quinta",
    Weekday.SATURDAY: "Sábado",
}


def _week_start(week_number: int) -> date:
    return PLAN_START + timedelta(weeks=week_number - 1)


def _long_run_km(week_number: int) -> float:
    progression = {
        1: 8.0,
        2: 10.0,
        3: 12.0,
        4: 14.0,
        5: 15.0,
        6: 16.0,
        7: 17.0,
        8: 18.0,
        9: 18.0,
        10: 19.0,
        11: 20.0,
        12: 21.0,
        13: 14.0,
        14: 10.0,
    }
    return progression[week_number]


def _wednesday_session(week_number: int) -> dict[str, object]:
    if week_number <= 4:
        templates = {
            1: ("Corrida Fácil", "45 min em ritmo conversacional (6:30-7:00/km)", 6.0, 45, "6:30-7:00"),
            2: ("Corrida Fácil + Strides", "40 min fácil + 4x20s acelerações", 7.0, 45, "6:30-7:00"),
            3: ("Corrida Moderada", "50 min progressivo nos últimos 15 min", 8.0, 50, "6:15-6:45"),
            4: ("Fartlek Leve", "45 min com 6 blocos de 2 min moderado", 8.0, 50, "6:00-6:45"),
        }
    elif week_number <= 8:
        templates = {
            5: ("Tempo Run", "15 min aquecimento + 20 min a 6:00/km + 10 min descanso", 9.0, 55, "6:00"),
            6: ("Intervalos Curtos", "2 km aquec. + 6x800m a 5:30/km (rec. 90s) + 1 km descanso", 10.0, 60, "5:30-6:30"),
            7: ("Limiar", "15 min aquec. + 25 min contínuos a 5:50/km + 10 min descanso", 10.0, 55, "5:50"),
            8: ("Intervalos Médios", "2 km aquec. + 4x1.6km a 5:40/km (rec. 2 min) + 1.5 km descanso", 11.0, 65, "5:40-6:30"),
        }
    elif week_number <= 12:
        templates = {
            9: ("Ritmo de Prova", "15 min aquec. + 3x2km a 5:40/km (rec. 2 min) + 10 min descanso", 12.0, 60, "5:40"),
            10: ("Tempo Longo", "20 min aquec. + 30 min a 5:50/km + 10 min descanso", 12.0, 65, "5:50"),
            11: ("Simulação Prova", "15 min aquec. + 8km a 5:40/km + 10 min descanso", 13.0, 70, "5:40"),
            12: ("Último Estímulo", "15 min aquec. + 5km a 5:35/km + 10 min descanso", 11.0, 55, "5:35-6:00"),
        }
    else:
        templates = {
            13: ("Ativação", "30 min fácil + 4x1 min a 5:30/km", 6.0, 40, "6:00-5:30"),
            14: ("Shake-out Pré-Prova", "20 min muito leve + 3 strides — descanso amanhã", 4.0, 25, "7:00"),
        }
    title, desc, dist, dur, pace = templates[week_number]
    return {
        "title": title,
        "description": desc,
        "target_distance_km": dist,
        "target_duration_min": dur,
        "target_pace_per_km": pace,
        "is_key_session": week_number >= 9,
    }


def _build_week_sessions(week_number: int) -> list[dict[str, object]]:
    wed = _wednesday_session(week_number)
    long_km = _long_run_km(week_number)

    sessions: list[dict[str, object]] = [
        {
            "weekday": Weekday.MONDAY,
            "session_type": SessionType.FOOTBALL,
            "title": "Futebol",
            "description": "Jogo de futebol 5-6 km equivalente. Hidratação extra. Sem fumar 2h antes/depois.",
            "target_distance_km": 5.5,
            "target_duration_min": 60,
            "target_pace_per_km": None,
            "is_key_session": False,
            "sort_order": 1,
        },
        {
            "weekday": Weekday.WEDNESDAY,
            "session_type": SessionType.RUN_SPECIFIC,
            "title": str(wed["title"]),
            "description": str(wed["description"]),
            "target_distance_km": float(wed["target_distance_km"]),  # type: ignore[arg-type]
            "target_duration_min": int(wed["target_duration_min"]),  # type: ignore[arg-type]
            "target_pace_per_km": str(wed["target_pace_per_km"]),
            "is_key_session": bool(wed["is_key_session"]),
            "sort_order": 2,
        },
        {
            "weekday": Weekday.THURSDAY,
            "session_type": SessionType.STRENGTH_MOBILITY,
            "title": "Força & Mobilidade",
            "description": (
                "20-25 min: agachamentos, pontes glúteo, prancha, mobilidade ancas/joelhos. "
                "Wall Sit 3x30-45s se joelhos estiverem bem."
            ),
            "target_distance_km": None,
            "target_duration_min": 25,
            "target_pace_per_km": None,
            "is_key_session": False,
            "sort_order": 3,
        },
        {
            "weekday": Weekday.SATURDAY,
            "session_type": SessionType.LONG_RUN,
            "title": f"Longão — {long_km:.0f} km",
            "description": (
                f"Longão de {long_km:.0f} km em ritmo fácil-moderado (6:15-6:45/km). "
                "Nutrição durante se >90 min."
            ),
            "target_distance_km": long_km,
            "target_duration_min": int(long_km * 6.5),
            "target_pace_per_km": "6:15-6:45",
            "is_key_session": week_number >= 5,
            "sort_order": 4,
        },
    ]

    if week_number == TOTAL_WEEKS:
        sessions.append(
            {
                "weekday": Weekday.SUNDAY,
                "session_type": SessionType.RACE,
                "title": "🏁 Meia Maratona",
                "description": "Prova principal! Ritmo-alvo 5:40/km (< 2h). Estratégia: conservador nos primeiros 10 km.",
                "target_distance_km": 21.097,
                "target_duration_min": 115,
                "target_pace_per_km": "5:40",
                "is_key_session": True,
                "sort_order": 5,
            }
        )

    return sessions


def seed_database(session: Session) -> None:
    existing = session.exec(select(User)).first()
    if existing:
        return

    user = User(
        name="Atleta",
        age=24,
        gender=Gender.MALE,
        weight_kg=60.0,
        height_m=1.69,
        is_smoker=True,
        injury_notes="Dores esporádicas nos joelhos. Monitorizar intensidade e volume.",
        phone_number=None,
    )
    session.add(user)
    session.flush()

    goal = Goal(
        user_id=user.id,  # type: ignore[arg-type]
        title="Meia Maratona sub-2h",
        target_date=RACE_DATE,
        target_time_seconds=7200,
        target_pace_per_km_seconds=340,
        distance_km=21.097,
        description="Meia Maratona com ritmo-alvo 5:40/km, prova a 13 de Setembro de 2026.",
    )
    session.add(goal)

    phase_records: dict[int, TrainingPhase] = {}
    for phase_def in PHASES:
        week_start_num, week_end_num = phase_def["weeks"]  # type: ignore[misc]
        phase = TrainingPhase(
            name=str(phase_def["name"]),
            phase_number=int(phase_def["phase_number"]),  # type: ignore[arg-type]
            start_date=_week_start(int(week_start_num)),  # type: ignore[arg-type]
            end_date=_week_start(int(week_end_num)) + timedelta(days=6),  # type: ignore[arg-type]
            focus=str(phase_def["focus"]),
            description=str(phase_def["description"]),
        )
        session.add(phase)
        session.flush()
        phase_records[int(phase_def["phase_number"])] = phase  # type: ignore[arg-type]

    for week_number in range(1, TOTAL_WEEKS + 1):
        phase_number = 1 if week_number <= 4 else 2 if week_number <= 8 else 3 if week_number <= 12 else 4
        start = _week_start(week_number)
        end = start + timedelta(days=6)

        week = TrainingWeek(
            phase_id=phase_records[phase_number].id,  # type: ignore[arg-type]
            week_number=week_number,
            start_date=start,
            end_date=end,
            notes=f"Semana {week_number} — {phase_records[phase_number].name}",
        )
        session.add(week)
        session.flush()

        for session_data in _build_week_sessions(week_number):
            training_session = TrainingSession(week_id=week.id, **session_data)  # type: ignore[arg-type]
            session.add(training_session)

    session.commit()
