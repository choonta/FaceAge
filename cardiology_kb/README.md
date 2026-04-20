# Cardiology Knowledge Base

A structured, searchable knowledge base centred on **ACC/AHA** and **ESC** clinical practice guidelines, with integrated **PubMed** search.

## Contents

### ACC Guidelines (7 topics)
| Topic | Guideline | Year |
|-------|-----------|------|
| `heart_failure` | 2022 AHA/ACC/HFSA Heart Failure Guideline | 2022 |
| `atrial_fibrillation` | 2023 ACC/AHA/ACCP/HRS AF Guideline | 2023 |
| `hypertension` | 2017 ACC/AHA High Blood Pressure Guideline | 2017 |
| `acute_coronary_syndromes` | 2021 ACC/AHA/SCAI Coronary Revascularisation + ACS | 2022 |
| `lipid_management` | 2018 ACC/AHA Blood Cholesterol Guideline | 2018 |
| `valvular_disease` | 2021 ACC/AHA Valvular Heart Disease Guideline | 2021 |
| `chest_pain` | 2021 ACC/AHA Chest Pain Evaluation Guideline | 2021 |

### ESC Guidelines (7 topics)
| Topic | Guideline | Year |
|-------|-----------|------|
| `heart_failure` | 2021 ESC Heart Failure Guidelines | 2021 |
| `atrial_fibrillation` | 2020 ESC AF Guidelines | 2020 |
| `hypertension` | 2018 ESC/ESH Arterial Hypertension Guidelines | 2018 |
| `acute_coronary_syndromes` | 2023 ESC ACS Guidelines | 2023 |
| `dyslipidaemias` | 2019 ESC/EAS Dyslipidaemias Guidelines | 2019 |
| `valvular_disease` | 2021 ESC/EACTS Valvular Heart Disease Guidelines | 2021 |
| `cardiovascular_prevention` | 2021 ESC CV Prevention Guidelines | 2021 |

Each guideline JSON file includes:
- **Definitions** of key terms and classifications
- **Recommendations** with Class (I/IIa/IIb/III) and Level of Evidence (A/B/C)
- **Pharmacotherapy** table with doses and indications
- **Key trials** with PMID references

---

## Quick Start

```python
from cardiology_kb import CardiologyKB

kb = CardiologyKB()

# Free-text search across all guidelines
results = kb.search("SGLT2 inhibitor heart failure")
for r in results:
    print(f"[{r['org'].upper()}/{r['topic']}] Class {r['class']}: {r['text'][:100]}")

# Retrieve a specific guideline
hf_acc = kb.get_guideline("acc", "heart_failure")

# Get only Class I recommendations
class_i = kb.get_recommendations("esc", "atrial_fibrillation", rec_class="I")

# Side-by-side ACC vs ESC comparison
comparison = kb.compare("heart_failure")

# Drug/drug-class lookup
ticagrelor_mentions = kb.drug_lookup("ticagrelor")

# Human-readable summary
print(kb.summary("acc", "heart_failure"))

# PubMed search
articles = kb.pubmed_search("empagliflozin heart failure", max_results=5)
for a in articles:
    print(f"{a['title']} ({a['year']}) PMID:{a['pmid']}")

# PubMed — RCTs only
rcts = kb.pubmed.search_rcts("catheter ablation atrial fibrillation", max_results=5)

# PubMed — guidelines only
guidelines = kb.pubmed.search_guidelines("heart failure", org="ESC", max_results=5)
```

---

## Command-Line Interface

```bash
# Search guidelines
python -m cardiology_kb search "SGLT2 inhibitor heart failure"
python -m cardiology_kb search "ticagrelor ACS" --org acc --n 5

# Retrieve a guideline (JSON or formatted summary)
python -m cardiology_kb guideline acc heart_failure --summary
python -m cardiology_kb guideline esc atrial_fibrillation

# Compare ACC vs ESC on a topic
python -m cardiology_kb compare heart_failure
python -m cardiology_kb compare hypertension

# Drug lookup across all guidelines
python -m cardiology_kb drug "sacubitril valsartan"
python -m cardiology_kb drug "PCSK9 inhibitor"

# PubMed search
python -m cardiology_kb pubmed "empagliflozin heart failure" --n 5
python -m cardiology_kb pubmed-rct "catheter ablation atrial fibrillation" --n 5
python -m cardiology_kb pubmed-guidelines "heart failure" --org ESC --n 5

# List all loaded guidelines
python -m cardiology_kb list

# Show KB statistics
python -m cardiology_kb stats
```

