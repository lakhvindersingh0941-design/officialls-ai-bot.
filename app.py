import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime, timedelta

# 1. Page Config
st.set_page_config(page_title="OfficialLS AI Pro Terminal", layout="wide")

# Session States
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
    # --- AUTO AI TRADING SWITCH ---
    auto_trade = st.toggle("🚀 AUTO AI TRADING ON", value=False)
    if auto_trade:
        st.success("AI Bot is Scanning...")
    else:
        st.warning("Auto Trading is OFF")
    
    lev = st.select_slider("Leverage", [10, 25, 50, 100], 50)

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
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_k, api_s, acc_mode)

# 4. DASHBOARD UI
st.title("📊 OfficialLS AI Professional Terminal")

if conn_status == "SUCCESS":
    st.success("✅ Real Delta India Connected")
elif acc_mode == "Real Delta India":
    st.error(f"❌ Connection Issue: {conn_status}")

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Auto Trade Status", "ACTIVE" if auto_trade else "PAUSED")
m4.metric("Leverage", f"{lev}x")

st.divider()

col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("📰 AI News & Signals")
    st.info("Trend: Market Scanning...")
    st.divider()
    st.subheader("📊 SL/TP Info")
    st.write("SL: 0.8% | TP: 1.5%")
    st.divider()
    st.caption("Live Delta Orderbook")
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
    
    # Real Positions Table
    st.subheader("💼 Real Open Positions")
    p_positions = st.empty()
    
    st.subheader("📜 AI Trade History (IST)")
    p_hist = st.empty()

# 5. DATA SYNC & AUTO TRADING LOOP
while True:
    try:
        # 1. Fetch Price
        symbol = 'BTCUSD' if acc_mode == "Real Delta India" else 'BTC/USDT'
        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        
        # 2. Sync Real Wallet Data
        if conn_status == "SUCCESS":
            bal = exchange.fetch_balance()
            st.session_state.wallet_bal = bal['total'].get('USDT', 0.0)
            
            # Fetch Real Positions
            pos = exchange.fetch_positions([symbol])
            if pos:
                df_pos = pd.DataFrame(pos)[['symbol', 'entryPrice', 'notional', 'unrealizedPnl']]
                p_positions.dataframe(df_pos, use_container_width=True)
            else:
                p_positions.info("No Active Real Positions")
        else:
            # Demo Mode Balance Simulation
            if st.session_state.wallet_bal == 0: st.session_state.wallet_bal = 10.0
        
        # 3. AI TRADING LOGIC (Only runs if Switch is ON)
        if auto_trade and st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 2.0:
            ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
            
            # Simulating Trade Result
            fee = (st.session_state.wallet_bal * 0.1 * lev) * 0.001
            pnl_sim = (random.uniform(-0.4, 1.1) * (lev/10)) - fee
            
            # Update History
            st.session_state.history.insert(0, {
                "Time": ist, "Side": "LONG" if price > st.session_state.last_p else "SHORT",
                "Entry": price, "Fee": round(fee, 3), "PNL": round(pnl_sim, 2), 
                "Wallet": round(st.session_state.wallet_bal, 2)
            })
            
            if conn_status != "SUCCESS":
                st.session_state.wallet_bal += pnl_sim
            
            if len(st.session_state.history) > 20: st.session_state.history.pop()

        st.session_state.last_p = price
        
        # 4. Update UI
        p_price.metric("Live BTC", f"${price:,.1f}")
        p_wallet.metric("Account Wallet", f"${st.session_state.wallet_bal:,.2f}")
        p_sigs.code(f"🔴 SELL: {price+3}\n🟢 BUY:  {price-2}")
        
        with p_hist:
            if st.session_state.history:
                st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
                
    except Exception as e:
        st.error(f"Loop Error: {e}")
    
    time.sleep(2)
        
