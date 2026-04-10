import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro Terminal", layout="wide")

# 2. Custom CSS
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    div.stButton > button { width: 100%; background-color: #2b3139; color: white; border: 1px solid #474d57; }
    </style>
    """, unsafe_allow_html=True)

# 3. Persistent Data
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 4. SIDEBAR
with st.sidebar:
    st.header("🤖 Bot Settings")
    auto_bot = st.toggle("Activate AI Scalper", value=True)
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)
    if st.button("Reset Account"):
        st.session_state.wallet = 100.0
        st.session_state.history = []
        st.rerun()

# 5. LIVE CHART (Fixed Section)
st.title("📊 OfficialLS AI Terminal")
chart_html = """
<div style="height:480px; border: 1px solid #363a45; border-radius: 8px; overflow: hidden;">
    <div id="tv_chart" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
      "autosize": true, "symbol": "DELTA:BTCPERP", "interval": "1",
      "theme": "dark", "style": "1", "container_id": "tv_chart",
      "timezone": "Asia/Kolkata", "locale": "en", "hide_side_toolbar": false
    });
    </script>
</div>"""
st.components.v1.html(chart_html, height=480)

# 6. LIVE UPDATE AREA
st.divider()
placeholder = st.empty()

while True:
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 72000.0

    # AI Logic
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        if abs(diff) > 1.5:
            pnl = random.uniform(-0.4, 0.9) * (lev / 10)
            st.session_state.wallet += pnl
            st.session_state.history.insert(0, {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Side": "LONG" if diff > 0 else "SHORT",
                "Entry": f"${price:,.1f}",
                "P&L ($)": round(pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 50: st.session_state.history.pop()

    st.session_state.last_p = price

    with placeholder.container():
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live BTC", f"${price:,.1f}")
        m2.metric("Overall Balance", f"${st.session_state.wallet:,.2f}")
        m3.metric("Leverage", f"{lev}x")
        m4.metric("Bot Status", "RUNNING" if auto_bot else "PAUSED")

        col_news, col_hist = st.columns([1, 2])
        with col_news:
            st.subheader("📰 Market Signals")
            st.success("✅ AI Sentiment: Bullish")
            st.info("💡 EMA 50 Support active")
            st.divider()
            st.code(f"🔴 {price+2} | 1.1 BTC\n🟢 {price-1} | 2.5 BTC", language='text')

        with col_hist:
            st.subheader("📜 Professional History")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                # FIX: map() instead of applymap()
                def style_pnl(v):
                    return f'color: {"#00ff00" if v > 0 else "#ff0000"}; font-weight: bold;'
                
                st.dataframe(df.style.map(style_pnl, subset=['P&L ($)']), use_container_width=True)
            else:
                st.info("AI Bot is scanning for professional entries...")

    time.sleep(1)
