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
            background: linear-gradient(180deg, #0b1220 0%, #0f172a 100%);
            color: #e5e7eb;
        }
        [data-testid="stSidebar"] {
            background: #0a0f1c;
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        [data-testid="stHeader"] {
            background: rgba(0,0,0,0);
        }
        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        .hero-wrap {
            background: linear-gradient(135deg, rgba(30,41,59,0.95), rgba(15,23,42,0.98));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        }
        .hero-title {
            font-size: 2rem;
            font-weight: 800;
            color: #f8fafc;
            margin-bottom: 6px;
            letter-spacing: -0.02em;
        }
        .hero-subtitle {
            color: #94a3b8;
            font-size: 0.98rem;
            margin-bottom: 0;
        }
        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0.4rem 0 0.8rem 0;
        }
        div[data-testid="metric-container"] {
            background: linear-gradient(180deg, rgba(15,23,42,0.92), rgba(17,24,39,0.92));
            border: 1px solid rgba(255,255,255,0.08);
            padding: 16px 14px;
            border-radius: 18px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.22);
        }
        div[data-testid="metric-container"] label {
            color: #94a3b8 !important;
        }
        div[data-testid="metric-container"] [data-testid="stMetricValue"] {
            color: #f8fafc;
        }
        .panel {
            background: rgba(15,23,42,0.82);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 20px;
            padding: 14px 14px 8px 14px;
            margin-bottom: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.18);
        }
        .pill {
            display: inline-block;
            padding: 6px 10px;
            margin-right: 8px;
            border-radius: 999px;
            background: rgba(59,130,246,0.16);
            color: #bfdbfe;
            font-size: 0.82rem;
            border: 1px solid rgba(96,165,250,0.24);
        }
        .small-note {
            color: #94a3b8;
            font-size: 0.85rem;
            margin-top: 6px;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background-color: #111827 !important;
            border-color: rgba(255,255,255,0.08) !important;
        }
        .stDataFrame, .stPlotlyChart {
            border-radius: 16px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(title, subtitle):
    st.markdown(
        f"""
        <div class="hero-wrap">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plotly_dark_layout(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.35)",
        font=dict(color="#e5e7eb"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", zeroline=False)
    return fig


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
        if top["isWinner"] or status_raw in ["DECLARED", "ELECTED", "WON", "FINAL"]:
            final_status = "Won"
        else:
            final_status = "Leading"

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
        ("nepalvotes_r2_constituencies", load_nepalvotes_json),
        ("local_repo_json", load_local_repo_json),
        ("github_raw_json", load_github_raw_json),
    ]

    for source_name, loader in loaders:
        try:
            df = loader()
            if df is not None and not df.empty:
                return {
                    "data": df,
                    "source": source_name,
                    "errors": source_errors,
                }
        except Exception as e:
            source_errors[source_name] = str(e)

    return {
        "data": pd.DataFrame(columns=EMPTY_COLUMNS),
        "source": None,
        "errors": source_errors,
    }


def render_empty_state(title_text, errors):
    render_hero(title_text, "No usable live election dataset is available right now.")
    st.info("The app could not load data from NepalVotes or backup JSON sources.")

    status = load_fetch_status()
    if status:
        st.markdown("### Fetch status")
        st.json(status, expanded=False)

    if errors:
        st.markdown("### Source errors")
        st.json(errors, expanded=False)

    st.markdown(
        '<div class="small-note">The app is trying NepalVotes R2 first, then local and GitHub backup JSON.</div>',
        unsafe_allow_html=True,
    )


def render_home_page():
    st_autorefresh(interval=25 * 1000, key="election_autorefresh")

    result = load_election_data()
    df = result["data"]
    active_source = result["source"]
    source_errors = result["errors"]

    if df.empty:
        render_empty_state("Nepal Election Live Dashboard", source_errors)
        return

    st.sidebar.title("Dashboard Filters")

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

    if filtered_df.empty:
        render_hero("Nepal Election Live Dashboard", "No results matched your current filters.")
        st.warning("Try changing province, party, status, or search text.")
        return

    total_seats = len(filtered_df)
    total_votes = int(filtered_df["votes"].sum())
    won_count = int((filtered_df["status"] == "Won").sum())
    leading_count = int((filtered_df["status"] == "Leading").sum())
    avg_progress = round(filtered_df["count_pct"].mean(), 1)

    render_hero(
        "Nepal Election Live Dashboard",
        "Live dashboard using mirrored NepalVotes constituency data with auto-refresh every 25 seconds.",
    )

    if active_source:
        st.caption(f"Active data source: {active_source}")

    st.markdown(
        """
        <span class="pill">NepalVotes R2 JSON</span>
        <span class="pill">25s app refresh</span>
        <span class="pill">Constituency drilldown</span>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Visible Seats", total_seats)
    c2.metric("Top Votes Sum", f"{total_votes:,}")
    c3.metric("Won", won_count)
    c4.metric("Leading", leading_count)
    c5.metric("Avg Count %", f"{avg_progress}%")

    left, right = st.columns([1.55, 1])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Constituency Results</div>', unsafe_allow_html=True)
        display_df = filtered_df[
            [
                "constituency", "province", "district", "candidate", "party",
                "votes", "runner_up", "runner_up_party", "runner_up_votes",
                "margin", "status", "count_pct",
            ]
        ].sort_values(["status", "votes"], ascending=[True, False])
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=430)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Party Standings</div>', unsafe_allow_html=True)
        party_summary = (
            filtered_df.groupby("party", as_index=False)
            .agg(
                seats_leading=("status", lambda x: int((x == "Leading").sum())),
                seats_won=("status", lambda x: int((x == "Won").sum())),
                total_top_votes=("votes", "sum"),
            )
            .sort_values(["seats_won", "seats_leading", "total_top_votes"], ascending=False)
            .head(12)
        )
        fig_party = px.bar(
            party_summary,
            x="party",
            y=["seats_won", "seats_leading"],
            barmode="group",
            color_discrete_sequence=["#22c55e", "#38bdf8"],
            text_auto=True,
        )
        fig_party = plotly_dark_layout(fig_party)
        fig_party.update_layout(height=360, showlegend=True)
        st.plotly_chart(fig_party, use_container_width=True)
        st.dataframe(party_summary, use_container_width=True, hide_index=True, height=180)
        st.markdown("</div>", unsafe_allow_html=True)

    bottom_left, bottom_mid, bottom_right = st.columns([1, 1, 1])

    with bottom_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Province Progress</div>', unsafe_allow_html=True)
        province_summary = (
            filtered_df.groupby("province", as_index=False)
            .agg(constituencies=("constituency", "count"), avg_count_pct=("count_pct", "mean"))
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
        fig_province = plotly_dark_layout(fig_province)
        fig_province.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig_province, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with bottom_mid:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top Votes by Party</div>', unsafe_allow_html=True)
        votes_by_party = (
            filtered_df.groupby("party", as_index=False)["votes"]
            .sum()
            .sort_values("votes", ascending=False)
            .head(10)
        )
        fig_votes = px.pie(votes_by_party, names="party", values="votes", hole=0.58)
        fig_votes = plotly_dark_layout(fig_votes)
        fig_votes.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_votes, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with bottom_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top Candidates</div>', unsafe_allow_html=True)
        top_candidates = filtered_df.sort_values("votes", ascending=False)[
            ["candidate", "party", "constituency", "votes", "status"]
        ].head(8)
        st.dataframe(top_candidates, use_container_width=True, hide_index=True, height=320)
        st.markdown("</div>", unsafe_allow_html=True)


def render_details_page():
    result = load_election_data()
    df = result["data"]
    active_source = result["source"]
    source_errors = result["errors"]

    if df.empty:
        render_empty_state("Constituency Details", source_errors)
        return

    render_hero(
        "Constituency Details",
        "Drill down into a seat, compare top two candidates, and inspect margin and counting progress.",
    )

    if active_source:
        st.caption(f"Active data source: {active_source}")

    st.sidebar.title("Seat Drilldown")
    province_list = ["All"] + sorted(df["province"].dropna().unique().tolist())
    selected_province = st.sidebar.selectbox("Province", province_list, key="details_province")

    filtered_df = df.copy()
    if selected_province != "All":
        filtered_df = filtered_df[filtered_df["province"] == selected_province]

    constituency_list = filtered_df["constituency"].sort_values().tolist()
    if not constituency_list:
        st.warning("No constituencies available for the selected province.")
        return

    selected_constituency = st.sidebar.selectbox("Choose constituency", constituency_list, key="details_constituency")
    seat = filtered_df[filtered_df["constituency"] == selected_constituency].iloc[0]

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Constituency", seat["constituency"])
    m2.metric("Leading / Winner", seat["candidate"])
    m3.metric("Party", seat["party"])
    m4.metric("Votes", f"{int(seat['votes']):,}")
    m5.metric("Margin", f"{int(seat['margin']):,}")

    left, right = st.columns([1.05, 1.2])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Seat Snapshot</div>', unsafe_allow_html=True)
        summary_df = pd.DataFrame([
            {"Field": "Province", "Value": seat["province"]},
            {"Field": "District", "Value": seat["district"]},
            {"Field": "Candidate", "Value": seat["candidate"]},
            {"Field": "Party", "Value": seat["party"]},
            {"Field": "Status", "Value": seat["status"]},
            {"Field": "Count Progress", "Value": f"{seat['count_pct']}%"},
            {"Field": "Runner-up", "Value": seat["runner_up"]},
            {"Field": "Runner-up Party", "Value": seat["runner_up_party"]},
            {"Field": "Runner-up Votes", "Value": f"{int(seat['runner_up_votes']):,}"},
            {"Field": "Margin", "Value": f"{int(seat['margin']):,}"},
        ])
        st.dataframe(summary_df, use_container_width=True, hide_index=True, height=388)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Vote Comparison</div>', unsafe_allow_html=True)
        compare_df = pd.DataFrame({
            "Candidate": [seat["candidate"], seat["runner_up"]],
            "Votes": [seat["votes"], seat["runner_up_votes"]],
            "Party": [seat["party"], seat["runner_up_party"]],
        })
        fig_compare = px.bar(compare_df, x="Candidate", y="Votes", color="Party", text_auto=True)
        fig_compare = plotly_dark_layout(fig_compare)
        fig_compare.update_layout(height=420)
        st.plotly_chart(fig_compare, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    bottom_left, bottom_right = st.columns([1.2, 1])

    with bottom_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">All Seats in Current Filter</div>', unsafe_allow_html=True)
        table_df = filtered_df[
            [
                "constituency", "province", "district", "candidate", "party",
                "votes", "runner_up", "runner_up_votes", "margin", "status", "count_pct",
            ]
        ].sort_values(["province", "district", "constituency"])
        st.dataframe(table_df, use_container_width=True, hide_index=True, height=380)
        st.markdown("</div>", unsafe_allow_html=True)

    with bottom_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top Margins</div>', unsafe_allow_html=True)
        margin_df = filtered_df[
            ["constituency", "candidate", "party", "margin"]
        ].sort_values("margin", ascending=False).head(8)
        fig_margin = px.bar(margin_df, x="constituency", y="margin", color="party", text_auto=True)
        fig_margin = plotly_dark_layout(fig_margin)
        fig_margin.update_layout(height=380)
        st.plotly_chart(fig_margin, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


inject_css()

home = st.Page(render_home_page, title="Dashboard", icon="🗳️", default=True)
details = st.Page(render_details_page, title="Details", icon="📍")

pg = st.navigation([home, details])
pg.run()
