import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(layout="wide", page_icon="🇳🇵")
st.title("🇳🇵 Nepal Election 2026 LIVE")

if st.button("🔄 Update LIVE Data"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=30)
def get_live_data():
    """Scrape Nepal's live election sites"""
    data = []
    sites = [
        "https://nepalvotes.live",
        "https://election.onlinekhabar.com",
        "https://election.ekantipur.com/?lng=eng"
    ]
    
    for site in sites:
        try:
            r = requests.get(site, timeout=10)
            soup
