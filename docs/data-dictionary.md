# ParcelPilot AI — Canonical Data Dictionary (Agent 02)

## 1. Table: `accounts`

| Column | Type | Nullable | Primary/Foreign Key | Description & Permitted Values | Security Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `account_id` | String (VARCHAR 32) | No | PK | Unique account identifier (e.g. `ACCT-001`). | Public / Identifiable |
| `account_name` | String (VARCHAR 128) | No | None | Customer legal entity name (e.g. `Northstar Logistics`). | Public |
| `plan` | Enum (VARCHAR 32) | No | None | Subscription tier: `Enterprise`, `Growth`, `Standard`. | Public |
| `status` | Enum (VARCHAR 32) | No | None | Account state: `active`, `suspended`, `pending`. | Internal |
| `csm` | String (VARCHAR 64) | Yes | None | Assigned Dedicated Customer Success Manager (e.g. `Priya Mehta`). | Public |
| `contract_file` | String (VARCHAR 128) | Yes | None | Name of signed contract file in docs pack (e.g. `05_...pdf`). | Internal |
| `premium_support` | Boolean | No | None | Flag indicating 24x7 dedicated routing. | Public |
| `notes` | Text | Yes | None | Operational context and account overview notes. | Internal |

---

## 2. Table: `orders`

| Column | Type | Nullable | Primary/Foreign Key | Description & Permitted Values | Security Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `order_id` | String (VARCHAR 32) | No | PK | Unique order tracking number (e.g. `ORD-1001`). | Tenant-Scoped |
| `account_id` | String (VARCHAR 32) | No | FK (`accounts.account_id`) | Owning tenant account ID. | Tenant-Scoped |
| `carrier` | String (VARCHAR 64) | No | None | Assigned logistics carrier (`SwiftShip`, `BlueDart Pro`, `RoadRunner`). | Tenant-Scoped |
| `status` | Enum (VARCHAR 32) | No | None | Order lifecycle state: `DRAFT`, `BOOKED`, `PICKED_UP`, `DELIVERED`, `CANCELLED`. | Tenant-Scoped |
| `booked_at` | DateTime | No | None | Timestamp when order was placed. | Tenant-Scoped |
| `pickup_window_start` | DateTime | Yes | None | Start of promised carrier pickup window. | Tenant-Scoped |
| `pickup_window_end` | DateTime | Yes | None | End of promised carrier pickup window. | Tenant-Scoped |
| `pickup_actual_at` | DateTime | Yes | None | Timestamp when carrier physically scanned parcel. | Tenant-Scoped |
| `shipment_fee_inr` | Float (NUMERIC 10,2) | No | None | Total delivery fee charged in INR. | Tenant-Scoped |
| `carrier_fault` | Boolean | No | None | True if carrier admitted or was verified at fault for delay. | Tenant-Scoped |
| `customer_fault` | Boolean | No | None | True if delay/miss was caused by customer unreadiness. | Tenant-Scoped |
| `cancellation_requested_at` | DateTime | Yes | None | Timestamp when customer initiated cancel request. | Tenant-Scoped |
| `notes` | Text | Yes | None | Operational order timeline notes. | Internal |

---

## 3. Table: `tickets`

| Column | Type | Nullable | Primary/Foreign Key | Description & Permitted Values | Security Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ticket_id` | String (VARCHAR 32) | No | PK | Support ticket identifier (e.g. `TKT-501`). | Tenant-Scoped |
| `account_id` | String (VARCHAR 32) | No | FK (`accounts.account_id`) | Submitting account identifier. | Tenant-Scoped |
| `created_at` | DateTime | No | None | Ticket submission timestamp. | Tenant-Scoped |
| `status` | Enum (VARCHAR 32) | No | None | Ticket lifecycle state: `open`, `pending`, `resolved`, `closed`. | Tenant-Scoped |
| `subject` | String (VARCHAR 255) | No | None | Summary subject line. | Tenant-Scoped |
| `description` | Text | No | None | Full customer issue description. | Tenant-Scoped |
| `channel` | Enum (VARCHAR 32) | No | None | Ingress channel: `email`, `chat`, `phone`. | Tenant-Scoped |
| `assigned_to` | String (VARCHAR 64) | Yes | None | Assigned support rep (e.g. `Rohit`, `Maya`). | Internal |
| `last_customer_message_at` | DateTime | Yes | None | Timestamp of most recent inbound message. | Tenant-Scoped |
| `historical_resolution` | Text | Yes | None | Past agent resolution notes (**Historical context only; zero policy weight**). | Internal |

---

## 4. Table: `pending_actions` (Two-Phase State Machine)

| Column | Type | Nullable | Primary/Foreign Key | Description & Permitted Values | Security Level |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `action_token` | String (UUID) | No | PK | Unique secure idempotency token for the proposed action. | Session-Scoped |
| `session_id` | String (VARCHAR 64) | No | None | Active chat session identifier. | Session-Scoped |
| `account_id` | String (VARCHAR 32) | No | FK (`accounts.account_id`) | Target tenant account. | Tenant-Scoped |
| `user_role` | String (VARCHAR 32) | No | None | Role of preparing user (`customer`, `support_agent`, `ops_manager`). | Internal |
| `action_type` | Enum (VARCHAR 64) | No | None | Action name (`cancel_order`, `apply_service_credit`, `escalate_ticket`, `update_ticket`). | Internal |
| `parameters` | JSON | No | None | Serialized JSON parameters for execution. | Internal |
| `summary` | Text | No | None | Plain English summary displayed on confirmation card. | Public |
| `status` | Enum (VARCHAR 32) | No | None | `PENDING`, `EXECUTED`, `CANCELLED`, `EXPIRED`. | Internal |
| `created_at` | DateTime | No | None | Proposal timestamp. | Internal |
| `expires_at` | DateTime | No | None | Expiration cutoff timestamp (e.g., created_at + 15 mins). | Internal |
