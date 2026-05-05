-- Calculates three revenue-per-user metrics for each day:
--   ARPU  — revenue per all active users
--   ARPPU — revenue per paying users only (placed ≥1 non-cancelled order)
--   AOV   — average order value (revenue / number of orders)
-- Paying users are counted per day, not cumulatively.

with not_cancel_order as (SELECT date(creation_time) as date,
                                 unnest(product_ids) as prod_id
                          FROM   orders
                          WHERE  order_id not in (SELECT order_id
                                                  FROM   user_actions
                                                  WHERE  action = 'cancel_order')), user_num as (SELECT date(time) as date,
                                                      count(distinct order_id) filter (WHERE order_id not in (SELECT order_id
                                                                                                       FROM   user_actions
                                                                                                       WHERE  action = 'cancel_order')) as num_order, count(distinct user_id) filter (
                                               WHERE  order_id not in (SELECT order_id
                                                                       FROM   user_actions
                                                                       WHERE  action = 'cancel_order')) as pay_user, count(distinct user_id) as all_users
                                               FROM   user_actions
                                               GROUP BY date
                                               ORDER BY date), rev_sum as (SELECT a.date,
                                   sum(b.price) as revenue
                            FROM   not_cancel_order a join products b
                                    ON a.prod_id = b.product_id
                            GROUP BY date
                            ORDER BY date)
SELECT a.date,
       round((a.revenue::decimal/b.all_users), 2) as arpu,
       round((a.revenue::decimal/b.pay_user), 2) as arppu,
       round((a.revenue::decimal/b.num_order), 2) as aov
FROM   rev_sum a join user_num b using(date)
