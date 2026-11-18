CREATE OR REPLACE TABLE mart_customer_checkpoint_90d AS
WITH events AS (
 SELECT c.*, c.acquisition_date + INTERVAL 90 DAY AS checkpoint_date,
        l.site_visits_pre_lead, l.engagement_score_pre_lead,
        date_diff('day', l.lead_date, c.acquisition_date) AS conversion_delay_days,
        month(c.acquisition_date) AS acquisition_month,
        date_trunc('month', c.acquisition_date) AS acquisition_cohort,
        c.acquisition_date + INTERVAL 270 DAY <= meta.observation_end AS mature_270d,
        t.txn_date, t.gross_revenue_usd, t.contribution_usd
 FROM customers c JOIN leads l USING(lead_id) CROSS JOIN metadata meta
 LEFT JOIN transactions t ON t.customer_id = c.customer_id
)
SELECT customer_id, lead_id, acquisition_date, checkpoint_date, market, channel,
       synthetic_segment, offer_arm, site_visits_pre_lead, engagement_score_pre_lead,
       conversion_delay_days, acquisition_month, acquisition_cohort, mature_270d,
       count(txn_date) FILTER(WHERE txn_date <= checkpoint_date) AS txn_count_90d,
       coalesce(sum(gross_revenue_usd) FILTER(WHERE txn_date <= checkpoint_date),0) AS revenue_90d_usd,
       coalesce(sum(contribution_usd) FILTER(WHERE txn_date <= checkpoint_date),0) AS contribution_90d_usd,
       coalesce(avg(gross_revenue_usd) FILTER(WHERE txn_date <= checkpoint_date),0) AS avg_transaction_90d_usd,
       count(DISTINCT date_trunc('month',txn_date)) FILTER(WHERE txn_date <= checkpoint_date) AS active_months_90d,
       coalesce(date_diff('day',max(txn_date) FILTER(WHERE txn_date <= checkpoint_date), checkpoint_date),91) AS recency_days_90d,
       max(txn_date) FILTER(WHERE txn_date <= checkpoint_date) AS feature_max_event_date,
       min(txn_date) FILTER(WHERE txn_date > checkpoint_date AND txn_date <= checkpoint_date + INTERVAL 180 DAY) AS label_min_event_date,
       max(txn_date) FILTER(WHERE txn_date > checkpoint_date AND txn_date <= checkpoint_date + INTERVAL 180 DAY) AS label_max_event_date,
       CASE WHEN mature_270d THEN coalesce(sum(contribution_usd / pow(1+meta.annual_discount_rate,
          date_diff('day',checkpoint_date,txn_date)/365.25)) FILTER(
          WHERE txn_date > checkpoint_date AND txn_date <= checkpoint_date + INTERVAL 180 DAY),0) END
          AS target_future_contribution_180d_usd
FROM events CROSS JOIN metadata meta
GROUP BY customer_id,lead_id,acquisition_date,checkpoint_date,market,channel,
 synthetic_segment,offer_arm,site_visits_pre_lead,engagement_score_pre_lead,
 conversion_delay_days,acquisition_month,acquisition_cohort,mature_270d;

CREATE OR REPLACE TABLE customer_cohort_value AS
SELECT c.customer_id, c.lead_id,
 coalesce(sum(t.contribution_usd) FILTER(WHERE t.txn_date <= c.acquisition_date + INTERVAL 180 DAY),0) AS contribution_180d_usd,
 count(t.transaction_id) FILTER(WHERE t.txn_date BETWEEN c.acquisition_date + INTERVAL 151 DAY AND c.acquisition_date + INTERVAL 180 DAY) > 0 AS active_days_151_180
FROM customers c LEFT JOIN transactions t USING(customer_id) GROUP BY c.customer_id,c.lead_id;

CREATE OR REPLACE TABLE customer_cohort_payout AS
SELECT c.lead_id, coalesce(sum(p.incentive_cost_usd) FILTER(
 WHERE p.payout_date <= c.acquisition_date + INTERVAL 180 DAY),0) AS payout_180d_usd
FROM customers c LEFT JOIN offer_payouts p USING(lead_id) GROUP BY c.lead_id;
