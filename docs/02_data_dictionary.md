# Data Dictionary

Database: `etable_analytics` — MySQL 8.0, InnoDB, utf8mb4

> Column types, keys, null counts and check constraints below are generated from `sql/01_schema.sql` and the source CSVs by `tools/gen_data_dictionary.py`. All descriptions are written by hand.
>
> **Four columns are commonly misread. Each is flagged in place:** `orders.customer_delivery_fee` (customer-paid, never a restaurant cost), `order_items.unit_food_cost` (point-in-time snapshot), `menu_items.base_food_cost_pct` (percentage of base price, not aggregator price), and `expenses.outlet_id` (NULL means company-level, not missing).

## Table overview

|Table|Grain|Rows|Columns|
|-|-|-:|-:|
|`outlets`|one row per physical outlet|3|9|
|`platforms`|one row per platform per commercial-terms period|4|7|
|`menu_items`|one row per menu item|28|8|
|`menu_item_prices`|one row per item x platform x effective price period|378|7|
|`customers`|one row per masked, platform-scoped customer reference|43,838|5|
|`orders`|one row per order|65,390|23|
|`order_items`|one row per line item within an order|111,523|8|
|`promotions`|one row per promotional campaign|66|9|
|`item_availability`|one row per item x outlet x date|59,465|7|
|`wastage`|one row per outlet x date x waste type|14,604|7|
|`expenses`|one row per outlet x month x expense category (outlet_id NULL = company-level)|1,101|6|
|`daily_operations`|one row per outlet x date|3,651|6|
|**Total**||**300,051**||

---
## `outlets`

**Grain:** one row per physical outlet **Rows:** 3 **Primary key:** `outlet_id`

**Why this table exists:** Stores the physical outlet structure needed to analyze outlet-level revenue, contribution, fixed costs, breakeven, and expansion performance against the project's Tier 1 operating-cost assumptions.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`outlet_id`|INT|N|PK|0|Unique identifier for each physical kitchen outlet.|
|`outlet_name`|VARCHAR(60)|N|—|0|Business name used to identify the outlet in analysis and reporting.|
|`outlet_type`|ENUM('hub','spoke')|N|—|0|Identifies whether the outlet is the central hub or a spoke location in the hub-and-spoke operating model.|
|`locality`|VARCHAR(60)|N|—|0|Local area in which the physical outlet operates; two of the three locality values are synthetic assumptions in this reconstruction.|
|`opening_date`|DATE|N|—|0|Date from which the outlet is treated as operational in the dataset.|
|`closing_date`|DATE|Y|—|0|Date on which the outlet ceased operating; NULL indicates that no closing date is recorded.|
|`monthly_rent`|DECIMAL(10,2)|N|—|0|Monthly rent assigned to the outlet and used as an outlet-level fixed cost.|
|`monthly_utilities`|DECIMAL(10,2)|N|—|0|Monthly utilities cost assigned to the outlet and used as an outlet-level fixed cost.|
|`status`|ENUM('active','restructured','closed')|N|—|0|Operational status of the outlet used to distinguish its role during the modeled period.|

**Check constraints:**

* `CONSTRAINT chk_outlet_dates CHECK (closing_date IS NULL OR closing_date >= opening_date)`
* `CONSTRAINT chk_outlet_rent  CHECK (monthly_rent >= 0 AND monthly_utilities >= 0)`

---
## `platforms`

**Grain:** one row per platform per commercial-terms period **Rows:** 4 **Primary key:** `platform_id`

