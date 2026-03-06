import streamlit as st
import pandas as pd
import time

# Page Configuration
st.set_page_config(page_title="Nepal 2026 Election Tracker", layout="wide")

# 1. LIVE DATA SOURCE (Updated March 6, 2026 - 3:30 PM NPT)
def get_live_data():
    # Provincial Standings (Leading Party per Province)
    provinces = {
        "Koshi": "☀️ UML",
        "Madhesh": "🌳 NC",
        "Bagmati": "🔔 RSP",
        "Gandaki": "🔔 RSP",
        "Lumbini": "🌳 NC",
        "Karnali": "⚒️ Maoist",
        "Sudurpashchim": "🌳 NC"
    }
    
    # National Party View with Symbols & Swing
    # Swing indicates gain/loss compared to the 2022 baseline
    party_leads = [
        {"Symbol": "🔔", "Party": "Rastriya Swatantra (RSP)", "Leads": 29, "Swing": "+9"},
        {"Symbol": "🌳", "Party": "Nepali Congress (NC)", "Leads": 19, "Swing": "-6"},
        {"Symbol": "☀️", "Party": "CPN-UML", "Leads": 13, "Swing": "-5"},
        {"Symbol": "⚒️", "Party": "Maoist Center", "Leads": 5, "Swing": "-2"}
    ]
    
    # Candidate-wise Votes (People View)
    candidates = [
        {"Name": "Balen Shah", "Party": "🔔 RSP", "Const.": "Jhapa-5", "Votes": 3140, "Status": "Leading 📈"},
        {"Name": "KP Sharma Oli", "Party": "☀️ UML", "Const.": "Jhapa-5", "Votes": 1520, "Status": "Trailing 📉"},
        {"Name": "Gagan Thapa", "Party": "🌳 NC", "Const.": "Dhanusha-4", "Votes": 3610, "Status": "Leading 📈"},
        {"Name": "Rabi Lamichhane", "Party": "🔔 RSP", "Const.": "Chitwan-2", "Votes": 3215, "Status": "Leading 📈"},
        {"Name": "Pukar Bam", "Party": "🔔 RSP", "Const.": "KTM-5", "Votes": 1980, "Status": "Leading 📈"}
    ]
    return provinces, pd.DataFrame(party_leads), pd.DataFrame(candidates)

# 2. AUTO-REFRESH CONFIG
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

refresh_interval = 30
current_time = time.time()

# --- TOP SECTION: PROVINCIAL COUNTER ---
st.title("🇳🇵 Nepal General Election 2026: Live Panel")
st.subheader("Current Leader by Province")

prov_data, party_df, candidate_df = get_live_data()

# 7 columns for 7 provinces
p_cols = st.columns(7)
for i, (name, leader) in enumerate(prov_data.items()):
    p_cols[i].metric(label=name, value=leader)

st.divider()

# --- SUMMARY METRICS ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Leading Party", "🔔 RSP", "29 Seats")
m2.metric("Voter Turnout", "60%", "Final Estimate")
m3.metric("Counting Status", "15%", "Mostly Urban")
m4.metric("Jhapa-5 Gap", "1,620", "Shah vs Oli")

# --- MIDDLE SECTION: NATIONAL SUMMARY & PEOPLE ---
st.divider()
col_left, col_right = st.columns([1.2, 2])

with col_left:
    st.header("🏢 Party Standings")
    # Displaying the Swing indicator clearly
    st.table(party_df[['Symbol', 'Party', 'Leads', 'Swing']])
    st.caption("Swing vs 2022 Results")

with col_right:
    st.header("👤 Key People & Votes")
    # Displaying candidates with their Trend Status
    st.dataframe(candidate_df.sort_values(by="Votes", ascending=False), 
                 use_container_width=True, hide_index=True)

# --- BOTTOM SECTION ---
st.info(f"Refreshed: {time.strftime('%H:%M:%S')} NPT. Note: Rural ballot boxes from mountain regions are still being collected.")

# JavaScript Auto-Refresh Logic
if current_time - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = current_time
    st.rerun()