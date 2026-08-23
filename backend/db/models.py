import datetime
import json
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, Enum, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Account(Base):
    __tablename__ = "accounts"

    account_id = Column(String(32), primary_key=True)
    account_name = Column(String(128), nullable=False)
    plan = Column(String(32), nullable=False)  # Enterprise, Growth, Standard
    status = Column(String(32), default="active", nullable=False)
    csm = Column(String(64), nullable=True)
    contract_file = Column(String(128), nullable=True)
    premium_support = Column(Boolean, default=False, nullable=False)
    notes = Column(Text, nullable=True)

    orders = relationship("Order", back_populates="account")
    tickets = relationship("Ticket", back_populates="account")
    agreement = relationship("CustomerAgreement", back_populates="account", uselist=False)

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "account_name": self.account_name,
            "plan": self.plan,
            "status": self.status,
            "csm": self.csm,
            "contract_file": self.contract_file,
            "premium_support": self.premium_support,
            "notes": self.notes,
        }

class CustomerAgreement(Base):
    __tablename__ = "customer_agreements"

    agreement_id = Column(String(32), primary_key=True)
    account_id = Column(String(32), ForeignKey("accounts.account_id"), unique=True, nullable=False)
    term_start = Column(String(32), nullable=True)
    term_end = Column(String(32), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)
    p1_sla = Column(String(64), nullable=True)
    p2_sla = Column(String(64), nullable=True)
    p3_sla = Column(String(64), nullable=True)
    free_cancellation_pre_pickup = Column(Boolean, default=False, nullable=False)
    credit_fixed_amount = Column(Float, nullable=True)
    credit_delay_hours = Column(Float, nullable=True)
    monthly_credit_cap = Column(Float, nullable=True)
    raw_contract_file = Column(String(128), nullable=True)

    account = relationship("Account", back_populates="agreement")

    def to_dict(self):
        return {
            "agreement_id": self.agreement_id,
            "account_id": self.account_id,
            "term_start": self.term_start,
            "term_end": self.term_end,
            "status": self.status,
            "p1_sla": self.p1_sla,
            "p2_sla": self.p2_sla,
            "p3_sla": self.p3_sla,
            "free_cancellation_pre_pickup": self.free_cancellation_pre_pickup,
            "credit_fixed_amount": self.credit_fixed_amount,
            "credit_delay_hours": self.credit_delay_hours,
            "monthly_credit_cap": self.monthly_credit_cap,
            "raw_contract_file": self.raw_contract_file,
        }

class Order(Base):
    __tablename__ = "orders"

    order_id = Column(String(32), primary_key=True)
    account_id = Column(String(32), ForeignKey("accounts.account_id"), nullable=False)
    carrier = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)  # DRAFT, BOOKED, PICKED_UP, DELIVERED, CANCELLED
    booked_at = Column(String(32), nullable=False)
    pickup_window_start = Column(String(32), nullable=True)
    pickup_window_end = Column(String(32), nullable=True)
    pickup_actual_at = Column(String(32), nullable=True)
    shipment_fee_inr = Column(Float, nullable=False)
    carrier_fault = Column(Boolean, default=False, nullable=False)
    customer_fault = Column(Boolean, default=False, nullable=False)
    cancellation_requested_at = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)

    account = relationship("Account", back_populates="orders")

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "account_id": self.account_id,
            "carrier": self.carrier,
            "status": self.status,
            "booked_at": self.booked_at,
            "pickup_window_start": self.pickup_window_start,
            "pickup_window_end": self.pickup_window_end,
            "pickup_actual_at": self.pickup_actual_at,
            "shipment_fee_inr": self.shipment_fee_inr,
            "carrier_fault": self.carrier_fault,
            "customer_fault": self.customer_fault,
            "cancellation_requested_at": self.cancellation_requested_at,
            "notes": self.notes,
        }

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(32), primary_key=True)
    account_id = Column(String(32), ForeignKey("accounts.account_id"), nullable=False)
    created_at = Column(String(32), nullable=False)
    status = Column(String(32), default="open", nullable=False)  # open, pending, resolved, closed, escalated
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    channel = Column(String(32), nullable=False)
    assigned_to = Column(String(64), nullable=True)
    last_customer_message_at = Column(String(32), nullable=True)
    historical_resolution = Column(Text, nullable=True)
    calculated_severity = Column(String(16), nullable=True)  # P1, P2, P3
    is_sla_breached = Column(Boolean, default=False, nullable=False)

    account = relationship("Account", back_populates="tickets")

    def to_dict(self):
        return {
            "ticket_id": self.ticket_id,
            "account_id": self.account_id,
            "created_at": self.created_at,
            "status": self.status,
            "subject": self.subject,
            "description": self.description,
            "channel": self.channel,
            "assigned_to": self.assigned_to,
            "last_customer_message_at": self.last_customer_message_at,
            "historical_resolution": self.historical_resolution,
            "calculated_severity": self.calculated_severity,
            "is_sla_breached": self.is_sla_breached,
        }

