-- Tracks daily and cumulative counts of new users and couriers,
-- plus day-over-day growth rates for all four metrics in %.
-- Insight: new user growth peaked at +519% on Day 2 then decelerated
-- sharply to low single digits by Sep 8 — signal that organic acquisition
-- is saturating. Uses four LAG() calls to calculate growth rates in one query.

with sub1 as (SELECT date,
                     count(user_id) as new_users
              FROM   (SELECT user_id,
                             min(time)::date as date
                      FROM   user_actions
                      GROUP BY user_id) t1
              GROUP BY date) , sub2 as (SELECT date,
                                 count(courier_id) as new_couriers
                          FROM   (SELECT courier_id,
                                         min(time)::date as date
                                  FROM   courier_actions
                                  GROUP BY courier_id) t2
                          GROUP BY date), sub3 as (SELECT date,
                                new_users,
                                new_couriers,
                                sum(new_users) OVER(ORDER BY date)::int as total_users,
                                sum(new_couriers) OVER(ORDER BY date)::int as total_couriers
                         FROM   (SELECT sub1.date,
                                        sub1.new_users,
                                        sub2.new_couriers
                                 FROM   sub1 join sub2 using(date))t3
                         ORDER BY date)
SELECT date,
       new_users,
       new_couriers,
       total_users,
       total_couriers,
       round((100.00*(new_users - lag (new_users, 1) OVER(ORDER BY date))/lag (new_users, 1) OVER(ORDER BY date)),
             2) as new_users_change,
       round((100.00*(new_couriers- lag (new_couriers, 1) OVER(ORDER BY date))/lag (new_couriers, 1)OVER(ORDER BY date)),
             2) as new_couriers_change,
       round((100.00*(total_users - lag (total_users, 1) OVER(ORDER BY date))/lag (total_users, 1) OVER(ORDER BY date)),
             2) as total_users_growth,
       round((100.00*(total_couriers- lag (total_couriers, 1) OVER(ORDER BY date))/lag (total_couriers, 1)OVER(ORDER BY date)),
             2) as total_couriers_growth
FROM   sub3
