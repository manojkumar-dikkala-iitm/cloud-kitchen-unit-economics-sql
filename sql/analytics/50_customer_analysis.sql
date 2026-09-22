/*
---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
MODULE E — CUSTOMER BEHAVIOUR              
Techniques: CTEs, window functions, cohort logic.
---------------------------------------------------------------------------------
---------------------------------------------------------------------------------
*/

USE etable_analytics;

/*
---------------------------------------------------------------------------------
E1. Repeat rate by platform.
---------------------------------------------------------------------------------
*/

WITH customer_orders AS (
    SELECT
        o.customer_id,
        c.platform_id,
        COUNT(*) AS order_count
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.order_status <> 'cancelled'
    GROUP BY o.customer_id, c.platform_id
)
SELECT
    p.platform_name,
    COUNT(*)                                                    AS customers,
    SUM(order_count)                                            AS orders,
    ROUND(AVG(order_count), 2)                                  AS avg_orders_per_customer,
    SUM(order_count > 1)                                        AS repeat_customers,
    ROUND(100 * SUM(order_count > 1) / COUNT(*), 1)             AS repeat_customer_pct,
    ROUND(100 * SUM(CASE WHEN order_count > 1 THEN order_count ELSE 0 END)
          / SUM(order_count), 1)                                AS pct_orders_from_repeaters
FROM customer_orders co
JOIN platforms p ON co.platform_id = p.platform_id
GROUP BY p.platform_name
ORDER BY repeat_customer_pct DESC;


/*
---------------------------------------------------------------------------------
E2. COHORT RETENTION.
    Group customers by the month of their first order, then track how many
    ordered again in each subsequent month.
---------------------------------------------------------------------------------
*/

WITH first_order AS (
    SELECT
        customer_id,
        DATE_FORMAT(MIN(order_datetime), '%Y-%m')               AS cohort_month
    FROM orders
    WHERE order_status <> 'cancelled'
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
        o.customer_id,
        f.cohort_month,
        DATE_FORMAT(o.order_datetime, '%Y-%m')                  AS active_month,
        TIMESTAMPDIFF(MONTH,
            STR_TO_DATE(CONCAT(f.cohort_month, '-01'), '%Y-%m-%d'),
            STR_TO_DATE(CONCAT(DATE_FORMAT(o.order_datetime, '%Y-%m'), '-01'),
                        '%Y-%m-%d'))                            AS month_offset
    FROM orders o
    JOIN first_order f ON o.customer_id = f.customer_id
    WHERE o.order_status <> 'cancelled'
),
sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM first_order GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    s.cohort_size,
    a.month_offset,
    COUNT(DISTINCT a.customer_id)                               AS active_customers,
    ROUND(100 * COUNT(DISTINCT a.customer_id) / s.cohort_size, 1) AS retention_pct
FROM activity a
JOIN sizes    s ON a.cohort_month = s.cohort_month
WHERE a.month_offset BETWEEN 0 AND 6
  AND a.cohort_month BETWEEN '2019-01' AND '2019-12'
GROUP BY a.cohort_month, s.cohort_size, a.month_offset
ORDER BY a.cohort_month, a.month_offset;

/*
---------------------------------------------------------------------------------
E3. Order value distribution: is AOV hiding a bimodal basket?
---------------------------------------------------------------------------------
*/

SELECT
    CASE
        WHEN gross_order_value < 250 THEN '1. under 250'
        WHEN gross_order_value < 350 THEN '2. 250-349'
        WHEN gross_order_value < 450 THEN '3. 350-449'
        WHEN gross_order_value < 600 THEN '4. 450-599'
        WHEN gross_order_value < 800 THEN '5. 600-799'
        ELSE                              '6. 800+'
    END                                                         AS value_band,
    COUNT(*)                                                    AS orders,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS pct_of_orders,
    ROUND(SUM(gross_order_value), 0)                            AS gross,
    ROUND(100 * SUM(gross_order_value)
          / SUM(SUM(gross_order_value)) OVER (), 1)             AS pct_of_revenue
FROM orders
WHERE order_status <> 'cancelled'
GROUP BY value_band
ORDER BY value_band;

