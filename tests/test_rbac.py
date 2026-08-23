import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from backend.db.seed import seed_database
from backend.tools.query_tools import (
    get_order_tool, get_ticket_tool, list_orders_tool, AuthorizationError
)
from backend.tools.action_engine import prepare_action

class TestRBACIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()

    def test_customer_cross_account_order_blocked(self):
        """Northstar (ACCT-001) attempting to query LumenWorks order (ORD-2001) must raise AuthorizationError."""
        with self.assertRaises(AuthorizationError):
            get_order_tool("ORD-2001", caller_role="customer", caller_account_id="ACCT-001")

    def test_customer_cross_account_ticket_blocked(self):
        """Northstar (ACCT-001) attempting to query LumenWorks ticket (TKT-502) must raise AuthorizationError."""
        with self.assertRaises(AuthorizationError):
            get_ticket_tool("TKT-502", caller_role="customer", caller_account_id="ACCT-001")

    def test_internal_support_cross_account_allowed(self):
        """Internal support_agent role should be allowed to view any customer order or ticket."""
        order = get_order_tool("ORD-2001", caller_role="support_agent", caller_account_id="ACCT-001")
        self.assertEqual(order.get("order_id"), "ORD-2001")

        ticket = get_ticket_tool("TKT-502", caller_role="support_agent", caller_account_id="ACCT-001")
        self.assertEqual(ticket.get("ticket_id"), "TKT-502")

    def test_customer_cannot_self_issue_credit(self):
        """Customer role attempting to prepare a service credit action must be blocked."""
        res = prepare_action(
            session_id="test_sess",
            account_id="ACCT-001",
            user_role="customer",
            user_name="Customer",
            action_type="apply_service_credit",
            parameters={"order_id": "ORD-1001", "amount_inr": 300.0},
            summary="Attempted self credit"
        )
        self.assertIn("error", res)
        self.assertIn("Unauthorized", res["error"])

    def test_large_credit_requires_ops_manager(self):
        """Support agent role attempting credit > INR 1,000 must require ops_manager approval."""
        res = prepare_action(
            session_id="test_sess",
            account_id="ACCT-001",
            user_role="support_agent",
            user_name="Maya",
            action_type="apply_service_credit",
            parameters={"order_id": "ORD-1001", "amount_inr": 1500.0},
            summary="Large credit"
        )
        self.assertIn("error", res)
        self.assertIn("Ops Manager approval", res["error"])

if __name__ == "__main__":
    unittest.main()
