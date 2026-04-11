import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import json
from datetime import datetime, timedelta

# 1. Terminal Configuration
st.set_page_config(page_title="OfficialLS Pro AI Terminal", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 26px !important; color: #f0b90b !important; }
    </style>
    """, unsafe_allow_html=True)

# Session States
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0
if 'real_bal' not in st.session_state: st.session_state.real_bal = 0.0

# 2. SIDEBAR
with st.sidebar:
    st.title("OfficialLS AI Bot")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Account Mode", ["Demo Simulation", "Real Delta India"])
    # Delta India use BTCUSD or ETHUSD symbols
    asset_choice = st.selectbox("Select Asset", ["BTCUSD", "ETHUSD"])
    
    api_k = st.text_input("API Key", type="password", key="final_k")
    api_s = st.text_input("API Secret", type="password", key="final_s")
    
    st.divider()
    auto_trade = st.toggle(f"🚀 AUTO REAL TRADE {asset_choice[:3]}", value=False)
    lev = st.select_slider("Leverage", [10, 25, 50, 100, 150, 200], 200)

# 3. Direct Delta India API Functions (Corrected Headers)
def get_delta_headers(method, path, query, payload, api_key, api_secret):
    timestamp = str(int(time.time()))
    # Critical: METHOD + TIMESTAMP + PATH + QUERY + PAYLOAD
    msg = method + timestamp + path + query + payload
    signature = hmac.new(api_secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()
    return {
        "api-key": api_key,
        "signature": signature, # Fixed Header Name
        "timestamp": timestamp, # Fixed Header Name
        "Content-Type": "application/json"
    }

def fetch_real_bal(api_key, api_secret):
    path = "/v2/wallet/balances"
    try:
        headers = get_delta_headers("GET", path, "", "", api_key, api_secret)
        r = requests.get("https://api.india.delta.exchange" + path, headers=headers, timeout=5)
        data = r.json()
        for item in data.get('result', []):
            if item.get('asset_symbol') in ['USDT', 'INR']:
                val = float(item.get('balance', 0.0))
                # Convert INR to USD approx display
                return val if item.get('asset_symbol') == 'USDT' else (val / 88.5)
    except: return 0.0
    return 0.0

# 4. DASHBOARD UI
st.title(f"📊 OfficialLS Professional Terminal: {asset_choice}")

m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
m3.metric("Auto Trade Status", "ACTIVE" if auto_trade else "PAUSED")
m4.metric("Leverage", f"{lev}x")

st.divider()

col_sig, col_main = st.columns([1, 3.2])

with col_sig:
    st.subheader("📰 AI Signals")
    st.success(f"{asset_choice[:3]} BULLISH")
    st.divider()
    st.subheader("📊 Trade Config")
    st.write("Fees: 0.1% | IST Time")
    st.write("Lot Size: 1 (Min)")
    st.divider()
    p_sigs = st.empty()

with col_main:
    # TradingView Chart
    chart_sym = "BINANCE:BTCUSDT" if "BTC" in asset_choice else "BINANCE:ETHUSDT"
    st.components.v1.html(f"""
    <div style="height:400px; border-radius: 10px; overflow: hidden; border: 1px solid #333;">
        <div id="tv" style="height:100%;"></div>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>
        new TradingView.widget({{"autosize":true,"symbol":"{chart_sym}","theme":"dark","container_id":"tv","timezone":"Asia/Kolkata"}});
        </script>
    </div>""", height=400)
    
    st.subheader("📜 AI Execution Logs (IST Time)")
    p_hist = st.empty()

# 5. DATA SYNC & EXECUTION LOOP
while True:
    try:
        # Get Price
        price_r = requests.get(f"https://api.india.delta.exchange/v2/tickers/{asset_choice}").json()
        price = float(price_r['result']['last_price'])
        
        # Sync Real Balance
        if acc_mode == "Real Delta India" and api_k and api_s:
            st.session_state.real_bal = fetch_real_bal(api_k, api_s)
        else:
            if st.session_state.real_bal == 0: st.session_state.real_bal = 10.0

        # AI AUTO TRADE LOGIC
        if auto_trade and st.session_state.last_p != 0 and abs(price - st.session_state.last_p) > 1.2:
            side = 'buy' if price > st.session_state.last_p else 'sell'
            ist = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%H:%M:%S")
            
            log_status = "Demo Trade"
            if acc_mode == "Real Delta India" and api_k and api_s:
                p_id = 1 if "BTC" in asset_choice else 3 # Standard Delta India IDs
                
                # 1. Set Leverage
                path_lev = "/v2/products/leverage"
                lev_payload = json.dumps({"product_id": p_id, "leverage": str(lev)})
                lev_headers = get_delta_headers("POST", path_lev, "", lev_payload, api_k, api_s)
                requests.post("https://api.india.delta.exchange" + path_lev, headers=lev_headers, data=lev_payload)
                
                # 2. Market Order (Size must be Integer)
                path_order = "/v2/orders"
                order_payload = json.dumps({
                    "product_id": p_id,
                    "size": 1, # 1 lot is minimum, 0.001 is invalid
                    "side": side,
                    "order_type": "market_order"
                })
                order_headers = get_delta_headers("POST", path_order, "", order_payload, api_k, api_s)
                
                res = requests.post("https://api.india.delta.exchange" + path_order, headers=order_headers, data=order_payload)
                
                if res.status_code == 200:
                    log_status = "REAL ORDER SUCCESS"
                else:
                    err_msg = res.json().get('error', {}).get('message', 'Error')
                    log_status = f"Fail: {err_msg[:15]}"

            st.session_state.history.insert(0, {
                "Time": ist, "Asset": asset_choice[:3], "Side": side.upper(),
                "Entry": price, "Status": log_status, "Wallet": round(st.session_state.real_bal, 3)
            })
            if len(st.session_state.history) > 30: st.session_state.history.pop()

        st.session_state.last_p = price
        p_price.metric(f"Live {asset_choice[:3]}", f"${price:,.2f}")
        p_wallet.metric("Balance ($ Approx)", f"${st.session_state.real_bal:,.3f}")
        p_sigs.code(f"🔴 SELL: {price + 1.2}\n🟢 BUY:  {price - 0.8}")
        
        with p_hist:
            if st.session_state.history:
                st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)
                
    except Exception as e: pass
    
    time.sleep(2)
    
