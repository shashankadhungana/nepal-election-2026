import requests
import pandas as pd
import plotly.express as px
import streamlit as st
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
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.15)", zeroline=False)
    return fig


def province_name_from_code(code):
    province_map = {
        1: "Koshi",
        2: "Madhesh",
        3: "Bagmati",
        4: "Gandaki",
        5: "Lumbini",
        6: "Karnali",
        7: "Sudurpashchim",
    }
    return province_map.get(code, "Unknown")


def normalize_raw_results(raw):
    if raw is None or raw.empty:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    required_columns = [
        "CandidateName",
        "PoliticalPartyName",
        "DistrictName",
        "State",
        "SCConstID",
        "TotalVoteReceived",
        "Rank",
        "Remarks",
    ]

    for col in required_columns:
        if col not in raw.columns:
            raw[col] = None

    raw["candidate"] = raw["CandidateName"].fillna("").astype(str).str.strip()
    raw["party"] = raw["PoliticalPartyName"].fillna("Independent").astype(str).str.strip()
    raw["district"] = raw["DistrictName"].fillna("Unknown").astype(str).str.strip()
    raw["sc_const_id"] = raw["SCConstID"].fillna("").astype(str).str.strip()
    raw["votes"] = pd.to_numeric(raw["TotalVoteReceived"], errors="coerce").fillna(0).astype(int)
    raw["rank_num"] = pd.to_numeric(raw["Rank"], errors="coerce")
    raw["remarks"] = raw["Remarks"].fillna("").astype(str).str.strip()
    raw["state_code"] = pd.to_numeric(raw["State"], errors="coerce").fillna(0).astype(int)
    raw["province"] = raw["state_code"].apply(province_name_from_code)

    raw = raw[(raw["district"] != "") & (raw["sc_const_id"] != "")]
    if raw.empty:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    raw["constituency"] = raw["district"] + "-" + raw["sc_const_id"]

    rows = []

    for constituency, group in raw.groupby("constituency", sort=True):
        group = group.sort_values(["votes", "rank_num"], ascending=[False, True]).reset_index(drop=True)

        top = group.iloc[0]
        runner = group.iloc[1] if len(group) > 1 else None

        top_votes = int(top["votes"])
        runner_votes = int(runner["votes"]) if runner is not None else 0

        rows.append(
            {
                "constituency": constituency,
                "province": top["province"],
                "district": top["district"],
                "candidate": top["candidate"] if top["candidate"] else "Unknown Candidate",
                "party": top["party"] if top["party"] else "Independent",
                "votes": top_votes,
                "runner_up": runner["candidate"] if runner is not None else "",
                "runner_up_party": runner["party"] if runner is not None else "",
                "runner_up_votes": runner_votes,
                "margin": top_votes - runner_votes,
                "status": "Won" if str(top["remarks"]).lower() == "elected" else "Leading",
                "count_pct": 100 if str(top["remarks"]).lower() == "elected" else 0,
            }
        )

    if not rows:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    return pd.DataFrame(rows).sort_values(
        ["province", "district", "constituency"]
    ).reset_index(drop=True)


