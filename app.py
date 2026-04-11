import streamlit as st
import requests
import time
import hmac
import hashlib
import json

st.set_page_config(page_title="SAFE PRO AI", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main { background-color:#0b0e11; color:#fff; }
.stButton>button { width:100%; background:#f0b90b; color:black; }
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "bal" not in st.session_state:
    st.session_state.bal = 100.0

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("SAFE PRO AI")

    mode = st.radio("Mode", ["Demo", "Real"])
    asset = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])

    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("API Secret", type="password")

    leverage = st.slider("Leverage", 1, 200, 20)
    capital_percent = st.slider("Capital %", 10, 100, 100)

# ---------------- HEADER ----------------
st.title(f"📊 Terminal: {asset}")

c1, c2, c3 = st.columns(3)
price_box = c1.empty()
bal_box = c2.empty()
status_box = c3.empty()

# ---------------- CHART ----------------
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

# ---------------- PRICE ----------------
try:
    r = requests.get(f"https://api.india.delta.exchange/v2/tickers/{asset}").json()
    price = float(r.get("result", {}).get("last_price", 0))
except:
    price = 0

price_box.metric("Price", f"${price}")

# ---------------- CORRECT SIGN FUNCTION ----------------
def generate_signature(method, path, payload, api_secret):
    timestamp = str(int(time.time()))  # ✅ seconds
    message = method + timestamp + path + payload
    signature = hmac.new(
        api_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature, timestamp

# ---------------- REAL ACCOUNT ----------------
if mode == "Demo":
    balance = st.session_state.bal
    status_box.success("Demo Mode ✅")

else:
    try:
        path = "/v2/wallet/balances"
        payload = ""

        signature, timestamp = generate_signature("GET", path, payload, api_secret)

        headers = {
            "api-key": api_key,
            "signature": signature,
            "timestamp": timestamp,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

        url = "https://api.india.delta.exchange" + path
        res = requests.get(url, headers=headers).json()

        # ✅ SAFE PARSE
        balance = 0
        for item in res.get("result", []):
            if item["asset_symbol"] == "USDT":
                balance = float(item["balance"])

        status_box.success("Connected ✅")

    except Exception as e:
        balance = 0
        status_box.error("API Error ❌")
        st.write("Error:", e)

bal_box.metric("Balance", f"${balance}")

# ---------------- NEWS ----------------
st.subheader("📰 Crypto News")

try:
    news = requests.get("https://min-api.cryptocompare.com/data/v2/news/?lang=EN").json()
    for n in news["Data"][:3]:
        st.markdown(f"**{n['title']}**")
        st.write(n["body"][:100])
        st.write("---")
except:
    st.warning("News failed")

# ---------------- LOT SIZE FIX ----------------
def get_lot_size(symbol):
    try:
        r = requests.get("https://api.india.delta.exchange/v2/products").json()
        for p in r["result"]:
            if p["symbol"] == symbol:
                return float(p["contract_value"])
    except:
        return 1

lot_size = get_lot_size(asset)

# ---------------- TRADE SIZE ----------------
trade_capital = (balance * capital_percent) / 100

# ✅ Correct lot calculation
qty = int((trade_capital * leverage) / (price * lot_size)) if price != 0 else 0
qty = max(qty, 1)

st.write(f"Lot Size: {qty}")

# ---------------- ORDER FUNCTION ----------------
def place_order(side):
    path = "/v2/orders"

    payload_dict = {
        "product_id": 27,  # BTC example (dynamic bhi kar sakte)
        "size": qty,
        "side": side,
        "order_type": "market_order"
    }

    payload = json.dumps(payload_dict)

    signature, timestamp = generate_signature("POST", path, payload, api_secret)

    headers = {
        "api-key": api_key,
        "signature": signature,
        "timestamp": timestamp,
        "Content-Type": "application/json"
    }

    url = "https://api.india.delta.exchange" + path
    return requests.post(url, headers=headers, data=payload).json()

# ---------------- MANUAL TRADE ----------------
col1, col2 = st.columns(2)

if col1.button("BUY"):
    if mode == "Real":
        res = place_order("buy")
        st.success(res)
    else:
        st.success(f"Demo BUY | Lot {qty}")

if col2.button("SELL"):
    if mode == "Real":
        res = place_order("sell")
        st.success(res)
    else:
        st.success(f"Demo SELL | Lot {qty}")

# ---------------- REFRESH ----------------
time.sleep(3)
st.rerun()
