import csv
import io
import json
import uuid
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from backboard.exceptions import BackboardError

from db import db, DEFAULT_GOALS_SEED
from backboard_client import (
    bb_client,
    USER_ASSISTANTS,
    USER_CHAT_THREADS,
    get_user_assistant,
    get_recommender_assistant,
)
from deps import require_user_id
from schemas import ChatRequest, LogWorkout, ProfileCreate


router = APIRouter()


EXERCISE_MUSCLE = {
    "abs elevation": "abs", "bicep curls": "biceps", "sit cable crunch": "abs",
    "dead hang": "grip", "knee push up": "chest", "knee push up open": "chest",
    "push up": "chest", "push up closed": "triceps", "peck deck": "chest",
    "lateral raises": "shoulders", "lat pulldown": "back",
    "seated cable row (traingle)": "back", "single arm lat pulldown": "back",
    "squat": "legs", "single leg bulgariansquat": "legs",
    "leg extension": "legs", "calf raises at the step": "calves",
    "single leg calf raises at the step": "calves",
    "v-up": "abs", "scissor kicks": "abs", "plank": "abs",
    "body rows": "back", "reverse tuck leg raises": "abs",
    "reverse plank hold": "back", "good morning's": "back",
    "bench press": "chest", "fly": "chest", "open push up": "chest",
    "closed push up": "triceps", "jump squat": "legs",
    "push up(knee)": "chest", "open push up(knee)": "chest", "closed push up(knee)": "triceps",
    "knee push up open": "chest"
}


# ------------------------------------------------------------------
# Profile routes (no auth — these are the entry point for the app)
# ------------------------------------------------------------------

def _profile_row_to_dict(row: Dict[str, Any]) -> Dict[str, Any]:
    goals_raw = row.get("goals_json")
    goals = None
    if goals_raw:
        try:
            goals = json.loads(goals_raw)
        except (TypeError, json.JSONDecodeError):
            goals = None
    return {
        "id": row["id"],
        "name": row["name"],
        "fitness_goal": row.get("fitness_goal"),
        "goals_json": goals,
        "created_at": str(row.get("created_at")) if row.get("created_at") else None,
    }


@router.get("/profiles")
def list_profiles():
    rows = db.query("SELECT id, name, fitness_goal, goals_json, created_at FROM profiles ORDER BY created_at")
    return [_profile_row_to_dict(r) for r in rows]


@router.post("/profiles")
def create_profile(body: ProfileCreate):
    pid = str(uuid.uuid4())
    goals_json = json.dumps(body.goals_json) if body.goals_json else json.dumps(DEFAULT_GOALS_SEED)
    db.execute(
        "INSERT INTO profiles (id, name, fitness_goal, goals_json) VALUES (?, ?, ?, ?)"
        if db.driver == "sqlite"
        else "INSERT INTO profiles (id, name, fitness_goal, goals_json) VALUES (:1, :2, :3, :4)",
        (pid, body.name, body.fitness_goal, goals_json),
    )
    rows = db.query(
        "SELECT id, name, fitness_goal, goals_json, created_at FROM profiles WHERE id = ?"
        if db.driver == "sqlite"
        else "SELECT id, name, fitness_goal, goals_json, created_at FROM profiles WHERE id = :1",
        (pid,),
    )
    return _profile_row_to_dict(rows[0])