**Why this table exists:** Stores aggregator commercial terms so platform-level revenue, commission, deductions, and platform-history analysis can be calculated consistently against the project's Tier 1 commission and platform-history assumptions.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`platform_id`|INT|N|PK|0|Unique identifier for each delivery platform terms record.|
|`platform_name`|VARCHAR(40)|N|UQ|0|Name of the delivery aggregator represented by the record.|
|`commission_rate`|DECIMAL(5,4)|N|—|0|Proportion of the applicable order value charged by the platform as commission; the project's Tier 1 assumption fixes the restaurant commission at 28%.|
|`customer_delivery_rate`|DECIMAL(5,4)|N|—|0|Proportion used to represent the customer delivery charge collected by the platform; this is paid by the customer to the platform and is not restaurant revenue.|
|`other_deduction_rate`|DECIMAL(5,4)|N|—|0|Proportion representing payment processing and other platform deductions applied to the order settlement; it is separate from commission.|
|`active_from`|DATE|N|UQ|0|Date from which this platform's commercial terms are treated as effective in the dataset.|
|`active_to`|DATE|Y|—|2 (50%)|Date through which these platform terms are treated as effective; NULL means the terms have no recorded end date.|

**Check constraints:**

* `CONSTRAINT chk_platform_rates CHECK ( commission_rate BETWEEN 0 AND 1 AND customer_delivery_rate BETWEEN 0 AND 1 AND other_deduction_rate BETWEEN 0 AND 1)`
* `CONSTRAINT chk_platform_dates CHECK (active_to IS NULL OR active_to >= active_from)`

---
## `menu_items`

**Grain:** one row per menu item **Rows:** 28 **Primary key:** `menu_item_id`

**Why this table exists:** Defines the menu items and their food-cost characteristics needed for item-level margin, popularity, category, and menu-performance analysis.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`menu_item_id`|INT|N|PK|0|Unique identifier for each menu item.|
|`item_name`|VARCHAR(80)|N|UQ|0|Business name of the menu item used to identify it across item-level analysis.|
|`category`|ENUM('Biryani','Starter','Curry','Meals', 'Beverage','Add-on','Dessert')|N|—|0|Menu category used to compare item performance within broad product groups.|
|`veg_nonveg`|ENUM('Veg','Non-veg')|N|—|0|Indicates whether the menu item is vegetarian or non-vegetarian.|
|`base_food_cost_pct`|DECIMAL(6,4)|N|—|0|Food cost as a proportion of the item's base/takeaway price; this is not calculated from the aggregator-listed price.|
|`launch_date`|DATE|N|—|0|Date from which the menu item is treated as available in the modeled menu.|
|`delist_date`|DATE|Y|—|26 (93%)|Date after which the menu item is treated as delisted; NULL means the item remained listed through the modeled period.|
|`is_combo`|TINYINT(1)|N|—|0|Indicates whether the menu item represents a combo rather than an individual standalone item.|

**Check constraints:**

* `CONSTRAINT chk_item_fc CHECK (base_food_cost_pct > 0 AND base_food_cost_pct < 1)`
* `CONSTRAINT chk_item_dates CHECK (delist_date IS NULL OR delist_date >= launch_date)`

---
## `menu_item_prices`

**Grain:** one row per item x platform x effective price period **Rows:** 378 **Primary key:** `price_id`

**Why this table exists:** Stores platform-specific menu prices over time so order economics can account for the difference between base/takeaway pricing and aggregator-listed pricing.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|:-:|-|
|`price_id`|INT|N|PK|0|Unique identifier for each menu-item pricing period.|
|`menu_item_id`|INT|N|FK UQ|0|Identifies the menu item to which this price record applies; references `menu_items.menu_item_id`.|
|`platform_id`|INT|N|FK UQ|0|Identifies the delivery platform for which this pricing record applies; references `platforms.platform_id`.|
|`base_price`|DECIMAL(8,2)|N|—|0|Base/takeaway price of the menu item before the aggregator listing premium.|
|`listed_price`|DECIMAL(8,2)|N|—|0|Price displayed to customers on the delivery platform; it may be higher than the base/takeaway price because of the modeled aggregator premium.|
|`effective_from`|DATE|N|UQ|0|Date from which this item-platform price becomes effective.|
|`effective_to`|DATE|Y|—|0|Date through which this item-platform price remains effective; NULL indicates no recorded end date.|

**Foreign keys:** `menu_item_id` → `menu_items.menu_item_id`, `platform_id` → `platforms.platform_id`

