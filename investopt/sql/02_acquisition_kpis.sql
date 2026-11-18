CREATE OR REPLACE TABLE mart_campaign_month AS
WITH outcomes AS (
 SELECT l.campaign_id, count(*) AS lead_count, sum(l.converted) AS converted_count,
 count(*) FILTER(WHERE offer_arm='treatment') AS assigned_treatment_count,
 count(*) FILTER(WHERE offer_arm='control') AS assigned_control_count,
 sum(coalesce(v.contribution_180d_usd,0)) AS contribution_180d_usd,
 sum(coalesce(p.payout_180d_usd,0)) AS payout_cost_usd,
 count(*) FILTER(WHERE v.active_days_151_180) AS active_days_151_180
 FROM leads l LEFT JOIN customer_cohort_value v USING(lead_id)
 LEFT JOIN customer_cohort_payout p USING(lead_id) GROUP BY l.campaign_id
)
SELECT b.*, coalesce(o.lead_count,0) AS lead_count,
 coalesce(o.converted_count,0) AS converted_count,
 coalesce(o.assigned_treatment_count,0) AS assigned_treatment_count,
 coalesce(o.assigned_control_count,0) AS assigned_control_count,
 b.month_start + INTERVAL 1 MONTH - INTERVAL 1 DAY + INTERVAL 210 DAY <= meta.observation_end AS mature_180d,
 CASE WHEN mature_180d THEN coalesce(o.contribution_180d_usd,0) END AS contribution_180d_usd,
 CASE WHEN mature_180d THEN coalesce(o.payout_cost_usd,0) END AS payout_cost_usd,
 CASE WHEN mature_180d THEN coalesce(o.active_days_151_180,0) END AS active_days_151_180,
 b.actual_spend_usd/nullif(b.planned_spend_usd,0) AS utilization,
 o.converted_count/nullif(o.lead_count,0) AS conversion_rate,
 (b.actual_spend_usd+payout_cost_usd)/nullif(o.converted_count,0) AS cac_usd,
 (contribution_180d_usd-b.actual_spend_usd-payout_cost_usd) AS net_profit_usd,
 net_profit_usd/nullif(b.actual_spend_usd+payout_cost_usd,0) AS cohort_roi
FROM campaign_budget b LEFT JOIN outcomes o USING(campaign_id) CROSS JOIN metadata meta;

CREATE OR REPLACE TABLE mart_market_month AS
SELECT market, month_start, bool_and(mature_180d) AS mature_180d,
 sum(lead_count) AS lead_count, sum(converted_count) AS converted_count,
 sum(planned_spend_usd) AS planned_spend_usd, sum(actual_spend_usd) AS actual_spend_usd,
 sum(contribution_180d_usd) AS contribution_180d_usd, sum(payout_cost_usd) AS payout_cost_usd
FROM mart_campaign_month GROUP BY market,month_start;
