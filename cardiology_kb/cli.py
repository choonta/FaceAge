"""
Command-line interface for the Cardiology Knowledge Base.


Usage examples
--------------
  python -m cardiology_kb.cli search "SGLT2 inhibitor heart failure"
  python -m cardiology_kb.cli guideline acc heart_failure
  python -m cardiology_kb.cli compare heart_failure
  python -m cardiology_kb.cli drug "ticagrelor"
  python -m cardiology_kb.cli pubmed "empagliflozin heart failure" --n 5
  python -m cardiology_kb.cli pubmed-rct "catheter ablation atrial fibrillation"
  python -m cardiology_kb.cli list
  python -m cardiology_kb.cli stats
"""

import argparse
import json
import sys
import textwrap
from typing import Optional

from .kb_engine import CardiologyKB


def _print_rec(rec: dict, idx: int) -> None:
    cls = rec.get("class", "?")
    loe = rec.get("level_of_evidence", "?")
    score = rec.get("score", "")
    score_str = f"  [score={score}]" if score else ""
    org = rec.get("org", "").upper()
    topic = rec.get("topic", "")
    print(f"\n  {idx}. [{org}/{topic}] Class {cls}, LOE {loe}{score_str}")
    text = rec.get("text", "")
    for line in textwrap.wrap(text, width=90, initial_indent="     ", subsequent_indent="     "):
        print(line)
    if rec.get("drugs"):
        print(f"     Drugs: {', '.join(rec['drugs'])}")
    if rec.get("drug_class"):
        print(f"     Drug class: {rec['drug_class']}")


def _print_article(art: dict, idx: int) -> None:
    authors = art.get("authors", [])
    author_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
    print(f"\n  {idx}. {art.get('title', 'N/A')}")
    print(f"     {author_str}")
    print(f"     {art.get('journal_abbrev', art.get('journal', ''))}  {art.get('year', '')}  PMID:{art.get('pmid', '')}")
    if art.get("doi"):
        print(f"     DOI: {art['doi']}")
    if art.get("abstract"):
        snippet = art["abstract"][:300]
        print(f"     {snippet}...")


def cmd_search(kb: CardiologyKB, args: argparse.Namespace) -> None:
    query = " ".join(args.query)
    org = args.org
    results = kb.search(query, org=org, top_k=args.n)
    print(f"\nSearch: '{query}'" + (f" [org={org}]" if org else "") + f"  — {len(results)} results\n{'='*70}")
    if not results:
        print("  No results found.")
        return
    for i, rec in enumerate(results, 1):
        _print_rec(rec, i)
    print()


def cmd_guideline(kb: CardiologyKB, args: argparse.Namespace) -> None:
    org = args.org
    topic = args.topic
    if args.summary:
        print(kb.summary(org, topic))
    else:
        g = kb.get_guideline(org, topic)
        print(json.dumps(g, indent=2))


def cmd_compare(kb: CardiologyKB, args: argparse.Namespace) -> None:
    topic = args.topic
    result = kb.compare(topic)
    print(f"\nComparison: {topic.upper()}\n{'='*70}")
    for org, data in result.items():
        if data is None:
            print(f"\n  {org.upper()}: No guideline found for '{topic}'")
            continue
        print(f"\n  {org.upper()} — {data['title']} ({data['year']})")
        print(f"  {'─'*60}")
        class_i = data.get("key_recommendations", [])
        if class_i:
            for rec in class_i:
                for line in textwrap.wrap(rec.get("text", ""), width=85, initial_indent="    • ", subsequent_indent="      "):
                    print(line)
        else:
            print("    (no Class I recommendations)")
    print()


def cmd_drug(kb: CardiologyKB, args: argparse.Namespace) -> None:
    drug = " ".join(args.drug)
    results = kb.drug_lookup(drug)
    print(f"\nDrug lookup: '{drug}'  — {len(results)} guideline mentions\n{'='*70}")
    if not results:
        print("  Not found in any loaded guideline.")
        return
    for i, hit in enumerate(results, 1):
        print(f"\n  {i}. [{hit['org']}/{hit['topic']}] {hit['guideline_title']} ({hit['year']})")
        print(f"     Class {hit['class']}, LOE {hit['level_of_evidence']}")
        for line in textwrap.wrap(hit.get("recommendation", ""), width=90,
                                   initial_indent="     ", subsequent_indent="     "):
            print(line)
    print()


def cmd_pubmed(kb: CardiologyKB, args: argparse.Namespace) -> None:
    query = " ".join(args.query)
    print(f"\nPubMed search: '{query}'  (max {args.n})\n{'='*70}")
    try:
        results = kb.pubmed_search(query, max_results=args.n)
    except Exception as exc:
        print(f"  PubMed request failed: {exc}")
        return
    if not results:
        print("  No results.")
        return
    for i, art in enumerate(results, 1):
        _print_article(art, i)
    print()


