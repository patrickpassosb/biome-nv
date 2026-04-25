Build the Biome web app — 2-hour hackathon delivery
You are building a complete working web application called Biome — a personal AI strength coach. I have 2 hours. Build the entire project end-to-end, working, deployable from this single prompt. No clarifying questions, no scaffolding back-and-forth — make decisions and ship.
What Biome does
Biome ingests gym workout CSV data, computes real training metrics with SQL/pandas, and uses an LLM to generate personalized workout recommendations grounded in those metrics. It also has a chat interface where the user can ask questions about their training and get data-grounded answers.
Tech stack (non-negotiable)

Backend: Python 3.11+ + FastAPI + uvicorn, single-file main.py
Database: Oracle Autonomous Database via oracledb Python driver, mTLS wallet auth
LLM: Anthropic API (anthropic Python SDK, model claude-sonnet-4-5) — env var ANTHROPIC_API_KEY
Frontend: Vite + React 18 + TypeScript + Tailwind CSS
Charts: Recharts
Icons: lucide-react

Project structure
biome/
  backend/
    main.py
    requirements.txt
    wallet/        (user provides mTLS wallet here)
    data/
      gym_data.csv (user provides)
    .env.example
  frontend/
    src/
      App.tsx
      main.tsx
      index.css
      components/
        Sidebar.tsx
        TodayScreen.tsx
        ProgressScreen.tsx
        LogScreen.tsx
        AskCoachScreen.tsx
    package.json
    vite.config.ts
    tailwind.config.js
    index.html
  README.md (setup steps)
Backend specification (single file main.py)
Database setup
On startup, connect to Oracle Autonomous Database using mTLS wallet auth. Env vars: ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN, ORACLE_WALLET_PASSWORD, wallet at ./wallet/. Use oracledb.init_oracle_client(config_dir="./wallet").
Create table on startup (drop if exists for idempotency):
sqlCREATE TABLE workout_sets (
  id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_date DATE NOT NULL,
  workout_type VARCHAR2(50) NOT NULL,
  exercise_name VARCHAR2(100) NOT NULL,
  exercise_canonical VARCHAR2(100) NOT NULL,
  side VARCHAR2(10),
  set_number NUMBER,
  reps NUMBER,
  duration_seconds NUMBER,
  weight_kg NUMBER,
  machine_level NUMBER,
  is_warmup NUMBER(1) DEFAULT 0,
  rpe NUMBER,
  notes VARCHAR2(500)
)
CSV import normalization
CSV columns: Date,Workout,Exercise,Set_Number,Reps,Duration_seconds,Weight_kg,Machine_level,Warm up,RPE,Notes. Date format M/D/YYYY. Rules:

Trim whitespace on all string fields
Lowercase exercise_canonical
If exercise name ends with " RS" or " LS", extract that into side column, store canonical without it
is_warmup = 1 if Warm up == "Yes" OR RPE < 6
Empty fields → NULL

Endpoints
POST /import          — upload CSV file, parse, insert, return {row_count}
GET  /workouts        — return all workout sessions grouped by date
GET  /recommend?workout_type=X — generate next-session recommendation
GET  /metrics/exercises — per-exercise progression for Progress screen
GET  /metrics/volume   — weekly volume per muscle group
GET  /metrics/asymmetry — left-right imbalances
POST /workouts        — log a new workout session, body: {date, workout_type, sets: [...]}
POST /chat            — body: {message: str, history: [{role, content}]}, returns coach reply with optional inline data
Hardcoded user goals (no goals UI in MVP)
pythonUSER_GOALS = {
  "objective": "muscle_and_weight_gain",
  "medical_context": "Underweight, weight gain is health-relevant",
  "training_days_per_week": 4,
  "rep_range": "6-15",
  "rpe_preference": "7-9",
  "volume_priority": "high",
  "current_injuries": "Right chest mild strain (early April), occasional left shoulder pain on pulls"
}
Metrics queries
Implement these as Python functions returning dicts/lists ready for JSON. Use raw SQL via oracledb:

Per-exercise status (last 8 weeks): session count, latest working weight or machine_level, max ever, avg RPE recent, trend (positive/flat/negative based on linear comparison of first half vs second half), status ("progressing" | "stalled" | "new")
Weekly volume per muscle group: map exercises to muscle groups using this dict (hardcode):

