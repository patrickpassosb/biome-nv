import os
import json
from typing import Optional, Dict, Any

from backboard import BackboardClient

from db import db

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "")

bb_client: Optional[BackboardClient] = (
    BackboardClient(api_key=BACKBOARD_API_KEY) if BACKBOARD_API_KEY else None
)

# Per-user assistant ids, cached to avoid repeated list_assistants() calls.
# Cookbook critical rule: each user gets their own assistant so memory="Auto"
# doesn't leak facts between users. The shared "_recommender" key is reserved
# for the no-memory recommendation assistant.
USER_ASSISTANTS: Dict[str, str] = {}
# user_id -> persistent chat thread_id (one ongoing conversation per user)
USER_CHAT_THREADS: Dict[str, str] = {}


CHAT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_exercise_metrics",
            "description": "Fetch the user's per-exercise metrics: load progression, RPE trends, session counts (last 8 weeks).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_volume_metrics",
            "description": "Fetch weekly training volume grouped by muscle (last 12 weeks).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_asymmetry_metrics",
            "description": "Fetch left/right asymmetries on unilateral exercises (last 4 weeks).",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def _chat_system_prompt(goals: Dict[str, Any]) -> str:
    return (
        "You are Biome, a personal AI strength coach. Speak in English, cite real numbers "
        "from the data when relevant, and give actionable advice. Use the available tools "
        "(get_exercise_metrics, get_volume_metrics, get_asymmetry_metrics) to fetch the "
        "user's training data on demand instead of asking the user for it. "
        f"User goals: {json.dumps(goals)}"
    )


def _rec_system_prompt() -> str:
    return """You are Biome, a personal AI strength coach. You receive STRUCTURED METRICS about a user's training and output a single session plan as JSON.
PRINCIPLES:
- Progressive overload drives adaptation
- Hypertrophy: 6-15 reps, RPE 7-9, 10-20 sets per muscle per week
- Warm-ups don't count toward working volume
- RPE rising on stable load = accumulating fatigue, may need deload
- Asymmetries >20% on unilateral lifts warrant correction work
- Injuries override progression — work around, never through
USER CONTEXT:
The user is underweight and gaining weight is health-relevant, not aesthetic.
- Prioritize volume accumulation over intensity PRs
- Recommend adding a set when an exercise is progressing comfortably
- When weight gain appears slow despite good training, explicitly note caloric intake is usually limiting
- Respect current exercise selection — guide progression, don't rewrite the program

Output ONLY valid JSON matching this exact schema (no markdown fences, no commentary):
{"session_plan":{"workout_type":string,"estimated_duration_minutes":number,"exercises":[{"name":string,"order":number,"sets":number,"target_reps":string,"target_weight_kg":number|null,"target_machine_level":number|null,"target_rpe":string,"rest_seconds":number,"rationale":string}]},"overall_reasoning":string,"warnings":[string],"confidence":"high"|"medium"|"low"}"""


async def get_user_assistant(user_id: str) -> str:
    if user_id in USER_ASSISTANTS:
        return USER_ASSISTANTS[user_id]
    name = f"biome-user-{user_id}"
    # Cookbook get-or-create: lookup by name, create if missing.
    assistants = await bb_client.list_assistants()
    for a in assistants:
        if a.name == name:
            USER_ASSISTANTS[user_id] = a.assistant_id
            return a.assistant_id
    goals = db.load_user_goals(user_id)
    created = await bb_client.create_assistant(
        name=name,
        system_prompt=_chat_system_prompt(goals),
        tools=CHAT_TOOLS,
    )
    USER_ASSISTANTS[user_id] = created.assistant_id
    return created.assistant_id


async def get_recommender_assistant() -> str:
    if "_recommender" in USER_ASSISTANTS:
        return USER_ASSISTANTS["_recommender"]
    name = "biome-recommender"
    assistants = await bb_client.list_assistants()
    for a in assistants:
        if a.name == name:
            USER_ASSISTANTS["_recommender"] = a.assistant_id
            return a.assistant_id
    created = await bb_client.create_assistant(
        name=name,
        system_prompt=_rec_system_prompt(),
    )
    USER_ASSISTANTS["_recommender"] = created.assistant_id
    return created.assistant_id
