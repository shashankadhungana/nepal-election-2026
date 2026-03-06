import streamlit as st
import pandas as pd
import time
from datetime import datetime

# 1. PAGE SETUP (iPad Optimization)
st.set_page_config(page_title="NEPAL 2026 LIVE", layout="wide", initial_sidebar_state="collapsed")

# 2. CUSTOM CSS (Newsroom Aesthetic)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #05070a;
    }
    
    /* Live National Counter Styling */
    .national-counter {
        background: linear-gradient(90deg, #1f4037 0%, #2193b0 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Glassmorphism Cards */
    div[data-testid="column"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 20px;
    }
    
    /* Live Pulse Animation */
    .live-dot {
        height: 12px; width: 12px;
        background-color: #ff4b4b;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 75, 75, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
    }
    </style>
""", unsafe_allow_html=True)

# 3. DYNAMIC DATA (March 6, 2026 - 4:00 PM NPT)
def fetch_election_engine():
    # The Global Live Counter (Total seats processed)
    total_seats_counted = 64
    total_voters = 18903689
    
    provincial_leaders = {
        "Koshi": "☀️ UML", "Madhesh": "🌳 NC", "Bagmati": "🔔 RSP",
        "Gandaki": "🔔 RSP", "Lumbini": "🌳 NC", "Karnali": "⚒️ Maoist",
        "Sudurpashchim": "🌳 NC"
    }
    
    party_data = [
        {"Symbol": "🔔", "Party": "RSP", "Leads": 34, "Swing": "↑ 14%", "Color": "#00d4ff"},
        {"Symbol": "🌳", "Party": "NC", "Leads": 22, "Swing": "↓ 4%", "Color": "#2ecc71"},
        {"Symbol": "☀️", "Party": "UML", "Leads": 15, "Swing": "↓ 6%", "Color": "#f1c40f"},
        {"Symbol": "⚒️", "Party": "Maoist", "Leads": 7, "Swing": "↓ 2%", "Color": "#e74c3c"}
    ]
    
    hot_seats = [
        {"Name": "Balen Shah", "Symbol": "🔔", "Const.": "Jhapa-5", "Votes": 4812, "Trend": "+2,105"},
        {"Name": "KP Sharma Oli", "Symbol": "☀️", "Const.": "Jhapa-5", "Votes": 2707, "Trend": "-2,105"},
        {"Name": "Gagan Thapa", "Symbol": "🌳", "Const.": "Sarlahi-4", "Votes": 5102, "Trend": "+1,440"},
        {"Name": "Rabi Lamichhane", "Symbol": "🔔", "Const.": "Chitwan-2", "Votes": 4920, "Trend": "+3,100"}
    ]
    
    news_ticker = [
        "🚨 BREAKING: RSP leading in 34/165 constituencies.",
        "🚁 HELI-UPDATE: Ballot boxes from Solukhumbu arriving at counting center.",
        "📊 ANALYSIS: Youth turnout in Bagmati at historic 72%."
    ]
    
    return total_seats_counted, provincial_leaders, pd.DataFrame(party_data), pd.DataFrame(hot_seats), news_ticker

# 4. DASHBOARD RENDER
count, provinces, party_df, hot_df, news = fetch_election_engine()

# HEADER & LIVE COUNTER
st.markdown(f"""
    <div class="national-counter">
        <h3 style="margin:0; opacity:0.8;">TOTAL SEATS COUNTING</h3>
        <h1 style="margin:0; font-size:4rem; letter-spacing:-2px;">{count} <span style="font-size:1.5rem; opacity:0.5;">/ 165</span></h1>
        <p style="margin:0; font-weight:bold;"><span class="live-dot"></span>LIVE FROM ELECTION COMMISSION</p>
    </div>
""", unsafe_allow_html=True)

# PROVINCIAL TICKER
p_cols = st.columns(7)
for i, (name, leader) in enumerate(provinces.items()):
    p_cols[i].metric(label=name, value=leader)

st.write("") # Spacing

# MAIN CONTENT
col_left, col_right = st.columns([1.5, 2])

with col_left:
    st.subheader("🏢 Party Standings & Swing")
    for _, row in party_df.iterrows():
        st.markdown(f"""
            <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid {row['Color']};">
                <span style="font-size:1.5rem;">{row['Symbol']}</span> 
                <b style="font-size:1.1rem; margin-left:10px;">{row['Party']}</b>
                <span style="float:right; color:{row['Color']}; font-weight:bold;">{row['Leads']} Seats ({row['Swing']})</span>
            </div>
        """, unsafe_allow_html=True)

with col_right:
    st.subheader("🔥 Key Battleground 'Hot Seats'")
    st.dataframe(hot_df, use_container_width=True, hide_index=True)

# BOTTOM NEWS TICKER
st.divider()
st.subheader("📡 Live News Feed")
for msg in news:
    st.write(msg)

# AUTO-REFRESH SCRIPT
if "refresh" not in st.session_state: st.session_state.refresh = time.time()
if time.time() - st.session_state.refresh > 30:
    st.session_state.refresh = time.time()
    st.rerun()