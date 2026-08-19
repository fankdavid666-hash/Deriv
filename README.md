# Deriv 4H Engulfing Bot

A GitHub/Streamlit starter bot for your strategy:

- Jump 100 Index
- Volatility 100 Index
- Volatility 100 (1s) Index
- Completed 4H engulfing candle
- Entry when price retraces to 50% of the engulfing candle
- Bullish → CALL/Rise
- Bearish → PUT/Fall
- $2 stake
- Maximum 3 trades/day
- Stop after 5 consecutive losses
- Intended contract duration: 3 days / 72 hours

## Deploy to GitHub + Streamlit

Upload these files:

- `app.py`
- `bot_core.py`
- `requirements.txt`
- `README.md`

Create a Streamlit Community Cloud app and choose `app.py`.

## Important

This version is deliberately **signal-only**. It does not place live trades.

Before adding live execution, verify the exact symbols and available contracts using Deriv's `active_symbols` and `contracts_for` endpoints. Then add authenticated proposal/buy/contract-monitoring logic.

Never put an API token in GitHub.

## Strategy note

The app uses the last completed 4H candle and treats the latest candle as potentially still forming. The 50% level is:

`(High + Low) / 2`

A production version should use a persistent tick stream to detect the first qualifying retracement rather than checking only the latest price when the dashboard refreshes.
