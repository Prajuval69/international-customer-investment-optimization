# 06 — Welcome Offer Randomized Experiment

## Design
The **unit of randomization is the eligible lead**, not the converted customer. `offer_arm` assignment is created before conversion within market × channel × month strata. Treatment leads are offered the synthetic welcome offer; control leads are not. The primary result is **intent-to-treat (ITT)** among all eligible leads, including those who do not convert.

## Primary outcome
`net_contribution_per_eligible_lead_180d = sum(transaction contribution earned in days 0–180 following the lead_date) - actual incentive payout in days 0–180 following lead_date`. For an unconverted lead the value is zero. Costs `gross - direct - service` are already deducted from transaction margin. Exclude campaign spend from arm comparison if common to both arms and allocated independently of assignment; if reporting total campaign economics, separately state campaign costs.

**Effect estimate:** Difference in mean net contribution/eligible lead between treatment and control: `mean(Y | treatment) - mean(Y | control)`. Also show conversion-rate lift in percentage points and incentive cost per randomized lead. This is ITT, not effect among converters. Never condition away nonconverters for primary inference.

## Inference
- Overall ITT, plus market-level and channel-level subgroup views.
- Stratification-adjusted estimator preferred: compute arm mean differences within prespecified strata and weight using all stratum lead shares. A plain overall difference is acceptable as a cross-check if treatment counts are balanced.
- Use independently randomized leads as independent experimental units; Welch two-sided confidence interval/test or stratified bootstrap with fixed seed and >=1000 replicates for overall ITT; document method.
- Include 95% CI, p-value, sample sizes, effect size, baseline rate, and multiple-comparison caution on subgroup exploration. Bootstrap should be fast for small demos; provide method choice.
- Check assignment proportions/balance of pre-treatment variables; small cohorts may have noisy effects.
- No claim of statistical significance if CI contains 0 or p>=0.05; also report practical uncertainty even when statistical significance exists.
- If testing multiple treatment offer variants, avoid multiple unadjusted comparisons or just implement one treatment variant in MVP.

## Core tests
1. Every raw lead is represented once in experiment mart.
2. Unconverted leads have 0 outcome and are included.
3. Control leads have no incentive payouts.
4. Treatment assignment predates conversion and outcomes.
5. Treatment/control cohort follow-up spans the same 180-day lead-based window.
6. Toy datasets with known effects yield correct ITT and sensible interval coverage.
7. Reordering transactions does not change lead-level results; repeat purchases cannot inflate sample size.
8. Strata with only one arm are flagged/excluded from stratified estimator with weight handling documented, not silently treated as valid.
9. Empty/small subgroup panels show explanation and refrain from confident significance claims.

## Outputs
`artifacts/experiment_results.json`, `reports/experiment_summary.csv` (summary only, no raw personal data), bar plot of effects/CIs. Page text explains what randomization can and cannot establish in a fully simulated population.