class ServiceCreditLog(Base):
    __tablename__ = "service_credit_logs"

    credit_id = Column(String(64), primary_key=True)
    order_id = Column(String(32), ForeignKey("orders.order_id"), nullable=False)
    account_id = Column(String(32), ForeignKey("accounts.account_id"), nullable=False)
    amount_inr = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    approval_status = Column(String(32), default="APPROVED_AUTO", nullable=False)  # APPROVED_AUTO, APPROVED_MANAGER, REJECTED
    approved_by = Column(String(64), nullable=False)
    created_at = Column(String(32), nullable=False)

    def to_dict(self):
        return {
            "credit_id": self.credit_id,
            "order_id": self.order_id,
            "account_id": self.account_id,
            "amount_inr": self.amount_inr,
            "reason": self.reason,
            "approval_status": self.approval_status,
            "approved_by": self.approved_by,
            "created_at": self.created_at,
        }

class EscalationLog(Base):
    __tablename__ = "escalation_logs"

    escalation_id = Column(String(64), primary_key=True)
    ticket_id = Column(String(32), ForeignKey("tickets.ticket_id"), nullable=False)
    account_id = Column(String(32), ForeignKey("accounts.account_id"), nullable=False)
    severity = Column(String(16), nullable=False)
    escalation_reason = Column(Text, nullable=False)
    assigned_team = Column(String(64), nullable=False)
    escalated_by = Column(String(64), nullable=False)
    escalated_at = Column(String(32), nullable=False)

    def to_dict(self):
        return {
            "escalation_id": self.escalation_id,
            "ticket_id": self.ticket_id,
            "account_id": self.account_id,
            "severity": self.severity,
            "escalation_reason": self.escalation_reason,
            "assigned_team": self.assigned_team,
            "escalated_by": self.escalated_by,
            "escalated_at": self.escalated_at,
        }

class KnownIssue(Base):
    __tablename__ = "known_issues"

    issue_id = Column(String(32), primary_key=True)  # KI-208, KI-211, KI-176
    title = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)  # Investigating, Monitoring, Resolved
    opened_at = Column(String(32), nullable=True)
    resolved_at = Column(String(32), nullable=True)
    description = Column(Text, nullable=False)
    affected_plans = Column(String(128), nullable=True)
    workaround = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "issue_id": self.issue_id,
            "title": self.title,
            "status": self.status,
            "opened_at": self.opened_at,
            "resolved_at": self.resolved_at,
            "description": self.description,
            "affected_plans": self.affected_plans,
            "workaround": self.workaround,
        }

class PendingAction(Base):
    __tablename__ = "pending_actions"

    action_token = Column(String(64), primary_key=True)  # UUID
    session_id = Column(String(64), nullable=False)
    account_id = Column(String(32), nullable=False)
    user_role = Column(String(32), nullable=False)
    action_type = Column(String(64), nullable=False)  # cancel_order, apply_service_credit, create_escalation, update_ticket
    parameters = Column(Text, nullable=False)  # JSON string
    summary = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING", nullable=False)  # PENDING, EXECUTED, CANCELLED, EXPIRED
    created_at = Column(String(32), nullable=False)
    expires_at = Column(String(32), nullable=False)

    def get_parameters_dict(self):
        try:
            return json.loads(self.parameters)
        except Exception:
            return {}

    def to_dict(self):
        return {
            "action_token": self.action_token,
            "session_id": self.session_id,
            "account_id": self.account_id,
            "user_role": self.user_role,
            "action_type": self.action_type,
            "parameters": self.get_parameters_dict(),
            "summary": self.summary,
            "status": self.status,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }
