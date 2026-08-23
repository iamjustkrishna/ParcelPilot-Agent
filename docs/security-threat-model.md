# ParcelPilot AI — Security Architecture & Threat Model (Agent 08)

## 1. Executive Summary & Security Objectives
ParcelPilot AI enforces strict defense-in-depth across authentication, RBAC authorization, session multi-tenancy, deterministic financial calculations, and two-phase action execution. The core security principle is that the **Large Language Model (LLM) is an untrusted reasoning component** and must never hold ultimate authority over database mutations or security decisions.

---

## 2. Threat Vector Analysis & Mitigations

| Threat ID | Threat Category | Threat Description | Mitigation Strategy | Enforcement Layer | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **TH-01** | **Multi-Tenant Isolation** | A malicious customer user attempts to query orders, tickets, or agreements belonging to another account (e.g. ACCT-001 requesting ACCT-002). | Database query tools and FastAPI middleware enforce strict tenant filtering: `WHERE account_id = :session_account_id`. | Python Tool & DB Layer | **SECURE (Verified in `test_rbac.py`)** |
| **TH-02** | **Autonomous State Mutation** | The LLM attempts to execute a destructive state change (order cancellation, credit issuance, escalation) on its own during a conversation turn. | LLM is provided only with `prepare_action` (creates a pending proposal with UUID token). Real execution requires an explicit human HTTP POST to `/api/actions/confirm`. | Two-Phase State Machine | **SECURE (Verified in `test_action_confirmation.py`)** |
| **TH-03** | **Financial Limit Bypass** | A user or support agent attempts to self-issue service credits exceeding the authorized threshold (> INR 1,000). | `prepare_action` and `confirm_action` check user role. Credits > INR 1,000 require explicit `ops_manager` or `admin` role approval. | Action Engine Backend | **SECURE (Verified in `test_rbac.py`)** |
| **TH-04** | **Replay & Forged Action Attack** | An attacker submits fabricated action tokens or replays an already executed token. | Action tokens are cryptographically random UUIDs stored in SQLite with state `PENDING` and a 15-minute expiration timestamp. Replays return `400 Bad Request`. | SQLite `pending_actions` | **SECURE (Verified in `test_action_confirmation.py`)** |
| **TH-05** | **Prompt Injection & Jailbreaks** | Adversarial input instructs the agent to ignore system instructions or enter "SuperAdmin" mode. | System prompts enforce strict grounding; tool definitions reject unauthorized role changes; backend tool layer validates caller session headers independently. | System Prompt + Tool Layer | **SECURE (Verified in `test_security_adversarial.py`)** |
| **TH-06** | **Stale / Deprecated Policy Hallucination** | System cites deprecated policies (e.g. `Support Policy v2`) or flawed historical ticket notes (`TKT-450`, `TKT-451`). | Deprecated policies are filtered out of ChromaDB (`status == 'CURRENT'`). Historical tickets are excluded from the vector knowledge store and treated as context only. | ChromaDB Retrieval + Prompt | **SECURE (Verified in `test_rag.py`)** |
| **TH-07** | **Sensitive Credential Exposure** | Customer or agent receives raw production API keys or credentials exposed in tickets (e.g. `TKT-505`). | System instructions explicitly scrub sensitive credentials, and historical resolution notes are stripped from customer-role API responses. | Tool Layer + System Prompt | **SECURE (Verified in `test_security_adversarial.py`)** |
