import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
from data import load_election_data


st.set_page_config(
    page_title="Nepal Election Dashboard",
    page_icon="🗳️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st_autorefresh(interval=30 * 1000, key="election_autorefresh")

constituencies_df = load_election_data()

st.sidebar.title("Filters")

province_options = ["All"] + sorted(constituencies_df["province"].unique().tolist())
party_options = ["All"] + sorted(constituencies_df["party"].unique().tolist())
status_options = ["All"] + sorted(constituencies_df["status"].unique().tolist())

selected_province = st.sidebar.selectbox("Province", province_options)
selected_party = st.sidebar.selectbox("Party", party_options)
selected_status = st.sidebar.selectbox("Status", status_options)
search_text = st.sidebar.text_input("Search constituency, district, or candidate")

filtered_df = constituencies_df.copy()

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

st.sidebar.markdown("---")
st.sidebar.caption("Next step: connect result.election.gov.np and replace mock data.")