---

## Architecture

```
cardiology_kb/
├── __init__.py           # Package entry point; exports CardiologyKB
├── kb_engine.py          # Core engine: load, search, compare, drug lookup, summary
├── pubmed_client.py      # PubMed E-utilities client (stdlib urllib, no extra deps)
├── cli.py / __main__.py  # CLI
├── search/
│   └── query_engine.py   # TF-IDF inverted index over guideline text
└── guidelines/
    ├── acc/              # 7 ACC/AHA JSON guideline files
    └── esc/              # 7 ESC JSON guideline files
```

### Dependencies
- **Zero external dependencies** — uses Python stdlib only (`urllib`, `xml`, `json`, `math`)
- Optional: `requests` (faster HTTP), `rich` (prettier terminal output)
- Python ≥ 3.10 (uses `list[str]` type hints in function signatures)

---

## PubMed Integration

The `PubMedClient` queries NCBI E-utilities directly:

| Method | Description |
|--------|-------------|
| `search(query, max_results)` | General PubMed search |
| `search_rcts(topic)` | Filter by RCT publication type |
| `search_meta_analyses(topic)` | Filter by meta-analysis/systematic review |
| `search_guidelines(topic, org)` | Filter by guideline publication type |
| `fetch(pmid)` | Fetch single article by PMID |
| `get_related(pmid)` | Find related articles |
| `format_citation(article)` | Vancouver-style citation |

Rate-limited to 3 requests/second (NCBI default). Provide `api_key` to increase to 10/second.

```python
kb = CardiologyKB(pubmed_email="your@email.com")
# With NCBI API key (free at https://www.ncbi.nlm.nih.gov/account/):
kb.pubmed.api_key = "YOUR_API_KEY"
```

Pre-built queries available in `cardiology_kb.pubmed_client.CARDIOLOGY_QUERIES`:
- `"heart_failure"`, `"atrial_fibrillation"`, `"hypertension"`, `"acute_mi"`
- `"lipids"`, `"valvular_disease"`, `"cardiac_prevention"`
- `"sglt2_heart_failure"`, `"pcsk9_inhibitors"`, `"catheter_ablation_af"`
- `"faceage_prognostication"`, `"cardiac_biomarkers"`

---

## JSON Schema

Each guideline JSON file follows this schema:

```json
{
  "title": "Full guideline title",
  "organization": "ACC/AHA",
  "year": 2022,
  "doi": "10.xxxx/...",
  "pmid": "PMID number",
  "topic": "slug",
  "definitions": { "Term": "Definition" },
  "recommendations": [
    {
      "id": "ACC-HF-001",
      "text": "Recommendation text...",
      "class": "I",
      "level_of_evidence": "A",
      "category": "pharmacotherapy",
      "drugs": ["drug1", "drug2"],
      "drug_class": "Beta-blocker"
    }
  ],
  "pharmacotherapy": [
    {
      "drug_class": "SGLT2 Inhibitor",
      "examples": "dapagliflozin 10 mg, empagliflozin 10 mg",
      "recommendation_class": "I",
      "level_of_evidence": "A",
      "indication": "HFrEF and HFpEF"
    }
  ],
  "key_trials": [
    {
      "name": "DAPA-HF",
      "drug": "dapagliflozin",
      "finding": "26% RRR in worsening HF or CV death",
      "pmid": "31535829"
    }
  ]
}
```

---

## Clinical Context

This knowledge base was developed as part of the **FaceAge** project, which estimates biological age from facial photographs for clinical prognostication. Cardiology is a key application domain given the strong relationship between cardiovascular biological age and outcomes.

The knowledge base enables:
- Rapid retrieval of evidence-based treatment recommendations
- Cross-guideline comparison (ACC vs ESC) for clinical decision support
- Integration with PubMed for up-to-date literature review
- Drug-class lookup for medication reconciliation
