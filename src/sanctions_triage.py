"""Sanctions name-screening triage demo using synthetic data only."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
from fuzzywuzzy import fuzz

# --------------------------
# CONFIG (adjust for your workflow)
# --------------------------
HIGH_RISK_THRESHOLD = 85  # Score >= 85 = urgent triage
MEDIUM_RISK_THRESHOLD = 70  # Score 70-84 = review
NAME_MATCH_WEIGHT = 80
BIRTHYEAR_BONUS = 10
NATIONALITY_BONUS = 5

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST_PATH = ROOT / "data" / "raw" / "dummy_sanctions_watchlist.csv"
CUSTOMERS_PATH = ROOT / "data" / "raw" / "dummy_customer_transactions.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "sanctions_triage_results.csv"

_TITLE_RE = re.compile(
    r"\b(mr|mrs|ms|dr|miss|mx)\b\.?",
    flags=re.IGNORECASE,
)


def preprocess_name(name: str) -> str:
    """Normalize names for fuzzy matching: titles, hyphens, punctuation."""
    name = name.lower().replace("-", " ")
    name = _TITLE_RE.sub(" ", name)
    name = "".join(c if c.isalpha() or c == " " else " " for c in name)
    return " ".join(name.split())


def calculate_match_score(
    customer: pd.Series, watchlist_entry: pd.Series
) -> tuple[int, str]:
    """Multi-factor match score: fuzzy name + birth year + nationality."""
    name_score = fuzz.token_sort_ratio(
        preprocess_name(customer["customer_name"]),
        preprocess_name(watchlist_entry["sanctioned_name"]),
    )

    total_score = name_score * NAME_MATCH_WEIGHT / 100
    birth_match = customer["birth_year"] == watchlist_entry["birth_year"]
    nationality_match = (
        str(customer["nationality"]).lower()
        == str(watchlist_entry["nationality"]).lower()
    )
    if birth_match:
        total_score += BIRTHYEAR_BONUS
    if nationality_match:
        total_score += NATIONALITY_BONUS
    total_score = min(int(round(total_score)), 100)

    if total_score >= HIGH_RISK_THRESHOLD:
        if birth_match:
            reason = "High risk: name + birth year match"
        else:
            reason = "High risk: near-exact name match"
    elif total_score >= MEDIUM_RISK_THRESHOLD:
        reason = "Medium risk: fuzzy name match (possible transliteration variation)"
    else:
        reason = "Low risk: likely false positive"

    return total_score, reason


def run_triage(
    watchlist: pd.DataFrame, customers: pd.DataFrame
) -> pd.DataFrame:
    """Screen each customer against the watchlist; keep medium+ hits."""
    triage_results: list[dict] = []

    for _, customer in customers.iterrows():
        best_match_score = 0
        best_match_watchlist = None
        best_reason = ""

        for _, watchlist_entry in watchlist.iterrows():
            score, reason = calculate_match_score(customer, watchlist_entry)
            if score > best_match_score:
                best_match_score = score
                best_match_watchlist = watchlist_entry
                best_reason = reason

        if best_match_score >= MEDIUM_RISK_THRESHOLD and best_match_watchlist is not None:
            triage_results.append(
                {
                    "triage_date": datetime.now().date(),
                    "customer_id": customer["customer_id"],
                    "customer_name": customer["customer_name"],
                    "transaction_id": customer["transaction_id"],
                    "amount_hkd": customer["amount_hkd"],
                    "matched_watchlist_id": best_match_watchlist["watchlist_id"],
                    "matched_sanctioned_name": best_match_watchlist["sanctioned_name"],
                    "match_score": best_match_score,
                    "risk_level": (
                        "High"
                        if best_match_score >= HIGH_RISK_THRESHOLD
                        else "Medium"
                    ),
                    "triage_reason": best_reason,
                }
            )

    if not triage_results:
        return pd.DataFrame(
            columns=[
                "triage_date",
                "customer_id",
                "customer_name",
                "transaction_id",
                "amount_hkd",
                "matched_watchlist_id",
                "matched_sanctioned_name",
                "match_score",
                "risk_level",
                "triage_reason",
            ]
        )

    return pd.DataFrame(triage_results).sort_values(
        by="match_score", ascending=False
    ).reset_index(drop=True)


def main() -> None:
    try:
        watchlist = pd.read_csv(WATCHLIST_PATH)
        customers = pd.read_csv(
            CUSTOMERS_PATH, parse_dates=["transaction_date"]
        )
    except FileNotFoundError as exc:
        print(f"Error: Missing data file - {exc}")
        return

    triage_df = run_triage(watchlist, customers)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    triage_df.to_csv(OUTPUT_PATH, index=False)

    high = int((triage_df["risk_level"] == "High").sum()) if len(triage_df) else 0
    medium = int((triage_df["risk_level"] == "Medium").sum()) if len(triage_df) else 0

    print("=== Sanctions Triage Complete ===")
    print(f"Total transactions screened: {len(customers)}")
    print(f"High-risk alerts requiring immediate review: {high}")
    print(f"Medium-risk alerts for further review: {medium}")
    print(f"Results written to: {OUTPUT_PATH}")
    if len(triage_df):
        print("\nTop matches:")
        print(
            triage_df.head(5)[
                [
                    "customer_name",
                    "matched_sanctioned_name",
                    "match_score",
                    "triage_reason",
                ]
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
