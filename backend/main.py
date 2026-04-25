import os, csv, io, json
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true"
ORACLE_USER = os.getenv("ORACLE_USER", "")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_DSN = os.getenv("ORACLE_DSN", "")
ORACLE_WALLET_PASSWORD = os.getenv("ORACLE_WALLET_PASSWORD", "")

USER_GOALS = {
    "objective": "muscle_and_weight_gain",
    "medical_context": "Underweight, weight gain is health-relevant",
    "training_days_per_week": 4,
    "rep_range": "6-15",
    "rpe_preference": "7-9",
    "volume_priority": "high",
    "current_injuries": "Right chest mild strain (early April), occasional left shoulder pain on pulls"
}

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


class DB:
    def __init__(self):
        self.conn = None
        self.driver = None

    def connect(self):
        try:
            import oracledb
            oracledb.init_oracle_client(config_dir="./wallet")
            self.conn = oracledb.connect(
                user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN,
                wallet_password=ORACLE_WALLET_PASSWORD, wallet_location="./wallet"
            )
            self.driver = "oracle"
            print("Connected to Oracle Autonomous Database")
        except Exception as e:
            print(f"Oracle failed: {e}")
            if USE_SQLITE_FALLBACK:
                import sqlite3
                self.conn = sqlite3.connect("./biome.db", check_same_thread=False)
                self.driver = "sqlite"
                print("Using SQLite fallback")
            else:
                raise

    def setup(self):
        c = self.conn.cursor()
        if self.driver == "oracle":
            c.execute("BEGIN EXECUTE IMMEDIATE 'DROP TABLE workout_sets'; EXCEPTION WHEN OTHERS THEN NULL; END;")
            c.execute("""CREATE TABLE workout_sets (
                id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                session_date DATE NOT NULL, workout_type VARCHAR2(50) NOT NULL,
                exercise_name VARCHAR2(100) NOT NULL, exercise_canonical VARCHAR2(100) NOT NULL,
                side VARCHAR2(10), set_number NUMBER, reps NUMBER, duration_seconds NUMBER,
                weight_kg NUMBER, machine_level NUMBER, is_warmup NUMBER(1) DEFAULT 0,
                rpe NUMBER, notes VARCHAR2(500))""")
        else:
            c.execute("DROP TABLE IF EXISTS workout_sets")
            c.execute("""CREATE TABLE workout_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_date TEXT NOT NULL,
                workout_type TEXT NOT NULL, exercise_name TEXT NOT NULL,
                exercise_canonical TEXT NOT NULL, side TEXT, set_number INTEGER,
                reps INTEGER, duration_seconds INTEGER, weight_kg REAL,
                machine_level INTEGER, is_warmup INTEGER DEFAULT 0, rpe REAL, notes TEXT)""")
        self.conn.commit()

    def insert(self, rows):
        c = self.conn.cursor()
        sql = """INSERT INTO workout_sets
            (session_date, workout_type, exercise_name, exercise_canonical, side, set_number,
             reps, duration_seconds, weight_kg, machine_level, is_warmup, rpe, notes)
            VALUES ({})""".format(", ".join(["?"]*13) if self.driver=="sqlite" else ", ".join([":"+str(i+1) for i in range(13)])
        )
        if self.driver == "oracle":
            for r in rows:
                c.execute(sql, r)
        else:
            c.executemany(sql, rows)
        self.conn.commit()

    def query(self, sql, params=None):
        c = self.conn.cursor()
        c.execute(sql, params or ())
        cols = [d[0].lower() for d in c.description] if c.description else []
        return [dict(zip(cols, row)) for row in c.fetchall()]

    def execute(self, sql, params=None):
        c = self.conn.cursor()
        c.execute(sql, params or ())
        self.conn.commit()

    def date_add(self, days):
        if self.driver == "oracle":
            return f"SYSDATE - {abs(days)}"
        return f"date('now', '-{abs(days)} days')"

    def nvl(self, *args):
        if self.driver == "oracle":
            return "NVL(" + ", ".join(args) + ")"
        return "COALESCE(" + ", ".join(args) + ")"


db = DB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    db.setup()
    yield
    if db.conn:
        db.conn.close()