**Check constraints:**

* `CONSTRAINT chk_price_positive CHECK (base_price > 0 AND listed_price > 0)`
* `CONSTRAINT chk_price_premium CHECK (listed_price >= base_price)`

\--

## `customers`

**Grain:** one row per masked, platform-scoped customer reference **Rows:** 43,838 **Primary key:** `customer_id`

**Why this table exists:** Provides a privacy-preserving customer reference for platform-scoped order and retention analysis without exposing real customer identity.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`customer_id`|INT|N|PK|0|Unique internal identifier for a customer reference in the reconstructed dataset.|
|`platform_id`|INT|N|FK UQ|0|Identifies the delivery platform to which the customer reference belongs; customer identity is intentionally scoped to that platform.|
|`platform_customer_ref`|VARCHAR(40)|N|UQ|0|Masked customer reference supplied within a platform scope; it is not a real-world customer identifier.|
|`first_order_date`|DATE|N|—|0|Date of the customer's first modeled order on the associated platform.|
|`delivery_area`|VARCHAR(60)|Y|—|0|Modeled delivery locality associated with the customer reference; NULL means no delivery area is recorded.|

**Foreign keys:** `platform_id` → `platforms.platform_id`

---
## `orders`

**Grain:** one row per order **Rows:** 65,390 **Primary key:** `order_id`

**Why this table exists:** Serves as the central order-level fact table for revenue, contribution, platform economics, service performance, basket, and outlet analysis.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`order_id`|BIGINT|N|PK|0|Unique identifier for each modeled customer order.|
|`customer_id`|INT|N|FK|0|Identifies the masked customer reference associated with the order; references `customers.customer_id`.|
|`outlet_id`|INT|N|FK|0|Identifies the physical outlet responsible for fulfilling the order; references `outlets.outlet_id`.|
|`platform_id`|INT|N|FK|0|Identifies the delivery platform through which the order was received; references `platforms.platform_id`.|
|`order_datetime`|DATETIME|N|—|0|Date and time at which the order was placed, used for time-based volume, day-type, monthly, and operational analysis.|
|`order_status`|ENUM('completed','cancelled', 'refunded_partial','refunded_full')|N|—|0|Final modeled status of the order, distinguishing completed orders from cancelled and partially or fully refunded orders.|
|`cancellation_reason`|VARCHAR(60)|Y|—|63,529 (97%)|Reason recorded when an order was cancelled; NULL is expected for orders where no cancellation reason applies or is recorded.|
|`gross_order_value`|DECIMAL(10,2)|N|—|0|Gross food/order value before modeled discounts; this is the starting order value used in the restaurant economics.|
|`platform_funded_discount`|DECIMAL(10,2)|N|—|0|Portion of the customer-visible discount funded by the delivery platform; it does not reduce the restaurant's realised revenue or count as a restaurant-funded discount.|
|`restaurant_funded_discount`|DECIMAL(10,2)|N|—|0|Portion of the customer-visible discount funded by the restaurant; this is a restaurant cost and must be distinguished from platform-funded discounts.|
|`net_order_value`|DECIMAL(10,2)|N|—|0|Order value remaining after the modeled customer-facing discounts; use the funding fields separately when analysing the restaurant's actual economics.|
|`commission_amount`|DECIMAL(10,2)|N|—|0|Platform commission amount recorded for the order; this is a point-in-time settlement snapshot rather than a rate that should be recalculated from current platform terms.|
|`other_deductions`|DECIMAL(10,2)|N|—|0|Non-commission deductions applied to the restaurant settlement, such as modeled payment-processing or other platform deductions.|
|`customer_delivery_fee`|DECIMAL(10,2)|N|—|0|Delivery fee paid by the customer to the platform; it is not restaurant revenue and must not be deducted from restaurant revenue as a restaurant cost.|
|`refund_amount`|DECIMAL(10,2)|N|—|0|Amount refunded against the order and therefore relevant when reconciling the final restaurant settlement.|
|`restaurant_settlement`|DECIMAL(10,2)|N|—|0|Modeled amount settled to the restaurant after applicable platform deductions, discounts, and refunds represented in the dataset.|
|`packaging_cost`|DECIMAL(8,2)|N|—|0|Packaging cost assigned to the order; the project's Tier 1 assumption fixes this at ₹15 per order.|
|`promised_minutes`|SMALLINT|Y|—|0|Promised service time in minutes, where a platform/order-level promise is recorded; NULL means no promise is recorded.|
|`prep_minutes`|SMALLINT|Y|—|0|Time in minutes spent preparing the order in the kitchen; used to evaluate operational performance and capacity pressure.|
|`delivery_minutes`|SMALLINT|Y|—|0|Modeled delivery time in minutes after preparation; used in service-time analysis.|
|`rating`|TINYINT|Y|—|22,280 (34%)|Customer rating on a 1–5 scale; NULL means the customer did not provide a rating and must not be treated as a zero rating.|
|`basket_type`|VARCHAR(30)|Y|—|0|Modeled classification of the order's basket size/type, used for analysing differences between smaller and larger multi-item baskets.|
|`is_combo_order`|TINYINT(1)|N|—|0|Indicates whether the order contains a combo item/order configuration under the dataset's modeled classification.|

