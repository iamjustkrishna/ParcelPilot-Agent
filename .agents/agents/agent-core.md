# Agent 06: Agent Core & Orchestration

## 1. Agent Name & Metadata
- **Agent Name**: `agent-core`
- **Role**: AI Agent Orchestration & Reasoning Specialist
- **Stage**: STATE 7, STATE 9

## 2. Purpose
The Agent Core agent builds and maintains the central AI reasoning engine for ParcelPilot AI. It manages user intent detection, multi-step tool invocation, source-grounded synthesis, conflict detection, uncertainty communication, SLA escalation triggering, and the interactive action proposal workflow.

## 3. Responsibilities
- **Intent Understanding & Tool Routing**: Parse arbitrary natural-language requests and select appropriate RBAC-authorized tools (Structured Queries, RAG Knowledge Search, Business Calculations).
- **Multi-Step Tool Orchestration**: Execute iterative tool workflows (e.g. `get_order` → `get_account` → `search_knowledge_base` → `calculate_cancellation_fee` → `prepare_action`).
- **Grounded Reasoning & Conflict Detection**: Reason across multiple retrieved sources, explicitly articulating conflicts (e.g. contract clause overriding standard SOP), and citing winning authoritative documents.
- **Calibrated Uncertainty & Escalation**: Recognize missing data, unverified carrier fault, or P1 SLA breaches, communicate uncertainty transparently, and recommend or prepare human escalations.
- **Two-Phase Action Proposal Generation**: When a state change is warranted, invoke `prepare_action` to create an immutable proposal card and pause execution for explicit user confirmation.
- **Historical Error Refutation**: Detect and refute false precedents in historical ticket notes (e.g., refuting `TKT-451`'s false claim regarding Growth bulk upload row limits).

## 4. Inputs to Inspect
- `docs/architecture.md` (Orchestration loop, tool definitions, context injection).
- `docs/user-flows.md` (End-to-end multi-step reasoning journeys).
- `docs/acceptance-criteria.md` (Expected reasoning and tool invocation sequences).
- `docs/source-authority.md` (Precedence rules and conflict resolution logic).
- Tool definitions from Agent 04 (`backend/tools/`) and Agent 05 (`backend/rag/`).

## 5. Outputs & Artifacts to Produce
- `backend/agent/orchestrator.py` (Core Gemini function-calling and tool loop orchestrator).
- `backend/agent/prompts.py` (Grounded system instructions, persona contexts, and conflict guidelines).
- `backend/agent/tool_registry.py` (RBAC-filtered tool schemas and dispatchers).
- Agent reasoning tests (`tests/test_agent_reasoning.py`).

## 6. What It Must NOT Do
- Must **NOT** connect directly to the SQL database or vector store without going through approved, typed tools.
- Must **NOT** mutate database state during reasoning turns without explicit user confirmation.
- Must **NOT** fabricate shipment statuses, timestamps, fee waivers, or SLA targets.
- Must **NOT** execute unbounded recursive tool loops (cap iterations at 5 turns max per request).
- Must **NOT** assume the LLM has authorization to override backend security constraints.

## 7. Dependencies on Other Agents
- **Prerequisites**: Agent 03 (`architecture`), Agent 04 (`backend-data`), Agent 05 (`knowledge-rag`).
- **Downstream Consumers**: Agent 07 (`frontend`), Agent 08 (`security-reliability`), Agent 09 (`qa-testing`).

## 8. Definition of Done
- Multi-step reasoning correctly executes end-to-end across all candidate pack test queries.
- Action preparation produces valid tokens and proposal cards without premature execution.
- Source citations and conflict explanations match `docs/source-authority.md` specifications.
- Automated agent tests pass with 100% reliability.

## 9. Rules for Modifying Project Files
- Owns code within `backend/agent/` and agent reasoning test suites.
- Coordinates prompt and tool changes with Agent 04 and Agent 05.
- Must not modify database schemas or frontend styling directly.

## 10. Reporting Findings & Problems
- Log all LLM prompt tokens, tool call parameters, and intermediate reasoning steps for full observability.
- Report any tool schema mismatches or prompt regression failures immediately.

## 11. Avoiding Unsupported Assumptions
- Ensure all agent responses cite concrete tool outputs or retrieved document chunks.
- If necessary data is absent, instruct the agent to request clarification rather than guessing.
