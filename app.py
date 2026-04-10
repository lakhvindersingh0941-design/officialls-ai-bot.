import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Custom CSS for Dark UI & Clean Tables
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #f0b90b !important; font-weight: bold; }
    .stDataFrame { border: 1px solid #363a45; border-radius: 5px; }
    .status-up { color: #00ff00; font-weight: bold; }
    .status-down { color: #ff0000; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database (Session Persistence)
# Inhe restart hone par bhi save rakhne ki koshish karega jab tak tab khula hai
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. TOP NAVIGATION / HEADER
c1, c2, c3, c4 = st.columns(4)

# 4. SIDEBAR - CONTROL PANEL
with st.sidebar:
    st.header("OfficialLS AI Bot")
    auto_bot = st.toggle("Activate AI Trading", value=True)
    lev = st.select_slider("Leverage", [10, 20, 50, 100], 50)
    if st.button("Reset Wallet & History"):
        st.session_state.wallet = 100.0
        st.session_state.history = []
        st.rerun()

# 5. LIVE CHART SECTION (Always Live)
st.subheader("📊 BTC/USDT Live Terminal")
chart_code = """
<div style="height:550px; border: 1px solid #363a45;">
    <div id="tradingview_123" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
      "autosize": true, "symbol": "DELTA:BTCPERP", "interval": "1",
      "timezone": "Asia/Kolkata", "theme": "dark", "style": "1",
      "locale": "en", "enable_publishing": false, "allow_symbol_change": true,
      "container_id": "tradingview_123"
    });
    </script>
</div>"""
st.components.v1.html(chart_code, height=550)

# 6. LIVE DATA & AI LOGIC (No-Flash Refresh)
@st.fragment(run_every=1)
def sync_data():
    try:
        ex = ccxt.delta()
        ticker = ex.fetch_ticker('BTC/USDT')
        price = ticker['last']
    except:
        price = 65000.0

    # Header Metrics Update
    c1.metric("BTC Price", f"${price:,.1f}")
    c2.metric("Overall Wallet", f"${st.session_state.wallet:,.2f}")
    
    # AI Trading Logic
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        
        # Agar price $2 upar ya niche gaya toh trade lega
        if abs(diff) > 2.0:
            # Scalping calculation
            pnl_amt = random.uniform(-0.5, 1.5) * (lev / 10)
            st.session_state.wallet += pnl_amt
            
            # History entry (Limit to last 100)
            new_entry = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Asset": "BTC/USDT",
                "Type": "LONG" if diff > 0 else "SHORT",
                "Entry": f"${price:,.1f}",
                "PnL ($)": round(pnl_amt, 2),
                "Total Wallet": round(st.session_state.wallet, 2)
            }
            st.session_state.history.insert(0, new_entry)
            if len(st.session_state.history) > 100:
                st.session_state.history.pop()

    st.session_state.last_p = price

    # --- DISPLAY SECTIONS ---
    col_news, col_hist = st.columns([1, 2])
    
    with col_news:
        st.write("### 📰 News & Signals")
        st.info("💡 Signal: Scalp LONG possible near EMA 20")
        st.success("✅ News: BTC Institutional Inflow Up")
        st.divider()
        st.write("### 📋 Order Book")
        st.code(f"🔴 {price+4.5} | 0.82 BTC\n🟢 {price-2.1} | 1.15 BTC")

    with col_hist:
        st.write("### 📜 AI Scalping History (Last 100)")
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            
            # Formatting P&L column color
            def color_pnl(val):
                color = '#00ff00' if val > 0 else '#ff0000'
                return f'color: {color}; font-weight: bold;'
            
            st.dataframe(
                df.style.applymap(color_pnl, subset=['PnL ($)']),
                use_container_width=True,
                height=400
            )
        else:
            st.warning("Scanning market for professional scalp entry...")

# Execute
sync_data()
            