**Foreign keys:** `customer_id` → `customers.customer_id`, `outlet_id` → `outlets.outlet_id`, `platform_id` → `platforms.platform_id`

**Check constraints:**

* `CONSTRAINT chk_orders_gross CHECK (gross_order_value > 0)`
* `CONSTRAINT chk_orders_rating CHECK (rating IS NULL OR rating BETWEEN 1 AND 5)`
* `CONSTRAINT chk_orders_disc CHECK (platform_funded_discount >= 0 AND restaurant_funded_discount >= 0)`

---
## `order_items`

**Grain:** one row per line item within an order **Rows:** 111,523 **Primary key:** `order_item_id`

**Why this table exists:** Provides the item-level quantities, prices, discounts, and snapshotted food costs needed to calculate item contribution and analyse menu-item economics.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`order_item_id`|BIGINT|N|PK|0|Unique identifier for each line item within an order.|
|`order_id`|BIGINT|N|FK|0|Identifies the order containing this line item; references `orders.order_id`.|
|`menu_item_id`|INT|N|FK|0|Identifies the menu item represented by this line item; references `menu_items.menu_item_id`.|
|`quantity`|SMALLINT|N|—|0|Number of units of the menu item included in the line item.|
|`unit_listed_price`|DECIMAL(8,2)|N|—|0|Price per unit at the time of the order based on the applicable listed delivery-platform price.|
|`unit_food_cost`|DECIMAL(8,2)|N|—|0|Food cost per unit captured at order time; this is a point-in-time cost snapshot and should not be replaced with the item's current food cost when analysing historical orders.|
|`item_discount`|DECIMAL(8,2)|N|—|0|Discount amount allocated to this line item for the order.|
|`line_total`|DECIMAL(10,2)|N|—|0|Total modeled value of the line item after applying the line-level discount represented in the dataset.|

**Foreign keys:** `order_id` → `orders.order_id`, `menu_item_id` → `menu_items.menu_item_id`

**Check constraints:**

* `CONSTRAINT chk_oi_qty CHECK (quantity > 0)`
* `CONSTRAINT chk_oi_cost CHECK (unit_food_cost >= 0 AND unit_listed_price > 0)`

---
## `promotions`

**Grain:** one row per promotional campaign **Rows:** 66 **Primary key:** `promotion_id`

