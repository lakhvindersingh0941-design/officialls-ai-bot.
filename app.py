import streamlit as st
import requests, time, hmac, hashlib, json
from datetime import datetime

st.set_page_config(page_title="OfficialLS SAFE PRO", layout="wide")

# ================= SESSION =================
for k in ["balance","positions","history","last_trade"]:
    if k not in st.session_state:
        st.session_state[k] = [] if k in ["positions","history"] else 0

# ================= SIDEBAR =================
with st.sidebar:
    st.title("🦅 SAFE PRO AI")

    mode = st.radio("Mode", ["Demo","Real"])
    asset = st.selectbox("Asset", ["BTCUSD","ETHUSD"])

    api_k = st.text_input("API Key", type="password")
    api_s = st.text_input("API Secret", type="password")

    leverage = st.slider("Leverage",10,100,20)
    capital_pct = st.slider("Capital %",10,50,20)

    st.warning("⚠️ High leverage risky")

# ================= SIGN =================
def sign(method,path,payload):
    ts=str(int(time.time()*1000))
    msg=method+path+ts+payload
    sig=hmac.new(api_s.encode(),msg.encode(),hashlib.sha256).hexdigest()
    return {"api-key":api_k,"signature":sig,"timestamp":ts,"Content-Type":"application/json"}

# ================= PRICE =================
def get_price():
    try:
        r=requests.get(f"https://api.india.delta.exchange/v2/tickers/{asset}").json()
        return float(r['result']['last_price'])
    except:
        return 0

price = get_price()
st.metric("Live Price", f"${price}")

# ================= BALANCE =================
if mode=="Demo":
    st.session_state.balance = 100
else:
    if api_k and api_s:
        try:
            r=requests.get("https://api.india.delta.exchange/v2/wallet/balances",
                           headers=sign("GET","/v2/wallet/balances","")).json()
            for i in r.get("result",[]):
                if i["asset_symbol"]=="USDT":
                    st.session_state.balance=float(i["balance"])
        except:
            st.error("API connection failed")

st.metric("Balance", f"${st.session_state.balance:.2f}")

# ================= PRODUCT ID =================
def get_product_id():
    r=requests.get("https://api.india.delta.exchange/v2/products").json()
    for p in r.get("result",[]):
        if p["symbol"]==asset:
            return p["id"]
    return None

# ================= MANUAL TRADE =================
st.subheader("🎯 Manual Trade")

col1,col2 = st.columns(2)

if col1.button("BUY"):
    side="buy"
elif col2.button("SELL"):
    side="sell"
else:
    side=None

if side and mode=="Real" and api_k and api_s:
    p_id = get_product_id()

    capital = (st.session_state.balance * capital_pct)/100
    size = max(1, int((capital * leverage)/price))

    payload = json.dumps({
        "product_id": int(p_id),
        "size": size,
        "side": side,
        "order_type": "market_order"
    })

    res = requests.post(
        "https://api.india.delta.exchange/v2/orders",
        headers=sign("POST","/v2/orders",payload),
        data=payload
    )

    if res.status_code == 200:
        st.success(f"✅ {side.upper()} ORDER PLACED | Size: {size}")
    else:
        st.error(f"❌ Order Failed: {res.text}")

# ================= POSITIONS =================
if mode=="Real" and api_k and api_s:
    try:
        r=requests.get("https://api.india.delta.exchange/v2/positions",
                       headers=sign("GET","/v2/positions","")).json()
        st.subheader("📊 Active Positions")
        st.write(r.get("result",[]))
    except:
        st.error("Position fetch failed")

# ================= SAFE INFO =================
st.info("""
✅ Use small capital  
✅ Avoid 200x full margin  
✅ Always test in demo first  
""")

# ================= AUTO REFRESH =================
time.sleep(3)
st.rerun()
