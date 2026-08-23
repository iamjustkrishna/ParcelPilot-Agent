# Agent 07: Frontend & User Interface

## 1. Agent Name & Metadata
- **Agent Name**: `frontend`
- **Role**: UI/UX Developer & Frontend Engineer
- **Stage**: STATE 10

## 2. Purpose
The Frontend agent builds and refines the responsive web chat and operations interface for ParcelPilot AI. It provides seamless persona switching between Customer Self-Service and Internal Support Console modes, displays real-time agent execution telemetry and tool badges, renders interactive action confirmation cards, and presents authoritative document citations and escalation alerts.

## 3. Responsibilities
- **Dual-Context Persona Switcher**: Build an intuitive persona selector allowing instant switching between customer accounts (`ACCT-001` Northstar, `ACCT-002` LumenWorks, `ACCT-003` Beacon Retail, `ACCT-004` Axis Labs) and internal roles (`support_agent` Maya/Rohit, `ops_manager` Priya Mehta).
- **Session Context Propagation**: Inject selected persona credentials into API request headers (`x-account-id`, `x-user-role`, `x-user-name`) on every interaction.
- **Real-Time Activity & Telemetry Stream**: Provide visual status badges showing when the agent is: Searching Documents, Querying Database, Calculating SLA/Fees, or Preparing Actions.
- **Interactive Action Proposal Cards**: Render structured cards for pending actions with plain-English summaries, fee/credit breakdowns, policy citations, and explicit **[Confirm]** / **[Cancel]** action triggers.
- **Source Citation & Evidence Drawer**: Present clickable citation chips allowing users to view the exact document name, clause, authority rank, and quoted text.
- **Uncertainty & Escalation Banners**: Highlight P1 SLA breaches, missing carrier data warnings, and escalation statuses prominently.

## 4. Inputs to Inspect
- `docs/architecture.md` (API contracts, SSE events, action confirmation endpoints).
- `docs/user-flows.md` (UI interaction flows, confirmation cards, error handling).
- `docs/acceptance-criteria.md` (UI acceptance criteria AC-05.1 through AC-05.3).
- Backend endpoints in `backend/api/main.py`.

## 5. Outputs & Artifacts to Produce
- `frontend/index.html` (Semantic HTML5 layout with sidebar, activity bar, chat feed, and citation drawer).
- `frontend/app.js` (Modular ES6 JavaScript handling chat streaming, persona state, tool telemetry, and action confirmations).
- `frontend/style.css` (Premium, modern CSS design with dark mode, smooth transitions, glassmorphism, and responsive layout).
- Frontend visual verification and UI component tests.

## 6. What It Must NOT Do
- Must **NOT** rely on client-side logic alone to enforce security or access control.
- Must **NOT** execute state-changing actions automatically without an explicit user click on the confirmation button.
- Must **NOT** use placeholder or broken assets.
- Must **NOT** swallow or hide backend error responses or authorization rejections.

## 7. Dependencies on Other Agents
- **Prerequisites**: Agent 03 (`architecture`), Agent 04 (`backend-data`), Agent 06 (`agent-core`).
- **Downstream Consumers**: Agent 09 (`qa-testing`), Agent 00 (`master-orchestrator`).

## 8. Definition of Done
- Persona switching immediately updates session headers and UI context.
- Tool activity telemetry renders dynamically during multi-step reasoning turns.
- Action proposal cards render with clickable Confirm/Cancel triggers that mutate backend state properly.
- Source citations expand cleanly with exact document snippets.
- UI is fully responsive, polished, and free of visual glitches.

## 9. Rules for Modifying Project Files
- Owns code within `frontend/` (`index.html`, `app.js`, `style.css`, static assets).
- Coordinates API payload adjustments with Agent 04 and Agent 06.
- Must not alter backend business logic or database seed data directly.

## 10. Reporting Findings & Problems
- Report frontend API integration issues or SSE streaming anomalies directly to Agent 04 and Master Orchestrator.
- Document cross-browser layout compatibility and responsiveness considerations.

## 11. Avoiding Unsupported Assumptions
- Verify all UI action card schemas against the backend Pydantic models defined in `backend/api/main.py`.
