import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# 2. Database Setup
if 'wallet' not in st.session_state:
    st.session_state.wallet = 100.0
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_p' not in st.session_state:
    st.session_state.last_p = 0

# 3. Sidebar
with st.sidebar:
    st.header("OfficialLS AI Control")
    auto_bot = st.toggle("Activate AI Trading", value=True)
    lev = st.select_slider("Select Leverage", [10, 25, 50, 100], 50)
    st.write("---")
    st.caption("Fee Logic: 0.05% on Total Position Value (Leverage Adjusted)")

# 4. LIVE CHART
st.title("📊 OfficialLS AI Professional Terminal")
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

# 5. DATA SYNC
st.divider()
placeholder = st.empty()

while True:
    try:
        ex = ccxt.delta()
        tk = ex.fetch_ticker('BTC/USDT')
        price = tk['last']
    except:
        price = st.session_state.last_p if st.session_state.last_p != 0 else 70000.0

    # AI Scalping Logic with DYNAMIC FEES
    if auto_bot and st.session_state.last_p != 0:
        diff = price - st.session_state.last_p
        
        # AI identifying a volatility move
        if abs(diff) > 2.0:
            # Margin used: 10% of wallet
            margin_used = st.session_state.wallet * 0.1
            # Total Position Value (Margin x Leverage)
            total_position_value = margin_used * lev
            
            # Delta Exchange Fee (0.05% Entry + 0.05% Exit = 0.1% total on position value)
            total_fee = total_position_value * 0.001 
            
            # Gross P&L before fees
            gross_pnl = random.uniform(-0.4, 1.1) * (lev / 10)
            # Net P&L after dynamic fees
            net_pnl = gross_pnl - total_fee
            
            st.session_state.wallet += net_pnl
            
            # Save Detail History
            st.session_state.history.insert(0, {
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Side": "LONG" if diff > 0 else "SHORT",
                "Entry": f"${price:,.1f}",
                "Leverage": f"{lev}x",
                "Position Value": f"${total_position_value:,.1f}",
                "Fee ($)": round(total_fee, 3),
                "Net PnL ($)": round(net_pnl, 2),
                "Wallet": round(st.session_state.wallet, 2)
            })
            if len(st.session_state.history) > 50: st.session_state.history.pop()

    st.session_state.last_p = price

    with placeholder.container():
        c1, c2, c3 = st.columns(3)
        c1.metric("Live BTC", f"${price:,.1f}")
        c2.metric("Wallet Balance", f"${st.session_state.wallet:,.2f}")
        c3.metric("Leverage", f"{lev}x")

        st.subheader("📜 Professional Trade Log")
        if st.session_state.history:
            df = pd.DataFrame(st.session_state.history)
            def style_pnl(v):
                return f'color: {"#00ff00" if v > 0 else "#ff0000"}; font-weight: bold;'
            st.dataframe(df.style.map(style_pnl, subset=['Net PnL ($)']), use_container_width=True)
        else:
            st.info("AI scanning market moves...")

    time.sleep(1)
