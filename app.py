import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import json
from datetime import datetime

# PAGE CONFIG
st.set_page_config(page_title="OfficialLS Safe Pro AI", layout="wide")

st.markdown("""
<style>
.main { background-color: #0b0e11; color: #eaecef; }
[data-testid="stMetricValue"] { font-size: 26px !important; color: #f0b90b !important; }
</style>
""", unsafe_allow_html=True)

# SESSION
if 'history' not in st.session_state: st.session_state.history = []
if 'last_trade_price' not in st.session_state: st.session_state.last_trade_price = 0
if 'last_trade_time' not in st.session_state: st.session_state.last_trade_time = 0
if 'balance' not in st.session_state: st.session_state.balance = 0.0

# SIDEBAR
with st.sidebar:
    st.title("🦅 OfficialLS AI")

    mode = st.radio("Mode", ["Demo", "Real"])
    asset = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])

    api_k = st.text_input("API Key", type="password")
    api_s = st.text_input("API Secret", type="password")

    auto = st.toggle("🚀 Start Scalping", False)
    lev = st.select_slider("Leverage", [10, 50, 100, 200], 200)
    target = st.slider("Target Move ($)", 5.0, 50.0, 10.0)

    debug = st.checkbox("Debug Mode")

# API SIGN FUNCTION
def sign(method, path, payload):
    timestamp = str(int(time.time() * 1000))
    msg = method + path + timestamp + payload
    signature = hmac.new(api_s.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return {
        "api-key": api_k,
        "signature": signature,
        "timestamp": timestamp,
        "Content-Type": "application/json"
    }

# HEADER UI
st.title(f"📊 Safe Pro Terminal: {asset}")

c1, c2, c3, c4 = st.columns(4)
p_price = c1.empty()
p_bal = c2.empty()
p_conn = c3.empty()
p_pos = c4.empty()

# ✅ FIXED CHART (NO BLOCK ISSUE)
symbol_map = {
    "BTCUSD": "BINANCE:BTCUSDT",
    "ETHUSD": "BINANCE:ETHUSDT"
}

tv_symbol = symbol_map.get(asset, "BINANCE:BTCUSDT")

st.components.v1.html(f"""
<div id="tradingview_chart"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({{
    "width": "100%",
    "height": 500,
    "symbol": "{tv_symbol}",
    "interval": "1",
    "timezone": "Asia/Kolkata",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#0b0e11",
    "enable_publishing": false,
    "container_id": "tradingview_chart"
}});
</script>
""", height=500)

# MAIN LOOP
try:
    # PRICE FETCH (FIXED)
    tick = requests.get("https://api.india.delta.exchange/v2/tickers").json()
    ticker = next((x for x in tick.get("result", []) if asset in x.get("symbol", "")), None)

    if ticker:
        price = float(ticker.get("last_price", 0))
    else:
        price = 0

    p_price.metric("Live Price", f"${price:,.2f}")

    # REAL MODE
    if mode == "Real" and api_k and api_s:

        # BALANCE
        bal_res = requests.get(
            "https://api.india.delta.exchange/v2/wallet/balances",
            headers=sign("GET", "/v2/wallet/balances", "")
        ).json()

        if debug:
            st.write("Balance API:", bal_res)

        if bal_res.get("success"):
            p_conn.success("✅ Connected")

            for item in bal_res.get("result", []):
                if item.get("asset_symbol") == "USDT":
                    st.session_state.balance = float(item.get("balance", 0))

        else:
            p_conn.error("❌ API Error")

        # POSITIONS
        pos_res = requests.get(
            "https://api.india.delta.exchange/v2/positions",
            headers=sign("GET", "/v2/positions", "")
        ).json()

        active_pos = [
            p for p in pos_res.get("result", [])
            if float(p.get("size", 0)) != 0
        ]

        p_pos.metric("Positions", len(active_pos))

        # INIT
        if st.session_state.last_trade_price == 0:
            st.session_state.last_trade_price = price

        # SCALPING LOGIC
        move = abs(price - st.session_state.last_trade_price)
        cooldown = (time.time() - st.session_state.last_trade_time) > 15

        if auto and len(active_pos) == 0 and move >= target and cooldown:

            side = "buy" if price > st.session_state.last_trade_price else "sell"

            # PRODUCT ID
            prod = requests.get("https://api.india.delta.exchange/v2/products").json()
            pid = next((p["id"] for p in prod["result"] if asset in p["symbol"]), None)

            if pid:
                # 🔥 LOW BALANCE FIX (IMPORTANT)
                if st.session_state.balance < 1:
                    size = 1
                else:
                    size = max(1, int((st.session_state.balance * lev) / price))

                # SET LEVERAGE
                lev_payload = json.dumps({"product_id": pid, "leverage": str(lev)})
                requests.post(
                    "https://api.india.delta.exchange/v2/products/leverage",
                    headers=sign("POST", "/v2/products/leverage", lev_payload),
                    data=lev_payload
                )

                # PLACE ORDER
                order_payload = json.dumps({
                    "product_id": pid,
                    "size": size,
                    "side": side,
                    "order_type": "market_order"
                })

                res = requests.post(
                    "https://api.india.delta.exchange/v2/orders",
                    headers=sign("POST", "/v2/orders", order_payload),
                    data=order_payload
                )

                if debug:
                    st.write("Order Response:", res.json())

                status = "SUCCESS" if res.status_code == 200 else "FAILED"

                st.session_state.history.insert(0, {
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Side": side.upper(),
                    "Price": price,
                    "Size": size,
                    "Status": status
                })

                st.session_state.last_trade_price = price
                st.session_state.last_trade_time = time.time()

    else:
        p_conn.info("Demo Mode")

    p_bal.metric("Balance (USDT)", f"${st.session_state.balance:.3f}")

    # HISTORY
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

except Exception as e:
    st.error(f"Error: {e}")

# AUTO REFRESH
time.sleep(2)
st.rerun()
