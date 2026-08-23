import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from backend.rag.retriever import search_knowledge_base

class TestKnowledgeRetrieval(unittest.TestCase):
    def test_northstar_contract_ranked_highest(self):
        """When searching cancellation policy for Northstar, Northstar Agreement (Rank 100) must be returned at the top."""
        res = search_knowledge_base("cancellation policy before pickup", account_id="ACCT-001")
        citations = res.get("citations", [])
        self.assertGreater(len(citations), 0)
        top_citation = citations[0]
        self.assertEqual(top_citation.get("authority_weight"), 100)
        self.assertEqual(top_citation.get("doc_id"), "DOC-AGR-NORTHSTAR")

    def test_lumenworks_contract_retrieval(self):
        """When searching service credits for LumenWorks, LumenWorks Agreement (Rank 100) must be retrieved."""
        res = search_knowledge_base("service credit for failed pickup delay", account_id="ACCT-002")
        citations = res.get("citations", [])
        self.assertTrue(any(c.get("doc_id") == "DOC-AGR-LUMENWORKS" for c in citations))

    def test_deprecated_policy_excluded(self):
        """Deprecated Support Policy v2 must NEVER be returned in standard queries."""
        res = search_knowledge_base("P1 SLA response time Enterprise", account_id="ACCT-004")
        citations = res.get("citations", [])
        self.assertGreater(len(citations), 0)
        for c in citations:
            self.assertNotEqual(c.get("doc_id"), "DOC-POL-V2-DEPRECATED")
            self.assertNotIn("deprecated", c.get("doc_name", "").lower())
            self.assertNotIn("policy v2", c.get("doc_name", "").lower())

if __name__ == "__main__":
    unittest.main()
