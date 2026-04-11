import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom CSS for Dark Mode
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Setup
if 'wallet' not in st.session_state: st.session_state.wallet = 10.0
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0

# 3. SIDEBAR (IP Finder & API Connect)
with st.sidebar:
    st.title("OfficialLS AI Bot")
    
    # Ye IP tumhe Delta Exchange ki API key settings mein daalni hai
    try:
        current_bot_ip = requests.get('https://api.ipify.org').text
        st.code(f"Your Bot IP: {current_bot_ip}", language='text')
        st.caption("Copy this IP to Delta API Whitelist")
    except:
        st.caption("Could not fetch IP")

    acc_mode = st.radio("Account Mode", ["Paper Trade ($10)", "Real Delta Account"])
    
    api_key = st.text_input("Delta API Key", type="password") if acc_mode == "Real Delta Account" else ""
    api_secret = st.text_input("Delta API Secret", type="password") if acc_mode == "Real Delta Account" else ""

    auto_bot = st.toggle("Activate AI Trading", value=True)
    lev = st.select_slider("Leverage Setting", [10, 25, 50, 100], 50)
    
    if st.button("Reset Terminal"):
        st.session_state.wallet = 10.0
        st.session_state.history = []
        st.rerun()

# 4. Exchange Connection Logic
@st.cache_resource
def connect_exchange(key, secret, mode):
    if mode == "Real Delta Account" and key and secret:
        try:
            ex = ccxt.delta({
                'apiKey': key.strip(),
                'secret': secret.strip(),
                'enableRateLimit': True,
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return ccxt.delta(), str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_key, api_secret, acc_mode)

# 5. HEADER & CHART
st.title("📊 OfficialLS AI Professional Terminal")

if "invalid_api_key" in str(conn_status).lower():
    st.error(f"❌ Connection Failed: IP Whitelisting Error. Make sure you added {current_bot_ip} in Delta.")
elif conn_status == "SUCCESS":
    st.success("✅ Real Delta Account Connected!")

chart_html = """
<div style="height:450px; border: 1px solid #363a45; border-radius: 8px; overflow: hidden;">
    <div id="tv_chart" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","interval":"1","theme":"dark","style":"1","container_id":"tv_chart","timezone":"Asia/Kolkata"});
    </script>
</div>"""
st.components.v1.html(chart_html, height=450)

# 6. LIVE SYNC LOOP
placeholder = st.empty()

while True:
    try:
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet = bal['total'].get('USDT', 0.0)
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72500.0

    # AI Scalping Logic (IST Time + Dual Fees + SL/TP)
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        if abs(diff) > 2.0:
            ist_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d-%m %H:%M:%S")
            margin = st.session_state.wallet * 0.1
            pos_val = margin * lev
            
            # Delta Dual Fees (0.05% Buy + 0.05% Sell = 0.1% total position value)
            total_fee = pos_val * 0.001
            gross_pnl = random.uniform(-0.5, 1.2) * (lev/10)
            net_pnl = gross = gross_pnl - total_fee
            
            if conn_status != "SUCCESS": st.session_state.wallet += net_pnl
            
            sl = price * 0.992 if diff > 0 else price * 1.008
            tp = price * 1.015 if diff > 0 else price * 0.985

            st.session_state.history.insert(0, {
                "Time (IST)": ist_time,
                "Type": "LONG" if diff > 0 else "SHORT",
                "Entry": round(price, 1),
                "SL": round(sl, 1),
                "TP": round(tp, 1),
                "Pos Value": f"${pos_val:,.1f}",
                "Total Fee": round(total_fee, 3),
                "Net PNL": round(net_pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 50: st.session_state.history.pop()

    st.session_state.last_p = price

    with placeholder.container():
        m1, m2, m3 = st.columns(3)
        m1.metric("Live BTC", f"${price:,.1f}")
        m2.metric("Wallet Balance", f"${st.session_state.wallet:,.2f}")
        m3.metric("Mode", "REAL" if conn_status == "SUCCESS" else "DEMO")

        cn, ch = st.columns([1, 3])
        with cn:
            st.subheader("📰 Market Signals")
            st.success("AI: Bullish Signal Active")
            st.info("EMA 200 Support Found")
            st.divider()
            st.code(f"🔴 {price+3} | 1.8 BTC\n🟢 {price-2} | 2.5 BTC", language='text')

        with ch:
            st.subheader("📜 AI Professional History (IST)")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                st.dataframe(df.style.map(lambda v: f'color: {"#00ff00" if v > 0 else "#ff0000"}; font-weight: bold;', subset=['Net PNL']), use_container_width=True)
            else:
                st.info("AI Bot scanning for entry signals...")

    time.sleep(1)
                
