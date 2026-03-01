import numpy as np

def run_backtest(df, transaction_cost=0.001):  # 0.1% per trade
    df = df.copy()

    df["returns"] = df["Close"].pct_change()

    # Detect trade changes (when position flips)
    df["trade"] = df["position"].diff().abs()

    df["strategy_returns"] = df["returns"] * df["position"]

    # Apply transaction cost when trade occurs
    df["strategy_returns"] -= df["trade"] * transaction_cost

    df["equity_curve"] = (1 + df["strategy_returns"]).cumprod()

    df["buy_hold_equity"] = (1 + df["returns"]).cumprod()

    return df