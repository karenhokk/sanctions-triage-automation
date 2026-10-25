# Sanctions Triage Automation

Python demo that scores synthetic customer names against a tiny dummy watchlist, then ranks alerts for an analyst-style triage queue.

Built as a portfolio proof of concept for AML / financial crime compliance automation — not a production screening system.

It draws on work with banks and consulting firms on AML / financial crime compliance.

## Data privacy

- All CSVs in this repo are **synthetic / dummy** data. No real customers, sanctioned persons, or bank transactions are included.
- Treat real watchlists and customer data as confidential: keep them off GitHub (see `.gitignore` patterns for `*_real_*.csv`).
- Generated results land under `data/processed/` and are gitignored.

## Problem

Name screening generates many near-matches (spelling and transliteration variants). Analysts need a fast first pass that:

1. Scores similarity with simple secondary identifiers (birth year, nationality)
2. Separates higher-priority hits from weaker ones
3. Leaves a short reason code for the review trail

## What this demo does

- Preprocesses names (titles, hyphens → spaces, punctuation)
- Fuzzy name match (`fuzzywuzzy` token sort ratio) with small bonuses for birth year / nationality
- High / Medium tiers with configurable thresholds
- Writes a sorted CSV queue under `data/processed/`

## Tech

Python 3, pandas, fuzzywuzzy, python-Levenshtein, pytest

## How to run

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/sanctions_triage.py
```

Run tests:

```bash
PYTHONPATH=src pytest -q
```

### Sample output (current dummy data)

```text
=== Sanctions Triage Complete ===
Total transactions screened: 8
High-risk alerts requiring immediate review: 3
Medium-risk alerts for further review: 4

Top matches include:
- Maria Gracia Lopez → Maria Garcia Lopez (90, name + birth year)
- Mohammed Al Rasheed → Mohammed Al-Rashid (89, name + birth year)
- Zhang Wey → Zhang Wei (86, name + birth year)
```

Exact scores can shift slightly if you change thresholds or sample rows.

## Possible next steps

- Streamlit review UI (accept / escalate / false positive)
- Decision audit log
- Stronger matching (phonetics, aka lists) — still on synthetic data only
- Optional connectors to published list formats (never commit live customer data)

## Note on standards

This is an educational illustration of triage workflow ideas often discussed in AML screening programmes. It is not certified against HKMA, OFAC, or UN requirements and must not be used for real screening without a proper vendor / bank control framework.
