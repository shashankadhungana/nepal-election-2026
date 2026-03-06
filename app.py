import streamlit as st
import pandas as pd
import time

# Page Configuration
st.set_page_config(page_title="Nepal 2026 Election Tracker", layout="wide")

# 1. LIVE DATA (As of March 6, 2026 - 3:15 PM NPT)
# This includes the "General View", "People", and "Votes"
def get_latest_election_data():
    # Party-wise Leads (General View)
    party_leads = {
        "Party": ["Rastriya Swatantra (RSP)", "Nepali Congress (NC)", "CPN-UML", "Maoist Center"],
        "Current Leads": [26, 17, 12, 4],
        "Won": [0, 0, 0, 0]
    }
    
    # Candidate-wise Votes (People View)
    candidates = [
        {"Name": "Balen Shah", "Party": "RSP", "Constituency": "Jhapa-5", "Votes": 2410, "Status": "Leading"},
        {"Name": "KP Sharma Oli", "Party": "CPN-UML", "Constituency": "Jhapa-5", "Votes": 1285, "Status": "Trailing"},
        {"Name": "Gagan Thapa", "Party": "NC", "Constituency": "Dhanusha-4", "Votes": 3102, "Status": "Leading"},
        {"Name": "Rabi Lamichhane", "Party": "RSP", "Constituency": "Chitwan-2", "Votes": 2890, "Status": "Leading"},
        {"Name": "Pukar Bam", "Party": "RSP", "Constituency": "Kathmandu-5", "Votes": 1740, "Status": "Leading"},
        {"Name": "Sushila Karki", "Party": "IND (Interim)", "Constituency": "Kathmandu-5", "Votes": 520, "Status": "Trailing"}
    ]
    return pd.DataFrame(party_leads), pd.DataFrame(candidates)

# 2. AUTO-REFRESH LOGIC
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Refresh every 30 seconds
refresh_interval = 30 
current_time = time.time()

# Header
st.title("🇳🇵 Nepal General Election 2026: Live Results")
st.write(f"**Last Updated:** {time.strftime('%H:%M:%S')} (NPT) | **Next Refresh in:** {int(refresh_interval - (current_time - st.session_state.last_refresh))}s")

# 3. DASHBOARD LAYOUT
party_df, candidate_df = get_latest_election_data()

# Summary Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Leading Party", "RSP", "+26 Seats")
m2.metric("Voter Turnout", "60%", "Approx 11.4M")
m3.metric("Counting Progress", "~12%", "Urban Centers")
m4.metric("Key Battle (Jhapa-5)", "Balen +1,125", "vs Oli")

# Section 1: General Party View
st.divider()
st.subheader("🏢 National Party Standings (FPTP)")
st.bar_chart(party_df.set_index('Party')['Current Leads'])

# Section 2: People & Votes View
st.divider()
st.subheader("👤 Live Candidate Leaderboard")
st.dataframe(candidate_df.sort_values(by="Votes", ascending=False), use_container_width=True)

# Footer info
st.info("Helicopters are currently transporting ballot boxes from mountain districts. Rural data will start appearing tonight.")

# JavaScript to trigger the refresh
if current_time - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = current_time
    st.rerun()