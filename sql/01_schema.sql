-- =====================================================================
-- E-Table Foods — Cloud Kitchen Unit Economics
-- 01_schema.sql : database and table definitions
-- Target: MySQL 8.0+ / MySQL Workbench
--
-- Run order: 01_schema.sql -> 02_load.sql -> 03_validate.sql
-- =====================================================================

DROP DATABASE IF EXISTS etable_analytics;
CREATE DATABASE etable_analytics
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_0900_ai_ci;
USE etable_analytics;

SET FOREIGN_KEY_CHECKS = 1;


-- =====================================================================
-- 1. outlets
-- Justified by: 1 -> 3 outlet expansion, per-outlet rent and utilities
-- Grain: one row per physical outlet
-- =====================================================================
CREATE TABLE outlets (
    outlet_id           INT             NOT NULL,
    outlet_name         VARCHAR(60)     NOT NULL,
    outlet_type         ENUM('hub','spoke') NOT NULL,
    locality            VARCHAR(60)     NOT NULL,
    opening_date        DATE            NOT NULL,
    closing_date        DATE            NULL,
    monthly_rent        DECIMAL(10,2)   NOT NULL,
    monthly_utilities   DECIMAL(10,2)   NOT NULL,
    status              ENUM('active','restructured','closed') NOT NULL,
    PRIMARY KEY (outlet_id),
    CONSTRAINT chk_outlet_dates CHECK (closing_date IS NULL OR closing_date >= opening_date),
    CONSTRAINT chk_outlet_rent  CHECK (monthly_rent >= 0 AND monthly_utilities >= 0)
) ENGINE=InnoDB;


-- =====================================================================
-- 2. platforms
-- Justified by: 28% commission (Tier 1), customer-paid delivery charge,
--   and the UberEats / Foodpanda shutdown dates.
-- Grain: one row per platform per commercial-terms period.
-- Effective-dating makes the shutdowns structural, not a convention.
-- NOTE: customer_delivery_rate is recorded for CUSTOMER-side analysis
--   only. It is never deducted from restaurant revenue.
-- =====================================================================
CREATE TABLE platforms (
    platform_id             INT             NOT NULL,
    platform_name           VARCHAR(40)     NOT NULL,
    commission_rate         DECIMAL(5,4)    NOT NULL,
    customer_delivery_rate  DECIMAL(5,4)    NOT NULL,
    other_deduction_rate    DECIMAL(5,4)    NOT NULL,
    active_from             DATE            NOT NULL,
    active_to               DATE            NULL,
    PRIMARY KEY (platform_id),
    UNIQUE KEY uq_platform_period (platform_name, active_from),
    CONSTRAINT chk_platform_rates CHECK (
        commission_rate BETWEEN 0 AND 1
        AND customer_delivery_rate BETWEEN 0 AND 1
        AND other_deduction_rate BETWEEN 0 AND 1),
    CONSTRAINT chk_platform_dates CHECK (active_to IS NULL OR active_to >= active_from)
) ENGINE=InnoDB;


-- =====================================================================
-- 3. menu_items
-- Justified by: 20-item menu, non-veg/biryani positioning, later veg
--   expansion, dessert discontinuation.
-- base_food_cost_pct is against BASE/takeaway price, never aggregator gross.
-- =====================================================================
CREATE TABLE menu_items (
    menu_item_id        INT             NOT NULL,
    item_name           VARCHAR(80)     NOT NULL,
    category            ENUM('Biryani','Starter','Curry','Meals',
                             'Beverage','Add-on','Dessert') NOT NULL,
    veg_nonveg          ENUM('Veg','Non-veg') NOT NULL,
    base_food_cost_pct  DECIMAL(6,4)    NOT NULL,
    launch_date         DATE            NOT NULL,
    delist_date         DATE            NULL,
    is_combo            TINYINT(1)      NOT NULL DEFAULT 0,
    PRIMARY KEY (menu_item_id),
    UNIQUE KEY uq_item_name (item_name),
    KEY idx_item_category (category),
    CONSTRAINT chk_item_fc    CHECK (base_food_cost_pct > 0 AND base_food_cost_pct < 1),
    CONSTRAINT chk_item_dates CHECK (delist_date IS NULL OR delist_date >= launch_date)
) ENGINE=InnoDB;


