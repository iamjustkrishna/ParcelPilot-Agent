import datetime
from typing import Dict, Any, Optional
from backend.db.database import SessionLocal
from backend.db.models import Order, Account, Ticket, CustomerAgreement
from backend.tools.query_tools import verify_tenant_access

# Authoritative Snapshot Timestamp
SNAPSHOT_DATETIME = datetime.datetime(2026, 8, 16, 11, 0, 0)

def parse_iso_or_custom_dt(dt_str: str) -> Optional[datetime.datetime]:
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            pass
    return None

def calculate_cancellation_fee(order_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001") -> Dict[str, Any]:
    """
    Deterministically computes the cancellation fee and eligibility for an order based on booking time,
    current status, and customer-specific contract waivers.
    """
    session = SessionLocal()
    try:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"error": f"Order '{order_id}' not found."}
        
        verify_tenant_access(order.account_id, caller_role, caller_account_id)
        account = session.query(Account).filter(Account.account_id == order.account_id).first()
        agreement = session.query(CustomerAgreement).filter(CustomerAgreement.account_id == order.account_id).first()

        status = order.status.upper()
        booked_at = parse_iso_or_custom_dt(order.booked_at)
        cancel_req_at = parse_iso_or_custom_dt(order.cancellation_requested_at) or SNAPSHOT_DATETIME

        # Case 1: DRAFT
        if status == "DRAFT":
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "status": status,
                "eligible_for_cancellation": True,
                "cancellation_fee_inr": 0.0,
                "fee_waived": False,
                "authority_rule": "SOP v4 Section 1: DRAFT orders may be cancelled with no fee.",
                "action_recommendation": "Ready to cancel with INR 0 fee."
            }

        # Case 2: PICKED_UP
        if status == "PICKED_UP":
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "status": status,
                "eligible_for_cancellation": False,
                "cancellation_fee_inr": 0.0,
                "fee_waived": False,
                "authority_rule": "SOP v4 Section 1 & Northstar Agreement Clause 2: Shipment is already picked up by carrier. Cannot be cancelled directly.",
                "action_recommendation": "Reject cancellation. Advise customer to initiate the Return-to-Origin (RTO) workflow."
            }

        # Case 3: DELIVERED
        if status == "DELIVERED":
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "status": status,
                "eligible_for_cancellation": False,
                "cancellation_fee_inr": 0.0,
                "fee_waived": False,
                "authority_rule": "SOP v4 Section 1: Delivered shipments cannot be cancelled.",
                "action_recommendation": "Reject cancellation."
            }

        # Case 4: CANCELLED
        if status == "CANCELLED":
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "status": status,
                "eligible_for_cancellation": False,
                "cancellation_fee_inr": 0.0,
                "fee_waived": False,
                "authority_rule": "Order is already in CANCELLED status.",
                "action_recommendation": "No further action needed."
            }

        # Case 5: BOOKED (Not yet picked up)
        if status == "BOOKED":
            # Check Contract Precedence first (Tier 1)
            if agreement and agreement.free_cancellation_pre_pickup:
                return {
                    "order_id": order_id,
                    "account_id": order.account_id,
                    "status": status,
                    "eligible_for_cancellation": True,
                    "cancellation_fee_inr": 0.0,
                    "fee_waived": True,
                    "waiver_reason": "Signed Customer Agreement Clause 2 waives cancellation fee for all BOOKED shipments before pickup.",
                    "authority_rule": f"{account.account_name} Enterprise Agreement Clause 2 (Overrides standard SOP v4 INR 250 fee).",
                    "action_recommendation": "Ready to cancel with INR 0 fee under customer enterprise agreement terms."
                }

            # Standard SOP v4 Section 1 Rule (Tier 2)
            if booked_at:
                elapsed_minutes = (cancel_req_at - booked_at).total_seconds() / 60.0
            else:
                elapsed_minutes = 999.0

            if elapsed_minutes <= 30.0:
                return {
                    "order_id": order_id,
                    "account_id": order.account_id,
                    "status": status,
                    "elapsed_minutes": round(elapsed_minutes, 1),
                    "eligible_for_cancellation": True,
                    "cancellation_fee_inr": 0.0,
                    "fee_waived": False,
                    "authority_rule": "SOP v4 Section 1: Cancelled within 30-minute booking grace period (INR 0 fee).",
                    "action_recommendation": "Ready to cancel with INR 0 fee."
                }
            else:
                return {
                    "order_id": order_id,
                    "account_id": order.account_id,
                    "status": status,
                    "elapsed_minutes": round(elapsed_minutes, 1),
                    "eligible_for_cancellation": True,
                    "cancellation_fee_inr": 250.0,
                    "fee_waived": False,
                    "authority_rule": "SOP v4 Section 1: Cancelled more than 30 minutes after booking without contract waiver (Standard INR 250 fee applies).",
                    "action_recommendation": "Propose cancellation with INR 250 fee deducted."
                }

        return {
            "order_id": order_id,
            "status": status,
            "eligible_for_cancellation": False,
            "cancellation_fee_inr": 0.0,
            "authority_rule": "Unrecognized status.",
            "action_recommendation": "Escalate to support."
        }
    finally:
        session.close()

