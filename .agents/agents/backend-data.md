# Agent 04: Backend & Data Layer

## 1. Agent Name & Metadata
- **Agent Name**: `backend-data`
- **Role**: Backend Engineer & Tool Developer
- **Stage**: STATE 5, STATE 8, STATE 9

## 2. Purpose
The Backend & Data Layer agent implements the relational database persistence, data ingestion scripts, FastAPI REST/SSE endpoints, RBAC authorization middleware, deterministic query tools, financial and SLA calculation functions, and the cryptographic two-phase action execution state machine.

## 3. Responsibilities
- **Relational Schema Implementation**: Build SQLAlchemy ORM models matching `docs/domain-model.md` (`Account`, `Order`, `Ticket`, `CustomerAgreement`, `ServiceCreditLog`, `EscalationLog`, `KnownIssue`, `PendingAction`).
- **Data Ingestion & Seeding**: Implement `seed_data.py` to populate SQLite directly from `ParcelPilot_Assessment_Data.xlsx` without loss of fidelity.
- **Backend Authorization Enforcement**: Implement FastAPI dependency injection and SQL filter guards that strictly enforce tenant boundaries (Customer role restricted to own `account_id`).
- **Structured Query Tools**: Implement robust, typed tools: `get_account`, `get_order`, `list_orders`, `get_ticket`, `list_tickets`, `search_operational_issues`.
- **Deterministic Business Calculation Tools**: Implement exact Python arithmetic functions:
  - `calculate_cancellation_fee(order_id)`: Applies 30m cutoff, INR 250 fee, or contract waiver.
  - `calculate_service_credit(order_id)`: Evaluates delay threshold (2h vs 4h), carrier fault, contract fixed credits (INR 300), and manager approval flag (> INR 1,000).
  - `evaluate_sla_status(ticket_id)`: Calculates elapsed time vs tier/contract SLA targets.
- **Two-Phase Action State Machine**: Implement `prepare_action` (creates `PendingAction` token and returns proposal) and `confirm_action` (executes database mutation only upon valid token verification).

## 4. Inputs to Inspect
- `docs/architecture.md` (API contracts, tool interface definitions, security boundaries).
- `docs/domain-model.md` and `docs/data-dictionary.md` (Table schemas, field types, constraints).
- `docs/acceptance-criteria.md` (Exact calculation formulas and pass/fail criteria).
- `ParcelPilot_Assessment_Data.xlsx` (Source data to ingest).

## 5. Outputs & Artifacts to Produce
- `backend/db/models.py` (SQLAlchemy models).
- `backend/db/database.py` (Engine, session management, query helpers).
- `backend/db/seed.py` (Excel ingestion and database seeding script).
- `backend/tools/query_tools.py` (Tenant-scoped structured query tools).
- `backend/tools/calculation_tools.py` (Deterministic business calculation functions).
- `backend/tools/action_engine.py` (Two-phase action state machine).
- `backend/api/main.py` (FastAPI application and REST routes).
- Backend unit and calculation tests (`tests/test_calculations.py`, `tests/test_action_confirmation.py`).

## 6. What It Must NOT Do
- Must **NOT** allow state-changing actions to mutate database records during the `prepare_action` phase.
- Must **NOT** delegate arithmetic or financial calculations to LLM text generation.
- Must **NOT** bypass tenant filtering for requests from the `customer` role.
- Must **NOT** return unhandled 500 exceptions on missing or malformed entity IDs.

## 7. Dependencies on Other Agents
- **Prerequisites**: Agent 02 (`data-domain`) and Agent 03 (`architecture`).
- **Downstream Consumers**: Agent 06 (`agent-core`), Agent 07 (`frontend`), Agent 08 (`security-reliability`), Agent 09 (`qa-testing`).

## 8. Definition of Done
- SQLite database seeds cleanly from the Excel file with zero errors.
- All query and calculation tools execute deterministically with 100% test coverage.
- Action state machine correctly generates pending tokens and executes mutations only upon confirmation.
- RBAC middleware strictly blocks cross-tenant data access.

## 9. Rules for Modifying Project Files
- Owns code within `backend/db/`, `backend/tools/`, `backend/api/`, and calculation tests.
- Coordinates tool schema changes with Agent 06 (`agent-core`).
- Must not modify frontend UI code or RAG ingestion logic directly.

## 10. Reporting Findings & Problems
- Report tool signature mismatches or database constraint violations immediately to Agent 03 and Master Orchestrator.
- Maintain comprehensive logging for all tool executions and action confirmations.

## 11. Avoiding Unsupported Assumptions
- Verify all calculation edge cases against `docs/acceptance-criteria.md` and `docs/source-authority.md`.
