"""Definição de tools Claude para extração de entidades e atualização do daily log."""

from datetime import date
from typing import Any

COACH_TOOLS: list[dict[str, Any]] = [
    {
        "name": "update_daily_log",
        "description": (
            "Atualiza o registo diário do atleta com base na mensagem recebida. "
            "Usa SEMPRE que o utilizador reportar treino, suplementos, água, dor nos joelhos, "
            "tabaco ou outros dados de tracking. Podes chamar múltiplas vezes numa mensagem "
            "se necessário, mas preferencialmente uma chamada com todos os campos detetados."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "log_date": {
                    "type": "string",
                    "description": "Data do registo (YYYY-MM-DD). Default: hoje.",
                },
                "water_liters": {
                    "type": "number",
                    "description": "Litros de água ingeridos hoje.",
                },
                "magnesium_taken": {
                    "type": "boolean",
                    "description": "Tomou Citrato de Magnésio Solgar à noite.",
                },
                "omega3_taken": {
                    "type": "boolean",
                    "description": "Tomou Ómega-3 (almoço ou jantar).",
                },
                "creatine_taken": {
                    "type": "boolean",
                    "description": "Tomou creatina.",
                },
                "creatine_grams": {
                    "type": "number",
                    "description": "Gramas de creatina tomadas (típico 3-5g).",
                },
                "training_completed": {
                    "type": "boolean",
                    "description": "Completou o treino planeado ou outro treino.",
                },
                "training_distance_km": {
                    "type": "number",
                    "description": "Distância corrida/jogada em km.",
                },
                "training_duration_min": {
                    "type": "integer",
                    "description": "Duração do treino em minutos.",
                },
                "training_notes": {
                    "type": "string",
                    "description": "Notas sobre o treino (ritmo, sensações, etc.).",
                },
                "knee_pain_level": {
                    "type": "integer",
                    "description": "Nível de dor nos joelhos de 0 a 10.",
                },
                "smoked_today": {
                    "type": "boolean",
                    "description": "Fumou hoje.",
                },
                "smoked_near_training": {
                    "type": "boolean",
                    "description": "Fumou dentro de 2h antes ou depois de treino/futebol.",
                },
                "sleep_hours": {
                    "type": "number",
                    "description": "Horas de sono na noite anterior.",
                },
                "weight_kg": {
                    "type": "number",
                    "description": "Peso corporal em kg.",
                },
                "notes": {
                    "type": "string",
                    "description": "Notas gerais do dia.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_training_plan",
        "description": (
            "Consulta o plano de treino real na base de dados. "
            "Usa SEMPRE que o atleta perguntar pelo plano completo, uma semana específica, "
            "uma fase, ou o que vem a seguir. Nunca inventes sessões — obtém os dados aqui."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["full", "current_week", "week", "phase", "upcoming"],
                    "description": (
                        "full=plano completo 14 semanas; current_week=semana actual; "
                        "week=semana específica; phase=fase 1-4; upcoming=próximas semanas"
                    ),
                },
                "week_number": {
                    "type": "integer",
                    "description": "Número da semana (1-14). Obrigatório quando scope=week.",
                },
                "phase_number": {
                    "type": "integer",
                    "description": "Número da fase (1-4). Obrigatório quando scope=phase.",
                },
                "weeks_ahead": {
                    "type": "integer",
                    "description": "Quantas semanas incluir quando scope=upcoming (default 2).",
                },
                "detail_level": {
                    "type": "string",
                    "enum": ["summary", "detailed"],
                    "description": (
                        "summary=visão compacta; detailed=todas as sessões com descrições"
                    ),
                },
            },
            "required": ["scope"],
        },
    },
]

# Alias retrocompatível
TRACKING_TOOLS = COACH_TOOLS


def build_system_prompt(
    user_profile: str,
    goal_info: str,
    week_plan: str,
    today_sessions: str,
    daily_log: str,
    recent_logs: str,
    days_to_race: int | None,
) -> str:
    race_countdown = f"{days_to_race} dias" if days_to_race is not None else "N/A"

    return f"""És um treinador de corrida de elite e nutricionista desportivo, a acompanhar um atleta amador.

## Persona
- Tom motivador mas exigente, baseado em evidência científica.
- Falas SEMPRE em Português de Portugal (PT-PT).
- Tratas o atleta por "tu", com respeito e proximidade profissional.
- Respostas concisas para Telegram (2-4 parágrafos curtos, texto simples sem markdown).

## Perfil do Atleta
{user_profile}

## Objetivo
{goal_info}
Dias até à prova: {race_countdown}

## Plano da Semana Atual
{week_plan}

## Treino(s) de Hoje
{today_sessions}

## Registo de Hoje
{daily_log}

## Histórico Recente (7 dias)
{recent_logs}

## Regras de Ouro (monitoriza e relembra ativamente)

### Regra do Tabaco
O atleta é fumador. PROIBIDO fumar 2 horas antes e 2 horas depois de qualquer treino ou futebol.
Isto protege tendões e sistema cardiovascular. Se violar, alerta firmemente mas construtivamente.

### Nutrição e Suplementos
Valida diariamente:
- Citrato de Magnésio Solgar — à noite (recovery)
- Ómega-3 — almoço e/ou jantar
- Creatina — 3 a 5 g por dia

### Hidratação
- Dias de treino/futebol: 3.5 L
- Dias de descanso: 2.5 L

### Joelhos
Se dor > 4/10: priorizar descanso, gelo (15-20 min) e agachamento isométrico (Wall Sit 3x30-45s).
Reduzir impacto e evitar volume extra.

## Instruções Operacionais
1. ANTES de responderes, usa `update_daily_log` se a mensagem contiver dados de tracking.
2. Usa `get_training_plan` quando perguntarem pelo plano (completo, semana X, fase, próximas semanas).
   - Plano completo: scope=full, detail_level=summary (ou detailed se pedirem detalhe).
   - Semana específica: scope=week, week_number=N.
3. Depois responde com coaching personalizado baseado nos dados reais.
4. Referencia o plano e as regras de ouro quando relevante.
5. NUNCA inventes treinos — consulta sempre a tool se não tiveres a informação.
"""


def parse_log_date(value: str | None, default: date | None = None) -> date:
    if not value:
        return default or date.today()
    return date.fromisoformat(value)
