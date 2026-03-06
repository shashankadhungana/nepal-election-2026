import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from streamlit_autorefresh import st_autorefresh


st.set_page_config(
    page_title="Nepal Election Live Dashboard",
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
            max-width: 1350px;
            padding-top: 1.25rem;
            padding-bottom: 2rem;
        }

        .hero {
            padding: 1.35rem 1.4rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #111827 0%, #172554 100%);
            border: 1px solid rgba(255,255,255,0.06);
            margin-bottom: 1rem;
        }

        .hero h1 {
            font-size: 2rem;
            line-height: 1.15;
            margin: 0 0 0.25rem 0;
            color: #f8fafc;
        }

        .hero p {
            margin: 0;
            color: #cbd5e1;
            font-size: 0.98rem;
        }

        .subtle {
            color: #94a3b8;
            font-size: 0.85rem;
        }

        .section-card {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 0.9rem 1rem 0.8rem 1rem;
            margin-bottom: 1rem;
        }

        .section-title {
            color: #f8fafc;
            font-size: 1.03rem;
            font-weight: 700;
            margin-bottom: 0.65rem;
        }

        div[data-testid="metric-container"] {
            background: #111827;
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 14px 12px;
            box-shadow: none;
        }

        div[data-testid="metric-container"] label {
            color: #94a3b8 !important;
        }

        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        .tag {
            display: inline-block;
            background: rgba(59,130,246,0.12);
            color: #bfdbfe;
            border: 1px solid rgba(96,165,250,0.18);
            border-radius: 999px;
            padding: 0.3rem 0.65rem;
            margin-right: 0.45rem;
            margin-bottom: 0.45rem;
            font-size: 0.82rem;
        }

        .status-good {
            color: #86efac;
            font-weight: 600;
        }

        .status-live {
            color: #7dd3fc;
            font-weight: 600;
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

    return out[EMPTY_COLUMNS].copy()


def clean_party_name(value):
    if value is None:
        return "Independent"
    text = str(value).strip()
    return text if text else "Independent"


def clean_candidate_name(value):
    return str(value or "").strip()


def normalize_nepalvotes_results(items):
    if not items or not isinstance(items, list):
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    rows = []

    for seat in items:
        candidates = seat.get("candidates", [])
        if not isinstance(candidates, list) or len(candidates) == 0:
            continue

        cleaned_candidates = []
        for c in candidates:
            cleaned_candidates.append(
                {
                    "candidate": clean_candidate_name(c.get("name") or c.get("nameEn") or c.get("nameNp")),
                    "party": clean_party_name(c.get("partyName") or c.get("party") or c.get("partyId")),
                    "votes": int(pd.to_numeric(c.get("votes", 0), errors="coerce") or 0),
                    "isWinner": bool(c.get("isWinner", False)),
                }
            )

        cleaned_candidates = sorted(cleaned_candidates, key=lambda x: x["votes"], reverse=True)
        top = cleaned_candidates[0]
        runner = cleaned_candidates[1] if len(cleaned_candidates) > 1 else {
            "candidate": "",
            "party": "",
            "votes": 0,
            "isWinner": False,
        }

        votes_cast = pd.to_numeric(seat.get("votesCast", 0), errors="coerce")
        total_voters = pd.to_numeric(seat.get("totalVoters", 0), errors="coerce")
        count_pct = 0.0
        if pd.notna(votes_cast) and pd.notna(total_voters) and float(total_voters) > 0:
            count_pct = round((float(votes_cast) / float(total_voters)) * 100, 1)

        status_raw = str(seat.get("status") or "").strip().upper()
        final_status = "Won" if top["isWinner"] or status_raw in ["DECLARED", "ELECTED", "WON", "FINAL"] else "Leading"

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

    df = pd.DataFrame(rows).sort_values(["province", "district", "constituency"]).reset_index(drop=True)
    return validate_final_schema(df)


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


def hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


def chart_layout(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        margin=dict(l=18, r=18, t=42, b=18),
        legend=dict(orientation="h", y=1.02, x=1, xanchor="right"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)")
    return fig


def render_empty_state(errors):
    hero("Nepal Election Live Dashboard", "No election data is available right now.")
    st.warning("The app could not load live or backup data.")

    status = load_fetch_status()
    if status:
        st.markdown("### Latest fetch status")
        st.json(status, expanded=False)

    if errors:
        st.markdown("### Source errors")
        st.json(errors, expanded=False)


def render_home_page():
    st_autorefresh(interval=25 * 1000, key="autorefresh")
    result = load_election_data()
    df = result["data"]
    active_source = result["source"]
    source_errors = result["errors"]

    if df.empty:
        render_empty_state(source_errors)
        return

    st.sidebar.title("Filters")
    province_options = ["All"] + sorted(df["province"].dropna().unique().tolist())
    party_options = ["All"] + sorted(df["party"].dropna().unique().tolist())
    status_options = ["All"] + sorted(df["status"].dropna().unique().tolist())

    selected_province = st.sidebar.selectbox("Province", province_options)
    selected_party = st.sidebar.selectbox("Party", party_options)
    selected_status = st.sidebar.selectbox("Race status", status_options)
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

    if filtered_df.empty:
        hero("Nepal Election Live Dashboard", "No seats match the current filters.")
        st.info("Try changing your province, party, status, or search text.")
        return

    total_seats = len(filtered_df)
    declared = int((filtered_df["status"] == "Won").sum())
    leading = int((filtered_df["status"] == "Leading").sum())
    avg_progress = round(filtered_df["count_pct"].mean(), 1)
    total_top_votes = int(filtered_df["votes"].sum())

    hero("Nepal Election Live Dashboard", "Readable live tracking for constituency leaders, margins, and counting progress.")

    st.markdown(
        f"""
        <span class="tag">Source: {active_source}</span>
        <span class="tag">Auto-refresh: 25s</span>
        <span class="tag">Visible seats: {total_seats}</span>
        """,
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Seats shown", total_seats)
    m2.metric("Declared", declared)
    m3.metric("Still leading", leading)
    m4.metric("Average count progress", f"{avg_progress}%")

    n1, n2 = st.columns([1.45, 1])

    with n1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Live constituency table")

        table_df = filtered_df.rename(
            columns={
                "candidate": "Leader",
                "party": "Leader party",
                "votes": "Leader votes",
                "runner_up": "Runner-up",
                "runner_up_party": "Runner-up party",
                "runner_up_votes": "Runner-up votes",
                "margin": "Margin",
                "status": "Status",
                "count_pct": "Count %",
                "constituency": "Seat",
                "province": "Province",
                "district": "District",
            }
        )[
            [
                "Seat", "Province", "District", "Leader", "Leader party", "Leader votes",
                "Runner-up", "Runner-up party", "Runner-up votes", "Margin", "Status", "Count %",
            ]
        ].sort_values(["Status", "Leader votes"], ascending=[True, False])

        st.dataframe(table_df, width="stretch", hide_index=True, height=470)
        st.markdown("</div>", unsafe_allow_html=True)

    with n2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Party position")

        party_summary = (
            filtered_df.groupby("party", as_index=False)
            .agg(
                declared=("status", lambda x: int((x == "Won").sum())),
                leading=("status", lambda x: int((x == "Leading").sum())),
                top_votes=("votes", "sum"),
            )
            .sort_values(["declared", "leading", "top_votes"], ascending=False)
            .head(10)
        )

        fig_party = px.bar(
            party_summary,
            x="party",
            y=["declared", "leading"],
            barmode="group",
            color_discrete_sequence=["#22c55e", "#38bdf8"],
            text_auto=True,
        )
        fig_party = chart_layout(fig_party)
        fig_party.update_layout(height=350)
        st.plotly_chart(fig_party, width="stretch")

        st.dataframe(party_summary, width="stretch", hide_index=True, height=210)
        st.markdown("</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)

    with b1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Province progress")

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
        fig_province.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig_province, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Top vote share by party")

        votes_by_party = (
            filtered_df.groupby("party", as_index=False)["votes"]
            .sum()
            .sort_values("votes", ascending=False)
            .head(8)
        )

        fig_votes = px.pie(
            votes_by_party,
            names="party",
            values="votes",
            hole=0.58,
            color_discrete_sequence=px.colors.sequential.Blues_r,
        )
        fig_votes = chart_layout(fig_votes)
        fig_votes.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_votes, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with b3:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Top leaders by votes")

        leaders = filtered_df.sort_values("votes", ascending=False)[
            ["candidate", "party", "constituency", "votes", "status"]
        ].rename(
            columns={
                "candidate": "Candidate",
                "party": "Party",
                "constituency": "Seat",
                "votes": "Votes",
                "status": "Status",
            }
        ).head(10)

        st.dataframe(leaders, width="stretch", hide_index=True, height=320)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    card_title("Quick notes")
    c1, c2, c3 = st.columns(3)
    c1.metric("Top-leader votes shown", f"{total_top_votes:,}")
    c2.metric("Highest visible margin", f"{int(filtered_df['margin'].max()):,}")
    c3.metric("Closest visible race", f"{int(filtered_df['margin'].min()):,}")
    st.caption("Leader votes are the current votes of the top candidate in each visible seat.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_details_page():
    result = load_election_data()
    df = result["data"]
    source_errors = result["errors"]
    active_source = result["source"]

    if df.empty:
        render_empty_state(source_errors)
        return

    hero("Constituency details", "Choose a seat to see leader, runner-up, margin, and local counting progress.")

    st.markdown(
        f"""
        <span class="tag">Source: {active_source}</span>
        <span class="tag">Drilldown view</span>
        """,
        unsafe_allow_html=True,
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

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Seat", seat["constituency"])
    m2.metric("Leader", seat["candidate"])
    m3.metric("Leader votes", f"{int(seat['votes']):,}")
    m4.metric("Margin", f"{int(seat['margin']):,}")
    m5.metric("Count progress", f"{seat['count_pct']}%")

    d1, d2 = st.columns([1, 1.2])

    with d1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Seat summary")

        seat_summary = pd.DataFrame([
            {"Field": "Province", "Value": seat["province"]},
            {"Field": "District", "Value": seat["district"]},
            {"Field": "Status", "Value": seat["status"]},
            {"Field": "Leader", "Value": seat["candidate"]},
            {"Field": "Leader party", "Value": seat["party"]},
            {"Field": "Leader votes", "Value": f"{int(seat['votes']):,}"},
            {"Field": "Runner-up", "Value": seat["runner_up"]},
            {"Field": "Runner-up party", "Value": seat["runner_up_party"]},
            {"Field": "Runner-up votes", "Value": f"{int(seat['runner_up_votes']):,}"},
            {"Field": "Margin", "Value": f"{int(seat['margin']):,}"},
        ])

        st.dataframe(seat_summary, width="stretch", hide_index=True, height=390)
        st.markdown("</div>", unsafe_allow_html=True)

    with d2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        card_title("Leader vs runner-up")

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
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig_compare = chart_layout(fig_compare)
        fig_compare.update_layout(height=430)
        st.plotly_chart(fig_compare, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    card_title("Other seats in current province filter")

    province_table = filtered_df[
        ["constituency", "candidate", "party", "votes", "runner_up", "runner_up_votes", "margin", "status", "count_pct"]
    ].rename(
        columns={
            "constituency": "Seat",
            "candidate": "Leader",
            "party": "Leader party",
            "votes": "Leader votes",
            "runner_up": "Runner-up",
            "runner_up_votes": "Runner-up votes",
            "margin": "Margin",
            "status": "Status",
            "count_pct": "Count %",
        }
    ).sort_values(["Status", "Leader votes"], ascending=[True, False])

    st.dataframe(province_table, width="stretch", hide_index=True, height=380)
    st.markdown("</div>", unsafe_allow_html=True)


inject_css()

home = st.Page(render_home_page, title="Dashboard", icon="🗳️", default=True)
details = st.Page(render_details_page, title="Details", icon="📍")

pg = st.navigation([home, details])
pg.run()