-- =====================================================================
-- 4. menu_item_prices
-- Justified by: platform-differential pricing (locked decision 0.7),
--   the ~15% aggregator premium, and 57 months of price history.
-- Grain: item x platform x effective period.
-- This table is why price is not an attribute of an item.
-- =====================================================================
CREATE TABLE menu_item_prices (
    price_id        INT             NOT NULL,
    menu_item_id    INT             NOT NULL,
    platform_id     INT             NOT NULL,
    base_price      DECIMAL(8,2)    NOT NULL,
    listed_price    DECIMAL(8,2)    NOT NULL,
    effective_from  DATE            NOT NULL,
    effective_to    DATE            NULL,
    PRIMARY KEY (price_id),
    UNIQUE KEY uq_price_period (menu_item_id, platform_id, effective_from),
    KEY idx_price_lookup (menu_item_id, platform_id, effective_from, effective_to),
    CONSTRAINT fk_price_item     FOREIGN KEY (menu_item_id) REFERENCES menu_items (menu_item_id),
    CONSTRAINT fk_price_platform FOREIGN KEY (platform_id)  REFERENCES platforms (platform_id),
    CONSTRAINT chk_price_positive CHECK (base_price > 0 AND listed_price > 0),
    CONSTRAINT chk_price_premium  CHECK (listed_price >= base_price)
) ENGINE=InnoDB;


-- =====================================================================
-- 5. customers
-- Justified by: repeat-order analysis under locked decision 0.3.
-- Aggregators never supplied customer PII to restaurants, so this holds
-- masked, PLATFORM-SCOPED references only. The composite unique key is
-- what prevents any implication of cross-platform identity resolution.
-- delivery_area is intentionally dirty (inconsistent spellings) — that is
-- the cleaning exercise, not a defect.
-- =====================================================================
CREATE TABLE customers (
    customer_id             INT             NOT NULL,
    platform_id             INT             NOT NULL,
    platform_customer_ref   VARCHAR(40)     NOT NULL,
    first_order_date        DATE            NOT NULL,
    delivery_area           VARCHAR(60)     NULL,
    PRIMARY KEY (customer_id),
    UNIQUE KEY uq_customer_platform_ref (platform_id, platform_customer_ref),
    KEY idx_customer_first_order (first_order_date),
    CONSTRAINT fk_customer_platform FOREIGN KEY (platform_id) REFERENCES platforms (platform_id)
) ENGINE=InnoDB;


-- =====================================================================
-- 6. orders
-- Justified by: ~65k orders, and the full settlement waterfall.
--
-- SETTLEMENT MODEL (Tier 1):
--   restaurant_settlement = gross_order_value
--                         - platform_funded_discount   (informational: platform bears it)
--                         - restaurant_funded_discount
--                         - commission_amount          (28%)
--                         - other_deductions
--                         - refund_amount
--   customer_delivery_fee is CUSTOMER-side and is NEVER subtracted.
--
-- Deliberate denormalisation: commission_amount and other_deductions are
-- stored as amounts rather than recomputed from platforms. Rates change
-- over time; storing the amount preserves the historical settlement and
-- avoids a temporal join on every profitability query. Standard practice
-- in financial fact tables.
-- =====================================================================
CREATE TABLE orders (
    order_id                    BIGINT          NOT NULL,
    customer_id                 INT             NOT NULL,
    outlet_id                   INT             NOT NULL,
    platform_id                 INT             NOT NULL,
    order_datetime              DATETIME        NOT NULL,
    order_status                ENUM('completed','cancelled',
                                     'refunded_partial','refunded_full') NOT NULL,
    cancellation_reason         VARCHAR(60)     NULL,
    gross_order_value           DECIMAL(10,2)   NOT NULL,
    platform_funded_discount    DECIMAL(10,2)   NOT NULL DEFAULT 0,
    restaurant_funded_discount  DECIMAL(10,2)   NOT NULL DEFAULT 0,
    net_order_value             DECIMAL(10,2)   NOT NULL,
    commission_amount           DECIMAL(10,2)   NOT NULL,
    other_deductions            DECIMAL(10,2)   NOT NULL DEFAULT 0,
    customer_delivery_fee       DECIMAL(10,2)   NOT NULL DEFAULT 0,
    refund_amount               DECIMAL(10,2)   NOT NULL DEFAULT 0,
    restaurant_settlement       DECIMAL(10,2)   NOT NULL,
    packaging_cost              DECIMAL(8,2)    NOT NULL DEFAULT 0,
    promised_minutes            SMALLINT        NULL,
    prep_minutes                SMALLINT        NULL,
    delivery_minutes            SMALLINT        NULL,
    rating                      TINYINT         NULL,
    basket_type                 VARCHAR(30)     NULL,
    is_combo_order              TINYINT(1)      NOT NULL DEFAULT 0,
    PRIMARY KEY (order_id),
    KEY idx_orders_datetime          (order_datetime),
    KEY idx_orders_outlet_datetime   (outlet_id, order_datetime),
    KEY idx_orders_platform_datetime (platform_id, order_datetime),
    KEY idx_orders_customer          (customer_id),
    KEY idx_orders_status            (order_status),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
    CONSTRAINT fk_orders_outlet   FOREIGN KEY (outlet_id)   REFERENCES outlets (outlet_id),
    CONSTRAINT fk_orders_platform FOREIGN KEY (platform_id) REFERENCES platforms (platform_id),
    CONSTRAINT chk_orders_gross   CHECK (gross_order_value > 0),
    CONSTRAINT chk_orders_rating  CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    CONSTRAINT chk_orders_disc    CHECK (platform_funded_discount >= 0
                                     AND restaurant_funded_discount >= 0)
) ENGINE=InnoDB;


