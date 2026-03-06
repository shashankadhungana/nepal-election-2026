import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh


st.set_page_config(
    page_title="Nepal Election Dashboard",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=30)
def load_election_data():
    df = pd.DataFrame([
        {
            "constituency": "Kathmandu-1",
            "province": "Bagmati",
            "district": "Kathmandu",
            "candidate": "Candidate A",
            "party": "Party X",
            "votes": 24567,
            "runner_up": "Candidate B",
            "runner_up_party": "Party Y",
            "runner_up_votes": 21950,
            "status": "Leading",
            "count_pct": 82,
        },
        {
            "constituency": "Kathmandu-2",
            "province": "Bagmati",
            "district": "Kathmandu",
            "candidate": "Candidate C",
            "party": "Party Y",
            "votes": 30110,
            "runner_up": "Candidate D",
            "runner_up_party": "Party X",
            "runner_up_votes": 28775,
            "status": "Won",
            "count_pct": 100,
        },
        {
            "constituency": "Lalitpur-1",
            "province": "Bagmati",
            "district": "Lalitpur",
            "candidate": "Candidate E",
            "party": "Party Z",
            "votes": 18670,
            "runner_up": "Candidate F",
            "runner_up_party": "Party X",
            "runner_up_votes": 18011,
            "status": "Leading",
            "count_pct": 74,
        },
        {
            "constituency": "Kaski-1",
            "province": "Gandaki",
            "district": "Kaski",
            "candidate": "Candidate G",
            "party": "Party X",
            "votes": 27890,
            "runner_up": "Candidate H",
            "runner_up_party": "Party Z",
            "runner_up_votes": 25100,
            "status": "Won",
            "count_pct": 100,
        },
        {
            "constituency": "Morang-3",
            "province": "Koshi",
            "district": "Morang",
            "candidate": "Candidate I",
            "party": "Party Y",
            "votes": 19880,
            "runner_up": "Candidate J",
            "runner_up_party": "Party X",
            "runner_up_votes": 19320,
            "status": "Leading",
            "count_pct": 68,
        },
        {
            "constituency": "Rupandehi-2",
            "province": "Lumbini",
            "district": "Rupandehi",
            "candidate": "Candidate K",
            "party": "Party X",
            "votes": 22440,
            "runner_up": "Candidate L",
            "runner_up_party": "Party Y",
            "runner_up_votes": 22010,
            "status": "Leading",
            "count_pct": 77,
        },
        {
            "constituency": "Dhanusha-1",
            "province": "Madhesh",
            "district": "Dhanusha",
            "candidate": "Candidate M",
            "party": "Party Z",
            "votes": 26440,
            "runner_up": "Candidate N",
            "runner_up_party": "Party Y",
            "runner_up_votes": 24490,
            "status": "Won",
            "count_pct": 100,
        },
        {
            "constituency": "Banke-1",
            "province": "Lumbini",
            "district": "Banke",
            "candidate": "Candidate O",
            "party": "Party Y",
            "votes": 17420,
            "runner_up": "Candidate P",
            "runner_up_party": "Party Z",
            "runner_up_votes": 17100,
            "status": "Leading",
            "count_pct": 59,
        },
    ])
    df["margin"] = df["votes"] - df["runner_up_votes"]
    return df


