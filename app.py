import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time

st.set_page_config(layout="wide", page_icon="🇳🇵")

st.title("🇳🇵 Nepal Election 2026 LIVE Dashboard")

# Refresh button (100% compatible)
if st.button("🔄 Refresh Data (Every 30s)"):
    st.rerun()

@st.cache_data(ttl=30)
def get_data():
    # Simulate real ECN data
    data = []
    parties = ['NC', 'UML', 'RSP', 'Maoist']
    for i in range(165):
        data.append({
            'Chhetra': f'{i+1}',
            'Party': np.random.choice(parties),
            'Votes': np.random.randint(15000, 30000),
            'Count%': np.random.uniform(60, 98),
            'Status': np.random.choice(['Leading', 'Won', 'Close'])
        })
    df = pd.DataFrame(data)
    df['AI Win%'] = (df['Count%'] * 0.8 + np.random.uniform(20, 60)).round()
    return df

df = get_data()

# Live counters
col1, col2, col3 = st.columns(3)
col1.metric("Total Votes", f"{df['Votes'].sum():,}")
col2.metric("Avg Count", f"{df['Count%'].mean():.0f}%")
col3.metric("Hot Races", len(df[df['Status']=='Close']))

# Hot seats
st.subheader("🔥 Hot Seats (Close Races)")
st.dataframe(df[df['Status']=='Close'].head(10)[['Chhetra', 'Party', 'Votes', 'AI Win%']])

# Provinces
st.subheader("📊 7 Provinces")
for prov in ['Koshi', 'Madhesh', 'Bagmati', 'Gandaki', 'Lumbini', 'Karnali', 'Sudurpashchim']:
    prov_df = df.sample(20)
    st.metric(prov, prov_df['Party'].mode()[0], f"{prov_df['Count%'].mean():.0f}%")

st.markdown(f"**Updated:** {datetime.now().strftime('%H:%M AEDT')}")
