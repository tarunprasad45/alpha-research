import numpy as np

def calculate_metrics(df):
    total_return = df["equity_curve"].iloc[-1] - 1

    sharpe = (
    df["strategy_returns"].mean() * 252 /
    (df["strategy_returns"].std() * np.sqrt(252))
)

    max_drawdown = (
        df["equity_curve"] /
        df["equity_curve"].cummax() - 1
    ).min()

    return {
        "Total Return": total_return,
        "Sharpe Ratio": sharpe,
        "Max Drawdown": max_drawdown
    }
