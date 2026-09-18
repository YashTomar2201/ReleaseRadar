# Paytm — Product Health Brief

*Trailing 30-day avg rating: **4.29★** · Negative share: **15.7%**(middle of the 3 tracked apps)*

**Bottom line:** Paytm's #2 issue (customer support) is unique among the three apps — it's the only one where support, not a product feature, is the second-highest RICE priority, and it's a statistically stable one.

## What changed
- Paytm is a competitor/control app in this project's release-impact analysis (PhonePe is the focus app), so no release-level significance testing was run for Paytm specifically.
- Phase 3's exploratory data analysis flagged a genuine **regime shift** in Paytm's negative-review baseline starting ~February-March 2026 — before that point, daily negative share mostly stayed under 15%; after, it regularly spikes above 20-40%. This was flagged as a candidate for deeper investigation but falls outside this project's release-impact scope (which focused on PhonePe releases specifically) — worth a dedicated follow-up.

## Competitive position
- **Net loser to both other tracked apps:** -1.66 mentions/10k reviews to PhonePe, -0.12/10k to Google Pay.
- Paytm receives relatively little *inbound* switching from BHIM/Amazon Pay/CRED/Navi (1 mention each) — its competitive exposure is concentrated in losing to the other two major UPI apps, not smaller players.

## Recommended priorities (last 90 days, RICE-ranked)

| Rank | Issue | Prevalence | Rating lift if fixed | Churn exposure | Stability* |
|---|---|---|---|---|---|
| 1 | `app_performance` | 8.1% | +0.107★ | 1.43% | **100%** |
| 2 | `customer_support` | 3.4% | +0.033★ | 0.30% | **83%** |
| 3 | `rewards_cashback` | 4.0% | +0.013★ | 0.93% | 56% |
| 4 | `ui_ux` ⚠️ | 2.5% | +0.009★ | 0.41% | 23% |
| 5 | `fraud_security` | 3.6% | +0.030★ | 0.82% | 19% |

*\*Top-3 stability under ±50% effort-estimate uncertainty (1,000 Monte Carlo runs). Note `customer_support`'s 83% stability is unusually high for a #2 rank — a more statistically confident second priority than either PhonePe's or Google Pay's #2 issue.*

⚠️ `ui_ux` needs a manual read (see the general caveat in the PhonePe brief) — its positive rating correlation means it's not a standard complaint-driven fix priority.

## Evidence
> "online video kyc mai only one agent h jo kyc karta h 1 hour wait kro fir network problem next agent cut call then again same problem 😔" (`app_performance`, 1★)

> "customer care support very poor" (`customer_support`, 1★)

## Caveats
- RICE "Reach" uses Play Store download counts (500M+) as an MAU proxy — valid for ranking Paytm's own issues, not for cross-app RICE comparison.
- The Feb-Mar 2026 regime shift in negative-review baseline (Phase 3 finding) has not been causally attributed to a specific cause in this project — flagged for follow-up, not resolved here.
- Switching counts are a validated lower bound (rule-based classifier).