-- =====================================================================
-- 7. order_items
-- Justified by: ~1.65 line items/order (~112k rows) and menu engineering.
-- Deliberate denormalisation: unit_food_cost is snapshotted at order time
-- so retrospective margin reflects the cost prevailing then, not now.
-- =====================================================================
CREATE TABLE order_items (
    order_item_id       BIGINT          NOT NULL,
    order_id            BIGINT          NOT NULL,
    menu_item_id        INT             NOT NULL,
    quantity            SMALLINT        NOT NULL,
    unit_listed_price   DECIMAL(8,2)    NOT NULL,
    unit_food_cost      DECIMAL(8,2)    NOT NULL,
    item_discount       DECIMAL(8,2)    NOT NULL DEFAULT 0,
    line_total          DECIMAL(10,2)   NOT NULL,
    PRIMARY KEY (order_item_id),
    KEY idx_oi_order (order_id),
    KEY idx_oi_item  (menu_item_id),
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id)     REFERENCES orders (order_id),
    CONSTRAINT fk_oi_item  FOREIGN KEY (menu_item_id) REFERENCES menu_items (menu_item_id),
    CONSTRAINT chk_oi_qty  CHECK (quantity > 0),
    CONSTRAINT chk_oi_cost CHECK (unit_food_cost >= 0 AND unit_listed_price > 0)
) ENGINE=InnoDB;


-- =====================================================================
-- 8. promotions
-- Justified by: ~60% discount incidence and the 70/30 funding split.
-- restaurant_funded_pct is the whole point: 0.00 = platform bears it,
-- 1.00 = restaurant bears it. Different P&L treatment entirely.
-- =====================================================================
CREATE TABLE promotions (
    promotion_id            INT             NOT NULL,
    platform_id             INT             NOT NULL,
    promotion_name          VARCHAR(80)     NOT NULL,
    discount_type           ENUM('flat','percentage','free_item','combo') NOT NULL,
    discount_value          DECIMAL(8,2)    NOT NULL,
    min_order_value         DECIMAL(8,2)    NULL,
    restaurant_funded_pct   DECIMAL(5,4)    NOT NULL,
    start_date              DATE            NOT NULL,
    end_date                DATE            NOT NULL,
    PRIMARY KEY (promotion_id),
    KEY idx_promo_window (start_date, end_date),
    KEY idx_promo_platform (platform_id),
    CONSTRAINT fk_promo_platform FOREIGN KEY (platform_id) REFERENCES platforms (platform_id),
    CONSTRAINT chk_promo_funded CHECK (restaurant_funded_pct BETWEEN 0 AND 1),
    CONSTRAINT chk_promo_dates  CHECK (end_date >= start_date)
) ENGINE=InnoDB;


-- =====================================================================
-- 9. item_availability
-- Justified by: limited-batch production and the 2-3% stockout rate.
-- This is where the stockout-versus-wastage trade-off becomes measurable.
-- sold_out_time NULL = the item never sold out that day.
-- =====================================================================
CREATE TABLE item_availability (
    availability_id         BIGINT      NOT NULL,
    outlet_id               INT         NOT NULL,
    menu_item_id            INT         NOT NULL,
    availability_date       DATE        NOT NULL,
    batch_prepared_qty      SMALLINT    NOT NULL,
    sold_out_time           TIME        NULL,
    estimated_lost_orders   SMALLINT    NOT NULL DEFAULT 0,
    PRIMARY KEY (availability_id),
    UNIQUE KEY uq_avail (outlet_id, menu_item_id, availability_date),
    KEY idx_avail_outlet_date (outlet_id, availability_date),
    KEY idx_avail_item (menu_item_id),
    CONSTRAINT fk_avail_outlet FOREIGN KEY (outlet_id)    REFERENCES outlets (outlet_id),
    CONSTRAINT fk_avail_item   FOREIGN KEY (menu_item_id) REFERENCES menu_items (menu_item_id),
    CONSTRAINT chk_avail_qty   CHECK (batch_prepared_qty >= 0 AND estimated_lost_orders >= 0)
) ENGINE=InnoDB;


