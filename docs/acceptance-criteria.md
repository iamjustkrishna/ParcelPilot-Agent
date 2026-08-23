# ParcelPilot AI — Acceptance Criteria (Agent 01)

## Category 1: Knowledge Retrieval & Source Precedence

- **AC-01.1 (Contract Supersedes SOP)**: When answering policy questions for an account with a custom contract (e.g. `ACCT-001` Northstar Logistics, `ACCT-002` LumenWorks), the agent MUST cite the signed agreement terms over general SOPs.
  - *Pass Condition*: For Northstar cancellation fee on `ORD-1001`, system outputs INR 0 (waived by contract) and explicitly notes that standard INR 250 fee is overridden.
  - *Pass Condition*: For LumenWorks service credit on `ORD-2002`, system calculates INR 300 (contract fixed credit) instead of default INR 240.
- **AC-01.2 (Deprecated Policy Exclusion)**: The system MUST NEVER cite `02_Support_Policy_v2_DEPRECATED.pdf` as active policy.
  - *Pass Condition*: When asked for standard Enterprise P1 SLA, system returns 30 minutes 24x7 (v3), NOT 1 hour (v2).
- **AC-01.3 (Historical Ticket Resolution Guard)**: Historical ticket resolution notes (e.g. `TKT-450`, `TKT-451`) MUST NEVER be treated as policy authority.
  - *Pass Condition*: When asked about Bulk Upload limits, system states product limit is 5,000 rows with a known issue (KI-208) failing > 3,000 rows, explicitly refuting TKT-451's statement that Growth plan only supports 3,000 rows.

---

## Category 2: Structured Data Queries & Calculations

- **AC-02.1 (Cancellation Fee Calculation)**:
  - DRAFT status: INR 0 fee.
  - BOOKED status <= 30 mins: INR 0 fee.
  - BOOKED status > 30 mins (Standard/Growth): INR 250 fee.
  - BOOKED status > 30 mins (Northstar Enterprise): INR 0 fee (contract waiver).
  - PICKED_UP status: Cancellation rejected; RTO workflow recommended.
  - DELIVERED status: Cancellation rejected.
- **AC-02.2 (Failed-Pickup Service Credit Calculation)**:
  - Standard/Growth (default): Delay > 2 hours past pickup window end + carrier fault + no customer fault -> `min(INR 500, 10% of shipment fee)`.
  - LumenWorks contract: Delay > 4 hours past pickup window end + carrier fault + no customer fault -> Fixed INR 300.
  - Credit > INR 1,000 requires manager approval flag.
  - Unknown carrier fault / missing pickup data -> Returns uncertainty warning and blocks credit calculation until verified.
- **AC-02.3 (SLA Breach Calculation)**:
  - Computes elapsed time between ticket `created_at` and current dataset snapshot (`2026-08-16 11:00`).
  - Evaluates against account SLA tier (e.g., TKT-501: Northstar P1 created 10:30, elapsed 30m vs 15m target -> BREACHED by 15m).

---

## Category 3: Action Execution & Confirmation State Machine

- **AC-03.1 (No Autonomous Execution)**: Under no circumstances may an action tool mutate the database during a reasoning step without an explicit confirmation signature.
- **AC-03.2 (Action Proposal Payload)**: When proposing an action, the agent must present:
  - Action Type (e.g. `cancel_order`, `apply_service_credit`, `create_escalation`, `update_ticket`)
  - Target Entity ID (e.g. `order_id`, `ticket_id`)
  - Parameters & Calculations (e.g. fee, credit amount, severity)
  - Business Rationale & Policy Reference
  - Action Confirmation ID Token
- **AC-03.3 (Confirmation Flow)**:
  - Upon user clicking [Confirm] or typing "Confirm action act_xxx", the backend executes the mutation and returns an immutable receipt.
  - Upon user clicking [Cancel] or typing "Reject", the action token is revoked with no database mutation.

---

## Category 4: Authorization & Multi-Tenancy (RBAC)

- **AC-04.1 (Customer Tenant Isolation)**:
  - In Customer Mode with `account_id = "ACCT-001"`, querying `ORD-2001` or `TKT-502` (`ACCT-002`) returns `403 Forbidden: Account access violation`.
  - Customer mode queries to list orders or tickets return ONLY records belonging to the authenticated account.
- **AC-04.2 (Role Boundary Enforcement)**:
  - Customer role cannot access internal known issues (`search_operational_issues`), internal notes, or manager approval tools.
  - Support Agent role can view all customer data and propose standard actions, but credits > INR 1,000 require Ops Manager role approval.
- **AC-04.3 (Backend-Enforced Security)**: Security boundaries are enforced via FastAPI dependency injection and SQLAlchemy tenant query filters, NOT merely LLM prompt conditioning.

---

## Category 5: User Interface & Experience

- **AC-05.1 (Real-Time Persona Switching)**: UI allows instant switching between:
  - Customer: Northstar Logistics (`ACCT-001`)
  - Customer: LumenWorks (`ACCT-002`)
  - Customer: Beacon Retail (`ACCT-003`)
  - Customer: Axis Labs (`ACCT-004`)
  - Internal: Support Agent (Maya / Rohit)
  - Internal: Ops Manager (Priya Mehta)
- **AC-05.2 (Live Activity & Telemetry)**: Visual indicators for Tool Execution, Document RAG Retrieval, Calculation Steps, and Pending Actions.
- **AC-05.3 (Interactive Confirmation Cards)**: Render dedicated UI cards for pending actions with explicit [Confirm] and [Reject] buttons.
