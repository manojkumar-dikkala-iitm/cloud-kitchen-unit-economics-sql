# Entity-Relationship Diagram

## ER diagram

![E-Table Analytics Entity-Relationship Diagram](er_diagram.png)

The diagram represents the relational structure of the reconstructed E-Table Foods transactional system. The database contains 12 tables covering orders, customers, outlets, platforms, menu items, pricing, promotions, inventory availability, wastage, expenses and daily operating conditions.

## Relationship overview

```text
                         ┌──────────────┐
                         │  platforms   │
                         └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌──────────────┐       ┌──────────────┐
             │   customers  │       │  promotions  │
             └──────┬───────┘       └──────────────┘
                    │
                    │
                    ▼
             ┌────────────────────┐
             │       orders       │
             └──────┬─────┬───────┘
                    │     │
          ┌─────────┘     └──────────────┐
          ▼                              ▼
   ┌──────────────┐              ┌────────────────┐
   │ order_items  │              │    outlets     │
   └──────┬───────┘              └───────┬────────┘
          │                              │
          ▼                              ├─────────────────────┐
   ┌──────────────┐                      │                     │
   │  menu_items  │                      ▼                     ▼
   └──────┬───────┘              ┌────────────────┐    ┌──────────────┐
          │                       │item_availability│   │    wastage    │
          ▼                       └────────────────┘    └──────────────┘
   ┌───────────────────┐
   │menu_item_prices   │
   └─────────┬─────────┘
             │
             └─────────────── platforms

                         ┌──────────────────┐
                         │     expenses     │
                         └────────┬─────────┘
                                  │
                               outlets

                         ┌──────────────────┐
                         │daily_operations  │
                         └────────┬─────────┘
                                  │
                               outlets
```

## Table relationships

### `outlets`

One outlet can have many:

- `orders`
- `item_availability` records
- `wastage` records
- `expenses` records
- `daily_operations` records

`outlets.outlet_id` is therefore referenced as a foreign key by these tables.

### `platforms`

One platform can have many:

- `customers`
- `orders`
- `promotions`
- `menu_item_prices`

`platforms.platform_id` identifies the aggregator associated with these records.

### `customers`

One platform-scoped customer reference can place many orders.

`customers.customer_id` → `orders.customer_id`

The customer entity is deliberately platform-scoped. Customer identity is masked and there is no cross-platform identity resolution.

### `orders`

`orders` is the central order-level fact table.

Each order belongs to:

- one customer reference
- one outlet
- one platform

An order can contain multiple rows in `order_items`.

`orders.order_id` → `order_items.order_id`

### `order_items`

Each order can contain multiple line items.

Each line item refers to one menu item through:

`order_items.menu_item_id` → `menu_items.menu_item_id`

This table provides the item-level quantity, listed price, discount and point-in-time food-cost snapshot required for menu and contribution analysis.

### `menu_items`

One menu item can have:

- many historical/platform-specific prices in `menu_item_prices`
- many order lines in `order_items`
- many availability records in `item_availability`

### `menu_item_prices`

Pricing is intentionally modelled at:

**menu item × platform × effective period**

rather than stored directly on `menu_items`.

This preserves platform-differential pricing and historical price changes across the modeled period.

### `promotions`

Each promotion belongs to one platform.

`promotions.platform_id` → `platforms.platform_id`

The table stores the campaign definition and restaurant-funding terms used to understand promotional economics.

### `item_availability`

Each record represents:

**one menu item × one outlet × one date**

It captures batch preparation, sell-out time and estimated lost orders so stockout economics can be compared with wastage.

### `wastage`

Each record represents:

**one outlet × one date × one waste type**

It captures quantity and estimated cost of food waste for operational and inventory analysis.

### `expenses`

Expenses can belong either to:

- a specific outlet, through `outlet_id`
- the company as a whole, when `outlet_id` is NULL

This allows the model to distinguish outlet-level profitability from company-level costs such as kitchen rent, compliance and founder drawings.

### `daily_operations`

Each record represents:

**one outlet × one operating date**

It stores staffing, kitchen capacity, weather and COVID phase information that cannot be reliably derived from the order or wastage tables.

---

## Normalisation and design decisions

The schema is designed in **third normal form (3NF)** for the transactional and reference data.

Entities are separated where attributes belong to different business concepts, and foreign keys are used to represent relationships rather than repeating descriptive attributes across transactional rows.

### Deliberate point-in-time snapshots

Two fields are intentionally stored at transaction time rather than recalculated from current reference data.

**`orders.commission_amount`**

The commission amount is stored on the order because historical platform commercial terms can change. Recalculating historical commission using a current platform rate could alter the economics of an old order.

**`order_items.unit_food_cost`**

Food cost is stored on the order-item row because historical contribution should remain stable even if the current food cost of the menu item changes later.

These are deliberate financial snapshots rather than accidental denormalisation.

## Why `daily_operations` exists separately

Some operational facts cannot be derived from transactional data.

Order count, preparation time and wastage are already represented elsewhere and therefore are not duplicated in `daily_operations`.

The table instead stores:

- staff on shift
- kitchen capacity
- weather condition
- COVID operating phase

This avoids unnecessary duplication while preserving the operational context required for capacity and COVID analysis.

## Central analytical path

The main analytical path through the schema is:

```text
customers
     │
     ▼
   orders ─────────────── outlets
     │                     │
     ▼                     ├── item_availability
order_items                ├── wastage
     │                     ├── expenses
     ▼                     └── daily_operations
menu_items
     │
     ▼
menu_item_prices
     │
     ▼
platforms
```

The order and order-item relationship forms the central transactional path. The remaining tables provide the commercial, product, customer and operational context needed to analyse unit economics.

## Related documentation

- [Data Dictionary](02_data_dictionary.md)
- [Assumptions Log](04_assumptions_log.md)
- [SQL Analysis](../sql/)
- [Project README](../README.md)