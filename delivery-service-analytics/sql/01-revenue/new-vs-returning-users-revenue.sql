with sub1 as (SELECT date,
                     sum(price) as revenue
              FROM   (SELECT date(creation_time) as date,
                             unnest(product_ids) as product_id
                      FROM   orders
                      WHERE  order_id not in (SELECT order_id
                                              FROM   user_actions
                                              WHERE  action = 'cancel_order'))t1 join products using(product_id)
              GROUP BY date
              ORDER BY date), sub2 as (SELECT t1.date,
                                t1.user_id,
                                coalesce(t2.order_id, 0)::int as order_id
                         FROM   (SELECT min(date(time)) as date,
                                        user_id
                                 FROM   user_actions
                                 GROUP BY user_id)t1 join user_actions as t2
                                 ON date(t2.time) = t1.date and
                                    t1.user_id = t2.user_id), sub3 as (SELECT date,
                                          coalesce(sum(price), 0) as new_users_revenue
                                   FROM   (SELECT date,
                                                  order_id,
                                                  unnest(product_ids) as product_id
                                           FROM   sub2 join orders using(order_id)
                                           WHERE  order_id not in (SELECT order_id
                                                                   FROM   user_actions
                                                                   WHERE  action = 'cancel_order'))t3 join products using(product_id)
                                   GROUP BY date)
SELECT date,
       revenue,
       new_users_revenue,
       round(100*new_users_revenue/revenue::decimal, 2) as new_users_revenue_share,
       100 - round(100*new_users_revenue/revenue::decimal, 2) as old_users_revenue_share
FROM   sub3 join sub1 using(date)
ORDER BY date
