import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import websocket

WS_URL = "wss://ws.binaryws.com/websockets/v3"

# Verify these against active_symbols returned by your Deriv account.
SYMBOLS = {
    "Jump 100 Index": "JD100",
    "Volatility 100 Index": "R_100",
    "Volatility 100 (1s) Index": "1HZ100V",
}

STATE_FILE = Path("bot_state.json")

def ws_request(ws, payload, msg_types):
    ws.send(json.dumps(payload))
    while True:
        data = json.loads(ws.recv())
        if data.get("error"):
            raise RuntimeError(data["error"].get("message", "Deriv API error"))
        if data.get("msg_type") in msg_types:
            return data

def get_4h_candles(symbol, count=100):
    ws = websocket.create_connection(WS_URL, timeout=20)
    try:
        response = ws_request(
            ws,
            {
                "ticks_history": symbol,
                "style": "candles",
                "granularity": 14400,
                "count": count,
                "end": "latest",
            },
            {"candles", "history"},
        )
        df = pd.DataFrame(response.get("candles", []))
        if df.empty:
            return df
        for col in ["open", "high", "low", "close"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["epoch"] = pd.to_numeric(df["epoch"])
        df["time"] = pd.to_datetime(df["epoch"], unit="s", utc=True)
        return df
    finally:
        ws.close()

def detect_engulfing(df):
    if len(df) < 3:
        return None

    previous = df.iloc[-3]
    current = df.iloc[-2]  # completed candle; latest candle may still be forming

    bullish = (
        previous.close < previous.open
        and current.close > current.open
        and current.open <= previous.close
        and current.close >= previous.open
    )
    bearish = (
        previous.close > previous.open
        and current.close < current.open
        and current.open >= previous.close
        and current.close <= previous.open
    )

    if not bullish and not bearish:
        return None

    return {
        "direction": "bullish" if bullish else "bearish",
        "contract_type": "CALL" if bullish else "PUT",
        "candle_time": current.time.isoformat(),
        "open": float(current.open),
        "high": float(current.high),
        "low": float(current.low),
        "close": float(current.close),
        "midpoint": float((current.high + current.low) / 2),
    }

def scan_market(symbol, tolerance_fraction=0.0005):
    df = get_4h_candles(symbol)
    if df.empty:
        raise RuntimeError("No candle data returned.")

    current_price = float(df.iloc[-1].close)
    signal = detect_engulfing(df)

    if not signal:
        return {
            "price": current_price,
            "pattern": None,
            "midpoint": None,
            "distance": None,
            "signal": "WAIT",
            "candle_time": None,
        }

    midpoint = signal["midpoint"]
    distance = current_price - midpoint
    tolerance = max(abs(midpoint) * tolerance_fraction, 1e-8)
    hit = abs(distance) <= tolerance

    return {
        "price": current_price,
        "pattern": signal["direction"],
        "midpoint": midpoint,
        "distance": distance,
        "signal": ("CALL / Rise" if signal["direction"] == "bullish" else "PUT / Fall") if hit else "WAIT",
        "candle_time": signal["candle_time"],
    }

def load_state():
    today = datetime.now(timezone.utc).date().isoformat()
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
        except Exception:
            state = {}
    else:
        state = {}

    if state.get("date") != today:
        state = {"date": today, "trades_today": 0, "loss_streak": 0, "last_signal": None}
        STATE_FILE.write_text(json.dumps(state, indent=2))

    return state

def reset_daily_state():
    today = datetime.now(timezone.utc).date().isoformat()
    state = {"date": today, "trades_today": 0, "loss_streak": 0, "last_signal": None}
    STATE_FILE.write_text(json.dumps(state, indent=2))
    return state
