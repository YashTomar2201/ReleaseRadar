# PhonePe — Product Health Brief

*Trailing 30-day avg rating: **4.43★** · Negative share: **9.7%** (best of the 3 tracked apps)*

**Bottom line:** PhonePe is in the strongest position of the three apps on both rating and switching, but its lead is fragile — it rests on the same weakness (app performance) that's also its own #1 internal fix priority.

## What changed
- 15 PhonePe releases tracked over the ~6-month data window; **12 had enough pre/post data to test causally, and 0 were significant** after correcting for multiple testing (Benjamini-Hochberg, q<0.10).
- The one release that looked like a real finding (`26.05.08.0`, health score 4.6) was investigated further and traced to a parallel-trends issue — both competitor apps moved during that comparison window while PhonePe itself stayed flat. Not a real release effect.
- **Practical read: no evidence any recent release has hurt or helped sentiment in a statistically defensible way.** Release quality has been stable.

## Competitive position
- PhonePe is the **net beneficiary** of stated brand switching among the 3 tracked apps: **+0.94 mentions/10k reviews** net from Google Pay, **+1.66/10k** net from Paytm.
- **Both inbound flows cite the same reason: app performance complaints on the app being left.** This is PhonePe's biggest strategic risk — its competitive edge is being won on a dimension (reliability) where PhonePe itself also has real, RICE-ranked issues.

## Recommended priorities (last 90 days, RICE-ranked)

| Rank | Issue | Prevalence | Rating lift if fixed | Churn exposure | Stability* |
|---|---|---|---|---|---|
| 1 | `app_performance` | 4.2% | +0.055★ | 0.43% | **100%** |
| 2 | `rewards_cashback` | 2.9% | +0.010★ | 0.42% | 51% |
| 3 | `fees_charges` | 1.8% | +0.008★ | 0.15% | 46% |
| 4 | `ui_ux` ⚠️ | 2.2% | +0.008★ | 0.25% | 41% |
| 5 | `payment_failure` | 3.2% | +0.022★ | 0.27% | 31% |

*\*Top-3 stability under ±50% effort-estimate uncertainty (1,000 Monte Carlo runs). `app_performance` is effectively locked in at #1 regardless of how effort is estimated; ranks below it are genuinely sensitive to the effort assumption and shouldn't be read as a precise order.*

⚠️ `ui_ux` has an unusual positive rating correlation — it's frequently paired with praise (constructive feature requests from happy users, not pure complaints). Needs a manual read before treating it as a standard fix priority.

## Evidence
> "not working" (`app_performance`, 1★)

> "i got many problems with technical issue Im in urgent money was not sending in phone showing to wait 72 hours" (`app_performance`, 1★)

## Caveats
- Rating-lift and churn-exposure figures are drawn from the reviewing population, not all users.
- RICE "Reach" uses Play Store download counts (500M+) as an MAU proxy — valid for ranking PhonePe's *own* issues against each other, not for comparing PhonePe's RICE scores directly against Google Pay's or Paytm's (different download-count scale).
- Switching counts are a validated lower bound (rule-based classifier, ~85-95% precision, incomplete recall — particularly for Hindi/Hinglish).
