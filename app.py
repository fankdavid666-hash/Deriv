import streamlit as st
import pandas as pd
from bot_core import SYMBOLS, scan_market, load_state, reset_daily_state

st.set_page_config(page_title="Deriv 4H Engulfing Bot", page_icon="🤖", layout="wide")

st.title("🤖 Deriv 4H Engulfing Bot")
st.caption("Jump 100 • Volatility 100 • Volatility 100 (1s)")

state = load_state()

with st.sidebar:
    st.header("Risk controls")
    st.write("Stake: **$2**")
    st.write("Maximum trades/day: **3**")
    st.write("Consecutive-loss lock: **5**")
    st.write("Contract duration: **3 days / 72 hours**")
    st.divider()
    st.warning("LIVE execution is disabled in this build. Test the signal engine on demo first.")

if st.button("Refresh market scan", type="primary"):
    rows = []
    for name, symbol in SYMBOLS.items():
        try:
            result = scan_market(symbol)
            rows.append({
                "Market": name,
                "Symbol": symbol,
                "Price": result["price"],
                "4H pattern": result["pattern"] or "None",
                "50% level": result["midpoint"],
                "Distance to 50%": result["distance"],
                "Signal": result["signal"],
                "Candle": result["candle_time"],
            })
        except Exception as exc:
            rows.append({"Market": name, "Symbol": symbol, "Error": str(exc)})
    st.session_state["scan"] = pd.DataFrame(rows)

if "scan" in st.session_state:
    st.dataframe(st.session_state["scan"], use_container_width=True, hide_index=True)

c1, c2, c3 = st.columns(3)
c1.metric("Trades today", f'{state["trades_today"]}/3')
c2.metric("Loss streak", f'{state["loss_streak"]}/5')
c3.metric("Status", "LOCKED" if state["loss_streak"] >= 5 or state["trades_today"] >= 3 else "READY")

st.subheader("Rules")
st.markdown("""
- Use the **last completed 4H candle**.
- Bullish engulfing → **CALL / Rise**.
- Bearish engulfing → **PUT / Fall**.
- Entry level = **50% of the engulfing candle range**.
- $2 stake.
- Maximum 3 trades per UTC day.
- Lock after 5 consecutive losses.
- Intended contract duration: 3 days.
""")

st.info(
    "This package deliberately separates signal detection from order execution. "
    "Before live execution, validate the exact contract type/duration available for each symbol "
    "and run the strategy on a Deriv demo account."
)
