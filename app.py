import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import json
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(page_title="OfficialLS Safe Pro AI", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #eaecef; }
    [data-testid="stMetricValue"] { font-size: 28px !important; color: #f0b90b !important; font-weight: bold; }
    .stButton>button { width: 100%; background-color: #f0b90b; color: black; font-weight: bold; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Session States
if 'history' not in st.session_state: st.session_state.history = []
if 'last_p' not in st.session_state: st.session_state.last_p = 0
if 'last_trade_p' not in st.session_state: st.session_state.last_trade_p = 0
if 'last_trade_time' not in st.session_state: st.session_state.last_trade_time = 0
if 'real_bal' not in st.session_state: st.session_state.real_bal = 0.0
if 'series_step' not in st.session_state: st.session_state.series_step = 0

# 2. SIDEBAR
with st.sidebar:
    st.title("🦅 OfficialLS AI Pro")
    st.info("Yuva Neta Sangaria Edition")
    st.error("🔴 Whitelist IP: 74.220.48.23")
    
    acc_mode = st.radio("Mode", ["Demo Simulation", "Real Delta India"])
    asset_choice = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])
    
    api_k = st.text_input("API Key", type="password", key="real_k")
    api_s = st.text_input("API Secret", type="password", key="real_s")
    
    st.divider()
    auto_trade = st.toggle("🚀 START SAFE COMPOUNDING", value=False)
    lev = st.select_slider("Leverage", [10, 50, 100, 200], 200)
    target_pts = st.slider("Target Move (Points)", 5.0, 100.0, 10.0)
    
    debug_on = st.checkbox("Show Debug Console")
    
    if st.button("Full Reset Terminal"):
        st.session_state.clear()
        st.rerun()

# 3. API Headers
def get_headers(method, path, payload, api_key, api_secret):
    timestamp = str(int(time.time() * 1000))
    msg = method + path + timestamp + payload
    signature = hmac.new(api_secret.encode('utf-8'), msg.encode('utf-8'), hashlib.sha256).hexdigest()
    return {"api-key": api_key, "signature": signature, "timestamp": timestamp, "Content-Type": "application/json"}

# 4. UI
st.title(f"📊 Safe Pro Terminal: {asset_choice}")
m1, m2, m3, m4 = st.columns(4)
p_price = m1.empty()
p_wallet = m2.empty()
p_series = m3.empty()
p_pos_count = m4.empty()

st.divider()

col_sig, col_main = st.columns([1, 3])

with col_sig:
    st.subheader("📰 War-Room Signals")
    st.success(f"Signal: {asset_choice[:3]} BULLISH")
    st.info("Market Vol: High")
    st.divider()
    st.subheader("📊 Series Config")
    st.write(f"Step: {st.session_state.series_step}/12")
    st.write("SL: 0.8% | TP: 1.5%")
    p_depth = st.empty()

with col_main:
    # ✅ FIXED CHART (TradingView)
    symbol_map = {
        "BTCUSD": "BINANCE:BTCUSDT",
        "ETHUSD": "BINANCE:ETHUSDT"
    }
    tv_symbol = symbol_map.get(asset_choice, "BINANCE:BTCUSDT")

    st.components.v1.html(f"""
    <div id="tradingview_chart"></div>
    <script src="https://s3.tradingview.com/tv.js"></script>
    <script>
    new TradingView.widget({{
      "width": "100%",
      "height": 520,
      "symbol": "{tv_symbol}",
      "interval": "1",
      "timezone": "Asia/Kolkata",
      "theme": "dark",
      "style": "1",
      "container_id": "tradingview_chart"
    }});
    </script>
    """, height=520)

    p_hist = st.empty()

# 5. LOGIC
try:
    t_resp = requests.get(f"https://api.india.delta.exchange/v2/tickers/{asset_choice}").json()
    price = float(t_resp['result']['last_price'])
    p_price.metric("Live Price", f"${price:,.2f}")
    p_depth.code(f"Ask: {price+1.5}\nBid: {price-0.5}")

    if st.session_state.last_trade_p == 0:
        st.session_state.last_trade_p = price

    if acc_mode == "Real Delta India" and api_k and api_s:
        h_bal = get_headers("GET", "/v2/wallet/balances", "", api_k, api_s)
        r_bal = requests.get("https://api.india.delta.exchange/v2/wallet/balances", headers=h_bal).json()
        
        for item in r_bal.get('result', []):
            if item['asset_symbol'] == 'USDT':
                st.session_state.real_bal = float(item['balance'])

        h_pos = get_headers("GET", "/v2/positions", "", api_k, api_s)
        r_pos = requests.get("https://api.india.delta.exchange/v2/positions", headers=h_pos).json()
        active_pos = [p for p in r_pos.get('result', []) if float(p.get('size', 0)) != 0]
        p_pos_count.metric("Active Positions", len(active_pos))

        p_diff = abs(price - st.session_state.last_trade_p)
        cooldown_ok = (time.time() - st.session_state.last_trade_time) > 15

        if auto_trade and len(active_pos) == 0 and p_diff >= target_pts and cooldown_ok:
            side = 'buy' if price > st.session_state.last_trade_p else 'sell'
            
            r_prod = requests.get("https://api.india.delta.exchange/v2/products").json()
            p_id = next((p['id'] for p in r_prod.get('result', []) if asset_choice in p['symbol']), None)

            if p_id:
                comp_size = max(1, int((st.session_state.real_bal * lev) / price))

                o_pay = json.dumps({
                    "product_id": int(p_id),
                    "size": comp_size,
                    "side": side,
                    "order_type": "market_order"
                })

                res = requests.post(
                    "https://api.india.delta.exchange/v2/orders",
                    headers=get_headers("POST", "/v2/orders", o_pay, api_k, api_s),
                    data=o_pay
                )

                status = "SUCCESS" if res.status_code == 200 else "FAILED"

                st.session_state.history.insert(0, {
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Side": side.upper(),
                    "Price": price,
                    "Status": status
                })

                st.session_state.last_trade_p = price
                st.session_state.last_trade_time = time.time()
                st.session_state.series_step += 1

    p_wallet.metric("Wallet", f"${st.session_state.real_bal:,.2f}")
    p_series.metric("Series", f"{st.session_state.series_step}/12")
    st.session_state.last_p = price

    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

except Exception as e:
    if debug_on:
        st.error(e)

time.sleep(2)
st.rerun()
