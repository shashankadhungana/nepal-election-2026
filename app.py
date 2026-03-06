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
    st.markdown(
        """
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
        """,
        unsafe_allow_html=True,
    )


def normalize_party_name(value):
    text = str(value or "").strip()
    if not text:
        return "Independent"
    return PARTY_NAME_NORMALIZATION.get(text, text)


def party_color(party):
    party = normalize_party_name(party)
    if party in PARTY_COLOR_MAP:
        return PARTY_COLOR_MAP[party]
    palette = ["#4F46E5", "#2563EB", "#F59E0B", "#EF4444", "#22C55E", "#8B5CF6", "#F97316", "#0EA5E9"]
    return palette[abs(hash(party)) % len(palette)]


def party_symbol(party):
    party = normalize_party_name(party)
    if party in PARTY_SYMBOLS:
        return PARTY_SYMBOLS[party]
    return "◆"


def symbol_chip(party):
    p = normalize_party_name(party)
    return f'<span class="symbol-chip" style="background:{party_color(p)};">{party_symbol(p)} {p}</span>'


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
        return pd.DataFrame(
            columns=[
                "constituency", "province", "district", "candidate", "party", "votes",
                "runner_up", "runner_up_party", "runner_up_votes", "margin", "status", "count_pct"
            ]
        )

    out = df.copy()

    for col in [
        "constituency", "province", "district", "candidate", "party", "runner_up", "runner_up_party", "status"
    ]:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").astype(str)

    for col in ["votes", "runner_up_votes", "margin", "count_pct"]:
        if col not in out.columns:
            out[col] = 0
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)

    out["votes"] = out["votes"].astype(int)
    out["runner_up_votes"] = out["runner_up_votes"].astype(int)
    out["margin"] = out["margin"].astype(int)
    out["count_pct"] = out["count_pct"].astype(float)
    out["party"] = out["party"].apply(normalize_party_name)
    out["runner_up_party"] = out["runner_up_party"].apply(normalize_party_name)
    out["status"] = out["status"].replace({"Counting": "Leading"}).fillna("Leading")

    return out


