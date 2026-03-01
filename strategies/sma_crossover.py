import pandas as pd

def generate_signals(data, short_window=20, long_window=50):
    df = data.copy()

    df["short_ma"] = df["Close"].rolling(short_window).mean()
    df["long_ma"] = df["Close"].rolling(long_window).mean()

    df["signal"] = 0
    df.loc[df["short_ma"] > df["long_ma"], "signal"] = 1

    df["position"] = df["signal"].shift(1)

    return df
    