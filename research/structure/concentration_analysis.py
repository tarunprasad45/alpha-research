import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

START = "2018-01-01"
AI_START = "2022-11-01"

tickers = ["SPY", "RSP", "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL"]

data = yf.download(tickers, start=START)["Close"]
data = data.dropna()

returns = data.pct_change().dropna()
cum_returns = (1 + returns).cumprod()

# Relative performance SPY vs Equal Weight
relative = cum_returns["SPY"] / cum_returns["RSP"]

# Plot SPY vs RSP
plt.figure()
plt.plot(cum_returns["SPY"], label="SPY")
plt.plot(cum_returns["RSP"], label="RSP")
plt.axvline(pd.to_datetime(AI_START), linestyle="--")
plt.title("SPY vs Equal Weight (RSP)")
plt.legend()
plt.show()

# Plot Relative Performance
plt.figure()
plt.plot(relative, label="SPY / RSP")
plt.axvline(pd.to_datetime(AI_START), linestyle="--")
plt.title("Relative Performance: SPY vs Equal Weight")
plt.legend()
plt.show()

pre_period = cum_returns.loc[:AI_START]
post_period = cum_returns.loc[AI_START:]

pre_spy = pre_period["SPY"].iloc[-1] / pre_period["SPY"].iloc[0] - 1
pre_rsp = pre_period["RSP"].iloc[-1] / pre_period["RSP"].iloc[0] - 1

post_spy = post_period["SPY"].iloc[-1] / post_period["SPY"].iloc[0] - 1
post_rsp = post_period["RSP"].iloc[-1] / post_period["RSP"].iloc[0] - 1

print("Pre-AI Regime:")
print(f"SPY Return: {pre_spy:.2%}")
print(f"RSP Return: {pre_rsp:.2%}")
print()

print("Post-AI Regime:")
print(f"SPY Return: {post_spy:.2%}")
print(f"RSP Return: {post_rsp:.2%}")

top5 = cum_returns[["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL"]].mean(axis=1)

rolling_corr = cum_returns["SPY"].rolling(60).corr(top5)

plt.figure()
plt.plot(rolling_corr)
plt.axvline(pd.to_datetime(AI_START), linestyle="--")
plt.title("Rolling Correlation: SPY vs Top 5 Basket")
plt.show()

# Relative return series (SPY vs RSP)
rel_series = cum_returns["SPY"] / cum_returns["RSP"]

# Compute rolling 6-month return of relative series
rel_6m = rel_series.pct_change(126)  # ~6 months

plt.figure()
plt.plot(rel_6m)
plt.axvline(pd.to_datetime(AI_START), linestyle="--")
plt.title("6-Month Relative Performance (SPY / RSP)")
plt.show()

# Average relative acceleration pre vs post
pre_rel = rel_6m.loc[:AI_START].mean()
post_rel = rel_6m.loc[AI_START:].mean()

print("Average 6M Relative Return:")
print(f"Pre-AI: {pre_rel:.4f}")
print(f"Post-AI: {post_rel:.4f}")


# Use daily returns
spy_ret = returns["SPY"]
# --- Market Cap Weighted Top 5 Basket ---

top5_tickers = ["NVDA", "AAPL", "MSFT", "AMZN", "GOOGL"]

# Get shares outstanding (static approximation)
shares = {}
for t in top5_tickers:
    shares[t] = yf.Ticker(t).info.get("sharesOutstanding", None)

shares_series = pd.Series(shares)

# Compute daily market cap
market_caps = data[top5_tickers].multiply(shares_series, axis=1)

# Compute daily weights (within top 5 universe)
weights = market_caps.div(market_caps.sum(axis=1), axis=0)

# Compute weighted returns
top5_weighted_ret = (returns[top5_tickers] * weights).sum(axis=1)

# Rolling 60-day R²
rolling_corr = spy_ret.rolling(60).corr(top5_weighted_ret)
rolling_r2 = rolling_corr ** 2

plt.figure()
plt.plot(rolling_r2)
plt.axvline(pd.to_datetime(AI_START), linestyle="--")
plt.title("Rolling R²: SPY Explained by Top 5 Basket")
plt.show()

# Compare average R² pre vs post
pre_r2 = rolling_r2.loc[:AI_START].mean()
post_r2 = rolling_r2.loc[AI_START:].mean()

print("Average R²:")
print(f"Pre-AI: {pre_r2:.4f}")
print(f"Post-AI: {post_r2:.4f}")