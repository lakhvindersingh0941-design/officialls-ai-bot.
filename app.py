import streamlit as st
import requests
import time
import hmac
import hashlib
import json
import pandas as pd

st.set_page_config(page_title="SAFE PRO AI FINAL", layout="wide")

# ---------- SESSION ----------
if "bal" not in st.session_state:
    st.session_state.bal = 100.0
if "history" not in st.session_state:
    st.session_state.history = []
if "last_trade_time" not in st.session_state:
    st.session_state.last_trade_time = 0

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("SAFE PRO AI FINAL")

    mode = st.radio("Mode", ["Demo", "Real"])
    asset = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])

    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("API Secret", type="password")

    leverage = st.slider("Leverage", 1, 200, 50)
    capital_percent = st.slider("Capital %", 10, 100, 100)

    auto_ai = st.toggle("🤖 AUTO AI TRADING", value=False)
    debug = st.checkbox("Show Debug")

# ---------- HEADER ----------
st.title(f"📊 Terminal: {asset}")

# ---------- CHART ----------
symbol_tv = "DELTAIN:BTCUSD.P" if asset == "BTCUSD" else "DELTAIN:ETHUSD.P"

st.components.v1.html(f"""
<div id="tv_chart"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({{
  "container_id": "tv_chart",
  "width": "100%",
  "height": 500,
  "symbol": "{symbol_tv}",
  "interval": "1",
  "theme": "dark"
}});
</script>
""", height=520)

# ---------- PRICE ----------
try:
    r = requests.get(f"https://api.india.delta.exchange/v2/tickers/{asset}").json()
    price = float(r.get("result", {}).get("last_price", 0))
except:
    price = 0

st.metric("Price", f"${price}")

# ---------- SIGN ----------
def sign(method, path, payload, secret):
    ts = str(int(time.time()))
    msg = method + ts + path + payload
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return sig, ts

# ---------- PRODUCT ID ----------
def get_product_id(symbol):
    try:
        r = requests.get("https://api.india.delta.exchange/v2/products").json()
        for p in r["result"]:
            if p["symbol"] == symbol:
                return p["id"]
    except:
        return None

product_id = get_product_id(asset)

# ---------- BALANCE + CONNECTION ----------
connected = False
balance = 0

if mode == "Demo":
    balance = st.session_state.bal
    connected = True
else:
    try:
        path = "/v2/wallet/balances"
        sig, ts = sign("GET", path, "", api_secret)

        headers = {
            "api-key": api_key,
            "signature": sig,
            "timestamp": ts,
            "Content-Type": "application/json"
        }

        res = requests.get("https://api.india.delta.exchange"+path, headers=headers).json()

        if debug:
            st.write("API Response:", res)

        # ✅ FIXED PART (USD + USDT)
        for i in res.get("result", []):
            if i.get("asset_symbol") in ["USD", "USDT"]:
                balance = float(i.get("balance", 0))
                connected = True
                break

    except Exception as e:
        if debug:
            st.error(e)

# ---------- STATUS ----------
col1, col2 = st.columns(2)

if connected:
    col1.success("✅ Connected")
else:
    col1.error("❌ Not Connected")

col2.metric("Balance", f"${balance:.4f}")

# ---------- SIGNAL ----------
def get_signal():
    try:
        r = requests.get(f"https://api.india.delta.exchange/v2/candles?symbol={asset}&resolution=1m").json()
        data = r["result"]

        closes = [float(c["close"]) for c in data][-30:]

        ema5 = sum(closes[-5:]) / 5
        ema20 = sum(closes[-20:]) / 20

        momentum = closes[-1] - closes[-3]

        if ema5 > ema20 and momentum > 0:
            return "BUY"
        elif ema5 < ema20 and momentum < 0:
            return "SELL"
        else:
            return "HOLD"
    except:
        return "HOLD"

# ---------- LOT SIZE ----------
trade_capital = (balance * capital_percent) / 100

if price > 0:
    qty = (trade_capital * leverage) / price
    qty = round(qty, 3)
    qty = max(qty, 1)  # minimum 1
else:
    qty = 1

# ---------- ORDER ----------
def place_order(side):
    path = "/v2/orders"

    payload = json.dumps({
        "product_id": product_id,
        "size": qty,
        "side": side.lower(),
        "order_type": "market_order"
    })

    sig, ts = sign("POST", path, payload, api_secret)

    headers = {
        "api-key": api_key,
        "signature": sig,
        "timestamp": ts,
        "Content-Type": "application/json"
    }

    return requests.post("https://api.india.delta.exchange"+path, headers=headers, data=payload).json()

# ---------- AUTO AI ----------
if auto_ai and connected and price != 0 and product_id:

    signal = get_signal()

    cooldown = time.time() - st.session_state.last_trade_time > 5

    if signal in ["BUY", "SELL"] and cooldown:

        if mode == "Real":
            res = place_order(signal)
            status = res
        else:
            status = "DEMO"

        st.session_state.history.insert(0, {
            "Time": time.strftime("%H:%M:%S"),
            "Signal": signal,
            "Price": round(price,2),
            "Qty": qty,
            "Mode": mode,
            "Status": str(status)[:50]
        })

        st.session_state.last_trade_time = time.time()

# ---------- HISTORY ----------
st.subheader("📜 Trade History")

if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# ---------- REFRESH ----------
time.sleep(3)
st.rerun()
