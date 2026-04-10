import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Setup (Balance changed to $10)
if 'wallet' not in st.session_state:
    st.session_state.wallet = 10.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    auto_bot = st.toggle("Activate AI Trading", value=True)
    lev = st.select_slider("Leverage Setting", [10, 25, 50, 100], 50)
    st.divider()
    st.info("Balance: $10 | Delta Fees: 0.05% (B+S)")
    if st.button("Reset Account ($10)"):
        st.session_state.wallet = 10.0
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

# 5. DATA SYNC LOOP
st.divider()
placeholder = st.empty()

while True:
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 71200.0

    # AI Scalping Logic
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        
        if abs(diff) > 2.0:
            # IST Time Calculation (Adding 5.30 hours to UTC)
            ist_time = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%d-%m %H:%M:%S")
            
            # Margin & Position
            margin = st.session_state.wallet * 0.1 
            pos_value = margin * lev 
            
            # Fees (0.05% Buy + 0.05% Sell)
            buy_fee = pos_value * 0.0005
            sell_fee = pos_value * 0.0005
            total_fee = buy_fee + sell_fee
            
            # Profit/Loss
            gross = random.uniform(-0.6, 1.4) * (lev / 10)
            net_pnl = gross - total_fee
            st.session_state.wallet += net_pnl
            
            # SL/TP
            sl = price * 0.992 if diff > 0 else price * 1.008
            tp = price * 1.015 if diff > 0 else price * 0.985

            # Save to History
            st.session_state.history.insert(0, {
                "Time (IST)": ist_time,
                "Side": "LONG" if diff > 0 else "SHORT",
                "Entry": round(price, 1),
                "SL": round(sl, 1),
                "TP": round(tp, 1),
                "Pos Value": f"${pos_value:,.1f}",
                "Buy Fee": round(buy_fee, 3),
                "Sell Fee": round(sell_fee, 3),
                "Total Fee": round(total_fee, 3),
                "Net PNL": round(net_pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 50: st.session_state.history.pop()

    st.session_state.last_p = price

    with placeholder.container():
        m1, m2, m3 = st.columns(3)
        m1.metric("Live BTC Price", f"${price:,.1f}")
        m2.metric("Overall Wallet", f"${st.session_state.wallet:,.2f}")
        m3.metric("Leverage", f"{lev}x")

        cn, ch = st.columns([1, 3])
        with cn:
            st.subheader("📰 Market AI")
            st.success("Bullish Sentiment Active")
            st.info("Signal: Scalp Buy Near Support")
            st.divider()
            st.caption("Live Order Book")
            st.code(f"🔴 {price+2} | 1.5 BTC\n🟢 {price-1} | 2.2 BTC", language='text')

        with ch:
            st.subheader("📜 Professional History (IST Time)")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                def color_pnl(v):
                    return f'color: {"#00ff00" if v > 0 else "#ff0000"}; font-weight: bold;'
                st.dataframe(df.style.map(color_pnl, subset=['Net PNL']), use_container_width=True)
            else:
                st.info("AI Bot scanning for entry signals...")

    time.sleep(1)
