# Sector Leadership Cycles in India

**Date:** 2026-03-11
**Status:** Idea
**Author:** @AlphaByProcess

---

## Question

How often do sector leaders change in Indian equities — and is there a
predictable pattern to that rotation?

---

## Hypothesis

> Sector leadership in Indian equities (Nifty sectoral indices) is
> mean-reverting over a 3–6 month horizon. The top-performing sector in
> quarter N is more likely to underperform in quarter N+1 than to
> continue outperforming.

**Null hypothesis:**
> Sector returns exhibit no autocorrelation. Past leadership has no
> predictive power over future leadership. Rotation is random.

**Secondary hypothesis:**
> Nifty sector rotation frequency is statistically higher than S&P 500
> sector rotation over the same period, measured by leadership
> persistence ratio. Indian markets rotate faster than developed markets.

---

## Why It Matters

Most retail and institutional narratives in India treat sector momentum
as persistent ("IT is on a run", "pharma is in favour"). If rotation is
systematically mean-reverting, that narrative is wrong — and exploitable.

The US comparison gives this a publishable angle: India as a structural
case study in emerging market sector dynamics vs developed market
behaviour.

---

## Tests

### Test 1 — Descriptive: Leadership Persistence Ratio
- Compute rolling 3M returns for each Nifty sector
- Rank sectors each quarter (1 = best, N = worst)
- Track: does rank 1 stay rank 1 next quarter?
- Compute **leadership persistence ratio** = % of quarters where top
  sector remains top

**Benchmark:**
- Random expectation ≈ 1/N (e.g. 1/10 = 10% for 10 sectors)
- < random → mean-reverting (supports hypothesis)
- \> random → momentum (rejects hypothesis)

---

### Test 2 — Statistical: Rank Autocorrelation
- Compute Spearman rank autocorrelation of sector returns at lag 1, 2, 3 quarters
- Test for statistical significance (p < 0.05)
- Negative autocorrelation → mean reversion confirmed
- Positive autocorrelation → momentum confirmed

---

### Test 3 — Comparative: India vs US
- Run identical analysis on S&P 500 sectors (XLK, XLV, XLE, XLF etc.)
- Same period, same methodology
- Compare persistence ratios using bootstrap test (n=1000 resamples)
- Is the difference statistically significant?

---

### Test 4 — Transition Matrix: Where Do Leaders Go?

Rank each sector into terciles each quarter (Top, Middle, Bottom).
Build a 3×3 transition matrix: given a sector is in tercile X this
quarter, what is the probability it lands in each tercile next quarter?

## Data

| Index | Ticker (yfinance) | Sector |
|---|---|---|
| Nifty IT | `^CNXIT` | Technology |
| Nifty Pharma | `^CNXPHARMA` | Healthcare |
| Nifty FMCG | `^CNXFMCG` | Consumer Staples |
| Nifty Bank | `^NSEBANK` | Financials |
| Nifty Auto | `^CNXAUTO` | Automobiles |
| Nifty Metal | `^CNXMETAL` | Materials |
| Nifty Realty | `^CNXREALTY` | Real Estate |
| Nifty Energy | `^CNXENERGY` | Energy |
| S&P 500 sectors | `XLK, XLV, XLE, XLF, XLY, XLP, XLI, XLB, XLU, XLRE` | US Benchmark |

**Period:** 2012–present (longer history = more robust rotation cycles)
**Frequency:** Monthly returns, quarterly rankings

> ⚠️ Verify yfinance coverage for Nifty tickers before building analysis.
> Some may have limited history or gaps.




