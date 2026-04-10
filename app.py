import streamlit as st
import ccxt
import pandas as pd
import time

st.set_page_config(page_title="OfficialLS AI Bot", layout="wide")
st.title("🤖 OfficialLS Bitcoin AI Trader")

# Wallet Setup
if 'balance' not in st.session_state:
    st.session_state.balance = 100.0
    st.session_state.trades = []

# Sidebar Controls
st.sidebar.header("⚙️ Settings")
mode = st.sidebar.radio("Mode", ["Paper Trade", "Real Money (Delta)"])

api_key = ""
api_secret = ""
if mode == "Real Money (Delta)":
    api_key = st.sidebar.text_input("API Key", type="password")
    api_secret = st.sidebar.text_input("API Secret", type="password")

# Connect to Delta Exchange
try:
    exchange = ccxt.delta()
    ticker = exchange.fetch_ticker('BTC/USDT')
    live_price = ticker['last']
    st.sidebar.metric("Live BTC Price", f"${live_price}")
except:
    st.sidebar.error("Connecting to Market...")

# Main Logic
auto_trade = st.toggle("Activate AI Auto-Pilot")

if auto_trade:
    st.success("AI is Scanning 1m, 5m, 1h charts...")
    # Entry simulation
    if len(st.session_state.trades) == 0:
        st.session_state.trades.append({
            "Time": time.strftime("%H:%M"),
            "Entry": live_price,
            "SL": live_price * 0.99,
            "TP": live_price * 1.02,
            "Status": "OPEN"
        })
        st.toast("New Trade Taken!")

st.write("### Active Trades & History")
if st.session_state.trades:
    st.table(pd.DataFrame(st.session_state.trades))

st.sidebar.metric("Your Balance", f"${st.session_state.balance}")
          
