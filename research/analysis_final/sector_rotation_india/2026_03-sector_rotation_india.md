# Findings — Sector Leadership Cycles in India

**Date:** 2026-03-11
**Status:** Complete
**Author:** @AlphaByProcess

---

## Summary

Sector leadership in Indian equities is mean-reverting — but the reversion is structural rather than mechanical. The top-performing Nifty sector in a given quarter is less likely to retain leadership next quarter than pure chance would predict. However, the signal is too noisy and statistically weak to be exploited with a fixed-lag rotation strategy. The secondary hypothesis — that India rotates faster than the US — is cleanly rejected: both markets exhibit identical rotation dynamics across every metric tested.

---

## Data

8 Nifty sectoral indices and 8 S&P 500 SPDR sector ETFs, sourced via yfinance. Effective period: January 2012 to March 2026 (54 quarters). Start date determined by the binding constraint of `^CNXAUTO` and `^CNXMETAL`, both of which begin in mid-2011. Monthly prices resampled to calendar quarter-end. Zero missing values across all 16 series.

Three macro regimes defined for conditioning analysis: Pre-COVID (Q1 2012 – Q4 2019), COVID Recovery (Q1 2020 – Q4 2021), Rate Hike (Q1 2022 – present).

---

## Test 1 — Leadership Persistence Ratio

**Result: Mean-reverting. Primary hypothesis supported.**

The top-ranked Nifty sector repeated as top sector in the following quarter only 9.3% of the time, against a random baseline of 12.5% (1/8). The top-quartile persistence — tracking the top 2 sectors rather than just rank 1 — was 26.9%, barely above the 25% random baseline. Both measures confirm that sector leadership in India does not persist.

The regime breakdown adds the most interesting texture. Pre-COVID persistence was 10.3%, below random. COVID Recovery was exactly 12.5%, indistinguishable from random — macro forces dominated sector selection during that period, making rotation essentially unpredictable. The rate hike regime produced the sharpest mean reversion of all three at 5.9%, less than half the random baseline. Rising rates appear to accelerate leadership turnover.

The leadership frequency distribution is a secondary finding worth noting. Realty led the cross-section in 29.1% of quarters — nearly one in three — despite not being a large index constituent. Bank Nifty, the largest weight in Nifty 50, led in only 5.5% of quarters. The sectors that dominate index performance are not the sectors that dominate quarterly leadership cycles.

---

## Test 2 — Rank Autocorrelation (Spearman)

**Result: Direction correct, statistically insignificant across all sectors and lags.**

The average Spearman ρ across all 8 sectors at lag 1 is -0.001, at lag 2 is +0.020, and at lag 3 is -0.024. The direction at lags 1 and 3 is consistent with mean reversion, but zero out of 8 sectors clear the p < 0.05 threshold at any lag. The pooled cross-sectional autocorrelation at lag 1 is +0.005 (p = 0.913) — statistically indistinguishable from zero.

The regime-conditioned results are similarly flat: Pre-COVID ρ = +0.038 (p = 0.567), COVID Recovery ρ = +0.027 (p = 0.842), Rate Hike ρ = -0.001 (p = 0.987). Mean reversion does not concentrate in any particular macro environment.

Two sectors diverge from the average. Pharma shows positive autocorrelation at both lag 1 (+0.161) and lag 2 (+0.092) — a mild momentum signature consistent across multiple lags, though not significant. Metal shows the strongest positive autocorrelation at lag 3 (+0.220), suggesting a slightly longer cycle before mean reversion kicks in.

The interpretation of this test matters for the paper's conclusion. Weak autocorrelation does not contradict Test 1 — it qualifies it. Rotation is real but not on a reliable schedule. The market doesn't revert at a fixed lag; it reverts eventually, with timing that varies by cycle and sector. This is structurally mean-reverting behaviour, not mechanically exploitable momentum.

---

## Test 3 — India vs US

**Result: Secondary hypothesis rejected. Rotation dynamics are identical.**

India and US persistence ratios are both 9.1%. The observed difference is +0.0%. The bootstrap test (n=1000 resamples) produces a p-value of 1.000 and a 95% confidence interval of [-0.127, +0.145] — completely straddling zero. The Spearman ρ at lag 1 is +0.005 for India and -0.001 for US, again indistinguishable.

The hypothesis that Indian markets rotate faster than developed markets — a reasonable prior given the EM liquidity and retail-driven narrative environment — is not supported by the data. Both markets rotate at the same speed, below the random baseline, with structurally similar autocorrelation profiles.

