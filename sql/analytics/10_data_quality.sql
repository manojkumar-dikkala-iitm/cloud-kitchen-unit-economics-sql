/*
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
MODULE A — DATA QUALITY AND PROFILING          
Techniques: joins, aggregates, GROUP BY, string functions. Your solid ground.
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
*/

USE etable_analytics;
/*
--------------------------------------------------------------------------------
		A1. Dataset shape and coverage.
		Business question: What period, what scale, which outlets are live when?
--------------------------------------------------------------------------------        
*/

SELECT
    o.outlet_id,
    ot.outlet_name,
    MIN(DATE(o.order_datetime))            AS first_order,
    MAX(DATE(o.order_datetime))            AS last_order,
    COUNT(*)                               AS total_orders,
    COUNT(DISTINCT o.customer_id)          AS unique_customers,
    ROUND(SUM(o.gross_order_value), 0)     AS lifetime_gross
FROM orders o
JOIN outlets ot ON o.outlet_id = ot.outlet_id
GROUP BY o.outlet_id, ot.outlet_name
ORDER BY lifetime_gross DESC;


/*
--------------------------------------------------------------------------------
		A2. THE CLEANING PROBLEM: inconsistent locality spellings.
	    Business question: how many delivery areas do we actually serve?
		Raw distinct count is wrong. Normalise, then count.
--------------------------------------------------------------------------------
*/

SELECT
    COUNT(DISTINCT delivery_area)                                  AS raw_variants,
    COUNT(DISTINCT LOWER(TRIM(REPLACE(delivery_area, '.', ''))))   AS cleaned_variants
FROM customers;

-- A2b. See the damage, and the fix.
SELECT
    LOWER(TRIM(REPLACE(delivery_area, '.', '')))    AS cleaned_area,
    COUNT(*)                                        AS customers,
    COUNT(DISTINCT delivery_area)                   AS spelling_variants,
    GROUP_CONCAT(DISTINCT delivery_area ORDER BY delivery_area SEPARATOR ' | ')
                                                    AS variants_found
FROM customers
GROUP BY LOWER(TRIM(REPLACE(delivery_area, '.', '')))
HAVING COUNT(DISTINCT delivery_area) > 1
ORDER BY customers DESC;

UPDATE outlets
SET outlet_name = CASE outlet_id
    WHEN 1 THEN 'E-Table Kandanchavadi'
    WHEN 2 THEN 'E-Table Velachery'
    WHEN 3 THEN 'E-Table Thoraipakkam'
END;

UPDATE outlets
SET
    outlet_name = 'E-Table Velachery',
    locality = 'Velachery'
WHERE outlet_id = 2;

UPDATE outlets
SET
    outlet_name = 'E-Table Thoraipakkam',
    locality = 'Thoraipakkam'
WHERE outlet_id = 3;

SELECT
    outlet_id,
    outlet_name,
    locality
FROM outlets
ORDER BY outlet_id;


/*
--------------------------------------------------------------------------------
		A3. Order status profile, and who bears the cost.
--------------------------------------------------------------------------------
*/

SELECT
    order_status,
    COUNT(*)                                                    AS orders,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)            AS pct_of_orders,
    ROUND(AVG(gross_order_value), 0)                            AS avg_order_value,
    ROUND(SUM(refund_amount), 0)                                AS total_refunded
FROM orders
GROUP BY order_status
ORDER BY orders DESC;

/*
--------------------------------------------------------------------------------
		A4. Cancellation reasons: which are operational (our fault) vs external?
--------------------------------------------------------------------------------
*/

SELECT
    COALESCE(cancellation_reason, '(not cancelled)')    AS reason,
    COUNT(*)                                           AS orders,
    ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM orders
                            WHERE order_status = 'cancelled'), 1) AS pct_of_cancellations
FROM orders
WHERE order_status = 'cancelled'
GROUP BY cancellation_reason
ORDER BY orders DESC;

/*
--------------------------------------------------------------------------------
		A5. Missing-data audit. Which columns have NULLs, and is that meaningful?
--------------------------------------------------------------------------------
*/

SELECT 'rating'              AS column_name,
       SUM(rating IS NULL)   AS null_rows,
       ROUND(100 * SUM(rating IS NULL) / COUNT(*), 1) AS null_pct
FROM orders
UNION ALL
SELECT 'cancellation_reason', SUM(cancellation_reason IS NULL),
       ROUND(100 * SUM(cancellation_reason IS NULL) / COUNT(*), 1)
FROM orders
UNION ALL
SELECT 'delivery_area', SUM(delivery_area IS NULL),
       ROUND(100 * SUM(delivery_area IS NULL) / COUNT(*), 1)
FROM customers;
