"""Serviços de acesso a dados de treino, logs e conversas."""

from datetime import date, datetime, timedelta

from sqlmodel import Session, col, select

from app.models import (
    ConversationMessage,
    DailyLog,
    Goal,
    MessageRole,
    SessionType,
    TrainingPhase,
    TrainingSession,
    TrainingWeek,
    User,
    Weekday,
)


def get_primary_user(session: Session) -> User:
    user = session.exec(select(User)).first()
    if not user:
        raise RuntimeError("Utilizador não encontrado. Execute o seed da base de dados.")
    return user


def link_telegram_user(
    session: Session,
    user: User,
    chat_id: str,
    telegram_user_id: str,
    first_name: str | None = None,
) -> User:
    user.telegram_chat_id = chat_id
    user.telegram_user_id = telegram_user_id
    if first_name and user.name == "Atleta":
        user.name = first_name
    session.add(user)
    session.flush()
    return user


def get_user_goal(session: Session, user_id: int) -> Goal | None:
    return session.exec(select(Goal).where(Goal.user_id == user_id)).first()


def get_current_training_week(session: Session, reference_date: date | None = None) -> TrainingWeek | None:
    ref = reference_date or date.today()
    return session.exec(
        select(TrainingWeek)
        .where(TrainingWeek.start_date <= ref)
        .where(TrainingWeek.end_date >= ref)
        .order_by(col(TrainingWeek.week_number))
    ).first()


def get_week_sessions(session: Session, week_id: int) -> list[TrainingSession]:
    return list(
        session.exec(
            select(TrainingSession)
            .where(TrainingSession.week_id == week_id)
            .order_by(col(TrainingSession.sort_order), col(TrainingSession.weekday))
        ).all()
    )


def get_today_sessions(session: Session, reference_date: date | None = None) -> list[TrainingSession]:
    week = get_current_training_week(session, reference_date)
    if not week:
        return []
    weekday = Weekday((reference_date or date.today()).weekday())
    return list(
        session.exec(
            select(TrainingSession)
            .where(TrainingSession.week_id == week.id)
            .where(TrainingSession.weekday == weekday)
        ).all()
    )


def is_training_day(session: Session, reference_date: date | None = None) -> bool:
    return len(get_today_sessions(session, reference_date)) > 0


def get_or_create_daily_log(session: Session, user_id: int, log_date: date | None = None) -> DailyLog:
    ref = log_date or date.today()
    log = session.exec(
        select(DailyLog).where(DailyLog.user_id == user_id).where(DailyLog.log_date == ref)
    ).first()
    if log:
        return log

    training_day = is_training_day(session, ref)
    log = DailyLog(
        user_id=user_id,
        log_date=ref,
        water_target_liters=3.5 if training_day else 2.5,
    )
    session.add(log)
    session.flush()
    return log


def get_recent_messages(
    session: Session, user_id: int, limit: int = 20
) -> list[ConversationMessage]:
    messages = session.exec(
        select(ConversationMessage)
        .where(ConversationMessage.user_id == user_id)
        .order_by(col(ConversationMessage.created_at).desc())
        .limit(limit)
    ).all()
    return list(reversed(messages))


def save_message(
    session: Session,
    user_id: int,
    role: MessageRole,
    content: str,
    metadata_json: str | None = None,
) -> ConversationMessage:
    message = ConversationMessage(
        user_id=user_id,
        role=role,
        content=content,
        metadata_json=metadata_json,
    )
    session.add(message)
    session.flush()
    return message


def get_phase_for_week(session: Session, week: TrainingWeek) -> TrainingPhase | None:
    return session.get(TrainingPhase, week.phase_id)


