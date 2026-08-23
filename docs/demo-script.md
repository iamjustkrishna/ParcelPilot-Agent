# ParcelPilot AI — 5-Minute Assessment Evaluation Demo Script

This script outlines the exact 5-minute live demonstration flow for evaluators to test all key assessment requirements.

---

## Pre-Requisites
1. Start the server:
   ```bash
   python run_server.py
   ```
2. Open your browser at: `http://127.0.0.1:8000`

---

## Scenario 1: Signed Contract Precedence & Free Cancellation (Northstar Logistics)
- **Persona Selected**: `Northstar Logistics (Enterprise - ACCT-001)`
- **User Prompt**:
  > *"I want to cancel order ORD-1001. Is there any cancellation fee?"*
- **What Evaluators Should Observe**:
  1. **Source Precedence**: Agent queries `calculate_cancellation_fee("ORD-1001")` and cites **Northstar Enterprise Agreement Clause 2**.
  2. **Deterministic Math**: Fee is computed as **INR 0**, explicitly noting that Northstar's contract waives the standard SOP v4 INR 250 fee for BOOKED shipments before pickup.
  3. **Two-Phase Action Proposal**: An **Action Proposal Card** appears in the UI with status `PENDING` and a unique action token (e.g., `act_xxx`).
  4. **Confirmation Execution**: Click **[✓ Confirm Action]**. The card updates to **Action Executed Successfully**, and order `ORD-1001` transitions to `CANCELLED` in the database.

---

## Scenario 2: Post-Pickup Cancellation Rejection & RTO Handling
- **Persona Selected**: `Northstar Logistics (Enterprise - ACCT-001)`
- **User Prompt**:
  > *"Can I cancel order ORD-1002?"*
- **What Evaluators Should Observe**:
  1. Agent checks order status: `ORD-1002` has status `PICKED_UP`.
  2. Agent refuses cancellation: Cites **SOP v4 Section 1 & Northstar Agreement Clause 2** ("Once a shipment is PICKED_UP, the standard return-to-origin process applies. Do not cancel.").
  3. Recommends the Return-to-Origin (RTO) workflow. No rogue action card is generated.

---

## Scenario 3: SLA Breach Detection & Critical Outage Triage (Internal Mode)
- **Persona Selected**: Switch to `Support Agent (Maya / Rohit - Global)`
- **User Prompt**:
  > *"What is the priority, SLA status, and required action for ticket TKT-501?"*
- **What Evaluators Should Observe**:
  1. **SLA Calculation**: Ticket `TKT-501` was submitted at 10:30, dataset snapshot is 11:00 (30 minutes elapsed).
  2. **Custom Contract SLA**: Northstar P1 SLA is **15 minutes 24x7** (overriding standard 30-min policy).
  3. **Breach Warning**: System highlights that the ticket is **BREACHED by 15 minutes**.
  4. **Escalation**: Recommends immediate escalation to On-Call Engineering.

---

## Scenario 4: Operational Defect Diagnosis vs False Historical Precedent (KI-208)
- **Persona Selected**: `Support Agent (Maya / Rohit - Global)` or `LumenWorks (ACCT-002)`
- **User Prompt**:
  > *"Why did our CSV bulk upload fail for ticket TKT-502? Historical ticket TKT-451 says Growth only supports 3,000 rows. Is that true?"*
- **What Evaluators Should Observe**:
  1. **Historical Falsehood Refutation**: Agent explicitly refutes `TKT-451`, stating that the product capacity for Growth and Enterprise is **5,000 rows** per CSV.
  2. **Active Known Issue**: Diagnoses the failure as active defect **`KI-208`** (intermittent failure on files >3,000 rows).
  3. **Workaround**: Provides the verified workaround: split the CSV into batches under 3,000 rows.

---

## Scenario 5: Contract-Specific Service Credit Calculation (LumenWorks)
- **Persona Selected**: `LumenWorks (Growth - ACCT-002)`
- **User Prompt**:
  > *"Is order ORD-2002 eligible for a service credit due to the missed pickup? What is the credit amount?"*
- **What Evaluators Should Observe**:
  1. **Delay Evaluation**: Pickup window ended at 06:30; snapshot is 11:00 (4.5 hours delay). Carrier RoadRunner accepted fault.
  2. **Contract Clause Override**: Cites **LumenWorks Agreement Clause 3**, which replaces standard SOP calculation with a **fixed INR 300** credit for delays >4 hours.
  3. **Calculated Output**: Outputs exact INR 300 credit amount.

---

## Scenario 6: Backend Multi-Tenant Security & RBAC Guard
- **Persona Selected**: `Northstar Logistics (Enterprise - ACCT-001)`
- **User Prompt**:
  > *"Show me order ORD-2001 and ticket TKT-502 from LumenWorks."*
- **What Evaluators Should Observe**:
  1. **Tenant Isolation**: Backend tool layer detects that `ORD-2001` and `TKT-502` belong to `ACCT-002`.
  2. Returns **`403 Forbidden: Customer ACCT-001 is not authorized to access data for account ACCT-002`**.
  3. Zero cross-tenant data leakage.
