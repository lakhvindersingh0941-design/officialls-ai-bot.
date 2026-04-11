import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# --- RENDER COMPATIBILITY ---
st.set_page_config(page_title="OfficialLS Pro AI", layout="wide")

# Persistent Data Setup
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# --- SIDEBAR (IP & Connection) ---
with st.sidebar:
    st.title("OfficialLS AI Bot")
    try:
        current_bot_ip = requests.get('https://api.ipify.org').text
        st.error(f"🔴 Delta Whitelist IP: {current_bot_ip}")
        st.caption("Ise Delta API mein update karein.")
    except:
        current_bot_ip = "Unknown"

    acc_mode = st.radio("Account Mode", ["Demo ($10)", "Real Delta"])
    api_key = st.text_input("Delta API Key", type="password") if acc_mode == "Real Delta" else ""
    api_secret = st.text_input("Delta API Secret", type="password") if acc_mode == "Real Delta" else ""
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)

# --- EXCHANGE CONNECTION ---
def connect_exchange(key, secret, mode):
    if mode == "Real Delta" and key and secret:
        try:
            ex = ccxt.delta({'apiKey': key.strip(), 'secret': secret.strip(), 'enableRateLimit': True})
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_key, api_secret, acc_mode)

# --- UI LAYOUT ---
st.title("📊 OfficialLS AI Terminal")

if conn_status != "SUCCESS" and conn_status != "DEMO":
    st.warning(f"⚠️ Connection Issue: Update Delta with IP {current_bot_ip}")
elif conn_status == "SUCCESS":
    st.success("✅ Real Account Connected!")

# Chart (TradingView)
st.components.v1.html("""
<div style="height:450px;"><div id="tv" style="height:100%;"></div><script src="https://s3.tradingview.com/tv.js"></script><script>
new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","interval":"1","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"});
</script></div>""", height=450)

# --- DATA LOOP ---
placeholder = st.empty()
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72900.0

    # Scalping Logic
    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        margin = st.session_state.wallet * 0.1
        total_fee = (margin * lev) * 0.001
        net_pnl = (random.uniform(-0.5, 1.2) * (lev/10)) - total_fee
        if conn_status != "SUCCESS": st.session_state.wallet += net_pnl
        st.session_state.history.insert(0, {"Time (IST)": ist_time, "Entry": price, "Fees": round(total_fee,3), "PNL": round(net_pnl,2), "Wallet": round(st.session_state.wallet,2)})

    st.session_state.last_p = price
    with placeholder.container():
        m1, m2 = st.columns(2)
        m1.metric("Live BTC", f"${price}")
        m2.metric("Wallet", f"${st.session_state.wallet:.2f}")
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
    time.sleep(1)
            
