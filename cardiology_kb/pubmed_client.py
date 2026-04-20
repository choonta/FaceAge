"""
PubMed/NCBI Entrez client using the public E-utilities REST API.
No Biopython dependency — uses only urllib from the standard library,
with optional requests if available.
"""

import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Optional

_ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Pre-built cardiology MeSH queries for convenience
CARDIOLOGY_QUERIES = {
    "heart_failure": "(heart failure[MeSH]) AND (treatment[MeSH] OR therapy[MeSH])",
    "atrial_fibrillation": "atrial fibrillation[MeSH] AND (management OR anticoagulation OR ablation)",
    "hypertension": "hypertension[MeSH] AND (treatment OR drug therapy[MeSH])",
    "acute_mi": "(myocardial infarction[MeSH]) AND (therapy OR intervention OR PCI)",
    "lipids": "(dyslipidemias[MeSH] OR cholesterol[MeSH]) AND (statin OR PCSK9 OR therapy)",
    "valvular_disease": "heart valve diseases[MeSH] AND (surgery OR TAVR OR repair)",
    "cardiac_prevention": "cardiovascular diseases[MeSH] AND prevention AND control[MeSH]",
    "faceage_prognostication": "biological age AND cardiovascular prognosis",
    "sglt2_heart_failure": "SGLT2 inhibitors AND heart failure AND clinical trial",
    "pcsk9_inhibitors": "PCSK9 inhibitors AND cardiovascular outcomes",
    "catheter_ablation_af": "catheter ablation AND atrial fibrillation AND randomized",
    "cardiac_biomarkers": "BNP OR NT-proBNP AND heart failure AND prognosis"
}