pythonEXERCISE_MUSCLE = {
  "abs elevation": "abs", "bicep curls": "biceps", "sit cable crunch": "abs",
  "dead hang": "grip", "knee push up": "chest", "knee push up open": "chest",
  "push up": "chest", "push up closed": "triceps", "peck deck": "chest",
  "lateral raises": "shoulders", "lat pulldown": "back",
  "seated cable row (traingle)": "back", "single arm lat pulldown": "back",
  "squat": "legs", "single leg bulgariansquat": "legs",
  "leg extension": "legs", "calf raises at the step": "calves",
  "single leg calf raises at the step": "calves"
}
Working volume = sum of reps × NVL(weight_kg, machine_level × 2, 1) per muscle per ISO week. Working sets only (is_warmup = 0).

Asymmetries: for exercises with both RS and LS sets in last 4 weeks, compare avg reps and avg RPE. Flag if reps differ by >20%.

/recommend endpoint logic

Build context payload combining: USER_GOALS, per-exercise status filtered to exercises typically in the requested workout_type, recent asymmetries, last 3 sessions of that workout_type with notes, current week's volume per muscle.
Call Claude with this exact system prompt:

You are Biome, a personal AI strength coach. You receive STRUCTURED METRICS about the user's training — never raw logs. Your reasoning is grounded in this structured summary and evidence-based programming principles.

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
- When weight gain appears slow despite good training, explicitly note caloric intake is usually limiting — don't pretend programming alone drives bodyweight
- Respect current exercise selection — guide progression, don't rewrite the program

Output ONLY valid JSON matching this exact schema (no markdown fences, no commentary):

{
  "session_plan": {
    "workout_type": string,
    "estimated_duration_minutes": number,
    "exercises": [
      {
        "name": string,
        "order": number,
        "sets": number,
        "target_reps": string,
        "target_weight_kg": number | null,
        "target_machine_level": number | null,
        "target_rpe": string,
        "rest_seconds": number,
        "rationale": string
      }
    ]
  },
  "overall_reasoning": string,
  "warnings": [string],
  "confidence": "high" | "medium" | "low"
}

Every recommendation ties back to the structured data. Be specific. Cite numbers from the data. No generic advice.

Parse JSON response, return to client. If parsing fails, retry once with explicit "your last response wasn't valid JSON, try again."

