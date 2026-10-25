import pandas as pd

from sanctions_triage import calculate_match_score, preprocess_name, run_triage


def test_preprocess_keeps_hyphen_as_space():
    assert preprocess_name("Mohammed Al-Rashid") == "mohammed al rashid"
    assert preprocess_name("Mr. Mohammed Al-Rashid") == "mohammed al rashid"


def test_preprocess_does_not_eat_amr():
    assert preprocess_name("Amr Hassan") == "amr hassan"


def test_al_rasheed_is_high_risk():
    customer = pd.Series(
        {
            "customer_name": "Mohammed Al Rasheed",
            "birth_year": 1978,
            "nationality": "Syria",
        }
    )
    watch = pd.Series(
        {
            "sanctioned_name": "Mohammed Al-Rashid",
            "birth_year": 1978,
            "nationality": "Syria",
        }
    )
    score, reason = calculate_match_score(customer, watch)
    assert score >= 85
    assert "birth year" in reason.lower()


def test_run_triage_flags_showcase_cases():
    watchlist = pd.read_csv("data/raw/dummy_sanctions_watchlist.csv")
    customers = pd.read_csv("data/raw/dummy_customer_transactions.csv")
    out = run_triage(watchlist, customers)
    names = set(out["customer_name"])
    assert "Mohammed Al Rasheed" in names
    assert "Maria Gracia Lopez" in names
