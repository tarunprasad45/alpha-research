"""
Sector Rotation India | @AlphaByProcess
research/analysis/sector_rotation_india/sector_rotation_analysis.py

Run from inside the project folder:
  cd research/analysis/sector_rotation_india
  python sector_rotation_analysis.py

Expects:
  ../../../data/raw/sector_prices_monthly.csv

Outputs:
  findings/01_leadership_persistence.csv
  findings/01_persistence_by_regime.csv
  findings/01_leadership_frequency.csv
  findings/02_rank_autocorrelation.csv
  findings/02_pooled_autocorr.csv
  findings/02_autocorr_by_regime.csv
  findings/03_india_vs_us.csv
  findings/03_bootstrap_test.csv
  findings/04_transition_matrix_india.csv
  findings/04_transition_matrix_us.csv
  findings/04_transition_summary.csv
  findings/charts/fig1_leadership_heatmap.png
  findings/charts/fig2_persistence_ratio.png
  findings/charts/fig3_autocorrelation.png
  findings/charts/fig4_india_vs_us.png
  findings/charts/fig5_transition_matrix.png
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from scipy import stats
import os

np.random.seed(42)

# ── Paths ─────────────────────────────────────────────────────────────────────

DATA_IN      = "../../../data/raw/sector_prices_monthly.csv"
FINDINGS_DIR = "findings"
CHARTS_DIR   = "findings/charts"

os.makedirs(FINDINGS_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR,   exist_ok=True)

# ── Sector Universe ───────────────────────────────────────────────────────────

INDIA_SECTORS = ["IT", "Pharma", "FMCG", "Bank", "Auto",
                 "Metal", "Realty", "Energy"]
US_SECTORS    = ["US_Tech", "US_Health", "US_Energy", "US_Financials",
                 "US_ConsDisc", "US_ConsStap", "US_Industrial", "US_Materials"]
ALL_SECTORS   = INDIA_SECTORS + US_SECTORS

N              = len(INDIA_SECTORS)
RANDOM_BASELINE = 1 / N  # 12.5%

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — BUILD PANEL
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("PHASE 2 — BUILDING PANEL")
print("=" * 60)

prices = pd.read_csv(DATA_IN, index_col=0, parse_dates=True)
prices = prices[ALL_SECTORS]

quarterly_prices  = prices.resample("QE").last()
quarterly_returns = quarterly_prices.pct_change().dropna()

def rank_quarter(row):
    return row.rank(ascending=False, method="min")

india_ranks = quarterly_returns[INDIA_SECTORS].apply(rank_quarter, axis=1)
india_ranks.columns = [f"{c}_rank" for c in INDIA_SECTORS]

us_ranks = quarterly_returns[US_SECTORS].apply(rank_quarter, axis=1)
us_ranks.columns = [f"{c}_rank" for c in US_SECTORS]

for lag in [1, 2, 3]:
    for col in INDIA_SECTORS:
        india_ranks[f"{col}_rank_lag{lag}"] = india_ranks[f"{col}_rank"].shift(lag)

def assign_regime(date):
    if date < pd.Timestamp("2020-01-01"):
        return "pre_covid"
    elif date < pd.Timestamp("2022-01-01"):
        return "covid_recovery"
    else:
        return "rate_hike"

quarterly_returns["regime"] = quarterly_returns.index.map(assign_regime)

panel = pd.concat([quarterly_returns, india_ranks, us_ranks], axis=1)
panel = panel.dropna(subset=[f"{INDIA_SECTORS[0]}_rank_lag1"])
panel.index.name = "quarter"

print(f"  Quarters      : {len(panel)}")
print(f"  Date range    : {panel.index[0].date()} → {panel.index[-1].date()}")
print(f"  Regime counts : {panel['regime'].value_counts().to_dict()}")
print("✓ Panel built\n")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — LEADERSHIP PERSISTENCE RATIO
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("TEST 1 — LEADERSHIP PERSISTENCE RATIO")
print("=" * 60)

def get_top_sector(row):
    for s in INDIA_SECTORS:
        if row[f"{s}_rank"] == 1:
            return s
    return None

panel["top_sector"]      = panel.apply(get_top_sector, axis=1)
panel["top_sector_lag1"] = panel["top_sector"].shift(1)

valid              = panel.dropna(subset=["top_sector", "top_sector_lag1"])
valid              = valid.copy()
valid["persisted"] = valid["top_sector"] == valid["top_sector_lag1"]
persistence_ratio  = valid["persisted"].mean()
n_quarters         = len(valid)

# Top quartile persistence
def get_top_quartile(row):
    return frozenset(s for s in INDIA_SECTORS if row[f"{s}_rank"] <= 2)

panel["top_q"]      = panel.apply(get_top_quartile, axis=1)
panel["top_q_lag1"] = panel["top_q"].shift(1)

def quartile_overlap(row):
    if not isinstance(row["top_q_lag1"], frozenset):
        return np.nan
    return len(row["top_q"] & row["top_q_lag1"]) / 2

panel["quartile_persistence"] = panel.apply(quartile_overlap, axis=1)
quartile_ratio = panel["quartile_persistence"].mean()

print(f"  Quarters analysed      : {n_quarters}")
print(f"  Random baseline (1/N)  : {RANDOM_BASELINE:.1%}")
print(f"  Top-1 persistence      : {persistence_ratio:.1%}")
print(f"  Top-quartile persist   : {quartile_ratio:.1%}")
verdict = "MEAN-REVERTING" if persistence_ratio < RANDOM_BASELINE else "MOMENTUM"
print(f"  Verdict                : {verdict}")

leadership_freq     = panel["top_sector"].value_counts()
leadership_freq_pct = (leadership_freq / len(panel) * 100).round(1)

print(f"\n  Leadership frequency:")
for sector, pct in leadership_freq_pct.items():
    print(f"    {sector:<10} {pct:.1f}%")

regime_results = []
print(f"\n  By regime:")
for regime in ["pre_covid", "covid_recovery", "rate_hike"]:
    subset = valid[valid["regime"] == regime]
    if len(subset) < 3:
        continue
    ratio = subset["persisted"].mean()
    regime_results.append({"regime": regime, "quarters": len(subset),
                            "persistence_ratio": round(ratio, 4),
                            "vs_random": round(ratio - RANDOM_BASELINE, 4)})
    direction = "↓ mean-revert" if ratio < RANDOM_BASELINE else "↑ momentum"
    print(f"    {regime:<22} {ratio:.1%}  {direction}")

# Save
pd.DataFrame([{"n_quarters": n_quarters, "random_baseline": RANDOM_BASELINE,
               "top1_persistence": round(persistence_ratio, 4),
               "top_quartile_persist": round(quartile_ratio, 4),
               "verdict": verdict}
              ]).to_csv(f"{FINDINGS_DIR}/01_leadership_persistence.csv", index=False)
pd.DataFrame(regime_results).to_csv(f"{FINDINGS_DIR}/01_persistence_by_regime.csv", index=False)
leadership_freq_pct.rename("pct_quarters_led").to_csv(f"{FINDINGS_DIR}/01_leadership_frequency.csv")
print("✓ Test 1 complete\n")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — RANK AUTOCORRELATION
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("TEST 2 — SPEARMAN RANK AUTOCORRELATION")
print("=" * 60)

def spearman_autocorr(series, lag):
    s = series.dropna()
    x, y = s.iloc[lag:].values, s.iloc[:-lag].values
    if len(x) < 5:
        return np.nan, np.nan, 0
    rho, pval = stats.spearmanr(x, y)
    return round(rho, 4), round(pval, 4), len(x)

print(f"\n  {'Sector':<12} {'Lag1 ρ':>8} {'p':>7} {'Lag2 ρ':>8} {'p':>7} {'Lag3 ρ':>8} {'p':>7}")
print("  " + "-" * 65)

full_results = []
for sector in INDIA_SECTORS:
    row      = {"sector": sector}
    row_print = f"  {sector:<12}"
    for lag in [1, 2, 3]:
        rho, pval, n = spearman_autocorr(panel[f"{sector}_rank"], lag)
        row[f"rho_lag{lag}"]  = rho
        row[f"pval_lag{lag}"] = pval
        row[f"n_lag{lag}"]    = n
        sig = "*" if pval < 0.05 else " "
        row_print += f"  {rho:>+7.3f}{sig}  {pval:>6.3f}"
    full_results.append(row)
    print(row_print)

print("\n  * = p < 0.05")

results_df = pd.DataFrame(full_results)
print(f"\n  Average ρ across all sectors:")
pooled_results = []
for lag in [1, 2, 3]:
    avg_rho = results_df[f"rho_lag{lag}"].mean()
    n_sig   = (results_df[f"pval_lag{lag}"] < 0.05).sum()
    print(f"    Lag {lag}: ρ = {avg_rho:+.3f}  |  {n_sig}/{N} significant  |  "
          f"{'mean-reverting' if avg_rho < 0 else 'momentum'}")

print(f"\n  Pooled cross-sectional autocorrelation:")
for lag in [1, 2, 3]:
    all_r, all_l = [], []
    for s in INDIA_SECTORS:
        r = panel[f"{s}_rank"].dropna()
        all_r.extend(r.iloc[lag:].values)
        all_l.extend(r.iloc[:-lag].values)
    rho, pval = stats.spearmanr(all_r, all_l)
    pooled_results.append({"lag": lag, "pooled_rho": round(rho, 4),
                            "pooled_pval": round(pval, 4)})
    sig = "✓" if pval < 0.05 else "✗"
    print(f"    Lag {lag}: ρ = {rho:+.4f}  p = {pval:.4f}  {sig}  "
          f"{'mean-reverting' if rho < 0 else 'momentum'}")

regime_autocorr = []
print(f"\n  By regime (lag 1, pooled):")
for regime in ["pre_covid", "covid_recovery", "rate_hike"]:
    subset = panel[panel["regime"] == regime]
    if len(subset) < 5:
        continue
    all_r, all_l = [], []
    for s in INDIA_SECTORS:
        r = subset[f"{s}_rank"].dropna()
        if len(r) > 1:
            all_r.extend(r.iloc[1:].values)
            all_l.extend(r.iloc[:-1].values)
    if len(all_r) < 5:
        continue
    rho, pval = stats.spearmanr(all_r, all_l)
    regime_autocorr.append({"regime": regime, "n_obs": len(all_r),
                             "rho_lag1": round(rho, 4), "pval_lag1": round(pval, 4)})
    print(f"    {regime:<22} ρ = {rho:+.3f}  p = {pval:.3f}  "
          f"{'mean-reverting' if rho < 0 else 'momentum'}")

# Save
results_df.to_csv(f"{FINDINGS_DIR}/02_rank_autocorrelation.csv", index=False)
pd.DataFrame(pooled_results).to_csv(f"{FINDINGS_DIR}/02_pooled_autocorr.csv", index=False)
pd.DataFrame(regime_autocorr).to_csv(f"{FINDINGS_DIR}/02_autocorr_by_regime.csv", index=False)
print("✓ Test 2 complete\n")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — INDIA vs US
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("TEST 3 — INDIA vs US SECTOR ROTATION")
print("=" * 60)

def compute_persistence_ratio(panel_df, sectors):
    def get_top(row):
        for s in sectors:
            if row[f"{s}_rank"] == 1:
                return s
        return None
    top     = panel_df.apply(get_top, axis=1)
    top_lag = top.shift(1)
    persisted = (top == top_lag).dropna()
    return persisted.mean(), len(persisted)

def pooled_spearman_lag1(panel_df, sectors):
    all_r, all_l = [], []
    for s in sectors:
        r = panel_df[f"{s}_rank"].dropna()
        all_r.extend(r.iloc[1:].values)
        all_l.extend(r.iloc[:-1].values)
    rho, pval = stats.spearmanr(all_r, all_l)
    return round(rho, 4), round(pval, 4)

india_persist, india_n = compute_persistence_ratio(panel, INDIA_SECTORS)
us_persist,    us_n    = compute_persistence_ratio(panel, US_SECTORS)
india_rho, india_pval  = pooled_spearman_lag1(panel, INDIA_SECTORS)
us_rho,    us_pval     = pooled_spearman_lag1(panel, US_SECTORS)

print(f"\n  {'Metric':<35} {'India':>10} {'US':>10}")
print("  " + "-" * 57)
print(f"  {'Persistence ratio':<35} {india_persist:>10.1%} {us_persist:>10.1%}")
print(f"  {'Spearman ρ (lag 1)':<35} {india_rho:>+10.3f} {us_rho:>+10.3f}")
print(f"  {'p-value':<35} {india_pval:>10.4f} {us_pval:>10.4f}")

diff = india_persist - us_persist
print(f"\n  Difference (India - US): {diff:+.1%}")

# Bootstrap
print(f"\n  Running bootstrap (n=1000)...")
N_BOOT, boot_diffs = 1000, []
quarters = panel.index.tolist()

for _ in range(N_BOOT):
    idx         = np.random.choice(len(quarters), size=len(quarters), replace=True)
    boot_panel  = panel.iloc[idx].copy()
    for s in INDIA_SECTORS:
        boot_panel[f"{s}_rank"] = boot_panel[INDIA_SECTORS].rank(
            axis=1, ascending=False, method="min")[s]
    for s in US_SECTORS:
        boot_panel[f"{s}_rank"] = boot_panel[US_SECTORS].rank(
            axis=1, ascending=False, method="min")[s]
    i_p, _ = compute_persistence_ratio(boot_panel, INDIA_SECTORS)
    u_p, _ = compute_persistence_ratio(boot_panel, US_SECTORS)
    boot_diffs.append(i_p - u_p)

boot_diffs = np.array(boot_diffs)
p_boot     = np.mean(np.abs(boot_diffs) >= np.abs(diff))
ci_lo, ci_hi = np.percentile(boot_diffs, [2.5, 97.5])

print(f"  Bootstrap p-value    : {p_boot:.4f} "
      f"({'significant' if p_boot < 0.05 else 'not significant'})")
print(f"  95% CI               : [{ci_lo:+.3f}, {ci_hi:+.3f}]")

# Save
pd.DataFrame([
    {"market": "India", "persistence_ratio": round(india_persist, 4),
     "spearman_rho_lag1": india_rho, "spearman_pval": india_pval, "n": india_n},
    {"market": "US",    "persistence_ratio": round(us_persist, 4),
     "spearman_rho_lag1": us_rho,    "spearman_pval": us_pval,    "n": us_n},
]).to_csv(f"{FINDINGS_DIR}/03_india_vs_us.csv", index=False)

pd.DataFrame([{"observed_diff": round(diff, 4), "bootstrap_pval": round(p_boot, 4),
               "ci_lo_95": round(ci_lo, 4), "ci_hi_95": round(ci_hi, 4),
               "significant": p_boot < 0.05}
              ]).to_csv(f"{FINDINGS_DIR}/03_bootstrap_test.csv", index=False)
print("✓ Test 3 complete\n")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — TRANSITION MATRIX
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("TEST 4 — RANK TRANSITION MATRIX")
print("=" * 60)

def assign_tercile(rank):
    if rank <= 2:   return "Top"
    elif rank <= 6: return "Mid"
    else:           return "Bot"

def build_transition_matrix(panel_df, sectors, label=""):
    transitions = []
    for s in sectors:
        r = panel_df[f"{s}_rank"].dropna()
        t = r.map(assign_tercile)
        for i in range(len(t) - 1):
            transitions.append({"current": t.iloc[i], "next": t.iloc[i+1]})
    df     = pd.DataFrame(transitions)
    counts = pd.crosstab(df["current"], df["next"])
    counts = counts.reindex(index=["Top","Mid","Bot"],
                            columns=["Top","Mid","Bot"], fill_value=0)
    probs  = counts.div(counts.sum(axis=1), axis=0).round(3)
    print(f"\n  {label} Transition Probabilities:")
    print(f"  {'':6} {'→ Top':>8} {'→ Mid':>8} {'→ Bot':>8}  {'(n)':>6}")
    for t in ["Top", "Mid", "Bot"]:
        print(f"  {t:<6} {probs.loc[t,'Top']:>8.1%} {probs.loc[t,'Mid']:>8.1%} "
              f"{probs.loc[t,'Bot']:>8.1%}  {counts.loc[t].sum():>6}")
    return probs, counts

india_probs, _ = build_transition_matrix(panel, INDIA_SECTORS, "INDIA")
us_probs,    _ = build_transition_matrix(panel, US_SECTORS,    "US")

print(f"\n  P(Top → Top): India {india_probs.loc['Top','Top']:.1%}  "
      f"US {us_probs.loc['Top','Top']:.1%}  (random: 33.3%)")
print(f"  India top sectors — P(→ Mid): {india_probs.loc['Top','Mid']:.1%}  "
      f"P(→ Bot): {india_probs.loc['Top','Bot']:.1%}")

# Save
india_probs.to_csv(f"{FINDINGS_DIR}/04_transition_matrix_india.csv")
us_probs.to_csv(f"{FINDINGS_DIR}/04_transition_matrix_us.csv")
pd.DataFrame([
    {"market": "India", "P_top_to_top": india_probs.loc["Top","Top"],
     "P_top_to_mid": india_probs.loc["Top","Mid"],
     "P_top_to_bot": india_probs.loc["Top","Bot"],
     "P_bot_to_top": india_probs.loc["Bot","Top"]},
    {"market": "US",    "P_top_to_top": us_probs.loc["Top","Top"],
     "P_top_to_mid": us_probs.loc["Top","Mid"],
     "P_top_to_bot": us_probs.loc["Top","Bot"],
     "P_bot_to_top": us_probs.loc["Bot","Top"]},
]).to_csv(f"{FINDINGS_DIR}/04_transition_summary.csv", index=False)
print("✓ Test 4 complete\n")

# ══════════════════════════════════════════════════════════════════════════════
# VISUALISATIONS
# ══════════════════════════════════════════════════════════════════════════════

print("=" * 60)
print("VISUALISATIONS")
print("=" * 60)

plt.rcParams.update({
    "figure.facecolor": "#0d1117", "axes.facecolor":  "#0d1117",
    "axes.edgecolor":   "#30363d", "axes.labelcolor": "#c9d1d9",
    "text.color":       "#c9d1d9", "xtick.color":     "#8b949e",
    "ytick.color":      "#8b949e", "grid.color":      "#21262d",
    "grid.linewidth":   0.5,       "font.family":     "monospace",
    "axes.spines.top":  False,     "axes.spines.right": False,
})

ACCENT  = "#58a6ff"
ACCENT2 = "#f78166"
ACCENT3 = "#3fb950"
MUTED   = "#8b949e"

# Fig 1 — Leadership Heatmap
rank_matrix = panel[[f"{s}_rank" for s in INDIA_SECTORS]].copy()
rank_matrix.columns = INDIA_SECTORS

fig, ax = plt.subplots(figsize=(14, 5))
sns.heatmap((9 - rank_matrix).T, ax=ax, cmap="YlOrRd",
            linewidths=0.3, linecolor="#0d1117",
            cbar_kws={"label": "← Laggard   Leader →", "shrink": 0.6},
            xticklabels=False)

regime_changes = panel[panel["regime"] != panel["regime"].shift(1)].index[1:]
for rc in regime_changes:
    ax.axvline(panel.index.get_loc(rc), color=MUTED,
               linewidth=1.2, linestyle="--", alpha=0.7)

year_ticks  = [i for i, d in enumerate(panel.index) if d.month <= 3]
ax.set_xticks(year_ticks)
ax.set_xticklabels([panel.index[i].year for i in year_ticks], fontsize=8)
ax.set_title("Nifty Sector Leadership — Quarterly Rank (2012–2026)",
             fontsize=12, pad=12, color="#e6edf3", fontweight="bold")
ax.tick_params(axis="y", labelsize=9)

for reg, label in [("pre_covid","Pre-COVID"),("covid_recovery","COVID"),("rate_hike","Rate Hike")]:
    subset = panel[panel["regime"] == reg]
    if subset.empty: continue
    mid_idx = panel.index.get_loc(subset.index[len(subset)//2])
    ax.text(mid_idx, -0.8, label, ha="center", va="top", color=MUTED, fontsize=7.5)

plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/fig1_leadership_heatmap.png",
            dpi=150, bbox_inches="tight", facecolor="#0d1117")
plt.close()
print("  ✓ Fig 1 — Leadership heatmap")

# Fig 2 — Persistence Ratio
persist_df = pd.read_csv(f"{FINDINGS_DIR}/01_leadership_persistence.csv")
regime_df  = pd.read_csv(f"{FINDINGS_DIR}/01_persistence_by_regime.csv")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax = axes[0]
observed = persist_df["top1_persistence"].values[0]
bars = ax.bar(["Random\nBaseline", "Observed"], [0.125, observed],
              color=[MUTED, ACCENT2 if observed < 0.125 else ACCENT],
              width=0.4, edgecolor="none")
ax.axhline(0.125, color=MUTED, linewidth=1, linestyle="--", alpha=0.5)
ax.set_title("Top-1 Persistence Ratio", fontsize=11, color="#e6edf3", fontweight="bold")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylim(0, 0.35)
for bar, val in zip(bars, [0.125, observed]):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
            f"{val:.1%}", ha="center", fontsize=10, color="#e6edf3")
ax.text(0.5, 0.92,
        f"Verdict: {'Mean-Reverting' if observed < 0.125 else 'Momentum'}",
        transform=ax.transAxes, ha="center", fontsize=9,
        color=ACCENT2 if observed < 0.125 else ACCENT3)

ax = axes[1]
regime_names = {"pre_covid": "Pre-COVID", "covid_recovery": "COVID Recovery",
                "rate_hike": "Rate Hike"}
colors_map   = {"pre_covid": ACCENT, "covid_recovery": ACCENT3, "rate_hike": ACCENT2}
x = np.arange(len(regime_df))
bars = ax.bar(x, regime_df["persistence_ratio"],
              color=[colors_map.get(r, MUTED) for r in regime_df["regime"]],
              width=0.5, edgecolor="none")
ax.axhline(0.125, color=MUTED, linewidth=1, linestyle="--", alpha=0.7, label="Random (12.5%)")
ax.set_xticks(x)
ax.set_xticklabels([regime_names.get(r, r) for r in regime_df["regime"]], fontsize=9)
ax.set_title("Persistence by Regime", fontsize=11, color="#e6edf3", fontweight="bold")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylim(0, 0.4)
ax.legend(fontsize=8)
for bar, val in zip(bars, regime_df["persistence_ratio"]):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
            f"{val:.1%}", ha="center", fontsize=9, color="#e6edf3")

plt.suptitle("Leadership Persistence — India Nifty Sectors",
             fontsize=13, color="#e6edf3", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/fig2_persistence_ratio.png",
            dpi=150, bbox_inches="tight", facecolor="#0d1117")
plt.close()
print("  ✓ Fig 2 — Persistence ratio")

# Fig 3 — Spearman Autocorrelation
autocorr_df = pd.read_csv(f"{FINDINGS_DIR}/02_rank_autocorrelation.csv")
fig, ax = plt.subplots(figsize=(12, 5))
x     = np.arange(len(INDIA_SECTORS))
width = 0.25
for i, (lag, color) in enumerate(zip([1, 2, 3], [ACCENT, ACCENT3, ACCENT2])):
    rhos  = autocorr_df[f"rho_lag{lag}"].values
    pvals = autocorr_df[f"pval_lag{lag}"].values
    ax.bar(x + i*width, rhos, width, label=f"Lag {lag}",
           color=color, alpha=0.85, edgecolor="none")
    for j, (rho, pval) in enumerate(zip(rhos, pvals)):
        if pval < 0.05:
            ax.text(x[j] + i*width, rho + (0.01 if rho >= 0 else -0.04),
                    "*", ha="center", fontsize=10, color="#e6edf3")

ax.axhline(0, color=MUTED, linewidth=1, alpha=0.5)
ax.set_xticks(x + width)
ax.set_xticklabels(INDIA_SECTORS, fontsize=9)
ax.set_ylabel("Spearman ρ")
ax.set_title("Rank Autocorrelation by Sector and Lag\n(negative = mean-reverting, * = p<0.05)",
             fontsize=11, color="#e6edf3", fontweight="bold")
ax.legend(fontsize=9)
ax.set_ylim(-0.7, 0.7)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/fig3_autocorrelation.png",
            dpi=150, bbox_inches="tight", facecolor="#0d1117")
plt.close()
print("  ✓ Fig 3 — Autocorrelation")

# Fig 4 — India vs US
comparison = pd.read_csv(f"{FINDINGS_DIR}/03_india_vs_us.csv")
bootstrap  = pd.read_csv(f"{FINDINGS_DIR}/03_bootstrap_test.csv")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
bar_colors = [ACCENT, ACCENT2]

ax = axes[0]
bars = ax.bar(comparison["market"], comparison["persistence_ratio"],
              color=bar_colors, width=0.4, edgecolor="none")
ax.axhline(0.125, color=MUTED, linewidth=1, linestyle="--",
           alpha=0.7, label="Random (12.5%)")
ax.set_title("Persistence Ratio: India vs US", fontsize=11,
             color="#e6edf3", fontweight="bold")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylim(0, 0.35)
ax.legend(fontsize=8)
for bar, val in zip(bars, comparison["persistence_ratio"]):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.005,
            f"{val:.1%}", ha="center", fontsize=11, color="#e6edf3")
boot_sig = bootstrap["significant"].values[0]
ax.text(0.5, 0.90,
        f"Bootstrap p = {bootstrap['bootstrap_pval'].values[0]:.3f} "
        f"({'✓ sig' if boot_sig else '✗ not sig'})",
        transform=ax.transAxes, ha="center", fontsize=9, color=MUTED)

ax = axes[1]
bars = ax.bar(comparison["market"], comparison["spearman_rho_lag1"],
              color=bar_colors, width=0.4, edgecolor="none")
ax.axhline(0, color=MUTED, linewidth=1, alpha=0.5)
ax.set_title("Spearman ρ at Lag 1: India vs US", fontsize=11,
             color="#e6edf3", fontweight="bold")
ax.set_ylabel("Spearman ρ")
ax.set_ylim(-0.5, 0.5)
for bar, rho, pval in zip(bars, comparison["spearman_rho_lag1"],
                           comparison["spearman_pval"]):
    ax.text(bar.get_x() + bar.get_width()/2,
            rho + (0.01 if rho >= 0 else -0.05),
            f"{rho:+.3f}{'*' if pval < 0.05 else ''}",
            ha="center", fontsize=11, color="#e6edf3")

plt.suptitle("India vs US Sector Rotation Dynamics",
             fontsize=13, color="#e6edf3", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/fig4_india_vs_us.png",
            dpi=150, bbox_inches="tight", facecolor="#0d1117")
plt.close()
print("  ✓ Fig 4 — India vs US")

# Fig 5 — Transition Matrix
india_tm = pd.read_csv(f"{FINDINGS_DIR}/04_transition_matrix_india.csv", index_col=0)
us_tm    = pd.read_csv(f"{FINDINGS_DIR}/04_transition_matrix_us.csv",    index_col=0)
order    = ["Top", "Mid", "Bot"]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, tm, title in zip(axes, [india_tm, us_tm], ["India", "US"]):
    tm = tm.reindex(index=order, columns=order)
    sns.heatmap(tm, ax=ax, annot=True, fmt=".0%", cmap="RdYlGn",
                vmin=0, vmax=0.6, linewidths=0.5, linecolor="#0d1117",
                cbar_kws={"shrink": 0.8},
                annot_kws={"size": 12, "color": "#0d1117"})
    ax.set_title(f"{title} — Sector Rank Transition Matrix",
                 fontsize=11, color="#e6edf3", fontweight="bold")
    ax.set_xlabel("Next Quarter Tercile", color="#c9d1d9")
    ax.set_ylabel("Current Quarter Tercile", color="#c9d1d9")

plt.suptitle("Probability of Tercile Transition (Q → Q+1)",
             fontsize=13, color="#e6edf3", fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{CHARTS_DIR}/fig5_transition_matrix.png",
            dpi=150, bbox_inches="tight", facecolor="#0d1117")
plt.close()
print("  ✓ Fig 5 — Transition matrix")

print("\n" + "=" * 60)
print("ALL DONE")
print(f"  CSVs   → {FINDINGS_DIR}/")
print(f"  Charts → {CHARTS_DIR}/")
print("=" * 60)