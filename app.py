import streamlit as st
import requests
import time
import hmac
import hashlib
import json
import pandas as pd

st.set_page_config(page_title="SAFE PRO AI", layout="wide")

# ---------- STYLE ----------
st.markdown("""
<style>
.main { background-color:#0b0e11; color:#fff; }
.stButton>button { width:100%; background:#f0b90b; color:black; }
</style>
""", unsafe_allow_html=True)

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

    leverage = st.slider("Leverage", 1, 200, 20)
    capital_percent = st.slider("Capital %", 10, 100, 100)

    auto_ai = st.toggle("🤖 AUTO AI TRADING", value=False)

# ---------- HEADER ----------
st.title(f"📊 Terminal: {asset}")

c1, c2, c3 = st.columns(3)
price_box = c1.empty()
bal_box = c2.empty()
status_box = c3.empty()

# ---------- CHART ----------
st.components.v1.html(f"""
<div id="tv_chart"></div>
<script src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({{
  "container_id": "tv_chart",
  "width": "100%",
  "height": 500,
  "symbol": "BINANCE:{asset.replace('USD','USDT')}",
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

price_box.metric("Price", f"${price}")

# ---------- SIGN ----------
def sign(method, path, payload, secret):
    ts = str(int(time.time()))
    msg = method + ts + path + payload
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return sig, ts

# ---------- BALANCE ----------
if mode == "Demo":
    balance = st.session_state.bal
    status_box.success("Demo")
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

        status_box.success("Connected")
    except:
        balance = 0
        status_box.error("Error")

bal_box.metric("Balance", f"${balance}")

# ---------- INDICATOR (AI LOGIC) ----------
def get_signal():
    try:
        url = f"https://api.india.delta.exchange/v2/candles/{asset}?resolution=1m"
        data = requests.get(url).json()["result"]

        closes = [float(c["close"]) for c in data][-20:]

        ema_short = sum(closes[-5:]) / 5
        ema_long = sum(closes) / 20

        momentum = closes[-1] - closes[-3]

        if ema_short > ema_long and momentum > 0:
            return "BUY"
        elif ema_short < ema_long and momentum < 0:
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
        "product_id": 27,
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
if auto_ai and price != 0:
    signal = get_signal()

    cooldown = time.time() - st.session_state.last_trade_time > 10

    if signal in ["BUY", "SELL"] and cooldown:

        entry = price

        # SL TP
        sl = entry * 0.995 if signal == "BUY" else entry * 1.005
        tp = entry * 1.01 if signal == "BUY" else entry * 0.99

        if mode == "Real":
            res = place_order(signal)
            status = "REAL"
        else:
            status = "DEMO"

        # SAVE HISTORY
        st.session_state.history.insert(0, {
            "Time": time.strftime("%H:%M:%S"),
            "Signal": signal,
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
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df, use_container_width=True)

# ---------- REFRESH ----------
time.sleep(3)
st.rerun()
