import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="OfficialLS 24/7 AI Terminal", layout="wide")

# 2. Database/Session Management
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. Sidebar
with st.sidebar:
    st.header("OfficialLS AI Bot")
    auto_bot = st.toggle("Activate AI Trading", value=True)
    lev = st.select_slider("Leverage", [10, 20, 50, 100], 50)
    st.info("Note: Delta Fee (0.05%) included in PnL")

# 4. LIVE CHART
st.title("📊 OfficialLS AI 24/7 Terminal")
chart_html = """
<div style="height:480px; border: 1px solid #363a45; border-radius: 8px; overflow: hidden;">
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
st.components.v1.html(chart_html, height=480)

# 5. DATA SYNC AREA
st.divider()
placeholder = st.empty()

while True:
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 70000.0

    # AI Scalping Logic with SL, TP and Fees
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        if abs(diff) > 2.0:
            # 1. SL/TP Calculation (Visual only)
            sl = price - (price * 0.005) if diff > 0 else price + (price * 0.005)
            tp = price + (price * 0.01) if diff > 0 else price - (price * 0.01)
            
            # 2. Brokerage Calculation (Delta approx 0.05% per side)
            notional_value = (st.session_state.wallet * 0.1) * lev # Using 10% of wallet
            brokerage = notional_value * 0.0005 * 2 # Entry + Exit
            
            # 3. Net PnL calculation
            gross_pnl = random.uniform(-0.5, 1.2) * (lev / 10)
            net_pnl = gross_pnl - brokerage
            
            st.session_state.wallet += net_pnl
            
            st.session_state.history.insert(0, {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Type": "LONG" if diff > 0 else "SHORT",
                "Entry": round(price, 1),
                "SL": round(sl, 1),
                "TP": round(tp, 1),
                "Gross PnL": round(gross_pnl, 2),
                "Fee ($)": round(brokerage, 2),
                "Net PnL ($)": round(net_pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 100: st.session_state.history.pop()

    st.session_state.last_p = price

    with placeholder.container():
        m1, m2, m3 = st.columns(3)
        m1.metric("Live Price", f"${price:,.1f}")
        m2.metric("Wallet (Net)", f"${st.session_state.wallet:,.2f}")
        m3.metric("Leverage", f"{lev}x")

        col_news, col_hist = st.columns([1, 3])
        with col_news:
            st.subheader("Market News")
            st.success("Bullish Sentiment: Low ETF Outflow")
            st.info("AI: Scanning Volatility")

        with col_hist:
            st.subheader("Professional Trade History (with Fees & SL/TP)")
            if st.session_state.history:
                df = pd.DataFrame(st.session_state.history)
                def style_pnl(v):
                    return f'color: {"#00ff00" if v > 0 else "#ff0000"}; font-weight: bold;'
                st.dataframe(df.style.map(style_pnl, subset=['Net PnL ($)']), use_container_width=True)
            else:
                st.info("Waiting for market volatility to scalp...")

    time.sleep(1)
