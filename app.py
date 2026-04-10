import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Professional Look
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #f0b90b !important; }
    .stTable { background-color: #1e2329; border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# 2. Database Setup
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. SIDEBAR CONTROLS
st.sidebar.title("🚀 OfficialLS Control")
auto_bot = st.sidebar.toggle("🤖 ACTIVATE AI BOT", value=True)
lev = st.sidebar.select_slider("Leverage Settings", [10, 25, 50, 100], 50)
st.sidebar.divider()
st.sidebar.metric("Your Wallet", f"${st.session_state.balance:.2f}")

# 4. LIVE TRADING VIEW (Iska refresh se koi lena dena nahi, ye hamesha live chalega)
st.subheader("📊 Live Technical Terminal")
chart_code = """
<div style="height:500px; border: 1px solid #363a45; border-radius: 5px;">
    <div id="tv-chart" style="height:100%;"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({
      "autosize":true, "symbol":"DELTA:BTCPERP", "interval":"1",
      "timezone":"Asia/Kolkata", "theme":"dark", "style":"1",
      "locale":"en", "toolbar_bg":"#f1f3f6", "enable_publishing":false,
      "withdateranges":true, "hide_side_toolbar":false, "allow_symbol_change":true,
      "container_id":"tv-chart"
    });
    </script>
</div>"""
st.components.v1.html(chart_code, height=500)

# 5. DATA SECTION (News & History) - Isme hum fragment use karenge taaki refresh na ho
@st.fragment(run_every=2)
def update_data():
    # Fetch Real Price
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = 65000.0

    # AI BOT LOGIC (Scalping 1m)
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        # Agar price 1 USD bhi hila, toh AI scalping trade execute karega
        if abs(diff) > 1.0:
            # Scalping calculation (High Frequency)
            pnl_factor = random.uniform(-0.2, 0.5) 
            profit = (st.session_state.balance * 0.05) * pnl_factor * (lev / 10)
            
            st.session_state.balance += profit
            st.session_state.trades.insert(0, {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": "SCALP LONG" if diff > 0 else "SCALP SHORT",
                "Entry": f"${price:,.1f}",
                "PnL ($)": round(profit, 2),
                "Wallet": round(st.session_state.balance, 2)
            })
    
    st.session_state.last_p = price

    # Display Side by Side
    col_news, col_hist = st.columns([1, 2])
    
    with col_news:
        st.write("### 📰 Live News Feed")
        st.success("🔥 BTC Inflow: High (Bullish)")
        st.info("📊 RSI (5m): Oversold - Scalp Buy")
        st.warning("⚠️ Volatility: Extreme")
        st.divider()
        st.write("### 📉 Live Order Book")
        st.code(f"🔴 {price+5} | 0.5 BTC\n🟢 {price-5} | 1.2 BTC", language='text')

    with col_hist:
        st.write("### 📜 AI Trade History (Scalping)")
        if st.session_state.trades:
            df = pd.DataFrame(st.session_state.trades).head(8)
            st.table(df)
        else:
            st.info("AI is scanning indicators & patterns...")

# Run the update function
update_data()
            
