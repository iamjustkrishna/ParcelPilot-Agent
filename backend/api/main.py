import os
import sys
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.db.database import SessionLocal, init_db
from backend.db.models import Account, Order, Ticket, KnownIssue, PendingAction
from backend.db.seed import seed_database
from backend.agent.orchestrator import run_agent_turn
from backend.tools.action_engine import confirm_action, cancel_pending_action
from backend.tools.query_tools import verify_tenant_access, AuthorizationError
from backend.security import normalize_role, redact_sensitive_payload, SecurityError

app = FastAPI(
    title="ParcelPilot AI - Operations & Support Engine",
    description="Dual-Context Support & Operations Intelligence System with deterministic RBAC and two-phase action confirmation.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory Session Conversation Store
SESSION_STORE: Dict[str, List[Dict[str, str]]] = {}

# Request & Response Schemas
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "sess_default"
    account_id: Optional[str] = None
    user_role: Optional[str] = None
    user_name: Optional[str] = None
    chat_history: Optional[List[Dict[str, str]]] = None

class ActionConfirmRequest(BaseModel):
    action_token: str
    user_role: Optional[str] = "customer"
    user_name: Optional[str] = "Customer Rep"
    account_id: Optional[str] = "ACCT-001"

class ActionCancelRequest(BaseModel):
    action_token: str
    user_name: Optional[str] = "User"
    user_role: Optional[str] = None
    account_id: Optional[str] = None

# Helper Dependency for Header-based Auth context
def get_auth_context(
    x_account_id: Optional[str] = Header(None),
    x_user_role: Optional[str] = Header(None),
    x_user_name: Optional[str] = Header(None)
):
    return {
        "account_id": x_account_id,
        "user_role": x_user_role,
        "user_name": x_user_name
    }

def resolve_auth_context(req_account_id: Optional[str], req_user_role: Optional[str], req_user_name: Optional[str], auth: dict):
    account_id = auth.get("account_id") or req_account_id or "ACCT-001"
    user_role = auth.get("user_role") or req_user_role or "customer"
    user_name = auth.get("user_name") or req_user_name or "Customer Rep"
    try:
        user_role = normalize_role(user_role)
    except SecurityError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    return account_id, user_role, user_name

# API Endpoints
@app.get("/api/health")
async def health_check():
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    has_groq = bool(os.environ.get("GROQ_API_KEY", "").strip())
    has_gemini = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    active_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile") if provider == "groq" else os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    return {
        "status": "healthy",
        "service": "ParcelPilot AI",
        "llm_provider": provider,
        "groq_configured": has_groq,
        "gemini_configured": has_gemini,
        "active_model": active_model
    }

@app.post("/api/chat/reset")
async def reset_chat_session(req: Optional[Dict[str, str]] = None):
    sid = (req or {}).get("session_id", "sess_default")
    if sid in SESSION_STORE:
        SESSION_STORE[sid] = []
    return {"status": "reset", "session_id": sid}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, auth: dict = Depends(get_auth_context)):
    account_id, user_role, user_name = resolve_auth_context(req.account_id, req.user_role, req.user_name, auth)
    session_id = req.session_id or "sess_default"

    # Resolve conversation history (from request payload or server session store)
    history = req.chat_history if req.chat_history is not None else SESSION_STORE.get(session_id, [])

    result = run_agent_turn(
        user_message=req.message,
        session_id=session_id,
        account_id=account_id,
        user_role=user_role,
        user_name=user_name,
        chat_history=history
    )

    # Persist turns into server session memory (capped at last 20 turns)
    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = []
    SESSION_STORE[session_id].append({"role": "user", "content": req.message})
    SESSION_STORE[session_id].append({"role": "assistant", "content": result.get("response", "")})
    SESSION_STORE[session_id] = SESSION_STORE[session_id][-20:]

    return result

@app.post("/api/actions/confirm")
async def confirm_action_endpoint(req: ActionConfirmRequest, auth: dict = Depends(get_auth_context)):
    account_id, user_role, user_name = resolve_auth_context(req.account_id, req.user_role, req.user_name, auth)

    res = confirm_action(
        action_token=req.action_token,
        user_role=user_role,
        user_name=user_name,
        account_id=account_id
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.post("/api/actions/cancel")
async def cancel_action_endpoint(req: ActionCancelRequest, auth: dict = Depends(get_auth_context)):
    account_id, user_role, user_name = resolve_auth_context(req.account_id, req.user_role, req.user_name, auth)
    res = cancel_pending_action(
        action_token=req.action_token,
        user_name=user_name,
        user_role=user_role,
        account_id=account_id,
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@app.get("/api/accounts")
async def list_accounts():
    session = SessionLocal()
    try:
        accounts = session.query(Account).all()
        return [a.to_dict() for a in accounts]
    finally:
        session.close()

@app.get("/api/orders")
async def get_orders_list(auth: dict = Depends(get_auth_context)):
    account_id, user_role, _ = resolve_auth_context(None, None, None, auth)
    session = SessionLocal()
    try:
        if user_role == "customer":
            orders = session.query(Order).filter(Order.account_id == account_id).all()
        else:
            orders = session.query(Order).all()
        return [o.to_dict() for o in orders]
    finally:
        session.close()

@app.get("/api/tickets")
async def get_tickets_list(auth: dict = Depends(get_auth_context)):
    account_id, user_role, _ = resolve_auth_context(None, None, None, auth)
    session = SessionLocal()
    try:
        if user_role == "customer":
            tickets = session.query(Ticket).filter(Ticket.account_id == account_id).all()
            # Omit internal resolution notes
            results = []
            for t in tickets:
                d = redact_sensitive_payload(t.to_dict())
                if "historical_resolution" in d:
                    del d["historical_resolution"]
                results.append(d)
            return results
        else:
            tickets = session.query(Ticket).all()
            return [redact_sensitive_payload(t.to_dict()) for t in tickets]
    finally:
        session.close()

@app.get("/api/known-issues")
async def get_known_issues(auth: dict = Depends(get_auth_context)):
    _, user_role, _ = resolve_auth_context(None, None, None, auth)
    if user_role == "customer":
        raise HTTPException(status_code=403, detail="Customer role is not authorized to access internal known issues.")
    session = SessionLocal()
    try:
        issues = session.query(KnownIssue).all()
        return [i.to_dict() for i in issues]
    finally:
        session.close()

@app.post("/api/system/reset")
async def reset_system_state():
    """
    Resets the SQLite database back to its original assessment seed state,
    clears all pending action proposals, and wipes in-memory chat session history.
    """
    try:
        SESSION_STORE.clear()
        seed_database()
        return {
            "status": "success",
            "message": "Database and sessions have been reset to pristine initial assessment state."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset system state: {str(e)}")

# Mount frontend directory for seamless local web serving
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
