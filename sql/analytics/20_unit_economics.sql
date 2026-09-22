/*
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
MODULE B — UNIT ECONOMICS                    
Techniques: CTEs, multi-table joins, derived metrics.
THIS MODULE IS THE CORE OF THE PROJECT.
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
*/

USE etable_analytics;
/*
--------------------------------------------------------------------------------
B1. THE MONTHLY P&L. Every other financial query descends from this one.
    Business question: what did each outlet actually earn, month by month?
--------------------------------------------------------------------------------
*/


WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items
    GROUP BY order_id
),
monthly_revenue AS (
    SELECT
        DATE_FORMAT(o.order_datetime, '%Y-%m-01')   AS month_start,
        o.outlet_id,
        COUNT(*)                                    AS orders,
        ROUND(AVG(o.gross_order_value), 0)          AS aov,
        SUM(o.gross_order_value)                    AS gross,
        SUM(o.platform_funded_discount)             AS platform_discount,
        SUM(o.restaurant_funded_discount)           AS our_discount,
        SUM(o.commission_amount)                    AS commission,
        SUM(o.other_deductions)                     AS other_deductions,
        SUM(o.refund_amount)                        AS refunds,
        SUM(f.food_cost)                            AS food_cost,
        SUM(o.packaging_cost)                       AS packaging
    FROM orders o
    JOIN order_food f ON o.order_id = f.order_id
    WHERE o.order_status <> 'cancelled'
    GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m-01'), o.outlet_id
),
monthly_opex AS (
    SELECT
        DATE_FORMAT(expense_month, '%Y-%m-01')  AS month_start,
        outlet_id,
        SUM(amount)                             AS opex
    FROM expenses
    WHERE outlet_id IS NOT NULL
    GROUP BY DATE_FORMAT(expense_month, '%Y-%m-01'), outlet_id
)
SELECT
    r.month_start,
    r.outlet_id,
    r.orders,
    r.aov,
    ROUND(r.gross, 0)                                           AS gross,
    ROUND(r.gross - r.our_discount - r.commission
          - r.other_deductions - r.refunds
          - r.food_cost - r.packaging, 0)                       AS contribution,
    ROUND(100 * (r.gross - r.our_discount - r.commission
          - r.other_deductions - r.refunds
          - r.food_cost - r.packaging) / r.gross, 1)            AS contribution_pct,
    ROUND(COALESCE(x.opex, 0), 0)                               AS opex,
    ROUND(r.gross - r.our_discount - r.commission
          - r.other_deductions - r.refunds - r.food_cost
          - r.packaging - COALESCE(x.opex, 0), 0)               AS outlet_net,
    ROUND(r.platform_discount, 0)                               AS platform_funded_discount_fyi
FROM monthly_revenue r
LEFT JOIN monthly_opex x
       ON r.month_start = x.month_start AND r.outlet_id = x.outlet_id
ORDER BY r.month_start, r.outlet_id;


