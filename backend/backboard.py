import os
import json
from typing import Optional, Dict, Any, List
import httpx

from db import db

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY", "")


class BackboardClient:
    """Thin wrapper over the Backboard REST API.

    See https://docs.backboard.io/ and the cookbook at
    github.com/Backboard-io/backboard_io_cookbook for the canonical patterns.
    """

    def __init__(self, api_key: str, base_url: str = "https://app.backboard.io/api"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        self._client = httpx.Client(timeout=60.0)

    def list_assistants(self) -> List[Dict[str, Any]]:
        resp = self._client.get(f"{self.base_url}/assistants", headers=self.headers)
        resp.raise_for_status()
        body = resp.json()
        if isinstance(body, list):
            return body
        return body.get("assistants") or body.get("data") or []

    def create_assistant(self, name: str, system_prompt: str, tools: Optional[list] = None) -> str:
        payload: Dict[str, Any] = {"name": name, "system_prompt": system_prompt}
        if tools:
            payload["tools"] = tools
        resp = self._client.post(f"{self.base_url}/assistants", json=payload, headers=self.headers)
        resp.raise_for_status()
        return resp.json()["assistant_id"]

    def get_or_create_assistant(self, name: str, system_prompt: str, tools: Optional[list] = None) -> str:
        # Cookbook pattern: lookup by name, create if missing. Never hardcode IDs —
        # restarts would otherwise spawn a new assistant on every boot.
        for a in self.list_assistants():
            if a.get("name") == name:
                return a.get("assistant_id") or a.get("id")
        return self.create_assistant(name=name, system_prompt=system_prompt, tools=tools)

    def create_thread(self, assistant_id: str) -> str:
        resp = self._client.post(
            f"{self.base_url}/assistants/{assistant_id}/threads",
            json={},
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()["thread_id"]

    def add_message(
        self,
        thread_id: str,
        content: str,
        memory: str = "Auto",
        stream: bool = False,
    ) -> Dict[str, Any]:
        resp = self._client.post(
            f"{self.base_url}/threads/{thread_id}/messages",
            json={"content": content, "stream": stream, "memory": memory},
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()

    def submit_tool_outputs(
        self,
        thread_id: str,
        run_id: str,
        tool_outputs: list,
    ) -> Dict[str, Any]:
        resp = self._client.post(
            f"{self.base_url}/threads/{thread_id}/runs/{run_id}/submit_tool_outputs",
            json={"tool_outputs": tool_outputs, "stream": False},
            headers=self.headers,
        )
        resp.raise_for_status()
        return resp.json()


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


def get_user_assistant(user_id: str) -> str:
    if user_id in USER_ASSISTANTS:
        return USER_ASSISTANTS[user_id]
    goals = db.load_user_goals(user_id)
    aid = bb_client.get_or_create_assistant(
        name=f"biome-user-{user_id}",
        system_prompt=_chat_system_prompt(goals),
        tools=CHAT_TOOLS,
    )
    USER_ASSISTANTS[user_id] = aid
    return aid


def get_recommender_assistant() -> str:
    if "_recommender" in USER_ASSISTANTS:
        return USER_ASSISTANTS["_recommender"]
    aid = bb_client.get_or_create_assistant(
        name="biome-recommender",
        system_prompt=_rec_system_prompt(),
        tools=None,
    )
    USER_ASSISTANTS["_recommender"] = aid
    return aid


def parse_tool_args(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    fn = tool_call.get("function", {})
    raw = fn.get("parsed_arguments")
    if raw is None:
        raw = fn.get("arguments")
    if raw is None or raw == "":
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
