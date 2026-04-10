import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom CSS: Isse refresh ke waqt hone wali "Blink" kam ho jayegi
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    div[data-testid="stMetricValue"] { font-size: 24px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 2. Permanent Storage (Refresh hone par bhi data nahi jayega)
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. Sidebar (Static - No Refresh)
with st.sidebar:
    st.header("OfficialLS AI")
    auto_bot = st.toggle("🤖 AI BOT ON/OFF", value=True)
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)
    if st.button("Clear History & Reset"):
        st.session_state.wallet = 100.0
        st.session_state.history = []
        st.rerun()

# 4. Live Chart (Ise ek baar load karenge, ye refresh nahi hoga)
st.subheader("📊 BTC/USDT Live Chart")
chart_html = """
<div style="height:450px; border: 1px solid #363a45;">
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
st.components.v1.html(chart_html, height=450)

# 5. LIVE DATA AREA (Ye wala area binna refresh ke update hoga)
st.divider()
data_container = st.empty() # Ye "Khali" jagah hai jahan data update hoga

# 6. Infinite Loop for Real-time Updates (Delta Exchange Style)
while True:
    try:
        ex = ccxt.delta()
        ticker = ex.fetch_ticker('BTC/USDT')
        price = ticker['last']
    except:
        price = 65000.0

    # AI Scalping Logic
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        if abs(diff) > 1.5: # $1.5 movement par trade
            pnl = random.uniform(-0.3, 0.8) * (lev / 10)
            st.session_state.wallet += pnl
            
            # History Save
            entry = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": "LONG" if diff > 0 else "SHORT",
                "Price": f"${price:,.1f}",
                "P&L ($)": round(pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            }
            st.session_state.history.insert(0, entry)
            if len(st.session_state.history) > 50: st.session_state.history.pop()

    st.session_state.last_p = price

    # Update the UI inside the container WITHOUT refreshing the whole page
    with data_container.container():
        col_stats, col_hist = st.columns([1, 2])
        
        with col_stats:
            st.metric("Live Wallet", f"${st.session_state.wallet:,.2f}")
            st.metric("BTC Price", f"${price:,.1f}")
            st.write("### 📰 News Feed")
            st.success("Bullish: BTC Inflow detected")
            st.info("Signal: Scalp Buy Active")
            
        with col_hist:
            st.write("### 📜 Real-time Trade History")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                # Coloring Profit/Loss
                def color_pnl(val):
                    return 'color: #00ff00' if val > 0 else 'color: #ff0000'
                st.dataframe(df.style.applymap(color_pnl, subset=['P&L ($)']), use_container_width=True, height=300)
            else:
                st.info("Scanning Market for Scalp Entry...")

    time.sleep(1) # Har 1 second mein update karega
            
