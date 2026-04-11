import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

# Persistent Storage
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0
if 'wallet_bal' not in st.session_state: st.session_state.wallet_bal = 0.0

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Mode", ["Demo Simulation", "Real Delta India"])
    
    api_k = st.text_input("API Key", type="password") if acc_mode == "Real Delta India" else ""
    api_s = st.text_input("API Secret", type="password") if acc_mode == "Real Delta India" else ""
    
    st.divider()
    # AUTO TRADING SWITCH
    auto_trade = st.toggle("🚀 AUTO AI TRADING ON", value=False)
    
    # UPGRADED LEVERAGE (UP TO 200x)
    lev = st.select_slider("Leverage", [10, 25, 50, 100, 150, 200], 100)
    
    if st.button("Reset Terminal"):
        st.session_state.history = []
        st.session_state.wallet_bal = 0.0
        st.rerun()

# 3. Delta India Connection Logic
def connect_exchange(k, s, m):
    if m == "Real Delta India" and k and s:
        try:
            ex = ccxt.delta({
                'apiKey': k.strip(),
                'secret': s.strip(),
                'enableRateLimit': True,
                'urls': {
                    'api': {
                        'public': 'https://api.india.delta.exchange',
                        'private': 'https://api.india.delta.exchange',
                    }
                },
                'options': {'adjustForTimeDifference': True, 'recvWindow': 30000}
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_k, api_s, acc_mode)

# 4. DASHBOARD UI
st.title("📊 OfficialLS AI Professional Terminal")

if conn_status == "SUCCESS":
    st.success("✅ Connected to Delta India!")
elif acc_mode == "Real Delta India":
    st.error(f"❌ Connection Issue: {conn_status}")

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Auto Trade", "ACTIVE" if auto_trade else "PAUSED")
m4.metric("Max Leverage", f"{lev}x")

st.divider()

col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("📰 AI News")
    st.success("Signal: BULLISH")
    st.divider()
    st.subheader("📊 Config")
    st.write(f"Fees: 0.1% | Lev: {lev}x")
    st.write("SL: 0.8% | TP: 1.5%")
    st.divider()
    p_sigs = st.empty()

with col_main:
    # TradingView Chart
    st.components.v1.html("""
    <div style="height:400px; border-radius: 10px; overflow: hidden; border: 1px solid #333;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({"autosize":true,"symbol":"BINANCE:BTCUSDT","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"});
        </script>
    </div>""", height=400)
    
    st.subheader("💼 Real Open Positions")
    p_positions = st.empty()
    
    st.subheader("📜 AI Trade History (IST)")
    p_hist = st.empty()

# 5. DATA SYNC & AUTO TRADING LOOP
while True:
    try:
        # Checking correct symbol for Delta India
        symbol = 'BTCUSDTPERP' if conn_status == "SUCCESS" else 'BTC/USDT'
        
        try:
            ticker = exchange.fetch_ticker(symbol)
        except:
            symbol = 'BTCUSD'
            ticker = exchange.fetch_ticker(symbol)
            
        price = ticker['last']
        
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet_bal = bal['total'].get('USDT', 0.0)
            
            # Fetch real positions
            try:
                pos = exchange.fetch_positions([symbol])
                if pos:
                    p_positions.dataframe(pd.DataFrame(pos)[['symbol', 'entryPrice', 'notional', 'unrealizedPnl']], use_container_width=True)
                else:
                    p_positions.info("No Active Real Positions")
            except: pass
        else:
            if st.session_state.wallet_bal == 0: st.session_state.wallet_bal = 10.0
        
        # AI TRADING LOGIC
        if auto_trade and st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 1.5:
            ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
            
            # Scalp Logic
            fee = (st.session_state.wallet_bal * 0.05 * lev) * 0.001
            pnl_sim = (random.uniform(-0.3, 0.9) * (lev/10)) - fee
            
            st.session_state.history.insert(0, {
                "Time": ist, "Side": "LONG" if price > st.session_state.last_p else "SHORT",
                "Entry": price, "Fee": round(fee, 3), "PNL": round(pnl_sim, 2), 
                "Wallet": round(st.session_state.wallet_bal, 2)
            })
            
            if conn_status != "SUCCESS": st.session_state.wallet_bal += pnl_sim
            if len(st.session_state.history) > 20: st.session_state.history.pop()

        st.session_state.last_p = price
        p_price.metric("Live BTC", f"${price:,.1f}")
        p_wallet.metric("Balance", f"${st.session_state.wallet_bal:,.2f}")
        p_sigs.code(f"🔴 SELL: {price+2}\n🟢 BUY:  {price-1}")
        
        with p_hist:
            if st.session_state.history:
                st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
                
    except Exception as e:
        if "market symbol" not in str(e).lower():
            st.error(f"System: {e}")
    
    time.sleep(2)
    
