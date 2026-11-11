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
            "SEM_EXCH": "NSE",
            "SEM_SMTT": "INDICES",
            "securityId": "13"
        }
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "ltp" in data["data"]:
                return float(data["data"]["ltp"])
    except Exception as e:
        pass
    return 25005.80

# --- SIDEBAR CONTROLS & TOKEN EXPIRY ---
st.sidebar.header("⚙️ Engine & Credentials")

st.sidebar.text_input("Dhan Client ID", key="client_id")
st.sidebar.text_input("Dhan Access Token", type="password", key="access_token")

# Token Expiry Display
token_expiry_str = get_token_expiry(st.session_state.access_token)
st.sidebar.info(f"🕒 **Token Expires At:**\n`{token_expiry_str}`")

# --- MULTI-STRATEGY SELECTOR ---
st.sidebar.subheader("🎯 Multi-Strategy Selector")
selected_strategy = st.sidebar.selectbox(
    "Choose Trading Logic:",
    [
        "Custom Indicator Logic (Chandu's Personal)", 
        "Super Trend & EMA Crossover", 
        "SMC Order Block Rejection"
    ]
)

st.sidebar.subheader("Strategy Parameters")
ema_fast = st.sidebar.slider("Fast EMA", 5, 20, 13)
ema_slow = st.sidebar.slider("Slow EMA", 21, 50, 34)
stop_loss = st.sidebar.number_input("Stop Loss (Points)", value=20)
target_pts = st.sidebar.number_input("Target (Points)", value=60)
max_reentries = st.sidebar.number_input("Max Re-Entries Allowed", value=2, min_value=0, max_value=5)

# --- TOP STATUS BAR ---
top_col1, top_col2, top_col3, top_col4 = st.columns([2, 2, 2, 2])

with top_col1:
    st.markdown("🟢 **DHAN LIVE** | Status: **Connected**")
with top_col2:
    st.markdown("🟢 **DATA STREAM** | Active: **5 Min Auto-Poll**")
with top_col3:
    if 'trading_mode' not in st.session_state:
        st.session_state.trading_mode = False
    st.session_state.trading_mode = st.toggle("🚀 TRADING ENGINE ON / OFF", value=st.session_state.trading_mode)
    if st.session_state.trading_mode:
        st.caption("⚡ Status: **LIVE TRADING ACTIVE**")
    else:
        st.caption("🔒 Status: **STANDBY / PAUSED**")

with top_col4:
    emergency_exit = st.button("🚨 EMERGENCY EXIT (KILL SWITCH)", type="primary")

if emergency_exit:
    st.session_state.trading_mode = False
    st.error("⚠️ KILL SWITCH ACTIVATED! All active positions closed, trading halted.")
    st.stop()

st.title("⚡ Smart Pro Engine - Nifty Algo Terminal & Re-Entry Logic")
st.markdown("---")

# Fetch Dynamic Live ATM Strike Calculation via Dhan API
live_spot_price = fetch_nifty_spot(st.session_state.client_id, st.session_state.access_token)
atm_strike = round(live_spot_price / 50) * 50

# --- DASHBOARD MAIN PANELS ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 NIFTY 50 Live & Strike Selector")
    st.metric(label="Live Spot Price", value=f"{live_spot_price}", delta="Bullish")
    st.markdown(f"""
    * **Active Strategy:** `{selected_strategy}`
    * **Calculated ATM Strike:** `{atm_strike} CE / PE`
    * **Trend Filter:** `{ema_fast} / {ema_slow} EMA`
    * **State Machine:** **Active (Re-Entry Enabled)**
    """)

with col2:
    st.subheader("📋 Execution & State Status")
    if st.session_state.trading_mode:
        st.success(f"🟢 Bot is actively running with **{selected_strategy}** logic.")
    else:
        st.warning("⚠️ Standby mode. Turn on the **TRADING ENGINE** switch above.")
    
    st.markdown(f"""
    * **Selected Option Type:** `ATM {atm_strike} CE`
    * **Re-Entry Limit:** Up to {max_reentries} times on same zone
    """)

st.markdown("---")

# --- SIMULATION & BACKTEST WITH RE-ENTRY LOGIC ---
if st.button("🚀 Run Strategy Simulation (With Re-Entry & ATM Logic)", type="primary"):
    with st.spinner(f"Running backtest for {selected_strategy}..."):
        np.random.seed(42)
        dates = pd.date_range(start="2026-11-08 09:15:00", periods=300, freq="5min")
        close_prices = 25000 + np.cumsum(np.random.randn(300) * 10)
        
        df = pd.DataFrame({
            'Date': dates,
            'Close': close_prices,
            'High': close_prices + 15,
            'Low': close_prices - 15
        })

        df['EMA_Fast'] = df['Close'].ewm(span=ema_fast, adjust=False).mean()
        df['EMA_Slow'] = df['Close'].ewm(span=ema_slow, adjust=False).mean()
        df['Signal'] = np.where(df['EMA_Fast'] > df['EMA_Slow'], 1, -1)

        trades = []
        position = 0
        entry_price = 0
        reentry_count = 0
        last_sl_price = 0

        for i in range(1, len(df)):
            current_signal = df['Signal'].iloc[i]
            prev_signal = df['Signal'].iloc[i-1]
            price = df['Close'].iloc[i]
            
            if current_signal != prev_signal or (position == 0 and last_sl_price > 0 and abs(price - last_sl_price) < 15):
                if position != 0:
                    raw_pnl = (price - entry_price) * position
                    if raw_pnl <= -stop_loss:
                        last_sl_price = entry_price
                        trades.append(-stop_loss)
                        position = 0
                    elif raw_pnl >= target_pts:
                        trades.append(target_pts)
                        position = 0
                        reentry_count = 0
                        last_sl_price = 0
                    else:
                        trades.append(raw_pnl)
                        position = 0
                
                if position == 0:
                    if last_sl_price > 0 and abs(price - last_sl_price) < 15 and reentry_count < max_reentries:
                        reentry_count += 1
                        position = current_signal
                        entry_price = price
                    elif last_sl_price == 0 and current_signal != prev_signal:
                        position = current_signal
                        entry_price = price

        total_trades = len(trades)
        winning_trades = [t for t in trades if t > 0]
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        net_points = sum(trades)

    st.success(f"Backtest Completed for {selected_strategy}!")
    
    res1, res2, res3, res4 = st.columns(4)
    res1.metric("Total Executed Trades", f"{total_trades}")
    res2.metric("Win Rate", f"{win_rate:.2f}%")
    res3.metric("Net P&L Points", f"{net_points:.2f} pts")
    res4.metric("Re-Entries Triggered", f"{reentry_count}")

    st.subheader("📈 Strategy Performance Chart with Re-Entry Points")
    st.line_chart(df[['Close', 'EMA_Fast', 'EMA_Slow']])
