"""
Cross-Sectional Momentum Decomposition
=======================================
Decomposes cross-sectional momentum returns into:
  - Industry Momentum
  - Stock-Specific Momentum
  - Factor Momentum

Method: Monthly Fama-MacBeth cross-sectional regressions
        with Newey-West corrected standard errors.

Place in: research/analysis/momentum_decomposition.py
Outputs:  data/processed/  and  reports/
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy import stats
from statsmodels.stats.sandwich_covariance import cov_hac
import statsmodels.api as sm
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parents[2]   # adjust if needed
DATA_OUT    = ROOT / "data" / "processed"
REPORTS_OUT = ROOT / "reports"
DATA_OUT.mkdir(parents=True, exist_ok=True)
REPORTS_OUT.mkdir(parents=True, exist_ok=True)

# ── Config ─────────────────────────────────────────────────────────────────────
START       = "2017-01-01"
AI_START    = "2022-11-01"
FORM_START  = 2          # skip most recent month (standard momentum convention)
FORM_END    = 13         # 12-1 month lookback
ROLL_WINDOW = 36         # months for rolling Fama-MacBeth

# ── Universe ───────────────────────────────────────────────────────────────────
# Loaded from CSV — 502 S&P 500 constituents with GICS sectors
# Note: survivorship bias present (current members only, no point-in-time)
SP500_CSV = ROOT / "data" / "raw" / "sp500_companies.csv"

# Factor proxies (ETFs)
FACTOR_TICKERS = {
    "value":   "IWD",
    "size":    "IWM",
    "quality": "QUAL",
    "lowvol":  "USMV",
}



# ── Style ──────────────────────────────────────────────────────────────────────
COLORS = {
    "industry": "#2563EB",   # blue
    "stock":    "#16A34A",   # green
    "factor":   "#DC2626",   # red
    "neutral":  "#6B7280",
    "ai_line":  "#F59E0B",
}
plt.rcParams.update({
    "font.family": "Arial",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "figure.dpi": 150,
})


# ══════════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def load_prices(csv_path: Path, factor_tickers: dict, start: str) -> tuple:
    """
    Loads S&P 500 universe from CSV, downloads monthly prices in batches.
    Returns (stock_prices, factor_prices, sector_map).
    """
    # Load universe
    df         = pd.read_csv(csv_path)
    df         = df[["Symbol", "Sector"]].dropna()
    df         = df[df["Sector"] != ""]
    tickers    = df["Symbol"].tolist()
    sector_map = dict(zip(df["Symbol"], df["Sector"]))

    # Batch download
    BATCH_SIZE = 200
    all_prices = []

    print(f"Downloading {len(tickers)} stocks in batches of {BATCH_SIZE}...")
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        print(f"  Batch {i} → {i + len(batch)}")
        try:
            data = yf.download(
                batch,
                start=start,
                progress=False,
                auto_adjust=True,
            )
            if "Close" in data:
                all_prices.append(data["Close"])
        except Exception as e:
            print(f"  Batch failed: {e}")
            continue

    # Combine and clean
    stock_prices = pd.concat(all_prices, axis=1)
    stock_prices = stock_prices.resample("ME").last()

    # Drop stocks missing more than 10% of history
    threshold    = int(0.9 * len(stock_prices))
    dropped      = stock_prices.columns[stock_prices.count() < threshold].tolist()
    if dropped:
        print(f"  Dropped {len(dropped)} stocks: {dropped[:10]}{'...' if len(dropped) > 10 else ''}")
    stock_prices = stock_prices.dropna(thresh=threshold, axis=1)

    # Sync sector_map to surviving tickers only
    sector_map   = {t: s for t, s in sector_map.items() if t in stock_prices.columns}

    # Download factor ETFs
    all_factors   = list(factor_tickers.values())
    factor_raw    = yf.download(all_factors, start=start, progress=False, auto_adjust=True)["Close"]
    factor_prices = factor_raw.resample("ME").last()

    print(f"  Final universe: {len(stock_prices.columns)} stocks across "
          f"{len(set(sector_map.values()))} sectors.")
    return stock_prices, factor_prices, sector_map

# ══════════════════════════════════════════════════════════════════════════════
# 2. SIGNAL CONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════

def momentum_12_1(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Standard 12-1 momentum: cumulative return from t-13 to t-2
    (skip most recent month to avoid microstructure reversal).
    """
    mom = (1 + returns).rolling(FORM_END).apply(np.prod, raw=True) \
        / (1 + returns).rolling(FORM_START).apply(np.prod, raw=True) - 1
    return mom


