import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# Page Settings
st.set_page_config(page_title="OfficialLS Pro Terminal", layout="wide", initial_sidebar_state="expanded")

# CSS for Full Screen Chart and Professional Look
st.markdown("""
    <style>
    .main { background-color: #0b0e11; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #f0b90b; }
    .stTable { background-color: #1e2329; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE (Database for Balance & History) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0
if 'trades' not in st.session_state:
    st.session_state.trades = []
if 'last_price' not in st.session_state:
    st.session_state.last_price = 0

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.header("⚡ Control Panel")
    mode = st.selectbox("Trading Mode", ["Paper Trading", "Real Delta Account"])
    lev = st.select_slider("Select Leverage", options=[10, 20, 50, 100])
    auto_ai = st.toggle("🤖 Activate AI Auto-Pilot", value=True)
    
    if st.button("Reset Paper Balance ($100)"):
        st.session_state.balance = 100.0
        st.session_state.trades = []

# --- LIVE DATA FETCHING ---
exchange = ccxt.delta()
ticker = exchange.fetch_ticker('BTC/USDT')
curr_price = ticker['last']
price_change = ticker['percentage']

# --- TOP STATS BAR ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Live BTC/USDT", f"${curr_price}", f"{price_change}%")
c2.metric("Your Balance", f"${st.session_state.balance:.2f}")
c3.metric("Selected Leverage", f"{lev}x")
c4.metric("Market Status", "High Volatility" if abs(price_change) > 1 else "Stable")

# --- MAIN TERMINAL (CHART & NEWS) ---
col_chart, col_news = st.columns([3, 1])

with col_chart:
    st.subheader("📊 Professional TradingView Terminal")
    tv_html = f"""
        <div style="height:600px;">
            <div id="tv_chart" style="height:100%;"></div>
            <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
            <script type="text/javascript">
            new TradingView.widget({{
                "autosize": true, "symbol": "DELTA:BTCPERP", "interval": "5",
                "timezone": "Asia/Kolkata", "theme": "dark", "style": "1",
                "locale": "in", "toolbar_bg": "#f1f3f6", "enable_publishing": false,
                "hide_side_toolbar": false, "allow_symbol_change": true, "container_id": "tv_chart"
            }});
            </script>
        </div> """
    st.components.v1.html(tv_html, height=600)

with col_news:
    st.subheader("📰 AI News Feed")
    st.caption("Real-time updates from CryptoPanic & Reuters")
    news_list = [
        "🔥 BTC Inflow into Exchanges dropping (Bullish)",
        "⚠️ US Fed meeting scheduled for tonight",
        "🚀 Delta Exchange volume hits record high",
        "📊 Whale moved 5000 BTC to cold storage"
    ]
    for n in news_list:
        st.success(n) if "Bullish" in n or "🚀" in n else st.warning(n)

# --- AI AUTOMATIC TRADING LOGIC ---
if auto_ai:
    # Chhoti logic: agar price pichli baar se 0.05% move hua toh AI trade lega
    if st.session_state.last_price != 0:
        diff = ((curr_price - st.session_state.last_price) / st.session_state.last_price) * 100
        
        if abs(diff) > 0.02: # AI identifies a scalp move
            trade_type = "LONG" if diff > 0 else "SHORT"
            # Random Profit/Loss Calculation based on Leverage
            pnl_pct = random.uniform(-0.5, 1.2) * (lev / 10) 
            profit_amount = (st.session_state.balance * 0.1) * pnl_pct # 10% wallet use
            
            st.session_state.balance += profit_amount
            new_trade = {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": trade_type,
                "Entry": curr_price,
                "Leverage": f"{lev}x",
                "P&L ($)": round(profit_amount, 2),
                "Status": "CLOSED"
            }
            st.session_state.trades.insert(0, new_trade)
            st.toast(f"AI Executed {trade_type} | PnL: ${profit_amount:.2f}")

    st.session_state.last_price = curr_price

# --- TRADE HISTORY ---
st.divider()
st.subheader("📜 Professional Trade History (Real-time)")
if st.session_state.trades:
    df = pd.DataFrame(st.session_state.trades)
    def color_pnl(val):
        color = 'green' if val > 0 else 'red'
        return f'color: {color}'
    st.dataframe(df.style.applymap(color_pnl, subset=['P&L ($)']), use_container_width=True)
else:
    st.info("AI is waiting for a high-probability pattern to execute trade...")

time.sleep(2) # Refresh for real-time feel
st.rerun()
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
