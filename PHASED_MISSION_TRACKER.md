# LifeOS Mission Tracker (Phase-by-Phase)

Updated: 2026-04-08  
Source inputs: `critical_flaw.env`, `missing.txt`, and current codebase audit.

## Sprint 1 — Stability and Core Orchestration

| Mission Name | Description | Status | Area |
|---|---|---|---|
| Context-Aware Agent Routing | Ensure user profile context is injected and routed safely with fallback behavior when confidence is low. | Done | Backend |
| Intent Reliability Hardening | Improve classifier confidence handling and fallback metadata; include missing agent intents in routing scope. | Done | Backend |
| Retryable Agent Execution | Add retry with short backoff for transient LLM/service errors during orchestrator calls. | Done | Backend |
| Action Execution Pipeline | Convert `ACTIONS_APPLIED` from empty telemetry into real action execution via structured JSON actions. | Done | Backend + Database |
| Planner Agent Bootstrap | Add initial `planner_agent` implementation and wire into orchestrator/intents. | Done | Backend |
| Knowledge Agent Bootstrap | Add initial `knowledge_agent` implementation and wire into orchestrator/intents. | Done | Backend |

## Sprint 2 — Data Safety and Persistence Guarantees

| Mission Name | Description | Status | Area |
|---|---|---|---|
| SQLite Backup/Export Strategy | Add scheduled export/backup flow, integrity checks, and restore runbook to reduce single-point DB loss risk. | Done | Database + Backend |
| Durable Action Contracts | Standardize action schema across agents (JSON contract + validation) and reject malformed actions with clear errors. | Done | Backend |
| Idempotent Saves | Prevent duplicate writes from retries/stream reconnects using idempotency keys or deterministic upserts. | Done | Backend + Database |

## Sprint 3 — Product Surface and Frontend Refactor

| Mission Name | Description | Status | Area |
|---|---|---|---|
| Chat Monolith Decomposition | Split `Chat.jsx` into focused modules (state, transport, renderer, action panels, session flow). | Pending | Frontend |
| Structured Agent Output Rendering | Replace regex-heavy parsing with schema-driven rendering for plans, tasks, meals, habits, and study outputs. | Pending | Frontend |
| Action Feedback UX | Display applied actions (saved task/meal/habit IDs + failures) in chat UI for transparency. | Pending | Frontend + Backend |

## Sprint 4 — Missing Product Capabilities

| Mission Name | Description | Status | Area |
|---|---|---|---|
| Planner → Task Integration | Ensure planner outputs create/update `Task` records with deadlines, priorities, and effort estimates. | In Progress | Backend + Database |
| Habit Coach Completion | Finalize habit prompts, logging flows, streak/nudge strategy, and reminder readiness. | In Progress | Backend + Database |
| Knowledge Retrieval Foundation | Add note storage schema and retrieval-ready indexing path (vector-ready abstraction). | Pending | Backend + Database |

## Sprint 5 — Quality, Integrations, and Trust

| Mission Name | Description | Status | Area |
|---|---|---|---|
| Automated Test Baseline | Add backend unit/integration tests and frontend smoke tests for core chat/orchestrator flows. | Pending | Backend + Frontend |
| Calendar/Notification Integrations | Add first-party integration points (calendar sync and reminder notifications). | Pending | Backend + Frontend |
| Personalization Maturity | Expand user profile preferences/goals usage across all agents and responses. | In Progress | Backend |

## Definition of Status

- **Done**: Implemented in code and wired into orchestration flow.
- **In Progress**: Partial implementation exists but requires completion or hardening.
- **Pending**: Not implemented yet.
