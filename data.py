import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

EMPTY_COLUMNS = [
    "constituency",
    "province",
    "district",
    "candidate",
    "party",
    "votes",
    "runner_up",
    "runner_up_party",
    "runner_up_votes",
    "margin",
    "status",
    "count_pct",
]


def _validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    out = df.copy()

    for col in EMPTY_COLUMNS:
        if col not in out.columns:
            out[col] = "" if col not in ["votes", "runner_up_votes", "margin", "count_pct"] else 0

    out["votes"] = pd.to_numeric(out["votes"], errors="coerce").fillna(0).astype(int)
    out["runner_up_votes"] = pd.to_numeric(out["runner_up_votes"], errors="coerce").fillna(0).astype(int)
    out["margin"] = pd.to_numeric(out["margin"], errors="coerce").fillna(0).astype(int)
    out["count_pct"] = pd.to_numeric(out["count_pct"], errors="coerce").fillna(0.0)

    for col in ["constituency", "province", "district", "candidate", "party", "runner_up", "runner_up_party", "status"]:
        out[col] = out[col].fillna("").astype(str)

    return out[EMPTY_COLUMNS].copy()


@st.cache_data(ttl=20)
def load_election_data():
    candidates = [
        Path("data/election_data.json"),
        Path("election_data.json"),
    ]

    for path in candidates:
        if path.exists():
            df = pd.read_json(path)
            return _validate_schema(df)

    return pd.DataFrame(columns=EMPTY_COLUMNS)


@st.cache_data(ttl=20)
def load_fetch_status():
    candidates = [
        Path("data/fetch_status.json"),
        Path("fetch_status.json"),
    ]

    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

    return {
        "last_attempt_utc": datetime.now(timezone.utc).isoformat(),
        "success": False,
        "row_count": 0,
        "source_url": None,
        "error": "fetch_status.json not found",
    }
