import os
import json
import re
from typing import Optional, List, Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_PATH = os.path.join(PROJECT_ROOT, "backend", "rag", "knowledge_chunks.json")

_cached_chunks: Optional[List[Dict[str, Any]]] = None

def get_knowledge_chunks() -> List[Dict[str, Any]]:
    global _cached_chunks
    if _cached_chunks is None:
        if os.path.exists(JSON_PATH):
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                _cached_chunks = json.load(f)
        else:
            _cached_chunks = []
    return _cached_chunks

def search_knowledge_base(query: str, account_id: str = None, top_k: int = 4, include_deprecated: bool = False) -> Dict[str, Any]:
    """
    Ultra-lightweight, memory-optimized Precedence Knowledge Retriever (< 5MB RAM).
    Contracts (100) > SOP v4 (80) > Policy v3 (70) > Product Guide (60) > Deprecated (0).
    """
    chunks = get_knowledge_chunks()
    if not chunks:
        # Fallback if JSON not created yet
        return {"context": "", "citations": [], "num_results": 0}

    # Normalize query tokens
    query_clean = query.lower()
    query_tokens = set(re.findall(r'\b\w+\b', query_clean))

    scored_items = []

    for item in chunks:
        meta = item.get("metadata", {})
        doc_status = meta.get("status", "CURRENT")
        doc_scope = meta.get("account_scope", "GLOBAL")
        authority = meta.get("authority_weight", 50)
        doc_text = item.get("text", "")
        doc_text_lower = doc_text.lower()

        # 1. Filter out deprecated documents unless explicitly requested
        if not include_deprecated and doc_status == "DEPRECATED":
            continue

        # 2. Filter by account scope (Allow GLOBAL + current account)
        if account_id and account_id != "GLOBAL":
            if doc_scope not in ["GLOBAL", account_id]:
                continue
        elif not account_id and doc_scope != "GLOBAL":
            # If no account specified, prefer global
            pass

        # 3. Fast keyword & token match scoring
        doc_tokens = set(re.findall(r'\b\w+\b', doc_text_lower))
        matching_tokens = query_tokens.intersection(doc_tokens)
        overlap_score = len(matching_tokens) / max(1, len(query_tokens))

        # Check exact phrase matches for key concepts
        phrase_boost = 0.0
        for phrase in [
            "cancellation", "service credit", "p1", "p2", "p3", "sla", 
            "pickup", "fee", "clause 2", "clause 4", "ki-208", "ki-211", "ki-176"
        ]:
            if phrase in query_clean and phrase in doc_text_lower:
                phrase_boost += 0.25

        # Combined precedence score
        total_match_score = overlap_score + phrase_boost
        if total_match_score > 0.05 or authority >= 100:
            rank_score = (authority * 2.0) + (total_match_score * 100.0)
            scored_items.append({
                "doc": doc_text,
                "metadata": meta,
                "match_score": total_match_score,
                "rank_score": rank_score
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
