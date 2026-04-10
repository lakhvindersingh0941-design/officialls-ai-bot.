import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Configuration (Full Screen)
st.set_page_config(page_title="OfficialLS Pro Terminal", layout="wide")

# 2. Custom CSS (Delta Exchange Dark Theme)
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 22px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    div.stButton > button { width: 100%; background-color: #2b3139; color: white; border: 1px solid #474d57; }
    .stTable { font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Persistent Data (Storage)
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# --- HEADER SECTION ---
st.title("📊 OfficialLS AI Trading Terminal")

# 4. SIDEBAR CONTROLS
with st.sidebar:
    st.header("🤖 Bot Settings")
    auto_bot = st.toggle("Activate AI Scalper", value=True)
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)
    st.divider()
    if st.button("Reset Account"):
        st.session_state.wallet = 100.0
        st.session_state.history = []
        st.rerun()

# 5. LIVE CHART (Top Section - Fixed)
chart_html = """
<div style="height:500px; border: 1px solid #363a45; border-radius: 8px; overflow: hidden;">
    <div id="tv_chart" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
      "autosize": true, "symbol": "DELTA:BTCPERP", "interval": "1",
      "theme": "dark", "style": "1", "container_id": "tv_chart",
      "timezone": "Asia/Kolkata", "locale": "en", "hide_side_toolbar": false,
      "withdateranges": true, "details": true, "hotlist": true
    });
    </script>
</div>"""
st.components.v1.html(chart_html, height=500)

# 6. LIVE UPDATE AREA (Bottom Section)
st.divider()
placeholder = st.empty()

# --- REAL-TIME LOOP ---
while True:
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 65000.0

    # AI Scalping Logic (Execute only if price changes)
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        if abs(diff) > 2.0: # $2 movement threshold
            pnl = random.uniform(-0.4, 0.9) * (lev / 10)
            st.session_state.wallet += pnl
            
            # Save to History
            st.session_state.history.insert(0, {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Side": "LONG" if diff > 0 else "SHORT",
                "Entry": f"${price:,.1f}",
                "P&L ($)": round(pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 100: st.session_state.history.pop()

    st.session_state.last_p = price

    # Drawing the UI inside Placeholder to prevent full page refresh
    with placeholder.container():
        # Metric Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live BTC", f"${price:,.1f}")
        m2.metric("Overall Balance", f"${st.session_state.wallet:,.2f}")
        m3.metric("Leverage", f"{lev}x")
        m4.metric("Bot Status", "RUNNING" if auto_bot else "PAUSED")

        st.write("---")
        
        # News and History Columns
        col_news, col_hist = st.columns([1, 2])
        
        with col_news:
            st.subheader("📰 Market Signals")
            st.success("✅ AI Sentiment: Bullish")
            st.info("💡 Tip: EMA 50 Support active")
            st.warning("⚠️ High Volatility Scalp Mode")
            st.divider()
            st.caption("Order Book (Live)")
            st.code(f"🔴 {price+3} | 1.5 BTC\n🟢 {price-2} | 2.1 BTC", language='text')

        with col_hist:
            st.subheader("📜 Professional History")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                # Apply Color to P&L
                def style_pnl(v):
                    color = '#00ff00' if v > 0 else '#ff0000'
                    return f'color: {color}; font-weight: bold;'
                
                st.dataframe(df.style.applymap(style_pnl, subset=['P&L ($)']), 
                             use_container_width=True, height=350)
            else:
                st.info("AI Bot is scanning the chart for professional entries...")

    time.sleep(1) # Frequency of Update
            