def home_page():
    st_autorefresh(interval=30 * 1000, key="election_autorefresh")
    df = load_election_data()

    st.sidebar.title("Filters")

    province_options = ["All"] + sorted(df["province"].unique().tolist())
    party_options = ["All"] + sorted(df["party"].unique().tolist())
    status_options = ["All"] + sorted(df["status"].unique().tolist())

    selected_province = st.sidebar.selectbox("Province", province_options)
    selected_party = st.sidebar.selectbox("Party", party_options)
    selected_status = st.sidebar.selectbox("Status", status_options)
    search_text = st.sidebar.text_input("Search constituency, district, or candidate")

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
            filtered_df["constituency"].str.lower().str.contains(q)
            | filtered_df["district"].str.lower().str.contains(q)
            | filtered_df["candidate"].str.lower().str.contains(q)
        ]

    total_constituencies = len(filtered_df)
    total_votes = int(filtered_df["votes"].sum()) if not filtered_df.empty else 0
    won_count = int((filtered_df["status"] == "Won").sum()) if not filtered_df.empty else 0
    leading_count = int((filtered_df["status"] == "Leading").sum()) if not filtered_df.empty else 0
    avg_progress = round(filtered_df["count_pct"].mean(), 1) if not filtered_df.empty else 0

    st.title("Nepal Election Dashboard")
    st.caption("Prototype UI using shared mock data. Official result endpoint integration comes next.")

    metric_cols = st.columns(5)
    metric_cols[0].metric("Visible Seats", total_constituencies)
    metric_cols[1].metric("Total Votes", f"{total_votes:,}")
    metric_cols[2].metric("Won", won_count)
    metric_cols[3].metric("Leading", leading_count)
    metric_cols[4].metric("Avg Count %", f"{avg_progress}%")

    left, right = st.columns([1.6, 1])

    with left:
        st.subheader("Constituency Results")
        display_df = filtered_df.copy()

        if not display_df.empty:
            display_df = display_df[
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

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Party Standings")

        if not filtered_df.empty:
            filtered_party = (
                filtered_df.groupby("party", as_index=False)
                .agg(
                    seats_leading=("status", lambda x: int((x == "Leading").sum())),
                    seats_won=("status", lambda x: int((x == "Won").sum())),
                    total_votes=("votes", "sum"),
                )
                .sort_values(["seats_won", "seats_leading", "total_votes"], ascending=False)
            )

            fig_party = px.bar(
                filtered_party,
                x="party",
                y=["seats_won", "seats_leading"],
                barmode="group",
                title="Seats by Party",
                text_auto=True,
            )
            fig_party.update_layout(height=360, legend_title_text="")
            st.plotly_chart(fig_party, use_container_width=True)

            st.dataframe(filtered_party, use_container_width=True, hide_index=True)
        else:
            st.info("No data for the selected filters.")

    st.markdown("---")

    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        st.subheader("Province Progress")

        if not filtered_df.empty:
            filtered_province = (
                filtered_df.groupby("province", as_index=False)
                .agg(
                    constituencies=("constituency", "count"),
                    avg_count_pct=("count_pct", "mean"),
                    total_votes=("votes", "sum"),
                )
                .sort_values("constituencies", ascending=False)
            )

            fig_province = px.bar(
                filtered_province,
                x="province",
                y="avg_count_pct",
                text_auto=".1f",
                title="Average Count Progress by Province",
            )
            fig_province.update_layout(height=350, yaxis_title="Count %")
            st.plotly_chart(fig_province, use_container_width=True)
        else:
            st.info("No province data available.")

    with bottom_right:
        st.subheader("Top Candidates")

        if not filtered_df.empty:
            top_candidates = filtered_df.sort_values("votes", ascending=False)[
                ["candidate", "party", "constituency", "votes", "status"]
            ].head(10)
            st.dataframe(top_candidates, use_container_width=True, hide_index=True)
        else:
            st.info("No candidate data available.")


def details_page():
    df = load_election_data()

    st.title("Constituency Details")
    st.caption("Seat-level drilldown using the same shared dataset as the home page.")

    st.sidebar.header("Drilldown")

    province_list = ["All"] + sorted(df["province"].unique().tolist())
    selected_province = st.sidebar.selectbox("Province", province_list, key="details_province")

    filtered_df = df.copy()
    if selected_province != "All":
        filtered_df = filtered_df[filtered_df["province"] == selected_province]

    constituency_list = filtered_df["constituency"].sort_values().tolist()
    selected_constituency = st.sidebar.selectbox(
        "Choose constituency",
        constituency_list,
        key="details_constituency",
    )

    seat = filtered_df[filtered_df["constituency"] == selected_constituency].iloc[0]

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Leading / Winner", seat["candidate"])
    top2.metric("Party", seat["party"])
    top3.metric("Votes", f"{int(seat['votes']):,}")
    top4.metric("Margin", f"{int(seat['margin']):,}")

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Seat Summary")

        summary_df = pd.DataFrame([
            {"Field": "Constituency", "Value": seat["constituency"]},
            {"Field": "Province", "Value": seat["province"]},
            {"Field": "District", "Value": seat["district"]},
            {"Field": "Candidate", "Value": seat["candidate"]},
            {"Field": "Party", "Value": seat["party"]},
            {"Field": "Status", "Value": seat["status"]},
            {"Field": "Count Progress", "Value": f"{seat['count_pct']}%"},
            {"Field": "Votes", "Value": f"{int(seat['votes']):,}"},
            {"Field": "Runner-up", "Value": seat["runner_up"]},
            {"Field": "Runner-up Party", "Value": seat["runner_up_party"]},
            {"Field": "Runner-up Votes", "Value": f"{int(seat['runner_up_votes']):,}"},
            {"Field": "Margin", "Value": f"{int(seat['margin']):,}"},
        ])

        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Vote Comparison")

        compare_df = pd.DataFrame({
            "Candidate": [seat["candidate"], seat["runner_up"]],
            "Party": [seat["party"], seat["runner_up_party"]],
            "Votes": [seat["votes"], seat["runner_up_votes"]],
        })

        fig = px.bar(
            compare_df,
            x="Candidate",
            y="Votes",
            color="Party",
            text_auto=True,
            title=f"{seat['constituency']} Vote Comparison",
        )
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    bottom_left, bottom_right = st.columns(2)

    with bottom_left:
        st.subheader("All Constituencies")
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
        st.dataframe(table_df, use_container_width=True, hide_index=True)

    with bottom_right:
        st.subheader("Top Margins")
        margin_df = filtered_df[
            ["constituency", "candidate", "party", "margin", "status"]
        ].sort_values("margin", ascending=False).head(10)

        fig_margin = px.bar(
            margin_df,
            x="constituency",
            y="margin",
            color="party",
            text_auto=True,
            title="Highest Winning / Leading Margins",
        )
        fig_margin.update_layout(height=420)
        st.plotly_chart(fig_margin, use_container_width=True)


home = st.Page(home_page, title="Dashboard", icon="🗳️")
details = st.Page(details_page, title="Details", icon="📍")

pg = st.navigation([home, details])
pg.run()
