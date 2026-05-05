-- For each day calculates the share of paying users who placed
-- exactly one order vs. two or more orders.
-- Measures daily usage intensity, not long-term loyalty.
-- Typical pattern: ~65–78% of paying users place only one order per day.

with sub1 as (SELECT date(time) as date,
                     count(distinct user_id) as paying_users
              FROM   user_actions
              WHERE  order_id not in (SELECT order_id
                                      FROM   user_actions
                                      WHERE  action = 'cancel_order')
              GROUP BY date(time)
              ORDER BY date), sub2 as(SELECT date,
                               count(paying_users_one) as paying_users_one_all
                        FROM   (SELECT date(time) as date,
                                       user_id,
                                       count(order_id) as paying_users_one
                                FROM   user_actions
                                WHERE  order_id not in (SELECT order_id
                                                        FROM   user_actions
                                                        WHERE  action = 'cancel_order')
                                GROUP BY date(time), user_id having count(order_id) = 1)t1
                        GROUP BY date
                        ORDER BY date)
SELECT date,
       round(100.0*paying_users_one_all/ paying_users, 2) as single_order_users_share,
       100 -round(100.0*paying_users_one_all/ paying_users,
                  2) as several_orders_users_share
FROM   (SELECT sub1.date,
               sub1.paying_users,
               sub2.paying_users_one_all
        FROM   sub1 join sub2 using(date))t3