def calculate_service_credit(order_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001") -> Dict[str, Any]:
    """
    Deterministically computes service credit eligibility and amount for missed/delayed pickups based on
    window duration, carrier fault attribution, and customer agreement terms.
    """
    session = SessionLocal()
    try:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"error": f"Order '{order_id}' not found."}

        verify_tenant_access(order.account_id, caller_role, caller_account_id)
        account = session.query(Account).filter(Account.account_id == order.account_id).first()
        agreement = session.query(CustomerAgreement).filter(CustomerAgreement.account_id == order.account_id).first()

        window_end = parse_iso_or_custom_dt(order.pickup_window_end)
        pickup_actual = parse_iso_or_custom_dt(order.pickup_actual_at)
        evaluation_time = pickup_actual or SNAPSHOT_DATETIME

        # Fault validation
        if order.customer_fault:
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "eligible": False,
                "credit_amount_inr": 0.0,
                "reason": "Customer-caused delay or unreadiness is not eligible for service credit under SOP v4 Section 2.",
                "authority_rule": "SOP v4 Section 2"
            }

        if not order.carrier_fault and not order.pickup_actual_at:
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "eligible": False,
                "credit_amount_inr": 0.0,
                "uncertainty_warning": "Carrier fault is not yet verified or pickup timing is unknown. SOP v4 Section 3 states: Do not promise a credit when carrier fault is unverified.",
                "reason": "Carrier fault confirmation pending.",
                "authority_rule": "SOP v4 Section 3"
            }

        # Calculate delay hours past scheduled pickup window end
        if window_end:
            delay_seconds = (evaluation_time - window_end).total_seconds()
            delay_hours = max(0.0, delay_seconds / 3600.0)
        else:
            delay_hours = 0.0

        # Check Customer Agreement Clause (Tier 1)
        if agreement and agreement.credit_fixed_amount is not None and agreement.credit_delay_hours is not None:
            threshold_hours = agreement.credit_delay_hours
            if delay_hours >= threshold_hours and order.carrier_fault:
                credit_amount = float(agreement.credit_fixed_amount)
                requires_manager = credit_amount > 1000.0
                return {
                    "order_id": order_id,
                    "account_id": order.account_id,
                    "eligible": True,
                    "delay_hours": round(delay_hours, 2),
                    "threshold_hours": threshold_hours,
                    "credit_amount_inr": credit_amount,
                    "requires_manager_approval": requires_manager,
                    "authority_rule": f"{account.account_name} Service Agreement Clause 3: Fixed INR {int(credit_amount)} credit for delay > {int(threshold_hours)} hours with carrier fault (Replaces default SOP calculation).",
                    "action_recommendation": f"Issue INR {int(credit_amount)} service credit under agreement terms."
                }
            else:
                return {
                    "order_id": order_id,
                    "account_id": order.account_id,
                    "eligible": False,
                    "delay_hours": round(delay_hours, 2),
                    "threshold_hours": threshold_hours,
                    "credit_amount_inr": 0.0,
                    "reason": f"Delay of {round(delay_hours, 2)}h does not meet the agreement threshold of {threshold_hours} hours.",
                    "authority_rule": f"{account.account_name} Service Agreement Clause 3"
                }

        # Default SOP v4 Section 2 Calculation (Tier 2)
        # Threshold is > 2 hours delay, lower of INR 500 or 10% of shipment fee
        if delay_hours >= 2.0 and order.carrier_fault:
            calculated_credit = min(500.0, 0.10 * order.shipment_fee_inr)
            requires_manager = calculated_credit > 1000.0
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "eligible": True,
                "delay_hours": round(delay_hours, 2),
                "threshold_hours": 2.0,
                "shipment_fee_inr": order.shipment_fee_inr,
                "credit_amount_inr": round(calculated_credit, 2),
                "requires_manager_approval": requires_manager,
                "authority_rule": "SOP v4 Section 2: Lower of INR 500 or 10% of shipment fee for carrier delay > 2 hours.",
                "action_recommendation": f"Issue INR {round(calculated_credit, 2)} service credit."
            }
        else:
            return {
                "order_id": order_id,
                "account_id": order.account_id,
                "eligible": False,
                "delay_hours": round(delay_hours, 2),
                "credit_amount_inr": 0.0,
                "reason": f"Delay of {round(delay_hours, 2)}h is below the 2-hour minimum threshold for service credit.",
                "authority_rule": "SOP v4 Section 2"
            }
    finally:
        session.close()

