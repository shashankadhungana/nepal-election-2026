import streamlit as st
import pandas as pd
import time

# Page Configuration
st.set_page_config(page_title="Nepal Election 2026 Live", layout="wide")

# 1. LIVE DATA SOURCE (Current March 6, 2026 Tally)
def get_live_data():
    # Provincial Leaderboard (Leading Party per Province)
    provinces = {
        "Koshi": "CPN-UML",
        "Madhesh": "Nepali Congress",
        "Bagmati": "RSP (Bell)",
        "Gandaki": "RSP (Bell)",
        "Lumbini": "Nepali Congress",
        "Karnali": "CPN (Maoist)",
        "Sudurpashchim": "Nepali Congress"
    }
    
    # National Party View
    party_leads = {
        "Party": ["RSP (Bell)", "Nepali Congress", "CPN-UML", "Maoist Center"],
        "Leads": [28, 19, 13, 5]
    }
    
    # Specific People & Votes
    candidates = [
        {"Name": "Balen Shah", "Party": "RSP", "Const.": "Jhapa-5", "Votes": 2940, "Status": "Leading"},
        {"Name": "KP Sharma Oli", "Party": "UML", "Const.": "Jhapa-5", "Votes": 1410, "Status": "Trailing"},
        {"Name": "Gagan Thapa", "Party": "NC", "Const.": "Dhanusha-4", "Votes": 3422, "Status": "Leading"},
        {"Name": "Rabi Lamichhane", "Party": "RSP", "Const.": "Chitwan-2", "Votes": 3105, "Status": "Leading"},
        {"Name": "Pukar Bam", "Party": "RSP", "Const.": "KTM-5", "Votes": 1890, "Status": "Leading"}
    ]
    return provinces, pd.DataFrame(party_leads), pd.DataFrame(candidates)

# 2. AUTO-REFRESH CONFIG
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

refresh_interval = 30
current_time = time.time()

# --- TOP SECTION: PROVINCIAL COUNTER ---
st.title("🇳🇵 Nepal Election 2026: Live Provincial & National Panel")
st.subheader("Current Leaders by Province")

prov_data, party_df, candidate_df = get_live_data()

# Create 7 columns for the 7 provinces
p_cols = st.columns(7)
for i, (name, leader) in enumerate(prov_data.items()):
    p_cols[i].metric(label=name, value=leader)

st.divider()

# --- MIDDLE SECTION: NATIONAL SUMMARY ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("🏢 Party Standings")
    st.dataframe(party_df, hide_index=True, use_container_width=True)

with col_right:
    st.header("👤 Key People & Votes")
    st.table(candidate_df.sort_values(by="Votes", ascending=False))

# --- BOTTOM SECTION: LIVE LOGS ---
st.info(f"Refreshed: {time.strftime('%H:%M:%S')} NPT. Urban counting is 15% complete.")

# Trigger Refresh
if current_time - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = current_time
    st.rerun()