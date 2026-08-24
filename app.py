import os
import json
import uuid
import gradio as gr
from dotenv import load_dotenv

# Safe Monkeypatch for Gradio 4.x schema generator bug when handling boolean additionalProperties
try:
    import gradio_client.utils as gc_utils
    _orig_func = gc_utils._json_schema_to_python_type
    def _safe_json_schema_to_python_type(schema, defs=None):
        if isinstance(schema, bool):
            return "dict" if schema else "None"
        if not isinstance(schema, dict):
            return "Any"
        return _orig_func(schema, defs)
    gc_utils._json_schema_to_python_type = _safe_json_schema_to_python_type
except Exception:
    pass

load_dotenv()

# Ensure database and vector index exist on cold start
if not os.path.exists("parcelpilot.db"):
    from backend.db.seed import seed_database
    seed_database()

if not os.path.exists("chroma_db"):
    from backend.rag.ingest import ingest_documents
    ingest_documents()

from backend.agent.orchestrator import run_agent_turn
from backend.tools.action_engine import confirm_action

PERSONAS = {
    "Northstar Logistics (Customer — ACCT-001)": {
        "account_id": "ACCT-001",
        "user_role": "customer",
        "user_name": "Priya Sharma (Northstar Rep)",
        "badge": "Enterprise Tier • Dedicated CSM: Priya Mehta"
    },
    "LumenWorks (Customer — ACCT-002)": {
        "account_id": "ACCT-002",
        "user_role": "customer",
        "user_name": "Vikram Patel (LumenWorks Rep)",
        "badge": "Growth Tier • 2h SLA Clause 4"
    },
    "ParcelPilot Support Desk (Internal Staff)": {
        "account_id": "ACCT-001",
        "user_role": "support_agent",
        "user_name": "Arjun Mehta (Support Rep)",
        "badge": "Internal Operations Console • Global Access"
    },
    "Operations Manager (Internal Staff)": {
        "account_id": "ACCT-001",
        "user_role": "ops_manager",
        "user_name": "Sunita Rao (Ops Manager)",
        "badge": "Ops Lead • Service Credit & Escalation Approval"
    }
}

CUSTOM_CSS = """
.gradio-container {
    max-width: 1200px !important;
    margin: auto !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
.hero-header {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #334155;
    margin-bottom: 1rem;
    color: white;
}
.hero-header h1 {
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 0.3rem;
    background: linear-gradient(90deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.telemetry-box {
    background: #090d16 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
}
"""

def handle_chat(user_message, history, persona_key, session_state):
    if not user_message or not user_message.strip():
        return history, "", session_state, ""

    persona = PERSONAS.get(persona_key, PERSONAS["Northstar Logistics (Customer — ACCT-001)"])
    session_id = session_state.get("session_id") if session_state else f"hf_sess_{uuid.uuid4().hex[:8]}"

    # Convert Gradio history format to orchestrator format
    chat_history = []
    if history:
        for u, a in history[-6:]:
            if u:
                chat_history.append({"role": "user", "content": u})
            if a:
                chat_history.append({"role": "assistant", "content": a})

    res = run_agent_turn(
        user_message=user_message,
        session_id=session_id,
        account_id=persona["account_id"],
        user_role=persona["user_role"],
        user_name=persona["user_name"],
        chat_history=chat_history
    )

    response_text = res.get("response", "No response generated.")
    citations = res.get("citations", [])
    if citations:
        response_text += "\n\n**Sources & Policy Citations:**\n"
        for c in citations:
            response_text += f"- 📄 **{c.get('doc_name')}** ({c.get('section', 'General')})\n"

    pending_act = res.get("pending_action")
    action_info = ""
    if pending_act:
        action_info = (
            f"⚡ **Action Prepared:** `{pending_act.get('action_type')}`\n"
            f"• **Summary:** {pending_act.get('summary')}\n"
            f"• **Token:** `{pending_act.get('action_token')}`\n"
            f"• **Status:** {pending_act.get('status')}"
        )
        session_state["pending_token"] = pending_act.get("action_token")

    # Format telemetry
    telemetry_lines = []
    for t in res.get("tool_telemetry", []):
        icon = "✅" if t.get("status") == "success" else ("⚠️" if t.get("status") == "forbidden" else "🔧")
        telemetry_lines.append(f"{icon} [{t.get('tool')}] {t.get('summary')}")
    telemetry_output = "\n".join(telemetry_lines) if telemetry_lines else "No tool calls invoked."

    new_history = history + [(user_message, response_text)]
    session_state["session_id"] = session_id

    return new_history, "", session_state, telemetry_output, action_info