/chat endpoint logic
Accept {message, history}. System prompt instructs Claude to be a conversational coach with access to the user's data. Backend pre-fetches: per-exercise status, asymmetries, current week volume, last 3 sessions, USER_GOALS — and includes it as context in the system message. Claude responds naturally in English, citing real numbers. Optionally include data_visualization field in response if a chart would help (frontend can render or ignore).
CORS
Allow http://localhost:5173 for frontend dev.
Frontend specification
Visual design (match the user's Stitch design exactly)

Background #0a0a0a, surface cards #141414, borders #262626
Text white #fafafa, gray #d4d4d4, muted #737373
Accent amber #f59e0b for primary CTAs, active states
Status: green #10b981 (progressing), red #ef4444 (stalled/warning), blue #3b82f6 (info)
Inter font (use Tailwind default or import from Google Fonts)
All copy in English
Desktop-first, max content width 1200px

Layout
Persistent left sidebar 240px wide. Main content takes remainder. Sidebar contains:

"Biome" wordmark at top
Nav items: Today, Progress, Log Workout, Ask Coach (use lucide icons: Calendar, TrendingUp, Dumbbell, MessageCircle)
Active item: amber left border (4px), slightly lighter background #1a1a1a
Bottom of sidebar: small profile section "Patrick" + "Building muscle · Week 12"

Today screen (default route)
Page header: "Today" 32px bold. Subheader: today's date + workout type ("Saturday, April 26 · Push Day"). Right side: small pill "Estimated 55 min".
Two-column layout, 65/35 split.
Left column: list of exercise cards. Each card:

Exercise name 20px bold
Prescription line: "3 sets × 8-10 reps · 70 kg · RPE 8" — make weight/RPE prominent (slightly larger, amber color for the numbers)
Rest period in small muted text
Rationale paragraph below in 14px muted gray
Card padding 24px, rounded-lg, subtle border

Bottom of left column: amber primary button "Start workout" full width.
Right column:

"Today's Focus" card with overall_reasoning
"Warnings" card (only if warnings array non-empty), orange-tinted border
"Confidence" card with horizontal bar (high = full amber, medium = half, low = quarter)

Fetch from GET /recommend?workout_type=Push%20Day on mount. Show skeleton loaders during fetch.
Progress screen
Header: "Progress · Last 8 weeks". Three tabs: Exercises (default), Volume, Asymmetries.
Exercises tab: Two-column. Left 60%: list of exercises from /metrics/exercises. Each row: name, mini sparkline (Recharts LineChart 100×30, no axes), current value, status pill (green Progressing / red Stalled / blue New). Click row to select. Right 40%: large LineChart 400×280 of selected exercise weight or e1RM over time. Below chart: stats row — Best ever, Current, Trend (kg/week), Sessions.
Volume tab: Recharts BarChart, X = week, Y = total working sets, bars grouped by muscle (chest, back, legs, shoulders, arms, core). Below: summary "This week: X sets. Last week: Y sets. ±Z%" with status badge.
Asymmetries tab: List of imbalances from /metrics/asymmetry. Each card: exercise name, two horizontal bars side-by-side (left/right), percentage gap highlighted in red if >20%, short explanation.
Log Workout screen
Header "Log Workout · [today's date]". Workout type selector: horizontal pill buttons (Push, Pull, Legs, Weak Point, Custom). Selected = amber background.
Search input "Add exercise..." with autocomplete using existing exercise names from /workouts data.
List of added exercises. Each is a card: exercise name + remove (X) button, table with columns Set | Reps | Weight | Level | RPE | Notes (inline editable inputs), "+ Add set" button below table.
Bottom: large amber "Save workout" button. POSTs to /workouts.
Ask Coach screen
Match the user's screenshot exactly — see Stitch design. Layout:

Page header "Ask Coach" with subtitle "Ask anything about your training"
Centered welcome state when chat empty: small amber Bot icon in rounded square, "Ask me anything" headline, 2x2 grid of 4 suggestion cards with icons:

Adjust Macros / "Recalculate for rest day" (Utensils icon)
Swap Exercise / "Alternative for Barbell Squats" (Dumbbell icon)
Analyze Volume / "Am I doing too much chest?" (BarChart icon)
Recovery Status / "Should I train today?" (Bed icon)


Each card: icon left, title bold, subtitle muted, click sends question
When chat has messages: render history. User messages right-aligned, gray bubble (#1f1f1f), max-width 70%. Coach messages left-aligned, no bubble, just clean text. Highlight numbers in amber within coach text. Small "Biome" label above coach messages.
Bottom: persistent input bar with subtle border-top. Paperclip icon (decorative), input "Ask Biome anything...", amber circular send button with up-arrow icon.
Below input: muted disclaimer "AI CAN MAKE MISTAKES. VERIFY IMPORTANT TRAINING ADVICE."
Loading: animated 3-dot indicator where coach response will appear
On send: POST to /chat, append user message immediately, append coach response when received

Routing
Use React Router. Routes: / → Today, /progress, /log, /ask. Sidebar nav uses NavLink.
Build order (you decide internally, but in this priority)

Backend main.py complete — DB connection, table creation, CSV import, /recommend endpoint with Claude integration
Frontend scaffold — sidebar layout + routing + Today screen wired to /recommend
Ask Coach screen with /chat endpoint
Progress screen with charts
Log Workout screen

If running short on time, ship 1+2+3 and skip 4+5. Today and Ask Coach are demo-critical.
What to deliver
All files written, complete, working. README.md with exact setup steps:
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# set env vars (see .env.example)
# place mTLS wallet in ./wallet/
# place CSV at ./data/gym_data.csv
uvicorn main:app --reload --port 8000
# Then in another terminal:
curl -X POST -F "file=@data/gym_data.csv" http://localhost:8000/import

# Frontend
cd frontend
npm install
npm run dev
# Open http://localhost:5173
No tests. No Docker. No CI. No abstractions beyond what's needed. Single-file backend. Component files only split as listed above. Make decisions, ship working code.