# ParcelPilot AI — System Requirements (Agent 01)

## 1. Executive Summary & Vision

ParcelPilot AI is a dual-context AI-powered support and operations intelligence system designed for logistics operations. The system is engineered to serve two distinct operational personas:
1. **Customer-Facing Context (External Portal)**: Self-service support for authenticated account representatives (e.g., Northstar Logistics, LumenWorks, Beacon Retail, Axis Labs) to query shipment status, policy details, SLA terms, request allowable cancellations, and review billing/service credit eligibility.
2. **Authorized Internal Operations / Support Context (Internal Console)**: Comprehensive tooling for Support Representatives, Operations Managers, and CSMs to investigate cross-account tickets, identify outages/known issues, verify carrier faults, execute policy overrides or ticket status transitions, manage SLA escalations, and issue financial service credits.

The system is **NOT** a generic chatbot; it is a deterministic, tool-augmented, RBAC-enforced multi-agent reasoning engine where all state changes adhere to a strict **Prepare → Confirm → Execute** workflow.

---

## 2. Core Functional Requirements

### 2.1 Multi-Persona Natural Language Interface
- **FR-01**: Provide a web-based natural language chat interface accepting arbitrary domain questions in both Customer and Internal Support modes.
- **FR-02**: Provide seamless switching between user personas with mocked authentication / session headers (`x-account-id`, `x-user-role`, `x-user-name`).
- **FR-03**: Display step-by-step tool execution telemetry, retrieved document citations, and uncertainty or conflict warnings in real time.

### 2.2 Knowledge Retrieval & RAG System
- **FR-04**: Ingest and index authoritative corporate documents including:
  - `01_Support_Policy_v3_CURRENT.pdf` (Active Support SLA Policy)
  - `03_Cancellation_and_Service_Credit_SOP_v4.pdf` (Active Cancellation & Credit SOP)
  - `04_Product_Operations_Guide_and_Known_Issues.pdf` (Active Product Guide & Known Issues KI-208, KI-211, KI-176)
  - `05_Northstar_Logistics_Enterprise_Agreement.pdf` (Active Customer-specific Contract for ACCT-001)
  - `06_LumenWorks_Service_Agreement.pdf` (Active Customer-specific Contract for ACCT-002)
- **FR-05**: Explicitly segregate and deprioritize/exclude deprecated policies (e.g., `02_Support_Policy_v2_DEPRECATED.pdf`) from general policy answering, using metadata filtering and freshness scoring.
- **FR-06**: Prevent the ingestion of historical ticket resolutions as policy truth, isolating them strictly as descriptive historical context.

### 2.3 Structured Data Access & Calculation Tools
- **FR-07**: Provide deterministic SQL/ORM querying tools for accounts, orders, and tickets:
  - `get_account(account_id)`: Fetches account tier, CSM, status, and contract references.
  - `get_order(order_id)`: Fetches shipment status, timestamps, carrier, fees, and fault flags.
  - `list_orders(account_id, filters)`: Lists orders scoped to tenant.
  - `get_ticket(ticket_id)`: Fetches ticket metadata, subject, description, timestamps, and SLA status.
  - `list_tickets(account_id, filters)`: Lists tickets scoped to tenant.
  - `search_operational_issues()`: Searches active operational incidents and known issues.
- **FR-08**: Provide deterministic business calculation tools:
  - `calculate_cancellation_fee(order_id)`: Determines fee based on booking timestamp, pickup status, and active contract clauses.
  - `calculate_service_credit(order_id)`: Calculates credit eligibility, delay duration relative to pickup window, carrier fault verification, contract overrides, and manager approval requirements (> INR 1,000).
  - `evaluate_sla_status(ticket_id)`: Calculates elapsed time vs P1/P2/P3 target based on account tier and contract SLA overrides (e.g., Northstar 15-minute P1).

### 2.4 State-Changing Actions & Strict Confirmation State Machine
- **FR-09**: Support real, auditable state-changing actions:
  - `action_cancel_order(order_id, reason)`: Transitions order to `CANCELLED`, applies calculated fee.
  - `action_apply_service_credit(order_id, amount_inr, reason, manager_approval_notes)`: Grants credit up to account monthly caps.
  - `action_create_escalation(ticket_id, severity, escalation_reason, assigned_team)`: Escalates breached/P1 tickets.
  - `action_update_ticket(ticket_id, status, notes)`: Updates ticket lifecycle status.
- **FR-10**: Every state-changing action MUST enforce the 2-phase lifecycle:
  1. `prepare_action`: Generates a pending action proposal with an idempotency token, action summary, required parameters, and estimated impact.
  2. `confirm_action`: Explicit user confirmation payload (or UI button click) triggers execution.
- **FR-11**: The LLM is strictly prohibited from executing state changes autonomously without user confirmation.

### 2.5 Multi-Step Reasoning & Conflict Detection
- **FR-12**: Support chained multi-step reasoning (e.g., Order lookup → Contract inspection → SOP comparison → Fee calculation → Action preparation).
- **FR-13**: Detect and articulate conflicts between general SOPs and customer-specific contractual agreements, always prioritizing signed customer contracts.
- **FR-14**: Refuse unsupported queries and express calibrated uncertainty when timestamps, carrier fault, or required data are missing.

---

## 3. Security & Access Control Requirements

- **SR-01 (Backend-Enforced RBAC & Multi-Tenancy)**: Authorization must be evaluated at the FastAPI middleware/tool level. If a Customer user requests data for an account ID outside their session token, the tool returns `403 Forbidden` / `Unauthorized Account Access`.
- **SR-02 (Role Permissions Boundary)**:
  - `customer`: Read access to own orders/tickets/contract; Action access limited to proposing cancellation of own eligible orders. No access to other customer data, internal ticket resolutions, or manager override actions.
  - `support_agent`: Read access across accounts; Action access to update tickets, prepare cancellations, and prepare standard service credits <= INR 1,000.
  - `ops_manager` / `admin`: Full read/write access including approval of service credits > INR 1,000, SLA escalations, and system configuration.
- **SR-03 (Adversarial Prompt & Injection Defense)**: System instructions, tool boundaries, and output guardrails prevent prompt injection from bypassing confirmation gates or leaking sensitive credentials (e.g., API key handling in TKT-505).

---

## 4. Operational Intelligence Requirements

- **OI-01 (Proactive Webhook / Carrier Delay Detection)**: Connect ticket symptoms with known issues (e.g., linking SwiftShip "still BOOKED" complaints to KI-211 webhook lag, or bulk upload 500s to KI-208).
- **OI-02 (Proactive SLA Breach Warning)**: Automatically compute SLA deadlines for active tickets and highlight breached tickets (e.g., TKT-501 Northstar P1 breached by 15 mins).
