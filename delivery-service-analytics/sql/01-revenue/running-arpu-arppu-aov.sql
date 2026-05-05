-- Calculates cumulative (running) versions of ARPU, ARPPU, and AOV.
-- For each day, uses all revenue and all users accumulated since day 1.
-- Shows how average monetisation metrics stabilise as the user base grows.
-- Demonstrates SUM OVER (ORDER BY date) for rolling aggregation.

with not_cancel_order as (SELECT date(creation_time) as date,
                                 unnest(product_ids) as prod_id
                          FROM   orders
                          WHERE  order_id not in (SELECT order_id
                                                  FROM   user_actions
                                                  WHERE  action = 'cancel_order')), pay_user_num as(SELECT date,
                                                         count(distinct user_id) as pay_user
                                                  FROM   (SELECT user_id,
                                                                 min(time)::date as date
                                                          FROM   user_actions
                                                          WHERE  order_id not in (SELECT order_id
                                                                                  FROM   user_actions
                                                                                  WHERE  action = 'cancel_order')
                                                          GROUP BY user_id) t1
                                                  GROUP BY date
                                                  ORDER BY date), user_order_not_cancel as (SELECT c.date,
                                                 c.num_order,
                                                 d.pay_user
                                          FROM   (SELECT date(time)as date,
                                                         count(distinct order_id) as num_order
                                                  FROM   user_actions
                                                  WHERE  order_id not in (SELECT order_id
                                                                          FROM   user_actions
                                                                          WHERE  action = 'cancel_order')
                                                  GROUP BY date
                                                  ORDER BY date) c join pay_user_num d using(date)), all_user_num as (SELECT a.date,
                                                                           a.all_users,
                                                                           b.pay_user,
                                                                           b.num_order,
                                                                           sum(a.all_users) OVER(ORDER BY date) as all_user_dif,
                                                                           sum(b.pay_user) OVER(ORDER BY date) as pay_user_dif,
                                                                           sum(b.num_order) OVER(ORDER BY date) as order_dif
                                                                    FROM   (SELECT date,
                                                                                   count(distinct user_id) as all_users
                                                                            FROM   (SELECT user_id,
                                                                                           min(time)::date as date
                                                                                    FROM   user_actions
                                                                                    GROUP BY user_id) t1
                                                                            GROUP BY date
                                                                            ORDER BY date) a join user_order_not_cancel b using(date)), rev_sum as (SELECT a.date,
                                                                               sum(b.price) as revenue
                                                                        FROM   not_cancel_order a join products b
                                                                                ON a.prod_id = b.product_id
                                                                        GROUP BY date
                                                                        ORDER BY date)
SELECT a.date,
       round(((sum(a.revenue) OVER(ORDER BY date))::decimal/all_user_dif),
             2) as running_arpu,
       round(((sum(a.revenue) OVER(ORDER BY date))::decimal/pay_user_dif),
             2) as running_arppu,
       round(((sum(a.revenue) OVER(ORDER BY date))::decimal/order_dif), 2) as running_aov
FROM   rev_sum a join all_user_num b using(date)