def handle_confirm_action(session_state, persona_key, history):
    token = session_state.get("pending_token")
    if not token:
        return history, "No pending action found to confirm.", session_state

    persona = PERSONAS.get(persona_key, PERSONAS["Northstar Logistics (Customer — ACCT-001)"])
    result = confirm_action(
        action_token=token,
        user_role=persona["user_role"],
        user_name=persona["user_name"],
        account_id=persona["account_id"]
    )

    status_msg = result.get("message", json.dumps(result))
    session_state["pending_token"] = None
    new_history = history + [("✅ [Action Confirmed by User]", f"**Execution Result:** {status_msg}")]
    return new_history, f"Executed: {status_msg}", session_state

def reset_chat():
    new_session_id = f"hf_sess_{uuid.uuid4().hex[:8]}"
    return [], "", {"session_id": new_session_id, "pending_token": None}, "", ""

# Build Gradio Blocks Application
with gr.Blocks(title="ParcelPilot AI — Operations & Support", css=CUSTOM_CSS, theme=gr.themes.Soft(primary_hue="sky")) as demo:
    session_state = gr.State({"session_id": f"hf_sess_{uuid.uuid4().hex[:8]}", "pending_token": None})

    gr.HTML("""
    <div class="hero-header">
        <h1>📦 ParcelPilot AI — Support & Operations Intelligence</h1>
        <p style="margin: 0; color: #94a3b8; font-size: 0.95rem;">
            Dual-Context Multi-Agent Co-Pilot with Precedence-Ranked Policy RAG, Deterministic RBAC & 2-Phase Confirmation Safety.
        </p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            persona_dropdown = gr.Dropdown(
                choices=list(PERSONAS.keys()),
                value="Northstar Logistics (Customer — ACCT-001)",
                label="👤 Active Persona & Auth Context",
                interactive=True
            )
            persona_badge = gr.Markdown("🔹 *Enterprise Tier • Dedicated CSM: Priya Mehta*")

            def on_persona_change(selected):
                badge_text = PERSONAS[selected]["badge"]
                return f"🔹 *{badge_text}*", [], {"session_id": f"hf_sess_{uuid.uuid4().hex[:8]}", "pending_token": None}, "", ""

            chatbot = gr.Chatbot(label="ParcelPilot Agent Dialogue", height=460, show_copy_button=True, type="tuples")

            with gr.Row():
                user_input = gr.Textbox(
                    placeholder="Ask about shipment status, cancellation fees, SLA breaches, or policy overrides...",
                    label="User Query",
                    scale=4,
                    lines=1
                )
                send_btn = gr.Button("Send 🚀", variant="primary", scale=1)

            with gr.Row():
                quick_btn1 = gr.Button("📦 Can I cancel order ORD-1001?", size="sm")
                quick_btn2 = gr.Button("⏱️ Evaluate SLA for ticket TKT-501", size="sm")
                quick_btn3 = gr.Button("💰 Failed pickup service credit rules", size="sm")
                clear_btn = gr.Button("🔄 Clear / Reset Session", size="sm", variant="secondary")

        with gr.Column(scale=2):
            gr.Markdown("### 🔍 Real-Time Agent Telemetry")
            telemetry_box = gr.Textbox(
                label="Tool Invocation Stream",
                interactive=False,
                lines=8,
                elem_classes=["telemetry-box"]
            )

            gr.Markdown("### ⚡ Two-Phase Action Proposal")
            action_box = gr.Markdown("*No pending action prepared.*")
            confirm_btn = gr.Button("✅ Confirm Proposed Action", variant="stop", size="sm")
            action_status = gr.Textbox(label="Action Execution Log", interactive=False, lines=2)

    # Event Bindings
    persona_dropdown.change(
        fn=on_persona_change,
        inputs=[persona_dropdown],
        outputs=[persona_badge, chatbot, session_state, telemetry_box, action_box]
    )

    send_btn.click(
        fn=handle_chat,
        inputs=[user_input, chatbot, persona_dropdown, session_state],
        outputs=[chatbot, user_input, session_state, telemetry_box, action_box]
    )

    user_input.submit(
        fn=handle_chat,
        inputs=[user_input, chatbot, persona_dropdown, session_state],
        outputs=[chatbot, user_input, session_state, telemetry_box, action_box]
    )

    confirm_btn.click(
        fn=handle_confirm_action,
        inputs=[session_state, persona_dropdown, chatbot],
        outputs=[chatbot, action_status, session_state]
    )

    clear_btn.click(
        fn=reset_chat,
        inputs=[],
        outputs=[chatbot, user_input, session_state, telemetry_box, action_box]
    )

    quick_btn1.click(lambda: "Can I cancel order ORD-1001?", None, user_input)
    quick_btn2.click(lambda: "Evaluate SLA status for ticket TKT-501", None, user_input)
    quick_btn3.click(lambda: "What are our allowable service credits for failed pickups?", None, user_input)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, show_api=False)