def industry_momentum(returns: pd.DataFrame,
                      sector_map: dict) -> pd.DataFrame:
    """
    For each stock, compute the equal-weight average momentum
    of all OTHER stocks in the same sector.
    This is a leave-one-out measure to reduce within-sector correlation.
    """
    mom     = momentum_12_1(returns)
    ind_mom = pd.DataFrame(index=mom.index, columns=mom.columns, dtype=float)

    for sector, tickers in {
        s: [t for t, sec in sector_map.items() if sec == s]
        for s in set(sector_map.values())
    }.items():
        valid = [t for t in tickers if t in mom.columns]
        if len(valid) < 2:
            continue
        for t in valid:
            peers     = [p for p in valid if p != t]
            ind_mom[t] = mom[peers].mean(axis=1)

    return ind_mom


def stock_specific_momentum(stock_mom: pd.DataFrame,
                            ind_mom: pd.DataFrame) -> pd.DataFrame:
    """
    Residual momentum: stock's own momentum minus its industry's momentum.
    Captures idiosyncratic alpha within the sector.
    """
    return stock_mom.sub(ind_mom)


def factor_momentum(factor_returns: pd.DataFrame) -> pd.Series:
    """
    Simple equal-weight composite of 12-1 factor momentum
    across the four factor proxies.
    """
    fmom = momentum_12_1(factor_returns)
    return fmom.mean(axis=1).rename("factor_momentum")


# ══════════════════════════════════════════════════════════════════════════════
# 3. FAMA-MACBETH REGRESSION
# ══════════════════════════════════════════════════════════════════════════════

def cross_sectional_regression(y: pd.Series,
                                X: pd.DataFrame) -> dict:
    """
    Single period OLS cross-sectional regression.
    Returns dict with coefficients and r-squared.
    """
    df = pd.concat([y, X], axis=1).dropna()
    if len(df) < 10:
        return None

    Y_   = df.iloc[:, 0]
    X_   = sm.add_constant(df.iloc[:, 1:])
    res  = sm.OLS(Y_, X_).fit()

    return {
        "alpha":        res.params.get("const", np.nan),
        "beta_industry": res.params.get("industry_mom", np.nan),
        "beta_stock":   res.params.get("stock_mom",    np.nan),
        "beta_factor":  res.params.get("factor_mom",   np.nan),
        "r2":           res.rsquared,
        "n":            int(res.nobs),
    }


def fama_macbeth(fwd_returns: pd.DataFrame,
                 ind_mom:     pd.DataFrame,
                 stk_mom:     pd.DataFrame,
                 fct_mom:     pd.Series) -> pd.DataFrame:
    """
    Run cross-sectional regression each month.
    Returns time series of monthly coefficients.
    """
    results = []
    dates   = fwd_returns.index

    for date in dates:
        if date not in ind_mom.index or date not in fct_mom.index:
            continue

        y = fwd_returns.loc[date]
        X = pd.DataFrame({
            "industry_mom": ind_mom.loc[date],
            "stock_mom":    stk_mom.loc[date],
            "factor_mom":   fct_mom.loc[date],
        })

        row = cross_sectional_regression(y, X)
        if row:
            row["date"] = date
            results.append(row)

    return pd.DataFrame(results).set_index("date")


def newey_west_tstat(series: pd.Series, lags: int = 6) -> tuple:
    """
    Computes mean, Newey-West standard error, and t-stat
    for a time series of regression coefficients.
    """
    clean  = series.dropna()
    mean   = clean.mean()
    X      = sm.add_constant(np.ones(len(clean)))
    model  = sm.OLS(clean.values, X).fit()
    nw_se  = np.sqrt(cov_hac(model, nlags=lags)[0, 0])
    tstat  = mean / nw_se if nw_se > 0 else np.nan
    return mean, nw_se, tstat


def summarise_betas(coefs: pd.DataFrame) -> pd.DataFrame:
    """
    Full-sample and pre/post AI summary table with Newey-West t-stats.
    """
    beta_cols = ["beta_industry", "beta_stock", "beta_factor"]
    rows      = []

    for period, mask in [
        ("Full Sample",   coefs.index >= coefs.index[0]),
        ("Pre-AI",        coefs.index <  pd.Timestamp(AI_START)),
        ("Post-AI",       coefs.index >= pd.Timestamp(AI_START)),
    ]:
        sub = coefs.loc[mask]
        for col in beta_cols:
            mean, se, t = newey_west_tstat(sub[col])
            rows.append({
                "Period":    period,
                "Signal":    col.replace("beta_", "").title(),
                "Mean Beta": round(mean, 4),
                "NW SE":     round(se,   4),
                "t-stat":    round(t,    2),
                "Sig":       "***" if abs(t) > 2.58
                        else "**"  if abs(t) > 1.96
                        else "*"   if abs(t) > 1.64
                        else "",
                "Avg R²":    round(sub["r2"].mean(), 3),
            })

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# 4. ROLLING FAMA-MACBETH
# ══════════════════════════════════════════════════════════════════════════════

