import streamlit as st
import requests
import time
import hmac
import hashlib
import json
import pandas as pd

st.set_page_config(page_title="SAFE PRO AI", layout="wide")

# ---------- SESSION ----------
if "bal" not in st.session_state:
    st.session_state.bal = 100.0
if "history" not in st.session_state:
    st.session_state.history = []
if "last_trade_time" not in st.session_state:
    st.session_state.last_trade_time = 0

# ---------- SIDEBAR ----------
with st.sidebar:
    st.title("SAFE PRO AI")

    mode = st.radio("Mode", ["Demo", "Real"])
    asset = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])

    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("API Secret", type="password")

    leverage = st.slider("Leverage", 1, 200, 50)
    capital_percent = st.slider("Capital %", 10, 100, 100)

    auto_ai = st.toggle("🤖 AUTO AI FAST SCALPING", value=False)

# ---------- HEADER ----------
st.title(f"📊 Terminal: {asset}")

# ---------- TRADINGVIEW CHART ----------
st.subheader("📈 Live Chart")

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
  "timezone": "Asia/Kolkata",
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

# ---------- BALANCE ----------
if mode == "Demo":
    balance = st.session_state.bal
else:
    try:
        path = "/v2/wallet/balances"
        sig, ts = sign("GET", path, "", api_secret)

        headers = {
            "api-key": api_key,
            "signature": sig,
            "timestamp": ts
        }

        res = requests.get("https://api.india.delta.exchange"+path, headers=headers).json()

        balance = 0
        for i in res.get("result", []):
            if i["asset_symbol"] == "USDT":
                balance = float(i["balance"])
    except:
        balance = 0

st.metric("Balance", f"${balance}")

# ---------- ADVANCED SIGNAL ----------
def get_signal():
    try:
        r = requests.get(f"https://api.india.delta.exchange/v2/candles?symbol={asset}&resolution=1m").json()
        data = r["result"]

        closes = [float(c["close"]) for c in data][-50:]

        ema9 = sum(closes[-9:]) / 9
        ema21 = sum(closes[-21:]) / 21

        momentum = closes[-1] - closes[-4]

        # RSI
        gains = []
        losses = []
        for i in range(1, 15):
            diff = closes[-i] - closes[-i-1]
            if diff > 0:
                gains.append(diff)
            else:
                losses.append(abs(diff))

        avg_gain = sum(gains)/14 if gains else 0.1
        avg_loss = sum(losses)/14 if losses else 0.1
        rs = avg_gain / avg_loss if avg_loss != 0 else 1
        rsi = 100 - (100 / (1 + rs))

        if ema9 > ema21 and rsi > 55 and momentum > 0:
            return "BUY"
        elif ema9 < ema21 and rsi < 45 and momentum < 0:
            return "SELL"
        else:
            return "HOLD"

    except:
        return "HOLD"

# ---------- LOT ----------
trade_capital = (balance * capital_percent) / 100
qty = int((trade_capital * leverage) / price) if price != 0 else 0
qty = max(qty, 1)

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
if auto_ai and price != 0 and product_id:

    signal = get_signal()
    cooldown = time.time() - st.session_state.last_trade_time > 3

    if signal in ["BUY", "SELL"] and cooldown:

        entry = price

        # SL / TP
        sl = entry * 0.996 if signal == "BUY" else entry * 1.004
        tp = entry * 1.006 if signal == "BUY" else entry * 0.994

        if mode == "Real":
            res = place_order(signal)
            status = "REAL"
        else:
            status = "DEMO"

        st.session_state.history.insert(0, {
            "Time": time.strftime("%H:%M:%S"),
            "Side": signal,
            "Entry": round(entry,2),
            "SL": round(sl,2),
            "TP": round(tp,2),
            "Qty": qty,
            "Mode": status
        })

        st.session_state.last_trade_time = time.time()

# ---------- HISTORY ----------
st.subheader("📜 Trade History")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

# ---------- REFRESH ----------
time.sleep(3)
st.rerun()
