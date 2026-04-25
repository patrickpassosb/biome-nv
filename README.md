# Biome – AI Strength Coach

Biome is a personal AI strength coach that reads your gym workout data, computes training metrics, and generates personalized workouts through an LLM (GPT OSS 120B via GROQ). Built for the OCI Track hackathon.

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, Oracle Autonomous Database (with SQLite fallback)
- **Frontend:** Vite + React 18 + TypeScript + Tailwind CSS + Recharts + Lucide-react
- **LLM:** GROQ API (GPT OSS 120B)

## Project Structure

```
biome/
├── backend/
│   ├── main.py              # FastAPI app, DB, CSV import, metrics, GROQ
│   ├── pyproject.toml       # Python deps (uv)
│   ├── .env.example         # Env template
│   ├── gym_data.csv         # Workout dataset 1
│   └── gym_data2.csv        # Workout dataset 2
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    └── src/
        ├── main.tsx         # React root
        ├── App.tsx          # Router + layout
        ├── api.ts           # Backend API helpers
        ├── index.css        # Tailwind entry
        ├── components/
        │   └── Sidebar.tsx
        └── screens/
            ├── TodayScreen.tsx
            ├── ProgressScreen.tsx
            ├── LogWorkoutScreen.tsx
            └── AskCoachScreen.tsx
```

## Quick Start

### Backend

```bash
cd backend
uv venv
uv pip install -e .
cp .env.example .env          # edit with your keys
uv run main.py                # or: uvicorn main:app --reload --port 8000
```

On first run the app auto-creates tables and imports `gym_data.csv` + `gym_data2.csv`. If Oracle connection fails it falls back to SQLite for local dev.

### Frontend

```bash
cd frontend
bun install
bun run dev                   # http://localhost:5173
```

## Environment Variables

Create `backend/.env`:

```
ORACLE_USER=<your-user>
ORACLE_PASSWORD=<your-password>
ORACLE_DSN=<your-dsn>
ORACLE_WALLET_PASSWORD=<optional>
GROQ_API_KEY=<your-groq-key>
```

## Features

- **Today** – AI-generated workout recommendation based on recent training load, focus, and imbalances.
- **Progress** – Interactive charts (exercise load trends, weekly volume by muscle group, left/right asymmetry flags).
- **Log Workout** – Log sets, reps, weight, RPE, notes, and side for any exercise.
- **Ask Coach** – Chat with the AI coach about programming, form, recovery, etc.

## Data Model

`biome_workouts` stores normalized exercises with load, reps, RPE, side, warmup flags, and notes. Computed metrics include:

- **Exercise metrics:** current / max load, session count, trend, status
- **Volume metrics:** weekly sets per muscle group
- **Asymmetry metrics:** left vs right rep and RPE gaps with % difference
