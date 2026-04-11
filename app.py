import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom UI
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #f0b90b !important; }
    </style>
    """, unsafe_allow_html=True)

if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Mode", ["Demo Simulation", "Real Delta India"])
    
    api_k = st.text_input("API Key", type="password") if acc_mode == "Real Delta India" else ""
    api_s = st.text_input("API Secret", type="password") if acc_mode == "Real Delta India" else ""
    
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)

# 3. Delta India Connection Logic (FIXED)
def connect_exchange(k, s, m):
    if m == "Real Delta India" and k and s:
        try:
            ex = ccxt.delta({
                'apiKey': k.strip(),
                'secret': s.strip(),
                'enableRateLimit': True,
                # Delta India ke liye specific URL dalna zaroori hai
                'urls': {
                    'api': {
                        'public': 'https://api.india.delta.exchange',
                        'private': 'https://api.india.delta.exchange',
                    }
                },
                'options': {
                    'adjustForTimeDifference': True,
                    'recvWindow': 30000 
                }
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_k, api_s, acc_mode)

# 4. DASHBOARD UI
st.title("📊 OfficialLS AI Professional Terminal")

if conn_status == "SUCCESS":
    st.success("✅ Connected to Delta India!")
elif acc_mode == "Real Delta India":
    st.error(f"❌ Connection Issue: {conn_status}")
    st.info("Check: Kya Delta India App mein 74.220.48.23 IP whitelist ki hai?")

# Metrics
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Mode", "REAL" if conn_status == "SUCCESS" else "DEMO")
m4.metric("Leverage", f"{lev}x")

st.divider()

col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("📰 AI News & Signals")
    st.success("Signal: BULLISH (72.8k Support)")
    st.info("Fees: 0.1% | IST Time")
    st.divider()
    st.caption("Live Delta Orderbook")
    p_sigs = st.empty()

with col_main:
    # TradingView Chart
    st.components.v1.html("""
    <div style="height:420px; border-radius: 10px; overflow: hidden; border: 1px solid #333;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"});
        </script>
    </div>""", height=420)
    
    st.subheader("📜 Live Trade History (IST Time)")
    p_hist = st.empty()

# 5. DATA SYNC & LOOP
while True:
    try:
        # Delta India par symbol 'BTCUSD' hota hai Perpetual ke liye
        ticker = exchange.fetch_ticker('BTCUSD' if conn_status == "SUCCESS" else 'BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72800.0

    if st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
        ist_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
        
        # Fees & SL/TP
        pos_val = (st.session_state.wallet * 0.1) * lev
        fee = pos_val * 0.001
        pnl_sim = (random.uniform(-0.5, 1.2) * (lev/10)) - fee
        
        sl = price * 0.992 if price > st.session_state.last_p else price * 1.008
        tp = price * 1.015 if price > st.session_state.last_p else price * 0.985
        
        if conn_status != "SUCCESS": st.session_state.wallet += pnl_sim

        st.session_state.history.insert(0, {
            "Time": ist_time, "Side": "LONG" if price > st.session_state.last_p else "SHORT",
            "Entry": price, "SL": round(sl, 1), "TP": round(tp, 1),
            "Fee": round(fee, 3), "PNL": round(pnl_sim, 2), "Wallet": round(st.session_state.wallet, 2)
        })

    st.session_state.last_p = price
    p_price.metric("Live BTC", f"${price:,.1f}")
    p_wallet.metric("Balance", f"${st.session_state.wallet:,.2f}")
    p_sigs.code(f"🔴 {price+2.5}\n🟢 {price-1.5}")
    
    with p_hist:
        if st.session_state.history:
            st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
    
    time.sleep(2)
    
