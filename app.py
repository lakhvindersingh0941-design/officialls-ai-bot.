import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import requests
import json
from datetime import datetime

st.set_page_config(page_title="SAFE PRO AI", layout="wide")

# -------- STYLE ----------
st.markdown("""
<style>
.main { background-color:#0b0e11; color:#fff; }
.stButton>button { width:100%; background:#f0b90b; color:black; }
</style>
""", unsafe_allow_html=True)

# -------- SESSION ----------
if "bal" not in st.session_state:
    st.session_state.bal = 100.0   # DEMO DEFAULT

# -------- SIDEBAR ----------
with st.sidebar:
    st.title("SAFE PRO AI")

    mode = st.radio("Mode", ["Demo", "Real"])

    asset = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])

    api_key = st.text_input("API Key", type="password")
    api_secret = st.text_input("API Secret", type="password")

    leverage = st.slider("Leverage", 1, 200, 20)

    capital_percent = st.slider("Capital %", 10, 100, 100)  # DEFAULT 100%

    st.warning("⚠ High leverage risky")

# -------- HEADER ----------
st.title(f"📊 Terminal: {asset}")

c1, c2, c3 = st.columns(3)
price_box = c1.empty()
bal_box = c2.empty()
status_box = c3.empty()

# -------- CHART (FIXED) ----------
st.subheader("📈 Live Chart")

st.components.v1.html(f"""
<!-- TradingView Widget -->
<div class="tradingview-widget-container">
  <div id="tv_chart"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
    new TradingView.widget({{
      "container_id": "tv_chart",
      "width": "100%",
      "height": 500,
      "symbol": "BINANCE:{asset.replace('USD','USDT')}",
      "interval": "1",
      "theme": "dark",
      "style": "1",
      "locale": "en",
      "toolbar_bg": "#f1f3f6",
      "enable_publishing": false,
      "hide_side_toolbar": false,
      "allow_symbol_change": true
    }});
  </script>
</div>
""", height=520)

# -------- PRICE FETCH FIX ----------
try:
    url = f"https://api.india.delta.exchange/v2/tickers/{asset}"
    res = requests.get(url).json()

    # FIX: safe extraction
    price = float(res.get("result", {}).get("last_price", 0))

except:
    price = 0

price_box.metric("Live Price", f"${price}")

# -------- DEMO / REAL BAL ----------
if mode == "Demo":
    balance = st.session_state.bal
    status_box.success("Demo Mode ✅")
else:
    try:
        timestamp = str(int(time.time()*1000))
        msg = "GET/v2/wallet/balances" + timestamp
        sign = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        headers = {
            "api-key": api_key,
            "signature": sign,
            "timestamp": timestamp
        }

        r = requests.get("https://api.india.delta.exchange/v2/wallet/balances", headers=headers).json()

        balance = float(r["result"][0]["balance"])
        status_box.success("Connected ✅")

    except:
        balance = 0
        status_box.error("API Error ❌")

bal_box.metric("Balance", f"${balance}")

# -------- NEWS (ADDED) ----------
st.subheader("📰 Crypto News")

try:
    news = requests.get(
        "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    ).json()

    for n in news["Data"][:5]:
        st.markdown(f"**{n['title']}**")
        st.write(n["body"][:120] + "...")
        st.write("---")

except:
    st.warning("News load failed")

# -------- MANUAL TRADE ----------
st.subheader("🎯 Manual Trade")

col1, col2 = st.columns(2)

# CALCULATE SIZE
trade_capital = (balance * capital_percent) / 100
qty = (trade_capital * leverage) / price if price != 0 else 0

if col1.button("BUY"):
    st.success(f"BUY placed | Size: {round(qty,4)}")

if col2.button("SELL"):
    st.success(f"SELL placed | Size: {round(qty,4)}")

# -------- AUTO REFRESH ----------
time.sleep(3)
st.rerun()
