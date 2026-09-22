-- =====================================================================
-- E-Table Foods — 03_validate.sql : post-load integrity checks
-- Run this immediately after 02_load.sql. Every check must return OK.
-- These use only basic SQL (joins, aggregates, CASE) — nothing above
-- your confirmed skill level. Nothing here is analysis; it is proof the
-- load worked before any analysis is trusted.
-- =====================================================================

USE etable_analytics;

-- ---------------------------------------------------------------------
-- CHECK 1 — row counts match the source CSVs
-- ---------------------------------------------------------------------
SELECT 'outlets' AS table_name, 3 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 3 THEN 'OK' ELSE 'MISMATCH' END AS status FROM outlets
UNION ALL
SELECT 'platforms' AS table_name, 4 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 4 THEN 'OK' ELSE 'MISMATCH' END AS status FROM platforms
UNION ALL
SELECT 'menu_items' AS table_name, 28 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 28 THEN 'OK' ELSE 'MISMATCH' END AS status FROM menu_items
UNION ALL
SELECT 'menu_item_prices' AS table_name, 378 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 378 THEN 'OK' ELSE 'MISMATCH' END AS status FROM menu_item_prices
UNION ALL
SELECT 'customers' AS table_name, 43838 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 43838 THEN 'OK' ELSE 'MISMATCH' END AS status FROM customers
UNION ALL
SELECT 'orders' AS table_name, 65390 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 65390 THEN 'OK' ELSE 'MISMATCH' END AS status FROM orders
UNION ALL
SELECT 'order_items' AS table_name, 111523 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 111523 THEN 'OK' ELSE 'MISMATCH' END AS status FROM order_items
UNION ALL
SELECT 'promotions' AS table_name, 66 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 66 THEN 'OK' ELSE 'MISMATCH' END AS status FROM promotions
UNION ALL
SELECT 'item_availability' AS table_name, 59465 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 59465 THEN 'OK' ELSE 'MISMATCH' END AS status FROM item_availability
UNION ALL
SELECT 'wastage' AS table_name, 14604 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 14604 THEN 'OK' ELSE 'MISMATCH' END AS status FROM wastage
UNION ALL
SELECT 'expenses' AS table_name, 1101 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 1101 THEN 'OK' ELSE 'MISMATCH' END AS status FROM expenses
UNION ALL
SELECT 'daily_operations' AS table_name, 3651 AS expected, COUNT(*) AS actual,
       CASE WHEN COUNT(*) = 3651 THEN 'OK' ELSE 'MISMATCH' END AS status FROM daily_operations;

-- ---------------------------------------------------------------------
-- CHECK 2 — referential integrity (should return zero rows)
-- FKs enforce this on insert, so an empty result is the expected outcome.
-- Included because a reviewer will ask whether you verified it.
-- ---------------------------------------------------------------------
SELECT 'orders.customer_id' AS orphan_in, COUNT(*) AS orphans
FROM orders o LEFT JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL
UNION ALL
SELECT 'order_items.order_id', COUNT(*)
FROM order_items oi LEFT JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_id IS NULL
UNION ALL
SELECT 'order_items.menu_item_id', COUNT(*)
FROM order_items oi LEFT JOIN menu_items m ON oi.menu_item_id = m.menu_item_id
WHERE m.menu_item_id IS NULL;

-- ---------------------------------------------------------------------
-- CHECK 3 — TIER 1 HARD CONSTRAINTS
-- These are the non-negotiables. Any FAIL invalidates the dataset.
-- ---------------------------------------------------------------------

-- 3a. UberEats must not appear after Jan 2020; Foodpanda not after 2019
SELECT p.platform_name,
       MIN(DATE(o.order_datetime)) AS first_order,
       MAX(DATE(o.order_datetime)) AS last_order,
       COUNT(*) AS orders
FROM orders o
JOIN platforms p ON o.platform_id = p.platform_id
GROUP BY p.platform_name
ORDER BY last_order;

-- 3b. Commission must be 28% of gross, uniformly
SELECT ROUND(100 * SUM(commission_amount) / SUM(gross_order_value), 2) AS commission_pct,
       CASE WHEN ROUND(100 * SUM(commission_amount) / SUM(gross_order_value), 1) = 28.0
            THEN 'OK' ELSE 'FAIL' END AS status
FROM orders;

-- 3c. Packaging must be exactly Rs 15.00 on every non-cancelled order
SELECT COUNT(*) AS non_15_rupee_rows,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM orders
WHERE order_status <> 'cancelled' AND packaging_cost <> 15.00;

-- 3d. Wastage must never be zero in any month
SELECT COUNT(*) AS zero_wastage_months,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM (
    SELECT DATE_FORMAT(wastage_date, '%Y-%m') AS ym, SUM(quantity_kg) AS kg
    FROM wastage
    GROUP BY DATE_FORMAT(wastage_date, '%Y-%m')
    HAVING SUM(quantity_kg) <= 0
) z;