/*
--------------------------------------------------------------------------------
B2. COMPANY-WIDE P&L including company-level costs.
    Business question: after central kitchen rent, compliance and my own drawings, what did the business actually make?
--------------------------------------------------------------------------------
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
),
monthly_contribution AS (
    SELECT
        DATE_FORMAT(o.order_datetime, '%Y-%m-01') AS month_start,
        SUM(o.gross_order_value)                  AS gross,
        SUM(o.gross_order_value - o.restaurant_funded_discount
            - o.commission_amount - o.other_deductions
            - o.refund_amount - f.food_cost - o.packaging_cost) AS contribution
    FROM orders o
    JOIN order_food f ON o.order_id = f.order_id
    WHERE o.order_status <> 'cancelled'
    GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m-01')
),
monthly_costs AS (
    SELECT
        DATE_FORMAT(expense_month, '%Y-%m-01') AS month_start,
        SUM(CASE WHEN outlet_id IS NOT NULL THEN amount ELSE 0 END) AS outlet_opex,
        SUM(CASE WHEN outlet_id IS NULL AND expense_category <> 'founder_drawings'
                 THEN amount ELSE 0 END)                            AS company_opex,
        SUM(CASE WHEN expense_category = 'founder_drawings'
                 THEN amount ELSE 0 END)                            AS founder_drawings
    FROM expenses
    GROUP BY DATE_FORMAT(expense_month, '%Y-%m-01')
)
SELECT
    c.month_start,
    ROUND(c.gross, 0)                                       AS gross,
    ROUND(c.contribution, 0)                                AS contribution,
    ROUND(k.outlet_opex, 0)                                 AS outlet_opex,
    ROUND(k.company_opex, 0)                                AS company_opex,
    ROUND(c.contribution - k.outlet_opex - k.company_opex, 0)
                                                            AS net_before_drawings,
    ROUND(k.founder_drawings, 0)                            AS founder_drawings,
    ROUND(c.contribution - k.outlet_opex - k.company_opex
          - k.founder_drawings, 0)                          AS net_after_drawings
FROM monthly_contribution c
JOIN monthly_costs k ON c.month_start = k.month_start
ORDER BY c.month_start;


/*
--------------------------------------------------------------------------------
B3. REVENUE SHARE IS NOT PROFIT SHARE.
    Business question: which outlet actually made money?
--------------------------------------------------------------------------------
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
),
outlet_perf AS (
    SELECT
        o.outlet_id,
        COUNT(*)                        AS orders,
        SUM(o.gross_order_value)        AS gross,
        SUM(o.gross_order_value - o.restaurant_funded_discount
            - o.commission_amount - o.other_deductions
            - o.refund_amount - f.food_cost - o.packaging_cost) AS contribution
    FROM orders o
    JOIN order_food f ON o.order_id = f.order_id
    WHERE o.order_status <> 'cancelled'
    GROUP BY o.outlet_id
),
outlet_cost AS (
    SELECT outlet_id, SUM(amount) AS opex
    FROM expenses WHERE outlet_id IS NOT NULL GROUP BY outlet_id
)
SELECT
    ot.outlet_name,
    ot.outlet_type,
    p.orders,
    ROUND(p.gross, 0)                                       AS lifetime_gross,
    ROUND(100 * p.gross / SUM(p.gross) OVER (), 1)          AS pct_of_revenue,
    ROUND(p.contribution - c.opex, 0)                       AS lifetime_net,
    ROUND(100 * (p.contribution - c.opex)
          / SUM(p.contribution - c.opex) OVER (), 1)        AS pct_of_profit
FROM outlet_perf p
JOIN outlet_cost c  ON p.outlet_id = c.outlet_id
JOIN outlets    ot  ON p.outlet_id = ot.outlet_id
ORDER BY lifetime_gross DESC;


/*
--------------------------------------------------------------------------------
B4. PLATFORM ECONOMICS: funded vs unfunded discount attribution.
    THIS IS YOUR DIFFERENTIATOR. Most portfolios subtract the entire
    customer-visible discount from restaurant revenue. That is wrong, and it
    understates realisation on every platform-funded campaign.
--------------------------------------------------------------------------------
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
)
SELECT
    p.platform_name,
    COUNT(*)                                                    AS orders,
    ROUND(SUM(o.gross_order_value), 0)                          AS gross,
    ROUND(SUM(o.platform_funded_discount), 0)                   AS platform_funded,
    ROUND(SUM(o.restaurant_funded_discount), 0)                 AS restaurant_funded,
    -- the discount the CUSTOMER saw
    ROUND(100 * SUM(o.platform_funded_discount + o.restaurant_funded_discount)
          / SUM(o.gross_order_value), 1)                        AS customer_visible_disc_pct,
    -- the discount that actually cost US anything
    ROUND(100 * SUM(o.restaurant_funded_discount)
          / SUM(o.gross_order_value), 1)                        AS our_real_cost_pct,
    -- true net realisation per rupee of gross
    ROUND(100 * SUM(o.gross_order_value - o.restaurant_funded_discount
          - o.commission_amount - o.other_deductions)
          / SUM(o.gross_order_value), 1)                        AS net_realisation_pct,
    ROUND(SUM(o.gross_order_value - o.restaurant_funded_discount
          - o.commission_amount - o.other_deductions
          - f.food_cost - o.packaging_cost) / COUNT(*), 2)      AS contribution_per_order
FROM orders o
JOIN order_food f  ON o.order_id = f.order_id
JOIN platforms  p  ON o.platform_id = p.platform_id
WHERE o.order_status <> 'cancelled'
GROUP BY p.platform_name
ORDER BY contribution_per_order DESC;


/*
--------------------------------------------------------------------------------
B5. PLATFORM SHUTDOWN: where did the orders go?
    UberEats shut Jan 2020; Foodpanda exited restaurant delivery in 2019.
    Did we lose that volume or did it migrate?
--------------------------------------------------------------------------------
*/

SELECT
    DATE_FORMAT(o.order_datetime, '%Y-%m')                      AS ym,
    SUM(p.platform_name = 'Swiggy')                             AS swiggy,
    SUM(p.platform_name = 'Zomato')                             AS zomato,
    SUM(p.platform_name = 'UberEats')                           AS ubereats,
    SUM(p.platform_name = 'Foodpanda')                          AS foodpanda,
    COUNT(*)                                                    AS total
FROM orders o
JOIN platforms p ON o.platform_id = p.platform_id
WHERE o.order_status <> 'cancelled'
  AND o.order_datetime >= '2019-01-01' AND o.order_datetime < '2020-07-01'
GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m')
ORDER BY ym;