**Why this table exists:** Defines the promotional campaigns and their restaurant-funding terms needed to understand the discount structure behind customer-visible promotions.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|:-:|-|
|`promotion_id`|INT|N|PK|0|Unique identifier for each modeled promotional campaign.|
|`platform_id`|INT|N|FK|0|Identifies the delivery platform on which the promotion was offered; references `platforms.platform_id`.|
|`promotion_name`|VARCHAR(80)|N|—|0|Name used to identify the promotional campaign in the reconstructed dataset.|
|`discount_type`|ENUM('flat','percentage','free_item','combo')|N|—|0|Mechanism used to represent the promotion, such as a fixed discount, percentage discount, free item, or combo offer.|
|`discount_value`|DECIMAL(8,2)|N|—|0|Nominal value associated with the promotion's discount mechanism; its interpretation depends on `discount_type`.|
|`min_order_value`|DECIMAL(8,2)|Y|—|0|Minimum order value required for the promotion where such a threshold applies; NULL indicates no minimum order threshold is recorded.|
|`restaurant_funded_pct`|DECIMAL(5,4)|N|—|0|Proportion of the promotion's discount funding assigned to the restaurant; this identifies funding responsibility but does not by itself establish that the promotion was incrementally effective.|
|`start_date`|DATE|N|—|0|Date from which the promotional campaign is treated as active.|
|`end_date`|DATE|N|—|0|Date through which the promotional campaign is treated as active.|

**Foreign keys:** `platform_id` → `platforms.platform_id`

**Check constraints:**

* `CONSTRAINT chk_promo_funded CHECK (restaurant_funded_pct BETWEEN 0 AND 1)`
* `CONSTRAINT chk_promo_dates CHECK (end_date >= start_date)`

---
## `item_availability`

**Grain:** one row per item x outlet x date **Rows:** 59,465 **Primary key:** `availability_id`

**Why this table exists:** Captures daily item availability, batch preparation, stockouts, and estimated lost orders so the stockout-versus-wastage trade-off can be analysed at item and outlet level.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`availability_id`|BIGINT|N|PK|0|Unique identifier for each item-availability record.|
|`outlet_id`|INT|N|FK UQ|0|Identifies the physical outlet for which the item's daily availability is recorded; references `outlets.outlet_id`.|
|`menu_item_id`|INT|N|FK UQ|0|Identifies the menu item whose daily preparation and availability are being tracked; references `menu_items.menu_item_id`.|
|`availability_date`|DATE|N|UQ|0|Date on which the item's preparation and availability record applies.|
|`batch_prepared_qty`|SMALLINT|N|—|0|Quantity of the item prepared in the planned batch for that outlet and date; used to compare prepared volume with demand and stockout risk.|
|`sold_out_time`|TIME|Y|—|57,283 (96%)|Time at which the item was recorded as sold out; NULL means no sold-out time was recorded for that item-day.|
|`estimated_lost_orders`|SMALLINT|N|—|0|Estimated number of customer orders that could not be fulfilled because the item was unavailable; this is an operational estimate rather than an observed order count.|

**Foreign keys:** `outlet_id` → `outlets.outlet_id`, `menu_item_id` → `menu_items.menu_item_id`

**Check constraints:**

* `CONSTRAINT chk_avail_qty CHECK (batch_prepared_qty >= 0 AND estimated_lost_orders >= 0)`

---
## `wastage`

**Grain:** one row per outlet x date x waste type **Rows:** 14,604 **Primary key:** `wastage_id`

**Why this table exists:** Captures the quantity and estimated cost of food waste by outlet and waste type so production decisions can be evaluated against the project's wastage and stockout trade-offs.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`wastage_id`|BIGINT|N|PK|0|Unique identifier for each recorded wastage event or daily waste record.|
|`outlet_id`|INT|N|FK|0|Identifies the physical outlet where the waste was recorded; references `outlets.outlet_id`.|
|`wastage_date`|DATE|N|—|0|Date on which the wastage was recorded.|
|`waste_type`|ENUM('prep_waste','unsold_cooked', 'returned_order','spoilage')|N|—|0|Category identifying the operational source of the waste, distinguishing preparation waste, unsold cooked food, returned orders, and spoilage.|
|`quantity_kg`|DECIMAL(7,2)|N|—|0|Estimated quantity of food wasted, measured in kilograms.|
|`estimated_cost`|DECIMAL(10,2)|N|—|0|Estimated food cost associated with the recorded wastage; used to quantify the economic impact of waste.|
|`reason`|VARCHAR(80)|Y|—|0|Optional explanation for why the waste occurred, such as an operational or demand-related cause; NULL means no specific reason is recorded.|

