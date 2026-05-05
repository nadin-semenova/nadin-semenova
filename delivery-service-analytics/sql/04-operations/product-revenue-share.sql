--- FILE: product_revenue_share.sql ---
-- Ranks all products by total revenue over the full observation period
-- and calculates each product's percentage share of overall revenue.
-- Products with a rounded share below 0.5% are grouped into 'Other'
-- to avoid cluttering visualisations with long-tail items.
-- Technique: SUM(revenue) OVER() without PARTITION BY gives the grand total
-- in every row, allowing per-row share calculation in a single pass.
-- Cancelled orders are excluded via NOT IN subquery on user_actions.


SELECT product_name,
       sum (revenue) as revenue,
       sum (share_in_revenue) as share_in_revenue
FROM   (SELECT case when round(100*revenue::decimal/sum(revenue) OVER(),
                               2) < 0.5 then 'Other'
                    else name end as product_name,
               revenue,
               round (100*revenue::decimal/sum (revenue) OVER (), 2) as share_in_revenue
        FROM   (SELECT name,
                       sum(price) as revenue
                FROM   (SELECT order_id,
                               date(creation_time),
                               unnest(product_ids) as product_id
                        FROM   orders
                        WHERE  order_id not in (SELECT order_id
                                                FROM   user_actions
                                                WHERE  action = 'cancel_order'))t1 join products using (product_id)
                GROUP BY name)t1) as t4
GROUP BY product_name
ORDER BY revenue desc;
