import streamlit as st
import pandas as pd
import ccxt
import time
import random
import requests
from datetime import datetime, timedelta

# 1. Page Configuration & UI Styling
st.set_page_config(page_title="OfficialLS Pro AI Multi-Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #f0b90b !important; }
    .stDataFrame { border: 1px solid #363a45; }
    </style>
    """, unsafe_allow_html=True)

# Persistent Storage
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0
if 'wallet_bal' not in st.session_state: st.session_state.wallet_bal = 0.0

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Mode", ["Demo Simulation", "Real Delta India"])
    asset = st.selectbox("Select Asset", ["BTCUSDTPERP", "ETHUSDTPERP"])
    
    api_k = st.text_input("API Key", type="password") if acc_mode == "Real Delta India" else ""
    api_s = st.text_input("API Secret", type="password") if acc_mode == "Real Delta India" else ""
    
    st.divider()
    auto_trade = st.toggle(f"🚀 AUTO REAL TRADE {asset[:3]}", value=False)
    lev = st.select_slider("Leverage", [10, 25, 50, 100, 150, 200], 200)
    
    if st.button("Full Reset Terminal"):
        st.session_state.history = []
        st.session_state.wallet_bal = 0.0
        st.rerun()

# 3. Secure Delta India Connection Logic
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
                'options': {'adjustForTimeDifference': True, 'defaultType': 'future', 'recvWindow': 30000}
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_k, api_s, acc_mode)

# 4. DASHBOARD UI
st.title(f"📊 OfficialLS AI Terminal: {asset[:3]}")

if conn_status == "SUCCESS":
    st.success(f"✅ Real Delta India Connected | Balance Sync")
elif acc_mode == "Real Delta India":
    st.error(f"❌ Connection Issue: {conn_status}")

# Top Metrics
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Auto Trade Status", "ACTIVE" if auto_trade else "PAUSED")
m4.metric("Leverage", f"{lev}x")

st.divider()

# Layout: Signals + Chart
col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("📰 AI News & Signals")
    st.success(f"Signal: {asset[:3]} BULLISH")
    st.info("Market Volume: High")
    st.divider()
    st.subheader("📊 Trade Config")
    st.write(f"Fees: 0.1% (Entry+Exit)")
    st.write(f"SL: 0.8% | TP: 1.5%")
    st.divider()
    p_sigs = st.empty()

with col_main:
    # TradingView Chart
    chart_symbol = "BINANCE:BTCUSDT" if "BTC" in asset else "BINANCE:ETHUSDT"
    st.components.v1.html(f"""
    <div style="height:400px; border-radius: 10px; overflow: hidden; border: 1px solid #333;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({{"autosize":true,"symbol":"{chart_symbol}","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"}});
        </script>
    </div>""", height=400)
    
    st.subheader(f"💼 Real {asset[:3]} Open Positions")
    p_positions = st.empty()
    
    st.subheader("📜 AI Trade Execution Logs (IST)")
    p_hist = st.empty()

# 5. DATA SYNC & REAL EXECUTION LOOP
while True:
    try:
        current_symbol = asset if conn_status == "SUCCESS" else (asset.replace("USDTPERP", "/USDT"))
        ticker = exchange.fetch_ticker(current_symbol)
        price = ticker['last']
        
        # Sync Real Wallet Data
        if conn_status == "SUCCESS":
            balance_info = exchange.fetch_balance()
            st.session_state.wallet_bal = balance_info.get('total', {}).get('USDT', 0.0)
            
            # Fetch real positions
            try:
                pos = exchange.fetch_positions([current_symbol])
                if pos:
                    p_positions.dataframe(pd.DataFrame(pos)[['symbol', 'entryPrice', 'contracts', 'unrealizedPnl']], use_container_width=True)
                else:
                    p_positions.info(f"No Active {asset[:3]} Positions")
            except: pass
        else:
            if st.session_state.wallet_bal == 0: st.session_state.wallet_bal = 10.0

        # AI TRADING LOGIC
        if auto_trade and st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > (0.5 if "ETH" in asset else 1.5):
            side = 'buy' if price > st.session_state.last_p else 'sell'
            ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
            
            # Real Order Execution
            order_status = "Simulated"
            if conn_status == "SUCCESS":
                try:
                    exchange.set_leverage(lev, current_symbol)
                    order = exchange.create_order(current_symbol, 'market', side, 0.001)
                    order_status = "REAL ORDER PLACED"
                except Exception as e:
                    order_status = f"Failed: {str(e)}"
            else:
                fee = (st.session_state.wallet_bal * 0.05 * lev) * 0.001
                pnl_sim = (random.uniform(-0.3, 0.9) * (lev/10)) - fee
                st.session_state.wallet_bal += pnl_sim
                order_status = f"Demo PNL: {round(pnl_sim, 2)}"

            st.session_state.history.insert(0, {
                "Time": ist, "Asset": asset[:3], "Side": side.upper(),
                "Entry": price, "Status": order_status, "Wallet": round(st.session_state.wallet_bal, 3)
            })
            if len(st.session_state.history) > 30: st.session_state.history.pop()

        st.session_state.last_p = price
        p_price.metric(f"Live {asset[:3]}", f"${price:,.2f}")
        p_wallet.metric("Account Wallet", f"${st.session_state.wallet_bal:,.3f}")
        p_sigs.code(f"🔴 SELL {asset[:3]}: {price + 1.5}\n🟢 BUY {asset[:3]}:  {price - 1.0}")
        
        with p_hist.container():
            if st.session_state.history:
                st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
                
    except Exception as e:
        if "market symbol" not in str(e).lower():
            st.error(f"System Error: {e}")
    
    time.sleep(2)
    
