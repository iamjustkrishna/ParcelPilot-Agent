import os
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANDIDATE_PACK_DIR = os.path.join(PROJECT_ROOT, "AI Agent Assessment - Candidate Pack")
CHROMA_DB_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

DOC_METADATA_REGISTRY = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "doc_id": "DOC-POL-V3",
        "doc_name": "ParcelPilot Support Policy v3",
        "doc_type": "policy",
        "status": "CURRENT",
        "authority_weight": 70,
        "account_scope": "GLOBAL",
        "effective_date": "2026-05-01",
        "summary": "Default support severity definitions (P1/P2/P3), response targets per tier, and escalation guidelines."
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "doc_id": "DOC-POL-V2-DEPRECATED",
        "doc_name": "ParcelPilot Support Policy v2 (DEPRECATED)",
        "doc_type": "policy",
        "status": "DEPRECATED",
        "authority_weight": 0,
        "account_scope": "GLOBAL",
        "effective_date": "2025-01-01",
        "summary": "Deprecated historical support policy. Not to be used for active query resolution."
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "doc_id": "DOC-SOP-V4",
        "doc_name": "ParcelPilot Cancellation & Service Credit SOP v4",
        "doc_type": "sop",
        "status": "CURRENT",
        "authority_weight": 80,
        "account_scope": "GLOBAL",
        "effective_date": "2026-06-15",
        "summary": "Standard cancellation fee rules (INR 250 after 30 mins) and failed-pickup service credits (lower of INR 500 or 10%)."
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "doc_id": "DOC-PROD-GUIDE",
        "doc_name": "ParcelPilot Product Operations Guide & Known Issues",
        "doc_type": "operations_guide",
        "status": "CURRENT",
        "authority_weight": 60,
        "account_scope": "GLOBAL",
        "effective_date": "2026-08-14",
        "summary": "Product plan limits (Bulk upload 5,000 CSV rows) and known issues KI-208, KI-211, KI-176."
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "doc_id": "DOC-AGR-NORTHSTAR",
        "doc_name": "Northstar Logistics Enterprise Agreement",
        "doc_type": "contract",
        "status": "CURRENT",
        "authority_weight": 100,
        "account_scope": "ACCT-001",
        "effective_date": "2026-01-01",
        "summary": "Northstar custom terms: P1 SLA 15m 24x7, P2 1h, P3 8h; free pre-pickup cancellation waiver; monthly credit cap INR 5,000; CSM Priya Mehta."
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "doc_id": "DOC-AGR-LUMENWORKS",
        "doc_name": "LumenWorks Service Agreement",
        "doc_type": "contract",
        "status": "CURRENT",
        "authority_weight": 100,
        "account_scope": "ACCT-002",
        "effective_date": "2026-03-01",
        "summary": "LumenWorks custom terms: Growth plan SLA (no weekend coverage); standard cancellation; fixed INR 300 credit for >4h delay with carrier fault."
    }
}

def extract_pdf_sections(pdf_path: str, doc_name: str):
    doc = fitz.open(pdf_path)
    chunks = []
    
    full_text = ""
    for page_idx, page in enumerate(doc):
        text = page.get_text()
        full_text += f"\n--- Page {page_idx + 1} ---\n" + text

    # Split logically by major headings or paragraphs
    lines = full_text.split("\n")
    current_section = "General Overview"
    current_chunk = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Detect section headings (numbered or status lines)
        if (stripped.startswith("1. ") or stripped.startswith("2. ") or 
            stripped.startswith("3. ") or stripped.startswith("4. ") or
            stripped.startswith("KI-") or stripped.startswith("Status:")):
            if current_chunk:
                chunk_content = "\n".join(current_chunk).strip()
                if len(chunk_content) > 30:
                    chunks.append({
                        "section": current_section,
                        "text": f"[{doc_name} - {current_section}]\n{chunk_content}"
                    })
                current_chunk = []
            current_section = stripped
        current_chunk.append(stripped)

    if current_chunk:
        chunk_content = "\n".join(current_chunk).strip()
        if len(chunk_content) > 30:
            chunks.append({
                "section": current_section,
                "text": f"[{doc_name} - {current_section}]\n{chunk_content}"
            })

    return chunks

def ingest_documents():
    print(f"Initializing ChromaDB vector store at: {CHROMA_DB_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

    # Use SentenceTransformers embedding function
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Drop existing collection if present to guarantee clean rebuild
    try:
        client.delete_collection(name="parcelpilot_knowledge_base")
    except Exception:
        pass

    collection = client.create_collection(
        name="parcelpilot_knowledge_base",
        embedding_function=embedding_fn,
        metadata={"description": "Authoritative ParcelPilot policy, SOP, operations guide, and agreement chunks"}
    )

    total_chunks = 0
    for filename, meta in DOC_METADATA_REGISTRY.items():
        pdf_path = os.path.join(CANDIDATE_PACK_DIR, filename)
        if not os.path.exists(pdf_path):
            print(f"Warning: File {filename} not found at {pdf_path}")
            continue

        print(f"Ingesting: {filename} (Authority: {meta['authority_weight']}, Scope: {meta['account_scope']}, Status: {meta['status']})")
        extracted_chunks = extract_pdf_sections(pdf_path, meta["doc_name"])

        for idx, item in enumerate(extracted_chunks):
            chunk_id = f"{meta['doc_id']}_chunk_{idx+1}"
            chunk_metadata = {
                "doc_id": meta["doc_id"],
                "doc_name": meta["doc_name"],
                "doc_type": meta["doc_type"],
                "status": meta["status"],
                "authority_weight": meta["authority_weight"],
                "account_scope": meta["account_scope"],
                "effective_date": meta["effective_date"],
                "section": item["section"],
                "filename": filename
            }

            collection.add(
                ids=[chunk_id],
                documents=[item["text"]],
                metadatas=[chunk_metadata]
            )
            total_chunks += 1

    print(f"Successfully ingested {total_chunks} authoritative knowledge chunks into ChromaDB!")

if __name__ == "__main__":
    ingest_documents()
