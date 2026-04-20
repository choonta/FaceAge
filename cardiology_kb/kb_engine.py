"""
Core knowledge base engine — loads ACC/ESC guidelines and exposes
unified search, lookup, and PubMed query helpers.
"""

import json
import os
from pathlib import Path
from typing import Optional

from .search.query_engine import QueryEngine
from .pubmed_client import PubMedClient

_GUIDELINES_DIR = Path(__file__).parent / "guidelines"


class CardiologyKB:
    """
    Unified cardiology knowledge base.

    Usage
    -----
    >>> kb = CardiologyKB()
    >>> kb.search("SGLT2 inhibitor heart failure")
    >>> kb.get_guideline("acc", "heart_failure")
    >>> kb.pubmed_search("FaceAge cardiovascular prognosis", max_results=5)
    """

    def __init__(self, pubmed_email: Optional[str] = None):
        self._guidelines: dict[str, dict] = {}
        self._load_all_guidelines()
        self.query_engine = QueryEngine(self._guidelines)
        self.pubmed = PubMedClient(email=pubmed_email or "cardiology_kb@research.org")

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_all_guidelines(self) -> None:
        for org in ("acc", "esc"):
            org_dir = _GUIDELINES_DIR / org
            if not org_dir.exists():
                continue
            self._guidelines[org] = {}
            for json_file in sorted(org_dir.glob("*.json")):
                topic = json_file.stem
                with open(json_file) as fh:
                    self._guidelines[org][topic] = json.load(fh)

    # ------------------------------------------------------------------
    # Guideline access
    # ------------------------------------------------------------------

    def list_guidelines(self) -> dict[str, list[str]]:
        """Return {org: [topic, ...]} for all loaded guidelines."""
        return {org: sorted(topics.keys()) for org, topics in self._guidelines.items()}

    def get_guideline(self, org: str, topic: str) -> dict:
        """
        Retrieve a full guideline document.

        Parameters
        ----------
        org   : "acc" or "esc"
        topic : e.g. "heart_failure", "atrial_fibrillation"
        """
        org = org.lower()
        topic = topic.lower()
        try:
            return self._guidelines[org][topic]
        except KeyError:
            available = self.list_guidelines().get(org, [])
            raise KeyError(
                f"No guideline '{topic}' for '{org}'. "
                f"Available: {available}"
            )

    def get_recommendations(
        self,
        org: str,
        topic: str,
        rec_class: Optional[str] = None,
        level_of_evidence: Optional[str] = None,
    ) -> list[dict]:
        """
        Filter recommendations by class (I, IIa, IIb, III) and/or
        level of evidence (A, B, C).
        """
        guideline = self.get_guideline(org, topic)
        recs = guideline.get("recommendations", [])
        if rec_class:
            recs = [r for r in recs if r.get("class", "").upper() == rec_class.upper()]
        if level_of_evidence:
            recs = [
                r
                for r in recs
                if r.get("level_of_evidence", "").upper() == level_of_evidence.upper()
            ]
        return recs

    # ------------------------------------------------------------------
    # Cross-guideline comparison
    # ------------------------------------------------------------------

    def compare(self, topic: str) -> dict:
        """
        Side-by-side comparison of ACC and ESC recommendations for a topic.
        Returns {"acc": [...], "esc": [...]} or notes if one is missing.
        """
        result = {}
        for org in ("acc", "esc"):
            try:
                g = self.get_guideline(org, topic)
                result[org] = {
                    "title": g.get("title"),
                    "year": g.get("year"),
                    "key_recommendations": [
                        r for r in g.get("recommendations", []) if r.get("class") == "I"
                    ],
                }
            except KeyError:
                result[org] = None
        return result

    # ------------------------------------------------------------------
    # Full-text search
    # ------------------------------------------------------------------

    def search(self, query: str, org: Optional[str] = None, top_k: int = 10) -> list[dict]:
        """
        Free-text search across all (or a single org's) guidelines.

        Returns ranked list of matching recommendation objects annotated
        with {org, topic, score}.
        """
        return self.query_engine.search(query, org=org, top_k=top_k)

    # ------------------------------------------------------------------
    # Drug lookup
    # ------------------------------------------------------------------

    def drug_lookup(self, drug_name: str) -> list[dict]:
        """
        Find all guideline mentions of a drug or drug class.
        Returns list of {org, topic, recommendation, class, level_of_evidence}.
        """
        hits = []
        for org, topics in self._guidelines.items():
            for topic, guideline in topics.items():
                for rec in guideline.get("recommendations", []):
                    text = " ".join([
                        rec.get("text", ""),
                        rec.get("drug", ""),
                        rec.get("drug_class", ""),
                        " ".join(rec.get("drugs", [])),
                    ]).lower()
                    if drug_name.lower() in text:
                        hits.append({
                            "org": org.upper(),
                            "topic": topic,
                            "guideline_title": guideline.get("title"),
                            "year": guideline.get("year"),
                            "recommendation": rec.get("text"),
                            "class": rec.get("class"),
                            "level_of_evidence": rec.get("level_of_evidence"),
                        })
        return hits

    # ------------------------------------------------------------------
    # PubMed
    # ------------------------------------------------------------------

    def pubmed_search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        date_range: Optional[tuple[str, str]] = None,
    ) -> list[dict]:
        """
        Search PubMed and return structured article metadata.

        Parameters
        ----------
        query       : PubMed query string (MeSH terms work well)
        max_results : max articles to return
        sort        : "relevance" or "pub_date"
        date_range  : ("YYYY/MM/DD", "YYYY/MM/DD") inclusive
        """
        return self.pubmed.search(
            query, max_results=max_results, sort=sort, date_range=date_range
        )

    def pubmed_fetch(self, pmid: str) -> dict:
        """Fetch full metadata for a single PubMed article by PMID."""
        return self.pubmed.fetch(pmid)

    # ------------------------------------------------------------------
    # Summary helpers
    # ------------------------------------------------------------------

    def summary(self, org: str, topic: str) -> str:
        """Human-readable summary of a guideline."""
        g = self.get_guideline(org, topic)
        lines = [
            f"{'='*60}",
            f"{g.get('title', topic.upper())}",
            f"Organisation : {org.upper()}   Year: {g.get('year', 'N/A')}",
            f"{'='*60}",
            "",
            "KEY DEFINITIONS",
            "-" * 40,
        ]
        for k, v in g.get("definitions", {}).items():
            lines.append(f"  {k}: {v}")

        lines += ["", "CLASS I RECOMMENDATIONS", "-" * 40]
        for rec in g.get("recommendations", []):
            if rec.get("class") == "I":
                loe = rec.get("level_of_evidence", "")
                lines.append(f"  [{loe}] {rec.get('text')}")

        lines += ["", "KEY DRUG THERAPIES", "-" * 40]
        for drug in g.get("pharmacotherapy", []):
            lines.append(
                f"  {drug.get('drug_class')}: {drug.get('examples')}  "
                f"[{drug.get('recommendation_class')}/{drug.get('level_of_evidence')}]"
            )

        return "\n".join(lines)

    def __repr__(self) -> str:
        counts = {org: len(t) for org, t in self._guidelines.items()}
        return f"CardiologyKB(guidelines={counts})"
