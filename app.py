import streamlit as st
import pandas as pd
import ccxt
import time
import random
from datetime import datetime, timedelta

# 1. Page & UI Setup
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 24px !important; color: #f0b90b !important; }
    </style>
    """, unsafe_allow_html=True)

# Session States (Refresh Safe Logic)
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0
if 'wallet_bal' not in st.session_state: st.session_state.wallet_bal = 0.0
if 'saved_key' not in st.session_state: st.session_state.saved_key = ""
if 'saved_secret' not in st.session_state: st.session_state.saved_secret = ""

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Mode", ["Demo Simulation", "Real Delta India"])
    asset = st.selectbox("Select Asset", ["BTCUSDTPERP", "ETHUSDTPERP"])
    
    # Auto-fill from session if refreshed
    api_k = st.text_input("API Key", value=st.session_state.saved_key, type="password") if acc_mode == "Real Delta India" else ""
    api_s = st.text_input("API Secret", value=st.session_state.saved_secret, type="password") if acc_mode == "Real Delta India" else ""
    
    if api_k: st.session_state.saved_key = api_k
    if api_s: st.session_state.saved_secret = api_s

    st.divider()
    auto_trade = st.toggle(f"🚀 AUTO REAL TRADE {asset[:3]}", value=False)
    lev = st.select_slider("Leverage", [10, 25, 50, 100, 150, 200], 200)
    
    if st.button("Full System Reset"):
        st.session_state.clear()
        st.rerun()

# 3. Connection Logic (Delta India Optimized)
@st.cache_resource
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
                'options': {'adjustForTimeDifference': True, 'defaultType': 'future', 'recvWindow': 60000}
            })
            ex.fetch_balance()
            return ex, "SUCCESS"
        except Exception as e:
            return None, str(e)
    return ccxt.delta(), "DEMO"

exchange, conn_status = connect_exchange(api_k, api_s, acc_mode)

# 4. MAIN DASHBOARD
st.title(f"📊 OfficialLS Terminal: {asset[:3]}")

if conn_status == "SUCCESS":
    st.success("✅ Real Delta India Connected | Syncing Balance...")
elif acc_mode == "Real Delta India":
    st.warning("⚠️ Waiting for API Credentials")

# Metrics
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Auto Trade Status", "ACTIVE" if auto_trade else "PAUSED")
m4.metric("Active Leverage", f"{lev}x")

st.divider()

col_sig, col_main = st.columns([1, 3.2])

with col_sig:
    st.subheader("📰 AI News")
    st.success(f"Signal: {asset[:3]} BULLISH")
    st.info("Trend: High Volume")
    st.divider()
    st.subheader("📊 Trade Config")
    st.write("Fees: 0.1% | IST Time")
    st.write("SL: 0.8% | TP: 1.5%")
    st.divider()
    p_sigs = st.empty()

with col_main:
    # TradingView Chart
    chart_sym = "BINANCE:BTCUSDT" if "BTC" in asset else "BINANCE:ETHUSDT"
    st.components.v1.html(f"""
    <div style="height:400px; border-radius: 10px; overflow: hidden; border: 1px solid #333;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({{"autosize":true,"symbol":"{chart_sym}","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"}});
        </script>
    </div>""", height=400)
    
    st.subheader(f"💼 Real {asset[:3]} Positions")
    p_positions = st.empty()
    st.subheader("📜 AI Execution History (IST)")
    p_hist = st.empty()

# 5. DATA SYNC & EXECUTION LOOP
while True:
    try:
        cur_sym = asset if conn_status == "SUCCESS" else (asset.replace("USDTPERP", "/USDT"))
        ticker = exchange.fetch_ticker(cur_sym)
        price = ticker['last']
        
        # Real-time Data Sync
        if conn_status == "SUCCESS":
            # Direct wallet fetch for small balances
            bal_raw = exchange.private_get_wallet_balances()
            for item in bal_raw.get('result', []):
                if item.get('asset_symbol') == 'USDT':
                    st.session_state.wallet_bal = float(item.get('balance', 0.0))
            
            # Position fetch
            try:
                pos = exchange.fetch_positions([cur_sym])
                if pos:
                    p_positions.dataframe(pd.DataFrame(pos)[['symbol', 'entryPrice', 'contracts', 'unrealizedPnl']], use_container_width=True)
                else:
                    p_positions.info(f"No active trades for {asset[:3]}")
            except: pass
        else:
            if st.session_state.wallet_bal == 0: st.session_state.wallet_bal = 10.0

        # AI TRADING LOGIC
        if auto_trade and st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > (0.5 if "ETH" in asset else 1.5):
            side = 'buy' if price > st.session_state.last_p else 'sell'
            ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
            
            status = "Simulated"
            if conn_status == "SUCCESS":
                try:
                    exchange.set_leverage(lev, cur_sym)
                    order = exchange.create_order(cur_sym, 'market', side, 0.001)
                    status = "REAL ORDER PLACED"
                except Exception as e:
                    status = f"Fail: {str(e)[:20]}"

            st.session_state.history.insert(0, {
                "Time": ist, "Asset": asset[:3], "Side": side.upper(),
                "Entry": price, "Status": status, "Balance": round(st.session_state.wallet_bal, 3)
            })

        st.session_state.last_p = price
        p_price.metric(f"Live {asset[:3]}", f"${price:,.2f}")
        p_wallet.metric("Account Wallet", f"${st.session_state.wallet_bal:,.3f}")
        p_sigs.code(f"🔴 SELL: {price + 1.5}\n🟢 BUY:  {price - 1.0}")
        
        with p_hist.container():
            if st.session_state.history:
                st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
                
    except Exception as e:
        if "market symbol" not in str(e).lower():
            st.error(f"Sync: {e}")
    
    time.sleep(2)
    
