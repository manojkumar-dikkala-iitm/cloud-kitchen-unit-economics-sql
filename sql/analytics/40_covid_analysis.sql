/*
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
MODULE D — COVID SHOCK AND COST BEHAVIOUR      
Techniques: CTEs, window functions, running totals.
YOUR THIRD DIFFERENTIATOR AND THE STRONGEST STORY IN THE PROJECT.
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
*/

USE etable_analytics;

/*
--------------------------------------------------------------------------------
D1. P&L BY COVID PHASE
--------------------------------------------------------------------------------        
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
),
phased AS (
    SELECT
        d.covid_phase,
        DATE_FORMAT(o.order_datetime, '%Y-%m')                  AS ym,
        SUM(o.gross_order_value)                                AS gross,
        COUNT(*)                                                AS orders,
        SUM(o.gross_order_value - o.restaurant_funded_discount
            - o.commission_amount - o.other_deductions
            - o.refund_amount - f.food_cost - o.packaging_cost) AS contribution
    FROM orders o
    JOIN order_food f       ON o.order_id = f.order_id
    JOIN daily_operations d ON d.outlet_id = o.outlet_id
                           AND d.operation_date = DATE(o.order_datetime)
    WHERE o.order_status <> 'cancelled'
    GROUP BY d.covid_phase, DATE_FORMAT(o.order_datetime, '%Y-%m')
),
costs AS (
    SELECT DATE_FORMAT(expense_month, '%Y-%m') AS ym, SUM(amount) AS opex
    FROM expenses GROUP BY DATE_FORMAT(expense_month, '%Y-%m')
)
SELECT
    p.covid_phase,
    COUNT(DISTINCT p.ym)                                        AS months,
    ROUND(AVG(p.orders), 0)                                     AS avg_monthly_orders,
    ROUND(AVG(p.gross), 0)                                      AS avg_monthly_gross,
    ROUND(AVG(p.contribution), 0)                               AS avg_contribution,
    ROUND(AVG(c.opex), 0)                                       AS avg_opex,
    ROUND(AVG(p.contribution) - AVG(c.opex), 0)                 AS avg_monthly_net
FROM phased p
JOIN costs c ON p.ym = c.ym
GROUP BY p.covid_phase
ORDER BY MIN(p.ym);


/*
--------------------------------------------------------------------------------
D2. FIXED VS VARIABLE COST BEHAVIOUR UNDER SHOCK.
     Business question: when revenue fell 88%, which costs fell with it?
     This is why expenses.cost_behaviour exists.
--------------------------------------------------------------------------------        
*/

WITH monthly_rev AS (
    SELECT DATE_FORMAT(order_datetime, '%Y-%m') AS ym,
           SUM(gross_order_value)               AS gross
    FROM orders WHERE order_status <> 'cancelled'
    GROUP BY DATE_FORMAT(order_datetime, '%Y-%m')
),
monthly_cost AS (
    SELECT DATE_FORMAT(expense_month, '%Y-%m')  AS ym,
           cost_behaviour,
           SUM(amount)                          AS amount
    FROM expenses
    GROUP BY DATE_FORMAT(expense_month, '%Y-%m'), cost_behaviour
),
baseline AS (   -- Feb 2020, the last pre-COVID month
    SELECT cost_behaviour, amount AS base_amount
    FROM monthly_cost WHERE ym = '2020-02'
),
base_rev AS (
    SELECT gross AS base_gross FROM monthly_rev WHERE ym = '2020-02'
)
SELECT
    c.ym,
    c.cost_behaviour,
    ROUND(c.amount, 0)                                          AS amount,
    ROUND(100 * c.amount / b.base_amount, 1)                    AS pct_of_feb2020_cost,
    ROUND(100 * r.gross / br.base_gross, 1)                     AS pct_of_feb2020_revenue
FROM monthly_cost c
JOIN baseline    b  ON c.cost_behaviour = b.cost_behaviour
JOIN monthly_rev r  ON c.ym = r.ym
CROSS JOIN base_rev br
WHERE c.ym BETWEEN '2020-02' AND '2020-08'
ORDER BY c.ym, c.cost_behaviour;


