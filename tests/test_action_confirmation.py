import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from backend.db.seed import seed_database
from backend.db.database import SessionLocal
from backend.db.models import Order, PendingAction, ServiceCreditLog, EscalationLog
from backend.tools.action_engine import prepare_action, confirm_action, cancel_pending_action

class TestActionConfirmationStateMachine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()

    def test_cancel_order_prepare_then_confirm_lifecycle(self):
        """Prepares an order cancellation, checks no premature mutation, then confirms and verifies DB mutation."""
        session = SessionLocal()
        order_before = session.query(Order).filter(Order.order_id == "ORD-1001").first()
        self.assertEqual(order_before.status, "BOOKED")
        session.close()

        # Step 1: Prepare action
        prep = prepare_action(
            session_id="test_sess_cancel",
            account_id="ACCT-001",
            user_role="customer",
            user_name="Northstar Rep",
            action_type="cancel_order",
            parameters={"order_id": "ORD-1001", "fee_inr": 0.0},
            summary="Cancel order ORD-1001 with INR 0 fee under Northstar Agreement."
        )

        token = prep.get("action_token")
        self.assertTrue(token.startswith("act_"))
        self.assertEqual(prep.get("status"), "PENDING")
        self.assertTrue(prep.get("requires_confirmation"))

        # Verify DB is STILL BOOKED (no premature mutation)
        session = SessionLocal()
        order_mid = session.query(Order).filter(Order.order_id == "ORD-1001").first()
        self.assertEqual(order_mid.status, "BOOKED")
        session.close()

        # Step 2: Confirm action
        conf = confirm_action(
            action_token=token,
            user_role="customer",
            user_name="Northstar Rep",
            account_id="ACCT-001"
        )
        self.assertTrue(conf.get("success"))
        self.assertEqual(conf.get("receipt", {}).get("new_status"), "CANCELLED")

        # Verify DB IS NOW CANCELLED
        session = SessionLocal()
        order_after = session.query(Order).filter(Order.order_id == "ORD-1001").first()
        self.assertEqual(order_after.status, "CANCELLED")
        self.assertIn("act_", order_after.notes)
        session.close()

        # Step 3: Attempt replay / second confirmation must fail
        replay = confirm_action(
            action_token=token,
            user_role="customer",
            user_name="Northstar Rep",
            account_id="ACCT-001"
        )
        self.assertIn("error", replay)

    def test_cancel_pending_action(self):
        """Verifies explicit rejection of an action token."""
        prep = prepare_action(
            session_id="test_sess_cancel_reject",
            account_id="ACCT-001",
            user_role="customer",
            user_name="Northstar Rep",
            action_type="cancel_order",
            parameters={"order_id": "ORD-1001", "fee_inr": 0.0},
            summary="Cancel proposal to reject"
        )
        token = prep.get("action_token")

        cancel_res = cancel_pending_action(token, user_name="Northstar Rep")
        self.assertTrue(cancel_res.get("success"))
        self.assertEqual(cancel_res.get("status"), "CANCELLED")

        # Confirmation after cancellation must fail
        conf_after = confirm_action(token, user_role="customer", user_name="Northstar Rep", account_id="ACCT-001")
        self.assertIn("error", conf_after)

if __name__ == "__main__":
    unittest.main()
