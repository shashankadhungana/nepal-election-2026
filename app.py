import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(layout="wide", page_icon="🇳🇵")
st.title("Nepal Election 2026 Live")

if st.button("Refresh"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=60)
def get_election_data():
    parties = ["NC", "UML", "RSP", "Maoist"]
    data = []
    for i in range(165):
        data.append({
            "Chhetra": i+1,
            "Party": np.random.choice(parties),
            "Votes": np.random.randint(10000, 30000),
            "Count": np.random.randint(50, 99)
        })
    return pd.DataFrame(data)

df = get_election_data()

col1, col2, col3 = st.columns(3)
col1.metric("Total Chhetra", len(df))
col2.metric("Total Votes", f"{df['Votes'].sum():,}")
col3.metric("Avg Count %", f"{df['Count'].mean():.0f}%")

st.subheader("Hot Races")
st.dataframe(df.nsmallest(10, 'Count')[["Chhetra", "Party", "Votes", "Count"]])

st.subheader("Party Summary")
party_summary = df.groupby("Party")["Votes"].sum().reset_index()
st.bar_chart(party_summary.set_index("Party"))

st.caption(f"Updated: {datetime.now().strftime('%H:%M')}")
