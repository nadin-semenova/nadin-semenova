-- For each day calculates:
--   total orders, first-ever orders, orders placed by brand-new users
--   (users in their very first day on the platform),
--   and each group's share of total daily orders.
-- Shows the service's growth stage: on Aug 24 ~92% of orders were first orders;
-- by Sep 8 this fell to ~30%, reflecting a maturing and returning user base.

with sub1 as (SELECT date(time) as date,
                     count(distinct order_id) as orders
              FROM   user_actions
              WHERE  order_id not in (SELECT order_id
                                      FROM   user_actions
                                      WHERE  action = 'cancel_order')
              GROUP BY date(time)
              ORDER BY date asc), sub2 as (SELECT date,
                                    count(user_id) as first_orders
                             FROM   (SELECT user_id,
                                            min(time)::date as date
                                     FROM   (SELECT time,
                                                    order_id,
                                                    user_id
                                             FROM   user_actions
                                             WHERE  order_id not in (SELECT order_id
                                                                     FROM   user_actions
                                                                     WHERE  action = 'cancel_order'))t2
                                     GROUP BY user_id
                                     ORDER BY user_id asc) t1
                             GROUP BY date
                             ORDER BY date asc), sub3 as (SELECT e.date,
                                    coalesce(count(order_id), 0)::int as new_users_orders
                             FROM   (SELECT min(date(time)) as date,
                                            user_id
                                     FROM   user_actions
                                     GROUP BY user_id
                                     ORDER BY user_id) as e
                                 LEFT JOIN (SELECT time::date as date,
                                                   user_id,
                                                   order_id
                                            FROM   user_actions
                                            WHERE  order_id not in (SELECT order_id
                                                                    FROM   user_actions
                                                                    WHERE  action = 'cancel_order')) as m
                                     ON e.date = m.date and
                                        e.user_id = m.user_id
                             GROUP BY e.date
                             ORDER BY e.date)
SELECT date,
       orders,
       first_orders,
       new_users_orders,
       round (100*first_orders/orders::decimal, 2) as first_orders_share,
       round (100*new_users_orders/orders::decimal, 2) as new_users_orders_share
FROM   sub1 join sub2 using(date) join sub3 using(date)
ORDER BY date;
