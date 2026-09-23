/*
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
MODULE F — OPERATIONS                            
Techniques: joins, CTEs, correlation by grouping.
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
*/

USE etable_analytics;

/*
--------------------------------------------------------------------------------
F1.. THE STOCKOUT VS WASTAGE TRADE-OFF.
     Business question: we deliberately preferred occasional stockouts over
     guaranteed wastage. Was that the right call?
--------------------------------------------------------------------------------        
*/

WITH daily_stockouts AS (
    SELECT
        outlet_id,
        availability_date,
        SUM(sold_out_time IS NOT NULL)                          AS items_sold_out,
        SUM(estimated_lost_orders)                              AS lost_orders
    FROM item_availability
    GROUP BY outlet_id, availability_date
),
daily_waste AS (
    SELECT outlet_id, wastage_date,
           SUM(quantity_kg)     AS waste_kg,
           SUM(estimated_cost)  AS waste_cost
    FROM wastage
    GROUP BY outlet_id, wastage_date
),
daily_orders AS (
    SELECT outlet_id, DATE(order_datetime) AS d, COUNT(*) AS orders
    FROM orders WHERE order_status <> 'cancelled'
    GROUP BY outlet_id, DATE(order_datetime)
)
SELECT
    CASE WHEN s.items_sold_out = 0 THEN 'No stockout'
         WHEN s.items_sold_out <= 2 THEN '1-2 items out'
         ELSE '3+ items out' END                                AS stockout_level,
    COUNT(*)                                                    AS days,
    ROUND(AVG(o.orders), 1)                                     AS avg_orders,
    ROUND(AVG(s.lost_orders), 2)                                AS avg_lost_orders,
    ROUND(AVG(w.waste_kg), 2)                                   AS avg_waste_kg,
    ROUND(AVG(w.waste_cost), 0)                                 AS avg_waste_cost
FROM daily_stockouts s
JOIN daily_waste  w ON s.outlet_id = w.outlet_id AND s.availability_date = w.wastage_date
JOIN daily_orders o ON s.outlet_id = o.outlet_id AND s.availability_date = o.d
WHERE s.outlet_id = 1
GROUP BY stockout_level
ORDER BY stockout_level;

/*
---------------------------------------------------------------------------------
F2. DOES LATE DELIVERY DAMAGE RATINGS?
---------------------------------------------------------------------------------
*/

SELECT
    CASE
        WHEN prep_minutes + delivery_minutes <= 30 THEN '1. under 30 min'
        WHEN prep_minutes + delivery_minutes <= 45 THEN '2. 30-45 min'
        WHEN prep_minutes + delivery_minutes <= 55 THEN '3. 45-55 min'
        ELSE                                            '4. over 55 min'
    END                                                         AS delivery_band,
    COUNT(*)                                                    AS orders,
    SUM(rating IS NOT NULL)                                     AS rated_orders,
    ROUND(AVG(rating), 2)                                       AS avg_rating,
    ROUND(100 * SUM(rating <= 2) / SUM(rating IS NOT NULL), 1)  AS pct_1_or_2_star
FROM orders
WHERE order_status = 'completed'
GROUP BY delivery_band
ORDER BY delivery_band;

/*
---------------------------------------------------------------------------------
F3. CAPACITY UTILISATION: were we turning away demand?
---------------------------------------------------------------------------------
*/

WITH daily AS (
    SELECT
        o.outlet_id,
        DATE(o.order_datetime)                                  AS d,
        COUNT(*)                                                AS orders,
        AVG(o.prep_minutes)                                     AS avg_prep
    FROM orders o
    WHERE o.order_status <> 'cancelled'
    GROUP BY o.outlet_id, DATE(o.order_datetime)
)
SELECT
    ROUND(100 * d.orders / p.kitchen_capacity_orders, 0)        AS utilisation_pct_bucket,
    COUNT(*)                                                    AS days,
    ROUND(AVG(d.avg_prep), 1)                                   AS avg_prep_minutes
FROM daily d
JOIN daily_operations p ON d.outlet_id = p.outlet_id AND d.d = p.operation_date
WHERE d.outlet_id = 1
GROUP BY ROUND(100 * d.orders / p.kitchen_capacity_orders, 0)
ORDER BY utilisation_pct_bucket;

/*
---------------------------------------------------------------------------------
F4. WASTAGE COMPOSITION OVER TIME: the month-6 optimisation, visible.
---------------------------------------------------------------------------------
*/

SELECT
    DATE_FORMAT(wastage_date, '%Y-%m')                          AS ym,
    ROUND(SUM(CASE WHEN waste_type = 'prep_waste'      THEN quantity_kg END), 1) AS prep,
    ROUND(SUM(CASE WHEN waste_type = 'unsold_cooked'   THEN quantity_kg END), 1) AS unsold,
    ROUND(SUM(CASE WHEN waste_type = 'spoilage'        THEN quantity_kg END), 1) AS spoilage,
    ROUND(SUM(CASE WHEN waste_type = 'returned_order'  THEN quantity_kg END), 1) AS returns,
    ROUND(SUM(quantity_kg), 1)                                  AS total_kg,
    ROUND(SUM(quantity_kg) / 4.35, 2)                           AS kg_per_week
FROM wastage
WHERE outlet_id = 1 AND wastage_date < '2019-07-01'
GROUP BY DATE_FORMAT(wastage_date, '%Y-%m')
ORDER BY ym;

