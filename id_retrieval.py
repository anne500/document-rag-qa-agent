"""Whole-ID priority with semantic fallback. No learned fusion or answer scoring."""

import hashlib
import json
import re


# ASCII hyphens; final component is optional letters followed by digits.
ID_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"[A-Za-z][A-Za-z0-9]*-(?:[A-Za-z0-9]+-)*[A-Za-z]*[0-9]+"
    r"(?![A-Za-z0-9_-])"
)


def identifiers(text):
    """Return unique identifiers in query order, normalized to upper case."""
    return list(dict.fromkeys(match.group(0).upper() for match in ID_PATTERN.finditer(text)))


def candidate(text, metadata, distance=None):
    if not isinstance(text, str) or not isinstance(metadata.get("source"), str):
        raise ValueError("Indexed chunks need text and source metadata")
    return {
        "source": metadata["source"], "page": metadata.get("page"),
        "text": text, "metadata": dict(metadata), "distance": distance,
    }


def chunk_key(chunk):
    identity = [chunk["source"], chunk.get("page"), chunk["text"]]
    return hashlib.sha256(
        json.dumps(identity, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


class IdentifierIndex:
    def __init__(self, inventory):
        self.chunks = {}
        self.by_id = {}
        for item in inventory:
            key = chunk_key(item)
            self.chunks.setdefault(key, dict(item))
            for identifier in identifiers(item["text"]):
                self.by_id.setdefault(identifier, set()).add(key)

    def rerank(self, query, semantic):
        """One best chunk per known query ID, other ID chunks, then semantic."""
        query_ids = identifiers(query)
        known = [identifier for identifier in query_ids if identifier in self.by_id]
        unknown = [identifier for identifier in query_ids if identifier not in self.by_id]
        decorated = [
            {**item, "semantic_rank": rank, "selection": "semantic"}
            for rank, item in enumerate(semantic, start=1)
        ]
        trace = {
            "query_ids": query_ids, "matched_ids": known, "unknown_ids": unknown,
            "policy": "id_priority" if known else "semantic_fallback",
            "semantic_candidates": len(semantic), "exact_candidate_count": 0,
        }
        if not known:
            return decorated, trace

        semantic_by_key = {}
        for item in decorated:
            semantic_by_key.setdefault(chunk_key(item), item)
        exact_keys = set().union(*(self.by_id[identifier] for identifier in known))
        trace["exact_candidate_count"] = len(exact_keys)

        def order(key):
            item = semantic_by_key.get(key, self.chunks[key])
            return (
                item.get("semantic_rank", float("inf")),
                item["source"], item.get("page") or 0, key,
            )

        selected = []
        seen = set()

        def append(key, reason):
            if key in seen:
                return
            seen.add(key)
            item = dict(semantic_by_key.get(key, self.chunks[key]))
            item.setdefault("semantic_rank", None)
            item["selection"] = reason
            item["matched_query_ids"] = [
                identifier for identifier in known if key in self.by_id[identifier]
            ]
            selected.append(item)

        # Query-order coverage prevents many chunks for ID 1 crowding out ID 2.
        for identifier in known:
            append(min(self.by_id[identifier], key=order), "exact_id")
        for key in sorted(exact_keys, key=order):
            append(key, "exact_id")
        for item in decorated:
            key = chunk_key(item)
            if key not in seen:
                seen.add(key)
                selected.append(item)
        return selected, trace


class IdentifierAwareRetriever:
    """Small-corpus adapter: cache indexed text once, search semantics per query."""

    def __init__(self, vectorstore, candidate_pool=20):
        if type(candidate_pool) is not int or candidate_pool < 1:
            raise ValueError("candidate_pool must be a positive integer")
        self.vectorstore = vectorstore
        self.candidate_pool = candidate_pool
        result = vectorstore.get(include=["documents", "metadatas"])
        texts = result.get("documents")
        metadata = result.get("metadatas")
        if texts is None or metadata is None or len(texts) != len(metadata):
            raise ValueError("Vector store returned inconsistent chunk columns")
        self.inventory = [
            candidate(text, meta or {}) for text, meta in zip(texts, metadata)
        ]
        if not self.inventory:
            raise ValueError("No indexed chunks available")
        self.index = IdentifierIndex(self.inventory)

    def retrieve(self, query, k):
        if type(k) is not int or k < 1:
            raise ValueError("k must be a positive integer")
        pool = min(max(k, self.candidate_pool), len(self.inventory))
        semantic = [
            candidate(doc.page_content, doc.metadata, float(distance))
            for doc, distance in self.vectorstore.similarity_search_with_score(query, k=pool)
        ]
        ranked, trace = self.index.rerank(query, semantic)
        return {"ranked": ranked[:k], "trace": trace}
