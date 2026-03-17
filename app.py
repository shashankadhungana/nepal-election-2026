
from datetime import datetime, timezone

import pandas as pd
import plotly.express as px
import streamlit as st

from data import load_election_data, load_fetch_status


st.set_page_config(
    page_title="Nepal Election Results 2082 - Final Dashboard",
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
    "Rastriya Swatantra Party": "#6366F1",
    "Nepali Congress": "#3B82F6", 
    "CPN-UML": "#F59E0B",
    "Maoist Centre": "#EF4444",
    "Rastriya Prajatantra Party": "#8B5CF6",
    "Janata Samajbadi Party": "#22C55E",
    "Janamat Party": "#EAB308",
    "Nagarik Unmukti Party": "#F97316",
    "Independent": "#6B7280",
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


def inject_premium_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        :root {
            --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --glass-bg: rgba(255,255,255,0.25);
            --glass-border: rgba(255,255,255,0.18);
            --shadow-lg: 0 25px 50px -12px rgba(0,0,0,0.25);
            --shadow-xl: 0 35px 60px -12px rgba(0,0,0,0.3);
            --radius-xl: 24px;
            --radius-lg: 20px;
        }

        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        .stApp {
            background: 
                radial-gradient(ellipse at top left, rgba(79,70,229,0.2) 0%, transparent 50%),
                radial-gradient(ellipse at bottom right, rgba(239,68,68,0.15) 0%, transparent 50%),
                linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%);
        }

        /* Header & Topbar */
        [data-testid="stHeader"] { background: transparent !important; }
        .top-hero {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: var(--radius-xl);
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
            box-shadow: var(--shadow-lg);
            animation: slideDown 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        .hero-title {
            font-size: clamp(2.2rem, 5vw, 3.5rem);
            font-weight: 800;
            background: linear-gradient(135deg, #1e293b, #334155);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.1;
            letter-spacing: -0.02em;
            margin-bottom: 0.5rem;
        }

        .hero-subtitle {
            font-size: 1.15rem;
            color: #64748b;
            font-weight: 400;
            max-width: 90%;
            line-height: 1.6;
        }

        .status-pills {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }

        .pill-premium {
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 50px;
            padding: 0.6rem 1.2rem;
            font-size: 0.9rem;
            font-weight: 600;
            color: #1e293b;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .pill-premium:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.15);
        }

        /* Cards */
        .glass-card {
            background: rgba(255,255,255,0.15);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-lg);
            padding: 2rem;
            margin-bottom: 1.5rem;
            transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            position: relative;
            overflow: hidden;
        }

        .glass-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
        }

        .glass-card:hover {
            transform: translateY(-8px);
            box-shadow: var(--shadow-xl);
        }

        .glass-card.majority::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 6px;
            height: 100%;
            background: linear-gradient(180deg, #10b981, #059669);
        }

        .glass-card.vs-builder::after {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 6px;
            height: 100%;
            background: linear-gradient(180deg, #3b82f6, #1d4ed8);
        }

        /* Section Headers */
        .section-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 1.5rem;
        }

        .section-icon {
            font-size: 1.5rem;
            background: rgba(255,255,255,0.2);
            border-radius: 12px;
            padding: 0.5rem;
            width: 48px;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .section-title-premium {
            font-size: 1.4rem;
            font-weight: 700;
            color: #1e293b;
            margin: 0;
            letter-spacing: -0.02em;
        }

        /* Metrics */
        div[data-testid="metric-container"] {
            background: rgba(255,255,255,0.2) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
            border-radius: var(--radius-lg) !important;
            padding: 1.5rem !important;
            margin: 0.5rem 0 !important;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1) !important;
        }

        /* Majority Bar */
        .premium-majority-bar {
            background: rgba(148,163,184,0.15);
            border-radius: 12px;
            height: 20px;
            overflow: hidden;
            margin: 1rem 0;
            border: 1px solid rgba(255,255,255,0.2);
        }

        .premium-fill {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #8b5cf6);
            transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 10px;
        }

        .premium-fill-win {
            background: linear-gradient(90deg, #10b981, #059669);
            box-shadow: 0 0 20px rgba(16,185,129,0.4);
        }

        /* PR Inputs */
        .pr-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.5rem;
        }

        .party-row {
            background: rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 1.25rem;
            border: 1px solid rgba(255,255,255,0.15);
            transition: all 0.3s ease;
        }

        .party-row:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-1px);
        }

        /* Dataframes */
        .stDataFrame > div > div {
            border-radius: var(--radius-lg);
            border: 1px solid rgba(255,255,255,0.2);
            overflow: hidden;
            box-shadow: var(--shadow-lg);
        }

        /* Animations */
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-30px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .glass-card {
            animation: fadeInUp 0.6s ease-out;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .pr-grid { grid-template-columns: 1fr; }
            .section-header { flex-direction: column; align-items: flex-start; gap: 0.5rem; }
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
        return pd.DataFrame(columns=["constituency", "province", "district", "candidate", "party", "votes", "runner_up", "runner_up_party", "runner_up_votes", "margin", "status", "count_pct", "Remarks"])

    out = df.copy()
    for col in ["constituency", "province", "district", "candidate", "party", "runner_up", "runner_up_party", "status"]:
        out[col] = out[col].fillna("").astype(str)

    for col in ["votes", "runner_up_votes", "margin"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)
    out["count_pct"] = pd.to_numeric(out["count_pct"], errors="coerce").fillna(0.0)

    out["party"] = out["party"].apply(normalize_party_name)
    out["runner_up_party"] = out["runner_up_party"].apply(normalize_party_name)
    out["status"] = out["status"].replace({"Counting": "Leading"}).fillna("Leading")

    # Map official EC "Elected" to "Won" for final-results logic
    if "Remarks" in out.columns:
        out.loc[out["Remarks"] == "Elected", "status"] = "Won"

    return out


def top_hero(fetch_status):
    updated_text = format_status_time(fetch_status)
    row_count = fetch_status.get("row_count", 0) if isinstance(fetch_status, dict) else 0

    st.markdown(
        f"""
        <div class="top-hero">
            <div class="hero-title">🇳🇵 Nepal Election Results 2082</div>
            <div class="hero-subtitle">
                Final official results from Election Commission • FPTP + PR seat analysis • 
                Interactive party comparisons and majority tracker
            </div>
            <div class="status-pills">
                <span class="pill-premium">FINAL RESULTS</span>
                <span class="pill-premium">Updated {updated_text}</span>
                <span class="pill-premium">{row_count:,} constituencies</span>
                <span class="pill-premium">Data: result.election.gov.np</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_metrics(df):
    declared = df[df["status"] == "Won"]
    total_races = len(df)
    won_races = len(declared)

    if declared.empty:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Constituencies", total_races, "0 declared")
        with col2:
            st.metric("Declared seats", 0, "Waiting...")
        return

    party_counts = declared["party"].value_counts()
    top_party = party_counts.index[0]
    top_count = party_counts.iloc[0]
    gap_to_majority = max(MAJORITY_NEEDED - top_count, 0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🏛️ Constituencies", total_races)
    with col2:
        st.metric("✅ Declared (FPTP)", won_races)
    with col3:
        st.metric("👑 Largest party", f"{party_symbol(top_party)} {top_party}", f"{top_count:,}")
    with col4:
        st.metric("🎯 Seats to majority", gap_to_majority)


def majority_and_pr_section(df):
    st.markdown('<div class="glass-card majority">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">🏛️</div>
            <h3 class="section-title-premium">House of Representatives (275 seats)</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"].copy()
    if declared.empty:
        st.info("📊 No declared FPTP seats yet. Check back soon.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    fptp_counts = declared["party"].value_counts().sort_values(ascending=False)

    st.markdown(
        """
        <div class="pr-grid">
        """,
        unsafe_allow_html=True,
    )

    pr_inputs = {}
    total_pr_entered = 0
    for i, party in enumerate(fptp_counts.head(10).index):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f'<div class="party-row"><strong>{party_symbol(party)} {party}</strong><br>'
                f'<small style="color: #64748b;">{int(fptp_counts[party])} FPTP seats</small></div>',
                unsafe_allow_html=True,
            )
        with col2:
            pr_val = st.number_input(
                f"PR {party[:15]}...",
                min_value=0,
                max_value=PR_SEATS,
                value=0,
                step=1,
                key=f"pr_{party}_{i}",
                format="%d",
            )
        pr_inputs[party] = pr_val
        total_pr_entered += pr_val

    st.markdown("</div>", unsafe_allow_html=True)

    # Combined totals & majority bar
    combined_df = pd.DataFrame([
        {"party": p, "FPTP": int(fptp_counts[p]), "PR": pr_inputs.get(p, 0), "Total": int(fptp_counts[p]) + pr_inputs.get(p, 0)}
        for p in fptp_counts.head(8).index
    ]).sort_values("Total", ascending=False)

    top_total = int(combined_df.iloc[0]["Total"]) if not combined_df.empty else 0
    majority_pct = min(top_total / MAJORITY_NEEDED, 1.0)

    st.markdown('<div class="premium-majority-bar">', unsafe_allow_html=True)
    fill_class = "premium-fill-win" if top_total >= MAJORITY_NEEDED else "premium-fill"
    st.markdown(
        f'<div class="{fill_class}" style="width: {majority_pct*100:.1f}%"></div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; margin-top: 1rem; font-size: 0.95rem;">
            <span><strong>{party_symbol(combined_df.iloc[0]["party"])}</strong> leads with {top_total} seats</span>
            <span>Majority: {MAJORITY_NEEDED} seats</span>
        </div>
        <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.5rem;">
            PR entered: {total_pr_entered}/{PR_SEATS} • Total tracked: {int(combined_df["Total"].sum())}/{TOTAL_HOUSE_SEATS}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)


def vs_builder_section(df):
    st.markdown('<div class="glass-card vs-builder">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">⚔️</div>
            <h3 class="section-title-premium">Party vs Party Builder</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"].copy()
    if declared.empty:
        st.info("⚔️ Select parties once FPTP results are available.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    fptp_counts = declared["party"].value_counts().sort_values(ascending=False)
    parties = list(fptp_counts.index[:12])  # Top 12 only

    col_a, spacer, col_b = st.columns([1, 0.2, 1])
    with col_a:
        party_a = st.selectbox("🥇 Party A", parties, index=0, key="vs_a")
    with col_b:
        party_b = st.selectbox("🥈 Party B", parties, index=1, key="vs_b")

    if party_a == party_b:
        st.warning("⚠️ Please select two different parties.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    def get_pr(party):
        return st.session_state.get(f"pr_{party}_0", 0)  # Match key pattern from PR inputs

    a_fptp = int(fptp_counts.get(party_a, 0))
    a_pr = int(get_pr(party_a))
    a_total = a_fptp + a_pr

    b_fptp = int(fptp_counts.get(party_b, 0))
    b_pr = int(get_pr(party_b))
    b_total = b_fptp + b_pr

    combined = a_total + b_total

    # VS Chart
    vs_data = [
        {"Party": f"{party_symbol(party_a)} {party_a}", "Seats": a_total},
        {"Party": f"{party_symbol(party_b)} {party_b}", "Seats": b_total},
    ]
    fig = px.bar(
        pd.DataFrame(vs_data),
        x="Seats",
        y="Party",
        orientation="h",
        color="Party",
        color_discrete_map={
            party_a: PARTY_COLOR_MAP.get(party_a, "#6B7280"),
            party_b: PARTY_COLOR_MAP.get(party_b, "#6B7280"),
        },
        text="Seats",
    )
    fig.update_layout(
        height=240,
        showlegend=False,
        title="Seats head-to-head (FPTP + PR)",
        margin=dict(l=120, r=20, t=50, b=20),
        yaxis_title="",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Status summaries
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{party_symbol(party_a)} {party_a}:** {a_total} seats")
        st.markdown(f"**{party_symbol(party_b)} {party_b}:** {b_total} seats")

    with col2:
        color_ab = "🟢" if combined >= MAJORITY_NEEDED else "🟡"
        st.markdown(f"**{color_ab} Combined:** {combined} seats")
        need = max(MAJORITY_NEEDED - combined, 0)
        st.markdown(f"**vs majority:** {'✅ Majority secured' if combined >= MAJORITY_NEEDED else f'{need} seats short'}")

    st.markdown("</div>", unsafe_allow_html=True)


def simple_party_totals(df):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">📊</div>
            <h3 class="section-title-premium">Declared FPTP Seats by Party</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"]
    if declared.empty:
        st.info("📈 No declared seats yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    won_series = declared["party"].value_counts().sort_values(ascending=False).head(12)

    fig = px.bar(
        won_series.reset_index(),
        x="count",
        y="index",
        orientation="h",
        text="count",
        color="index",
        color_discrete_map={p: PARTY_COLOR_MAP.get(p, "#6B7280") for p in won_series.index},
        title="Final FPTP seats won",
    )
    fig.update_layout(
        height=400,
        showlegend=False,
        margin=dict(l=140, r=20, t=50, b=20),
        yaxis_title="Party",
        xaxis_title="Seats won",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)


def hot_races(df):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">🔥</div>
            <h3 class="section-title-premium">Closest Races</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    declared = df[df["status"] == "Won"].copy()
    if declared.empty:
        st.info("⚡ No declared seats yet.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    close = (
        declared.sort_values("margin")
        .head(12)[
            ["constituency", "district", "candidate", "party", "votes", "runner_up", "runner_up_party", "runner_up_votes", "margin"]
        ]
        .rename(columns={
            "candidate": "Winner", 
            "party": "Winner Party",
            "runner_up": "Runner-up", 
            "runner_up_party": "Runner-up Party",
            "runner_up_votes": "RU Votes",
            "margin": "Margin"
        })
    )

    st.dataframe(close, use_container_width=True, height=420, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def search_table(df):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">🔍</div>
            <h3 class="section-title-premium">All Constituency Results</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mode = st.radio("Show", ["Declared only", "All records"], horizontal=True, index=0)

    data = df[df["status"] == "Won"].copy() if mode == "Declared only" else df.copy()

    q = st.text_input("🔍 Search by constituency, candidate, district or party...", placeholder="e.g. Kathmandu, Oli, RSP...")

    if q:
        q_lower = q.lower()
        mask = (
            data["constituency"].str.contains(q_lower, case=False, na=False) |
            data["district"].str.contains(q_lower, case=False, na=False) |
            data["candidate"].str.contains(q_lower, case=False, na=False) |
            data["party"].str.contains(q_lower, case=False, na=False)
        )
        data = data[mask]

    cols = ["constituency", "district", "province", "candidate", "party", "votes", "runner_up", "runner_up_party", "runner_up_votes", "margin", "status"]
    st.dataframe(data[cols], use_container_width=True, height=500, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_premium_css()

    df = clean_df(load_election_data())
    fetch_status = load_fetch_status()

    top_hero(fetch_status)

    if df.empty:
        st.markdown(
            """
            <div class="glass-card" style="text-align: center; padding: 4rem;">
                <h2 style="color: #64748b;">📊 No results yet</h2>
                <p style="color: #94a3b8; font-size: 1.1rem;">Waiting for election data from <strong>result.election.gov.np</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Main dashboard sections
    hero_metrics(df)

    col1, col2 = st.columns([2, 1])
    with col1:
        majority_and_pr_section(df)
    with col2:
        vs_builder_section(df)

    simple_party_totals(df)
    hot_races(df)
    search_table(df)

    # Footer
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.9rem;">
            <strong>Nepal Election Results 2082</strong> • 
            Official data from Election Commission • 
            Built with ❤️ for election nerds
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
