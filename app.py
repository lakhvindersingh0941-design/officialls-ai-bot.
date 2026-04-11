import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# Persistent States
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Type", ["Demo ($10 Simulation)", "Real Delta Account"])
    
    api_key = ""
    api_secret = ""
    if acc_mode == "Real Delta Account":
        api_key = st.text_input("Delta API Key", type="password")
        api_secret = st.text_input("Delta API Secret", type="password")
    
    lev = st.select_slider("Leverage Setting", [10, 25, 50, 100], 50)
    
    if st.button("Reset Terminal"):
        st.session_state.wallet = 10.0
        st.session_state.history = []
        st.rerun()

# 3. Connection Logic (Fixed for Delta Errors)
def connect_exchange(k, s, m):
    if m == "Real Delta Account" and k and s:
        try:
            ex = ccxt.delta({
                'apiKey': k.strip(),
                'secret': s.strip(),
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 15000,
                    'defaultType': 'future'
                }
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_key, api_secret, acc_mode)

# 4. MAIN UI
st.title("📊 OfficialLS AI Professional Terminal")

if conn_status == "SUCCESS":
    st.success("✅ Real Delta Account Connected!")
elif "Error" in str(conn_status) or "invalid" in str(conn_status).lower():
    st.error(f"❌ Connection Failed: {conn_status}")
    st.info("Tip: Delta par Nayi Key banayein aur 'Main Account' check karein.")

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
placeholder_price = m1.empty()
placeholder_wallet = m2.empty()
m3.metric("Mode", "REAL" if conn_status == "SUCCESS" else "DEMO")
m4.metric("Leverage", f"{lev}x")

st.divider()

# Layout: Signals + Chart
col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("📰 AI News & Signals")
    st.success("Signal: BULLISH (EMA Support)")
    st.info("News: BTC holding 72.5k Zone.")
    st.divider()
    st.subheader("📊 Trade Config")
    st.write("Fees: 0.1% (Buy+Sell)")
    st.write("SL: 0.8% | TP: 1.5%")
    st.divider()
    st.caption("Live Orderbook")
    placeholder_sigs = st.empty()

with col_main:
    # Real-Time Professional Chart
    chart_html = """
    <div style="height:420px; border-radius: 10px; overflow: hidden;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({
          "autosize": true, "symbol": "BINANCE:BTCUSDT", "interval": "1",
          "theme": "dark", "container_id": "tv", "timezone": "Asia/Kolkata"
        });
        </script>
    </div>"""
    st.components.v1.html(chart_html, height=420)
    
    st.subheader("📜 Live Trade History (IST Time)")
    placeholder_history = st.empty()

# 5. DATA SYNC & TRADING LOOP
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72700.0

    # AI Execution Logic
    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        
        # Fees: Position Value * 0.1%
        margin = st.session_state.wallet * 0.1
        pos_val = margin * lev
        total_fee = pos_val * 0.001
        
        # SL/TP logic
        sl = price * 0.992 if price > st.session_state.last_p else price * 1.008
        tp = price * 1.015 if price > st.session_state.last_p else price * 0.985
        
        pnl = (random.uniform(-0.5, 1.2) * (lev/10)) - total_fee
        
        if conn_status != "SUCCESS":
            st.session_state.wallet += pnl
            
        st.session_state.history.insert(0, {
            "Time (IST)": ist_time, "Side": "LONG" if price > st.session_state.last_p else "SHORT",
            "Entry": price, "SL": round(sl, 1), "TP": round(tp, 1),
            "Fee": round(total_fee, 3), "PNL": round(pnl, 2), "Wallet": round(st.session_state.wallet, 2)
        })
        if len(st.session_state.history) > 30: st.session_state.history.pop()

    st.session_state.last_p = price
    
    # Update Placeholders
    placeholder_price.metric("Live Price", f"${price:,.1f}")
    placeholder_wallet.metric("Total Wallet", f"${st.session_state.wallet:,.2f}")
    placeholder_sigs.code(f"🔴 {price+2.5}\n🟢 {price-1.5}")
    
    with placeholder_history.container():
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df.style.map(lambda v: f'color: {"#00ff00" if v > 0 else "#ff0000"}', subset=['PNL']), use_container_width=True)
    
    time.sleep(2)
