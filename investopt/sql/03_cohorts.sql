CREATE OR REPLACE TABLE mart_acquisition_cohort AS
WITH segments AS (
 SELECT l.campaign_id, l.synthetic_segment, count(*) AS lead_count,
 sum(l.converted) AS converted_count,
 sum(coalesce(v.contribution_180d_usd,0)) AS contribution_180d_usd,
 sum(coalesce(p.payout_180d_usd,0)) AS payout_cost_usd,
 count(*) FILTER(WHERE v.active_days_151_180) AS active_days_151_180
 FROM leads l LEFT JOIN customer_cohort_value v USING(lead_id)
 LEFT JOIN customer_cohort_payout p USING(lead_id)
 GROUP BY l.campaign_id,l.synthetic_segment
)
SELECT m.market,m.channel,m.month_start,s.synthetic_segment,m.mature_180d,
 s.lead_count,s.converted_count,
 m.actual_spend_usd*s.lead_count/nullif(m.lead_count,0) AS allocated_spend_usd,
 CASE WHEN m.mature_180d THEN s.contribution_180d_usd END AS contribution_180d_usd,
 CASE WHEN m.mature_180d THEN s.payout_cost_usd END AS payout_cost_usd,
 CASE WHEN m.mature_180d THEN s.active_days_151_180 END AS active_days_151_180
FROM segments s JOIN mart_campaign_month m USING(campaign_id);
