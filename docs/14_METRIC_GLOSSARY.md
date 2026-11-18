# 14 — KPI Glossary and Interpretation

| Name | Formula | Grain/Horizon | Caveat |
| --- | --- | --- | --- |
| Eligible leads | Count of unique lead IDs | lead month, market/channel | Experimental denominator includes nonconverters |
| Acquisitions | Number of converting leads / unique customer IDs | lead-month cohort | Conversion within 30 days |
| Conversion rate | Acquisitions / eligible leads | eligible lead cohort | Not incremental lift unless randomized comparison |
| Actual campaign spend | Sum actual USD spend | campaign market/channel/month | Not transaction revenue, never multiply through joins |
| Investment utilization | Actual campaign spend / planned spend | campaign/month | Can exceed 100%; planned zero => N/A |
| Offer payouts | Sum observed paid welcome incentives | acquired treatment leads | Separate from transaction costs and marketing spend |
| Contribution margin | Gross transaction revenue - direct variable costs - servicing costs | selected mature cohort horizon | Can be negative; revenue != profit |
| Acquisition investment | Campaign spend + paid welcome incentives | aligned cohort | Don't double count |
| CAC | Acquisition investment / new customers | acquisition cohort | N/A for zero conversions; includes both cost types |
| Cohort ROI | (contribution margin - campaign spend - payouts) / (campaign spend + payouts) | mature acquisition cohort, declared horizon | Not randomized incremental ROI; spend/outcome horizons must align |
| 180d customer contribution | Contribution 0–180d after acquisition | mature acquired cohort | Historical, not all-time LTV |
| Forward customer value | Discounted contribution days 91–270 after acquisition | 90-day model checkpoint | Predictive 180-day forward proxy, not full lifetime LTV |
| RCT net ITT/lead | Mean(net contribution 0–180d after lead, treatment) - control mean | randomly assigned eligible leads | Includes zero nonconverters; subtracts actual incentives |
| Predicted new customers | Sum a_i*(1-exp(-b_i/s_i)) | hypothetical spend scenario | Planning assumption, no causal claim |
| Optimization projected ROI | Expected scenario profit / total scenario budget plus incentive payouts if separately included | prospective simulated planning horizon | Not observed, do not compare to historic ROI without caveats |

## Important resolution for optimizer ROI
Budget `b_i` includes campaign spend **only** and expected incentive payouts `q_i * customers_i(b_i)` are additional costs. Therefore report:
- Projected contribution = Σ customers_i * v_i
- Projected offer payouts = Σ customers_i * q_i
- Planned campaign budget = Σ b_i
- Projected net profit = contribution - payouts - campaign budget
- Projected acquisition investment = campaign budget + payouts
- Projected ROI = projected net profit / projected acquisition investment if denominator positive.
If the user changes a budget slider, the equality constraint applies to campaign spend, not total incentive-inclusive acquisition investment. Make this visible in the UI.
