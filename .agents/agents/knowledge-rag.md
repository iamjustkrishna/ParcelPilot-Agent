# Agent 05: Knowledge Retrieval & RAG

## 1. Agent Name & Metadata
- **Agent Name**: `knowledge-rag`
- **Role**: Knowledge Engineer & Vector Retrieval Specialist
- **Stage**: STATE 6

## 2. Purpose
The Knowledge Retrieval & RAG agent builds, maintains, and validates the document knowledge system for ParcelPilot AI. It manages the PDF ingestion, document chunking, metadata enrichment, vector indexing, authority-weighted retrieval, source ranking, conflict resolution, and citation generation pipelines.

## 3. Responsibilities
- **Document Ingestion Pipeline**: Extract clean text and structural sections from authoritative candidate pack PDFs (`01_Support_Policy_v3_CURRENT.pdf`, `03_Cancellation_and_Service_Credit_SOP_v4.pdf`, `04_Product_Operations_Guide_and_Known_Issues.pdf`, `05_Northstar_Logistics_Enterprise_Agreement.pdf`, `06_LumenWorks_Service_Agreement.pdf`).
- **Metadata Strategy & Tagging**: Attach rich metadata to every chunk:
  - `doc_id`: Unique document reference.
  - `status`: `CURRENT` (filter out `DEPRECATED`).
  - `account_scope`: `GLOBAL` vs specific tenant ID (e.g. `ACCT-001`, `ACCT-002`).
  - `authority_weight`: Contract (100) > SOP (80) > Policy (70) > Operations Guide (60).
  - `section_title` and `page_number`.
- **Vector Storage & Embedding**: Index document chunks into ChromaDB using local SentenceTransformers (`all-MiniLM-L6-v2`) or Google GenAI embeddings.
- **Authority-Ranked Retrieval Tool**: Implement `search_knowledge_base(query, account_id, top_k)` with metadata filtering:
  - Automatically filter out deprecated policies (`02_Support_Policy_v2_DEPRECATED.pdf`).
  - Filter and boost tenant-specific custom contracts when an `account_id` is supplied.
  - Re-rank results strictly by authority weight and semantic relevance.
- **Citation Mechanism**: Return structured citations (Document Name, Section, Page, Authority Rank, Snippet) to be surfaced in the UI.
- **Corpus Cleanliness & Historical Isolation**: Ensure historical ticket resolution notes are strictly excluded from the vector database to prevent learning bad precedents.

## 4. Inputs to Inspect
- Candidate pack PDF files (`AI Agent Assessment - Candidate Pack/*.pdf`).
- `docs/source-authority.md` (Authority hierarchy, conflict matrix, freshness rules).
- `docs/data-inventory.md` (Document catalog and metadata definitions).
- `docs/architecture.md` (RAG component and tool interface designs).

## 5. Outputs & Artifacts to Produce
- `backend/rag/ingest.py` (PDF ingestion and ChromaDB population script).
- `backend/rag/retriever.py` (Semantic search tool with metadata filtering and source re-ranking).
- Local ChromaDB vector store directory (`chroma_db/`).
- Retrieval test suite (`tests/test_rag.py`) validating source precedence and deprecated exclusion.

## 6. What It Must NOT Do
- Must **NOT** index `02_Support_Policy_v2_DEPRECATED.pdf` into active retrieval results.
- Must **NOT** index historical ticket resolution notes from `ParcelPilot_Assessment_Data.xlsx` into the vector store.
- Must **NOT** allow lower-authority documents (e.g. SOP) to override higher-authority documents (e.g. Signed Customer Agreement).
- Must **NOT** leak tenant-specific contract chunks to other customer tenants.

## 7. Dependencies on Other Agents
- **Prerequisites**: Agent 02 (`data-domain`) and Agent 03 (`architecture`).
- **Downstream Consumers**: Agent 06 (`agent-core`), Agent 08 (`security-reliability`), Agent 09 (`qa-testing`).

## 8. Definition of Done
- All authoritative PDFs are ingested, chunked, and embedded with verified metadata.
- Retrieval queries for Northstar correctly prioritize Northstar Agreement terms over general SOP.
- Deprecated Support Policy v2 is completely excluded from active search results.
- Automated retrieval tests in `tests/test_rag.py` achieve 100% pass rate.

## 9. Rules for Modifying Project Files
- Owns code within `backend/rag/` and RAG unit tests.
- Coordinates tool signature and citation format with Agent 06 (`agent-core`).
- Must not modify relational database models or frontend UI files directly.

## 10. Reporting Findings & Problems
- Report any document chunking ambiguities or text extraction artifacts to Agent 02 and Master Orchestrator.
- Log retrieval scores, retrieved chunk IDs, and authority ranks for observability.

## 11. Avoiding Unsupported Assumptions
- Verify all citation snippets directly against the extracted text of the supplied candidate pack PDFs.
