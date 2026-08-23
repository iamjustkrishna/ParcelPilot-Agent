import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agent.orchestrator import run_agent_turn

def test_northstar_cancel():
    print("Testing Northstar ORD-1001 Cancellation Query...")
    result = run_agent_turn(
        user_message="I want to cancel order ORD-1001. Is there any cancellation fee?",
        session_id="test_sess_1",
        account_id="ACCT-001",
        user_role="customer",
        user_name="Northstar Representative"
    )

    print("\n=== ASSISTANT RESPONSE ===")
    try:
        print(result["response"])
    except UnicodeEncodeError:
        print(result["response"].encode("ascii", "replace").decode("ascii"))

    print("\n=== CITATIONS ===")
    for c in result.get("citations", []):
        print(f"- [{c.get('authority_weight')}] {c.get('doc_name')} -> {c.get('section')}")

    print("\n=== TOOL TELEMETRY ===")
    for t in result.get("tool_telemetry", []):
        print(f"- {t.get('tool')} ({t.get('status')}) -> {t.get('summary')}")

    print("\n=== PENDING ACTION ===")
    print(result.get("pending_action"))

if __name__ == "__main__":
    test_northstar_cancel()
