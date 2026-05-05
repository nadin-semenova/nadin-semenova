-- Cohort retention analysis: groups users by their first action date
-- and tracks what share of each cohort returns on each subsequent day.
-- Day 0 = 1.0 (100%) for all cohorts by definition.
-- Uses a window function to find each user's first action date,
-- then calculates retention as users_on_day_N / cohort_size.

SELECT date_trunc('month', start_date)::date as start_month,
       start_date,
       date - start_date as day_number,
       round(count(distinct user_id)::decimal/max(count(distinct user_id)) OVER (PARTITION BY start_date),
             2) as retention
FROM   (SELECT user_id,
               min(time::date) OVER (PARTITION BY user_id) as start_date,
               time::date as date
        FROM   user_actions) t1
GROUP BY date, start_date
ORDER BY start_date, day_number
