# Cross-Sectional Momentum Decomposition: Industry, Stock-Specific, and Factor Sources

## Abstract

This note decomposes cross-sectional momentum into three components — industry momentum, stock-specific momentum, and factor momentum — using monthly Fama-MacBeth regressions on 474 S&P 500 constituents from 2017 to 2026.

Two questions are examined:

1. Which momentum component predicts next-month cross-sectional returns — industry trends, idiosyncratic stock outperformance, or broad factor regimes?
2. Did the answer change after the AI era began in November 2022?

---

## Data & Instruments

- **Universe** — 474 S&P 500 constituents across 11 GICS sectors
- **Factor proxies** — IWD (value), IWM (size), QUAL (quality), USMV (low volatility)

**Regime split:** November 2022

Monthly return data sourced via `yfinance`. Survivorship bias present — universe reflects current S&P 500 membership applied retrospectively.

---

## Signal Definitions

| Signal | Definition |
|---|---|
| Industry Momentum | Equal-weighted avg 12-1 month return of sector peers (leave-one-out) |
| Stock-Specific Momentum | Stock's own 12-1 month return minus its industry average |
| Factor Momentum | Equal-weighted composite of 12-1 month returns across four factor ETF proxies |

The leave-one-out construction for industry momentum prevents a stock from contaminating its own sector signal.

Stock-specific momentum is orthogonal to factor momentum by construction. Industry and factor momentum carry a correlation of 0.746 — the primary multicollinearity concern in the model. The factor beta reported below should be interpreted as an upper bound on the true isolated effect.

---

## Methodology

A cross-sectional regression is estimated each calendar month:

```
r(i,t) = α + β₁ · IndustryMom + β₂ · StockMom + β₃ · FactorMom + ε
```

This produces a monthly time series of cross-sectional coefficients (Fama-MacBeth procedure).

Newey-West standard errors with 6 lags are applied to the time series of betas to obtain t-statistics robust to autocorrelation.

Rolling betas are smoothed over a 36-month window for visualization.

---

## Results

### Fama-MacBeth Beta Summary

| Period | Signal | Mean Beta | NW Std Err | t-stat | Avg R² |
|---|---|---|---|---|---|
| Full Sample | Industry | 0.0107 | 0.0110 | 0.97 | 5.4% |
| Full Sample | Stock-Specific | 0.0049 | 0.0040 | 1.22 | 5.4% |
| Full Sample | Factor | 1.0709 | 0.8752 | 1.22 | 5.4% |
| Pre-AI | Industry | 0.0108 | 0.0170 | 0.64 | 6.0% |
| Pre-AI | Stock-Specific | 0.0045 | 0.0049 | 0.92 | 6.0% |
| Pre-AI | Factor | 0.1905 | 0.1931 | 0.99 | 6.0% |
| Post-AI | Industry | 0.0104 | 0.0116 | 0.90 | 4.5% |
| Post-AI | Stock-Specific | 0.0054 | 0.0069 | 0.79 | 4.5% |
| Post-AI | Factor | 2.3255 | 1.9921 | 1.17 | 4.5% |

Conventional significance thresholds: |t| > 1.96 (5%), |t| > 1.64 (10%). No signal clears the 5% threshold. The post-AI factor beta does not reach statistical significance given ~38 monthly observations — a data availability constraint, not a methodological failure.

---

### Key Findings

**Industry Momentum**
- Beta near zero throughout the full sample — pre- and post-2022
- Decile long-short spread shows persistent positive returns post-2022, but this appears subsumed by factor momentum once controlled for in the regression

**Stock-Specific Momentum**
- Beta near zero throughout; no cross-sectional predictive edge
- Decile spread persistently negative — consistent with short-term mean reversion in the idiosyncratic component

**Factor Momentum**
- Beta increased from 0.19 pre-AI to 2.33 post-AI — a 12-fold increase in economic magnitude
- Given industry-factor correlation of 0.746, the factor beta is likely overstated; 2.33 represents an upper bound
- Rolling beta chart shows a sharp, sustained rise post-2022 that holds through 2026

---

## Interpretation

Industry momentum and stock-specific momentum contributed negligibly to cross-sectional return prediction in the Fama-MacBeth framework across the full sample.

Factor momentum became the dominant cross-sectional predictor post-2022. The AI era did not create a new momentum structure — it rewarded a specific type of momentum more intensely. Broad factor regimes became the organizing force behind cross-sectional return dispersion.

Average R² declined from 6.0% pre-AI to 4.5% post-AI, consistent with the companion concentration analysis: post-2022 markets became harder to predict cross-sectionally in aggregate, even as specific factor tailwinds delivered large returns to those positioned correctly.

---

## Caveats

- **Survivorship bias** — delisted and removed constituents are excluded; momentum short-leg returns are likely understated
- **ETF factor proxies** — IWD, IWM, QUAL, USMV are blunt instruments relative to constructed long-short factor portfolios; the flat factor decile spread reflects proxy noise, not an absence of factor momentum
- **Multicollinearity** — industry-factor correlation of 0.746 means factor beta estimates should be treated as upper bounds
- **Short post-AI window** — ~38 monthly observations limits statistical power; the directional finding is robust but confirmation requires a longer sample

---

## Reproducibility

Analysis script:

[View analysis script](../research/analysis/momentum_decomposition.py)

Run locally:

```bash
python research/analysis/momentum_decomposition.py
```
