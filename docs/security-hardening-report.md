# ParcelPilot AI Security Hardening Report

Date: 2026-08-23

## Executive Summary

This pass reviewed ParcelPilot AI from an ethical-hacking perspective against the official assessment requirements and the local implementation. The strongest parts of the system are the deterministic tool layer, tenant-scoped order/ticket lookup, source precedence in retrieval, and the two-phase action proposal model.

The main hardening work completed in this pass focused on moving security checks closer to the mutation and data-access boundaries. Pending action tokens are now reauthorized at confirmation time, internal known issues are protected at the tool layer, and API-key-like content is redacted before exposure to model/UI responses.

## What Was Strengthened

### Backend Authorization

- Added shared role validation for `customer`, `support_agent`, `ops_manager`, and `admin`.
- Preserved demo persona switching while making API header auth take precedence over body-provided role/account values.
- Enforced customer tenant boundaries in internal data access paths where they were previously missing.
- Blocked direct customer access to `search_operational_issues_tool`; this is now enforced by the tool, not just by chatbot wording.

### Action Confirmation State Machine

- Revalidated authorization during `confirm_action`, not only during `prepare_action`.
- Bound every pending action to the real target account discovered from the database.
- Confirmations now check token status, expiry, caller role, caller account, financial limits, and target account consistency.
- Added target existence checks before issuing action tokens for cancellations, service credits, escalations, and ticket updates.
- Prevented cross-account cancellation/revocation of pending action tokens by customer users.
- Fixed cancellation receipts to record the actual previous order status.

### Secret And Sensitive Data Handling

- Added deterministic redaction for API-key-like, token-like, password, and secret patterns.
- Applied redaction to ticket payloads returned through query tools and API ticket list responses.
- Applied redaction to orchestrator responses, telemetry, citations, and pending action payloads.

### Reliability Fixes

- Removed an early Gemini-only API-key failure path so the orchestrator can use Groq or the deterministic fallback correctly.
- Fixed the `search_operational_issues` tool dispatch mismatch in the orchestrator.
- Routed “known issue” and “backend bug” customer prompts to the RBAC guard instead of falling through to document retrieval.

## Remaining Gaps And Recommended Next Work

### Priority 1: Production Authentication

Current auth is intentionally mocked for the assessment. In production, replace persona headers/body fields with signed sessions or JWTs issued by a real identity provider. The backend should derive `account_id`, `role`, and `user_name` from the verified session, never from browser-controlled form data.

### Priority 2: Immutable Audit Trail

`pending_actions` tracks proposal state, but the system should add an append-only audit log for prepare, confirm, cancel, expiry, failed confirmation, and authorization-denied events. Include actor, account, target entity, action token, timestamp, and decision reason.

### Priority 3: Broader Prompt-Injection Coverage

The current checks cover direct “ignore instructions” style attacks and data-layer isolation. Add a larger adversarial corpus covering indirect prompt injection from retrieved documents, malicious ticket descriptions, role impersonation, tool-argument manipulation, and requests to reveal system prompts or credentials.

### Priority 4: Retrieval Isolation And Offline Model Setup

The Chroma/SentenceTransformer path can attempt network access if the embedding model is not locally cached. For reliable demos and deployments, vendor/cache the embedding model or configure an offline embedding provider explicitly.

### Priority 5: Operational Monitoring

Add runtime monitoring for repeated 403s, failed action confirmations, unusual action preparation volume, repeated large credit attempts, and repeated cross-account lookup attempts. These events should feed an internal security/ops dashboard.

## Verification Added

New adversarial regression tests cover:

- Customer direct access to internal known issues is denied at the tool layer.
- Customer chatbot requests for internal known issues do not leak the catalog.
- Possession of an action token is insufficient for cross-account confirmation.
- Customers cannot cancel another tenant's pending action proposal.
- High-value service credits are rechecked at confirmation time.
- Tampered pending action parameters are blocked when target account no longer matches the pending action account.
- Tokens are not issued for nonexistent action targets.
- API-key-like strings are redacted.

Focused security test command:

```powershell
python -m unittest tests.test_security_adversarial
```

Result: 11 tests passed.
