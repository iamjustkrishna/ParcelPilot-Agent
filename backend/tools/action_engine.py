import json
import uuid
import datetime
from typing import Dict, Any, Optional
from backend.db.database import SessionLocal
from backend.db.models import PendingAction, Order, Ticket, ServiceCreditLog, EscalationLog, Account
from backend.security import MANAGER_ROLES, normalize_role, redact_sensitive_payload, SecurityError

CUSTOMER_MUTATION_ERROR = {
    "apply_service_credit": "Unauthorized: Customers cannot self-issue service credits. Please contact Support.",
    "create_escalation": "Unauthorized: Customer users cannot directly escalate tickets or modify internal ticket states.",
    "update_ticket": "Unauthorized: Customer users cannot directly escalate tickets or modify internal ticket states.",
}


ACTION_TYPE_SYNONYMS = {
    "order_cancel": "cancel_order",
    "cancel_shipment": "cancel_order",
    "cancel_booking": "cancel_order",
    "cancel_request": "cancel_order",
    "service_credit": "apply_service_credit",
    "issue_service_credit": "apply_service_credit",
    "escalate_ticket": "create_escalation",
    "ticket_escalation": "create_escalation",
    "ticket_update": "update_ticket",
}

def normalize_action_type(action_type: str) -> str:
    cleaned = (action_type or "").strip().lower()
    return ACTION_TYPE_SYNONYMS.get(cleaned, cleaned)

def _target_account_for_action(session, action_type: str, parameters: Dict[str, Any]) -> Optional[str]:
    action_type = normalize_action_type(action_type)
    if action_type in ["cancel_order", "apply_service_credit"]:
        order_id = str(parameters.get("order_id") or parameters.get("order") or "").strip()
        if order_id and order_id.isdigit() and not order_id.startswith("ORD-"):
            order_id = f"ORD-{order_id}"
            parameters["order_id"] = order_id
        if not order_id:
            raise SecurityError(f"Missing required order_id for {action_type}.")
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            raise SecurityError(f"Target order '{order_id}' not found.")
        return order.account_id

    if action_type in ["create_escalation", "update_ticket"]:
        ticket_id = str(parameters.get("ticket_id") or parameters.get("ticket") or "").strip()
        if ticket_id and ticket_id.isdigit() and not ticket_id.startswith("TKT-"):
            ticket_id = f"TKT-{ticket_id}"
            parameters["ticket_id"] = ticket_id
        if not ticket_id:
            raise SecurityError(f"Missing required ticket_id for {action_type}.")
        ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            raise SecurityError(f"Target ticket '{ticket_id}' not found.")
        return ticket.account_id

    raise SecurityError(f"Unknown action type: {action_type}")


def _authorize_action(
    session,
    action_type: str,
    parameters: Dict[str, Any],
    user_role: str,
    caller_account_id: str,
    pending_account_id: Optional[str] = None,
) -> str:
    user_role = normalize_role(user_role)
    target_account_id = _target_account_for_action(session, action_type, parameters)

    if pending_account_id and target_account_id != pending_account_id:
        raise SecurityError(
            f"Action target account '{target_account_id}' does not match pending action account '{pending_account_id}'."
        )

    if user_role == "customer" and target_account_id != caller_account_id:
        raise SecurityError("Unauthorized: Customer cannot act on records from other accounts.")

    if action_type in CUSTOMER_MUTATION_ERROR and user_role == "customer":
        raise SecurityError(CUSTOMER_MUTATION_ERROR[action_type])

    if action_type == "apply_service_credit":
        amount = float(parameters.get("amount_inr", 0.0))
        if amount > 1000.0 and user_role not in MANAGER_ROLES:
            raise SecurityError(
                f"Authorization Required: Service credits exceeding INR 1,000 (requested INR {amount}) require Ops Manager approval."
            )

    return target_account_id