def format_week_plan(session: Session, week: TrainingWeek) -> str:
    phase = get_phase_for_week(session, week)
    sessions = get_week_sessions(session, week.id)  # type: ignore[arg-type]
    lines = [
        f"Semana {week.week_number} ({week.start_date} a {week.end_date})",
        f"Fase: {phase.name if phase else 'N/A'} — {phase.focus if phase else ''}",
        "",
    ]
    weekday_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    for s in sessions:
        day = weekday_pt[s.weekday.value]
        dist = f"{s.target_distance_km:.1f} km" if s.target_distance_km else ""
        dur = f"{s.target_duration_min} min" if s.target_duration_min else ""
        metrics = " | ".join(filter(None, [dist, dur, s.target_pace_per_km or ""]))
        lines.append(f"  {day}: {s.title} ({s.session_type.value}) — {metrics}")
        lines.append(f"       {s.description}")
    return "\n".join(lines)


def format_daily_log(log: DailyLog) -> str:
    parts = [f"Data: {log.log_date}"]
    if log.water_liters is not None:
        parts.append(f"Água: {log.water_liters}L / meta {log.water_target_liters}L")
    elif log.water_target_liters:
        parts.append(f"Meta água: {log.water_target_liters}L (ainda não registado)")

    supps = []
    if log.magnesium_taken is True:
        supps.append("Magnésio ✓")
    elif log.magnesium_taken is False:
        supps.append("Magnésio ✗")
    if log.omega3_taken is True:
        supps.append("Ómega-3 ✓")
    if log.creatine_taken is True:
        grams = f" ({log.creatine_grams}g)" if log.creatine_grams else ""
        supps.append(f"Creatina ✓{grams}")
    if supps:
        parts.append("Suplementos: " + ", ".join(supps))

    if log.training_completed is not None or log.training_distance_km:
        status = "Sim" if log.training_completed else "Não"
        dist = f", {log.training_distance_km} km" if log.training_distance_km else ""
        parts.append(f"Treino: {status}{dist}")
    if log.knee_pain_level is not None:
        parts.append(f"Dor joelhos: {log.knee_pain_level}/10")
    if log.smoked_near_training is True:
        parts.append("⚠️ Fumou perto do treino")
    if log.notes:
        parts.append(f"Notas: {log.notes}")
    return " | ".join(parts)


def get_days_until_race(session: Session, user_id: int, reference_date: date | None = None) -> int | None:
    goal = get_user_goal(session, user_id)
    if not goal:
        return None
    ref = reference_date or date.today()
    return (goal.target_date - ref).days


def get_recent_logs_summary(session: Session, user_id: int, days: int = 7) -> str:
    since = date.today() - timedelta(days=days)
    logs = session.exec(
        select(DailyLog)
        .where(DailyLog.user_id == user_id)
        .where(DailyLog.log_date >= since)
        .order_by(col(DailyLog.log_date))
    ).all()
    if not logs:
        return "Sem registos recentes."
    return "\n".join(format_daily_log(log) for log in logs)


def get_all_training_weeks(session: Session) -> list[TrainingWeek]:
    return list(
        session.exec(select(TrainingWeek).order_by(col(TrainingWeek.week_number))).all()
    )


def get_training_week_by_number(session: Session, week_number: int) -> TrainingWeek | None:
    return session.exec(
        select(TrainingWeek).where(TrainingWeek.week_number == week_number)
    ).first()


def get_training_phase(session: Session, phase_number: int) -> TrainingPhase | None:
    return session.exec(
        select(TrainingPhase).where(TrainingPhase.phase_number == phase_number)
    ).first()


def get_weeks_for_phase(session: Session, phase_number: int) -> list[TrainingWeek]:
    phase = get_training_phase(session, phase_number)
    if not phase or phase.id is None:
        return []
    return list(
        session.exec(
            select(TrainingWeek)
            .where(TrainingWeek.phase_id == phase.id)
            .order_by(col(TrainingWeek.week_number))
        ).all()
    )


def get_upcoming_weeks(session: Session, weeks_ahead: int = 2) -> list[TrainingWeek]:
    ref = date.today()
    all_weeks = get_all_training_weeks(session)
    return [w for w in all_weeks if w.end_date >= ref][:weeks_ahead]


