import json
from typing import Dict, Any, Optional, List
from backend.db.database import SessionLocal
from backend.db.models import Account, Order, Ticket, CustomerAgreement, KnownIssue
from backend.security import INTERNAL_ROLES, normalize_role, redact_sensitive_payload

class AuthorizationError(Exception):
    pass

def verify_tenant_access(requested_account_id: str, caller_role: str, caller_account_id: str):
    """
    Enforces backend RBAC tenant boundaries.
    Customer role can only access their own account data.
    Internal roles (support_agent, ops_manager, admin) can access any account.
    """
    caller_role = normalize_role(caller_role)
    if caller_role == "customer":
        if requested_account_id != caller_account_id:
            raise AuthorizationError(
                f"Access Denied: Customer '{caller_account_id}' is not authorized to access data for account '{requested_account_id}'."
            )

def get_account_tool(account_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001") -> Dict[str, Any]:
    """
    Fetches account details, subscription plan, assigned CSM, and custom agreement references.
    """
    verify_tenant_access(account_id, caller_role, caller_account_id)
    session = SessionLocal()
    try:
        account = session.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return {"error": f"Account '{account_id}' not found."}
        
        data = account.to_dict()
        if account.agreement:
            data["custom_agreement"] = account.agreement.to_dict()
        return data
    finally:
        session.close()

def get_order_tool(order_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001") -> Dict[str, Any]:
    """
    Fetches shipment details, carrier, booking timestamp, pickup window, actual pickup time, and fault flags.
    """
    session = SessionLocal()
    try:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        if not order:
            return {"error": f"Order '{order_id}' not found."}
        
        # Verify tenant access
        verify_tenant_access(order.account_id, caller_role, caller_account_id)
        return order.to_dict()
    finally:
        session.close()

def list_orders_tool(account_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001", status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists orders for an account with optional status filtering.
    """
    verify_tenant_access(account_id, caller_role, caller_account_id)
    session = SessionLocal()
    try:
        query = session.query(Order).filter(Order.account_id == account_id)
        if status_filter:
            query = query.filter(Order.status == status_filter.upper())
        orders = query.all()
        return [o.to_dict() for o in orders]
    finally:
        session.close()

def get_ticket_tool(ticket_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001") -> Dict[str, Any]:
    """
    Fetches support ticket details, subject, description, timestamps, assigned agent, and SLA status.
    """
    session = SessionLocal()
    try:
        ticket = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return {"error": f"Ticket '{ticket_id}' not found."}
        
        verify_tenant_access(ticket.account_id, caller_role, caller_account_id)
        data = ticket.to_dict()
        data = redact_sensitive_payload(data)

        # Customer role should not receive raw internal resolution notes if they contain sensitive or erroneous data
        if caller_role == "customer" and "historical_resolution" in data:
            del data["historical_resolution"]

        return data
    finally:
        session.close()

def list_tickets_tool(account_id: str, caller_role: str = "customer", caller_account_id: str = "ACCT-001", status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists tickets for an account.
    """
    verify_tenant_access(account_id, caller_role, caller_account_id)
    session = SessionLocal()
    try:
        query = session.query(Ticket).filter(Ticket.account_id == account_id)
        if status_filter:
            query = query.filter(Ticket.status == status_filter.lower())
        tickets = query.all()
        results = []
        for t in tickets:
            d = t.to_dict()
            d = redact_sensitive_payload(d)
            if caller_role == "customer" and "historical_resolution" in d:
                del d["historical_resolution"]
            results.append(d)
        return results
    finally:
        session.close()

def search_operational_issues_tool(category_filter: Optional[str] = "all", caller_role: str = "support_agent") -> List[Dict[str, Any]]:
    """
    Returns active known operational issues (KI-208, KI-211, KI-176).
    """
    caller_role = normalize_role(caller_role)
    if caller_role not in INTERNAL_ROLES:
        raise AuthorizationError("Customer role is not authorized to access internal operational known issues.")

    session = SessionLocal()
    try:
        query = session.query(KnownIssue)
        if category_filter and category_filter != "all":
            query = query.filter(KnownIssue.category == category_filter)
        issues = query.all()
        return [i.to_dict() for i in issues]
    finally:
        session.close()
