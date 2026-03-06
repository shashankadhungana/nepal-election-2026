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
    page_title="Nepal Election Results 2082 (2026)",
    page_icon="🗳️",
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
TOTAL_SEATS = 275
FPTP_SEATS = 165
PROVINCES_TOTAL = 7
MAJORITY_NEEDED = 138

PARTY_COLOR_MAP = {
    "CPN-UML": "#e11d48",
    "Nepali Congress": "#2563eb",
    "Maoist Centre": "#dc2626",
    "Rastriya Swatantra Party": "#14b8a6",
    "Rastriya Prajatantra Party": "#7c3aed",
    "Janamat Party": "#f59e0b",
    "Nagarik Unmukti Party": "#f97316",
    "Janata Samajbadi Party": "#22c55e",
    "Independent": "#94a3b8",
}

PARTY_NAME_NORMALIZATION = {
    "CPN UML": "CPN-UML",
    "CPN (UML)": "CPN-UML",
    "Nepali Congress Party": "Nepali Congress",
    "NC": "Nepali Congress",
    "RSP": "Rastriya Swatantra Party",
    "RPP": "Rastriya Prajatantra Party",
    "JSP": "Janata Samajbadi Party",
    "Maoist": "Maoist Centre",
}


def inject_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: #0b1220;
            color: #e5e7eb;
        }

        [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }

        .block-container {
            max-width: 1320px;
            padding-top: 0.8rem;
            padding-bottom: 2rem;
        }

        .topnav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 0.9rem;
            padding: 0.85rem 0.2rem 0.2rem 0.2rem;
        }

        .brand {
            font-size: 1.25rem;
            font-weight: 800;
            color: #f8fafc;
        }

        .nav-links {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .nav-pill {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.07);
            color: #cbd5e1;
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            font-size: 0.85rem;
        }

        .live-banner {
            background: linear-gradient(135deg, #111827 0%, #1e3a8a 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 22px;
            padding: 1.25rem 1.25rem 1.05rem 1.25rem;
            margin-bottom: 1rem;
        }

        .live-row {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 0.5rem;
        }

        .live-badge {
            background: #dc2626;
            color: white;
            font-weight: 700;
            font-size: 0.78rem;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
        }

        .updated-badge {
            background: rgba(255,255,255,0.12);
            color: #e2e8f0;
            font-size: 0.8rem;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
        }

        .hero-title {
            font-size: 1.95rem;
            font-weight: 800;
            color: #f8fafc;
            margin: 0.2rem 0;
        }

        .hero-subtitle {
            color: #dbeafe;
            font-size: 0.98rem;
            margin-bottom: 0.8rem;
        }

        .hero-stats {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .hero-stat {
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.12);
            color: #eff6ff;
            border-radius: 16px;
            padding: 0.7rem 0.9rem;
            min-width: 120px;
        }

        .hero-stat .label {
            font-size: 0.78rem;
            color: #cbd5e1;
        }

        .hero-stat .value {
            font-size: 1.2rem;
            font-weight: 800;
            color: #ffffff;
        }

        .section-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 18px;
            padding: 1rem 1rem 0.95rem 1rem;
            margin-bottom: 1rem;
        }

        .section-title {
            color: #f8fafc;
            font-size: 1.06rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .section-subtle {
            color: #94a3b8;
            font-size: 0.86rem;
            margin-bottom: 0.8rem;
        }

        .featured-card {
            background: linear-gradient(180deg, rgba(30,41,59,0.9), rgba(17,24,39,0.95));
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: 18px;
            padding: 0.95rem;
            min-height: 210px;
        }

        .small-label {
            color: #93c5fd;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .seat-name {
            color: #f8fafc;
            font-size: 1.1rem;
            font-weight: 800;
            margin: 0.2rem 0;
        }

        .seat-meta {
            color: #cbd5e1;
            font-size: 0.84rem;
            margin-bottom: 0.7rem;
        }

        .candidate-line {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            margin: 0.35rem 0;
            color: #e5e7eb;
            font-size: 0.9rem;
        }

        .party-chip {
            display: inline-block;
            padding: 0.22rem 0.55rem;
            border-radius: 999px;
            font-size: 0.78rem;
            color: white;
            margin-right: 0.35rem;
            margin-bottom: 0.3rem;
            font-weight: 600;
        }

        .update-item {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 0.7rem 0.8rem;
            margin-bottom: 0.55rem;
        }

        div[data-testid="metric-container"] {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.06);
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

        .small-note {
            color: #94a3b8;
            font-size: 0.84rem;
        }

        @media (max-width: 900px) {
            .hero-title {
                font-size: 1.55rem;
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


def party_color(party):
    return PARTY_COLOR_MAP.get(normalize_party_name(party), "#64748b")


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
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=18, r=18, t=40, b=18),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)")
    return fig


def party_chip_html(party):
    return f'<span class="party-chip" style="background:{party_color(party)};">{normalize_party_name(party)}</span>'


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
            <div class="brand">Nepal Election Results 2082 (2026)</div>
            <div class="nav-links">
                <span class="nav-pill">Home</span>
                <span class="nav-pill">Explore</span>
                <span class="nav-pill">Map</span>
                <span class="nav-pill">Parties</span>
                <span class="nav-pill">Candidates</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_banner(source_text, updated_text, constituencies_count, provinces_count, parties_count):
    st.markdown(
        f"""
        <div class="live-banner">
            <div class="live-row">
                <span class="live-badge">LIVE</span>
                <span class="updated-badge">Last updated {updated_text}</span>
            </div>
            <div class="hero-title">Nepal House of Representatives</div>
            <div class="hero-subtitle">General Election · March 5, 2026</div>
            <div class="hero-stats">
                <div class="hero-stat"><div class="label">Constituencies</div><div class="value">{constituencies_count}</div></div>
                <div class="hero-stat"><div class="label">Provinces</div><div class="value">{provinces_count}</div></div>
                <div class="hero-stat"><div class="label">Parties</div><div class="value">{parties_count}</div></div>
                <div class="hero-stat"><div class="label">Total Seats</div><div class="value">{TOTAL_SEATS}</div></div>
            </div>
            <div class="small-note" style="margin-top:0.8rem;">Source: {source_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_title(text, subtle=None):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
    if subtle:
        st.markdown(f'<div class="section-subtle">{subtle}</div>', unsafe_allow_html=True)


def seat_share_chart(df):
    seat_counts = (
        df.groupby("party", as_index=False)
        .agg(
            counting=("status", lambda x: int((x == "Counting").sum())),
            declared=("status", lambda x: int((x == "Won").sum())),
        )
        .sort_values(["declared", "counting"], ascending=False)
        .head(12)
    )

    if seat_counts.empty:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=seat_counts["party"],
            y=seat_counts["counting"],
            name="Leading / Counting",
            marker_color="#38bdf8",
        )
    )
    fig.add_trace(
        go.Bar(
            x=seat_counts["party"],
            y=seat_counts["declared"],
            name="Declared",
            marker_color="#22c55e",
        )
    )

    fig.add_hline(
        y=MAJORITY_NEEDED,
        line_dash="dash",
        line_color="#fbbf24",
        annotation_text=f"Majority needed: {MAJORITY_NEEDED}",
        annotation_position="top left",
    )

    fig.update_layout(
        barmode="stack",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=18, r=18, t=40, b=18),
        height=360,
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)")

    return fig


def featured_seats(df):
    if df.empty:
        return df
    featured = df.sort_values(["count_pct", "margin"], ascending=[False, True]).head(2)
    if len(featured) < 2:
        featured = df.head(2)
    return featured


def build_updates(df):
    if df.empty:
        return []

    updates = []
    declared_df = df[df["status"] == "Won"].sort_values("margin", ascending=False).head(4)
    for _, row in declared_df.iterrows():
        updates.append(
            f"{row['candidate']} ({row['party']}) declared in {row['constituency']} by {int(row['margin']):,} votes."
        )

    counting_df = df[df["status"] == "Counting"].sort_values("margin", ascending=True).head(4)
    for _, row in counting_df.iterrows():
        updates.append(
            f"{row['constituency']} remains close: {row['candidate']} ({row['party']}) leads by {int(row['margin']):,} votes."
        )

    return updates[:6]


def render_empty_state(errors):
    top_nav()
    hero_banner("Source unavailable", "Unknown", 0, 0, 0)
    st.warning("The app could not load live or backup data.")
    if errors:
        st.json(errors, expanded=False)


def render_home_page():
    st_autorefresh(interval=25 * 1000, key="autorefresh")

    result = load_election_data()
    df = result["data"]
    active_source = result["source"]
    source_errors = result["errors"]
    fetch_status = load_fetch_status()

    if df.empty:
        render_empty_state(source_errors)
        return

    st.sidebar.title("Filters")
    province_options = ["All"] + sorted(df["province"].dropna().unique().tolist())
    party_options = ["All"] + sorted(df["party"].dropna().unique().tolist())
    status_options = ["All"] + sorted(df["status"].dropna().unique().tolist())

    selected_province = st.sidebar.selectbox("Province", province_options)
    selected_party = st.sidebar.selectbox("Party", party_options)
    selected_status = st.sidebar.selectbox("Status", status_options)
    search_text = st.sidebar.text_input("Search seat, district, candidate")

    filtered_df = df.copy()
    if selected_province != "All":
        filtered_df = filtered_df[filtered_df["province"] == selected_province]
    if selected_party != "All":
        filtered_df = filtered_df[filtered_df["party"] == selected_party]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]

    if search_text:
        q = search_text.strip().lower()
        filtered_df = filtered_df[
            filtered_df["constituency"].str.lower().str.contains(q, na=False)
            | filtered_df["district"].str.lower().str.contains(q, na=False)
            | filtered_df["candidate"].str.lower().str.contains(q, na=False)
        ]

    top_nav()
    hero_banner(
        source_text=active_source,
        updated_text=format_last_updated(fetch_status),
        constituencies_count=filtered_df["constituency"].nunique(),
        provinces_count=filtered_df["province"].nunique(),
        parties_count=filtered_df["party"].nunique(),
    )

    declared_count = int((filtered_df["status"] == "Won").sum())
    declared_pct = round((declared_count / FPTP_SEATS) * 100, 1) if FPTP_SEATS else 0
    hot_df = filtered_df.sort_values(["margin", "count_pct"], ascending=[True, False]).head(6)
    featured_df = featured_seats(filtered_df)

    c1, c2 = st.columns([1.4, 1])

    with c1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("⭐ Featured Section", "Highlighted constituencies")
        fcols = st.columns(2)

        for idx, (_, row) in enumerate(featured_df.iterrows()):
            with fcols[idx]:
                st.markdown(
                    f"""
                    <div class="featured-card">
                        <div class="small-label">{row['province']} · {row['status']}</div>
                        <div class="seat-name">{row['constituency']}</div>
                        <div class="seat-meta">{row['district']}</div>
                        <div class="candidate-line"><span>{row['candidate']}</span><span>{int(row['votes']):,}</span></div>
                        <div class="candidate-line"><span>{row['runner_up']}</span><span>{int(row['runner_up_votes']):,}</span></div>
                        <div style="margin-top:0.6rem;">{party_chip_html(row['party'])}{party_chip_html(row['runner_up_party'])}</div>
                        <div class="small-note" style="margin-top:0.6rem;">
                            Margin: {int(row['margin']):,} · Count: {row['count_pct']}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("🔥 Hot Seats", "Closely contested constituencies")
        st.metric("Seats in hot list", len(hot_df))
        hot_display = hot_df[
            ["constituency", "candidate", "party", "runner_up", "margin", "status"]
        ].rename(
            columns={
                "constituency": "Seat",
                "candidate": "Leader",
                "party": "Party",
                "runner_up": "Runner-up",
                "margin": "Margin",
                "status": "Status",
            }
        )
        st.dataframe(hot_display, width="stretch", hide_index=True, height=280)
        st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([1.25, 0.75])

    with c1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Latest Updates", "Newly declared seats and lead changes")
        updates = build_updates(filtered_df)
        if updates:
            for item in updates:
                st.markdown(f'<div class="update-item">{item}</div>', unsafe_allow_html=True)
        else:
            st.info("Updates will appear here once counting activity starts.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Declared Constituencies", f"{declared_count} / {FPTP_SEATS} declared")
        st.metric("Declared progress", f"{declared_pct}%")
        st.progress(min(max(declared_pct / 100, 0.0), 1.0))
        st.markdown(
            f'<div class="small-note" style="margin-top:0.7rem;">Counting and declared status are based on the visible filtered seats.</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    card_title("Seat Share (Out of 275)", f"Majority needed: {MAJORITY_NEEDED}")
    fig_share = seat_share_chart(filtered_df)
    st.plotly_chart(fig_share, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    card_title("Party position", "Current top seats and declared seats by party")

    party_summary = (
        filtered_df.groupby("party", as_index=False)
        .size()
        .rename(columns={"size": "current_top_seats"})
        .merge(
            filtered_df[filtered_df["status"] == "Won"]
            .groupby("party", as_index=False)
            .size()
            .rename(columns={"size": "declared"}),
            on="party",
            how="left",
        )
        .merge(
            filtered_df.groupby("party", as_index=False)["votes"]
            .sum()
            .rename(columns={"votes": "top_votes"}),
            on="party",
            how="left",
        )
        .fillna({"declared": 0, "top_votes": 0})
    )

    party_summary["declared"] = party_summary["declared"].astype(int)
    party_summary["top_votes"] = party_summary["top_votes"].astype(int)

    party_summary = party_summary.sort_values(
        ["declared", "current_top_seats", "top_votes"],
        ascending=False
    ).head(12)

    fig_party = px.bar(
        party_summary,
        x="party",
        y=["current_top_seats", "declared"],
        barmode="group",
        text_auto=True,
        color_discrete_sequence=["#38bdf8", "#22c55e"],
        labels={
            "party": "Party",
            "value": "Seats",
            "variable": "Metric",
        },
    )

    fig_party.for_each_trace(
        lambda t: t.update(
            name={
                "current_top_seats": "Current top seats",
                "declared": "Declared seats",
            }.get(t.name, t.name)
        )
    )

    fig_party = chart_layout(fig_party)
    fig_party.update_layout(height=360)

    st.plotly_chart(fig_party, width="stretch")

    st.dataframe(
        party_summary.rename(
            columns={
                "party": "Party",
                "current_top_seats": "Current top seats",
                "declared": "Declared seats",
                "top_votes": "Top votes",
            }
        ),
        width="stretch",
        hide_index=True,
        height=260,
    )

    st.markdown("</div>", unsafe_allow_html=True)


    with c2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Province progress", "Average visible count progress by province")
        province_summary = (
            filtered_df.groupby("province", as_index=False)
            .agg(
                seats=("constituency", "count"),
                avg_count_pct=("count_pct", "mean"),
            )
            .sort_values("avg_count_pct", ascending=False)
        )
        fig_province = px.bar(
            province_summary,
            x="province",
            y="avg_count_pct",
            text_auto=".1f",
            color="avg_count_pct",
            color_continuous_scale="Blues",
        )
        fig_province = chart_layout(fig_province)
        fig_province.update_layout(height=360, coloraxis_showscale=False)
        st.plotly_chart(fig_province, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
    st.dataframe(table_df, width="stretch", hide_index=True, height=430)
    st.markdown("</div>", unsafe_allow_html=True)


def render_details_page():
    result = load_election_data()
    df = result["data"]
    active_source = result["source"]
    source_errors = result["errors"]
    fetch_status = load_fetch_status()

    if df.empty:
        render_empty_state(source_errors)
        return

    top_nav()
    hero_banner(
        source_text=active_source,
        updated_text=format_last_updated(fetch_status),
        constituencies_count=df["constituency"].nunique(),
        provinces_count=df["province"].nunique(),
        parties_count=df["party"].nunique(),
    )

    st.sidebar.title("Seat view")
    province_list = ["All"] + sorted(df["province"].dropna().unique().tolist())
    selected_province = st.sidebar.selectbox("Province", province_list, key="details_province")

    filtered_df = df.copy()
    if selected_province != "All":
        filtered_df = filtered_df[filtered_df["province"] == selected_province]

    constituency_list = filtered_df["constituency"].sort_values().tolist()
    if not constituency_list:
        st.warning("No constituencies available for the selected province.")
        return

    selected_constituency = st.sidebar.selectbox("Choose seat", constituency_list, key="details_constituency")
    seat = filtered_df[filtered_df["constituency"] == selected_constituency].iloc[0]

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    card_title("Constituency detail", seat["constituency"])
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Province", seat["province"])
    m2.metric("Leader", seat["candidate"])
    m3.metric("Leader votes", f"{int(seat['votes']):,}")
    m4.metric("Margin", f"{int(seat['margin']):,}")
    m5.metric("Count progress", f"{seat['count_pct']}%")

    st.markdown(
        f'{party_chip_html(seat["party"])}{party_chip_html(seat["runner_up_party"])}',
        unsafe_allow_html=True,
    )

    compare_df = pd.DataFrame({
        "Candidate": [seat["candidate"], seat["runner_up"]],
        "Votes": [seat["votes"], seat["runner_up_votes"]],
        "Party": [seat["party"], seat["runner_up_party"]],
    })

    fig_compare = px.bar(
        compare_df,
        x="Candidate",
        y="Votes",
        color="Party",
        text_auto=True,
        color_discrete_map={
            seat["party"]: party_color(seat["party"]),
            seat["runner_up_party"]: party_color(seat["runner_up_party"]),
        },
    )
    fig_compare = chart_layout(fig_compare)
    fig_compare.update_layout(height=420)
    st.plotly_chart(fig_compare, width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    inject_css()

    home = st.Page(render_home_page, title="Home", icon="🏠", default=True)
    details = st.Page(render_details_page, title="Explore", icon="🔎")

    pg = st.navigation([home, details])
    pg.run()


if __name__ == "__main__":
    main()
