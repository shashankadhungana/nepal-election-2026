from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from data import load_election_data, load_fetch_status

st.set_page_config(
    page_title="Nepal Election Results 2026 🔔",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="collapsed",
)

TOTAL_HOUSE_SEATS = 275
MAJORITY_NEEDED = 138

PARTY_COLORS = {
    "Rastriya Swatantra Party": "#4F46E5", 
    "Nepali Congress": "#2563EB",
    "CPN-UML": "#F59E0B", 
    "Maoist Centre": "#EF4444"
}

PARTY_SYMBOLS = {
    "Rastriya Swatantra Party": "🔔", 
    "Nepali Congress": "🌳",
    "CPN-UML": "☀️", 
    "Maoist Centre": "⚒️"
}

def simple_css():
    st.markdown("""
    <style>
    .big-number { font-size: 3rem !important; font-weight: 900 !important; }
    .main-metric { background: white; border-radius: 20px; padding: 1.5rem; }
    .simple-card { background: white; border-radius: 16px; padding: 1.5rem; margin: 1rem 0; }
    .party-chip { padding: 0.5rem 1rem; border-radius: 25px; font-weight: bold; margin: 0.2rem; }
    </style>
    """, unsafe_allow_html=True)

def clean_data(df):
    if df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    df['party'] = df['party'].fillna('Independent')
    df['votes'] = pd.to_numeric(df['votes'], errors='coerce').fillna(0).astype(int)
    df['status'] = df['status'].fillna('Leading').replace('Counting', 'Leading')
    return df

def show_status(fetch_status):
    time = fetch_status.get('last_attempt_utc', 'Unknown')
    rows = fetch_status.get('row_count', 0)
    st.markdown(f"""
    <div style='background: linear-gradient(90deg, #ef4444, #fb7185); color: white; padding: 1rem; border-radius: 12px; text-align: center;'>
        <h2>🔴 LIVE UPDATES</h2>
        <p>Updated: {time} | Showing {rows:,} races</p>
    </div>
    """, unsafe_allow_html=True)

def hero_section(df):
    if df.empty: return
    
    # Simple counts
    total_races = len(df)
    won_races = len(df[df['status'] == 'Won'])
    top_party = df['party'].value_counts().index[0]
    top_count = df['party'].value_counts().iloc[0]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="main-metric">
            <h3>Total Races</h3>
            <div class="big-number">{total_races:,}</div>
            <p>of 165 seats</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="main-metric">
            <h3>Seats Won</h3>
            <div class="big-number">{won_races:,}</div>
            <p>officially declared</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="main-metric">
            <h3>Leading Party</h3>
            <div style="font-size: 2rem; font-weight: 900;">{PARTY_SYMBOLS.get(top_party, '⭐')} {top_party}</div>
            <p>{top_count} seats</p>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="main-metric">
            <h3>Majority Needed</h3>
            <div class="big-number">{MAJORITY_NEEDED}</div>
            <p>out of 275 total</p>
        </div>
        """, unsafe_allow_html=True)

def simple_totals(df):
    st.markdown('<div class="simple-card">', unsafe_allow_html=True)
    st.markdown('<h3>🏛️ Current Results</h3>')
    
    party_wins = df[df['status'] == 'Won']['party'].value_counts().head(5)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Races with results", f"{len(df):,}", f"{len(df[df['status'] == 'Won']):,} won")
    with col2:
        st.metric("Top party gap to majority", party_wins.iloc[0], f"{MAJORITY_NEEDED - party_wins.iloc[0]} needed")
    
    # Simple bar chart
    fig = px.bar(party_wins.head(8), text_auto=True, color=party_wins.index)
    fig.update_layout(height=400, showlegend=False, title="Seats Won by Party")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def hot_races(df):
    st.markdown('<div class="simple-card">', unsafe_allow_html=True)
    st.markdown('<h3>🔥 Closest Races</h3>')
    
    close_races = (df.sort_values('margin').head(8)
                  .rename(columns={
                      'constituency': 'Race', 
                      'candidate': 'Leader', 
                      'party': 'Party',
                      'votes': 'Votes',
                      'margin': 'Lead by'
                  })[['Race', 'Leader', 'Party', 'Votes', 'Lead by']])
    
    st.dataframe(close_races, use_container_width=True, height=400)
    st.markdown('</div>', unsafe_allow_html=True)

def search_table(df):
    st.markdown('<div class="simple-card">', unsafe_allow_html=True)
    st.markdown('<h3>📊 All Results</h3>')
    
    search = st.text_input("Search races, candidates, or parties")
    
    if search:
        df = df[df.apply(lambda row: search.lower() in ' '.join(row.astype(str)).lower(), axis=1)]
    
    simple_df = df[['constituency', 'district', 'candidate', 'party', 'votes', 'status']].head(50)
    st.dataframe(simple_df, use_container_width=True, height=500)
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    simple_css()
    st_autorefresh(interval=30 * 1000)
    
    df = clean_data(load_election_data())
    status = load_fetch_status()
    
    st.title("🇳🇵 Nepal Election Results 2026")
    show_status(status)
    
    if df.empty:
        st.error("No data available yet. Check back soon!")
        return
    
    hero_section(df)
    simple_totals(df)
    hot_races(df)
    search_table(df)

if __name__ == "__main__":
    main()
