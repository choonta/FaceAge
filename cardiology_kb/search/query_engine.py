"""
Full-text search across loaded ACC/ESC guidelines.
Uses TF-IDF-style term scoring without external dependencies.
"""

import re
import math
from collections import defaultdict
from typing import Optional


class QueryEngine:
    """
    In-memory inverted index over guideline recommendation text.
    Supports free-text queries with basic relevance ranking.
    """

    def __init__(self, guidelines: dict[str, dict]):
        self._guidelines = guidelines
        self._documents: list[dict] = []  # flat list of all recommendations
        self._index: dict[str, list[int]] = defaultdict(list)  # term → [doc_ids]
        self._build_index()

    # ------------------------------------------------------------------
    # Index construction
    # ------------------------------------------------------------------

    def _build_index(self) -> None:
        doc_id = 0
        for org, topics in self._guidelines.items():
            for topic, guideline in topics.items():
                for rec in guideline.get("recommendations", []):
                    # Combine all searchable text
                    text = " ".join(filter(None, [
                        rec.get("text", ""),
                        rec.get("category", ""),
                        rec.get("drug_class", ""),
                        " ".join(rec.get("drugs", [])),
                        guideline.get("title", ""),
                        topic,
                    ]))
                    doc = {
                        "doc_id": doc_id,
                        "org": org,
                        "topic": topic,
                        "guideline_title": guideline.get("title", ""),
                        "guideline_year": guideline.get("year"),
                        "text": rec.get("text", ""),
                        "class": rec.get("class", ""),
                        "level_of_evidence": rec.get("level_of_evidence", ""),
                        "category": rec.get("category", ""),
                        "drugs": rec.get("drugs", []),
                        "drug_class": rec.get("drug_class", ""),
                        "_full_text": text.lower(),
                    }
                    self._documents.append(doc)
                    for term in self._tokenise(text):
                        if doc_id not in self._index[term]:
                            self._index[term].append(doc_id)
                    doc_id += 1

        # Also index pharmacotherapy entries
        for org, topics in self._guidelines.items():
            for topic, guideline in topics.items():
                for pharm in guideline.get("pharmacotherapy", []):
                    text = " ".join(filter(None, [
                        pharm.get("drug_class", ""),
                        pharm.get("examples", ""),
                        pharm.get("indication", ""),
                        topic,
                    ]))
                    doc = {
                        "doc_id": doc_id,
                        "org": org,
                        "topic": topic,
                        "guideline_title": guideline.get("title", ""),
                        "guideline_year": guideline.get("year"),
                        "text": f"{pharm.get('drug_class')}: {pharm.get('examples')} — {pharm.get('indication')}",
                        "class": pharm.get("recommendation_class", ""),
                        "level_of_evidence": pharm.get("level_of_evidence", ""),
                        "category": "pharmacotherapy",
                        "drugs": [],
                        "drug_class": pharm.get("drug_class", ""),
                        "_full_text": text.lower(),
                    }
                    self._documents.append(doc)
                    for term in self._tokenise(text):
                        if doc_id not in self._index[term]:
                            self._index[term].append(doc_id)
                    doc_id += 1

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        org: Optional[str] = None,
        top_k: int = 10,
    ) -> list[dict]:
        """
        Return top_k results sorted by relevance score.
        Each result is a copy of the doc dict with an added 'score' key.
        """
        query_terms = self._tokenise(query)
        if not query_terms:
            return []

        scores: dict[int, float] = defaultdict(float)
        n_docs = len(self._documents)

        for term in query_terms:
            doc_ids = self._index.get(term, [])
            idf = math.log((n_docs + 1) / (len(doc_ids) + 1)) + 1.0
            for doc_id in doc_ids:
                doc = self._documents[doc_id]
                # Filter by org if requested
                if org and doc["org"].lower() != org.lower():
                    continue
                tf = doc["_full_text"].count(term)
                # Boost Class I recommendations
                class_boost = 1.5 if doc.get("class") == "I" else 1.0
                scores[doc_id] += tf * idf * class_boost

        # Phrase match bonus
        phrase = query.lower()
        for doc_id, doc in enumerate(self._documents):
            if phrase in doc["_full_text"]:
                if org and doc["org"].lower() != org.lower():
                    continue
                scores[doc_id] += 5.0

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for doc_id, score in ranked:
            result = {k: v for k, v in self._documents[doc_id].items() if k != "_full_text"}
            result["score"] = round(score, 3)
            results.append(result)

        return results

    def search_by_category(self, category: str, org: Optional[str] = None) -> list[dict]:
        """Return all recommendations matching a category tag."""
        results = []
        for doc in self._documents:
            if doc.get("category", "").lower() == category.lower():
                if org and doc["org"].lower() != org.lower():
                    continue
                results.append({k: v for k, v in doc.items() if k != "_full_text"})
        return results

    def search_class_i(self, org: Optional[str] = None, topic: Optional[str] = None) -> list[dict]:
        """Return all Class I recommendations, optionally filtered."""
        results = []
        for doc in self._documents:
            if doc.get("class") != "I":
                continue
            if org and doc["org"].lower() != org.lower():
                continue
            if topic and doc["topic"].lower() != topic.lower():
                continue
            results.append({k: v for k, v in doc.items() if k != "_full_text"})
        return results

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise(text: str) -> list[str]:
        """Lower-case, strip punctuation, split, remove stopwords."""
        _STOPWORDS = {
            "a", "an", "the", "is", "in", "of", "for", "and", "or",
            "to", "with", "on", "at", "by", "as", "be", "are", "it",
            "not", "this", "that", "from", "when", "who", "which",
        }
        tokens = re.sub(r"[^\w\s/\-]", " ", text.lower()).split()
        return [t for t in tokens if t not in _STOPWORDS and len(t) > 1]

    def stats(self) -> dict:
        """Return index statistics."""
        org_counts: dict = defaultdict(int)
        for doc in self._documents:
            org_counts[doc["org"]] += 1
        return {
            "total_documents": len(self._documents),
            "unique_terms": len(self._index),
            "by_org": dict(org_counts),
        }