-- 3e. Customer delivery fee must NEVER be inside restaurant settlement.
--     settlement = gross - discounts - commission - other - refund
--     If this returns rows, the delivery fee has leaked into the P&L.
SELECT COUNT(*) AS settlement_mismatches,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM orders
WHERE ABS(restaurant_settlement
          - (gross_order_value - platform_funded_discount
             - restaurant_funded_discount - commission_amount
             - other_deductions - refund_amount)) > 0.05;

-- 3e2. Order/line reconciliation: sum(line_total) must equal gross_order_value.
--      Combo discounts are distributed across line items rather than applied at
--      order level, so this holds on every order including combos.
SELECT COUNT(*) AS order_line_mismatches,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM (
    SELECT o.order_id, o.gross_order_value, SUM(oi.line_total) AS line_sum
    FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
    GROUP BY o.order_id, o.gross_order_value
    HAVING ABS(o.gross_order_value - SUM(oi.line_total)) > 0.05
) m;

-- 3f. Aggregator listed price must never sit below base price
SELECT COUNT(*) AS bad_prices,
       CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'FAIL' END AS status
FROM menu_item_prices
WHERE listed_price < base_price;

-- 3g. Desserts must appear only in the early experimental window
SELECT m.item_name,
       MIN(DATE(o.order_datetime)) AS first_sold,
       MAX(DATE(o.order_datetime)) AS last_sold,
       COUNT(*) AS units
FROM order_items oi
JOIN menu_items m ON oi.menu_item_id = m.menu_item_id
JOIN orders o     ON oi.order_id = o.order_id
WHERE m.category = 'Dessert'
GROUP BY m.item_name;

-- ---------------------------------------------------------------------
-- CHECK 4 — TIER 2 CALIBRATION RANGES
-- These should land inside the bands, not hit exact values.
-- ---------------------------------------------------------------------

-- 4a. AOV must sit inside the Rs 390-450 envelope every year
SELECT YEAR(order_datetime) AS yr,
       COUNT(*) AS orders,
       ROUND(AVG(gross_order_value), 0) AS aov,
       CASE WHEN AVG(gross_order_value) BETWEEN 390 AND 450
            THEN 'IN RANGE' ELSE 'OUT OF RANGE' END AS status
FROM orders
WHERE order_status <> 'cancelled'
GROUP BY YEAR(order_datetime)
ORDER BY yr;

-- 4b. Mature benchmark outlet: 900-950 orders/month, Rs 3.8-4.0L gross
SELECT DATE_FORMAT(order_datetime, '%Y-%m') AS ym,
       COUNT(*) AS orders,
       ROUND(SUM(gross_order_value), 0) AS gross,
       ROUND(AVG(gross_order_value), 0) AS aov
FROM orders
WHERE outlet_id = 1
  AND order_status <> 'cancelled'
  AND order_datetime >= '2019-01-01' AND order_datetime < '2020-01-01'
GROUP BY DATE_FORMAT(order_datetime, '%Y-%m')
ORDER BY ym;

-- 4c. Food cost must be ~35% of BASE price (not of aggregator gross)
SELECT ROUND(100 * SUM(oi.unit_food_cost * oi.quantity) / SUM(oi.line_total), 1)
           AS pct_of_listed,
       ROUND(100 * SUM(oi.unit_food_cost * oi.quantity)
                 / (SUM(oi.line_total) / 1.15), 1) AS approx_pct_of_base
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
WHERE o.order_status <> 'cancelled';

-- 4d. Behavioural rates
SELECT
    ROUND(100 * SUM(order_status = 'cancelled') / COUNT(*), 2) AS cancel_pct,
    ROUND(100 * SUM(order_status LIKE 'refunded%') / COUNT(*), 2) AS refund_pct,
    ROUND(100 * SUM(rating IS NULL) / COUNT(*), 1) AS unrated_pct,
    ROUND(AVG(prep_minutes + delivery_minutes), 1) AS avg_total_minutes,
    ROUND(100 * SUM((prep_minutes + delivery_minutes) > 55) / COUNT(*), 1) AS late_pct
FROM orders;

-- ---------------------------------------------------------------------
-- CHECK 5 — the deliberate dirt is present and needs cleaning
-- If these return only one variant each, the cleaning exercise is missing.
-- ---------------------------------------------------------------------
SELECT delivery_area, COUNT(*) AS customers
FROM customers
WHERE LOWER(TRIM(REPLACE(delivery_area, '.', ''))) LIKE '%kandanchavadi%'
   OR LOWER(TRIM(REPLACE(delivery_area, '.', ''))) LIKE '%kandanchawadi%'
GROUP BY delivery_area
ORDER BY customers DESC;

-- ---------------------------------------------------------------------
-- CHECK 6 — company-level expenses loaded with NULL outlet_id
-- Expected: 141 rows across kitchen_rent, compliance, founder_drawings
-- ---------------------------------------------------------------------
SELECT expense_category, COUNT(*) AS months, ROUND(SUM(amount), 0) AS total
FROM expenses
WHERE outlet_id IS NULL
GROUP BY expense_category;
