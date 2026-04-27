# Comprehensive Project Execution Plan (PLAN.MD)

## Executive Summary
This document serves as the master roadmap for the Biome AI Strength Coach. It outlines the step-by-step transition from a stateless, single-user prototype to a highly intelligent, stateful, multi-tenant application leveraging Backboard AI and Supabase.

---

## Phase 1: Frontend Multi-Tenant Foundation (Visuals First)

Before we wire up complex cloud databases, we must establish the user experience and architectural patterns for multi-tenancy on the frontend.

### 1.1 UI Component Architecture
- **Navigation Update:** Introduce a global navigation header/sidebar that explicitly shows the currently active "Profile" or "User Context".
- **Profile Selector Modal:** A UI component allowing the user to switch between accounts (e.g., "Patrick" vs "Jim"). 
- **State Management:** Implement a global React Context (`UserContext`) that stores the `activeUserId`. All frontend components will read from this context to know whose data they should display.

### 1.2 View Segregation
- **Dashboard Isolation:** Ensure that the `TodayScreen` and `AnalyticsScreen` dynamically re-render based on the `activeUserId`.
- **Placeholder Login Flow:** Create a `LoginScreen` component that visually looks like a real authentication wall, but temporarily bypasses real security to allow fast testing during the hackathon.

---

## Phase 2: Backboard AI Integration (The Intelligence Layer)

The core value proposition of this hackathon submission is the integration of Backboard AI. We will replace the primitive, stateless GROQ LLM calls with a sophisticated multi-agent system.

### 2.1 Backend Refactoring (main.py)
- **Remove Stateless Calls:** Strip out the `_groq_chat` function. The system will no longer concatenate massive arrays of previous chat messages.
- **Backboard SDK Integration:** Introduce the Backboard REST API logic for creating Assistants, Threads, and Messages.

### 2.2 Thread Management (Persistent Memory)
- **Thread per User:** When a user is selected in the frontend (via the Phase 1 Profile Selector), the frontend will request a `thread_id` from the backend.
- **Stateful Conversations:** The `AskCoachScreen.tsx` will be updated to stop sending the `history` array. It will only send the user's latest text input and their assigned `thread_id`. Backboard will natively remember the entire conversation history.

### 2.3 Tool Calling Implementation (Smart Data Access)
Currently, the backend queries the database for volume, asymmetry, and metrics on *every single request* and injects it into the system prompt. This is wildly inefficient.
- **Define Tools:** We will expose our SQLite queries as Backboard "Tools" (e.g., `fetch_weekly_volume`, `fetch_recent_sets`, `fetch_pr`).
- **Autonomous Execution:** When the user asks "How is my chest volume?", the Backboard Assistant will autonomously decide to call `fetch_weekly_volume("chest")`, retrieve the specific data, and formulate an answer. This dramatically reduces token usage and prevents prompt overflow.

### 2.4 Intelligent Document Processing (RAG)
- **Scientific Grounding:** To prevent hallucination (a critical issue in fitness AI), we will upload PDFs of sports science literature and biomechanics textbooks to the Backboard Assistant.
- **RAG Execution:** When a user asks a complex physiological question, the AI will natively search its Document library before answering, ensuring clinically and scientifically accurate advice.

---

## Phase 3: The Multi-Tenant Cloud Migration (Supabase)

Once the frontend visually supports multiple users and the AI is intelligent enough to use Tool Calling, we will replace the underlying data engine.

*(For an exhaustive technical breakdown of this phase, refer to `MULTI-TENANT.MD`)*

### 3.1 Cloud Infrastructure Provisioning
- **Create Project:** Spin up a Supabase project.
- **Schema Migration:** Translate the SQLite schema into PostgreSQL syntax. Add `user_id` columns to all tables.
- **Security:** Implement Row Level Security (RLS) policies to ensure absolute data isolation between tenants.

### 3.2 Authentication Wiring
- **Install SDK:** Add `@supabase/supabase-js` to the React project.
- **Replace Mocks:** Replace the Phase 1 placeholder login flow with real Supabase Auth calls (Email/Password & OAuth).
- **JWT Protection:** Update the FastAPI backend to intercept requests, decode the Supabase JWT, and extract the `user_id`.

### 3.3 Backend Database Driver Swapping
- **Remove SQLite:** Delete the local `.db` files and SQLite connection strings.
- **Async Postgres:** Implement `asyncpg` or `psycopg2` in FastAPI to connect to the Supabase connection pool. Ensure all SQL queries pass the authenticated `user_id` to respect RLS policies.

---

## Phase 4: Production Polish & Demo Prep

With the core mechanics built, we must prepare the application for the hackathon judges and real-world usage.

### 4.1 Performance Optimization
- **Caching:** Implement Redis or in-memory caching in FastAPI for frequently accessed metrics (like all-time PRs).
- **Lazy Loading:** Update the React frontend to lazy-load charts and heavy components to improve the initial First Contentful Paint (FCP) metric.

### 4.2 Error Handling & Edge Cases
- **Network Resilience:** Add retry logic in the frontend for when Backboard API calls timeout or fail.
- **Empty States:** Design beautiful empty state UI components for brand-new users who have zero workout history logged.

### 4.3 Hackathon Deliverables
- **Video Walkthrough:** Record the required 4-5 minute YouTube demo, explicitly highlighting how Backboard Tool Calling and Threads replaced the old architecture.
- **Documentation:** Finalize the `README.md` to cleanly instruct judges on how to run the application locally or view the deployed version.

---

## Phase 5: Future Roadmap (Post-Hackathon)

If the project gains traction, here are the strategic next steps:

### 5.1 Advanced Analytics
- **Predictive Fatigue Modeling:** Use AI to analyze volume trends and predict when a user is likely to overtrain, preemptively suggesting deload weeks.
- **Computer Vision (AR):** Allow users to upload videos of their squats/deadlifts. Use vision models to analyze bar path and form breakdowns.

### 5.2 Social & Community Features
- **Leaderboards:** Allow users to opt-in to public leaderboards for specific lifts (e.g., 1RM Bench Press) within their weight class.
- **Program Sharing:** Let users publish their AI-generated workout splits so other tenants can subscribe to and follow them.

### 5.3 Mobile Application
- **React Native / Expo:** Port the web application to iOS and Android. A gym tracker is fundamentally a mobile-first utility.
- **Offline Mode:** Implement local caching (WatermelonDB or similar) so users can log sets in gym basements with poor cellular reception, syncing to Supabase when they reconnect.
