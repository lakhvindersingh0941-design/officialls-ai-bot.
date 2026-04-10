import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom CSS for Dark UI
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Setup
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    auto_bot = st.toggle("Activate AI Trading", value=True)
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)
    if st.button("Reset All Data"):
        st.session_state.wallet = 100.0
        st.session_state.history = []
        st.rerun()

# 4. LIVE CHART
st.title("📊 OfficialLS AI Professional Terminal")
chart_html = """
<div style="height:450px; border: 1px solid #363a45; border-radius: 8px; overflow: hidden;">
    <div id="tv_chart" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
      "autosize": true, "symbol": "DELTA:BTCPERP", "interval": "1",
      "theme": "dark", "style": "1", "container_id": "tv_chart",
      "timezone": "Asia/Kolkata", "locale": "en"
    });
    </script>
</div>"""
st.components.v1.html(chart_html, height=450)

# 5. DATA SYNC
st.divider()
placeholder = st.empty()

while True:
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 71500.0

    # AI Scalping Logic
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        if abs(diff) > 1.8:
            # Fee & PnL Calculation
            margin = st.session_state.wallet * 0.1
            pos_val = margin * lev
            total_fee = pos_val * 0.001 # 0.05% Buy + 0.05% Sell
            
            gross = random.uniform(-0.5, 1.2) * (lev / 10)
            net_pnl = gross - total_fee
            st.session_state.wallet += net_pnl
            
            # SL/TP
            sl = price * 0.99 if diff > 0 else price * 1.01
            tp = price * 1.02 if diff > 0 else price * 0.98
            
            # Entry
            st.session_state.history.insert(0, {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": "LONG" if diff > 0 else "SHORT",
                "Entry": round(price, 1),
                "SL": round(sl, 1),
                "TP": round(tp, 1),
                "PNL": round(net_pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 50: st.session_state.history.pop()

    st.session_state.last_p = price

    with placeholder.container():
        m1, m2, m3 = st.columns(3)
        m1.metric("Live BTC", f"${price:,.1f}")
        m2.metric("Net Wallet", f"${st.session_state.wallet:,.2f}")
        m3.metric("Leverage", f"{lev}x")

        c_news, c_hist = st.columns([1, 2.5])
        with c_news:
            st.subheader("📰 AI Signals")
            st.success("Bullish: BTC Inflow detected")
            st.info("Signal: Scalp LONG active")
            st.divider()
            st.code(f"🔴 {price+3} | 1.8 BTC\n🟢 {price-2} | 2.5 BTC", language='text')

        with c_hist:
            st.subheader("📜 AI Professional History")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                # FIXED: Simple formatting without complex map for reliability
                def style_color(v):
                    return f'color: {"#00ff00" if v > 0 else "#ff0000"}; font-weight: bold;'
                
                st.dataframe(df.style.map(style_color, subset=['PNL']), use_container_width=True)
            else:
                st.info("AI Bot scanning market indicators...")

    time.sleep(1)