-- =====================================================================
-- 10. wastage
-- Justified by: ~5-6 kg/week post-optimisation, the month-6 step change,
--   and returned food becoming unsellable.
-- Tier 1: wastage is never zero in any period.
-- =====================================================================
CREATE TABLE wastage (
    wastage_id      BIGINT          NOT NULL,
    outlet_id       INT             NOT NULL,
    wastage_date    DATE            NOT NULL,
    waste_type      ENUM('prep_waste','unsold_cooked',
                         'returned_order','spoilage') NOT NULL,
    quantity_kg     DECIMAL(7,2)    NOT NULL,
    estimated_cost  DECIMAL(10,2)   NOT NULL,
    reason          VARCHAR(80)     NULL,
    PRIMARY KEY (wastage_id),
    KEY idx_waste_outlet_date (outlet_id, wastage_date),
    KEY idx_waste_type (waste_type),
    CONSTRAINT fk_waste_outlet FOREIGN KEY (outlet_id) REFERENCES outlets (outlet_id),
    CONSTRAINT chk_waste_qty   CHECK (quantity_kg >= 0 AND estimated_cost >= 0)
) ENGINE=InnoDB;


-- =====================================================================
-- 11. expenses
-- Justified by: the fixed-cost base and the COVID fixed-vs-variable analysis.
--
-- outlet_id NULL = company-level cost (central kitchen rent, compliance,
-- founder drawings). 141 such rows.
--
-- cost_behaviour is not decoration. It turns the entire fixed-vs-variable
-- shock analysis into a GROUP BY instead of a hand-maintained CASE.
-- =====================================================================
CREATE TABLE expenses (
    expense_id          INT             NOT NULL,
    outlet_id           INT             NULL,
    expense_month       DATE            NOT NULL,
    expense_category    ENUM('staff','rent','utilities','gas_consumables',
                             'procurement_travel','repairs','advertising',
                             'packaging_extra','compliance','founder_drawings',
                             'kitchen_rent') NOT NULL,
    amount              DECIMAL(12,2)   NOT NULL,
    cost_behaviour      ENUM('fixed','semi_variable','variable') NOT NULL,
    PRIMARY KEY (expense_id),
    KEY idx_exp_outlet_month (outlet_id, expense_month),
    KEY idx_exp_month (expense_month),
    KEY idx_exp_category (expense_category),
    KEY idx_exp_behaviour (cost_behaviour),
    CONSTRAINT fk_exp_outlet FOREIGN KEY (outlet_id) REFERENCES outlets (outlet_id),
    CONSTRAINT chk_exp_amount CHECK (amount >= 0)
) ENGINE=InnoDB;


-- =====================================================================
-- 12. daily_operations
-- Justified by: staffing, capacity, weather and COVID phase — none of
-- which are derivable from any other table.
--
-- 3NF NOTE: order counts, prep times and wastage kg are DELIBERATELY
-- EXCLUDED here. All three are derivable from orders and wastage, so
-- storing them would breach 3NF and create update anomalies. What remains
-- is genuinely non-derivable. That is why this table earns its place.
--
-- Natural composite primary key; no surrogate needed.
-- =====================================================================
CREATE TABLE daily_operations (
    outlet_id               INT         NOT NULL,
    operation_date          DATE        NOT NULL,
    staff_on_shift          TINYINT     NOT NULL,
    kitchen_capacity_orders SMALLINT    NOT NULL,
    weather_flag            ENUM('normal','rain','extreme') NULL,
    covid_phase             ENUM('pre','wave1','reopening','plateau',
                                 'wave2','recovery','decline') NOT NULL,
    PRIMARY KEY (outlet_id, operation_date),
    KEY idx_ops_date (operation_date),
    KEY idx_ops_phase (covid_phase),
    CONSTRAINT fk_ops_outlet FOREIGN KEY (outlet_id) REFERENCES outlets (outlet_id),
    CONSTRAINT chk_ops_staff CHECK (staff_on_shift >= 0 AND kitchen_capacity_orders > 0)
) ENGINE=InnoDB;
