import streamlit as st
import pandas as pd
import time
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="🇳🇵 Nepal Election 2082 LIVE",
    page_icon="🇳🇵",
    layout="wide",
    page_title="Live Election Dashboard"
)

# Simulated live data generator (replace with real API)
@st.cache_data(ttl=10)
def fetch_live_data():
    np.random.seed(int(time.time() // 10))  # Deterministic but changing
    provinces = ["Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]
    major_parties = ["Nepali Congress", "CPN-UML", "Rastriya Swatantra", "Maoist Centre", "Independent"]
    
    data = []
    for province in provinces:
        for i in range(np.random.randint(8, 20)):
            party = np.random.choice(major_parties)
            seats_won = np.random.randint(0, 3)
            seats_leading = np.random.choice([0, 1, 2], p=[0.6, 0.3, 0.1])
            votes = np.random.randint(50000, 300000)
            data.append({
                "province": province,
                "party": party,
                "seats_won": seats_won,
                "seats_leading": seats_leading,
                "votes": votes,
                "update_time": datetime.now()
            })
    return pd.DataFrame(data)

# App
st.title("🇳🇵 Nepal Election 2082 LIVE COUNTDOWN")
st.markdown("**Real-time FPTP results | 165 seats | Auto-refresh every 10s** 🎯")

# Real-time loop with animation-friendly updates
placeholder = st.empty()
refresh_col, last_update_col = st.columns([3, 1])

with refresh_col:
    if st.button("🔄 Force Refresh", use_container_width=True):
        st.cache_data.clear()
with last_update_col:
    st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))

# Main live content
with placeholder.container():
    df = fetch_live_data()
    
    # Animated KPIs with deltas (built-in animation)
    col1, col2, col3, col4 = st.columns(4)
    
    total_won = df["seats_won"].sum()
    total_leading = df["seats_leading"].sum()
    total_declared = total_won + total_leading
    top_votes = df["votes"].max()
    
    col1.metric("Seats Won 🏆", f"{total_won:,}", delta="+2")  # Animated delta
    col2.metric("Seats Leading ⚡", f"{total_leading:,}", delta="+1")
    col3.metric("Declared /165", f"{total_declared:,}", f"{165-total_declared:,} left")
    col4.metric("Top Constituency", f"{top_votes:,}", delta="+15k")
    
    # Confetti on milestones
    if total_declared >= 100:
        st.balloons()  # Or st.snow() for snow effect
    
    # Leaderboard with animation-ready bar chart
    party_summary = (
        df.groupby("party")[["seats_won", "seats_leading"]].sum()
        .assign(total=lambda x: x.sum(axis=1))
        .sort_values("total", ascending=False).head(8)
        .reset_index()
    )
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.subheader("🏅 Live Party Leaderboard")
        fig_leader = px.bar(
            party_summary, x="total", y="party", orientation="h",
            title="Seats (Won + Leading)",
            color="total", color_continuous_scale="RdYlGn",
            text="total", height=400
        )
        fig_leader.update_traces(texttemplate="%{text}<br>(%{y})", textposition="outside")
        st.plotly_chart(fig_leader, use_container_width=True)
    
    with col_b:
        st.subheader("🔥 Hot Races")
        hot_races = df.nlargest(5, "votes")[["province", "party", "votes"]]
        st.dataframe(
            hot_races.style.format({"votes": "{:,}"}),
            use_container_width=True,
            height=300
        )
    
    # Vote trends animation (simulated line chart)
    st.subheader("📈 Vote Surge (Last 10 Updates)")
    trend_df = df.groupby("party")["votes"].sum().reset_index()
    fig_trend = px.line(
        trend_df.sort_values("votes", ascending=False).head(7),
        x="party", y="votes", markers=True,
        title="Total Votes by Party",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Footer
    st.caption("💡 Demo data simulating live counts | Real API: nepalvotes.live / result.election.gov.np")

# Auto-refresh simulation (runs every 10s in background)
time.sleep(10)
st.rerun()
