import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import streamlit_autorefresh

st.set_page_config(
    page_title="Nepal Election 2082 | Live Results",
    page_icon="🇳🇵",
    layout="wide"
)

# Auto-refresh every 15s (client-side, no server load)
count = streamlit_autorefresh.st_autorefresh(interval=15000, limit=None, key="f")

@st.cache_data(ttl=300)  # 5 min cache = instant loads
def fetch_live_results():
    """Simulates real constituency data"""
    constituencies = [
        "Jhapa-5", "Chitwan-2", "Kathmandu-1", "Bhaktapur-1", "Jumla-1", "Pyuthan-1", 
        "Rautahat-1", "Kanchanpur-2", "Dang-2", "Nuwakot-1", "Rolpa-1", "Saptari-3"
    ]
    candidates = [
        "Balen Shah (RSP)", "Rabi Lamichhane (RSP)", "KP Sharma Oli (UML)", "Gagan Thapa (NC)",
        "Sobita Gautam (RSP)", "Shanti Lal Mahat (UML)", "Prakash Sharan Mahat (NC)"
    ]
    
    data = []
    np.random.seed(int(datetime.now().timestamp() // 300))
    for const in constituencies:
        for cand in np.random.choice(candidates, np.random.randint(3,6), replace=False):
            votes = np.random.randint(8000, 35000)
            margin = np.random.uniform(-5000, 5000)
            status = "Leading" if margin > 0 else "Trailing"
            data.append({
                "Constituency": const,
                "Candidate": cand,
                "Party": cand.split(" (")[1][:-1] if "(" in cand else "IND",
                "Votes": votes,
                "Margin": abs(margin),
                "Status": status,
                "Update": datetime.now().strftime("%H:%M")
            })
    return pd.DataFrame(data).sort_values("Votes", ascending=False)

st.title("🇳🇵 Nepal Election 2082")
st.markdown("**House of Representatives | Live FPTP Results | Data simulated from Election Commission**")

df = fetch_live_results()

# Header KPIs
col1, col2, col3 = st.columns(3)
total_declared = df["Constituency"].nunique()
top_votes = df["Votes"].max()
seats_projected = int(total_declared * 0.6)

with col1:
    st.metric("Constituencies Reporting", total_declared, "12")
with col2:
    st.metric("Highest Votes", f"{top_votes:,}", "+2.1k")
with col3:
    st.metric("Projected Seats (RSP)", seats_projected, "+5")

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Leaderboard", "🔥 Hot Seats", "🏛️ All Constituencies"])

with tab1:
    st.subheader("Top Candidates by Votes")
    top_df = df.nlargest(15, "Votes")[["Candidate", "Party", "Constituency", "Votes", "Status"]]
    st.dataframe(top_df.style.format({"Votes": "{:,}"}), use_container_width=True)

with tab2:
    st.subheader("Hot Seats (Closest Races)")
    hot_df = df.loc[df.groupby("Constituency")["Margin"].idxmin()].nsmallest(10, "Margin")
    hot_df = hot_df[["Constituency", "Candidate", "Party", "Votes", "Margin", "Status"]]
    fig_hot = px.bar(
        hot_df, x="Margin", y="Constituency", orientation="h",
        color="Status", title="Margin Between Leader & Runner-up",
        color_discrete_map={"Leading": "#1f77b4", "Trailing": "#ff7f0e"},
        height=500
    )
    st.plotly_chart(fig_hot, use_container_width=True)
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.metric("Tightest Race", f"{hot_df['Margin'].min():,.0f}")
    with col_h2:
        st.metric("Hot Seat Constituencies", len(hot_df))

with tab3:
    st.subheader("All Area Vote Results")
    province_filter = st.multiselect("Filter Constituency", df["Constituency"].unique(), default=df["Constituency"].unique()[:6])
    df_filtered = df[df["Constituency"].isin(province_filter)]
    
    col_sort, col_view = st.columns(2)
    with col_sort:
        sort_by = st.selectbox("Sort by", ["Votes", "Margin", "Constituency"])
    with col_view:
        show_cols = st.multiselect("Columns", df.columns, default=["Constituency", "Candidate", "Party", "Votes", "Status"])
    
    df_display = df_filtered.sort_values(sort_by, ascending=(sort_by != "Votes")).loc[:, show_cols]
    st.dataframe(df_display.style.format({"Votes": "{:,}", "Margin": "{:,.0f}"}), height=600, use_container_width=True)

st.markdown("---")
st.caption("Live simulation | Real data: nepalvotes.live, result.election.gov.np | Auto-refreshes every 15s")

if st.button("🔄 Manual Refresh"):
    st.cache_data.clear()
    st.rerun()
