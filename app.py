import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="OfficialLS Pro AI", layout="wide")

if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.info("Delta Whitelist IP: 74.220.48.23")
    acc_mode = st.radio("Account Mode", ["Demo ($10)", "Real Delta"])
    api_key = st.text_input("Delta API Key", type="password")
    api_secret = st.text_input("Delta API Secret", type="password")
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)

def connect_exchange(key, secret, mode):
    if mode == "Real Delta" and key and secret:
        try:
            ex = ccxt.delta({
                'apiKey': key.strip(),
                'secret': secret.strip(),
                'enableRateLimit': True,
                'options': {'adjustForTimeDifference': True}
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            # Ye line asli error batayegi
            return None, f"Error: {str(e)}"
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_key, api_secret, acc_mode)

st.title("📊 OfficialLS AI Terminal")

if conn_status == "SUCCESS":
    st.success("✅ Real Account Connected!")
elif "Error" in conn_status:
    st.error(f"❌ Connection Failed: {conn_status}")
    st.info("Tip: Check if IP 74.220.48.23 is added to Delta Whitelist.")

st.components.v1.html('<div style="height:400px;"><div id="tv" style="height:100%;"></div><script src="https://s3.tradingview.com/tv.js"></script><script>new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","interval":"1","theme":"dark","container_id":"tv"});</script></div>', height=400)

data_area = st.empty()
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72900.0

    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        fee = (st.session_state.wallet * 0.1 * lev) * 0.001
        pnl = (random.uniform(-0.5, 1.2) * (lev/10)) - fee
        if conn_status != "SUCCESS": st.session_state.wallet += pnl
        st.session_state.history.insert(0, {"Time": ist, "Entry": price, "PNL": round(pnl,2), "Wallet": round(st.session_state.wallet,2)})

    st.session_state.last_p = price
    with data_area.container():
        c1, c2 = st.columns(2)
        c1.metric("Live BTC", f"${price}")
        c2.metric("Balance", f"${st.session_state.wallet:.2f}")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history).head(10), use_container_width=True)
    time.sleep(2)
        
