import streamlit as st
import pandas as pd
import time
import hmac
import hashlib
import json
import requests
from datetime import datetime

# 1. NEW PRO CONFIG
st.set_page_config(page_title="OfficialLS SCALPER", layout="wide")

st.markdown("""
<style>
.main { background-color:#060606; color:#00ff00; }
[data-testid="stMetricValue"] { font-size: 32px !important; color: #f0b90b !important; }
.stButton>button { background:#f0b90b; color:black; font-weight:bold; border-radius:2px; }
</style>
""", unsafe_allow_html=True)

# Session States
if "history" not in st.session_state: st.session_state.history = []
if "last_trade_time" not in st.session_state: st.session_state.last_trade_time = 0
if "series_step" not in st.session_state: st.session_state.series_step = 0

# 2. SIDEBAR (SCALPING SETTINGS)
with st.sidebar:
    st.title("🦅 OfficialLS SCALPER")
    mode = st.radio("Mode", ["Simulation", "Real Delta India"])
    asset = st.selectbox("Asset", ["BTCUSD", "ETHUSD"])
    api_k = st.text_input("API Key", type="password")
    api_s = st.text_input("API Secret", type="password")
    
    st.divider()
    lev = st.select_slider("Scalp Leverage", [50, 100, 150, 200], 200)
    sc_points = st.slider("Scalp Target (Points)", 2.0, 50.0, 5.0) # Small moves for scalping
    auto_ai = st.toggle("🚀 START AI SCALPING", value=False)
    
    if st.button("Reset Terminal"):
        st.session_state.clear()
        st.rerun()

# 3. DASHBOARD UI
st.title(f"⚡ Live Scalping: {asset}")
c1, c2, c3, c4 = st.columns(4)
p_price = c1.empty()
p_bal = c2.empty()
p_step = c3.empty()
p_status = c4.empty()

# 4. NEW DELTA NATIVE CHART (Jo tune maanga tha)
# URL: https://www.delta.exchange/app/futures/trade/BTC/BTCUSD
asset_url = asset.replace("USD", "")
st.components.v1.html(f"""
    <iframe src="https://india.delta.exchange/app/futures/trade/{asset_url}/{asset}?chart_orderbook_tab=chart" 
    width="100%" height="600px" style="border:none; border-radius:8px; background: #0b0e11;"></iframe>
""", height=600)

# 5. DATA & SECURITY
def get_headers(method, path, payload, ak, as_):
    ts = str(int(time.time() * 1000))
    msg = method + path + ts + payload
    sig = hmac.new(as_.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return {"api-key": ak, "signature": sig, "timestamp": ts, "Content-Type": "application/json"}

try:
    ticker = requests.get(f"https://api.india.delta.exchange/v2/tickers/{asset}").json()
    price = float(ticker['result']['last_price'])
    p_price.metric("Price", f"${price:,.2f}")
except: price = 0

# 6. SCALPING AI LOGIC (EMA + RSI)
def get_scalp_signal():
    try:
        url = f"https://api.india.delta.exchange/v2/candles/{asset}?resolution=1m"
        candles = requests.get(url).json()["result"]
        closes = [float(c["close"]) for c in candles]
        
        # Fast EMA for Scalping
        ema3 = sum(closes[-3:]) / 3
        ema8 = sum(closes[-8:]) / 8
        
        # Quick RSI
        deltas = [closes[i]-closes[i-1] for i in range(1, len(closes))]
        rsi = 100 - (100 / (1 + (sum([d for d in deltas[-7:] if d>0])/7 / (abs(sum([d for d in deltas[-7:] if d<0]))/7 or 1))))

        if ema3 > ema8 and rsi < 65: return "BUY"
        if ema3 < ema8 and rsi > 35: return "SELL"
        return "WAIT"
    except: return "WAIT"

# 7. EXECUTION
if auto_ai and price != 0:
    signal = get_scalp_signal()
    cooldown = (time.time() - st.session_state.last_trade_time) > 8 # Faster 8s cooldown for scalps

    if signal in ["BUY", "SELL"] and cooldown:
        # Calculate Qty
        trade_bal = 100.0 # Default if no API
        if mode == "Real Delta India" and api_k and api_s:
            # Sync Balance
            h = get_headers("GET", "/v2/wallet/balances", "", api_k, api_s)
            r_bal = requests.get("https://api.india.delta.exchange/v2/wallet/balances", headers=h).json()
            for b in r_bal.get('result', []):
                if b['asset_symbol'] in ['USDT', 'INR']: trade_bal = float(b['balance']) / (1 if b['asset_symbol']=='USDT' else 89)
        
        qty = int((trade_bal * lev) / price)
        qty = max(qty, 1)

        status = "DEMO"
        if mode == "Real Delta India":
            p_id = 1 if "BTC" in asset else 3
            pay = json.dumps({"product_id": p_id, "size": qty, "side": signal.lower(), "order_type": "market_order"})
            res = requests.post("https://api.india.delta.exchange/v2/orders", headers=get_headers("POST", "/v2/orders", pay, api_k, api_s), data=pay).json()
            status = "REAL OK" if "result" in res else "ERR"

        # Update
        st.session_state.series_step += 1
        st.session_state.history.insert(0, {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Signal": signal,
            "Price": price,
            "Qty": qty,
            "Status": status
        })
        st.session_state.last_trade_time = time.time()

# UI Updates
p_bal.metric("Wallet", f"Active")
p_step.metric("Step", f"{st.session_state.series_step}/12")
p_status.success(f"Signal: {get_scalp_signal()}")

st.subheader("📜 Scalp History")
if st.session_state.history:
    st.dataframe(pd.DataFrame(st.session_state.history), use_container_width=True)

time.sleep(2)
st.rerun()
    