The more interesting implication is that mean reversion in sector leadership appears to be a property of equity markets in general, not a feature unique to emerging markets. India is not an outlier; it is representative.

---

## Test 4 — Rank Transition Matrix

**Result: Gradual fade, not sharp reversal. Symmetric across India and US.**

The transition matrix reveals how sector leadership decays. When India's top-tercile sectors leave the top, 47.2% move to the middle tercile and only 25.9% fall straight to the bottom. The US pattern is near-identical: 50.0% to Mid, 23.1% to Bot. Leadership erodes gradually rather than collapsing — consistent with the weak autocorrelation in Test 2, where the timing of reversion is diffuse rather than concentrated at a single lag.

P(Top → Top) is 26.9% for both India and US, against a random baseline of 33.3%. Both are below random, confirming mean reversion at the tercile level, and both are at exactly the same level — a further confirmation that the rotation mechanism is structurally identical across markets.

One asymmetry is worth flagging. India's bottom sectors have a 23.1% probability of recovering to the top tercile, compared to 26.9% for US. Losers are slightly stickier in India than in the US. This may reflect the thinner liquidity and higher transaction costs in Nifty sectoral indices relative to SPDR ETFs, making recovery rotations slower to materialise.

---

## Conclusions

**Primary hypothesis — supported, with qualification.** Sector leadership in Indian equities is mean-reverting. The top sector is less likely to remain top than chance alone would predict, and this holds across all three macro regimes. The qualification is that the reversion is structural rather than mechanical — there is no fixed lag at which it reliably occurs, which limits direct trading applications.

**Secondary hypothesis — rejected.** India does not rotate faster than the US. Persistence ratios, autocorrelation profiles, and transition matrices are identical across both markets. Mean reversion in sector leadership is a universal market feature, not an emerging market phenomenon.

**The narrative implication.** The common market language — "IT is on a run", "Pharma is in favour" — embeds an assumption of persistence that the data does not support. Leadership rotates. The sectors dominating today's conversation are, on average, more likely to be next quarter's laggards than next quarter's leaders. Investors anchored to current sector narratives are systematically leaning against the direction of the market's own rotation dynamics.

---

## Limitations

- 54 quarters is adequate but not long. Findings should be revisited as the sample extends, particularly to build more statistical power in the regime-conditioned tests.
- The Nifty sectoral indices are highly concentrated. Bank Nifty tracks a small number of large-cap banks; Realty tracks a small-cap dominated universe. Intra-sector concentration may distort the cross-sectional ranking in ways that a more diversified sector definition would not.
- The US comparison uses SPDR ETFs, which are tradeable instruments with their own liquidity and flow dynamics. The Nifty sectoral indices are not directly investable in the same way. This is a like-for-like comparison of market structure, not of investor experience.
- Regime definitions are coarse. A more precise rate cycle definition — using RBI policy rate change dates — would produce sharper conditioning than the calendar-based Pre/COVID/Rate Hike split used here.

---

## Tradable Insight

The data does not support a systematic long-short sector rotation strategy. Test 2 eliminated that possibility — there is no reliable lag at which mean reversion concentrates, so there is no mechanical entry signal to build a strategy around.

What the data does support is a **narrative contrarian overlay** for risk management. When a sector has dominated financial media and analyst commentary for a full quarter, the persistence ratio says that leadership is more likely to rotate away than to continue. The consensus trade, at the point it becomes consensus, is statistically closer to a peak than a continuation.

The Rate Hike regime sharpens this further. With persistence dropping to 5.9% during tightening cycles — less than half the random baseline — concentration in the favoured sector during RBI rate hike periods has historically been the worst time to add to that position. The market rotates fastest precisely when macro uncertainty is highest and sector narratives feel most compelling.

The transition matrix adds one practical qualification. When top sectors fall, 47% move to the middle tercile and only 26% fall straight to the bottom. The rotation is gradual, not violent. This means there is typically time to reduce a position as a sector fades — but not time to wait for confirmation before starting to trim.

The honest framing: this is a **risk management insight, not an alpha generation one**. It tells you when to be sceptical of persistence, not what to buy next. The transition matrix shows where leadership goes in aggregate — to the middle — but not which specific sector rises to replace it. A predictive model for successor sectors would require a separate analysis.

---

## Open Questions

- Does the Pharma momentum signature persist if tested on a longer pre-2012 sample?
- Is the bottom-sector stickiness in India a function of liquidity, sectoral concentration, or something else?
- Would monthly rather than quarterly ranking produce a stronger or weaker mean-reversion signal?
- Can the regime conditioning be sharpened using a quantitative regime detection model rather than calendar dates?


