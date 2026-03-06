import json
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from streamlit_autorefresh import st_autorefresh


st.set_page_config(
    page_title="Nepal Election Intelligence Dashboard 2026",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

NEPALVOTES_URL = "https://pub-4173e04d0b78426caa8cfa525f827daa.r2.dev/constituencies.json"
TOTAL_HOUSE_SEATS = 275
FPTP_SEATS = 165
PR_SEATS = 110
MAJORITY_NEEDED = 138

PARTY_COLOR_MAP = {
    "Rastriya Swatantra Party": "#38bdf8",
    "Nepali Congress": "#2563eb",
    "CPN-UML": "#f59e0b",
    "Maoist Centre": "#ef4444",
    "Rastriya Prajatantra Party": "#a855f7",
    "Janata Samajbadi Party": "#22c55e",
    "Janamat Party": "#eab308",
    "Nagarik Unmukti Party": "#f97316",
    "Independent": "#94a3b8",
}

PARTY_NAME_NORMALIZATION = {
    "CPN UML": "CPN-UML",
    "CPN (UML)": "CPN-UML",
    "NC": "Nepali Congress",
    "Nepali Congress Party": "Nepali Congress",
    "RSP": "Rastriya Swatantra Party",
    "RPP": "Rastriya Prajatantra Party",
    "JSP": "Janata Samajbadi Party",
    "Maoist": "Maoist Centre",
}

PARTY_ICONS = {
    "Rastriya Swatantra Party": "🔔",
    "Nepali Congress": "🌳",
    "CPN-UML": "☀️",
    "Maoist Centre": "⚒️",
    "Rastriya Prajatantra Party": "👑",
    "Janata Samajbadi Party": "🟢",
    "Janamat Party": "🟡",
    "Nagarik Unmukti Party": "🟠",
    "Independent": "👤",
}


def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #07111f;
            --panel: rgba(15, 23, 42, 0.68);
            --panel-2: rgba(17, 24, 39, 0.78);
            --border: rgba(255,255,255,0.08);
            --text: #f8fafc;
            --muted: #94a3b8;
            --cyan: #38bdf8;
            --green: #22c55e;
            --amber: #f59e0b;
            --red: #ef4444;
            --purple: #a855f7;
        }

        .stApp {
            background:
                radial-gradient(circle at 20% 20%, rgba(56,189,248,0.10), transparent 30%),
                radial-gradient(circle at 80% 10%, rgba(168,85,247,0.10), transparent 25%),
                radial-gradient(circle at 50% 100%, rgba(34,197,94,0.08), transparent 30%),
                linear-gradient(180deg, #06101d 0%, #0b1220 100%);
            color: var(--text);
        }

        [data-testid="stSidebar"] {
            background: rgba(8, 15, 28, 0.95);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }

        .block-container {
            max-width: 1400px;
            padding-top: 0.8rem;
            padding-bottom: 2rem;
        }

        .topnav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 0.85rem;
            padding: 0.25rem 0.2rem 0.1rem 0.2rem;
            animation: fadeUp .6s ease-out;
        }

        .brand {
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: 0.01em;
            color: #ffffff;
        }

        .nav-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .nav-pill {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.08);
            color: #dbeafe;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            font-size: 0.82rem;
            transition: transform .18s ease, border-color .18s ease, background .18s ease;
        }

        .nav-pill:hover {
            transform: translateY(-1px);
            border-color: rgba(56,189,248,0.35);
            background: rgba(56,189,248,0.08);
        }

        .hero-shell {
            background: linear-gradient(135deg, rgba(11,18,32,0.70), rgba(30,41,59,0.76));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 26px;
            padding: 1.2rem 1.2rem 1rem 1.2rem;
            margin-bottom: 1rem;
            box-shadow: 0 14px 60px rgba(0,0,0,0.28);
            animation: fadeUp .7s ease-out;
        }

        .live-row {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 0.6rem;
        }

        .live-badge {
            background: linear-gradient(90deg, #dc2626, #ef4444);
            color: white;
            font-weight: 800;
            font-size: 0.75rem;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            box-shadow: 0 0 18px rgba(239,68,68,0.28);
        }

        .updated-badge, .soft-pill {
            background: rgba(255,255,255,0.08);
            color: #e2e8f0;
            font-size: 0.8rem;
            padding: 0.28rem 0.58rem;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.07);
        }

        .hero-title {
            font-size: 2.05rem;
            font-weight: 900;
            color: #ffffff;
            margin: 0.15rem 0;
            line-height: 1.1;
        }

        .hero-subtitle {
            color: #dbeafe;
            font-size: 0.98rem;
            margin-bottom: 0.9rem;
        }

        .hero-stats {
            display: grid;
            grid-template-columns: repeat(4, minmax(120px, 1fr));
            gap: 10px;
        }

        .hero-stat, .glass-tile {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 0.8rem 0.9rem;
            transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
        }

        .hero-stat:hover, .glass-tile:hover, .glass-card:hover, .story-card:hover, .clash-card:hover {
            transform: translateY(-2px);
            border-color: rgba(56,189,248,0.28);
            box-shadow: 0 10px 26px rgba(2, 8, 23, 0.22);
        }

        .hero-stat .label {
            font-size: 0.77rem;
            color: #a5b4fc;
        }

        .hero-stat .value {
            font-size: 1.28rem;
            font-weight: 900;
            color: #ffffff;
            line-height: 1.15;
        }

        .glass-card {
            background: rgba(15, 23, 42, 0.68);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 1rem;
            margin-bottom: 1rem;
            animation: fadeUp .5s ease-out;
            transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
        }

        .story-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.78), rgba(15,23,42,0.88));
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 1rem;
            min-height: 220px;
            margin-bottom: 1rem;
            animation: fadeUp .6s ease-out;
            transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
        }

        .section-title {
            color: #f8fafc;
            font-size: 1.04rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .section-subtle {
            color: #94a3b8;
            font-size: 0.86rem;
            margin-bottom: 0.75rem;
        }

        .majority-shell {
            background: linear-gradient(135deg, rgba(8,15,28,0.72), rgba(17,24,39,0.80));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 1rem 1rem 1.1rem 1rem;
            margin-bottom: 1rem;
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            animation: fadeUp .55s ease-out;
        }

        .bar-label {
            color: #cbd5e1;
            font-size: 0.82rem;
            margin-bottom: 0.35rem;
        }

        .track {
            height: 16px;
            width: 100%;
            background: rgba(255,255,255,0.08);
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 0.8rem;
            position: relative;
        }

        .fill-cyan, .fill-green, .fill-amber {
            height: 100%;
            border-radius: 999px;
            animation: growBar 1s ease-out;
        }

        .fill-cyan {
            background: linear-gradient(90deg, #22d3ee, #38bdf8);
        }

        .fill-green {
            background: linear-gradient(90deg, #4ade80, #22c55e);
        }

        .fill-amber {
            background: linear-gradient(90deg, #fbbf24, #f59e0b);
        }

        .coalition-pill {
            display: inline-block;
            padding: 0.38rem 0.72rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 700;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
            background: rgba(255,255,255,0.07);
            color: #e2e8f0;
            border: 1px solid rgba(255,255,255,0.06);
        }

        .status-good {
            background: rgba(34,197,94,0.14);
            color: #86efac;
            border: 1px solid rgba(34,197,94,0.22);
        }

        .status-warn {
            background: rgba(251,191,36,0.12);
            color: #fde68a;
            border: 1px solid rgba(251,191,36,0.22);
        }

        .status-bad {
            background: rgba(239,68,68,0.12);
            color: #fca5a5;
            border: 1px solid rgba(239,68,68,0.22);
        }

        .clash-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 0.8rem 0.85rem;
            margin-bottom: 0.7rem;
            transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
        }

        .candidate-line {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin: 0.38rem 0;
            color: #e5e7eb;
            font-size: 0.9rem;
        }

        .small-note {
            color: #94a3b8;
            font-size: 0.82rem;
        }

        .tiny-head {
            color: #93c5fd;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: .05em;
            font-weight: 700;
        }

        .headline-value {
            font-size: 2.05rem;
            font-weight: 900;
            color: #ffffff;
            line-height: 1.05;
            margin: 0.1rem 0 0.2rem 0;
        }

        .party-chip {
            display: inline-block;
            padding: 0.22rem 0.56rem;
            border-radius: 999px;
            font-size: 0.78rem;
            color: white;
            margin-right: 0.35rem;
            margin-bottom: 0.3rem;
            font-weight: 700;
            border: 1px solid rgba(255,255,255,0.08);
        }

        .update-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
            margin-bottom: 0.55rem;
        }

        div[data-testid="metric-container"] {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 16px;
            padding: 12px 12px;
            box-shadow: none;
        }

        div[data-testid="metric-container"] label {
            color: #94a3b8 !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        [data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
        }

        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0px);
            }
        }

        @keyframes growBar {
            from { width: 0%; }
        }

        @media (max-width: 980px) {
            .hero-title {
                font-size: 1.55rem;
            }
            .hero-stats {
                grid-template-columns: repeat(2, minmax(120px, 1fr));
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def make_session():
    session = requests.Session()
    retry = Retry(
        total=4,
        connect=4,
        read=4,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json,text/plain,*/*",
        }
    )
    return session


def normalize_party_name(value):
    text = str(value or "").strip()
    if not text:
        return "Independent"
    return PARTY_NAME_NORMALIZATION.get(text, text)


def get_party_icon(party):
    return PARTY_ICONS.get(normalize_party_name(party), "•")


def party_color(party):
    return PARTY_COLOR_MAP.get(normalize_party_name(party), "#64748b")


def party_chip_html(party):
    party = normalize_party_name(party)
    return f'<span class="party-chip" style="background:{party_color(party)};">{get_party_icon(party)} {party}</span>'


def validate_final_schema(df):
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

    out["party"] = out["party"].apply(normalize_party_name)
    out["runner_up_party"] = out["runner_up_party"].apply(normalize_party_name)

    return out[EMPTY_COLUMNS].copy()


def normalize_nepalvotes_results(items):
    if not items or not isinstance(items, list):
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    rows = []

    for seat in items:
        candidates = seat.get("candidates", [])
        if not isinstance(candidates, list) or len(candidates) == 0:
            continue

        cleaned = []
        for c in candidates:
            cleaned.append(
                {
                    "candidate": str(c.get("name") or c.get("nameEn") or c.get("nameNp") or "").strip(),
                    "party": normalize_party_name(c.get("partyName") or c.get("party") or c.get("partyId") or "Independent"),
                    "votes": int(pd.to_numeric(c.get("votes", 0), errors="coerce") or 0),
                    "isWinner": bool(c.get("isWinner", False)),
                }
            )

        cleaned = sorted(cleaned, key=lambda x: x["votes"], reverse=True)
        top = cleaned[0]
        runner = cleaned[1] if len(cleaned) > 1 else {
            "candidate": "",
            "party": "Independent",
            "votes": 0,
            "isWinner": False,
        }

        votes_cast = pd.to_numeric(seat.get("votesCast", 0), errors="coerce")
        total_voters = pd.to_numeric(seat.get("totalVoters", 0), errors="coerce")
        count_pct = 0.0
        if pd.notna(votes_cast) and pd.notna(total_voters) and float(total_voters) > 0:
            count_pct = round((float(votes_cast) / float(total_voters)) * 100, 1)

        status_raw = str(seat.get("status") or "").strip().upper()
        final_status = "Won" if top["isWinner"] or status_raw in ["DECLARED", "ELECTED", "WON", "FINAL"] else "Counting"

        constituency = str(seat.get("name") or seat.get("code") or "").strip()
        province = str(seat.get("province") or "Unknown").strip()
        district = str(seat.get("district") or "Unknown").strip()

        if not constituency:
            continue

        rows.append(
            {
                "constituency": constituency,
                "province": province,
                "district": district,
                "candidate": top["candidate"] if top["candidate"] else "Unknown Candidate",
                "party": top["party"],
                "votes": top["votes"],
                "runner_up": runner["candidate"],
                "runner_up_party": runner["party"],
                "runner_up_votes": runner["votes"],
                "margin": top["votes"] - runner["votes"],
                "status": final_status,
                "count_pct": count_pct,
            }
        )

    if not rows:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    return validate_final_schema(
        pd.DataFrame(rows).sort_values(["province", "district", "constituency"]).reset_index(drop=True)
    )


def load_local_repo_json():
    path = Path("data/election_data.json")
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list) and len(data) > 0:
        return validate_final_schema(pd.DataFrame(data))
    return None


def load_github_raw_json():
    url = "https://raw.githubusercontent.com/shashankadhungana/nepal-election-2026/main/data/election_data.json"
    session = make_session()
    r = session.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and len(data) > 0:
        return validate_final_schema(pd.DataFrame(data))
    return None


def load_nepalvotes_json():
    session = make_session()
    r = session.get(
        NEPALVOTES_URL,
        headers={
            "Origin": "https://nepalvotes.live",
            "Referer": "https://nepalvotes.live/",
            "Accept": "application/json,text/plain,*/*",
            "User-Agent": "Mozilla/5.0",
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return normalize_nepalvotes_results(data)


@st.cache_data(ttl=25)
def load_fetch_status():
    path = Path("data/fetch_status.json")
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


@st.cache_data(ttl=25)
def load_election_data():
    source_errors = {}

    loaders = [
        ("NepalVotes live JSON", load_nepalvotes_json),
        ("Local backup JSON", load_local_repo_json),
        ("GitHub raw backup JSON", load_github_raw_json),
    ]

    for source_name, loader in loaders:
        try:
            df = loader()
            if df is not None and not df.empty:
                return {"data": df, "source": source_name, "errors": source_errors}
        except Exception as e:
            source_errors[source_name] = str(e)

    return {"data": pd.DataFrame(columns=EMPTY_COLUMNS), "source": None, "errors": source_errors}


def chart_layout(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.35)",
        font=dict(color="#e5e7eb"),
        margin=dict(l=18, r=18, t=40, b=18),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        transition={"duration": 450, "easing": "cubic-in-out"},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)")
    return fig


def format_last_updated(fetch_status):
    if not fetch_status:
        return "Unknown"
    raw = fetch_status.get("last_attempt_utc")
    if not raw:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        return dt.strftime("%I:%M %p UTC")
    except Exception:
        return str(raw)


def top_nav():
    st.markdown(
        """
        <div class="topnav">
            <div class="brand">Nepal Election Intelligence Dashboard</div>
            <div class="nav-links">
                <span class="nav-pill">Majority Tracker</span>
                <span class="nav-pill">Coalition Builder</span>
                <span class="nav-pill">Mega Clashes</span>
                <span class="nav-pill">Province Speed</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_banner(source_text, updated_text, constituencies_count, provinces_count, parties_count):
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="live-row">
                <span class="live-badge">LIVE</span>
                <span class="updated-badge">Last refresh {updated_text}</span>
                <span class="soft-pill">House size {TOTAL_HOUSE_SEATS}</span>
                <span class="soft-pill">Majority line {MAJORITY_NEEDED}</span>
            </div>
            <div class="hero-title">Hung Parliament Tracker</div>
            <div class="hero-subtitle">Real-time constituency tracking, coalition math, provincial counting speed, and high-attention races.</div>
            <div class="hero-stats">
                <div class="hero-stat"><div class="label">Visible constituencies</div><div class="value">{constituencies_count}</div></div>
                <div class="hero-stat"><div class="label">Visible provinces</div><div class="value">{provinces_count}</div></div>
                <div class="hero-stat"><div class="label">Visible parties</div><div class="value">{parties_count}</div></div>
                <div class="hero-stat"><div class="label">Data source</div><div class="value" style="font-size:0.96rem;">{source_text}</div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_title(text, subtle=None):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
    if subtle:
        st.markdown(f'<div class="section-subtle">{subtle}</div>', unsafe_allow_html=True)


def build_party_blocks(df):
    if df.empty:
        return pd.DataFrame(columns=["party", "leads", "won", "votes"])
    return (
        df.groupby("party", as_index=False)
        .agg(
            leads=("party", "size"),
            won=("status", lambda x: int((x == "Won").sum())),
            votes=("votes", "sum"),
        )
        .sort_values(["won", "leads", "votes"], ascending=False)
        .reset_index(drop=True)
    )


def majority_tracker_html(top_party, top_leads, top_won):
    lead_pct = min((top_leads / MAJORITY_NEEDED) * 100, 100)
    won_pct = min((top_won / MAJORITY_NEEDED) * 100, 100)
    gap = max(MAJORITY_NEEDED - top_leads, 0)

    return f"""
    <div class="majority-shell">
        <div class="section-title">Majority Tracker</div>
        <div class="section-subtle">The dashboard centers on the 138-seat threshold needed to control the 275-member House.</div>

        <div style="display:grid;grid-template-columns:1.35fr 0.85fr;gap:14px;align-items:center;">
            <div>
                <div class="bar-label">Largest visible bloc: {get_party_icon(top_party)} {top_party}</div>
                <div class="track"><div class="fill-cyan" style="width:{lead_pct}%;"></div></div>

                <div class="bar-label">Declared wins for the largest bloc</div>
                <div class="track"><div class="fill-green" style="width:{won_pct}%;"></div></div>

                <div class="small-note">Current leads are based on visible constituency leaders, while declared wins count only rows marked Won.</div>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                <div class="hero-stat"><div class="label">Largest bloc</div><div class="value">{top_leads}</div></div>
                <div class="hero-stat"><div class="label">Declared wins</div><div class="value">{top_won}</div></div>
                <div class="hero-stat"><div class="label">Gap to 138</div><div class="value">{gap}</div></div>
                <div class="hero-stat"><div class="label">Majority line</div><div class="value">{MAJORITY_NEEDED}</div></div>
            </div>
        </div>
    </div>
    """


def coalition_summary(df, selected_parties):
    if df.empty or not selected_parties:
        return {
            "fptp_leads": 0,
            "won_seats": 0,
            "projected_pr": 0,
            "total_projected": 0,
            "gap": MAJORITY_NEEDED,
            "vote_share": 0.0,
        }

    coalition_df = df[df["party"].isin(selected_parties)].copy()
    fptp_leads = len(coalition_df)
    won_seats = int((coalition_df["status"] == "Won").sum())

    vote_by_party = df.groupby("party")["votes"].sum()
    total_votes_all = vote_by_party.sum()

    selected_votes = vote_by_party[vote_by_party.index.isin(selected_parties)].sum()
    vote_share = (selected_votes / total_votes_all) if total_votes_all > 0 else 0.0

    projected_pr = int(round(vote_share * PR_SEATS))
    total_projected = fptp_leads + projected_pr
    gap = max(MAJORITY_NEEDED - total_projected, 0)

    return {
        "fptp_leads": int(fptp_leads),
        "won_seats": int(won_seats),
        "projected_pr": int(projected_pr),
        "total_projected": int(total_projected),
        "gap": int(gap),
        "vote_share": round(vote_share * 100, 1),
    }


def province_speed_table(df):
    if df.empty:
        return pd.DataFrame(columns=["Province", "Avg count %", "Visible seats", "Speed"])

    out = (
        df.groupby("province", as_index=False)
        .agg(
            visible_seats=("constituency", "count"),
            avg_count_pct=("count_pct", "mean"),
        )
        .sort_values("avg_count_pct", ascending=False)
    )

    def speed_label(x):
        if x >= 40:
            return "High"
        if x >= 20:
            return "Medium"
        return "Low"

    out["Speed"] = out["avg_count_pct"].apply(speed_label)

    return out.rename(
        columns={
            "province": "Province",
            "avg_count_pct": "Avg count %",
            "visible_seats": "Visible seats",
        }
    )


def mega_clashes(df):
    if df.empty:
        return pd.DataFrame(columns=EMPTY_COLUMNS)
    return df.sort_values(["margin", "count_pct"], ascending=[True, False]).head(8)


def trend_arrow(margin):
    return "📉" if margin <= 1000 else "📈"


def render_empty_state(errors):
    top_nav()
    hero_banner("Source unavailable", "Unknown", 0, 0, 0)
    st.warning("The app could not load live or backup data.")
    if errors:
        st.json(errors, expanded=False)


def render_main_dashboard():
    st_autorefresh(interval=25 * 1000, key="autorefresh")

    result = load_election_data()
    df = result["data"]
    active_source = result["source"]
    source_errors = result["errors"]
    fetch_status = load_fetch_status()

    if df.empty:
        render_empty_state(source_errors)
        return

    st.sidebar.title("Control room")

    province_options = ["All"] + sorted(df["province"].dropna().unique().tolist())
    status_options = ["All"] + sorted(df["status"].dropna().unique().tolist())
    party_options = sorted(df["party"].dropna().unique().tolist())

    selected_province = st.sidebar.selectbox("Province", province_options)
    selected_status = st.sidebar.selectbox("Status", status_options)
    search_text = st.sidebar.text_input("Search seat, district, candidate")

    default_coalition = []
    for p in ["Rastriya Swatantra Party", "Nepali Congress"]:
        if p in party_options:
            default_coalition.append(p)
    if not default_coalition:
        default_coalition = party_options[:2]

    coalition_pick = st.sidebar.multiselect(
        "Coalition Builder",
        options=party_options,
        default=default_coalition,
    )

    st.sidebar.caption("Projected PR seats are modeled from visible vote share, not final PR allocation.")

    filtered_df = df.copy()

    if selected_province != "All":
        filtered_df = filtered_df[filtered_df["province"] == selected_province]

    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]

    if search_text:
        q = search_text.strip().lower()
        filtered_df = filtered_df[
            filtered_df["constituency"].str.lower().str.contains(q, na=False)
            | filtered_df["district"].str.lower().str.contains(q, na=False)
            | filtered_df["candidate"].str.lower().str.contains(q, na=False)
            | filtered_df["runner_up"].str.lower().str.contains(q, na=False)
        ]

    top_nav()
    hero_banner(
        source_text=active_source,
        updated_text=format_last_updated(fetch_status),
        constituencies_count=filtered_df["constituency"].nunique(),
        provinces_count=filtered_df["province"].nunique(),
        parties_count=filtered_df["party"].nunique(),
    )

    party_blocks = build_party_blocks(filtered_df)

    if party_blocks.empty:
        top_party = "N/A"
        top_leads = 0
        top_won = 0
    else:
        top_party = party_blocks.iloc[0]["party"]
        top_leads = int(party_blocks.iloc[0]["leads"])
        top_won = int(party_blocks.iloc[0]["won"])

    st.markdown(
        majority_tracker_html(top_party=top_party, top_leads=top_leads, top_won=top_won),
        unsafe_allow_html=True,
    )

    top_row_left, top_row_right = st.columns([1.25, 0.75])

    with top_row_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        card_title("Interactive Coalition Builder", "Live coalition testing with clearly labeled PR projection")

        coalition = coalition_summary(filtered_df, coalition_pick)
        coalition_label = " + ".join([f"{get_party_icon(p)} {p}" for p in coalition_pick]) if coalition_pick else "No coalition selected"

        if coalition["total_projected"] >= MAJORITY_NEEDED:
            status_class = "status-good"
            status_text = f"Projected to cross 138 by {coalition['total_projected'] - MAJORITY_NEEDED} seats"
        elif coalition["gap"] <= 10:
            status_class = "status-warn"
            status_text = f"{coalition['gap']} seats short of 138"
        else:
            status_class = "status-bad"
            status_text = f"{coalition['gap']} seats short of 138"

        st.markdown(f'<div class="coalition-pill">{coalition_label}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="coalition-pill {status_class}">{status_text}</div>', unsafe_allow_html=True)

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("FPTP leads", coalition["fptp_leads"])
        c2.metric("Declared wins", coalition["won_seats"])
        c3.metric("Vote share", f"{coalition['vote_share']}%")
        c4.metric("Projected PR", coalition["projected_pr"])
        c5.metric("Projected total", coalition["total_projected"])

        coalition_df = pd.DataFrame(
            [
                {"Metric": "FPTP leads", "Seats": coalition["fptp_leads"]},
                {"Metric": "Declared wins", "Seats": coalition["won_seats"]},
                {"Metric": "Projected PR seats", "Seats": coalition["projected_pr"]},
                {"Metric": "Projected total", "Seats": coalition["total_projected"]},
                {"Metric": "Majority line", "Seats": MAJORITY_NEEDED},
            ]
        )

        fig_coal = px.bar(
            coalition_df,
            x="Metric",
            y="Seats",
            text_auto=True,
            color="Metric",
            color_discrete_sequence=["#38bdf8", "#22c55e", "#f59e0b", "#a78bfa", "#ef4444"],
        )
        fig_coal = chart_layout(fig_coal)
        fig_coal.update_layout(height=350, showlegend=False)
        fig_coal.add_hline(
            y=MAJORITY_NEEDED,
            line_dash="dash",
            line_color="#fbbf24",
            annotation_text="138 majority line",
            annotation_position="top left",
        )
        st.plotly_chart(fig_coal, width="stretch")

        st.caption("Projected PR seats are estimated from visible vote share in the currently loaded data and are not a final PR allocation.")
        st.markdown("</div>", unsafe_allow_html=True)

    with top_row_right:
        st.markdown('<div class="story-card">', unsafe_allow_html=True)
        st.markdown('<div class="tiny-head">Main story</div>', unsafe_allow_html=True)
        st.markdown('<div class="headline-value">Hung Parliament Watch</div>', unsafe_allow_html=True)

        gap = max(MAJORITY_NEEDED - top_leads, 0)
        st.markdown(
            f"""
            <div class="section-subtle">
                Largest visible bloc: {get_party_icon(top_party)} {top_party}<br>
                Current leads: {top_leads}<br>
                Declared wins: {top_won}<br>
                Gap to 138: {gap}
            </div>
            """,
            unsafe_allow_html=True,
        )

        for _, row in party_blocks.head(4).iterrows():
            st.markdown(
                f"""
                <div class="update-item">
                    {get_party_icon(row['party'])} <b>{row['party']}</b><br>
                    Leads: {int(row['leads'])} · Wins: {int(row['won'])} · Visible votes: {int(row['votes']):,}
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    mid_left, mid_right = st.columns([1.15, 0.85])

    with mid_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        card_title("Mega Clashes", "Closest visible contests by margin and count progress")

        clashes = mega_clashes(filtered_df)
        if clashes.empty:
            st.info("No close races found.")
        else:
            for _, row in clashes.iterrows():
                st.markdown(
                    f"""
                    <div class="clash-card">
                        <div style="font-size:1rem;font-weight:800;color:#f8fafc;">
                            {row['constituency']} {trend_arrow(int(row['margin']))}
                        </div>
                        <div class="small-note">{row['province']} · {row['district']} · Count {row['count_pct']}%</div>
                        <div class="candidate-line">
                            <span>{get_party_icon(row['party'])} {row['candidate']} ({row['party']})</span>
                            <span>{int(row['votes']):,}</span>
                        </div>
                        <div class="candidate-line">
                            <span>{get_party_icon(row['runner_up_party'])} {row['runner_up']} ({row['runner_up_party']})</span>
                            <span>{int(row['runner_up_votes']):,}</span>
                        </div>
                        <div class="small-note">Margin: {int(row['margin']):,} · Status: {row['status']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with mid_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        card_title("Provincial Speed Gauge", "Average visible count progress by province")

        speed_df = province_speed_table(filtered_df)

        if speed_df.empty:
            st.info("No provincial speed data available.")
        else:
            fig_speed = px.bar(
                speed_df,
                x="Province",
                y="Avg count %",
                text_auto=".1f",
                color="Avg count %",
                color_continuous_scale="Blues",
            )
            fig_speed = chart_layout(fig_speed)
            fig_speed.update_layout(height=320, coloraxis_showscale=False)
            st.plotly_chart(fig_speed, width="stretch")

            st.dataframe(speed_df, width="stretch", hide_index=True, height=260)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    card_title("Party Landscape", "Current leads, declared wins, and visible vote volume")

    party_summary = (
        filtered_df.groupby("party", as_index=False)
        .agg(
            current_leads=("party", "size"),
            declared_wins=("status", lambda x: int((x == "Won").sum())),
            visible_votes=("votes", "sum"),
        )
        .sort_values(["declared_wins", "current_leads", "visible_votes"], ascending=False)
        .head(12)
    )

    fig_party = px.bar(
        party_summary,
        x="party",
        y=["current_leads", "declared_wins"],
        barmode="group",
        text_auto=True,
        color_discrete_sequence=["#38bdf8", "#22c55e"],
        labels={"party": "Party", "value": "Seats", "variable": "Metric"},
    )

    fig_party.for_each_trace(
        lambda t: t.update(
            name={"current_leads": "Current leads", "declared_wins": "Declared wins"}.get(t.name, t.name)
        )
    )

    fig_party = chart_layout(fig_party)
    fig_party.update_layout(height=360)
    st.plotly_chart(fig_party, width="stretch")

    st.dataframe(
        party_summary.rename(
            columns={
                "party": "Party",
                "current_leads": "Current leads",
                "declared_wins": "Declared wins",
                "visible_votes": "Visible votes",
            }
        ),
        width="stretch",
        hide_index=True,
        height=260,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    card_title("Constituency Results", "Searchable live table")

    table_df = filtered_df.rename(
        columns={
            "constituency": "Seat",
            "province": "Province",
            "district": "District",
            "candidate": "Leader",
            "party": "Leader party",
            "votes": "Leader votes",
            "runner_up": "Runner-up",
            "runner_up_party": "Runner-up party",
            "runner_up_votes": "Runner-up votes",
            "margin": "Margin",
            "status": "Status",
            "count_pct": "Count %",
        }
    )[
        [
            "Seat", "Province", "District", "Leader", "Leader party", "Leader votes",
            "Runner-up", "Runner-up party", "Runner-up votes", "Margin", "Status", "Count %",
        ]
    ].sort_values(["Status", "Leader votes"], ascending=[True, False])

    st.dataframe(table_df, width="stretch", hide_index=True, height=470)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_css()
    render_main_dashboard()


if __name__ == "__main__":
    main()
