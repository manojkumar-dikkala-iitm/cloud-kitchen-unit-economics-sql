-- =====================================================================
-- E-Table Foods — 02_load.sql : load the 12 CSVs
-- Target: MySQL 8.0+ / MySQL Workbench
-- =====================================================================
--
-- BEFORE YOU RUN THIS — two setup steps, both one-time:
--
-- STEP 1. Enable local file loading on the SERVER
--   In Workbench:  Server > Status and System Variables > search "local_infile"
--   If OFF, run:   SET GLOBAL local_infile = 1;
--   (If that errors, add local_infile=ON under [mysqld] in my.ini and restart.)
--
-- STEP 2. Enable it on the CLIENT (Workbench specifically)
--   Workbench does NOT send the client-side flag by default.
--   Database > Manage Connections > [your connection] > Advanced tab
--   In the "Others:" box add:      OPT_LOCAL_INFILE=1
--   Save, then reconnect.
--
--   Alternative if you would rather not touch connection settings:
--   run from the command line instead, which is more reliable:
--     mysql --local-infile=1 -u root -p etable_analytics < 02_load.sql
--
-- STEP 3. Set your CSV folder path below. Two rules on Windows:
--   - use FORWARD slashes, or doubled backslashes
--   - the path must be absolute
--   e.g.  C:/Users/you/etable/data/orders.csv
--
-- Then find-and-replace  __CSVDIR__  with your folder path.
-- =====================================================================

USE etable_analytics;

SET FOREIGN_KEY_CHECKS = 0;   -- load order independence; re-enabled at the end
SET UNIQUE_CHECKS = 0;
-- SET SQL_MODE = 'NO_ENGINE_SUBSTITUTION';

-- NOTE ON LINE ENDINGS: the CSVs are written with CRLF, hence
-- LINES TERMINATED BY '\r\n'. If you regenerate them on Linux/macOS,
-- change every occurrence to '\n'.

-- NOTE ON NULLS: the CSVs represent NULL as an empty field. Each nullable
-- column is therefore read into a @variable and converted with NULLIF.


-- ---------------------------------------------------------------- 1
-- LOAD DATA LOCAL INFILE '__CSVDIR__/outlets.csv'
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/outlets.csv'
INTO TABLE outlets
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(outlet_id, outlet_name, outlet_type, locality, opening_date,
 @closing_date, monthly_rent, monthly_utilities, status)
SET closing_date = NULLIF(@closing_date, '');


-- ---------------------------------------------------------------- 2
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/platforms.csv'
INTO TABLE platforms
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(platform_id, platform_name, commission_rate, customer_delivery_rate,
 other_deduction_rate, active_from, @active_to)
SET active_to = NULLIF(@active_to, '');


-- ---------------------------------------------------------------- 3
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/menu_items.csv'
INTO TABLE menu_items
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(menu_item_id, item_name, category, veg_nonveg, base_food_cost_pct,
 launch_date, @delist_date, is_combo)
SET delist_date = NULLIF(@delist_date, '');


-- ---------------------------------------------------------------- 4
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/menu_item_prices.csv'
INTO TABLE menu_item_prices
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(price_id, menu_item_id, platform_id, base_price, listed_price,
 effective_from, @effective_to)
SET effective_to = NULLIF(@effective_to, '');


-- ---------------------------------------------------------------- 5
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(customer_id, platform_id, platform_customer_ref, first_order_date,
 @delivery_area)
SET delivery_area = NULLIF(@delivery_area, '');


-- ---------------------------------------------------------------- 6
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/orders.csv'
INTO TABLE orders
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(order_id, customer_id, outlet_id, platform_id, order_datetime,
 order_status, @cancellation_reason, gross_order_value,
 platform_funded_discount, restaurant_funded_discount, net_order_value,
 commission_amount, other_deductions, customer_delivery_fee,
 refund_amount, restaurant_settlement, packaging_cost,
 @promised_minutes, @prep_minutes, @delivery_minutes, @rating, @basket_type,
 is_combo_order)
SET cancellation_reason = NULLIF(@cancellation_reason, ''),
    promised_minutes    = NULLIF(@promised_minutes, ''),
    prep_minutes        = NULLIF(@prep_minutes, ''),
    delivery_minutes    = NULLIF(@delivery_minutes, ''),
    rating              = NULLIF(@rating, ''),
    basket_type         = NULLIF(@basket_type, '');


-- ---------------------------------------------------------------- 7
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/order_items.csv'
INTO TABLE order_items
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(order_item_id, order_id, menu_item_id, quantity, unit_listed_price,
 unit_food_cost, item_discount, line_total);


-- ---------------------------------------------------------------- 8
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/promotions.csv'
INTO TABLE promotions
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(promotion_id, platform_id, promotion_name, discount_type, discount_value,
 @min_order_value, restaurant_funded_pct, start_date, end_date)
SET min_order_value = NULLIF(@min_order_value, '');


-- ---------------------------------------------------------------- 9
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/item_availability.csv'
INTO TABLE item_availability
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(availability_id, outlet_id, menu_item_id, availability_date,
 batch_prepared_qty, @sold_out_time, estimated_lost_orders)
SET sold_out_time = NULLIF(@sold_out_time, '');


-- ---------------------------------------------------------------- 10
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/wastage.csv'
INTO TABLE wastage
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(wastage_id, outlet_id, wastage_date, waste_type, quantity_kg,
 estimated_cost, @reason)
SET reason = NULLIF(@reason, '');


-- ---------------------------------------------------------------- 11
-- outlet_id is NULL for the 141 company-level rows
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/expenses.csv'
INTO TABLE expenses
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(expense_id, @outlet_id, expense_month, expense_category, amount,
 cost_behaviour)
SET outlet_id = NULLIF(@outlet_id, '');


-- ---------------------------------------------------------------- 12
LOAD DATA LOCAL INFILE 'C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data/daily_operations.csv'
INTO TABLE daily_operations
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\r\n'
IGNORE 1 LINES
(outlet_id, operation_date, staff_on_shift, kitchen_capacity_orders,
 @weather_flag, covid_phase)
SET weather_flag = NULLIF(@weather_flag, '');


-- =====================================================================
SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;

-- Confirm nothing was silently dropped. Any non-zero warning count here
-- means a row was truncated or coerced — investigate before analysing.
SHOW WARNINGS;
