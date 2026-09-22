/*
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
MODULE G — QUERY OPTIMISATION
Techniques: EXPLAIN, index reasoning.
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
*/

USE etable_analytics;


/*
---------------------------------------------------------------------------------
G1. Baseline: read the plan for the heaviest query.
---------------------------------------------------------------------------------
*/

EXPLAIN ANALYZE
SELECT DATE_FORMAT(o.order_datetime, '%Y-%m') AS ym,
       COUNT(*), SUM(o.gross_order_value)
FROM orders o
WHERE o.outlet_id = 1
  AND o.order_datetime >= '2019-01-01' AND o.order_datetime < '2020-01-01'
GROUP BY DATE_FORMAT(o.order_datetime, '%Y-%m');

/*
---------------------------------------------------------------------------------
G2. Prove the composite index is being used.
---------------------------------------------------------------------------------
*/

SHOW INDEX FROM orders;

EXPLAIN
SELECT COUNT(*) FROM orders
WHERE outlet_id = 1 AND order_datetime >= '2019-06-01';

/*
---------------------------------------------------------------------------------
G3. Demonstrate why a function on an indexed column kills the index.
    SLOW: the function prevents index use on order_datetime.
---------------------------------------------------------------------------------
*/

EXPLAIN
SELECT COUNT(*) FROM orders WHERE YEAR(order_datetime) = 2019;

--     FAST: a range predicate is index-usable ("sargable").
EXPLAIN
SELECT COUNT(*) FROM orders
WHERE order_datetime >= '2019-01-01' AND order_datetime < '2020-01-01';

/*
---------------------------------------------------------------------------------
G4. A view that earns its place.
    order-level food cost is recomputed in almost every financial query.
    A view removes the repetition without hiding logic.
---------------------------------------------------------------------------------
*/

CREATE OR REPLACE VIEW v_order_economics AS
SELECT
    o.order_id,
    o.outlet_id,
    o.platform_id,
    o.customer_id,
    o.order_datetime,
    o.order_status,
    o.gross_order_value,
    o.platform_funded_discount,
    o.restaurant_funded_discount,
    o.commission_amount,
    o.other_deductions,
    o.refund_amount,
    o.packaging_cost,
    o.customer_delivery_fee,
    f.food_cost,
    (o.gross_order_value - o.restaurant_funded_discount - o.commission_amount
     - o.other_deductions - o.refund_amount - f.food_cost
     - o.packaging_cost)                                        AS contribution
FROM orders o
JOIN (
    SELECT order_id, SUM(unit_food_cost * quantity) AS food_cost
    FROM order_items GROUP BY order_id
) f ON o.order_id = f.order_id;

