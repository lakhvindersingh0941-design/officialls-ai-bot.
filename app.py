import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Persistent States
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Mode", ["Demo ($10 Simulation)", "Real Delta Account"])
    
    api_k = st.text_input("Delta API Key", type="password") if acc_mode == "Real Delta Account" else ""
    api_s = st.text_input("Delta API Secret", type="password") if acc_mode == "Real Delta Account" else ""
    
    lev = st.select_slider("Leverage Setting", [10, 25, 50, 100], 50)
    
    if st.button("Reset Terminal"):
        st.session_state.wallet = 10.0
        st.session_state.history = []
        st.rerun()

# 3. Connection Logic (FORCED CONNECT)
def connect_exchange(k, s, m):
    if m == "Real Delta Account" and k and s:
        try:
            # Direct Connection without extra headers to avoid 'Invalid' error
            ex = ccxt.delta({
                'apiKey': k.strip(),
                'secret': s.strip(),
                'enableRateLimit': True,
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 60000 # Max window for slow connections
                }
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_k, api_s, acc_mode)

# 4. UI: Metrics & Terminal
st.title("📊 OfficialLS AI Professional Terminal")

if conn_status == "SUCCESS":
    st.success("✅ Real Delta Account Connected!")
elif acc_mode == "Real Delta Account":
    st.error(f"❌ Connection Issue: {conn_status}")
    st.info("Tip: Delta API settings mein 'Permissions' (Read/Trading) zaroor check karein.")

# Layout
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Mode", "REAL" if conn_status == "SUCCESS" else "DEMO")
m4.metric("Leverage", f"{lev}x")

st.divider()

col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("AI Signals & News")
    st.success("Signal: BULLISH (72.8k Support)")
    st.info("Trend: Market Volume High")
    st.divider()
    st.subheader("Trade Config")
    st.write("Fees: 0.1% (Entry+Exit)")
    st.write("SL: 0.8% | TP: 1.5%")
    st.divider()
    p_sigs = st.empty()

with col_main:
    # Professional Chart
    st.components.v1.html("""
    <div style="height:420px; border-radius: 10px; overflow: hidden;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"});
        </script>
    </div>""", height=420)
    
    st.subheader("📜 History (IST Time + Fees)")
    p_hist = st.empty()

# 5. DATA SYNC & LOOP
while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72800.0

    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        
        # Fees: Position Value * 0.1%
        margin = st.session_state.wallet * 0.1
        pos_val = margin * lev
        fee = pos_val * 0.001
        
        # SL/TP logic
        sl = price * 0.992 if price > st.session_state.last_p else price * 1.008
        tp = price * 1.015 if price > st.session_state.last_p else price * 0.985
        
        pnl = (random.uniform(-0.5, 1.2) * (lev/10)) - fee
        
        if conn_status != "SUCCESS":
            st.session_state.wallet += net_pnl = pnl

        st.session_state.history.insert(0, {
            "Time (IST)": ist, "Side": "LONG" if price > st.session_state.last_p else "SHORT",
            "Entry": price, "SL": round(sl, 1), "TP": round(tp, 1),
            "Fee": round(fee, 3), "PNL": round(pnl, 2), "Wallet": round(st.session_state.wallet, 2)
        })

    st.session_state.last_p = price
    p_price.metric("Live Price", f"${price:,.1f}")
    p_wallet.metric("Wallet", f"${st.session_state.wallet:,.2f}")
    p_sigs.code(f"🔴 {price+3}\n🟢 {price-2}")
    
    with p_hist:
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
    
    time.sleep(2)
            
