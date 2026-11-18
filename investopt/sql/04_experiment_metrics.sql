CREATE OR REPLACE TABLE mart_experiment_lead_outcomes AS
WITH margin AS (
 SELECT l.lead_id, coalesce(sum(t.contribution_usd),0) AS gross_contribution_180d_usd
 FROM leads l LEFT JOIN transactions t ON t.customer_id=l.customer_id
 AND t.txn_date BETWEEN l.lead_date AND l.lead_date + INTERVAL 180 DAY GROUP BY l.lead_id
), incentive AS (
 SELECT l.lead_id, coalesce(sum(p.incentive_cost_usd),0) AS incentive_cost_180d_usd
 FROM leads l LEFT JOIN offer_payouts p ON p.lead_id=l.lead_id
 AND p.payout_date BETWEEN l.lead_date AND l.lead_date + INTERVAL 180 DAY GROUP BY l.lead_id
)
SELECT l.lead_id,l.market,l.channel,l.offer_arm,l.converted,l.lead_date,
 date_trunc('month',l.lead_date) AS lead_month,
 l.site_visits_pre_lead,l.engagement_score_pre_lead,
 l.lead_date+INTERVAL 180 DAY <= meta.observation_end AS mature_180d,
 CASE WHEN mature_180d THEN m.gross_contribution_180d_usd END AS gross_contribution_180d_usd,
 CASE WHEN mature_180d THEN i.incentive_cost_180d_usd END AS incentive_cost_180d_usd,
 gross_contribution_180d_usd-incentive_cost_180d_usd AS net_contribution_180d_usd
FROM leads l JOIN margin m USING(lead_id) JOIN incentive i USING(lead_id) CROSS JOIN metadata meta;
