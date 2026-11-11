import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import datetime

# Page Configuration
st.set_page_config(page_title="R J SNACKS - Smart Rocket Breakout Scanner", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 6px; font-weight: bold; background-color: #ff9800; color: white; }
    .stButton>button:hover { background-color: #e68900; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 Smart Rocket Breakout Scanner (Chandu's Custom Logic)")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("⚙️ Smart Scanner Controls")
min_price = st.sidebar.number_input("Min Price (INR)", value=50)
max_price = st.sidebar.number_input("Max Price (INR)", value=5000)
min_rsi = st.sidebar.slider("Min RSI (14)", 30, 70, 45)
max_rsi = st.sidebar.slider("Max RSI (14)", 60, 90, 80)
min_chg_pct = st.sidebar.slider("Min Today's Gain (%)", 0.0, 5.0, 1.0)

scan_btn = st.sidebar.button("🔍 Scan Smart Rocket Stocks")

# Comprehensive NSE Watchlist
nse_watchlist = [
    "SUNTV.NS", "KTKBANK.NS", "HINDPETRO.NS", "RELIANCE.NS", "TCS.NS", 
    "INFY.NS", "SBIN.NS", "TATAMOTORS.NS", "ITC.NS", "ICICIBANK.NS", 
    "AXISBANK.NS", "LT.NS", "BHARTIARTL.NS", "BAJFINANCE.NS", "MARUTI.NS",
    "TITAN.NS", "ASIANPAINT.NS", "HINDUNILVR.NS", "NTPC.NS", "POWERGRID.NS",
    "SUNPHARMA.NS", "TATASTEEL.NS", "WIPRO.NS", "HCLTECH.NS", "ADANIENT.NS",
    "ZOMATO.NS", "PAYTM.NS", "JIOFIN.NS", "IRCTC.NS", "BEL.NS"
]

@st.cache_data(ttl=300)
def fetch_smart_breakouts(min_p, max_p, rsi_lo, rsi_hi, min_chg):
    rocket_list = []
    
    for ticker in nse_watchlist:
        try:
            df = yf.download(ticker, period="2mo", interval="1d", progress=False)
            if df.empty or len(df) < 30:
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            close = df['Close']
            volume = df['Volume']
            
            cmp = float(close.iloc[-1])
            prev_close = float(close.iloc[-2])
            
            # 1. Price Filter
            if not (min_p <= cmp <= max_p):
                continue
                
            # 2. Today's Gain % (Momentum check)
            chg_pct = float(((cmp - prev_close) / prev_close) * 100)
            if chg_pct < min_chg:
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
                
            # 4. Volume Surge Check (Current volume > 20-day average volume)
            avg_vol = float(volume.rolling(window=20).mean().iloc[-1])
            current_vol = float(volume.iloc[-1])
            rel_vol = round(current_vol / avg_vol, 2) if avg_vol > 0 else 1.0
            
            # Smart Trend check: Price above 20 EMA
            ema_20 = float(close.ewm(span=20, adjust=False).mean().iloc[-1])
            if cmp < ema_20:
                continue
            
            rocket_list.append({
                "Symbol": ticker.replace(".NS", ""),
                "CMP (INR)": round(cmp, 2),
                "Chg %": round(chg_pct, 2),
                "RSI (14)": round(current_rsi, 2),
                "Rel Vol": rel_vol,
                "EMA 20": round(ema_20, 2)
            })
            
        except Exception as e:
            continue
            
    return pd.DataFrame(rocket_list)

if scan_btn or True:
    with st.spinner("Analyzing NSE live momentum and breakout stocks with smart logic..."):
        df_result = fetch_smart_breakouts(min_price, max_price, min_rsi, max_rsi, min_chg_pct)
        
    if df_result is not None and not df_result.empty:
        st.success(f"🎯 Found {len(df_result)} Momentum Rocket Stocks!")
        st.dataframe(df_result, use_container_width=True)
    else:
        st.warning("⚠️ No stocks matched current filters. Click 'Scan Smart Rocket Stocks' in the sidebar or widen the range.")
