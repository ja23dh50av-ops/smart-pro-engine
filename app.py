import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime
import requests

# Page Configuration
st.set_page_config(page_title="R J SNACKS - Dhan Live Algo Terminal", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; background-color: #ff9800; color: white; }
    .stButton>button:hover { background-color: #e68900; }
    </style>
""", unsafe_allow_html=True

# Initialize Session State for Dhan Credentials
if 'client_id' not in st.session_state:
    st.session_state.client_id = "1105922505"
if 'access_token' not in st.session_state:
    st.session_state.access_token = ""
if 'trading_mode' not in st.session_state:
    st.session_state.trading_mode = False

st.title("🚀 Dhan Live API Integrated Rocket Breakout Scanner")
st.markdown("---")

# --- SIDEBAR CONTROLS & DHAN CREDENTIALS ---
st.sidebar.header("⚙️ Dhan Broker Credentials")
st.session_state.client_id = st.sidebar.text_input("Dhan Client ID", value=st.session_state.client_id)
st.session_state.access_token = st.sidebar.text_input("Dhan Access Token", type="password", value=st.session_state.access_token)

st.sidebar.markdown("---")
st.sidebar.header("📊 Scanner Filters & Parameters")
min_price = st.sidebar.number_input("Min Price (INR)", value=50)
max_price = st.sidebar.number_input("Max Price (INR)", value=5000)
min_rsi = st.sidebar.slider("Min RSI (14)", 20, 70, 35)
max_rsi = st.sidebar.slider("Max RSI (14)", 60, 98, 85)
min_chg_pct = st.sidebar.slider("Min Today's Gain (%)", -5.0, 5.0, 0.2)

scan_btn = st.sidebar.button("🔄 Refresh & Scan Live Stocks")

# Watchlist with Dhan Security IDs for NSE Equity
nse_watchlist = {
    "SUNTV": "1340",
    "KTKBANK": "1993",
    "HINDPETRO": "1435",
    "RELIANCE": "2885",
    "TCS": "11536",
    "INFY": "1594",
    "SBIN": "3045",
    "TATAMOTORS": "3456",
    "ITC": "1660",
    "ICICIBANK": "4963",
    "AXISBANK": "5900",
    "LT": "11483",
    "BHARTIARTL": "10604",
    "BAJFINANCE": "317",
    "MARUTI": "10999",
    "TITAN": "3506",
    "ASIANPAINT": "236",
    "HINDUNILVR": "1394",
    "NTPC": "11630",
    "POWERGRID": "14977"
}

@st.cache_data(ttl=60)
def fetch_live_market_data(min_p, max_p, rsi_lo, rsi_hi, min_chg):
    rocket_list = []
    symbols_ns = [f"{sym}.NS" for sym in nse_watchlist.keys()]
    
    try:
        data = yf.download(symbols_ns, period="1mo", interval="1d", group_by='ticker', progress=False)
        
        for sym, sec_id in nse_watchlist.items():
            ticker = f"{sym}.NS"
            try:
                df = data[ticker].dropna() if len(symbols_ns) > 1 else data.dropna()
                if df.empty or len(df) < 15:
                    continue
                
                close = df['Close']
                volume = df['Volume']
                
                cmp = float(close.iloc[-1])
                prev_close = float(close.iloc[-2])
                
                if not (min_p <= cmp <= max_p):
                    continue
                    
                chg_pct = float(((cmp - prev_close) / prev_close) * 100)
                if chg_pct < min_chg:
                    continue
                    
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                current_rsi = float(rsi.iloc[-1])
                
                if not (rsi_lo <= current_rsi <= rsi_hi):
                    continue
                    
                signal = "BUY" if chg_pct > 0 else "SELL"
                decision = "Confirmed" if abs(chg_pct) > 1.0 else "Watching"
                
                if signal == "BUY":
                    entry_cmp = round(cmp, 2)
                    sl = round(cmp * 0.985, 2)
                    target1 = round(cmp * 1.025, 2)
                    target2 = round(cmp * 1.045, 2)
                    risk = entry_cmp - sl
                    reward = target1 - entry_cmp
                    rr = f"1 : {round(reward/risk, 2)}" if risk > 0 else "1 : 1.5"
                else:
                    entry_cmp = round(cmp, 2)
                    sl = round(cmp * 1.015, 2)
                    target1 = round(cmp * 0.975, 2)
                    target2 = round(cmp * 0.955, 2)
                    risk = sl - entry_cmp
                    reward = entry_cmp - target1
                    rr = f"1 : {round(reward/risk, 2)}" if risk > 0 else "1 : 1.5"

                rocket_list.append({
                    "Symbol": sym,
                    "Security ID": sec_id,
                    "BUY/SELL": signal,
                    "Entry CMP": entry_cmp,
                    "CMP": round(cmp, 2),
                    "Decision": decision,
                    "RR": rr,
                    "SL": sl,
                    "Target 1": target1,
                    "Target 2": target2,
                    "Gain/Loss %": round(chg_pct, 2)
                })
            except Exception:
                continue
    except Exception:
        pass
        
    return pd.DataFrame(rocket_list)

# Function to execute live order via Dhan API v2
def place_dhan_live_order(client_id, access_token, transaction_type, quantity, security_id):
    try:
        url = "https://api.dhan.co/v2/orders"
        headers = {
            "access-token": access_token,
            "client-id": client_id,
            "Content-Type": "application/json"
        }
        payload = {
            "dhanClientId": client_id,
            "correlationId": "rj_rocket_1",
            "transactionType": transaction_type, # "BUY" or "SELL"
            "exchangeSegment": "NSE_EQ",
            "productType": "INTRADAY",
            "orderType": "MARKET",
            "validity": "DAY",
            "securityId": str(security_id),
            "quantity": int(quantity),
            "disclosedQuantity": 0,
            "price": 0,
            "triggerPrice": 0
        }
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            res_data = response.json()
            return True, res_data.get("orderId", "SUCCESS")
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

if scan_btn or True:
    with st.spinner("Scanning live NSE market and calculating targets..."):
        df_result = fetch_live_market_data(min_price, max_price, min_rsi, max_rsi, min_chg_pct)
        
    if df_result is not None and not df_result.empty:
        st.success(f"🎯 Live Market Scan Complete — Found {len(df_result)} Breakout Stocks")
        
        def color_signals(val):
            if val == "BUY":
                return 'color: #4caf50; font-weight: bold;'
            elif val == "SELL":
                return 'color: #f44336; font-weight: bold;'
            return ''

        st.dataframe(
            df_result.style.map(color_signals, subset=['BUY/SELL']),
            use_container_width=True,
            height=400
        )
    else:
        st.warning("⚠️ No stocks matched current filters. Adjust parameters in the sidebar.")

st.markdown("---")
st.subheader("⚡ Dhan Live API Order Execution Terminal")

# Trading Engine On/Off Switch
st.session_state.trading_mode = st.toggle("🚀 ENABLE DHAN LIVE TRADING ENGINE", value=st.session_state.trading_mode)

exec_col1, exec_col2, exec_col3, exec_col4 = st.columns(4)

with exec_col1:
    available_symbols = df_result["Symbol"].tolist() if df_result is not None and not df_result.empty else list(nse_watchlist.keys())
    selected_stock = st.selectbox("Select Stock Symbol to Trade", available_symbols)
with exec_col2:
    order_action = st.radio("Action", ["BUY", "SELL"], horizontal=True)
with exec_col3:
    order_qty = st.number_input("Quantity / Shares", value=10, min_value=1)
with exec_col4:
    st.markdown("<br>", unsafe_allow_html=True)
    place_trade = st.button("🔥 FIRE LIVE ORDER TO DHAN", type="primary")

if place_trade:
    if not st.session_state.trading_mode:
        st.error("❌ ERROR: Please turn ON the **ENABLE DHAN LIVE TRADING ENGINE** toggle above before placing live orders!")
    elif not st.session_state.access_token:
        st.error("❌ ERROR: Please enter your Dhan Access Token in the sidebar!")
    else:
        # Get Security ID for selected stock
        sec_id = nse_watchlist.get(selected_stock, "2885")
        with st.spinner(f"Firing {order_action} order for {selected_stock} via Dhan API..."):
            success, msg = place_dhan_live_order(
                st.session_state.client_id,
                st.session_state.access_token,
                order_action,
                order_qty,
                sec_id
            )
            if success:
                st.success(f"🎉 LIVE ORDER PLACED SUCCESSFULLY VIA DHAN! Order ID: {msg}")
            else:
                st.error(f"❌ Dhan API Error: {msg}")