@router.delete("/profiles/{profile_id}")
def delete_profile(profile_id: str):
    rows = db.query(
        "SELECT id FROM profiles WHERE id = ?" if db.driver == "sqlite"
        else "SELECT id FROM profiles WHERE id = :1",
        (profile_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Profile {profile_id} not found")
    db.execute(
        "DELETE FROM workout_sets WHERE user_id = ?" if db.driver == "sqlite"
        else "DELETE FROM workout_sets WHERE user_id = :1",
        (profile_id,),
    )
    db.execute(
        "DELETE FROM profiles WHERE id = ?" if db.driver == "sqlite"
        else "DELETE FROM profiles WHERE id = :1",
        (profile_id,),
    )
    # Drop any cached assistant/thread for this user — Backboard-side resources
    # remain (the assistant lives there) but our local cache should not point at them.
    USER_ASSISTANTS.pop(profile_id, None)
    USER_CHAT_THREADS.pop(profile_id, None)
    return {"deleted": profile_id}


def _to_int(val):
    try:
        return int(float(val.strip())) if val and str(val).strip() else None
    except (ValueError, AttributeError):
        return None


def _to_float(val):
    try:
        return float(str(val).strip()) if val and str(val).strip() else None
    except (ValueError, AttributeError):
        return None


@router.post("/import")
async def import_csv(file: UploadFile = File(...), user_id: str = Depends(require_user_id)):
    text = (await file.read()).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for rec in reader:
        date_raw = rec.get("Date", "").strip()
        try:
            dt = datetime.strptime(date_raw, "%m/%d/%Y")
            date_str = dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
        ex_raw = rec.get("Exercise", "").strip()
        side = None
        ex_canon = ex_raw.lower()
        if ex_canon.endswith(" rs"):
            side, ex_canon, ex_raw = "RS", ex_canon[:-3].strip(), ex_raw[:-3].strip()
        elif ex_canon.endswith(" ls"):
            side, ex_canon, ex_raw = "LS", ex_canon[:-3].strip(), ex_raw[:-3].strip()
        rows.append((
            date_str, rec.get("Workout", "").strip(), ex_raw, ex_canon, side,
            _to_int(rec.get("Set_Number")), _to_int(rec.get("Reps")),
            _to_int(rec.get("Duration_seconds")), _to_float(rec.get("Weight_kg")),
            _to_int(rec.get("Machine_level")),
            1 if (rec.get("Warm up", "").strip().lower() == "yes" or
                  (_to_float(rec.get("RPE")) or 10) < 6) else 0,
            _to_float(rec.get("RPE")),
            rec.get("Notes", "").strip() or None
        ))
    db.insert(rows, user_id)
    return {"row_count": len(rows)}


@router.get("/workouts")
def get_workouts(user_id: str = Depends(require_user_id)):
    sql = ("""SELECT session_date, workout_type, exercise_name, side, set_number,
        reps, duration_seconds, weight_kg, machine_level, is_warmup, rpe, notes
        FROM workout_sets WHERE user_id = ?
        ORDER BY session_date DESC, workout_type, exercise_name, set_number"""
        if db.driver == "sqlite"
        else """SELECT session_date, workout_type, exercise_name, side, set_number,
        reps, duration_seconds, weight_kg, machine_level, is_warmup, rpe, notes
        FROM workout_sets WHERE user_id = :1
        ORDER BY session_date DESC, workout_type, exercise_name, set_number""")
    return db.query(sql, (user_id,))


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

def _exercise_metrics(user_id: str) -> list:
    cutoff = db.date_add(56)
    sql = f"""SELECT exercise_canonical, side, COUNT(DISTINCT session_date) as session_count,
        MAX(CASE WHEN is_warmup = 0 THEN {db.nvl('weight_kg', 'machine_level * 2', '1')} END) as max_load,
        AVG(CASE WHEN is_warmup = 0 THEN rpe END) as avg_rpe,
        MAX(session_date) as last_date
        FROM workout_sets WHERE user_id = ? AND session_date >= {cutoff}
        GROUP BY exercise_canonical, side ORDER BY exercise_canonical"""
    rows = db.query(sql, (user_id,))
    result = []
    for r in rows:
        ex, side = r["exercise_canonical"], r.get("side") or ""
        full_name = f"{ex} {side}".strip() if side else ex
        trend_sql = f"""SELECT session_date,
            {db.nvl('weight_kg', 'machine_level * 2', '1')} as load_val, rpe
            FROM workout_sets WHERE user_id = ? AND exercise_canonical = ?
            AND COALESCE(side, '') = ? AND is_warmup = 0 AND session_date >= {cutoff}
            ORDER BY session_date"""
        trend_rows = db.query(trend_sql, (user_id, ex, side))
        trend, status = "flat", "new"
        if len(trend_rows) >= 4:
            mid = len(trend_rows) // 2
            first = sum((x["load_val"] or 1) for x in trend_rows[:mid]) / mid
            second = sum((x["load_val"] or 1) for x in trend_rows[mid:]) / (len(trend_rows) - mid)
            diff = second - first
            if diff > 0.5:
                trend, status = "positive", "progressing"
            elif diff < -0.5:
                trend, status = "negative", "stalled"
            else:
                trend, status = "flat", "stalled" if r["session_count"] > 3 else "new"
        elif trend_rows:
            status = "new"
        latest_sql = f"""SELECT {db.nvl('weight_kg', 'machine_level * 2', '1')} as load_val
            FROM workout_sets WHERE user_id = ? AND exercise_canonical = ? AND COALESCE(side, '') = ?
            AND is_warmup = 0 ORDER BY session_date DESC, set_number DESC LIMIT 1"""
        if db.driver == "oracle":
            latest_sql = latest_sql.replace("LIMIT 1", "FETCH FIRST 1 ROWS ONLY")
        latest = db.query(latest_sql, (user_id, ex, side))
        result.append({
            "exercise": full_name, "canonical": ex, "side": side,
            "sessions": r["session_count"], "current_load": latest[0]["load_val"] if latest else None,
            "max_load": r["max_load"], "avg_rpe": round(r["avg_rpe"], 2) if r["avg_rpe"] else None,
            "trend": trend, "status": status
        })
    return result


def _volume_metrics(user_id: str) -> list:
    cutoff = db.date_add(84)
    if db.driver == "oracle":
        week_col = "TO_CHAR(session_date, 'IW')"
    else:
        week_col = "strftime('%W', session_date)"
    sql = f"""SELECT {week_col} as week_num, exercise_canonical,
        SUM(reps * {db.nvl('weight_kg', 'machine_level * 2', '1')}) as volume
        FROM workout_sets WHERE user_id = ? AND is_warmup = 0 AND session_date >= {cutoff}
        GROUP BY {week_col}, exercise_canonical ORDER BY week_num"""
    rows = db.query(sql, (user_id,))
    weeks = {}
    for r in rows:
        muscle = EXERCISE_MUSCLE.get(r["exercise_canonical"], "other")
        w = r["week_num"]
        if w not in weeks:
            weeks[w] = {}
        weeks[w][muscle] = weeks[w].get(muscle, 0) + (r["volume"] or 0)
    return [{"week": w, "muscles": {m: round(v, 1) for m, v in weeks[w].items()}}
            for w in sorted(weeks.keys())]


def _asymmetry_metrics(user_id: str) -> list:
    cutoff = db.date_add(28)
    sql = f"""SELECT exercise_canonical, side,
        AVG(reps) as avg_reps, AVG(rpe) as avg_rpe
        FROM workout_sets WHERE user_id = ? AND side IS NOT NULL AND side IN ('RS','LS')
        AND is_warmup = 0 AND session_date >= {cutoff}
        GROUP BY exercise_canonical, side"""
    rows = db.query(sql, (user_id,))
    by_ex = {}
    for r in rows:
        ex = r["exercise_canonical"]
        by_ex.setdefault(ex, {})[r["side"]] = r
    result = []
    for ex, sides in by_ex.items():
        if "RS" in sides and "LS" in sides:
            rs, ls = sides["RS"], sides["LS"]
            rep_gap = abs((rs["avg_reps"] or 0) - (ls["avg_reps"] or 0))
            avg_reps = ((rs["avg_reps"] or 0) + (ls["avg_reps"] or 0)) / 2
            pct = (rep_gap / avg_reps * 100) if avg_reps > 0 else 0
            rpe_gap = abs((rs["avg_rpe"] or 0) - (ls["avg_rpe"] or 0))
            result.append({
                "exercise": ex, "rs_reps": round(rs["avg_reps"], 1),
                "ls_reps": round(ls["avg_reps"], 1), "rs_rpe": round(rs["avg_rpe"], 2),
                "ls_rpe": round(ls["avg_rpe"], 2), "rep_gap_pct": round(pct, 1),
                "rpe_gap": round(rpe_gap, 2), "flagged": pct > 20
            })
    return result


@router.get("/metrics/exercises")
def get_exercise_metrics(user_id: str = Depends(require_user_id)):
    return _exercise_metrics(user_id)


@router.get("/metrics/volume")
def get_volume_metrics(user_id: str = Depends(require_user_id)):
    return _volume_metrics(user_id)


@router.get("/metrics/asymmetry")
def get_asymmetry_metrics(user_id: str = Depends(require_user_id)):
    return _asymmetry_metrics(user_id)


def _dispatch_tool(name: str, args: Dict[str, Any], user_id: str) -> Any:
    if name == "get_exercise_metrics":
        return _exercise_metrics(user_id)
    if name == "get_volume_metrics":
        return _volume_metrics(user_id)
    if name == "get_asymmetry_metrics":
        return _asymmetry_metrics(user_id)
    return {"error": f"Unknown tool: {name}"}


def _is_in_workout_type(exercise: str, workout_type: str) -> bool:
    ex = exercise.lower()
    wt = workout_type.lower()
    if "push" in wt:
        return any(x in ex for x in ["push up", "bench", "peck", "lateral", "chest", "triceps"])
    if "pull" in wt:
        return any(x in ex for x in ["lat", "row", "pull", "bicep", "back"])
    if "leg" in wt:
        return any(x in ex for x in ["squat", "leg", "calf", "bulgarian"])
    return True


def _fallback_recommendation(workout_type: str):
    exercises = {
        "push day": [
            {"name": "Push Up", "order": 1, "sets": 4, "target_reps": "8-12", "target_weight_kg": None,
             "target_machine_level": None, "target_rpe": "8", "rest_seconds": 90, "rationale": "Progressive overload on bodyweight pressing."},
            {"name": "Peck Deck", "order": 2, "sets": 3, "target_reps": "10-12", "target_weight_kg": None,
             "target_machine_level": 7, "target_rpe": "8.5", "rest_seconds": 60, "rationale": "Isolation work to build chest volume."},
            {"name": "Lateral Raises", "order": 3, "sets": 4, "target_reps": "12-15", "target_weight_kg": 7,
             "target_machine_level": None, "target_rpe": "8", "rest_seconds": 60, "rationale": "Shoulder lateral head development."},
        ],
        "pull day": [
            {"name": "Lat Pulldown", "order": 1, "sets": 4, "target_reps": "10-12", "target_weight_kg": None,
             "target_machine_level": 11, "target_rpe": "8.5", "rest_seconds": 90, "rationale": "Vertical pulling for lat width."},
            {"name": "Seated Cable Row", "order": 2, "sets": 3, "target_reps": "10-12", "target_weight_kg": None,
             "target_machine_level": 11, "target_rpe": "9", "rest_seconds": 90, "rationale": "Horizontal rowing for mid-back thickness."},
            {"name": "Single Arm Lat Pulldown", "order": 3, "sets": 3, "target_reps": "10-12", "target_weight_kg": 2,
             "target_machine_level": 6, "target_rpe": "8.5", "rest_seconds": 60, "rationale": "Unilateral work to address asymmetries."},
        ],
        "leg day": [
            {"name": "Single Leg Bulgarian Squat", "order": 1, "sets": 3, "target_reps": "10-12", "target_weight_kg": 24,
             "target_machine_level": None, "target_rpe": "9", "rest_seconds": 120, "rationale": "Unilateral leg strength, address imbalance."},
            {"name": "Leg Extension", "order": 2, "sets": 3, "target_reps": "12-14", "target_weight_kg": None,
             "target_machine_level": 10, "target_rpe": "9", "rest_seconds": 60, "rationale": "Quad isolation for hypertrophy."},
            {"name": "Calf Raises", "order": 3, "sets": 3, "target_reps": "15-20", "target_weight_kg": 4,
             "target_machine_level": None, "target_rpe": "8.5", "rest_seconds": 45, "rationale": "Calf development with controlled tempo."},
        ],
    }
    plan = exercises.get(workout_type.lower(), exercises["push day"])
    return {
        "session_plan": {
            "workout_type": workout_type,
            "estimated_duration_minutes": 55,
            "exercises": plan
        },
        "overall_reasoning": "Based on your recent training data, prioritize volume accumulation with controlled RPE 8-9 working sets.",
        "warnings": ["Monitor right chest strain on pressing movements."],
        "confidence": "medium"
    }


# ------------------------------------------------------------------
# Recommend endpoint
# ------------------------------------------------------------------

@router.get("/recommend")
async def get_recommendation(workout_type: str = "Push Day", user_id: str = Depends(require_user_id)):
    metrics = _exercise_metrics(user_id)
    asymmetry = _asymmetry_metrics(user_id)
    volume = _volume_metrics(user_id)
    relevant = [m for m in metrics if _is_in_workout_type(m["canonical"], workout_type)]

    sql = ("""SELECT session_date, exercise_name, reps,
        COALESCE(weight_kg, machine_level * 2, 1) as load_val, rpe, notes
        FROM workout_sets WHERE user_id = ? AND workout_type = ?
        ORDER BY session_date DESC, set_number"""
        if db.driver == "sqlite"
        else """SELECT session_date, exercise_name, reps,
        COALESCE(weight_kg, machine_level * 2, 1) as load_val, rpe, notes
        FROM workout_sets WHERE user_id = :1 AND workout_type = :2
        ORDER BY session_date DESC, set_number""")
    recent = db.query(sql, (user_id, workout_type))
    sessions = {}
    for r in recent:
        sessions.setdefault(r["session_date"], []).append(r)
    last_3 = [{"date": d, "sets": sessions[d]} for d in sorted(sessions.keys(), reverse=True)[:3]]

    context = {
        "user_goals": db.load_user_goals(user_id),
        "exercise_status": relevant,
        "asymmetries": asymmetry,
        "last_sessions": last_3,
        "current_week_volume": volume[-1] if volume else {}
    }

    user_message = f"Workout type: {workout_type}\n\nContext:\n{json.dumps(context, indent=2)}"

    if not bb_client:
        return _fallback_recommendation(workout_type)

    # Recommendations don't need cross-thread memory, so we use a fresh thread
    # on a shared no-memory assistant. memory="Off" keeps the rec context out
    # of the user's chat memory.
    try:
        assistant_id = await get_recommender_assistant()
        thread = await bb_client.create_thread(assistant_id)
        res = await bb_client.add_message(
            thread_id=thread.thread_id, content=user_message, memory="Off"
        )

        if res.content:
            try:
                return json.loads(res.content)
            except json.JSONDecodeError:
                pass

        # Single retry — the LLM occasionally wraps JSON in markdown or trailing prose.
        retry = await bb_client.add_message(
            thread_id=thread.thread_id,
            content=(
                "Your last response wasn't valid JSON. Re-output ONLY the JSON object — "
                "no markdown fences, no commentary."
            ),
            memory="Off",
        )
        try:
            return json.loads(retry.content or "")
        except json.JSONDecodeError:
            return _fallback_recommendation(workout_type)
    except BackboardError as e:
        print(f"Backboard error: {e}")
        return _fallback_recommendation(workout_type)


@router.post("/chat")
async def chat_endpoint(req: ChatRequest, user_id: str = Depends(require_user_id)):
    if not bb_client:
        return {"reply": "Backboard API is not configured. Set BACKBOARD_API_KEY in your environment."}

    try:
        assistant_id = await get_user_assistant(user_id)

        thread_id = USER_CHAT_THREADS.get(user_id)
        if not thread_id:
            thread = await bb_client.create_thread(assistant_id)
            thread_id = thread.thread_id
            USER_CHAT_THREADS[user_id] = thread_id

        res = await bb_client.add_message(
            thread_id=thread_id, content=req.message, memory="Auto"
        )

        # Tool-calling loop — see Backboard cookbook recipe 03.
        # Cap iterations so a buggy LLM can't loop us forever.
        max_iterations = 5
        while (
            res.status == "REQUIRES_ACTION"
            and res.tool_calls
            and max_iterations > 0
        ):
            max_iterations -= 1
            tool_outputs = []
            for tc in res.tool_calls:
                fn_name = tc.function.name
                args = tc.function.parsed_arguments or {}
                print(f"[Tool] {fn_name}({args})")
                result = _dispatch_tool(fn_name, args, user_id)
                tool_outputs.append({
                    "tool_call_id": tc.id,
                    "output": json.dumps(result),
                })
            res = await bb_client.submit_tool_outputs(
                thread_id=thread_id, run_id=res.run_id, tool_outputs=tool_outputs
            )

        return {"reply": res.content or "I received an empty response from the AI."}
    except BackboardError as e:
        print(f"Backboard error: {e}")
        return {"reply": "I'm having trouble connecting to the AI service. Please try again later."}


# ------------------------------------------------------------------
# Log workout endpoint
# ------------------------------------------------------------------

@router.post("/workouts")
def log_workout(body: LogWorkout, user_id: str = Depends(require_user_id)):
    rows = []
    for ex in body.exercises:
        for s in ex.sets:
            rows.append((
                body.date, body.workout_type, ex.exercise_name, ex.exercise_name.lower(),
                ex.side, s.set_number, s.reps, None, s.weight_kg, s.machine_level,
                s.is_warmup, s.rpe, s.notes
            ))
    db.insert(rows, user_id)
    return {"row_count": len(rows)}
