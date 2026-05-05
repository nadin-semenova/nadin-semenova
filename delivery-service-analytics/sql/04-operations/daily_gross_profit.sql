-- daily_gross_profit.sql
-- Calculates daily and cumulative P&L:
--   revenue, costs (fixed + variable), VAT (10% or 20% by product),
--   gross profit, and gross margin %.
--
-- Cost model:
--   Fixed warehouse rent: $1,200/day in Aug, $1,500/day in Sep
--   Assembly fee per order: $1.40 in Aug, $1.15 in Sep
--   Courier pay: $1.50 per delivered order
--   Courier bonus: $4.00 (Aug) / $5.00 (Sep) if courier delivers 5+ orders/day
--
-- VAT rates:
--   10% — basic food staples (see list below)
--   20% — all other products
--


with sub1_revenue as (SELECT data,
                             sum(price) as revenue,
                             sum(tax) as tax
                      FROM   (SELECT data,
                                     order_id,
                                     name,
                                     price,
                                     case when name in ('sugar', 'croutons', 'mini bread rings', 'sunflower seeds',
                                                        'flaxseed oil', 'grapes', 'olive oil', 'watermelon', 'white bread', 'yogurt',
                                                         'cream', 'buckwheat', 'oatmeal', 'pasta', 'lamb', 'oranges', 'bagels', 'bread',
                                                         'peas', 'sour cream', 'smoked fish', 'flour', 'sprats', 'sausages', 'pork',
                                                         'rice', 'sesame oil', 'condensed milk', 'pineapple', 'beef', 'salt', 'dried fish',
                                                         'sunflower oil', 'apples', 'pears', 'flatbread', 'milk', 'chicken',
                                                         'lavash', 'wafers', 'tangerines')
                                          then round (price*10/110, 2)
                                          else round (price*20/120, 2) end as tax
                              FROM   (SELECT data,
                                             order_id,
                                             name,
                                             price
                                      FROM   (SELECT order_id,
                                                     date(creation_time) as data,
                                                     unnest(product_ids) as product_id
                                              FROM   orders
                                              WHERE  order_id not in (SELECT order_id
                                                                      FROM   user_actions
                                                                      WHERE  action = 'cancel_order')) t1
                                          LEFT JOIN products using(product_id))t5)t6
                      GROUP BY data
                      ORDER BY data), sub2_cost_cour as (SELECT data,
                                          sum(cost) as cost
                                   FROM   (SELECT courier_id,
                                                  kol_zak,
                                                  data,
                                                  date_part('month', data)::int as month,
                                                  case when kol_zak >= 5 and
                                                            date_part('month', data)::int >= 9 then kol_zak*150+500
                                                       when kol_zak >= 5 and
                                                            date_part('month', data)::int = 8 then kol_zak*150+400
                                                       when kol_zak < 5 then kol_zak*150 end as cost
                                           FROM   (SELECT courier_id,
                                                          count(courier_id) as kol_zak,
                                                          date(time) as data
                                                   FROM   courier_actions
                                                   WHERE  action = 'deliver_order'
                                                   GROUP BY date(time), courier_id
                                                   ORDER BY data) t2) t4
                                   GROUP BY data
                                   ORDER BY data), sub3_order_costs as (SELECT data,
                                            kol_order,
                                            case when date_part('month', data)::int = 8 then kol_order*140+120000
                                                 else kol_order*115+150000 end as price_order
                                     FROM   (SELECT date(time) as data,
                                                    count(order_id) as kol_order
                                             FROM   courier_actions
                                             WHERE  order_id not in (SELECT order_id
                                                                     FROM   user_actions
                                                                     WHERE  action = 'cancel_order')
                                                and action = 'accept_order'
                                             GROUP BY date(time)
                                             ORDER BY data) t3), sub4_all_costs as (SELECT data,
                                              revenue,
                                              cost+price_order as costs,
                                              tax
                                       FROM   sub2_cost_cour join sub3_order_costs using (data) join sub1_revenue using(data))
SELECT data as date,
       revenue,
       costs,
       tax,
       revenue-(costs+tax) as gross_profit,
       sum(revenue) OVER (ORDER BY data) as total_revenue,
       sum(costs) OVER (ORDER BY data) as total_costs,
       sum(tax) OVER(ORDER BY data) as total_tax,
       sum(revenue-costs-tax) OVER(ORDER BY data) as total_gross_profit,
       round(100*(revenue-costs-tax)/revenue, 2) as gross_profit_ratio,
       round(100*sum(revenue-costs-tax) OVER (ORDER BY data)/sum(revenue) OVER (ORDER BY data),
             2) as total_gross_profit_ratio
FROM   sub4_all_costs
ORDER BY data
