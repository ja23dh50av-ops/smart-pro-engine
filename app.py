import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime

# Page Configuration
st.set_page_config(page_title="R J SNACKS - Live Rocket Breakout Scanner", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; background-color: #ff9800; color: white; }
    .stButton>button:hover { background-color: #e68900; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Live Rocket Breakout Scanner (TradingView Logic)")
st.markdown("---")

# Sidebar Filters matching your TradingView Screener
st.sidebar.header("⚙️ Screener Filters (Live)")
min_price = st.sidebar.number_input("Min Price (INR)", value=300)
max_price = st.sidebar.number_input("Max Price (INR)", value=1200)
min_rsi = st.sidebar.slider("Min RSI (14)", 40, 70, 55)
max_rsi = st.sidebar.slider("Max RSI (14)", 70, 90, 75)
min_rel_vol = st.sidebar.slider("Min Relative Volume", 1.0, 5.0, 2.0)

scan_btn = st.sidebar.button("🔍 Scan Live Rocket Stocks")

# Popular NSE Stocks Universe to scan live
nse_watchlist = [
    "SUNTV.NS", "KTKBANK.NS", "HINDPETRO.NS", "RELIANCE.NS", "TCS.NS", 
    "INFY.NS", "SBIN.NS", "TATAMOTORS.NS", "ITC.NS", "ICICIBANK.NS", 
    "AXISBANK.NS", "LT.NS", "BHARTIARTL.NS", "BAJFINANCE.NS", "MARUTI.NS",
    "TITAN.NS", "ASIANPAINT.NS", "HINDUNILVR.NS", "NTPC.NS", "POWERGRID.NS"
]

@st.cache_data(ttl=300)
def fetch_and_filter_stocks(min_p, max_p, rsi_lo, rsi_hi, min_rv):
    rocket_list = []
    
    for ticker in nse_watchlist:
        try:
            df = yf.download(ticker, period="6mo", interval="1d", progress=False)
            if df.empty or len(df) < 200:
                continue
                
            # Flatten multi-index columns if returned by yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close = df['Close']
            volume = df['Volume']
            
            cmp = float(close.iloc[-1])
            
            # 1. Price Filter (300 to 1200)
            if not (min_p <= cmp <= max_p):
                continue
                
            # 2. Moving Averages (Price > EMA 50 and EMA 200)
            ema_50 = float(close.ewm(span=50, adjust=False).mean().iloc[-1])
            ema_200 = float(close.ewm(span=200, adjust=False).mean().iloc[-1])
            
            if not (cmp > ema_50 and cmp > ema_200):
                continue
                
            # 3. RSI (14) Calculation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = float(rsi.iloc[-1])
            
            if not (rsi_lo <= current_rsi <= rsi_hi):
                continue
                
            # 4. Volume & Relative Volume Check
            avg_vol_20 = float(volume.rolling(window=20).mean().iloc[-1])
            current_vol = float(volume.iloc[-1])
            rel_vol = current_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
            
            if rel_vol < min_rv:
                continue
                
            # 5. 3M High Breakout Check (Price near 3-month high)
            high_3m = float(close.rolling(window=60).max().iloc[-1])
            if cmp < (high_3m * 0.96): # Within 4% of 3M high
                continue
                
            chg_pct = float(((cmp - float(close.iloc[-2])) / float(close.iloc[-2])) * 100)
            
            rocket_list.append({
                "Symbol": ticker.replace(".NS", ""),
                "CMP (INR)": round(cmp, 2),
                "Chg %": round(chg_pct, 2),
                "RSI (14)": round(current_rsi, 2),
                "Rel Vol": round(rel_vol, 2),
                "EMA 50": round(ema_50, 2),
                "EMA 200": round(ema_200, 2),
                "3M High": round(high_3m, 2)
            })
            
        except Exception as e:
            continue
            
        return pd.DataFrame(rocket_list)

if scan_btn or True:
    with st.spinner("Scanning NSE live market for rocket breakout stocks using your TradingView filters..."):
        df_result = fetch_and_filter_stocks(min_price, max_price, min_rsi, max_rsi, min_rel_vol)
        
    if df_result is not None and not df_result.empty:
        st.success(f"🎯 Found {len(df_result)} Live Rocket Breakout Stocks matching your criteria!")
        st.dataframe(df_result, use_container_width=True)
    else:
        st.warning("⚠️ No stocks matched the strict filter criteria right now, or market data is syncing. Try adjusting the RSI or Price range slightly.")
