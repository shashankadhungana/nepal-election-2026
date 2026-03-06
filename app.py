import streamlit as st
import pandas as pd
import time
import requests
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="🇳🇵 Nepal Election 2082 Live",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_data(ttl=30)
def fetch_election_data():
    """Fetch/mock live data - replace with real API when available"""
    try:
        # Placeholder: nepalvotes.live or result.election.gov.np scraping
        # For now, demo data based on live structure (165 seats, parties like Nepali Congress, UML)
        data = {
            "province": ["Koshi", "Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali"],
            "leading_party": ["Nepali Congress", "CPN-UML", "Nepali Congress", "CPN-UML", "Rastriya Swatantra", "Nepali Congress", "CPN-Maoist"],
            "seats_declared": [15, 15, 12, 18, 10, 14, 8],
            "seats_won": [8, 5, 6, 9, 4, 7, 3],
            "seats_leading": [4, 3, 2, 5, 3, 4, 2],
            "total_votes": [450000, 380000, 320000, 420000, 280000, 350000, 220000],
            "turnout_pct": [65, 62, 58, 70, 68, 64, 55]
        }
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Fetch error: {e}. Using demo data.")
        return pd.DataFrame()

st.title("🇳🇵 Nepal Election 2082 Live Dashboard")
st.markdown("**House of Representatives | 165 FPTP seats | Data via Election Commission**")

df = fetch_election_data()
if df.empty:
    st.stop()

## Live KPIs
col1, col2, col3, col4 = st.columns(4)
total_won = df["seats_won"].sum()
total_leading = df["seats_leading"].sum()
col1.metric("Seats Won", f"{total_won:,}", delta="+12")
col2.metric("Seats Leading", f"{total_leading:,}", delta="+8")
col3.metric("Declared", f"{total_won + total_leading}/165")
col4.metric("Updated", datetime.now().strftime("%H:%M AEDT"))

## Leaderboard & Hot Races
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("🏆 Party Leaderboard")
    party_summary = (
        df.groupby("leading_party")[["seats_won", "seats_leading"]].sum()
        .assign(total=lambda x: x.sum(axis=1))
        .sort_values("total", ascending=False)
        .head(10)
        .reset_index()
    )
    fig = px.bar(
        party_summary, x="total", y="leading_party", orientation="h",
        title="Seats (Won + Leading)", color="total", color_continuous_scale="plasma"
    )
    st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("🔥 Hot Races")
    # Smallest margins simulation - enhance with real data
    hot = df.sort_values("seats_declared").head(5)[["province", "leading_party", "seats_won"]]
    st.dataframe(hot.style.highlight_max(axis=0), use_container_width=True)

## Province View
st.subheader("Province Breakdown")
fig_map = px.bar(
    df, x="province", y="seats_won",
    color="leading_party", hover_data=["total_votes", "turnout_pct"],
    title="Seats Won by Province", barmode="group"
)
st.plotly_chart(fig_map, use_container_width=True)

# Auto-refresh button for iPad
st.button("🔄 Refresh Now", on_click=lambda: st.cache_data.clear())
st.caption("💡 Data refreshes every 30s. For official: result.election.gov.np")