def format_week_summary(session: Session, week: TrainingWeek) -> str:
    phase = get_phase_for_week(session, week)
    sessions = get_week_sessions(session, week.id)  # type: ignore[arg-type]
    weekday_pt = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    session_bits: list[str] = []
    for s in sessions:
        day = weekday_pt[s.weekday.value]
        if s.target_distance_km:
            metric = f"{s.target_distance_km:.0f}km"
        elif s.target_duration_min:
            metric = f"{s.target_duration_min}min"
        else:
            metric = ""
        session_bits.append(f"{day} {s.title}" + (f" ({metric})" if metric else ""))
    phase_name = phase.name if phase else "?"
    return (
        f"Semana {week.week_number} ({week.start_date} a {week.end_date}) — {phase_name}: "
        + "; ".join(session_bits)
    )


def format_phase_plan(
    session: Session, phase: TrainingPhase, detail_level: str = "summary"
) -> str:
    weeks = get_weeks_for_phase(session, phase.phase_number)
    lines = [
        f"{phase.name} (Semanas {weeks[0].week_number}-{weeks[-1].week_number})"
        if weeks
        else phase.name,
        f"Foco: {phase.focus}",
        f"{phase.description or ''}",
        "",
    ]
    for week in weeks:
        if detail_level == "detailed":
            lines.append(format_week_plan(session, week))
            lines.append("")
        else:
            lines.append(format_week_summary(session, week))
    return "\n".join(lines).strip()


def query_training_plan(
    session: Session,
    scope: str = "current_week",
    week_number: int | None = None,
    phase_number: int | None = None,
    weeks_ahead: int = 2,
    detail_level: str = "summary",
) -> dict[str, str | int | bool]:
    detail = detail_level if detail_level in ("summary", "detailed") else "summary"

    if scope == "current_week":
        week = get_current_training_week(session)
        if not week:
            return {"success": False, "error": "Sem plano para a data actual."}
        plan = (
            format_week_plan(session, week)
            if detail == "detailed"
            else format_week_summary(session, week)
        )
        return {"success": True, "scope": scope, "plan": plan}

    if scope == "week":
        if week_number is None:
            return {"success": False, "error": "Indica week_number (1-14) para scope=week."}
        week = get_training_week_by_number(session, week_number)
        if not week:
            return {"success": False, "error": f"Semana {week_number} não encontrada."}
        plan = (
            format_week_plan(session, week)
            if detail == "detailed"
            else format_week_summary(session, week)
        )
        return {"success": True, "scope": scope, "week_number": week_number, "plan": plan}

    if scope == "phase":
        if phase_number is None:
            return {"success": False, "error": "Indica phase_number (1-4) para scope=phase."}
        phase = get_training_phase(session, phase_number)
        if not phase:
            return {"success": False, "error": f"Fase {phase_number} não encontrada."}
        return {
            "success": True,
            "scope": scope,
            "phase_number": phase_number,
            "plan": format_phase_plan(session, phase, detail),
        }

    if scope == "upcoming":
        weeks = get_upcoming_weeks(session, max(1, weeks_ahead))
        if not weeks:
            return {"success": False, "error": "Sem semanas futuras no plano."}
        lines = [format_week_plan(session, w) if detail == "detailed" else format_week_summary(session, w) for w in weeks]
        return {
            "success": True,
            "scope": scope,
            "weeks_included": len(weeks),
            "plan": "\n\n".join(lines),
        }

    if scope == "full":
        weeks = get_all_training_weeks(session)
        phases = session.exec(select(TrainingPhase).order_by(col(TrainingPhase.phase_number))).all()
        lines: list[str] = ["PLANO COMPLETO — 14 SEMANAS", ""]
        for phase in phases:
            lines.append(f"=== {phase.name} ===")
            lines.append(f"Foco: {phase.focus}")
            phase_weeks = [w for w in weeks if w.phase_id == phase.id]
            for week in phase_weeks:
                if detail == "detailed":
                    lines.append(format_week_plan(session, week))
                else:
                    lines.append(format_week_summary(session, week))
            lines.append("")
        return {"success": True, "scope": scope, "total_weeks": len(weeks), "plan": "\n".join(lines).strip()}

    return {"success": False, "error": f"Scope desconhecido: {scope}"}
