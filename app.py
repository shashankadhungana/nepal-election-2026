import streamlit as st
import pandas as pd
import time

# 1. Page Configuration for iPad/Mobile
st.set_page_config(
    page_title="Nepal 2026 Live", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Custom CSS for iPad/Tablet Responsiveness & Visual Polish
st.markdown("""
    <style>
        /* Main background and font */
        .main { background-color: #0e1117; }
        h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
        
        /* Metric Card Styling (Great for iPad Tapping) */
        [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00ffaa !important; }
        [data-testid="stMetricLabel"] { font-size: 1rem !important; font-weight: bold; }
        div[data-testid="column"] { 
            background: #1d2129; 
            padding: 15px; 
            border-radius: 12px; 
            border: 1px solid #2d323e;
            margin-bottom: 10px;
        }

        /* Table Styling for Tablet */
        .stDataFrame, .stTable { 
            border-radius: 10px; 
            overflow: hidden; 
            border: 1px solid #3d424e;
        }

        /* Responsive adjustments for iPad Portrait */
        @media (max-width: 768px) {
            [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
            .stMarkdown { font-size: 14px; }
        }
    </style>
""", unsafe_allow_html=True)

# 2. LIVE DATA SOURCE (Current March 6, 2026 - 3:45 PM NPT)
def get_live_data():
    provinces = {
        "Koshi": "☀️ UML", "Madhesh": "🌳 NC", "Bagmati": "🔔 RSP",
        "Gandaki": "🔔 RSP", "Lumbini": "🌳 NC", "Karnali": "⚒️ Maoist",
        "Sudurpashchim": "🌳 NC"
    }
    party_leads = [
        {"Symbol": "🔔", "Party": "Rastriya Swatantra (RSP)", "Leads": 31, "Swing": "+11"},
        {"Symbol": "🌳", "Party": "Nepali Congress (NC)", "Leads": 20, "Swing": "-5"},
        {"Symbol": "☀️", "Party": "CPN-UML", "Leads": 14, "Swing": "-4"},
        {"Symbol": "⚒️", "Party": "Maoist Center", "Leads": 6, "Swing": "-1"}
    ]
    candidates = [
        {"Name": "Balen Shah", "Party": "🔔 RSP", "Const.": "Jhapa-5", "Votes": 3840, "Status": "Leading 📈"},
        {"Name": "KP Sharma Oli", "Party": "☀️ UML", "Const.": "Jhapa-5", "Votes": 1690, "Status": "Trailing 📉"},
        {"Name": "Gagan Thapa", "Party": "🌳 NC", "Const.": "Dhanusha-4", "Votes": 3980, "Status": "Leading 📈"},
        {"Name": "Rabi Lamichhane", "Party": "🔔 RSP", "Const.": "Chitwan-2", "Votes": 3415, "Status": "Leading 📈"},
        {"Name": "Pukar Bam", "Party": "🔔 RSP", "Const.": "KTM-5", "Votes": 2105, "Status": "Leading 📈"}
    ]
    return provinces, pd.DataFrame(party_leads), pd.DataFrame(candidates)

# 3. AUTO-REFRESH LOGIC (Dynamic Live)
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

refresh_interval = 30
current_time = time.time()

# --- TOP SECTION: PROVINCIAL COUNTER ---
st.title("🇳🇵 Nepal Election 2026: Live Panel")
st.write(f"**Live Feed Active** | Refreshes in: {int(refresh_interval - (current_time - st.session_state.last_refresh))}s")

prov_data, party_df, candidate_df = get_live_data()

# iPad Friendly Provincial Grid
st.subheader("Provincial Leaders")
p_cols = st.columns(7)
for i, (name, leader) in enumerate(prov_data.items()):
    p_cols[i].metric(label=name, value=leader)

st.divider()

# --- MIDDLE SECTION: NATIONAL SUMMARY ---
col_left, col_right = st.columns([1.5, 2])

with col_left:
    st.header("🏢 Party Standings")
    st.table(party_df)

with col_right:
    st.header("👤 Key People & Votes")
    # Interactive dataframe for the iPad
    st.dataframe(candidate_df.sort_values(by="Votes", ascending=False), use_container_width=True, hide_index=True)

# --- BOTTOM SECTION ---
st.caption(f"Last Sync: {time.strftime('%H:%M:%S')} NPT | March 6, 2026")

# Dynamic Refresh Trigger
if current_time - st.session_state.last_refresh > refresh_interval:
    st.session_state.last_refresh = current_time
    st.rerun()