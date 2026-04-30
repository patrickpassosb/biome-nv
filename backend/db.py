import os
import json
import uuid
from typing import Optional, Dict, Any

USE_SQLITE_FALLBACK = os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true"
ORACLE_USER = os.getenv("ORACLE_USER", "")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_DSN = os.getenv("ORACLE_DSN", "")
ORACLE_WALLET_PASSWORD = os.getenv("ORACLE_WALLET_PASSWORD", "")

# Used to seed the first profile on a fresh install. Each profile then carries
# its own goals JSON in the profiles table — this constant is only the default.
DEFAULT_GOALS_SEED = {
    "objective": "muscle_and_weight_gain",
    "medical_context": "Underweight, weight gain is health-relevant",
    "training_days_per_week": 4,
    "rep_range": "6-15",
    "rpe_preference": "7-9",
    "volume_priority": "high",
    "current_injuries": "Right chest mild strain (early April), occasional left shoulder pain on pulls"
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
        # Idempotent: never drops existing data. Migrates legacy single-tenant
        # DBs by adding the user_id column when missing.
        c = self.conn.cursor()
        if self.driver == "oracle":
            c.execute("BEGIN EXECUTE IMMEDIATE 'CREATE TABLE profiles ("
                      "id VARCHAR2(64) PRIMARY KEY, name VARCHAR2(100) NOT NULL, "
                      "fitness_goal VARCHAR2(200), goals_json CLOB, "
                      "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'; "
                      "EXCEPTION WHEN OTHERS THEN NULL; END;")
            c.execute("BEGIN EXECUTE IMMEDIATE 'CREATE TABLE workout_sets ("
                      "id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY, "
                      "user_id VARCHAR2(64), session_date DATE NOT NULL, "
                      "workout_type VARCHAR2(50) NOT NULL, exercise_name VARCHAR2(100) NOT NULL, "
                      "exercise_canonical VARCHAR2(100) NOT NULL, side VARCHAR2(10), "
                      "set_number NUMBER, reps NUMBER, duration_seconds NUMBER, "
                      "weight_kg NUMBER, machine_level NUMBER, is_warmup NUMBER(1) DEFAULT 0, "
                      "rpe NUMBER, notes VARCHAR2(500))'; "
                      "EXCEPTION WHEN OTHERS THEN NULL; END;")
            c.execute("BEGIN EXECUTE IMMEDIATE 'ALTER TABLE workout_sets ADD (user_id VARCHAR2(64))'; "
                      "EXCEPTION WHEN OTHERS THEN NULL; END;")
        else:
            c.execute("""CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                fitness_goal TEXT,
                goals_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )""")
            c.execute("""CREATE TABLE IF NOT EXISTS workout_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_date TEXT NOT NULL,
                workout_type TEXT NOT NULL,
                exercise_name TEXT NOT NULL,
                exercise_canonical TEXT NOT NULL,
                side TEXT,
                set_number INTEGER,
                reps INTEGER,
                duration_seconds INTEGER,
                weight_kg REAL,
                machine_level INTEGER,
                is_warmup INTEGER DEFAULT 0,
                rpe REAL,
                notes TEXT
            )""")
            cols = {row[1] for row in c.execute("PRAGMA table_info(workout_sets)").fetchall()}
            if "user_id" not in cols:
                c.execute("ALTER TABLE workout_sets ADD COLUMN user_id TEXT")
            c.execute("CREATE INDEX IF NOT EXISTS ix_workout_sets_user_id ON workout_sets(user_id)")
        self.conn.commit()

    def seed_default_profile(self) -> Optional[str]:
        """On a fresh install, create a 'Patrick' profile and backfill any orphaned
        workout_sets to him. If a profile already exists, just backfill orphans
        to the first profile. Returns the profile id, or None if no work was done.
        """
        first = self.query(
            "SELECT id FROM profiles ORDER BY created_at LIMIT 1" if self.driver == "sqlite"
            else "SELECT id FROM profiles ORDER BY created_at FETCH FIRST 1 ROWS ONLY"
        )
        if first:
            target_id = first[0]["id"]
        else:
            target_id = str(uuid.uuid4())
            self.execute(
                "INSERT INTO profiles (id, name, fitness_goal, goals_json) VALUES (?, ?, ?, ?)"
                if self.driver == "sqlite"
                else "INSERT INTO profiles (id, name, fitness_goal, goals_json) VALUES (:1, :2, :3, :4)",
                (target_id, "Patrick", "Building muscle · weight gain",
                 json.dumps(DEFAULT_GOALS_SEED)),
            )
            print(f"Seeded default profile: Patrick ({target_id})")

        # Always backfill orphaned rows so legacy data attaches to the first profile.
        self.execute(
            "UPDATE workout_sets SET user_id = ? WHERE user_id IS NULL"
            if self.driver == "sqlite"
            else "UPDATE workout_sets SET user_id = :1 WHERE user_id IS NULL",
            (target_id,),
        )
        return target_id

    def insert(self, rows, user_id: str):
        # Each row is (session_date, workout_type, exercise_name, exercise_canonical,
        # side, set_number, reps, duration_seconds, weight_kg, machine_level,
        # is_warmup, rpe, notes) — 13 fields. We prepend user_id for 14 total.
        c = self.conn.cursor()
        rows_with_user = [(user_id, *r) for r in rows]
        placeholders = (
            ", ".join(["?"] * 14)
            if self.driver == "sqlite"
            else ", ".join(f":{i + 1}" for i in range(14))
        )
        sql = f"""INSERT INTO workout_sets
            (user_id, session_date, workout_type, exercise_name, exercise_canonical,
             side, set_number, reps, duration_seconds, weight_kg, machine_level,
             is_warmup, rpe, notes)
            VALUES ({placeholders})"""
        if self.driver == "oracle":
            for r in rows_with_user:
                c.execute(sql, r)
        else:
            c.executemany(sql, rows_with_user)
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

    def load_user_goals(self, user_id: str) -> Dict[str, Any]:
        rows = self.query(
            "SELECT goals_json FROM profiles WHERE id = ?" if self.driver == "sqlite"
            else "SELECT goals_json FROM profiles WHERE id = :1",
            (user_id,),
        )
        if not rows or not rows[0].get("goals_json"):
            return DEFAULT_GOALS_SEED
        try:
            return json.loads(rows[0]["goals_json"])
        except (TypeError, json.JSONDecodeError):
            return DEFAULT_GOALS_SEED


db = DB()
