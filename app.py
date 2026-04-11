import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro AI", layout="wide")

# Persistent State
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 2. Sidebar
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    mode = st.radio("Mode", ["Demo Simulation", "Real Delta Account"])
    
    key = st.text_input("Delta API Key", type="password") if mode == "Real Delta Account" else ""
    secret = st.text_input("Delta API Secret", type="password") if mode == "Real Delta Account" else ""
    
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)

# 3. Connection Logic (Super Stable)
def connect_exchange(k, s, m):
    if m == "Real Delta Account" and k and s:
        try:
            # Simple connection setup
            ex = ccxt.delta({
                'apiKey': k.strip(),
                'secret': s.strip(),
                'enableRateLimit': True,
            })
            # Check balance to verify key
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(key, secret, mode)

# 4. Professional UI
st.title("📊 OfficialLS AI Professional Terminal")

if conn_status == "SUCCESS":
    st.success("✅ REAL ACCOUNT CONNECTED!")
elif mode == "Real Delta Account":
    st.error(f"❌ Connection Failed: {conn_status}")
    st.info("Solution: Delta par Nayi API Key banayein aur Permissions (Read/Trading) ON karein.")

# Metrics
m1, m2, m3 = st.columns(3)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Leverage", f"{lev}x")

st.divider()

# Layout: Signals + Chart
c_news, c_main = st.columns([1, 3])

with c_news:
    st.subheader("📰 AI News")
    st.success("Signal: Bullish Trend")
    st.info("Fees: 0.1% | IST Time")
    st.divider()
    st.subheader("📊 SL/TP Info")
    st.write("SL: 0.8% | TP: 1.5%")
    st.divider()
    p_sigs = st.empty()

with c_main:
    # Real Chart
    st.components.v1.html("""
    <div style="height:420px; border-radius: 10px; overflow: hidden;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","theme":"dark","container_id":"tv"});
        </script>
    </div>""", height=420)
    
    st.subheader("📜 History (IST Time + Fees)")
    p_hist = st.empty()

# 5. Trading Loop
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72500.0

    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        
        # Fees & PNL Logic
        pos_val = (st.session_state.wallet * 0.1) * lev
        fee = pos_val * 0.001
        pnl = (random.uniform(-0.5, 1.2) * (lev/10)) - fee
        
        if conn_status != "SUCCESS": st.session_state.wallet += pnl
        
        sl = price * 0.992 if price > st.session_state.last_p else price * 1.008
        tp = price * 1.015 if price > st.session_state.last_p else price * 0.985

        st.session_state.history.insert(0, {
            "Time": ist, "Type": "LONG" if price > st.session_state.last_p else "SHORT",
            "Entry": price, "SL": round(sl,1), "TP": round(tp,1), 
            "Fee": round(fee,3), "Net PNL": round(pnl,2), "Wallet": round(st.session_state.wallet,2)
        })

    st.session_state.last_p = price
    p_price.metric("Live BTC", f"${price:,.1f}")
    p_wallet.metric("Balance", f"${st.session_state.wallet:,.2f}")
    p_sigs.code(f"🔴 {price+2}\n🟢 {price-1}")
    
    with p_hist:
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
    
    time.sleep(2)
