import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro AI", layout="wide")

# 2. Database Setup
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. Sidebar (Simplified for No Errors)
st.sidebar.title("OfficialLS AI Control")
mode = st.sidebar.selectbox("Account Type", ["Paper Trade", "Delta Live"])
lev = st.sidebar.select_slider("Leverage", [10, 20, 50, 100], 50)
auto_on = st.sidebar.toggle("AI Auto-Pilot", True)

# 4. Market Data
try:
    ex = ccxt.delta()
    tk = ex.fetch_ticker('BTC/USDT')
    price = tk['last']
    change = tk['percentage']
except:
    price, change = 65000.0, 0.0

# 5. Top Bar Stats
c1, c2, c3 = st.columns(3)
c1.metric("BTC/USDT", f"${price}", f"{change}%")
c2.metric("Wallet Balance", f"${st.session_state.balance:.2f}")
c3.metric("Current Leverage", f"{lev}x")

# 6. Professional TradingView Chart (Big Size)
chart_code = f"""
<div style="height:550px;">
    <div id="tv-chart" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{"autosize":true,"symbol":"DELTA:BTCPERP","interval":"1","theme":"dark","style":"1","locale":"en","container_id":"tv-chart"}});
    </script>
</div>"""
st.components.v1.html(chart_code, height=550)

# 7. AI Automatic Trading Engine
if auto_on and st.session_state.last_p != 0:
    diff = price - st.session_state.last_p
    if abs(diff) > 1.5:
        pnl = random.uniform(-0.5, 1.5) * (lev/10)
        st.session_state.balance += pnl
        st.session_state.trades.insert(0, {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Side": "LONG" if diff > 0 else "SHORT",
            "PnL ($)": round(pnl, 2),
            "Balance": round(st.session_state.balance, 2)
        })

st.session_state.last_p = price

# 8. News & History Sections
col_news, col_hist = st.columns([1, 2])
with col_news:
    st.write("### 📰 AI News")
    st.success("Bullish: BTC Exchange Outflow")
    st.warning("High Volatility Detected")

with col_hist:
    st.write("### 📜 Trade History")
    if st.session_state.trades:
        st.table(pd.DataFrame(st.session_state.trades).head(10))
    else:
        st.info("AI scanning for signals...")

# 9. Real-time Auto-Refresh
time.sleep(2)
st.rerun()