**Foreign keys:** `outlet_id` → `outlets.outlet_id`

**Check constraints:**

* `CONSTRAINT chk_waste_qty CHECK (quantity_kg >= 0 AND estimated_cost >= 0)`

---
## `expenses`

**Grain:** one row per outlet x month x expense category (outlet_id NULL = company-level) **Rows:** 1,101 **Primary key:** `expense_id`

**Why this table exists:** Provides the monthly fixed, semi-variable, and variable cost structure needed for outlet-level profitability, cost-behaviour, and breakeven analysis.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`expense_id`|INT|N|PK|0|Unique identifier for each recorded expense line.|
|`outlet_id`|INT|Y|FK|141 (13%)|Identifies the outlet to which the expense is assigned; NULL deliberately represents a company-level cost that is not attributable to a single outlet.|
|`expense_month`|DATE|N|—|0|Month to which the expense applies, used for monthly cost and profitability analysis.|
|`expense_category`|ENUM('staff','rent','utilities','gas_consumables', 'procurement_travel','repairs','advertising', 'packaging_extra','compliance','founder_drawings', 'kitchen_rent')|N|—|0|Business category used to classify the expense for cost-structure, profitability, and breakeven analysis.|
|`amount`|DECIMAL(12,2)|N|—|0|Monetary amount of the expense for the recorded month and scope.|
|`cost_behaviour`|ENUM('fixed','semi_variable','variable')|N|—|0|Classification of how the expense behaves as operating volume changes; used to separate costs relevant to contribution and breakeven calculations.|

**Foreign keys:** `outlet_id` → `outlets.outlet_id`

**Check constraints:**

* `CONSTRAINT chk_exp_amount CHECK (amount >= 0)`

---
## `daily_operations`

**Grain:** one row per outlet x date **Rows:** 3,651 **Primary key:** `outlet_id`, `operation_date` *(natural composite key — no surrogate id)*

**Why this table exists:** Holds daily staffing, kitchen capacity, weather, and COVID-phase facts that are not derivable from `orders` or `wastage` and are needed for operational capacity and demand-shock analysis.

**3NF note:** order counts, preparation times and wastage quantities were in the first draft of this table and were deliberately removed. All three are derivable from `orders` and `wastage`, so storing them would breach third normal form and create update anomalies. What remains is genuinely non-derivable, which is why the table earns its place.

|Column|Type|Null|Key|Nulls in data|Description|
|-|-|:-:|:-:|-:|-|
|`outlet_id`|INT|N|PK FK|0|Identifies the physical outlet for the daily operational record; references `outlets.outlet_id`.|
|`operation_date`|DATE|N|PK|0|Date to which the outlet's operational conditions apply.|
|`staff_on_shift`|TINYINT|N|—|0|Number of staff assigned to the outlet on the recorded date; used to assess staffing against operational load.|
|`kitchen_capacity_orders`|SMALLINT|N|—|0|Modeled number of orders the kitchen can handle for the day under the recorded operating setup; used to assess capacity pressure.|
|`weather_flag`|ENUM('normal','rain','extreme')|Y|—|0|Daily weather condition classification used to analyse whether operating conditions coincided with changes in demand or service performance. Nullable in the schema but populated on every row in this dataset.|
|`covid_phase`|ENUM('pre','wave1','reopening','plateau', 'wave2','recovery','decline')|N|—|0|Business-period classification used to distinguish COVID-related demand and operating phases in the analysis.|

**Foreign keys:** `outlet_id` → `outlets.outlet_id`

**Check constraints:**

* `CONSTRAINT chk_ops_staff CHECK (staff_on_shift >= 0 AND kitchen_capacity_orders > 0)`

---