def cmd_pubmed_rct(kb: CardiologyKB, args: argparse.Namespace) -> None:
    query = " ".join(args.query)
    print(f"\nPubMed RCT search: '{query}'  (max {args.n})\n{'='*70}")
    try:
        results = kb.pubmed.search_rcts(query, max_results=args.n)
    except Exception as exc:
        print(f"  PubMed request failed: {exc}")
        return
    if not results:
        print("  No results.")
        return
    for i, art in enumerate(results, 1):
        _print_article(art, i)
    print()


def cmd_pubmed_guidelines(kb: CardiologyKB, args: argparse.Namespace) -> None:
    topic = " ".join(args.topic)
    org = args.org
    print(f"\nPubMed guideline search: '{topic}'" + (f" [org={org}]" if org else "") + f"\n{'='*70}")
    try:
        results = kb.pubmed.search_guidelines(topic, org=org, max_results=args.n)
    except Exception as exc:
        print(f"  PubMed request failed: {exc}")
        return
    if not results:
        print("  No results.")
        return
    for i, art in enumerate(results, 1):
        _print_article(art, i)
    print()


def cmd_list(kb: CardiologyKB, _args: argparse.Namespace) -> None:
    listing = kb.list_guidelines()
    print(f"\nLoaded Guidelines\n{'='*50}")
    for org, topics in sorted(listing.items()):
        print(f"\n  {org.upper()}:")
        for t in sorted(topics):
            print(f"    • {t}")
    print()


def cmd_stats(kb: CardiologyKB, _args: argparse.Namespace) -> None:
    s = kb.query_engine.stats()
    print(f"\nKnowledge Base Statistics\n{'='*50}")
    print(f"  Total indexed documents : {s['total_documents']}")
    print(f"  Unique index terms      : {s['unique_terms']}")
    print("\n  Documents by organisation:")
    for org, count in sorted(s["by_org"].items()):
        print(f"    {org.upper():>5}: {count}")
    print()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cardiology_kb",
        description="Cardiology Knowledge Base — ACC/ESC Guidelines + PubMed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = p.add_subparsers(dest="command", required=True)

    # search
    sp = sub.add_parser("search", help="Free-text search across all guidelines")
    sp.add_argument("query", nargs="+", help="Search query")
    sp.add_argument("--org", choices=["acc", "esc"], help="Filter by organisation")
    sp.add_argument("--n", type=int, default=10, help="Max results")

    # guideline
    gp = sub.add_parser("guideline", help="Retrieve a specific guideline")
    gp.add_argument("org", choices=["acc", "esc"], help="Organisation")
    gp.add_argument("topic", help="Topic slug (e.g. heart_failure)")
    gp.add_argument("--summary", action="store_true", help="Print formatted summary")

    # compare
    cp = sub.add_parser("compare", help="Compare ACC vs ESC on a topic")
    cp.add_argument("topic", help="Topic slug")

    # drug
    dp = sub.add_parser("drug", help="Look up drug mentions across all guidelines")
    dp.add_argument("drug", nargs="+", help="Drug or drug class name")

    # pubmed
    pp = sub.add_parser("pubmed", help="Search PubMed")
    pp.add_argument("query", nargs="+", help="PubMed query")
    pp.add_argument("--n", type=int, default=5, help="Max results")

    # pubmed-rct
    rp = sub.add_parser("pubmed-rct", help="Search PubMed for RCTs")
    rp.add_argument("query", nargs="+", help="Topic query")
    rp.add_argument("--n", type=int, default=5, help="Max results")

    # pubmed-guidelines
    gpp = sub.add_parser("pubmed-guidelines", help="Search PubMed for published guidelines")
    gpp.add_argument("topic", nargs="+", help="Topic")
    gpp.add_argument("--org", help="Filter by org name (e.g. ESC, ACC)")
    gpp.add_argument("--n", type=int, default=5, help="Max results")

    # list
    sub.add_parser("list", help="List all loaded guidelines")

    # stats
    sub.add_parser("stats", help="Show knowledge base statistics")

    return p


def main(argv: Optional[list] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    kb = CardiologyKB()

    commands = {
        "search": cmd_search,
        "guideline": cmd_guideline,
        "compare": cmd_compare,
        "drug": cmd_drug,
        "pubmed": cmd_pubmed,
        "pubmed-rct": cmd_pubmed_rct,
        "pubmed-guidelines": cmd_pubmed_guidelines,
        "list": cmd_list,
        "stats": cmd_stats,
    }

    handler = commands.get(args.command)
    if handler:
        handler(kb, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
