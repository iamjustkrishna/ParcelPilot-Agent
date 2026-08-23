# ParcelPilot AI — Source Authority & Conflict Precedence (Agent 02)

## 1. Hierarchy of Source Authority

When answering queries or making policy decisions, the system MUST enforce the following strict priority order:

```
┌────────────────────────────────────────────────────────┐
│  TIER 1: Signed Customer Enterprise Agreement          │  (Authority Weight: 100)
│  (e.g., Northstar Enterprise Agreement, LumenWorks)     │  Custom SLA, cancellation fee waiver, custom credits
└──────────────────────────┬─────────────────────────────┘
                           │ overrides
┌──────────────────────────▼─────────────────────────────┐
│  TIER 2: Current Standard Operating Procedure (SOP)     │  (Authority Weight: 80)
│  (e.g., Cancellation & Service Credit SOP v4)           │  Operational thresholds, credit calculation formulas
└──────────────────────────┬─────────────────────────────┘
                           │ overrides
┌──────────────────────────▼─────────────────────────────┐
│  TIER 3: Current Corporate Support Policy               │  (Authority Weight: 70)
│  (e.g., Support Policy v3 - Effective 1 May 2026)      │  Default P1/P2/P3 severity & plan response targets
└──────────────────────────┬─────────────────────────────┘
                           │ overrides
┌──────────────────────────▼─────────────────────────────┐
│  TIER 4: Product Operations Guide & Known Issues       │  (Authority Weight: 60)
│  (e.g., Operations Guide, Active KIs: KI-208, KI-211)  │  Product feature limits, active bugs, webhooks
└──────────────────────────┬─────────────────────────────┘
                           │ strictly subordinate
┌──────────────────────────▼─────────────────────────────┐
│  TIER 5: Relational Transaction Data                   │  (Authority Weight: 50)
│  (Structured SQL: accounts, orders, tickets)           │  Transactional ground truth (timestamps, statuses)
└────────────────────────────────────────────────────────┘
```

### Excluded / Discredited Sources:
- **Deprecated Policies (`02_Support_Policy_v2_DEPRECATED.pdf`)**: Weight `0`. Must NEVER be cited as active policy.
- **Historical Ticket Resolutions (`historical_resolution` column)**: Weight `0` (Context only). Past human agent notes are known to contain policy errors and must never override Tier 1–4 documents.

---

## 2. Conflict Matrix & Decision Rules

| Conflict Scenario | Tier A Source | Tier B Source | Winning Rule & Authority Justification | Concrete Example & Correct Outcome |
| :--- | :--- | :--- | :--- | :--- |
| **Cancellation Fee for Northstar (`ACCT-001`)** | **Northstar Agreement Clause 2**: "Northstar may cancel any BOOKED shipment before pickup with no cancellation fee, regardless of how long ago booked." (Tier 1) | **SOP v4 Section 1**: "After 30 minutes, charge INR 250 fee." (Tier 2) | **Tier 1 overrides Tier 2**. Contract specifically waives fee. | Order `ORD-1001` (booked 2h ago): **INR 0 fee**. Cites Northstar Agreement Clause 2. |
| **Failed Pickup Credit for LumenWorks (`ACCT-002`)** | **LumenWorks Agreement Clause 3**: "Delay > 4 hours past window end + carrier fault -> Fixed INR 300 credit." (Tier 1) | **SOP v4 Section 2**: "Delay > 2 hours + carrier fault -> lower of INR 500 or 10% shipment fee." (Tier 2) | **Tier 1 overrides Tier 2**. Contract clause explicitly replaces default timing and formula. | Order `ORD-2002` (4.5h delay, fee INR 2400): **INR 300 credit**. Cites LumenWorks Agreement Clause 3. |
| **Bulk Upload Max Capacity for Growth Plan** | **Product Operations Guide Section 1**: "Growth and Enterprise support Bulk Upload up to 5,000 rows per CSV. KI-208 is an active defect > 3,000 rows." (Tier 4) | **Historical Ticket TKT-451**: "Agent told customer Growth only supports 3,000 rows." (Tier 5 Context) | **Tier 4 overrides Tier 5 notes**. Historical agent note was an error. Product limit is 5,000 rows with active bug KI-208. | For `TKT-502`: Explain supported limit is 5,000, explain KI-208 defect, advise temporary workaround of splitting files into <3,000 rows. |
| **Standard Enterprise P1 SLA Target** | **Support Policy v3 Section 3**: Enterprise P1 target is 30 minutes 24x7. (Tier 3 Current) | **Support Policy v2 Section 3**: Enterprise P1 target is 1 hour. (Deprecated) | **Current Policy v3 supersedes Deprecated Policy v2**. | For Axis Labs (`ACCT-004`), P1 SLA is **30 minutes**, NOT 1 hour. |

---

## 3. Freshness & Temporal Calibration

- **Temporal Anchor**: All real-time evaluations are computed relative to dataset snapshot **`2026-08-16 11:00:00 Asia/Kolkata`**.
- **Resolved Issues Filter**:
  - `KI-176` (Address validation) was resolved on 18 July 2026. The agent MUST NOT attribute new shipment creation errors to KI-176 unless explicit address syntax errors match.
- **Active Known Issues Filter**:
  - `KI-208` (Bulk upload failure > 3,000 rows) opened 10 August 2026: **ACTIVE**.
  - `KI-211` (SwiftShip webhook delay 20 mins) opened 12 August 2026: **ACTIVE**.