def prepare_action(
    session_id: str,
    account_id: str,
    user_role: str,
    user_name: str,
    action_type: str,
    parameters: Dict[str, Any],
    summary: str
) -> Dict[str, Any]:
    """
    Registers a proposed state-changing action in the pending_actions table with a 15-minute TTL.
    Does NOT execute the action. Returns a proposal token and summary for explicit user confirmation.
    """
    try:
        user_role = normalize_role(user_role)
        action_type = normalize_action_type(action_type)
    except SecurityError as e:
        return {"error": str(e)}

    action_token = f"act_{uuid.uuid4().hex[:12]}"
    now = datetime.datetime.now()
    expires_at = now + datetime.timedelta(minutes=15)

    session = SessionLocal()
    try:
        effective_account_id = _authorize_action(
            session=session,
            action_type=action_type,
            parameters=parameters,
            user_role=user_role,
            caller_account_id=account_id,
        )

        pending = PendingAction(
            action_token=action_token,
            session_id=session_id,
            account_id=effective_account_id,
            user_role=user_role,
            action_type=action_type,
            parameters=json.dumps(parameters),
            summary=summary,
            status="PENDING",
            created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            expires_at=expires_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        session.add(pending)
        session.commit()

        return {
            "action_token": action_token,
            "action_type": action_type,
            "account_id": effective_account_id,
            "summary": summary,
            "parameters": parameters,
            "status": "PENDING",
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S"),
            "requires_confirmation": True,
            "message": "Action prepared. Please review the details and click [Confirm] to execute."
        }
    except Exception as e:
        session.rollback()
        return {"error": f"Failed to prepare action: {str(e)}"}
    finally:
        session.close()

def confirm_action(
    action_token: str,
    user_role: str = "customer",
    user_name: str = "Customer",
    account_id: str = "ACCT-001"
) -> Dict[str, Any]:
    """
    Executes a previously prepared action upon receiving explicit user confirmation and valid token.
    """
    try:
        user_role = normalize_role(user_role)
    except SecurityError as e:
        return {"error": str(e)}

    session = SessionLocal()
    try:
        pending = session.query(PendingAction).filter(PendingAction.action_token == action_token).first()
        if not pending:
            return {"error": f"Action token '{action_token}' not found."}

        if pending.status != "PENDING":
            return {"error": f"Action '{action_token}' cannot be executed because its status is '{pending.status}'."}

        # Check expiration
        expires_at = datetime.datetime.strptime(pending.expires_at, "%Y-%m-%d %H:%M:%S")
        if datetime.datetime.now() > expires_at:
            pending.status = "EXPIRED"
            session.commit()
            return {"error": f"Action proposal '{action_token}' has expired. Please initiate a new request."}

        params = pending.get_parameters_dict()
        action_type = pending.action_type
        try:
            _authorize_action(
                session=session,
                action_type=action_type,
                parameters=params,
                user_role=user_role,
                caller_account_id=account_id,
                pending_account_id=pending.account_id,
            )
        except SecurityError as e:
            return {"error": str(e)}

        result_receipt = {}

        # 1. Action: cancel_order
        if action_type == "cancel_order":
            order_id = params.get("order_id")
            order = session.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                return {"error": f"Target order '{order_id}' not found."}
            
            fee = params.get("fee_inr", 0.0)
            previous_status = order.status
            order.status = "CANCELLED"
            order.notes = f"{order.notes or ''} [Cancelled via action {action_token} by {user_name} ({user_role}) with fee INR {fee}]".strip()
            session.commit()

            result_receipt = {
                "action_type": "cancel_order",
                "order_id": order_id,
                "previous_status": previous_status,
                "new_status": "CANCELLED",
                "cancellation_fee_inr": fee,
                "executed_by": user_name,
                "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"Order {order_id} has been successfully CANCELLED (Fee: INR {fee})."
            }

        # 2. Action: apply_service_credit
        elif action_type == "apply_service_credit":
            order_id = params.get("order_id")
            amount = float(params.get("amount_inr", 0.0))
            reason = params.get("reason", "Service credit for delay")
            credit_id = f"CRD-{uuid.uuid4().hex[:8].upper()}"

            credit_log = ServiceCreditLog(
                credit_id=credit_id,
                order_id=order_id,
                account_id=pending.account_id,
                amount_inr=amount,
                reason=reason,
                approval_status="APPROVED_MANAGER" if user_role in ["ops_manager", "admin"] else "APPROVED_AUTO",
                approved_by=user_name,
                created_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(credit_log)
            session.commit()

            result_receipt = {
                "action_type": "apply_service_credit",
                "credit_id": credit_id,
                "order_id": order_id,
                "amount_inr": amount,
                "reason": reason,
                "approved_by": user_name,
                "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"Service credit of INR {amount} has been successfully applied to account {pending.account_id}."
            }

        # 3. Action: create_escalation
        elif action_type == "create_escalation":
            ticket_id = params.get("ticket_id")
            severity = params.get("severity", "P1")
            escalation_reason = params.get("escalation_reason", "SLA breach / Outage")
            assigned_team = params.get("assigned_team", "Tier 2 Support")
            escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"

            esc_log = EscalationLog(
                escalation_id=escalation_id,
                ticket_id=ticket_id,
                account_id=pending.account_id,
                severity=severity,
                escalation_reason=escalation_reason,
                assigned_team=assigned_team,
                escalated_by=user_name,
                escalated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            session.add(esc_log)

            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if ticket:
                ticket.status = "escalated"
                ticket.assigned_to = assigned_team

            session.commit()

            result_receipt = {
                "action_type": "create_escalation",
                "escalation_id": escalation_id,
                "ticket_id": ticket_id,
                "severity": severity,
                "assigned_team": assigned_team,
                "escalated_by": user_name,
                "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"Ticket {ticket_id} ({severity}) successfully escalated to {assigned_team}."
            }

        # 4. Action: update_ticket
        elif action_type == "update_ticket":
            ticket_id = params.get("ticket_id")
            new_status = params.get("status", "resolved")
            notes = params.get("notes", "")

            ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
            if ticket:
                ticket.status = new_status
                if notes:
                    ticket.description = f"{ticket.description}\n[Update by {user_name}]: {notes}"
            session.commit()

            result_receipt = {
                "action_type": "update_ticket",
                "ticket_id": ticket_id,
                "status": new_status,
                "updated_by": user_name,
                "executed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": f"Ticket {ticket_id} status updated to '{new_status}'."
            }

        else:
            return {"error": f"Unknown action type: {action_type}"}

        # Mark action proposal as EXECUTED
        pending.status = "EXECUTED"
        session.commit()

        return {
            "success": True,
            "action_token": action_token,
            "receipt": redact_sensitive_payload(result_receipt)
        }

    except Exception as e:
        session.rollback()
        return {"error": f"Execution failed: {str(e)}"}
    finally:
        session.close()

def cancel_pending_action(
    action_token: str,
    user_name: str = "User",
    user_role: str = "customer",
    account_id: str = "ACCT-001",
) -> Dict[str, Any]:
    """
    Cancels/revokes a pending action proposal without making any state mutations.
    """
    try:
        user_role = normalize_role(user_role)
    except SecurityError as e:
        return {"error": str(e)}

    session = SessionLocal()
    try:
        pending = session.query(PendingAction).filter(PendingAction.action_token == action_token).first()
        if not pending:
            return {"error": f"Action token '{action_token}' not found."}
        if user_role == "customer" and pending.account_id != account_id:
            return {"error": "Unauthorized: Customer cannot cancel action proposals from other accounts."}
        
        pending.status = "CANCELLED"
        session.commit()
        return {
            "success": True,
            "action_token": action_token,
            "status": "CANCELLED",
            "message": f"Action proposal {action_token} was cancelled by {user_name}."
        }
    finally:
        session.close()