def rolling_fama_macbeth(coefs: pd.DataFrame,
                          window: int = ROLL_WINDOW) -> pd.DataFrame:
    """
    Rolling average of monthly betas over `window` months.
    This is your hero chart — shows regime changes in signal attribution.
    """
    return coefs[["beta_industry", "beta_stock", "beta_factor"]] \
               .rolling(window).mean()


# ══════════════════════════════════════════════════════════════════════════════
# 5. DECILE PORTFOLIOS  (optional validation layer)
# ══════════════════════════════════════════════════════════════════════════════

def decile_spread_returns(signal:      pd.DataFrame,
                           fwd_returns: pd.DataFrame,
                           signal_name: str) -> pd.Series:
    """
    Each month: sort stocks into deciles on signal.
    Return = top decile avg - bottom decile avg.
    Long-short decile spread as a reality check.
    """
    spreads = []
    for date in fwd_returns.index:
        if date not in signal.index:
            continue
        combined = pd.concat([
            signal.loc[date].rename("sig"),
            fwd_returns.loc[date].rename("ret")
        ], axis=1).dropna()

        if len(combined) < 20:
            continue

        combined["decile"] = pd.qcut(combined["sig"], 10,
                                     labels=False, duplicates="drop")
        top    = combined[combined["decile"] == 9]["ret"].mean()
        bottom = combined[combined["decile"] == 0]["ret"].mean()
        spreads.append({"date": date, signal_name: top - bottom})

    return pd.DataFrame(spreads).set_index("date")[signal_name]


# ══════════════════════════════════════════════════════════════════════════════
# 6. CHARTS
# ══════════════════════════════════════════════════════════════════════════════

def _add_ai_line(ax):
    ax.axvline(pd.Timestamp(AI_START), color=COLORS["ai_line"],
               linestyle="--", linewidth=1.2, alpha=0.8, label="Nov 2022 (AI era)")


