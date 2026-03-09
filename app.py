from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from data import load_election_data, load_fetch_status


st.set_page_config(
    page_title="Nepal Election Intelligence Dashboard 2026",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TOTAL_HOUSE_SEATS = 275
FPTP_SEATS = 165
PR_SEATS = 110
MAJORITY_NEEDED = 138

PARTY_NAME_NORMALIZATION = {
    "CPN UML": "CPN-UML",
    "CPN (UML)": "CPN-UML",
    "NC": "Nepali Congress",
    "RSP": "Rastriya Swatantra Party",
    "RPP": "Rastriya Prajatantra Party",
    "JSP": "Janata Samajbadi Party",
    "Maoist": "Maoist Centre",
}

PARTY_COLOR_MAP = {
    "Rastriya Swatantra Party": "#4F46E5",
    "Nepali Congress": "#2563EB",
    "CPN-UML": "#F59E0B",
    "Maoist Centre": "#EF4444",
    "Rastriya Prajatantra Party": "#8B5CF6",
    "Janata Samajbadi Party": "#22C55E",
    "Janamat Party": "#EAB308",
    "Nagarik Unmukti Party": "#F97316",
    "Independent": "#64748B",
}

PARTY_SYMBOLS = {
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

FAMOUS_CANDIDATES = [
    "KP Sharma Oli",
    "Balendra Shah",
    "Balen Shah",
    "Gagan Thapa",
    "Bishnu Prasad Paudel",
    "Prakashman Singh",
    "Rabi Lamichhane",
    "Sher Bahadur Deuba",
    "Pushpa Kamal Dahal",
    "Prachanda",
    "Chandra Kanta Raut",
    "CK Raut",
    "Rajendra Lingden",
    "Swarnim Wagle",
    "Svarnima Wagle",
]


def inject_css():
    st.markdown("""
        <style>
        :root {
            --bg1: #f8fafc;
            --bg2: #eef2ff;
            --text: #0f172a;
            --muted: #64748b;
            --line: rgba(15,23,42,0.07);
            --card: rgba(255,255,255,0.72);
            --card-strong: rgba(255,255,255,0.86);
            --shadow: 0 16px 40px rgba(15,23,42,0.08);
            --radius: 24px;
        }

        .stApp {
            background:
                radial-gradient(circle at 0% 0%, rgba(79,70,229,0.10), transparent 22%),
                radial-gradient(circle at 100% 0%, rgba(56,189,248,0.10), transparent 18%),
                linear-gradient(180deg, var(--bg1) 0%, #f8fafc 50%, var(--bg2) 100%);
            color: var(--text);
        }

        [data-testid="stHeader"] {
            background: rgba(255,255,255,0);
        }

        .block-container {
            max-width: 1380px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 0.9rem;
            animation: fadeUp .45s ease-out;
        }

        .brand {
            font-size: 1.4rem;
            font-weight: 900;
            color: #0f172a;
            letter-spacing: -0.03em;
        }

        .subbrand {
            color: #64748b;
            font-size: 0.93rem;
            margin-top: 0.16rem;
        }

        .live-pills {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .pill {
            background: rgba(255,255,255,0.65);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(15,23,42,0.07);
            border-radius: 999px;
            padding: 0.42rem 0.74rem;
            font-size: 0.82rem;
            color: #334155;
            box-shadow: 0 8px 18px rgba(15,23,42,0.04);
        }

        .pill-live {
            background: linear-gradient(90deg, #ef4444, #fb7185);
            color: white;
            border: none;
            font-weight: 800;
        }

        .hero {
            background: rgba(255,255,255,0.68);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid rgba(255,255,255,0.60);
            border-radius: 28px;
            box-shadow: var(--shadow);
            padding: 1.15rem 1.2rem;
            margin-bottom: 1rem;
            animation: fadeUp .55s ease-out;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: 1.35fr 1fr;
            gap: 14px;
            align-items: center;
        }

        .hero-title {
            font-size: 2.05rem;
            font-weight: 900;
            color: #0f172a;
            line-height: 1.04;
            letter-spacing: -0.04em;
            margin-bottom: 0.35rem;
        }

        .hero-subtitle {
            color: #475569;
            font-size: 0.98rem;
            line-height: 1.5;
            max-width: 880px;
        }

        .metric-strip {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
        }

        .stat-card {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(15,23,42,0.07);
            border-radius: 20px;
            padding: 0.86rem 0.92rem;
            box-shadow: 0 10px 28px rgba(15,23,42,0.05);
            transition: transform .18s ease, box-shadow .18s ease;
        }

        .stat-card:hover, .soft-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 36px rgba(15,23,42,0.10);
        }

        .stat-label {
            color: #64748b;
            font-size: 0.76rem;
        }

        .stat-value {
            color: #0f172a;
            font-size: 1.2rem;
            font-weight: 900;
            margin-top: 0.12rem;
        }

        .soft-card {
            background: rgba(255,255,255,0.72);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(15,23,42,0.07);
            border-radius: 24px;
            box-shadow: var(--shadow);
            padding: 1rem;
            margin-bottom: 1rem;
            transition: transform .18s ease, box-shadow .18s ease;
            animation: fadeUp .5s ease-out;
        }

        .section-title {
            font-size: 1.02rem;
            font-weight: 900;
            color: #0f172a;
            margin-bottom: 0.16rem;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 0.86rem;
            margin-bottom: 0.8rem;
        }

        .majority-bar-label {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            color: #475569;
            font-size: 0.84rem;
            margin-bottom: 0.35rem;
        }

        .majority-track {
            width: 100%;
            height: 16px;
            border-radius: 999px;
            overflow: hidden;
            background: rgba(148,163,184,0.22);
            margin-bottom: 0.85rem;
        }

        .majority-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #4F46E5, #38BDF8);
            animation: growBar 1.0s ease-out;
        }

        .majority-fill-win {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #10B981, #22C55E);
            animation: growBar 1.0s ease-out;
        }

        .coalition-pill {
            display: inline-block;
            border-radius: 999px;
            padding: 0.42rem 0.72rem;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
            background: rgba(79,70,229,0.08);
            color: #4338ca;
            font-size: 0.82rem;
            font-weight: 800;
        }

        .status-good {
            background: rgba(34,197,94,0.12);
            color: #15803d;
        }

        .status-warn {
            background: rgba(249,115,22,0.12);
            color: #c2410c;
        }

        .hot-card {
            background: linear-gradient(135deg, rgba(255,247,237,0.92), rgba(255,255,255,0.82));
            border: 1px solid rgba(251,146,60,0.24);
        }

        .hot-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 0.12rem;
        }

        .fire {
            font-size: 1.2rem;
            filter: drop-shadow(0 4px 10px rgba(249,115,22,0.36));
            animation: pulseFire 1.7s ease-in-out infinite;
        }

        .clash-row, .ranking-row {
            background: rgba(255,255,255,0.66);
            border: 1px solid rgba(15,23,42,0.07);
            border-radius: 18px;
            padding: 0.78rem 0.82rem;
            margin-bottom: 0.62rem;
        }

        .clash-title {
            color: #111827;
            font-weight: 900;
            font-size: 0.98rem;
            margin-bottom: 0.12rem;
        }

        .clash-meta, .tiny-note {
            color: #64748b;
            font-size: 0.82rem;
        }

        .candidate-line {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            color: #334155;
            font-size: 0.9rem;
            margin: 0.3rem 0;
        }

        .symbol-chip {
            display: inline-block;
            padding: 0.22rem 0.52rem;
            border-radius: 999px;
            margin-right: 0.32rem;
            margin-bottom: 0.32rem;
            color: white;
            font-size: 0.76rem;
            font-weight: 800;
        }

        .rank-badge {
            display: inline-flex;
            width: 28px;
            height: 28px;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            background: linear-gradient(135deg, #4F46E5, #38BDF8);
            color: white;
            font-weight: 900;
            margin-right: 0.55rem;
            font-size: 0.8rem;
        }

        div[data-testid="metric-container"] {
            background: rgba(255,255,255,0.55);
            border: 1px solid rgba(15,23,42,0.07);
            border-radius: 18px;
            box-shadow: none;
            padding: 12px 12px;
        }

        div[data-testid="metric-container"] label {
            color: #64748b !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #0f172a;
        }

        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes growBar {
            from { width: 0; }
        }

        @keyframes pulseFire {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
        }

        @media (max-width: 980px) {
            .hero-grid { grid-template-columns: 1fr; }
            .metric-strip { grid-template-columns: repeat(2, 1fr); }
        }
        </style>
        """, unsafe_allow_html=True)

def normalize_party_name(value):
    text = str(value or "").strip()
    if not text:
        return "Independent"
    return PARTY_NAME_NORMALIZATION.get(text, text)

def party_symbol(party):
    party = normalize_party_name(party)
    return PARTY_SYMBOLS.get(party, "◆")

def format_status_time(fetch_status):
    raw = fetch_status.get("last_attempt_utc") if isinstance(fetch_status, dict) else None
    if not raw:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        return dt.strftime("%I:%M %p UTC")
    except Exception:
        return str(raw)

def clean_df(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["constituency", "province", "district", "candidate", "party", "votes", "runner_up", "runner_up_party", "runner_up_votes", "margin", "status", "count_pct"])

    out = df.copy()
    for col in ["constituency", "province", "district", "candidate", "party", "runner_up", "runner_up_party", "status"]:
        out[col] = out[col].fillna("").astype(str)

    for col in ["votes", "runner_up_votes", "margin"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["count_pct"] = pd.to_numeric(out["count_pct"], errors="coerce").fillna(0.0)

    out["party"] = out["party"].apply(normalize_party_name)
    out["runner_up_party"] = out["runner_up_party"].apply(normalize_party_name)
    out["status"] = out["status"].replace({"Counting": "Leading"}).fillna("Leading")

    return out

def topbar(fetch_status):
    updated_text = format_status_time(fetch_status)
    row_count = fetch_status.get("row_count", 0) if isinstance(fetch_status, dict) else 0

    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="brand">🇳🇵 Nepal Election Results</div>
                <div class="subbrand">Live results • Party totals • Closest races • Search any constituency</div>
            </div>
            <div class="live-pills">
                <span class="pill pill-live">LIVE</span>
                <span class="pill">Updated {updated_text}</span>
                <span class="pill">{row_count:,} races</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def hero(df):
    if df.empty:
        return

    total_races = len(df)
    won_races = len(df[df['status'] == 'Won'])
    top_party = df['party'].value_counts().index[0]
    top_count = df['party'].value_counts().iloc[0]
    gap_to_majority = max(MAJORITY_NEEDED - top_count, 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Races with results", total_races)
    with col2:
        st.metric("Seats officially won", won_races)
    with col3:
        st.metric("Leading party", f"{party_symbol(top_party)} {top_party}", f"{top_count:,} seats")
    with col4:
        st.metric("Seats needed for majority", gap_to_majority)

def simple_party_totals(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Party Results</div>', unsafe_allow_html=True)

    # Won seats by party
    won_df = df[df['status'] == 'Won']['party'].value_counts().head(10)

    fig = px.bar(won_df, text_auto=True, color=won_df.index)
    fig.update_layout(height=350, showlegend=False, title="Seats Won by Party")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def hot_races(df):
    st.markdown('<div class="soft-card hot-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Closest Races 🔥</div>', unsafe_allow_html=True)

    close = df.sort_values('margin').head(10)[['constituency', 'district', 'candidate', 'party', 'votes', 'margin', 'status']]
    st.dataframe(close, use_container_width=True, height=400)
    st.markdown('</div>', unsafe_allow_html=True)

def search_table(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">All Results</div>', unsafe_allow_html=True)

    q = st.text_input("🔍 Search races, candidates, districts...")

    if q:
        mask = df['constituency'].str.contains(q, case=False, na=False) |                df['district'].str.contains(q, case=False, na=False) |                df['candidate'].str.contains(q, case=False, na=False)
        df = df[mask]

    cols = ['constituency', 'district', 'candidate', 'party', 'votes', 'status']
    st.dataframe(df[cols], use_container_width=True, height=500)
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    inject_css()
    st_autorefresh(interval=25*1000)

    df = clean_df(load_election_data())
    fetch_status = load_fetch_status()

    topbar(fetch_status)

    if df.empty:
        st.error("No live results yet. Data updates every 5 minutes.")
        return

    hero(df)
    simple_party_totals(df)
    hot_races(df)
    search_table(df)

if __name__ == "__main__":
    main()
