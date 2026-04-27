# Multi-Tenant Architecture & Supabase Migration

This document outlines the future state of the Biome application, where it will transition from a single-user local SQLite database to a fully-fledged, multi-tenant SaaS platform using Supabase (PostgreSQL).

## 1. Why Supabase?

While SQLite is excellent for rapid prototyping and local development during a hackathon, it fundamentally lacks the capability to handle thousands of concurrent users writing data simultaneously. Supabase solves this by providing:

*   **Managed PostgreSQL:** The industry standard for relational data.
*   **Built-in Authentication:** No need to build custom JWT issuing, password hashing, or social login logic.
*   **Row Level Security (RLS):** This is the core of our multi-tenant strategy. It guarantees at the database engine level that User A can never query or modify User B's workout data.
*   **Realtime Subscriptions:** We can push live workout updates or coach notifications directly to the frontend.

## 2. Multi-Tenant Database Schema

To support multiple users, every core table must be linked to a specific user.

### 2.1 The `users` Table (Managed by Supabase Auth)
We will rely on Supabase's built-in `auth.users` table for authentication, but we will create a public `profiles` table to store application-specific data.

```sql
CREATE TABLE public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
  fitness_goal TEXT,
  preferred_split TEXT
);
```

### 2.2 Updating the `workout_sets` Table
Our existing workout table will be migrated to Postgres and updated to include a `user_id`.

```sql
CREATE TABLE public.workout_sets (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) NOT NULL,
  session_date DATE NOT NULL,
  workout_type TEXT NOT NULL,
  exercise_name TEXT NOT NULL,
  reps INTEGER NOT NULL,
  weight_kg DECIMAL,
  machine_level INTEGER,
  rpe INTEGER,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);
```

## 3. Implementing Row Level Security (RLS)

RLS acts as a firewall around every single row in the database.

### 3.1 Enabling RLS
```sql
ALTER TABLE public.workout_sets ENABLE ROW LEVEL SECURITY;
```

### 3.2 Security Policies
We will define policies that explicitly tell Postgres who can view/edit what.

**SELECT Policy (Read):**
```sql
CREATE POLICY "Users can view their own workout sets" 
ON public.workout_sets FOR SELECT 
USING (auth.uid() = user_id);
```

**INSERT Policy (Create):**
```sql
CREATE POLICY "Users can insert their own workout sets" 
ON public.workout_sets FOR INSERT 
WITH CHECK (auth.uid() = user_id);
```

These policies mean our Python backend and React frontend don't need complex `if user_id == X` logic. If a user tries to run `SELECT * FROM workout_sets`, Postgres will silently intercept it and only return rows where `user_id` matches their JWT token.

## 4. Frontend Authentication Flow

To make this functional in the future, we will integrate `@supabase/supabase-js` into the React application.

### 4.1 Login / Signup Screens
We will build a dedicated `/auth` route containing:
*   Email/Password registration.
*   "Sign in with Google" OAuth integration.
*   Password reset flows.

### 4.2 Auth State Management
We will use a React Context (`AuthProvider`) to globally track if a user is logged in.

```typescript
// Future implementation snippet
export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session))
    supabase.auth.onAuthStateChange((_event, session) => setSession(session))
  }, [])
  
  return <AuthContext.Provider value={{ session }}>{children}</AuthContext.Provider>
}
```

## 5. Backend Migration (FastAPI)

When we migrate, `backend/main.py` will no longer query SQLite.

### 5.1 Verifying JWTs
When the React frontend makes a request to `/chat` or `/recommend`, it will pass the Supabase JWT in the `Authorization` header. FastAPI will decode this token to securely identify the user.

### 5.2 Connecting to Postgres
We will replace the SQLite driver with `psycopg2` or `asyncpg` to query the Supabase Postgres database. We will configure the database connection to respect the authenticated user's context so RLS policies trigger correctly.

## 6. The Migration Strategy

1. **Build the UI (Current Step):** We are currently building the frontend UI (User Selection/Profile Switcher) to simulate multi-tenancy visually.
2. **Backboard Core:** We are ensuring the AI logic works perfectly with the mock data.
3. **Database Spin-up:** We will create the Supabase project and execute the SQL schema.
4. **Auth Integration:** We will wire up the login screens.
5. **Data Import:** We will create a script to read `gym_data.csv` and insert it into Supabase, associating it with your primary user account.

By following this architecture, Biome will securely scale from a local hackathon project to a production-ready application capable of serving thousands of athletes.
