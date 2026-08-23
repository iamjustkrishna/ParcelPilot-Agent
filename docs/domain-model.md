# ParcelPilot AI — Canonical Domain Model (Agent 02)

## 1. Domain Entity Relationship Diagram

```mermaid
erDiagram
    ACCOUNT ||--o{ ORDER : places
    ACCOUNT ||--o{ TICKET : submits
    ACCOUNT ||--o| CUSTOMER_AGREEMENT : has
    ACCOUNT ||--o{ SERVICE_CREDIT_LOG : receives
    ORDER ||--o{ SERVICE_CREDIT_LOG : references
    TICKET ||--o{ ESCALATION_LOG : triggers
    
    ACCOUNT {
        string account_id PK
        string account_name
        enum plan "Enterprise, Growth, Standard"
        enum status "active, suspended"
        string csm
        string contract_file
        boolean premium_support
        string notes
    }

    CUSTOMER_AGREEMENT {
        string agreement_id PK
        string account_id FK
        datetime term_start
        datetime term_end
        string p1_sla
        string p2_sla
        string p3_sla
        boolean free_cancellation_pre_pickup
        float credit_fixed_amount
        float credit_delay_hours
        float monthly_credit_cap
        string raw_contract_file
    }

    ORDER {
        string order_id PK
        string account_id FK
        string carrier
        enum status "DRAFT, BOOKED, PICKED_UP, DELIVERED, CANCELLED"
        datetime booked_at
        datetime pickup_window_start
        datetime pickup_window_end
        datetime pickup_actual_at
        float shipment_fee_inr
        boolean carrier_fault
        boolean customer_fault
        datetime cancellation_requested_at
        string notes
    }

    TICKET {
        string ticket_id PK
        string account_id FK
        datetime created_at
        enum status "open, pending, resolved, closed"
        string subject
        string description
        enum channel "email, chat, phone"
        string assigned_to
        datetime last_customer_message_at
        string historical_resolution
        enum calculated_severity "P1, P2, P3"
        boolean is_sla_breached
    }

    SERVICE_CREDIT_LOG {
        string credit_id PK
        string order_id FK
        string account_id FK
        float amount_inr
        string reason
        enum approval_status "APPROVED_AUTO, PENDING_MANAGER, APPROVED_MANAGER, REJECTED"
        string approved_by
        datetime created_at
    }

    ESCALATION_LOG {
        string escalation_id PK
        string ticket_id FK
        string account_id FK
        string severity
        string escalation_reason
        string assigned_team
        string escalated_by
        datetime escalated_at
    }

    KNOWN_ISSUE {
        string issue_id PK "e.g. KI-208, KI-211, KI-176"
        string title
        enum status "Investigating, Monitoring, Resolved"
        datetime opened_at
        datetime resolved_at
        string description
        string affected_plans
        string workaround
    }

    PENDING_ACTION {
        string action_token PK "UUID"
        string session_id
        string account_id
        string user_role
        string action_type "cancel_order, apply_credit, escalate_ticket, update_ticket"
        json parameters
        string summary
        datetime created_at
        datetime expires_at
        enum status "PENDING, EXECUTED, CANCELLED, EXPIRED"
    }
```

---

## 2. Storage Partitioning Strategy

### 2.1 Structured Relational Storage (SQLite + SQLAlchemy)
- **Tables**: `accounts`, `orders`, `tickets`, `customer_agreements`, `service_credit_logs`, `escalation_logs`, `known_issues`, `pending_actions`.
- **Purpose**: ACID transactional integrity, multi-tenant relational filtering, deterministic arithmetic, exact equality/date range indexing, and strict state persistence.

### 2.2 Vector Storage (ChromaDB / Embedding Store)
- **Collection**: `parcelpilot_knowledge_base`
- **Indexed Sources**:
  - `01_Support_Policy_v3_CURRENT.pdf` (Global chunks)
  - `03_Cancellation_and_Service_Credit_SOP_v4.pdf` (Global chunks)
  - `04_Product_Operations_Guide_and_Known_Issues.pdf` (Global chunks)
  - `05_Northstar_Logistics_Enterprise_Agreement.pdf` (Tenant-scoped to `ACCT-001`)
  - `06_LumenWorks_Service_Agreement.pdf` (Tenant-scoped to `ACCT-002`)
- **Metadata Filters**:
  - `doc_id`: unique document identifier
  - `account_scope`: `GLOBAL` or specific `account_id`
  - `doc_status`: `CURRENT` (filter out `DEPRECATED`)
  - `authority_weight`: Integer rank (100 = Contract, 80 = SOP, 70 = Support Policy, 60 = Operations Guide)
- **Strict Exclusion**: Historical ticket resolution notes are excluded from vector embedding to avoid hallucination contamination.