def evaluate_sla_status(ticket_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001") -> Dict[str, Any]:
    """
    Evaluates response SLA status, elapsed time, and breach condition against account plan and signed agreements.
    """
    session = SessionLocal()
    try:
        ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return {"error": f"Ticket '{ticket_id}' not found."}

        verify_tenant_access(ticket.account_id, caller_role, caller_account_id)
        account = session.query(Account).filter(Account.account_id == ticket.account_id).first()
        agreement = session.query(CustomerAgreement).filter(CustomerAgreement.account_id == ticket.account_id).first()

        created_at = parse_iso_or_custom_dt(ticket.created_at) or SNAPSHOT_DATETIME
        elapsed_minutes = max(0.0, (SNAPSHOT_DATETIME - created_at).total_seconds() / 60.0)

        # Severity determination
        subject_desc = f"{ticket.subject} {ticket.description}".lower()
        if "outage" in subject_desc or "failing" in subject_desc or "exposure" in subject_desc or "security" in subject_desc:
            severity = "P1"
        elif "bulk" in subject_desc or "degraded" in subject_desc or "fails" in subject_desc:
            severity = "P2"
        else:
            severity = "P3"

        # Determine target minutes based on contract or Support Policy v3
        target_minutes = 240.0  # Default 4 business hours
        sla_source = "Support Policy v3"

        if account.account_id == "ACCT-001" and agreement:  # Northstar Custom SLA
            sla_source = "Northstar Enterprise Agreement Clause 1"
            if severity == "P1":
                target_minutes = 15.0
            elif severity == "P2":
                target_minutes = 60.0
            else:
                target_minutes = 480.0
        elif account.plan == "Enterprise":  # Standard Enterprise (e.g. Axis Labs)
            sla_source = "Support Policy v3 (Enterprise Plan)"
            if severity == "P1":
                target_minutes = 30.0
            elif severity == "P2":
                target_minutes = 120.0
            else:
                target_minutes = 480.0
        elif account.plan == "Growth":  # Growth Plan (e.g. LumenWorks)
            sla_source = "Support Policy v3 (Growth Plan)"
            if severity == "P1":
                target_minutes = 120.0
            elif severity == "P2":
                target_minutes = 240.0
            else:
                target_minutes = 960.0
        else:  # Standard Plan (e.g. Beacon Retail)
            sla_source = "Support Policy v3 (Standard Plan)"
            if severity == "P1":
                target_minutes = 240.0
            elif severity == "P2":
                target_minutes = 480.0
            else:
                target_minutes = 960.0

        is_breached = elapsed_minutes > target_minutes
        breach_minutes = max(0.0, elapsed_minutes - target_minutes)

        recommendation = "Normal queue handling."
        if severity == "P1":
            recommendation = "CRITICAL INCIDENT: Immediate escalation required."
        elif is_breached:
            recommendation = f"SLA BREACH DETECTED ({round(breach_minutes, 1)}m overdue): Escalate to Tier 2."

        return {
            "ticket_id": ticket_id,
            "account_id": ticket.account_id,
            "account_name": account.account_name,
            "severity": severity,
            "created_at": ticket.created_at,
            "elapsed_minutes": round(elapsed_minutes, 1),
            "target_sla_minutes": target_minutes,
            "is_breached": is_breached,
            "breach_minutes": round(breach_minutes, 1),
            "sla_source": sla_source,
            "recommendation": recommendation
        }
    finally:
        session.close()
