# ParcelPilot AI — Product & Architectural Decisions (Agent 01)

## Architecture Decision Record (ADR) Log

### ADR-01: Unified Agent Core with Context-Injected RBAC
- **Context**: The assessment requires supporting both customer-facing self-service and internal support operations without duplicating core agent logic.
- **Decision**: Build a single unified LangGraph/Function-Calling Agent Core in FastAPI. The session context (`account_id`, `user_role`, `user_name`) is injected into every request cycle. Tool registries and backend data layers filter available tools and SQL query predicates dynamically based on the verified caller identity.
- **Tradeoffs**: Requires rigorous backend authorization checks per tool call, but prevents drift, code duplication, and dual maintenance overhead.

---

### ADR-02: Deterministic Business Calculations (No LLM Mental Math)
- **Context**: LLMs are prone to arithmetic errors, hallucinated percentages, and inconsistent boundary condition handling (e.g. 30m cutoff, 2h vs 4h delay, INR 250 fee vs INR 500 cap).
- **Decision**: All fee calculations, service credit formulas, and SLA elapsed time evaluations are performed by deterministic Python functions exposed as tools (`calculate_cancellation_fee`, `calculate_service_credit`, `evaluate_sla_status`). The LLM is strictly responsible for extracting entities, invoking the calculation tool, and explaining the grounded result.
- **Tradeoffs**: Requires creating explicit calculation tools, but guarantees 100% mathematical precision and regulatory compliance.

---

### ADR-03: Two-Phase Prepare-Confirm-Execute Action Protocol
- **Context**: State-changing actions (cancellations, credits, escalations, ticket edits) must never execute solely because the LLM generated a tool call.
- **Decision**: When an agent decides an action is appropriate, it invokes `prepare_action(...)`. This registers a `PendingAction` object with a UUID token, expiration timestamp, parameters, and human-readable summary. The agent returns a structured Action Proposal Card. The actual execution is triggered only when a subsequent request explicitly submits the valid confirmation token.
- **Tradeoffs**: Requires maintaining pending action state and a two-turn conversation flow, but ensures total human-in-the-loop safety and zero autonomous rogue mutations.

---

### ADR-04: Metadata-Filtered RAG with Document Precedence
- **Context**: The candidate pack contains conflicting and deprecated documents (`02_Support_Policy_v2_DEPRECATED.pdf` vs `01_Support_Policy_v3_CURRENT.pdf`, and customer-specific enterprise agreements).
- **Decision**: All ingested documents carry rich metadata:
  - `document_type`: `contract`, `policy`, `sop`, `product_guide`
  - `status`: `current`, `deprecated`
  - `account_id`: `ACCT-001`, `ACCT-002`, `GLOBAL`
  - `authority_weight`: Contract (100) > SOP (80) > Policy (70) > Product Guide (60) > Deprecated (0)
  Deprecated documents are excluded by default in retrieval filters. When a query is scoped to an account, customer contract chunks are boosted and retrieved alongside global policies.
- **Tradeoffs**: Requires metadata tagging at ingestion, but completely prevents stale policy hallucinations.

---

### ADR-05: Isolation of Historical Tickets from Policy Corpus
- **Context**: Historical tickets in `ParcelPilot_Assessment_Data.xlsx` contain past human agent errors (e.g. `TKT-450` incorrectly claiming INR 250 fee for Northstar; `TKT-451` incorrectly claiming Growth limit is 3,000 rows).
- **Decision**: Historical tickets are stored strictly in the relational database (`tickets` table) for case lookup and context analysis. They are **EXCLUDED** from the RAG knowledge vector store. When an agent queries a historical ticket, it is explicitly prompted that past notes are context only and subordinate to authoritative policies.
- **Tradeoffs**: Prevents the agent from learning bad precedent, reinforcing policy correctness.

---

### ADR-06: Fixed Dataset Temporal Anchor (`2026-08-16 11:00 Asia/Kolkata`)
- **Context**: The assessment data represents a frozen snapshot at `2026-08-16 11:00 Asia/Kolkata`.
- **Decision**: All relative time calculations (e.g. "order booked 2 hours ago", "SLA elapsed 30 minutes ago", "pickup window ended 4.5 hours ago") use `2026-08-16 11:00:00` as the authoritative `CURRENT_TIMESTAMP` unless overridden.
- **Tradeoffs**: Ensures deterministic, reproducible test scenarios matching the assessment rubric.