def chart_rolling_betas(rolling: pd.DataFrame, save_path: Path):
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(rolling.index, rolling["beta_industry"], color=COLORS["industry"],
            linewidth=1.8, label="Industry Momentum β")
    ax.plot(rolling.index, rolling["beta_stock"],    color=COLORS["stock"],
            linewidth=1.8, label="Stock-Specific Momentum β")
    ax.plot(rolling.index, rolling["beta_factor"],   color=COLORS["factor"],
            linewidth=1.8, label="Factor Momentum β")
    ax.axhline(0, color="black", linewidth=0.8, linestyle="-")
    _add_ai_line(ax)

    ax.set_title(f"Rolling {ROLL_WINDOW}-Month Fama-MacBeth Betas\n"
                 "Cross-Sectional Momentum Decomposition",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Beta Coefficient")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(fontsize=9, framealpha=0.4)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    print(f"  Saved: {save_path.name}")
    plt.show()


def chart_decile_spreads(spreads: dict, save_path: Path):
    cum = {k: (1 + v).cumprod() for k, v in spreads.items()}

    fig, ax = plt.subplots(figsize=(10, 5))
    color_map = {
        "Industry":     COLORS["industry"],
        "Stock-Specific": COLORS["stock"],
        "Factor":       COLORS["factor"],
    }
    for name, series in cum.items():
        ax.plot(series.index, series, color=color_map.get(name, "grey"),
                linewidth=1.8, label=f"{name} (L/S Decile Spread)")

    _add_ai_line(ax)
    ax.axhline(1, color="black", linewidth=0.8, linestyle="-")
    ax.set_title("Cumulative Returns: Long-Short Decile Spreads\n"
                 "Top Decile Minus Bottom Decile by Signal",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_ylabel("Growth of $1")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(fontsize=9, framealpha=0.4)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    print(f"  Saved: {save_path.name}")
    plt.show()


def chart_beta_bars(summary: pd.DataFrame, save_path: Path):
    """
    Pre vs Post AI bar chart for each signal's mean beta.
    """
    signals    = ["Industry", "Stock", "Factor"]
    pre        = summary[summary["Period"] == "Pre-AI"].set_index("Signal")
    post       = summary[summary["Period"] == "Post-AI"].set_index("Signal")

    x      = np.arange(len(signals))
    width  = 0.35
    fig, ax = plt.subplots(figsize=(8, 5))

    bars1 = ax.bar(x - width/2,
                   [pre.loc[s, "Mean Beta"] for s in signals],
                   width, label="Pre-AI", color=COLORS["neutral"], alpha=0.8)
    bars2 = ax.bar(x + width/2,
                   [post.loc[s, "Mean Beta"] for s in signals],
                   width, label="Post-AI (Nov 2022+)",
                   color=COLORS["ai_line"], alpha=0.9)

    # t-stat annotations
    for bar, sig, period_df in [
        *[(b, s, pre)  for b, s in zip(bars1, signals)],
        *[(b, s, post) for b, s in zip(bars2, signals)],
    ]:
        t = period_df.loc[sig, "t-stat"]
        star = period_df.loc[sig, "Sig"]
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.0005,
                f"t={t:.1f}{star}", ha="center", va="bottom",
                fontsize=8, color="black")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{s} Momentum" for s in signals])
    ax.set_ylabel("Mean Monthly Beta")
    ax.set_title("Momentum Signal Betas: Pre vs Post AI Era\n"
                 "Newey-West t-statistics shown",
                 fontsize=13, fontweight="bold", pad=12)
    ax.legend()
    ax.axhline(0, color="black", linewidth=0.8)
    plt.tight_layout()
    fig.savefig(save_path, bbox_inches="tight")
    print(f"  Saved: {save_path.name}")
    plt.show()

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().dropna(how="all")
# ══════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("Cross-Sectional Momentum Decomposition")
    print("=" * 60)

    # ── Load ──────────────────────────────────────────────────────────────────
    stock_px, factor_px, sector_map = load_prices(
        SP500_CSV, FACTOR_TICKERS, START
    )
    stock_ret  = compute_returns(stock_px)
    factor_ret = compute_returns(factor_px)

    # ── Signals ───────────────────────────────────────────────────────────────
    print("\nConstructing signals...")
    stock_mom_full = momentum_12_1(stock_ret)
    ind_mom        = industry_momentum(stock_ret, sector_map)
    stk_mom        = stock_specific_momentum(stock_mom_full, ind_mom)
    fct_mom        = factor_momentum(factor_ret)

    # Forward returns: 1 month ahead
    fwd_ret = stock_ret.shift(-1)

    # Align all signals to same dates
    common_dates = (stock_mom_full.dropna(how="all").index
                    .intersection(ind_mom.dropna(how="all").index)
                    .intersection(fct_mom.dropna().index))
    fwd_ret  = fwd_ret.loc[common_dates]
    ind_mom  = ind_mom.loc[common_dates]
    stk_mom  = stk_mom.loc[common_dates]
    fct_mom  = fct_mom.loc[common_dates]

    # ── Fama-MacBeth ──────────────────────────────────────────────────────────
    print("\nRunning Fama-MacBeth regressions...")
    coefs   = fama_macbeth(fwd_ret, ind_mom, stk_mom, fct_mom)
    summary = summarise_betas(coefs)

    print("\n── Summary Table ──────────────────────────────────────────")
    print(summary.to_string(index=False))

    # Save
    coefs.to_csv(DATA_OUT / "fm_coefficients.csv")
    summary.to_csv(DATA_OUT / "fm_summary.csv", index=False)
    print(f"\nSaved coefficients → {DATA_OUT}")

    # ── Rolling Betas ─────────────────────────────────────────────────────────
    print("\nGenerating charts...")
    rolling = rolling_fama_macbeth(coefs)

    chart_rolling_betas(
        rolling,
        REPORTS_OUT / "chart1_rolling_betas.png"
    )

    # ── Beta Bar Chart ────────────────────────────────────────────────────────
    chart_beta_bars(
        summary,
        REPORTS_OUT / "chart2_beta_pre_post_ai.png"
    )

    # ── Decile Spreads ────────────────────────────────────────────────────────
    print("\nComputing decile spread portfolios...")

    # Factor momentum is a single value per date — broadcast it across all
    # stocks so decile_spread_returns receives a stock-shaped DataFrame.
    fct_mom_broadcast = pd.DataFrame(
        np.tile(fct_mom.values[:, None], (1, ind_mom.shape[1])),
        index=fct_mom.index,
        columns=ind_mom.columns,
    )

    spreads = {
        "Industry":       decile_spread_returns(ind_mom,           fwd_ret, "Industry"),
        "Stock-Specific": decile_spread_returns(stk_mom,           fwd_ret, "Stock-Specific"),
        "Factor":         decile_spread_returns(fct_mom_broadcast, fwd_ret, "Factor"),
    }

    chart_decile_spreads(
        spreads,
        REPORTS_OUT / "chart3_decile_spreads.png"
    )

    # ── Quick diagnostics ─────────────────────────────────────────────────────
    print("\n── Signal Correlation Matrix ──────────────────────────────")
    stacked_index = ind_mom.stack().index
    fct_broadcast = fct_mom.reindex(ind_mom.index).repeat(ind_mom.shape[1])
    fct_broadcast.index = stacked_index

    sig_df = pd.DataFrame({
        "IndMom": ind_mom.stack(),
        "StkMom": stk_mom.stack(),
        "FctMom": fct_broadcast,
    }).dropna()
    print(sig_df.corr().round(3))
    print("\nLow correlation between signals = clean decomposition ✓")

    print("\nDone. Charts saved to:", REPORTS_OUT)


if __name__ == "__main__":
    main()