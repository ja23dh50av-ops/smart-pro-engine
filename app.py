import streamlit as st
import pandas as pd
import numpy as np
import base64
import json
import datetime
import requests

# Page Configuration
st.set_page_config(page_title="Smart Pro Engine - Zero-Lag & Strike Selector", page_icon="⚡", layout="wide")

# Custom Styling for Terminal
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State (Local & Safe)
if 'client_id' not in st.session_state:
    st.session_state.client_id = "1105922505"
if 'access_token' not in st.session_state:
    st.session_state.access_token = ""

# Helper function to decode JWT token and find expiry time
def get_token_expiry(token):
    try:
        parts = token.split('.')
        if len(parts) >= 2:
            payload = parts[1]
            padded = payload + '=' * (-len(payload) % 4)
            decoded = base64.urlsafe_b64decode(padded).decode('utf-8')
            data = json.loads(decoded)
            if 'exp' in data:
                exp_timestamp = data['exp']
                exp_time = datetime.datetime.fromtimestamp(exp_timestamp)
                return exp_time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        pass
    return "Invalid or Unreadable Token"

# Function to fetch live Nifty Spot Price from Dhan API
def fetch_nifty_spot(client_id, access_token):
    try:
        url = "https://api.dhan.co/v2/marketfeed/ltp"
        headers = {
            "access-token": access_token,
            "client-id": client_id,
            "Content-Type": "application/json"
        }
        payload = {
            "SEM_
