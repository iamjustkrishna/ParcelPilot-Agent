import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from backend.db.seed import seed_database
from backend.tools.calculation_tools import (
    calculate_cancellation_fee, calculate_service_credit, evaluate_sla_status
)

class TestDeterministicCalculations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        seed_database()

    def test_northstar_cancellation_fee_waiver(self):
        """ORD-1001: Northstar Enterprise contract waives fee for BOOKED shipments before pickup."""
        res = calculate_cancellation_fee("ORD-1001", caller_role="customer", caller_account_id="ACCT-001")
        self.assertTrue(res.get("eligible_for_cancellation"))
        self.assertEqual(res.get("cancellation_fee_inr"), 0.0)
        self.assertTrue(res.get("fee_waived"))
        self.assertIn("Clause 2", res.get("authority_rule", ""))

    def test_picked_up_shipment_rejection(self):
        """ORD-1002: Picked up shipment cannot be cancelled directly; RTO workflow required."""
        res = calculate_cancellation_fee("ORD-1002", caller_role="customer", caller_account_id="ACCT-001")
        self.assertFalse(res.get("eligible_for_cancellation"))
        self.assertIn("RTO", res.get("action_recommendation", ""))

    def test_lumenworks_cancellation_fee_sop(self):
        """ORD-2001: LumenWorks booked 75m ago without waiver -> INR 250 fee applies under SOP v4."""
        res = calculate_cancellation_fee("ORD-2001", caller_role="customer", caller_account_id="ACCT-002")
        self.assertTrue(res.get("eligible_for_cancellation"))
        self.assertEqual(res.get("cancellation_fee_inr"), 250.0)
        self.assertFalse(res.get("fee_waived"))

    def test_beacon_within_30m_grace(self):
        """ORD-3001: Cancelled 15 mins after booking -> INR 0 fee under SOP v4 30-minute grace."""
        res = calculate_cancellation_fee("ORD-3001", caller_role="customer", caller_account_id="ACCT-003")
        self.assertTrue(res.get("eligible_for_cancellation"))
        self.assertEqual(res.get("cancellation_fee_inr"), 0.0)

    def test_delivered_shipment_rejection(self):
        """ORD-4001: Delivered shipment cannot be cancelled."""
        res = calculate_cancellation_fee("ORD-4001", caller_role="customer", caller_account_id="ACCT-004")
        self.assertFalse(res.get("eligible_for_cancellation"))

    def test_lumenworks_service_credit_override(self):
        """ORD-2002: Missed pickup 4.5h delay with carrier fault -> Fixed INR 300 under LumenWorks Agreement."""
        res = calculate_service_credit("ORD-2002", caller_role="customer", caller_account_id="ACCT-002")
        self.assertTrue(res.get("eligible"))
        self.assertEqual(res.get("credit_amount_inr"), 300.0)
        self.assertIn("Clause 3", res.get("authority_rule", ""))

    def test_northstar_sla_breach_p1(self):
        """TKT-501: Northstar P1 outage created 10:30, snapshot 11:00 -> 30m elapsed vs 15m target -> BREACHED by 15m."""
        res = evaluate_sla_status("TKT-501", caller_role="customer", caller_account_id="ACCT-001")
        self.assertEqual(res.get("severity"), "P1")
        self.assertEqual(res.get("target_sla_minutes"), 15.0)
        self.assertEqual(res.get("elapsed_minutes"), 30.0)
        self.assertTrue(res.get("is_breached"))
        self.assertEqual(res.get("breach_minutes"), 15.0)

    def test_axis_labs_sla_breach_p1(self):
        """TKT-505: Axis Labs standard Enterprise P1 security incident created 08:30, snapshot 11:00 -> 150m elapsed vs 30m target -> BREACHED."""
        res = evaluate_sla_status("TKT-505", caller_role="customer", caller_account_id="ACCT-004")
        self.assertEqual(res.get("severity"), "P1")
        self.assertEqual(res.get("target_sla_minutes"), 30.0)
        self.assertTrue(res.get("is_breached"))
        self.assertEqual(res.get("breach_minutes"), 120.0)

if __name__ == "__main__":
    unittest.main()