/*
--------------------------------------------------------------------------------
D3. THE SURVIVABLE ORDER FLOOR (breakeven).
    Business question: below how many orders a day was an outlet not worth
    keeping open? I remembered roughly 20. Does the data agree?
--------------------------------------------------------------------------------        
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
),
contrib AS (
    SELECT
        o.outlet_id,
        AVG(o.gross_order_value - o.restaurant_funded_discount
            - o.commission_amount - o.other_deductions
            - o.refund_amount - f.food_cost - o.packaging_cost) AS contrib_per_order
    FROM orders o
    JOIN order_food f ON o.order_id = f.order_id
    WHERE o.order_status <> 'cancelled'
      AND o.order_datetime >= '2019-01-01' AND o.order_datetime < '2020-03-01'
    GROUP BY o.outlet_id
),
fixed_cost AS (
    SELECT
        outlet_id,
        AVG(monthly_fixed)                                      AS avg_monthly_fixed
    FROM (
        SELECT outlet_id, DATE_FORMAT(expense_month, '%Y-%m') AS ym,
               SUM(amount) AS monthly_fixed
        FROM expenses
        WHERE outlet_id IS NOT NULL
          AND expense_month >= '2019-01-01' AND expense_month < '2020-03-01'
        GROUP BY outlet_id, DATE_FORMAT(expense_month, '%Y-%m')
    ) t
    GROUP BY outlet_id
)
SELECT
    ot.outlet_name,
    ROUND(c.contrib_per_order, 2)                               AS contribution_per_order,
    ROUND(x.avg_monthly_fixed, 0)                               AS monthly_fixed_cost,
    ROUND(x.avg_monthly_fixed / c.contrib_per_order, 0)         AS breakeven_orders_month,
    ROUND(x.avg_monthly_fixed / c.contrib_per_order / 30.44, 1) AS breakeven_orders_day
FROM contrib    c
JOIN fixed_cost x  ON c.outlet_id = x.outlet_id
JOIN outlets    ot ON c.outlet_id = ot.outlet_id
ORDER BY breakeven_orders_day;


/*
--------------------------------------------------------------------------------
D4. WEEKDAY VS WEEKEND: WHERE THE PROFIT ACTUALLY CAME FROM.
    This is the headline finding. Nobody told you this; the data says it.
--------------------------------------------------------------------------------        
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
),
daily AS (
    SELECT
        DATE(o.order_datetime)                                  AS d,
        CASE WHEN WEEKDAY(o.order_datetime) >= 5 THEN 'Weekend'
             ELSE 'Weekday' END                                 AS day_type,
        COUNT(*)                                                AS orders,
        SUM(o.gross_order_value - o.restaurant_funded_discount
            - o.commission_amount - o.other_deductions
            - o.refund_amount - f.food_cost - o.packaging_cost) AS contribution
    FROM orders o
    JOIN order_food f ON o.order_id = f.order_id
    WHERE o.order_status <> 'cancelled'
      AND o.outlet_id = 1
      AND o.order_datetime >= '2019-01-01' AND o.order_datetime < '2020-03-01'
    GROUP BY DATE(o.order_datetime), CASE WHEN WEEKDAY(o.order_datetime) >= 5
                                          THEN 'Weekend' ELSE 'Weekday' END
)
SELECT
    day_type,
    COUNT(*)                                                    AS days,
    ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)            AS pct_of_days,
    ROUND(AVG(orders), 1)                                       AS avg_orders_per_day,
    ROUND(AVG(contribution), 0)                                 AS avg_contribution_per_day,
    ROUND(SUM(contribution), 0)                                 AS total_contribution,
    ROUND(100 * SUM(contribution) / SUM(SUM(contribution)) OVER (), 1)
                                                                AS pct_of_contribution
FROM daily
GROUP BY day_type;


/*
--------------------------------------------------------------------------------
D5. CUMULATIVE PROFITABILITY: the closure, visible.
    Window function: SUM(...) OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED
    PRECEDING AND CURRENT ROW) is a running total. The frame clause is what
    makes it cumulative rather than a repeated grand total.
--------------------------------------------------------------------------------
*/

WITH order_food AS (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
),
monthly AS (
    SELECT
        DATE_FORMAT(o.order_datetime, '%Y-%m')                  AS ym,
        SUM(o.gross_order_value - o.restaurant_funded_discount
            - o.commission_amount - o.other_deductions
            - o.refund_amount - f.food_cost - o.packaging_cost) AS contribution
    FROM orders o
    JOIN order_food f ON o.order_id = f.order_id
    WHERE o.order_status <> 'cancelled'
    GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m')
),
costs AS (
    SELECT DATE_FORMAT(expense_month, '%Y-%m') AS ym, SUM(amount) AS opex
    FROM expenses GROUP BY DATE_FORMAT(expense_month, '%Y-%m')
),
net AS (
    SELECT m.ym, ROUND(m.contribution - c.opex, 0) AS monthly_net
    FROM monthly m JOIN costs c ON m.ym = c.ym
)
SELECT
    ym,
    monthly_net,
    SUM(monthly_net) OVER (ORDER BY ym
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)       AS cumulative_net
FROM net
ORDER BY ym;

/*
--------------------------------------------------------------------------------
D6. MONTH-OVER-MONTH AND YEAR-OVER-YEAR CHANGE.
    Window function: LAG(x, n) returns the value from n rows earlier in the
    ordered partition. LAG(gross, 12) gives the same month last year.
--------------------------------------------------------------------------------
*/

WITH monthly AS (
    SELECT DATE_FORMAT(order_datetime, '%Y-%m') AS ym,
           SUM(gross_order_value)               AS gross,
           COUNT(*)                             AS orders
    FROM orders WHERE order_status <> 'cancelled'
    GROUP BY DATE_FORMAT(order_datetime, '%Y-%m')
)
SELECT
    ym,
    orders,
    ROUND(gross, 0)                                             AS gross,
    ROUND(100 * (gross - LAG(gross, 1)  OVER (ORDER BY ym))
              / LAG(gross, 1)  OVER (ORDER BY ym), 1)           AS mom_pct,
    ROUND(100 * (gross - LAG(gross, 12) OVER (ORDER BY ym))
              / LAG(gross, 12) OVER (ORDER BY ym), 1)           AS yoy_pct
FROM monthly
ORDER BY ym;