def topbar(fetch_status):
    updated_text = format_status_time(fetch_status)
    success = fetch_status.get("success", False) if isinstance(fetch_status, dict) else False
    row_count = fetch_status.get("row_count", 0) if isinstance(fetch_status, dict) else 0
    source = "Workflow mirror" if success else "Workflow mirror unavailable"

    st.markdown(
        f"""
        <div class="topbar">
            <div>
                <div class="brand">🇳🇵 Nepal Election Intelligence Dashboard</div>
                <div class="subbrand">Single-page control room for majority math, coalition scenarios, and the hottest constituency races.</div>
            </div>
            <div class="live-pills">
                <span class="pill pill-live">LIVE</span>
                <span class="pill">Updated {updated_text}</span>
                <span class="pill">Rows {row_count}</span>
                <span class="pill">{source}</span>
                <span class="pill">Majority {MAJORITY_NEEDED}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(df):
    party_summary = (
        df.groupby("party", as_index=False)
        .agg(
            current_leads=("party", "size"),
            declared_wins=("status", lambda s: int((s == "Won").sum())),
            visible_votes=("votes", "sum"),
        )
        .sort_values(["declared_wins", "current_leads", "visible_votes"], ascending=False)
    )

    if party_summary.empty:
        largest_party = "N/A"
        largest_leads = 0
        declared = 0
    else:
        largest_party = party_summary.iloc[0]["party"]
        largest_leads = int(party_summary.iloc[0]["current_leads"])
        declared = int((df["status"] == "Won").sum())

    gap = max(MAJORITY_NEEDED - largest_leads, 0)

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-grid">
                <div>
                    <div class="hero-title">A premium single-page view of the race to 138</div>
                    <div class="hero-subtitle">
                        Leading seats and declared wins are separated clearly. Coalition math includes a PR projection from visible vote share, not a final PR allocation.
                    </div>
                </div>
                <div class="metric-strip">
                    <div class="stat-card">
                        <div class="stat-label">Largest bloc</div>
                        <div class="stat-value">{party_symbol(largest_party)} {largest_party}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Current leads</div>
                        <div class="stat-value">{largest_leads}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Declared wins</div>
                        <div class="stat-value">{declared}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Gap to 138</div>
                        <div class="stat-value">{gap}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def majority_tracker(df):
    party_summary = (
        df.groupby("party", as_index=False)
        .agg(
            current_leads=("party", "size"),
            declared_wins=("status", lambda s: int((s == "Won").sum())),
            visible_votes=("votes", "sum"),
        )
        .sort_values(["declared_wins", "current_leads", "visible_votes"], ascending=False)
    )

    if party_summary.empty:
        top_party = "N/A"
        top_leads = 0
        top_wins = 0
    else:
        top_party = party_summary.iloc[0]["party"]
        top_leads = int(party_summary.iloc[0]["current_leads"])
        top_wins = int(party_summary.iloc[0]["declared_wins"])

    lead_pct = min((top_leads / MAJORITY_NEEDED) * 100, 100)
    win_pct = min((top_wins / MAJORITY_NEEDED) * 100, 100)

    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Majority Tracker</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Tracks the largest visible bloc against the 138-seat majority threshold.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="majority-bar-label">
            <span>Largest visible bloc · {party_symbol(top_party)} {top_party}</span>
            <span>{top_leads} / {MAJORITY_NEEDED}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="majority-track"><div class="majority-fill" style="width:{lead_pct}%;"></div></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="majority-bar-label">
            <span>Declared wins for that bloc</span>
            <span>{top_wins} / {MAJORITY_NEEDED}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="majority-track"><div class="majority-fill-win" style="width:{win_pct}%;"></div></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Largest bloc leads", top_leads)
    c2.metric("Largest bloc wins", top_wins)
    c3.metric("Short of majority", max(MAJORITY_NEEDED - top_leads, 0))

    fig = px.bar(
        party_summary.head(10),
        x="party",
        y=["current_leads", "declared_wins"],
        barmode="group",
        text_auto=True,
        color_discrete_sequence=["#4F46E5", "#22C55E"],
        labels={"party": "Party", "value": "Seats", "variable": "Metric"},
    )
    fig.for_each_trace(
        lambda t: t.update(
            name={"current_leads": "Current leads", "declared_wins": "Declared wins"}.get(t.name, t.name)
        )
    )
    fig.update_layout(
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.25)",
        font=dict(color="#0f172a"),
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
        transition={"duration": 450},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(15,23,42,0.08)")
    st.plotly_chart(fig, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

    return party_summary


def coalition_builder(df, party_summary):
    available = party_summary["party"].tolist() if not party_summary.empty else sorted(df["party"].unique().tolist())

    defaults = []
    for p in ["Rastriya Swatantra Party", "Nepali Congress", "CPN-UML"]:
        if p in available:
            defaults.append(p)
    if not defaults:
        defaults = available[:2]

    selected = st.segmented_control(
        "Coalition Builder",
        options=available[:8],
        default=defaults,
        selection_mode="multi",
        width="stretch",
        key="coalition_builder",
    )
    selected = selected or []

    coalition_df = df[df["party"].isin(selected)] if selected else df.iloc[0:0]
    total_visible_votes = df["votes"].sum()
    selected_votes = coalition_df["votes"].sum()

    fptp_leads = int(len(coalition_df))
    declared_wins = int((coalition_df["status"] == "Won").sum())
    visible_vote_share = round((selected_votes / total_visible_votes) * 100, 1) if total_visible_votes > 0 else 0.0
    projected_pr = int(round((selected_votes / total_visible_votes) * PR_SEATS)) if total_visible_votes > 0 else 0
    projected_total = fptp_leads + projected_pr
    gap = max(MAJORITY_NEEDED - projected_total, 0)

    status_class = "status-good" if projected_total >= MAJORITY_NEEDED else "status-warn"
    status_text = (
        f"Projected to clear majority by {projected_total - MAJORITY_NEEDED}"
        if projected_total >= MAJORITY_NEEDED
        else f"{gap} short of majority"
    )

    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Coalition Builder</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Combines current FPTP leads with a PR projection based on visible vote share. PR is modeled here as a projection only.</div>',
        unsafe_allow_html=True,
    )

    selected_html = (
        "".join([f'<span class="coalition-pill">{party_symbol(p)} {p}</span>' for p in selected])
        if selected else
        '<span class="coalition-pill">No parties selected</span>'
    )
    st.markdown(selected_html, unsafe_allow_html=True)
    st.markdown(f'<span class="coalition-pill {status_class}">{status_text}</span>', unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("FPTP leads", fptp_leads)
    m2.metric("Declared wins", declared_wins)
    m3.metric("Projected PR", projected_pr)
    m4.metric("Projected total", projected_total)

    chart_df = pd.DataFrame(
        [
            {"Metric": "FPTP leads", "Seats": fptp_leads},
            {"Metric": "Declared wins", "Seats": declared_wins},
            {"Metric": "Projected PR", "Seats": projected_pr},
            {"Metric": "Projected total", "Seats": projected_total},
            {"Metric": "Majority line", "Seats": MAJORITY_NEEDED},
        ]
    )

    fig = px.bar(
        chart_df,
        x="Metric",
        y="Seats",
        text_auto=True,
        color="Metric",
        color_discrete_sequence=["#5AC8FA", "#22C55E", "#F59E0B", "#4F46E5", "#EF4444"],
    )
    fig.update_layout(
        height=340,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.25)",
        font=dict(color="#0f172a"),
        margin=dict(l=10, r=10, t=20, b=10),
        showlegend=False,
        transition={"duration": 450},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(15,23,42,0.08)")
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Visible vote share used for PR projection: {visible_vote_share}%")
    st.markdown("</div>", unsafe_allow_html=True)


def hot_seats(df):
    st.markdown('<div class="soft-card hot-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="hot-header"><span class="fire">🔥</span><div class="section-title">Hot Seats</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">Closest high-attention races ranked by smallest margin and active count progress.</div>',
        unsafe_allow_html=True,
    )

    clashes = (
        df[df["status"].isin(["Leading", "Won"])]
        .sort_values(["margin", "count_pct"], ascending=[True, False])
        .head(6)
    )

    for _, row in clashes.iterrows():
        st.markdown(
            f"""
            <div class="clash-row">
                <div class="clash-title">{row['constituency']}</div>
                <div class="clash-meta">{row['province']} · {row['district']} · Count {row['count_pct']}% · Status {row['status']}</div>
                <div>{symbol_chip(row['party'])}{symbol_chip(row['runner_up_party'])}</div>
                <div class="candidate-line"><span>{row['candidate']}</span><span>{int(row['votes']):,}</span></div>
                <div class="candidate-line"><span>{row['runner_up']}</span><span>{int(row['runner_up_votes']):,}</span></div>
                <div class="tiny-note">Margin: {int(row['margin']):,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def featured_candidates(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Featured Candidates</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Famous names when present in the live mirror, otherwise the strongest visible candidates by area and vote rank.</div>',
        unsafe_allow_html=True,
    )

    famous_mask = df["candidate"].str.lower().isin([n.lower() for n in FAMOUS_CANDIDATES]) | df["runner_up"].str.lower().isin([n.lower() for n in FAMOUS_CANDIDATES])
    famous_df = df[famous_mask].copy()

    if famous_df.empty:
        ranked = (
            df.sort_values(["votes", "count_pct"], ascending=[False, False])
            .groupby("district", group_keys=False)
            .head(2)
            .copy()
        )
        ranked["Rank"] = ranked.groupby("district")["votes"].rank(method="first", ascending=False).astype(int)
    else:
        ranked = famous_df.sort_values(["votes", "count_pct"], ascending=[False, False]).copy()
        ranked["Rank"] = ranked.groupby("district")["votes"].rank(method="first", ascending=False).astype(int)

    for _, row in ranked.head(10).iterrows():
        st.markdown(
            f"""
            <div class="ranking-row">
                <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
                    <div>
                        <span class="rank-badge">{int(row['Rank'])}</span>
                        <span style="font-weight:900;color:#0f172a;">{row['candidate']}</span>
                        <span class="tiny-note">· {row['district']}</span>
                    </div>
                    <div class="tiny-note">{int(row['votes']):,} votes</div>
                </div>
                <div class="tiny-note" style="margin-top:0.35rem;">
                    {row['constituency']} · {row['province']} · {row['status']}
                </div>
                <div style="margin-top:0.38rem;">{symbol_chip(row['party'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def results_table(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Constituency Results</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Searchable table with current leader, runner-up, margin, count progress, and status.</div>',
        unsafe_allow_html=True,
    )

    q = st.text_input("Search constituency, district, or candidate", placeholder="Jhapa-5, Kathmandu, Oli, Rabi...")
    view = st.selectbox("View", ["All", "Leading only", "Won only"], index=0)

    table_df = df.copy()

    if q:
        term = q.strip().lower()
        table_df = table_df[
            table_df["constituency"].str.lower().str.contains(term, na=False)
            | table_df["district"].str.lower().str.contains(term, na=False)
            | table_df["candidate"].str.lower().str.contains(term, na=False)
            | table_df["runner_up"].str.lower().str.contains(term, na=False)
        ]

    if view == "Leading only":
        table_df = table_df[table_df["status"] == "Leading"]
    elif view == "Won only":
        table_df = table_df[table_df["status"] == "Won"]

    display = table_df.rename(
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

    st.dataframe(display, width="stretch", height=520, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def empty_state(fetch_status):
    err = fetch_status.get("error") if isinstance(fetch_status, dict) else None
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.error("Election data is currently unavailable.")
    if err:
        st.caption(f"Latest workflow error: {err}")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_css()
    st_autorefresh(interval=25 * 1000, key="dashboard_autorefresh")

    df = clean_df(load_election_data())
    fetch_status = load_fetch_status()

    topbar(fetch_status)

    if df.empty:
        empty_state(fetch_status)
        return

    hero(df)

    col1, col2 = st.columns([1.25, 1])
    with col1:
        party_summary = majority_tracker(df)
    with col2:
        coalition_builder(df, party_summary)

    col3, col4 = st.columns([1.05, 0.95])
    with col3:
        hot_seats(df)
    with col4:
        featured_candidates(df)

    results_table(df)


if __name__ == "__main__":
    main()
