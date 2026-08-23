import os
import chromadb
from chromadb.utils import embedding_functions

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_DB_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

_client = None
_collection = None

def get_chroma_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        _collection = _client.get_collection(
            name="parcelpilot_knowledge_base",
            embedding_function=embedding_fn
        )
    return _collection

def search_knowledge_base(query: str, account_id: str = None, top_k: int = 4, include_deprecated: bool = False):
    """
    Retrieves authoritative documents and SOPs with metadata filtering and source precedence ranking.
    Contract (100) > SOP (80) > Policy (70) > Operations Guide (60) > Deprecated (0).
    """
    collection = get_chroma_collection()

    # Build metadata filter condition
    # Filter out deprecated documents unless explicitly requested
    if account_id and account_id != "GLOBAL":
        where_clause = {
            "$and": [
                {"status": "CURRENT" if not include_deprecated else {"$in": ["CURRENT", "DEPRECATED"]}},
                {"account_scope": {"$in": ["GLOBAL", account_id]}}
            ]
        }
    else:
        where_clause = {
            "status": "CURRENT" if not include_deprecated else {"$in": ["CURRENT", "DEPRECATED"]}
        }

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k * 2, 10),
        where=where_clause
    )

    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results["metadatas"] else []
    distances = results["distances"][0] if results["distances"] else []

    scored_items = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        authority = meta.get("authority_weight", 50)
        # Higher authority gets a significant precedence boost
        similarity_score = max(0.0, 1.0 - dist)
        combined_rank = (authority * 1.5) + (similarity_score * 100)

        scored_items.append({
            "doc": doc,
            "metadata": meta,
            "distance": dist,
            "similarity": similarity_score,
            "rank_score": combined_rank
        })

    # Sort by authority-weighted score descending
    scored_items.sort(key=lambda x: x["rank_score"], reverse=True)
    top_items = scored_items[:top_k]

    citations = []
    formatted_texts = []

    for item in top_items:
        meta = item["metadata"]
        citations.append({
            "doc_id": meta.get("doc_id"),
            "doc_name": meta.get("doc_name"),
            "section": meta.get("section"),
            "authority_weight": meta.get("authority_weight"),
            "account_scope": meta.get("account_scope"),
            "filename": meta.get("filename"),
            "snippet": item["doc"][:300] + "..." if len(item["doc"]) > 300 else item["doc"]
        })
        formatted_texts.append(
            f"=== DOCUMENT: {meta.get('doc_name')} (Authority Weight: {meta.get('authority_weight')}) ===\n"
            f"Section: {meta.get('section')}\n"
            f"Scope: {meta.get('account_scope')} | Effective: {meta.get('effective_date')}\n"
            f"Content:\n{item['doc']}\n"
        )

    full_context = "\n\n".join(formatted_texts)
    return {
        "context": full_context,
        "citations": citations,
        "num_results": len(top_items)
    }

if __name__ == "__main__":
    # Quick sanity check
    res = search_knowledge_base("cancellation policy", account_id="ACCT-001")
    print(f"Retrieved {res['num_results']} results for Northstar:")
    for c in res["citations"]:
        print(f"- [{c['authority_weight']}] {c['doc_name']} -> {c['section']}")