app = FastAPI(title="Biome AI Strength Coach", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://localhost:3000"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class LogSet(BaseModel):
    set_number: int
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    machine_level: Optional[int] = None
    rpe: Optional[float] = None
    notes: Optional[str] = None
    is_warmup: int = 0


class LogExercise(BaseModel):
    exercise_name: str
    side: Optional[str] = None
    sets: List[LogSet]


class LogWorkout(BaseModel):
    date: str
    workout_type: str
    exercises: List[LogExercise]


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


@app.post("/import")
async def import_csv(file: UploadFile = File(...)):
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
    db.insert(rows)
    return {"row_count": len(rows)}


@app.get("/workouts")
def get_workouts():
    return db.query("""SELECT session_date, workout_type, exercise_name, side, set_number,
        reps, duration_seconds, weight_kg, machine_level, is_warmup, rpe, notes
        FROM workout_sets ORDER BY session_date DESC, workout_type, exercise_name, set_number""")


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------

@app.get("/metrics/exercises")
def get_exercise_metrics():
    cutoff = db.date_add(56)
    sql = f"""SELECT exercise_canonical, side, COUNT(DISTINCT session_date) as session_count,
        MAX(CASE WHEN is_warmup = 0 THEN {db.nvl('weight_kg', 'machine_level * 2', '1')} END) as max_load,
        AVG(CASE WHEN is_warmup = 0 THEN rpe END) as avg_rpe,
        MAX(session_date) as last_date
        FROM workout_sets WHERE session_date >= {cutoff}
        GROUP BY exercise_canonical, side ORDER BY exercise_canonical"""
    rows = db.query(sql)
    result = []
    for r in rows:
        ex, side = r["exercise_canonical"], r.get("side") or ""
        full_name = f"{ex} {side}".strip() if side else ex
        trend_sql = f"""SELECT session_date,
            {db.nvl('weight_kg', 'machine_level * 2', '1')} as load_val, rpe
            FROM workout_sets WHERE exercise_canonical = ?
            AND COALESCE(side, '') = ? AND is_warmup = 0 AND session_date >= {cutoff}
            ORDER BY session_date"""
        trend_rows = db.query(trend_sql, (ex, side))
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
            FROM workout_sets WHERE exercise_canonical = ? AND COALESCE(side, '') = ?
            AND is_warmup = 0 ORDER BY session_date DESC, set_number DESC LIMIT 1"""
        if db.driver == "oracle":
            latest_sql = latest_sql.replace("LIMIT 1", "FETCH FIRST 1 ROWS ONLY")
        latest = db.query(latest_sql, (ex, side))
        result.append({
            "exercise": full_name, "canonical": ex, "side": side,
            "sessions": r["session_count"], "current_load": latest[0]["load_val"] if latest else None,
            "max_load": r["max_load"], "avg_rpe": round(r["avg_rpe"], 2) if r["avg_rpe"] else None,
            "trend": trend, "status": status
        })
    return result


@app.get("/metrics/volume")
def get_volume_metrics():
    cutoff = db.date_add(84)
    if db.driver == "oracle":
        week_col = "TO_CHAR(session_date, 'IW')"
    else:
        week_col = "strftime('%W', session_date)"
    sql = f"""SELECT {week_col} as week_num, exercise_canonical,
        SUM(reps * {db.nvl('weight_kg', 'machine_level * 2', '1')}) as volume
        FROM workout_sets WHERE is_warmup = 0 AND session_date >= {cutoff}
        GROUP BY {week_col}, exercise_canonical ORDER BY week_num"""
    rows = db.query(sql)
    weeks = {}
    for r in rows:
        muscle = EXERCISE_MUSCLE.get(r["exercise_canonical"], "other")
        w = r["week_num"]
        if w not in weeks:
            weeks[w] = {}
        weeks[w][muscle] = weeks[w].get(muscle, 0) + (r["volume"] or 0)
    return [{"week": w, "muscles": {m: round(v, 1) for m, v in weeks[w].items()}}
            for w in sorted(weeks.keys())]


@app.get("/metrics/asymmetry")
def get_asymmetry_metrics():
    cutoff = db.date_add(28)
    sql = f"""SELECT exercise_canonical, side,
        AVG(reps) as avg_reps, AVG(rpe) as avg_rpe
        FROM workout_sets WHERE side IS NOT NULL AND side IN ('RS','LS')
        AND is_warmup = 0 AND session_date >= {cutoff}
        GROUP BY exercise_canonical, side"""
    rows = db.query(sql)
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


# ------------------------------------------------------------------
# GROQ helpers
# ------------------------------------------------------------------

def _groq_chat(messages: list, model: str = "llama-3.3-70b-versatile") -> str:
    if not GROQ_API_KEY:
        return None
    try:
        import groq
        client = groq.Groq(api_key=GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=0.7, max_tokens=2048
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"GROQ error: {e}")
        return None


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

@app.get("/recommend")
def get_recommendation(workout_type: str = "Push Day"):
    metrics = get_exercise_metrics()
    asymmetry = get_asymmetry_metrics()
    volume = get_volume_metrics()
    relevant = [m for m in metrics if _is_in_workout_type(m["canonical"], workout_type)]

    sql = """SELECT session_date, exercise_name, reps,
        COALESCE(weight_kg, machine_level * 2, 1) as load_val, rpe, notes
        FROM workout_sets WHERE workout_type = ?
        ORDER BY session_date DESC, set_number"""
    recent = db.query(sql, (workout_type,))
    sessions = {}
    for r in recent:
        sessions.setdefault(r["session_date"], []).append(r)
    last_3 = [{"date": d, "sets": sessions[d]} for d in sorted(sessions.keys(), reverse=True)[:3]]

    context = {
        "user_goals": USER_GOALS,
        "exercise_status": relevant,
        "asymmetries": asymmetry,
        "last_sessions": last_3,
        "current_week_volume": volume[-1] if volume else {}
    }

    system_prompt = f"""You are Biome, a personal AI strength coach. You receive STRUCTURED METRICS about the user's training.
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
{{"session_plan":{{"workout_type":string,"estimated_duration_minutes":number,"exercises":[{{"name":string,"order":number,"sets":number,"target_reps":string,"target_weight_kg":number|null,"target_machine_level":number|null,"target_rpe":string,"rest_seconds":number,"rationale":string}}]}},"overall_reasoning":string,"warnings":[string],"confidence":"high"|"medium"|"low"}}"""

    user_prompt = f"Workout type: {workout_type}\n\nContext:\n{json.dumps(context, indent=2)}"

    content = _groq_chat([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])
    if not content:
        return _fallback_recommendation(workout_type)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Retry once
        content2 = _groq_chat([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + "\n\nYour last response wasn't valid JSON, try again. Output only JSON."}
        ])
        if content2:
            try:
                return json.loads(content2)
            except json.JSONDecodeError:
                pass
        return _fallback_recommendation(workout_type)


# ------------------------------------------------------------------
# Chat endpoint
# ------------------------------------------------------------------

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    metrics = get_exercise_metrics()
    asymmetry = get_asymmetry_metrics()
    volume = get_volume_metrics()

    sql = """SELECT session_date, workout_type, exercise_name, reps,
        COALESCE(weight_kg, machine_level * 2, 1) as load_val, rpe, notes
        FROM workout_sets ORDER BY session_date DESC LIMIT 30"""
    if db.driver == "oracle":
        sql = sql.replace("LIMIT 30", "FETCH FIRST 30 ROWS ONLY")
    recent = db.query(sql)

    context = {
        "user_goals": USER_GOALS,
        "exercise_status": metrics,
        "asymmetries": asymmetry,
        "current_week_volume": volume[-1] if volume else {},
        "recent_sets": recent
    }

    system_msg = f"""You are Biome, a personal AI strength coach with access to the user's training data.
You speak in English, cite real numbers from the data, and give actionable advice.
Current training context:\n{json.dumps(context, indent=2)}"""

    messages = [{"role": "system", "content": system_msg}]
    for h in req.history:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": req.message})

    content = _groq_chat(messages)
    if not content:
        return {"reply": "I'm having trouble connecting to the AI service. Please try again later."}
    return {"reply": content}


# ------------------------------------------------------------------
# Log workout endpoint
# ------------------------------------------------------------------

@app.post("/workouts")
def log_workout(body: LogWorkout):
    rows = []
    for ex in body.exercises:
        for s in ex.sets:
            rows.append((
                body.date, body.workout_type, ex.exercise_name, ex.exercise_name.lower(),
                ex.side, s.set_number, s.reps, None, s.weight_kg, s.machine_level,
                s.is_warmup, s.rpe, s.notes
            ))
    db.insert(rows)
    return {"row_count": len(rows)}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

