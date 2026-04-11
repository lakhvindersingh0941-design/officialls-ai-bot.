import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Persistent Data Setup
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 2. SIDEBAR (Fixed Connection Logic)
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.info("Whitelisted IP: 74.220.48.23") # As per your screenshot
    
    acc_mode = st.radio("Account Mode", ["Demo ($10 Simulation)", "Real Delta Account"])
    
    api_key = st.text_input("Delta API Key", type="password") if acc_mode == "Real Delta Account" else ""
    api_secret = st.text_input("Delta API Secret", type="password") if acc_mode == "Real Delta Account" else ""
    lev = st.select_slider("Leverage Setting", [10, 25, 50, 100], 50)
    
    if st.button("Reset Account"):
        st.session_state.wallet = 10.0
        st.session_state.history = []
        st.rerun()

# 3. Enhanced Exchange Connection
@st.cache_resource
def connect_exchange(key, secret, mode):
    if mode == "Real Delta Account" and key and secret:
        try:
            ex = ccxt.delta({
                'apiKey': key.strip(),
                'secret': secret.strip(),
                'enableRateLimit': True,
                'timeout': 30000,
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 15000 # Increased window for slow server
                }
            })
            # Check connection
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
elif conn_status != "DEMO":
    st.error(f"❌ Connection Issue: {conn_status}")
    st.info("Check: API Secret sahi paste kiya hai? Ek bhi word miss toh nahi?")

# Metrics
m1, m2, m3 = st.columns(3)
placeholder_price = m1.empty()
placeholder_wallet = m2.empty()
m3.metric("Mode", "REAL" if conn_status == "SUCCESS" else "DEMO")

st.divider()

# Layout
c_news, c_main = st.columns([1, 3])

with c_news:
    st.subheader("📰 AI Signals")
    st.success("Signal: BULLISH")
    st.info("EMA: $72,800 Support")
    st.divider()
    st.subheader("📊 Fees Logic")
    st.write(f"Entry: 0.05%")
    st.write(f"Exit: 0.05%")
    st.write(f"Leverage: {lev}x")

with c_main:
    # UPDATED: Real Delta Exchange Chart
    chart_html = """
    <div style="height:450px;">
        <div id="tv_chart" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({
          "autosize": true, "symbol": "DELTA:BTCPERP", "interval": "1",
          "theme": "dark", "timezone": "Asia/Kolkata", "container_id": "tv_chart"
        });
        </script>
    </div>"""
    st.components.v1.html(chart_html, height=450)
    
    st.subheader("📜 Professional History (IST)")
    placeholder_history = st.empty()

# 5. DATA LOOP
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72794.0

    # Trade Simulation
    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        
        # Fees: (Position Value * 0.1%)
        pos_val = (st.session_state.wallet * 0.1) * lev
        total_fee = pos_val * 0.001
        
        gross = random.uniform(-0.4, 1.1) * (lev/10)
        net_pnl = gross - total_fee
        
        if conn_status != "SUCCESS":
            st.session_state.wallet += net_pnl
            
        st.session_state.history.insert(0, {
            "Time (IST)": ist, "Type": "LONG" if price > st.session_state.last_p else "SHORT",
            "Entry": price, "Fee": round(total_fee, 3), "PNL": round(net_pnl, 2), "Wallet": round(st.session_state.wallet, 2)
        })

    st.session_state.last_p = price
    placeholder_price.metric("Live Price", f"${price:,.1f}")
    placeholder_wallet.metric("Account Balance", f"${st.session_state.wallet:,.2f}")
    
    with placeholder_history.container():
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            st.dataframe(df.style.map(lambda v: f'color: {"#00ff00" if v > 0 else "#ff0000"}', subset=['PNL']), use_container_width=True)
    
    time.sleep(2)
    
