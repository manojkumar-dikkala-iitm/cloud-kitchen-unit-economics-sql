/*
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
MODULE C - MENU ENGINEERING                 
Techniques: CTEs, window functions, median workaround.
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
*/

USE etable_analytics;

/*
--------------------------------------------------------------------------------
C1. The base table: volume and margin per item.
--------------------------------------------------------------------------------        
*/

SELECT
    m.menu_item_id,
    m.item_name,
    m.category,
    m.veg_nonveg,
    SUM(oi.quantity)                                            AS units_sold,
    ROUND(SUM(oi.line_total), 0)                                AS gross_revenue,
    ROUND(SUM(oi.unit_food_cost * oi.quantity), 0)              AS food_cost,
    ROUND((SUM(oi.line_total) - SUM(oi.unit_food_cost * oi.quantity))
          / SUM(oi.quantity), 2)                                AS contribution_per_unit,
    ROUND(100 * (SUM(oi.line_total) - SUM(oi.unit_food_cost * oi.quantity))
          / SUM(oi.line_total), 1)                              AS contribution_margin_pct
FROM order_items oi
JOIN orders     o ON oi.order_id = o.order_id
JOIN menu_items m ON oi.menu_item_id = m.menu_item_id
WHERE o.order_status <> 'cancelled'
GROUP BY m.menu_item_id, m.item_name, m.category, m.veg_nonveg
ORDER BY units_sold DESC;


/*
--------------------------------------------------------------------------------
C2. THE KASAVANA-SMITH CLASSIFICATION.
     Window functions used: AVG(...) OVER () computes the menu-wide average
     but returns it on every row, so each item can be compared to it without
     a self-join.
--------------------------------------------------------------------------------        
*/

WITH item_stats AS (
    SELECT
        m.menu_item_id,
        m.item_name,
        m.category,
        SUM(oi.quantity)                                        AS units_sold,
        (SUM(oi.line_total) - SUM(oi.unit_food_cost * oi.quantity))
            / SUM(oi.quantity)                                  AS contrib_per_unit
    FROM order_items oi
    JOIN orders     o ON oi.order_id = o.order_id
    JOIN menu_items m ON oi.menu_item_id = m.menu_item_id
    WHERE o.order_status <> 'cancelled'
      AND m.category IN ('Biryani','Starter','Curry','Meals')   -- mains only
    GROUP BY m.menu_item_id, m.item_name, m.category
),
benchmarks AS (
    SELECT
        s.*,
        AVG(s.units_sold)      OVER ()                          AS avg_units,
        AVG(s.contrib_per_unit) OVER ()                         AS avg_contrib,
        SUM(s.units_sold)      OVER ()                          AS total_units
    FROM item_stats s
)
SELECT
    item_name,
    category,
    units_sold,
    ROUND(100 * units_sold / total_units, 2)                    AS volume_share_pct,
    ROUND(contrib_per_unit, 2)                                  AS contribution_per_unit,
    ROUND(avg_contrib, 2)                                       AS menu_avg_contribution,
    CASE WHEN units_sold >= 0.70 * avg_units THEN 'HIGH' ELSE 'LOW' END AS popularity,
    CASE WHEN contrib_per_unit >= avg_contrib THEN 'HIGH' ELSE 'LOW' END AS profitability,
    CASE
        WHEN units_sold >= 0.70 * avg_units AND contrib_per_unit >= avg_contrib
             THEN 'STAR'
        WHEN units_sold >= 0.70 * avg_units AND contrib_per_unit <  avg_contrib
             THEN 'PLOWHORSE'
        WHEN units_sold <  0.70 * avg_units AND contrib_per_unit >= avg_contrib
             THEN 'PUZZLE'
        ELSE 'DOG'
    END                                                         AS menu_quadrant
FROM benchmarks
ORDER BY menu_quadrant, units_sold DESC;

/*
--------------------------------------------------------------------------------
C2b. MEDIAN WORKAROUND (PERCENTILE_CONT does not exist in MySQL 8).
--------------------------------------------------------------------------------        
*/

WITH item_contrib AS (
    SELECT
        m.item_name,
        (SUM(oi.line_total) - SUM(oi.unit_food_cost * oi.quantity))
            / SUM(oi.quantity)                                  AS contrib_per_unit
    FROM order_items oi
    JOIN orders     o ON oi.order_id = o.order_id
    JOIN menu_items m ON oi.menu_item_id = m.menu_item_id
    WHERE o.order_status <> 'cancelled'
      AND m.category IN ('Biryani','Starter','Curry','Meals')
    GROUP BY m.item_name
),
ranked AS (
    SELECT
        contrib_per_unit,
        ROW_NUMBER() OVER (ORDER BY contrib_per_unit)           AS rn,
        COUNT(*)     OVER ()                                    AS n
    FROM item_contrib
)
SELECT ROUND(AVG(contrib_per_unit), 2) AS median_contribution_per_unit
FROM ranked
WHERE rn IN (FLOOR((n + 1) / 2), CEIL((n + 1) / 2));

/*
--------------------------------------------------------------------------------
C3. DID DISCONTINUING DESSERTS HELP?
    Business question: desserts were dropped for wastage. Was that right?
--------------------------------------------------------------------------------        
*/

SELECT
    CASE WHEN w.wastage_date < '2018-09-01' THEN 'Desserts on menu'
         ELSE 'After discontinuation' END                       AS period,
    COUNT(DISTINCT w.wastage_date)                              AS days,
    ROUND(SUM(w.quantity_kg), 1)                                AS total_kg,
    ROUND(SUM(w.quantity_kg) / COUNT(DISTINCT w.wastage_date), 2) AS kg_per_day,
    ROUND(SUM(w.estimated_cost), 0)                             AS waste_cost
FROM wastage w
WHERE w.outlet_id = 1
  AND w.wastage_date < '2019-06-01'
GROUP BY CASE WHEN w.wastage_date < '2018-09-01' THEN 'Desserts on menu'
              ELSE 'After discontinuation' END;


/*
C4. THE VEG EXPANSION: was customer-driven expansion justified?
*/

SELECT
    YEAR(o.order_datetime)                                      AS yr,
    m.veg_nonveg,
    COUNT(DISTINCT o.order_id)                                  AS orders_containing,
    SUM(oi.quantity)                                            AS units,
    ROUND(SUM(oi.line_total), 0)                                AS revenue,
    ROUND(100 * (SUM(oi.line_total) - SUM(oi.unit_food_cost * oi.quantity))
          / SUM(oi.line_total), 1)                              AS margin_pct
FROM order_items oi
JOIN orders     o ON oi.order_id = o.order_id
JOIN menu_items m ON oi.menu_item_id = m.menu_item_id
WHERE o.order_status <> 'cancelled'
GROUP BY YEAR(o.order_datetime), m.veg_nonveg
ORDER BY yr, m.veg_nonveg;

