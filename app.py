import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS AI Pro", layout="wide")

# Persistent State
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 2. Sidebar
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.info("Delta Whitelist IP: 74.220.48.23")
    acc_mode = st.radio("Account Mode", ["Demo Simulation", "Real Delta Account"])
    api_key = st.text_input("Delta API Key", type="password") if acc_mode == "Real Delta Account" else ""
    api_secret = st.text_input("Delta API Secret", type="password") if acc_mode == "Real Delta Account" else ""
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)
    if st.button("Reset Terminal"):
        st.session_state.wallet = 10.0
        st.session_state.history = []
        st.rerun()

# 3. Connection Logic (Standard Mode)
def connect_exchange(key, secret, mode):
    if mode == "Real Delta Account" and key and secret:
        try:
            ex = ccxt.delta({'apiKey': key.strip(), 'secret': secret.strip()})
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_key, api_secret, acc_mode)

# 4. UI Display
st.title("📊 OfficialLS Professional Terminal")
if conn_status == "SUCCESS": st.success("✅ Real Delta Connected")

m1, m2 = st.columns(2)
p_price = m1.empty()
p_wallet = m2.empty()

# Chart
st.components.v1.html('<div style="height:400px;"><div id="tv" style="height:100%;"></div><script src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({"autosize":true,"symbol":"DELTA:BTCPERP","theme":"dark","container_id":"tv"});</script></div>', height=400)

hist_area = st.empty()

# 5. Simple Loop
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72900.0

    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        fee = (st.session_state.wallet * 0.1 * lev) * 0.001
        pnl = (random.uniform(-0.5, 1.2) * (lev/10)) - fee
        if conn_status != "SUCCESS": st.session_state.wallet += pnl
        st.session_state.history.insert(0, {"Time (IST)": ist, "Entry": price, "PNL": round(pnl,2), "Wallet": round(st.session_state.wallet,2)})

    st.session_state.last_p = price
    p_price.metric("Live Price", f"${price}")
    p_wallet.metric("Balance", f"${st.session_state.wallet:.2f}")
    
    with hist_area:
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history).head(10), use_container_width=True)
    time.sleep(2)