@st.cache_data(ttl=30)
def load_fetch_status():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    status_url = "https://raw.githubusercontent.com/shashankadhungana/nepal-election-2026/main/data/fetch_status.json"

    try:
        r = requests.get(status_url, headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    return None


@st.cache_data(ttl=30)
def load_election_data():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json,text/plain,*/*",
    }

    github_raw_url = "https://raw.githubusercontent.com/shashankadhungana/nepal-election-2026/main/data/election_data.json"

    try:
        r = requests.get(github_raw_url, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return pd.DataFrame(data)
    except Exception:
        pass

    official_urls = [
        "https://result.election.gov.np/JSONFiles/ElectionResultCentral.txt",
        "https://result.election.gov.np/JSONFiles/ElectionResultCentral2079.txt",
    ]

    for url in official_urls:
        try:
            r = requests.get(
                url,
                headers={
                    **headers,
                    "Referer": "https://result.election.gov.np/",
                    "Origin": "https://result.election.gov.np",
                },
                timeout=30,
            )
            if r.status_code == 200:
                raw = pd.DataFrame(r.json())
                df = normalize_raw_results(raw)
                if not df.empty:
                    return df
        except Exception:
            pass

    return pd.DataFrame(columns=EMPTY_COLUMNS)


def render_empty_state(title_text):
    status = load_fetch_status()

    render_hero(
        title_text,
        "Official data source is temporarily unavailable or blocked from the hosting environment.",
    )
    st.info("The Election Commission source did not return usable data right now.")

    if status:
        st.markdown("### Fetch status")
        st.json(status, expanded=True)

    st.markdown(
        '<div class="small-note">The app is waiting for the GitHub mirror workflow to fetch and store usable data.</div>',
        unsafe_allow_html=True,
    )


def render_home_page():
    st_autorefresh(interval=30 * 1000, key="election_autorefresh")
    df = load_election_data()

    if df.empty:
        render_empty_state("Nepal Election Live Dashboard")
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
        render_hero(
            "Nepal Election Live Dashboard",
            "No results matched your current filters.",
        )
        st.warning("Try changing province, party, status, or search text.")
        return

    total_seats = len(filtered_df)
    total_votes = int(filtered_df["votes"].sum())
    won_count = int((filtered_df["status"] == "Won").sum())
    leading_count = int((filtered_df["status"] == "Leading").sum())
    avg_progress = round(filtered_df["count_pct"].mean(), 1)

    render_hero(
        "Nepal Election Live Dashboard",
        "Live dashboard using mirrored official election data with auto-refresh every 30 seconds.",
    )

    st.markdown(
        """
        <span class="pill">Official-source mirror</span>
        <span class="pill">30s app refresh</span>
        <span class="pill">Constituency drilldown</span>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Visible Seats", total_seats)
    c2.metric("Total Votes", f"{total_votes:,}")
    c3.metric("Won", won_count)
    c4.metric("Leading", leading_count)
    c5.metric("Avg Count %", f"{avg_progress}%")

    left, right = st.columns([1.55, 1])

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Constituency Results</div>', unsafe_allow_html=True)

        display_df = filtered_df[
            [
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
                total_votes=("votes", "sum"),
            )
            .sort_values(["seats_won", "seats_leading", "total_votes"], ascending=False)
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
            .agg(
                constituencies=("constituency", "count"),
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
        fig_province = plotly_dark_layout(fig_province)
        fig_province.update_layout(height=320, coloraxis_showscale=False)
        st.plotly_chart(fig_province, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with bottom_mid:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Votes by Party</div>', unsafe_allow_html=True)

        votes_by_party = (
            filtered_df.groupby("party", as_index=False)["votes"]
            .sum()
            .sort_values("votes", ascending=False)
            .head(10)
        )

        fig_votes = px.pie(
            votes_by_party,
            names="party",
            values="votes",
            hole=0.58,
        )
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

    st.markdown(
        '<div class="small-note">Source: mirrored data from the official Election Commission result files. Count progress is estimated as 100 for elected seats and 0 otherwise because the central result feed does not expose a direct count percentage field in the normalized output.</div>',
        unsafe_allow_html=True,
    )


def render_details_page():
    df = load_election_data()

    if df.empty:
        render_empty_state("Constituency Details")
        return

    render_hero(
        "Constituency Details",
        "Drill down into a seat, compare top two candidates, and inspect margin and result status.",
    )

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

    selected_constituency = st.sidebar.selectbox(
        "Choose constituency",
        constituency_list,
        key="details_constituency",
    )

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

        fig_compare = px.bar(
            compare_df,
            x="Candidate",
            y="Votes",
            color="Party",
            text_auto=True,
        )
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
                "constituency",
                "province",
                "district",
                "candidate",
                "party",
                "votes",
                "runner_up",
                "runner_up_votes",
                "margin",
                "status",
                "count_pct",
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

        fig_margin = px.bar(
            margin_df,
            x="constituency",
            y="margin",
            color="party",
            text_auto=True,
        )
        fig_margin = plotly_dark_layout(fig_margin)
        fig_margin.update_layout(height=380)
        st.plotly_chart(fig_margin, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


inject_css()

home = st.Page(render_home_page, title="Dashboard", icon="🗳️", default=True)
details = st.Page(render_details_page, title="Details", icon="📍")

pg = st.navigation([home, details])
pg.run()
