import streamlit as st
import pandas as pd
import ccxt
import time
from datetime import datetime

# Page Configuration for Professional Look
st.set_page_config(page_title="OfficialLS Pro Terminal", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for Dark Mode Professional UI
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: white; }
    .stMetric { background-color: #1e2329; border-radius: 10px; padding: 10px; border: 1px solid #363a45; }
    iframe { border-radius: 10px; border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR - Trading Settings
with st.sidebar:
    st.header("⚡ OfficialLS Control")
    mode = st.radio("Trading Mode", ["Paper Trading", "Delta Real Account"])
    leverage = st.slider("Leverage", 1, 50, 25)
    if mode == "Delta Real Account":
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("API Secret", type="password")

# TOP BAR - Live Prices
exchange = ccxt.delta()
ticker = exchange.fetch_ticker('BTC/USDT')
live_p = ticker['last']

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("BTC/USDT", f"${live_p}", f"{ticker['percentage']}%")
col_b.metric("24h High", f"${ticker['high']}")
col_c.metric("24h Low", f"${ticker['low']}")
col_d.metric("AI Sentiment", "BULLISH", "Strong")

# MAIN SECTION - TradingView Live Chart
st.subheader("📊 Live Trading Terminal")
# TradingView Widget Integration
tradingview_html = f"""
    <div class="tradingview-widget-container" style="height:500px;">
        <div id="tradingview_chart"></div>
        <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
        <script type="text/javascript">
        new TradingView.widget({{
            "autosize": true,
            "symbol": "BINANCE:BTCUSDT",
            "interval": "5",
            "timezone": "Etc/UTC",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "container_id": "tradingview_chart"
        }});
        </script>
    </div>
    """
st.components.v1.html(tradingview_html, height=500)

# LOWER SECTION - Execution & History
col_e, col_f = st.columns([1, 2])

with col_e:
    st.subheader("🎯 AI Execution")
    auto_pilot = st.toggle("Activate AI Auto-Trade")
    if auto_pilot:
        st.info("AI Scanning Patterns: Bull Flag Detected...")
        if st.button("Force Manual Entry"):
            st.toast("Executing Order on Delta...")

with col_f:
    st.subheader("📜 Order History")
    # Sample Data
    history_data = {
        "Time": [datetime.now().strftime("%H:%M:%S")],
        "Type": ["LONG"],
        "Entry": [live_p],
        "SL": [live_p * 0.995],
        "TP": [live_p * 1.01],
        "Result": ["RUNNING"]
    }
    st.table(pd.DataFrame(history_data))