class PubMedClient:
    """
    Lightweight PubMed client via NCBI E-utilities.

    All methods return structured dicts with article metadata.
    Rate-limited to 3 requests/second (NCBI limit without API key).
    """

    def __init__(self, email: str = "cardiology_kb@research.org", api_key: Optional[str] = None):
        self.email = email
        self.api_key = api_key
        self._last_request = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        date_range: Optional[tuple] = None,
    ) -> list[dict]:
        """
        Search PubMed, return list of article dicts.

        Parameters
        ----------
        query       : PubMed query string
        max_results : Maximum articles to return (≤10000)
        sort        : "relevance" or "pub_date"
        date_range  : (mindate, maxdate) as "YYYY/MM/DD"
        """
        pmids = self._esearch(query, max_results=max_results, sort=sort, date_range=date_range)
        if not pmids:
            return []
        return self._efetch_batch(pmids)

    def fetch(self, pmid: str) -> dict:
        """Fetch full metadata for a single article by PMID."""
        results = self._efetch_batch([str(pmid)])
        if not results:
            raise ValueError(f"PMID {pmid} not found.")
        return results[0]

    def search_guidelines(
        self,
        topic: str,
        org: Optional[str] = None,
        max_results: int = 10,
    ) -> list[dict]:
        """
        Convenience method: search PubMed for clinical practice guidelines
        on a cardiology topic, optionally filtered by ACC or ESC.

        Parameters
        ----------
        topic : e.g. "heart failure", "atrial fibrillation"
        org   : "ACC", "ESC", "AHA", or None for all
        """
        base = f"({topic}[Title/Abstract]) AND (guideline[Publication Type] OR practice guideline[Publication Type])"
        if org:
            base += f' AND ("{org}"[Title/Abstract] OR "{org}"[Affiliation])'
        return self.search(base, max_results=max_results, sort="pub_date")

    def search_rcts(self, topic: str, max_results: int = 10) -> list[dict]:
        """Search for randomized controlled trials on a cardiology topic."""
        query = f'({topic}[Title/Abstract]) AND (randomized controlled trial[Publication Type])'
        return self.search(query, max_results=max_results, sort="relevance")

    def search_meta_analyses(self, topic: str, max_results: int = 10) -> list[dict]:
        """Search for meta-analyses and systematic reviews on a topic."""
        query = (
            f'({topic}[Title/Abstract]) AND '
            '(meta-analysis[Publication Type] OR systematic review[Publication Type])'
        )
        return self.search(query, max_results=max_results, sort="relevance")

    def get_related(self, pmid: str, max_results: int = 5) -> list[dict]:
        """Fetch articles related to a given PMID via NCBI elink."""
        related_pmids = self._elink(pmid, max_results=max_results)
        if not related_pmids:
            return []
        return self._efetch_batch(related_pmids[:max_results])

    def format_citation(self, article: dict, style: str = "vancouver") -> str:
        """
        Format an article dict as a citation string.

        Parameters
        ----------
        style : "vancouver" or "ama"
        """
        authors = article.get("authors", [])
        if style == "vancouver":
            if len(authors) > 6:
                author_str = ", ".join(authors[:6]) + ", et al."
            else:
                author_str = ", ".join(authors)
            return (
                f"{author_str}. "
                f"{article.get('title', 'N/A')}. "
                f"{article.get('journal', 'N/A')}. "
                f"{article.get('year', 'N/A')};{article.get('volume', '')}({article.get('issue', '')}):{article.get('pages', '')}. "
                f"doi:{article.get('doi', 'N/A')}. PMID:{article.get('pmid', 'N/A')}"
            )
        return str(article)

    # ------------------------------------------------------------------
    # E-utilities internals
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < 0.34:  # ~3 req/s
            time.sleep(0.34 - elapsed)
        self._last_request = time.time()

    def _build_params(self, extra: dict) -> str:
        params = {"tool": "cardiology_kb", "email": self.email, **extra}
        if self.api_key:
            params["api_key"] = self.api_key
        return urllib.parse.urlencode(params)

    def _get(self, url: str) -> str:
        self._rate_limit()
        req = urllib.request.Request(url, headers={"User-Agent": "cardiology_kb/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")

    def _esearch(
        self,
        query: str,
        max_results: int,
        sort: str,
        date_range: Optional[tuple],
    ) -> list[str]:
        params: dict = {
            "db": "pubmed",
            "term": query,
            "retmax": min(max_results, 10000),
            "retmode": "json",
            "sort": "relevance" if sort == "relevance" else "pub+date",
            "usehistory": "n",
        }
        if date_range:
            params["mindate"] = date_range[0]
            params["maxdate"] = date_range[1]
            params["datetype"] = "pdat"
        url = f"{_ENTREZ_BASE}/esearch.fcgi?{self._build_params(params)}"
        try:
            data = json.loads(self._get(url))
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as exc:
            return []

    def _efetch_batch(self, pmids: list[str]) -> list[dict]:
        if not pmids:
            return []
        params = {
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "xml",
            "rettype": "abstract",
        }
        url = f"{_ENTREZ_BASE}/efetch.fcgi?{self._build_params(params)}"
        try:
            xml_text = self._get(url)
            return self._parse_pubmed_xml(xml_text)
        except Exception as exc:
            return [{"pmid": p, "error": str(exc)} for p in pmids]

    def _elink(self, pmid: str, max_results: int) -> list[str]:
        params = {
            "dbfrom": "pubmed",
            "db": "pubmed",
            "id": pmid,
            "cmd": "neighbor_score",
            "retmode": "json",
        }
        url = f"{_ENTREZ_BASE}/elink.fcgi?{self._build_params(params)}"
        try:
            data = json.loads(self._get(url))
            link_sets = data.get("linksets", [])
            if not link_sets:
                return []
            links = link_sets[0].get("linksetdbs", [])
            for link_db in links:
                if link_db.get("linkname") == "pubmed_pubmed":
                    return [str(l["id"]) for l in link_db.get("links", [])][:max_results]
        except Exception:
            pass
        return []

    @staticmethod
    def _parse_pubmed_xml(xml_text: str) -> list[dict]:
        articles = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        for article_elem in root.findall(".//PubmedArticle"):
            article = {}

            # PMID
            pmid_elem = article_elem.find(".//PMID")
            article["pmid"] = pmid_elem.text if pmid_elem is not None else ""

            # Title
            title_elem = article_elem.find(".//ArticleTitle")
            article["title"] = (title_elem.text or "").strip() if title_elem is not None else ""

            # Abstract
            abstract_parts = article_elem.findall(".//AbstractText")
            if abstract_parts:
                parts = []
                for p in abstract_parts:
                    label = p.get("Label", "")
                    text = p.text or ""
                    parts.append(f"{label}: {text}" if label else text)
                article["abstract"] = " ".join(parts).strip()
            else:
                article["abstract"] = ""

            # Authors
            authors = []
            for author in article_elem.findall(".//Author"):
                last = author.findtext("LastName", "")
                first = author.findtext("Initials", "")
                if last:
                    authors.append(f"{last} {first}".strip())
            article["authors"] = authors

            # Journal
            journal_elem = article_elem.find(".//Journal/Title")
            article["journal"] = journal_elem.text if journal_elem is not None else ""

            # ISO abbreviation
            iso_elem = article_elem.find(".//Journal/ISOAbbreviation")
            article["journal_abbrev"] = iso_elem.text if iso_elem is not None else ""

            # Year
            year_elem = (
                article_elem.find(".//Journal/JournalIssue/PubDate/Year")
                or article_elem.find(".//PubDate/Year")
            )
            article["year"] = year_elem.text if year_elem is not None else ""

            # Volume / Issue / Pages
            article["volume"] = article_elem.findtext(".//Volume", "")
            article["issue"] = article_elem.findtext(".//Issue", "")
            article["pages"] = article_elem.findtext(".//MedlinePgn", "")

            # DOI
            doi = ""
            for loc_id in article_elem.findall(".//ArticleId"):
                if loc_id.get("IdType") == "doi":
                    doi = loc_id.text or ""
                    break
            article["doi"] = doi

            # MeSH terms
            mesh_terms = []
            for mesh in article_elem.findall(".//MeshHeading/DescriptorName"):
                if mesh.text:
                    mesh_terms.append(mesh.text)
            article["mesh_terms"] = mesh_terms

            # Publication types
            pub_types = [
                pt.text
                for pt in article_elem.findall(".//PublicationType")
                if pt.text
            ]
            article["publication_types"] = pub_types

            # URL
            article["url"] = (
                f"https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/"
                if article.get("pmid") else ""
            )

            articles.append(article)

        return articles


def quick_search(query: str, max_results: int = 5) -> list[dict]:
    """Module-level convenience function."""
    client = PubMedClient()
    return client.search(query, max_results=max_results)
