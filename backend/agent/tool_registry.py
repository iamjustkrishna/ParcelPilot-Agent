import json
from typing import Dict, Any, List
from backend.rag.retriever import search_knowledge_base
from backend.tools.query_tools import (
    get_account_tool, get_order_tool, list_orders_tool,
    get_ticket_tool, list_tickets_tool, search_operational_issues_tool,
    AuthorizationError
)
from backend.tools.calculation_tools import (
    calculate_cancellation_fee, calculate_service_credit, evaluate_sla_status
)
from backend.tools.action_engine import prepare_action

# Gemini Function Declarations
TOOL_DECLARATIONS = [
    {
        "name": "search_knowledge_base",
        "description": "Searches authoritative ParcelPilot policies, SOPs, operations guides, customer agreements, and known issues. Returns grounded text and citations with source precedence.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (e.g. 'cancellation fee after 30 mins', 'Northstar SLA targets', 'bulk upload row limit', 'service credit threshold')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_account",
        "description": "Retrieves account metadata, plan tier (Enterprise, Growth, Standard), status, assigned CSM, and custom agreement terms.",
        "parameters": {
            "type": "object",
            "properties": {
                "account_id": {
                    "type": "string",
                    "description": "The account ID (e.g. 'ACCT-001', 'ACCT-002', 'ACCT-003', 'ACCT-004')"
                }
            },
            "required": ["account_id"]
        }
    },
    {
        "name": "get_order",
        "description": "Retrieves shipment details: carrier, status (BOOKED, PICKED_UP, DELIVERED), timestamps, fees, and carrier/customer fault flags.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order tracking ID (e.g. 'ORD-1001', 'ORD-1002', 'ORD-2001', 'ORD-2002', 'ORD-3001', 'ORD-4001')"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "list_orders",
        "description": "Lists orders for the current account with optional status filtering.",
        "parameters": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Optional status filter (e.g. 'BOOKED', 'PICKED_UP', 'DELIVERED', 'CANCELLED')"
                }
            }
        }
    },
    {
        "name": "get_ticket",
        "description": "Retrieves support ticket details: subject, description, status, channel, created timestamp, and assigned agent.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The ticket ID (e.g. 'TKT-501', 'TKT-502', 'TKT-503', 'TKT-504', 'TKT-505')"
                }
            },
            "required": ["ticket_id"]
        }
    },
    {
        "name": "list_tickets",
        "description": "Lists support tickets for the current account.",
        "parameters": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Optional status filter (e.g. 'open', 'pending', 'resolved', 'closed')"
                }
            }
        }
    },
    {
        "name": "search_operational_issues",
        "description": "Retrieves active operational known issues, bug reports, and workarounds (e.g. KI-208 CSV bulk upload defect, KI-211 SwiftShip webhook lag, KI-176 address validation).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "calculate_cancellation_fee",
        "description": "Deterministically calculates the cancellation fee and eligibility for an order based on booking time, status, and signed contract clauses.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to evaluate (e.g. 'ORD-1001', 'ORD-2001', 'ORD-3001')"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "calculate_service_credit",
        "description": "Deterministically calculates failed-pickup service credit eligibility, delay duration, credit amount, and manager approval requirements.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID with suspected carrier delay (e.g. 'ORD-2002')"
                }
            },
            "required": ["order_id"]
        }
    },
    {
        "name": "evaluate_sla_status",
        "description": "Evaluates ticket response SLA elapsed time, plan/contract target, breach duration, and escalation recommendation.",
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "string",
                    "description": "The support ticket ID (e.g. 'TKT-501', 'TKT-502', 'TKT-505')"
                }
            },
            "required": ["ticket_id"]
        }
    },
    {
        "name": "prepare_action",
        "description": "Prepares a state-changing action proposal (e.g. cancel_order, apply_service_credit, create_escalation, update_ticket) and returns an action token for explicit user confirmation. Does not mutate the database directly.",
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "description": "The action type: 'cancel_order', 'apply_service_credit', 'create_escalation', 'update_ticket'"
                },
                "parameters": {
                    "type": "object",
                    "description": "Parameters for the action (e.g. {'order_id': 'ORD-1001', 'fee_inr': 0.0}, {'ticket_id': 'TKT-501', 'severity': 'P1', 'assigned_team': 'On-Call Eng'})"
                },
                "summary": {
                    "type": "string",
                    "description": "Clear human-readable summary of the action and its impact to be presented on the confirmation card."
                }
            },
            "required": ["action_type", "parameters", "summary"]
        }
    }
]

def dispatch_tool_call(
    tool_name: str,
    tool_args: Dict[str, Any],
    session_id: str,
    account_id: str,
    user_role: str,
    user_name: str
) -> Dict[str, Any]:
    """
    Executes the requested tool with session and security context injected.
    """
    try:
        if tool_name == "search_knowledge_base":
            query = tool_args.get("query", "")
            return search_knowledge_base(query, account_id=account_id)

        elif tool_name == "get_account":
            target_acc = tool_args.get("account_id", account_id)
            return get_account_tool(target_acc, caller_role=user_role, caller_account_id=account_id)

        elif tool_name == "get_order":
            order_id = tool_args.get("order_id")
            return get_order_tool(order_id, caller_role=user_role, caller_account_id=account_id)

        elif tool_name == "list_orders":
            status_filter = tool_args.get("status_filter")
            return list_orders_tool(account_id, caller_role=user_role, caller_account_id=account_id, status_filter=status_filter)

        elif tool_name == "get_ticket":
            ticket_id = tool_args.get("ticket_id")
            return get_ticket_tool(ticket_id, caller_role=user_role, caller_account_id=account_id)

        elif tool_name == "list_tickets":
            status_filter = tool_args.get("status_filter")
            return list_tickets_tool(account_id, caller_role=user_role, caller_account_id=account_id, status_filter=status_filter)

        elif tool_name == "search_operational_issues":
            return search_operational_issues_tool(caller_role=user_role)

        elif tool_name == "calculate_cancellation_fee":
            order_id = tool_args.get("order_id")
            return calculate_cancellation_fee(order_id, caller_role=user_role, caller_account_id=account_id)

        elif tool_name == "calculate_service_credit":
            order_id = tool_args.get("order_id")
            return calculate_service_credit(order_id, caller_role=user_role, caller_account_id=account_id)

        elif tool_name == "evaluate_sla_status":
            ticket_id = tool_args.get("ticket_id")
            return evaluate_sla_status(ticket_id, caller_role=user_role, caller_account_id=account_id)

        elif tool_name == "prepare_action":
            action_type = tool_args.get("action_type")
            params = tool_args.get("parameters", {})
            summary = tool_args.get("summary", "")
            return prepare_action(
                session_id=session_id,
                account_id=account_id,
                user_role=user_role,
                user_name=user_name,
                action_type=action_type,
                parameters=params,
                summary=summary
            )

        else:
            return {"error": f"Unknown tool name: {tool_name}"}

    except AuthorizationError as ae:
        return {"error": f"403 Forbidden: {str(ae)}", "auth_blocked": True}
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
