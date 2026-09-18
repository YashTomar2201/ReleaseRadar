# Google Pay — Product Health Brief

*Trailing 30-day avg rating: **4.15★** · Negative share: **17.5%** (worst of the 3 tracked apps)*

**Bottom line:** Google Pay has both the highest `app_performance` complaint rate (double PhonePe's) and is a net loser in stated brand switching — the two are directly connected in the review evidence.

## What changed
- Google Pay has the longest data history of the 3 apps (~16.5 months) but is not the focus app for the causal release-impact analysis in this project (PhonePe is) — no release-level significance testing was run for Google Pay specifically.
- Google Pay **is** the app behind this project's one independently-confirmed early-warning validation case: a real UPI-wide outage on 2025-08-07 (~19:45 IST, NPCI-attributed to bank-side technical issues). The detector correctly flagged the affected time window, though with a 3-hour detection bin (needed given Google Pay's lower review volume relative to PhonePe) the realistic alert would have lagged the public report by ~45 minutes rather than beaten it.

## Competitive position
- **Net loser to PhonePe:** -0.94 mentions/10k reviews (PhonePe gains this).
- **Roughly balanced with Paytm:** a small net gain (+0.12/10k) — not clearly distinguishable from noise given overlapping confidence intervals.
- **Additional one-directional outflow** to BHIM (18 mentions), Amazon Pay (11), CRED (3), Navi (2), Supermoney (1) with no offsetting inbound flow observed from any of them.
- Google Pay shows the **most total outflow mentions of the 3 tracked apps** — consistent with its higher negative-share and 1-star rate found in the EDA phase of this project.

## Recommended priorities (last 90 days, RICE-ranked)

| Rank | Issue | Prevalence | Rating lift if fixed | Churn exposure | Stability* |
|---|---|---|---|---|---|
| 1 | `app_performance` | **8.4%** | +0.111★ | 1.33% | **99%** |
| 2 | `rewards_cashback` | 4.6% | +0.015★ | 1.11% | 86% |
| 3 | `payment_failure` | 6.8% | +0.048★ | 0.62% | 68% |
| 4 | `fraud_security` | 4.7% | +0.038★ | 0.71% | 27% |
| 5 | `ads_spam` | 1.7% | +0.017★ | 0.43% | 17% |

*\*Top-3 stability under ±50% effort-estimate uncertainty (1,000 Monte Carlo runs).*

**`app_performance` prevalence (8.4%) is double PhonePe's (4.2%)** — this is a genuine severity signal independent of any reach-scaling effect (both figures are plain percentages of each app's own reviews), not an artifact of Google Pay's larger download base.

## Evidence
> "whenever I try to open correctly the app it's not respond and not open" (`app_performance`, 1★)

> "sound box replacement delay so many times. google pay is very slow" (`app_performance`, 1★)

## Caveats
- RICE "Reach" uses Play Store download counts (1B+) as an MAU proxy — Google Pay's RICE scores are higher than PhonePe's/Paytm's *partly* because of its 2x larger download count, not solely issue severity. Compare `app_performance`'s **prevalence** (8.4% vs. 4.2%), not its RICE score, when benchmarking severity against PhonePe.
- Switching counts are a validated lower bound (rule-based classifier).
