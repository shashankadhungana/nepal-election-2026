from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

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
            font-weight: 600;
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

        .tiny-note {
            color: #64748b;
            font-size: 0.82rem;
        }

        .hot-card {
            background: linear-gradient(135deg, rgba(255,247,237,0.92), rgba(255,255,255,0.82));
            border: 1px solid rgba(251,146,60,0.24);
        }

        .vs-card {
            background: linear-gradient(135deg, rgba(239,246,255,0.95), rgba(255,255,255,0.92));
            border: 1px solid rgba(59,130,246,0.16);
        }

        .fire {
            font-size: 1.2rem;
            filter: drop-shadow(0 4px 10px rgba(249,115,22,0.36));
            animation: pulseFire 1.7s ease-in-out infinite;
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
        return pd.DataFrame(
            columns=[
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
        )

    out = df.copy()
    for col in [
        "constituency",
        "province",
        "district",
        "candidate",
        "party",
        "runner_up",
        "runner_up_party",
        "status",
    ]:
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
                <div class="brand">🇳🇵 Nepal Election Results 2082</div>
                <div class="subbrand">Final results • Party totals • Tightest races • Search any constituency</div>
            </div>
            <div class="live-pills">
                <span class="pill">FINAL</span>
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

    declared = df[df["status"] == "Won"]
    total_races = len(df)
    won_races = len(declared)
    if declared.empty:
        return

    party_counts = declared["party"].value_counts()
    top_party = party_counts.index[0]
    top_count = party_counts.iloc[0]
    gap_to_majority = max(MAJORITY_NEEDED - top_count, 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Constituencies total", total_races)
    with col2:
        st.metric("Seats declared (FPTP)", won_races)
    with col3:
        st.metric("Largest party (FPTP)", f"{party_symbol(top_party)} {top_party}", f"{top_count:,} seats")
    with col4:
        st.metric("Seats to majority (275)", gap_to_majority)


def majority_and_pr_section(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">House Majority (275 seats)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Final FPTP seats from data + manually entered PR seats per party when official list is available.</div>',
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"].copy()
    if declared.empty:
        st.info("No declared FPTP seats yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # FPTP seats per party
    fptp_counts = declared["party"].value_counts().sort_values(ascending=False)

    st.write("### Enter PR seats per party")
    pr_inputs = {}
    total_pr_entered = 0

    for party in fptp_counts.index:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(
                f"{party_symbol(party)} <strong>{party}</strong> &nbsp;·&nbsp; {int(fptp_counts[party])} FPTP seats",
                unsafe_allow_html=True,
            )
        with col2:
            pr_val = st.number_input(
                f"PR ({party})",
                min_value=0,
                max_value=PR_SEATS,
                value=0,
                step=1,
                key=f"pr_{party}",
            )
        with col3:
            st.markdown("&nbsp;", unsafe_allow_html=True)
        pr_inputs[party] = pr_val
        total_pr_entered += pr_val

    # Combined seats per party
    combined = []
    for party, fptp_seats in fptp_counts.items():
        pr_seats = pr_inputs.get(party, 0)
        combined.append(
            {
                "party": party,
                "FPTP": int(fptp_seats),
                "PR": int(pr_seats),
                "Total": int(fptp_seats) + int(pr_seats),
            }
        )
    combined_df = pd.DataFrame(combined).sort_values("Total", ascending=False)

    # Majority bar uses top party
    if not combined_df.empty:
        top_row = combined_df.iloc[0]
        top_party = top_row["party"]
        top_total = int(top_row["Total"])
        majority_pct = min(top_total / MAJORITY_NEEDED, 1.0)
    else:
        top_party, top_total, majority_pct = "N/A", 0, 0.0

    st.markdown('<div class="majority-bar-label">', unsafe_allow_html=True)
    st.markdown(
        f"<span>Largest party: {party_symbol(top_party)} <strong>{top_party}</strong> – {top_total} seats (FPTP + PR)</span>"
        f"<span>Majority threshold: {MAJORITY_NEEDED} seats</span>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    bar_class = "majority-fill-win" if top_total >= MAJORITY_NEEDED else "majority-fill"
    st.markdown('<div class="majority-track">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="{bar_class}" style="width: {majority_pct*100:.1f}%"></div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div class="tiny-note">PR seats entered: {total_pr_entered} / {PR_SEATS} • '
        f'Total House seats represented here: {int(combined_df["Total"].sum())} / {TOTAL_HOUSE_SEATS}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


def vs_builder_section(df):
    st.markdown('<div class="soft-card vs-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">VS Builder: Party vs Party</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Pick any two parties to compare their total seats (FPTP + PR) against each other and the 138-seat majority line.</div>',
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"].copy()
    if declared.empty:
        st.info("No declared FPTP seats yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Base: FPTP seats
    fptp_counts = declared["party"].value_counts().sort_values(ascending=False)
    parties = list(fptp_counts.index)

    if len(parties) < 2:
        st.info("Need at least two parties with seats for VS view.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    col_a, col_b = st.columns(2)
    with col_a:
        party_a = st.selectbox("Party A", parties, index=0, key="vs_party_a")
    with col_b:
        default_b = 1 if len(parties) > 1 else 0
        party_b = st.selectbox("Party B", parties, index=default_b, key="vs_party_b")

    if party_a == party_b:
        st.warning("Pick two different parties to compare.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    def get_pr(party):
        return st.session_state.get(f"pr_{party}", 0)

    data_rows = []
    for party in [party_a, party_b]:
        fptp = int(fptp_counts.get(party, 0))
        pr = int(get_pr(party))
        total = fptp + pr
        data_rows.append(
            {
                "Party": party,
                "FPTP seats": fptp,
                "PR seats": pr,
                "Total seats": total,
            }
        )

    vs_df = pd.DataFrame(data_rows)

    # Horizontal bar chart: Party A vs Party B
    fig = px.bar(
        vs_df,
        x="Total seats",
        y="Party",
        orientation="h",
        color="Party",
        text="Total seats",
        color_discrete_map={p: PARTY_COLOR_MAP.get(p, "#64748B") for p in vs_df["Party"]},
    )
    fig.update_layout(
        height=260,
        showlegend=False,
        title="Total seats (FPTP + PR) – head to head",
        xaxis_title="Seats",
        yaxis_title="",
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Text summary vs majority
    a_row = vs_df.iloc[0]
    b_row = vs_df.iloc[1]

    def status_line(row):
        seats = int(row["Total seats"])
        if seats >= MAJORITY_NEEDED:
            return f"✅ {row['Party']} clears the majority line with {seats} seats."
        else:
            need = MAJORITY_NEEDED - seats
            return f"ℹ️ {row['Party']} is {need} seats short of the majority (has {seats})."

    st.markdown(status_line(a_row))
    st.markdown(status_line(b_row))

    # A + B combined vs majority
    combined_ab = int(a_row["Total seats"] + b_row["Total seats"])
    if combined_ab >= MAJORITY_NEEDED:
        combined_msg = (
            f"🔥 Together, <strong>{a_row['Party']} + {b_row['Party']}</strong> reach {combined_ab} seats "
            f"and clear the {MAJORITY_NEEDED}-seat majority line."
        )
    else:
        need_ab = MAJORITY_NEEDED - combined_ab
        combined_msg = (
            f"➕ Together, <strong>{a_row['Party']} + {b_row['Party']}</strong> have {combined_ab} seats, "
            f"{need_ab} short of the {MAJORITY_NEEDED}-seat majority."
        )

    st.markdown(combined_msg, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def simple_party_totals(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Final FPTP Seats by Party</div>', unsafe_allow_html=True)

    declared = df[df["status"] == "Won"]
    if declared.empty:
        st.info("No declared seats yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    won_series = declared["party"].value_counts().sort_values(ascending=False)

    fig = px.bar(
        won_series,
        text_auto=True,
        color=won_series.index,
        color_discrete_map={p: PARTY_COLOR_MAP.get(p, "#64748B") for p in won_series.index},
    )
    fig.update_layout(
        height=350,
        showlegend=False,
        title="Seats won (FPTP, declared constituencies)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def hot_races(df):
    st.markdown('<div class="soft-card hot-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Tightest Final Margins 🔥</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Declared constituencies ordered by winning margin.</div>',
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"].copy()
    if declared.empty:
        st.info("No declared seats yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    close = (
        declared.sort_values("margin")
        .head(10)[
            [
                "constituency",
                "district",
                "candidate",
                "party",
                "votes",
                "runner_up",
                "runner_up_party",
                "runner_up_votes",
                "margin",
            ]
        ]
    )

    close = close.rename(
        columns={
            "candidate": "Winner",
            "party": "Winner party",
            "runner_up": "Runner‑up",
            "runner_up_party": "Runner‑up party",
            "runner_up_votes": "Runner‑up votes",
            "margin": "Win margin",
        }
    )

    st.dataframe(close, use_container_width=True, height=400)
    st.markdown("</div>", unsafe_allow_html=True)


def search_table(df):
    st.markdown('<div class="soft-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Final Constituency Results</div>', unsafe_allow_html=True)

    mode = st.radio(
        "View",
        ["Declared seats only", "All records"],
        horizontal=True,
        index=0,
    )

    if mode == "Declared seats only":
        data = df[df["status"] == "Won"].copy()
    else:
        data = df.copy()

    q = st.text_input("🔍 Search constituencies, candidates, districts, parties...")

    if q:
        q_lower = q.lower()
        mask = (
            data["constituency"].str.lower().str.contains(q_lower, na=False)
            | data["district"].str.lower().str.contains(q_lower, na=False)
            | data["candidate"].str.lower().str.contains(q_lower, na=False)
            | data["party"].str.lower().str.contains(q_lower, na=False)
        )
        data = data[mask]

    cols = [
        "constituency",
        "district",
        "province",
        "candidate",
        "party",
        "votes",
        "runner_up",
        "runner_up_party",
        "runner_up_votes",
        "margin",
    ]
    existing = [c for c in cols if c in data.columns]
    st.dataframe(data[existing], use_container_width=True, height=500)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_css()

    df = clean_df(load_election_data())
    fetch_status = load_fetch_status()

    topbar(fetch_status)

    if df.empty:
        st.error("No election results loaded. Check data source or try again.")
        return

    hero(df)
    majority_and_pr_section(df)
    vs_builder_section(df)
    simple_party_totals(df)
    hot_races(df)
    search_table(df)


if __name__ == "__main__":
    main()
