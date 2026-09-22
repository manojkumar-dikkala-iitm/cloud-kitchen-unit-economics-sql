"""
E-Table Foods — Phase 3B DATA VALIDATION (pre-MySQL gate)

Seven layers. Run this before touching MySQL. Zero ERRORS required to proceed.

NOTE ON NUMBERING: this is Phase 3B in the project roadmap, not "Phase 5".
Phase 5 is SQL Analytics. Keeping the numbering straight matters because the
commit history and documentation reference it.

WHAT THIS SCRIPT DELIBERATELY DOES NOT CHECK, AND WHY
  - orders.promotion_id        : does not exist. Discounts are stored as
                                 AMOUNTS (platform_funded_discount /
                                 restaurant_funded_discount) because an order
                                 can be touched by stacked promotions and
                                 because the amount must be preserved
                                 historically. A single FK to promotions cannot
                                 represent that.
  - wastage.menu_item_id       : does not exist. Wastage grain is
                                 outlet x date x waste_type. Prep waste and
                                 spoilage are not attributable to one item.
  - daily_operations.operation_id : does not exist. That table has a NATURAL
                                 composite primary key (outlet_id,
                                 operation_date). Adding a surrogate key to a
                                 table that already has a unique natural key is
                                 a schema regression, not a fix.
  - commission = net x rate    : WRONG. Commission is 28% of GROSS (Tier 1).
                                 Measured against net it varies 25-45% and is
                                 not a constant. This script asserts the
                                 correct basis.

NULLABLE FOREIGN KEYS
  expenses.outlet_id is NULL for company-level costs (central kitchen rent,
  compliance, founder drawings) — 141 rows. A NULL FK is valid. The orphan test
  must therefore exclude NULLs before the isin() check, because pandas treats
  NaN as "not in" any list.
"""

from pathlib import Path
import sys
import pandas as pd

# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

MONEY_TOL = 0.05          # rupee tolerance for reconciliation (rounding)
RATE_TOL = 0.0005         # tolerance on commission rate

EXPECTED_ROW_COUNTS = {
    "outlets": 3,
    "platforms": 4,
    "menu_items": 28,
    "menu_item_prices": 378,
    "customers": 43838,
    "orders": 65390,
    "order_items": 111523,
    "promotions": 66,
    "item_availability": 59465,
    "wastage": 14604,
    "expenses": 1101,
    "daily_operations": 3651,
}

# Primary keys AS ACTUALLY DESIGNED. daily_operations is composite.
PRIMARY_KEYS = {
    "outlets": ["outlet_id"],
    "platforms": ["platform_id"],
    "menu_items": ["menu_item_id"],
    "menu_item_prices": ["price_id"],
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "order_items": ["order_item_id"],
    "promotions": ["promotion_id"],
    "item_availability": ["availability_id"],
    "wastage": ["wastage_id"],
    "expenses": ["expense_id"],
    "daily_operations": ["outlet_id", "operation_date"],
}

# Uniqueness constraints beyond the primary key
UNIQUE_KEYS = {
    "customers": ["platform_id", "platform_customer_ref"],
    "menu_item_prices": ["menu_item_id", "platform_id", "effective_from"],
    "item_availability": ["outlet_id", "menu_item_id", "availability_date"],
    "menu_items": ["item_name"],
}

REQUIRED_COLUMNS = {
    "orders": ["order_id", "customer_id", "outlet_id", "platform_id",
               "order_datetime", "order_status", "gross_order_value",
               "platform_funded_discount", "restaurant_funded_discount",
               "net_order_value", "commission_amount", "other_deductions",
               "customer_delivery_fee", "refund_amount",
               "restaurant_settlement", "packaging_cost"],
    "order_items": ["order_item_id", "order_id", "menu_item_id", "quantity",
                    "unit_listed_price", "unit_food_cost", "item_discount",
                    "line_total"],
    "expenses": ["expense_id", "outlet_id", "expense_month",
                 "expense_category", "amount", "cost_behaviour"],
    "daily_operations": ["outlet_id", "operation_date", "staff_on_shift",
                         "kitchen_capacity_orders", "covid_phase"],
}

# child_table, child_col, parent_table, parent_col, nullable
FOREIGN_KEYS = [
    ("orders", "customer_id", "customers", "customer_id", False),
    ("orders", "outlet_id", "outlets", "outlet_id", False),
    ("orders", "platform_id", "platforms", "platform_id", False),
    ("order_items", "order_id", "orders", "order_id", False),
    ("order_items", "menu_item_id", "menu_items", "menu_item_id", False),
    ("customers", "platform_id", "platforms", "platform_id", False),
    ("menu_item_prices", "menu_item_id", "menu_items", "menu_item_id", False),
    ("menu_item_prices", "platform_id", "platforms", "platform_id", False),
    ("promotions", "platform_id", "platforms", "platform_id", False),
    ("item_availability", "outlet_id", "outlets", "outlet_id", False),
    ("item_availability", "menu_item_id", "menu_items", "menu_item_id", False),
    ("wastage", "outlet_id", "outlets", "outlet_id", False),
    ("expenses", "outlet_id", "outlets", "outlet_id", True),   # NULL = company-level
    ("daily_operations", "outlet_id", "outlets", "outlet_id", False),
]

# Enumerated domains, enforced as ENUM in the MySQL schema
ENUM_DOMAINS = {
    ("outlets", "outlet_type"): {"hub", "spoke"},
    ("outlets", "status"): {"active", "restructured", "closed"},
    ("menu_items", "category"): {"Biryani", "Starter", "Curry", "Meals",
                                 "Beverage", "Add-on", "Dessert"},
    ("menu_items", "veg_nonveg"): {"Veg", "Non-veg"},
    ("orders", "order_status"): {"completed", "cancelled",
                                 "refunded_partial", "refunded_full"},
    ("promotions", "discount_type"): {"flat", "percentage", "free_item", "combo"},
    ("wastage", "waste_type"): {"prep_waste", "unsold_cooked",
                                "returned_order", "spoilage"},
    ("expenses", "expense_category"): {"staff", "rent", "utilities",
                                       "gas_consumables", "procurement_travel",
                                       "repairs", "advertising",
                                       "packaging_extra", "compliance",
                                       "founder_drawings", "kitchen_rent"},
    ("expenses", "cost_behaviour"): {"fixed", "semi_variable", "variable"},
    ("daily_operations", "weather_flag"): {"normal", "rain", "extreme"},
    ("daily_operations", "covid_phase"): {"pre", "wave1", "reopening",
                                          "plateau", "wave2", "recovery",
                                          "decline"},
}

# Non-negative numeric domains
NON_NEGATIVE = [
    ("order_items", "quantity"), ("order_items", "unit_listed_price"),
    ("order_items", "unit_food_cost"), ("order_items", "item_discount"),
    ("order_items", "line_total"),
    ("orders", "gross_order_value"), ("orders", "platform_funded_discount"),
    ("orders", "restaurant_funded_discount"), ("orders", "commission_amount"),
    ("orders", "other_deductions"), ("orders", "customer_delivery_fee"),
    ("orders", "refund_amount"), ("orders", "packaging_cost"),
    ("wastage", "quantity_kg"), ("wastage", "estimated_cost"),
    ("item_availability", "batch_prepared_qty"),
    ("item_availability", "estimated_lost_orders"),
    ("expenses", "amount"),
    ("menu_item_prices", "base_price"), ("menu_item_prices", "listed_price"),
]

dfs, errors, warnings_ = {}, [], []


def err(msg):
    errors.append(msg)
    print(f"  [ERROR] {msg}")


def warn(msg):
    warnings_.append(msg)
    print(f"  [WARN ] {msg}")


def ok(msg):
    print(f"  [ OK  ] {msg}")


def header(title):
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


# ============================================================
# V1 — FILES AND ROW COUNTS
# ============================================================
def v1_files():
    header("V1 — FILES AND ROW COUNTS")
    for table, expected in EXPECTED_ROW_COUNTS.items():
        path = DATA_DIR / f"{table}.csv"
        if not path.exists():
            err(f"{table}: file missing at {path}")
            continue
        try:
            dfs[table] = pd.read_csv(path)
        except Exception as exc:
            err(f"{table}: unreadable -> {exc}")
            continue
        actual = len(dfs[table])
        if actual == expected:
            ok(f"{table}: {actual:,} rows")
        else:
            err(f"{table}: expected {expected:,} rows, found {actual:,}")
    total = sum(len(d) for d in dfs.values())
    ok(f"total rows loaded: {total:,}")


# ============================================================
# V2 — REQUIRED COLUMNS AND ENUM DOMAINS
# ============================================================
def v2_schema():
    header("V2 — REQUIRED COLUMNS AND ENUM DOMAINS")
    for table, cols in REQUIRED_COLUMNS.items():
        if table not in dfs:
            continue
        missing = [c for c in cols if c not in dfs[table].columns]
        if missing:
            err(f"{table}: missing column(s): {', '.join(missing)}")
        else:
            ok(f"{table}: all {len(cols)} required columns present")

    for (table, col), domain in ENUM_DOMAINS.items():
        if table not in dfs or col not in dfs[table].columns:
            err(f"{table}.{col}: column absent, cannot check domain")
            continue
        found = set(dfs[table][col].dropna().unique())
        rogue = found - domain
        if rogue:
            err(f"{table}.{col}: values outside ENUM domain: {sorted(rogue)}")
        else:
            ok(f"{table}.{col}: {len(found)} value(s), all inside domain")


# ============================================================
# V3 — PRIMARY AND UNIQUE KEYS
# ============================================================
def v3_keys():
    header("V3 — PRIMARY AND UNIQUE KEYS")
    for table, keys in PRIMARY_KEYS.items():
        if table not in dfs:
            continue
        df = dfs[table]
        missing = [k for k in keys if k not in df.columns]
        if missing:
            err(f"{table}: PK column(s) absent: {', '.join(missing)}")
            continue
        nulls = int(df[keys].isna().any(axis=1).sum())
        dupes = int(df.duplicated(keys).sum())
        label = "+".join(keys)
        if nulls:
            err(f"{table}.({label}): {nulls:,} NULL(s) in primary key")
        if dupes:
            err(f"{table}.({label}): {dupes:,} duplicate key(s)")
        if not nulls and not dupes:
            kind = "composite PK" if len(keys) > 1 else "PK"
            ok(f"{table}.({label}): unique, no NULLs [{kind}]")

    for table, keys in UNIQUE_KEYS.items():
        if table not in dfs:
            continue
        df = dfs[table]
        if any(k not in df.columns for k in keys):
            err(f"{table}: unique-key column(s) absent: {keys}")
            continue
        dupes = int(df.duplicated(keys).sum())
        label = "+".join(keys)
        if dupes:
            err(f"{table}.({label}): {dupes:,} duplicate(s), UNIQUE violated")
        else:
            ok(f"{table}.({label}): UNIQUE satisfied")


# ============================================================
# V4 — FOREIGN KEYS (nullable-aware)
# ============================================================
def v4_foreign_keys():
    header("V4 — FOREIGN KEYS")
    for child, ccol, parent, pcol, nullable in FOREIGN_KEYS:
        if child not in dfs or parent not in dfs:
            err(f"{child}.{ccol} -> {parent}.{pcol}: table missing")
            continue
        if ccol not in dfs[child].columns:
            err(f"{child}.{ccol}: column absent")
            continue
        col = dfs[child][ccol]
        valid = set(dfs[parent][pcol].dropna())
        # CRITICAL: exclude NULLs before isin(). pandas treats NaN as "not in".
        orphan_mask = col.notna() & ~col.isin(valid)
        orphans = int(orphan_mask.sum())
        nulls = int(col.isna().sum())
        if orphans:
            err(f"{child}.{ccol} -> {parent}.{pcol}: {orphans:,} orphan(s)")
        elif nulls and not nullable:
            err(f"{child}.{ccol}: {nulls:,} NULL(s) but FK is NOT NULL")
        elif nulls and nullable:
            ok(f"{child}.{ccol} -> {parent}.{pcol}: valid "
               f"({nulls:,} NULLs = company-level, permitted)")
        else:
            ok(f"{child}.{ccol} -> {parent}.{pcol}: valid")


# ============================================================
# V5 — TEMPORAL INTEGRITY
# ============================================================
def v5_temporal():
    header("V5 — TEMPORAL INTEGRITY")
    o = dfs["orders"].copy()
    o["dt"] = pd.to_datetime(o["order_datetime"], errors="coerce")
    bad = int(o["dt"].isna().sum())
    if bad:
        err(f"orders.order_datetime: {bad:,} unparseable")
    else:
        ok(f"orders.order_datetime: all parse; range "
           f"{o.dt.min().date()} to {o.dt.max().date()}")

    # orders must fall inside each outlet's operating window
    outlets = dfs["outlets"].set_index("outlet_id")
    for oid, grp in o.groupby("outlet_id"):
        open_d = pd.Timestamp(outlets.loc[oid, "opening_date"])
        close_d = outlets.loc[oid, "closing_date"]
        close_d = pd.Timestamp(close_d) if pd.notna(close_d) \
            else pd.Timestamp("2099-12-31")
        viol = int(((grp.dt < open_d) |
                    (grp.dt > close_d + pd.Timedelta(days=1))).sum())
        if viol:
            err(f"outlet {oid}: {viol:,} order(s) outside "
                f"{open_d.date()}..{close_d.date()}")
        else:
            ok(f"outlet {oid}: all orders inside operating window "
               f"({grp.dt.min().date()} to {grp.dt.max().date()})")

    # TIER 1: platform shutdown dates are hard constraints
    plats = dfs["platforms"].set_index("platform_id")
    for pid, grp in o.groupby("platform_id"):
        name = plats.loc[pid, "platform_name"]
        act_from = pd.Timestamp(plats.loc[pid, "active_from"])
        act_to = plats.loc[pid, "active_to"]
        act_to = pd.Timestamp(act_to) if pd.notna(act_to) \
            else pd.Timestamp("2099-12-31")
        viol = int(((grp.dt < act_from) |
                    (grp.dt > act_to + pd.Timedelta(days=1))).sum())
        if viol:
            err(f"TIER 1 BREACH — {name}: {viol:,} order(s) outside "
                f"{act_from.date()}..{act_to.date()}")
        else:
            ok(f"{name}: {grp.dt.min().date()} to {grp.dt.max().date()} "
               f"(within licensed window)")

    # date-pair sanity
    pairs = [("outlets", "opening_date", "closing_date"),
             ("menu_items", "launch_date", "delist_date"),
             ("menu_item_prices", "effective_from", "effective_to"),
             ("promotions", "start_date", "end_date")]
    for table, start, end in pairs:
        df = dfs[table]
        s = pd.to_datetime(df[start], errors="coerce")
        e = pd.to_datetime(df[end], errors="coerce")
        viol = int((e.notna() & (e < s)).sum())
        if viol:
            err(f"{table}: {viol:,} row(s) with {end} before {start}")
        else:
            ok(f"{table}: {start} <= {end} on every row")

    # a customer's first_order_date must match their earliest actual order
    first_actual = o.groupby("customer_id").dt.min().dt.date
    cu = dfs["customers"].set_index("customer_id")
    stated = pd.to_datetime(cu["first_order_date"]).dt.date
    joined = pd.DataFrame({"stated": stated}).join(
        first_actual.rename("actual"), how="inner")
    viol = int((joined.stated != joined.actual).sum())
    if viol:
        warn(f"customers.first_order_date: {viol:,} disagree with earliest "
             f"order (acceptable if cancelled orders count as first contact)")
    else:
        ok("customers.first_order_date matches earliest order for all")


# ============================================================
# V6 — BUSINESS-RULE RECONCILIATION
# ============================================================
def v6_business_rules():
    header("V6 — BUSINESS-RULE RECONCILIATION")
    o = dfs["orders"]
    oi = dfs["order_items"]

    # non-negative domains
    neg_found = False
    for table, col in NON_NEGATIVE:
        if table not in dfs or col not in dfs[table].columns:
            continue
        n = int((dfs[table][col] < 0).sum())
        if n:
            err(f"{table}.{col}: {n:,} negative value(s)")
            neg_found = True
    if not neg_found:
        ok(f"all {len(NON_NEGATIVE)} monetary/quantity columns non-negative")

    n = int((oi["quantity"] <= 0).sum())
    err(f"order_items.quantity: {n:,} row(s) <= 0") if n else \
        ok("order_items.quantity: all > 0")

    # R1  net = gross - platform_funded - restaurant_funded
    calc = (o.gross_order_value - o.platform_funded_discount
            - o.restaurant_funded_discount)
    n = int((abs(calc - o.net_order_value) > MONEY_TOL).sum())
    err(f"R1 net_order_value: {n:,} mismatch(es)") if n else \
        ok("R1 net_order_value = gross - platform_disc - restaurant_disc")

    # R2  commission = 28% of GROSS  (Tier 1 — NOT of net)
    rate = o.commission_amount / o.gross_order_value
    n = int((abs(rate - 0.28) > RATE_TOL).sum())
    if n:
        err(f"R2 commission basis: {n:,} order(s) not at 28% of gross "
            f"(observed mean {rate.mean():.4f})")
    else:
        ok(f"R2 commission = 28.00% of GROSS on all orders "
           f"(sd {rate.std():.6f})")
    rate_net = (o.commission_amount / o.net_order_value)
    ok(f"     for contrast, commission/net = {rate_net.mean():.4f} "
       f"+/- {rate_net.std():.4f} — not a constant, so net is the wrong basis")

    # R3  settlement = net - commission - other_deductions - refund
    #     customer_delivery_fee must NOT appear. This is the Tier 1 rule that
    #     took two rounds to get right; it is asserted here permanently.
    calc = (o.net_order_value - o.commission_amount
            - o.other_deductions - o.refund_amount)
    n = int((abs(calc - o.restaurant_settlement) > MONEY_TOL).sum())
    err(f"R3 restaurant_settlement: {n:,} mismatch(es)") if n else \
        ok("R3 settlement = net - commission - other - refund "
           "(delivery fee correctly EXCLUDED)")

    # R3b prove the delivery fee is not silently inside settlement
    with_fee = (o.net_order_value - o.commission_amount - o.other_deductions
                - o.refund_amount - o.customer_delivery_fee)
    n = int((abs(with_fee - o.restaurant_settlement) <= MONEY_TOL).sum())
    if n > len(o) * 0.01:
        err(f"R3b TIER 1 BREACH — delivery fee appears deducted on {n:,} orders")
    else:
        ok("R3b customer delivery fee is not deducted from restaurant revenue")

    # R4  line_total = quantity * unit_listed_price - item_discount
    calc = oi.quantity * oi.unit_listed_price - oi.item_discount
    n = int((abs(calc - oi.line_total) > MONEY_TOL).sum())
    err(f"R4 line_total: {n:,} mismatch(es)") if n else \
        ok("R4 line_total = quantity * unit_listed_price - item_discount")

    # R5  sum(line_total) = gross_order_value
    li = oi.groupby("order_id").line_total.sum().rename("line_sum")
    m = o.set_index("order_id").join(li)
    n = int((abs(m.gross_order_value - m.line_sum) > MONEY_TOL).sum())
    if n:
        err(f"R5 order/line reconciliation: {n:,} order(s) where "
            f"sum(line_total) != gross_order_value")
    else:
        ok("R5 sum(line_total) = gross_order_value on every order")

    # R6  packaging exactly Rs 15 on non-cancelled, Rs 0 on cancelled (Tier 1)
    live = o[o.order_status != "cancelled"]
    dead = o[o.order_status == "cancelled"]
    n1 = int((abs(live.packaging_cost - 15.0) > 0.001).sum())
    n2 = int((dead.packaging_cost != 0).sum())
    if n1 or n2:
        err(f"R6 packaging: {n1:,} non-cancelled not at Rs 15, "
            f"{n2:,} cancelled non-zero")
    else:
        ok("R6 packaging = Rs 15.00 on all fulfilled, Rs 0 on cancelled")

    # R7  listed_price >= base_price (aggregator premium never negative)
    p = dfs["menu_item_prices"]
    n = int((p.listed_price < p.base_price).sum())
    err(f"R7 pricing: {n:,} row(s) with listed below base") if n else \
        ok(f"R7 listed_price >= base_price; premium "
           f"{(p.listed_price/p.base_price).min():.3f}-"
           f"{(p.listed_price/p.base_price).max():.3f}")

    # R8  rating domain and NULL semantics
    r = o.rating.dropna()
    n = int((~r.isin([1, 2, 3, 4, 5])).sum())
    err(f"R8 rating: {n:,} outside 1-5") if n else \
        ok(f"R8 rating in 1-5; {int(o.rating.isna().sum()):,} NULL "
           f"({100*o.rating.isna().mean():.1f}%) = customer did not rate")

    # R9  cancellation_reason present iff cancelled
    bad1 = int(((o.order_status == "cancelled") &
                (o.cancellation_reason.isna())).sum())
    bad2 = int(((o.order_status != "cancelled") &
                (o.cancellation_reason.notna())).sum())
    if bad1 or bad2:
        err(f"R9 cancellation_reason: {bad1:,} cancelled without reason, "
            f"{bad2:,} non-cancelled with reason")
    else:
        ok("R9 cancellation_reason present exactly when cancelled")

    # R10 refunds only on refunded orders
    bad = int(((~o.order_status.str.startswith("refunded")) &
               (o.refund_amount > 0)).sum())
    err(f"R10 refund_amount: {bad:,} on non-refunded orders") if bad else \
        ok("R10 refund_amount > 0 only on refunded orders")

    # R11 wastage never zero in any month (Tier 1)
    w = dfs["wastage"].copy()
    w["ym"] = pd.to_datetime(w.wastage_date).dt.to_period("M")
    zero = int((w.groupby("ym").quantity_kg.sum() <= 0).sum())
    err(f"R11 TIER 1 BREACH — {zero} month(s) with zero wastage") if zero else \
        ok(f"R11 wastage non-zero in all {w.ym.nunique()} months")

    # R12 menu item sales must fall inside launch..delist (Tier 1: desserts)
    mi = dfs["menu_items"].set_index("menu_item_id")
    j = oi.merge(o[["order_id", "order_datetime"]], on="order_id")
    j["dt"] = pd.to_datetime(j.order_datetime)
    viol = 0
    for mid, grp in j.groupby("menu_item_id"):
        launch = pd.Timestamp(mi.loc[mid, "launch_date"])
        delist = mi.loc[mid, "delist_date"]
        delist = pd.Timestamp(delist) if pd.notna(delist) \
            else pd.Timestamp("2099-12-31")
        viol += int(((grp.dt < launch) |
                     (grp.dt > delist + pd.Timedelta(days=1))).sum())
    err(f"R12 {viol:,} item sale(s) outside launch/delist window") if viol else \
        ok("R12 every item sold only within its launch..delist window")


# ============================================================
# V7 — STATISTICAL REALITY CHECKS (Tier 2 calibration)
# ============================================================
def v7_reality():
    header("V7 — STATISTICAL REALITY CHECKS (Tier 2 calibration bands)")
    o = dfs["orders"].copy()
    oi = dfs["order_items"]
    o["dt"] = pd.to_datetime(o.order_datetime)
    live = o[o.order_status != "cancelled"]

    def band(label, value, lo, hi, fmt="{:,.1f}"):
        inside = lo <= value <= hi
        msg = (f"{label}: {fmt.format(value)} "
               f"(band {fmt.format(lo)}-{fmt.format(hi)})")
        ok(msg) if inside else err(msg + " OUT OF BAND")

    for yr, grp in live.groupby(live.dt.dt.year):
        band(f"AOV {yr}", grp.gross_order_value.mean(), 390, 450, "{:,.0f}")

    k19 = live[(live.outlet_id == 1) & (live.dt.dt.year == 2019)]
    band("mature orders/month (outlet 1, 2019)",
         k19.groupby(k19.dt.dt.to_period("M")).size().mean(), 880, 970, "{:,.0f}")
    band("mature gross/month (outlet 1, 2019)",
         k19.groupby(k19.dt.dt.to_period("M")).gross_order_value.sum().mean(),
         351000, 428000, "{:,.0f}")
    band("line items per order",
         oi.groupby("order_id").quantity.sum().mean(), 1.55, 1.85, "{:.2f}")

    fc = (oi.unit_food_cost * oi.quantity).sum()
    band("food cost % of BASE price",
         100 * 1.15 * fc / oi.line_total.sum(), 33.5, 36.5, "{:.1f}")
    band("cancellation rate %",
         100 * (o.order_status == "cancelled").mean(), 2.2, 3.6, "{:.2f}")
    band("refund rate %",
         100 * o.order_status.str.startswith("refunded").mean(), 1.0, 2.2, "{:.2f}")
    band("unrated orders %", 100 * o.rating.isna().mean(), 28, 40, "{:.1f}")

    feb20 = len(live[live.dt.dt.to_period("M") == "2020-02"])
    apr20 = len(live[live.dt.dt.to_period("M") == "2020-04"])
    band("Wave 1 volume decline % vs Feb 2020",
         100 * (1 - apr20 / feb20), 82, 92, "{:.1f}")

    # monthly volume must VARY, not repeat a constant
    sd = k19.groupby(k19.dt.dt.to_period("M")).size().std()
    if sd < 15:
        err(f"monthly order volume sd = {sd:.1f} — too uniform, looks synthetic")
    else:
        ok(f"monthly order volume varies (sd {sd:.1f} orders)")

    # deliberate dirt must be present
    cu = dfs["customers"]
    raw = cu.delivery_area.nunique()
    clean = (cu.delivery_area.astype(str).str.lower().str.strip()
             .str.replace(".", "", regex=False).nunique())
    if raw <= clean:
        err("delivery_area: no spelling variants — the cleaning exercise is missing")
    else:
        ok(f"delivery_area: {raw} raw variants collapse to {clean} real areas "
           f"(cleaning exercise present)")


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 74)
    print("E-TABLE FOODS — PHASE 3B DATA VALIDATION (pre-MySQL gate)")
    print(f"data directory: {DATA_DIR}")
    print("=" * 74)

    v1_files()
    if len(dfs) < len(EXPECTED_ROW_COUNTS):
        print("\nAborting: not all tables loaded.")
        sys.exit(1)
    v2_schema()
    v3_keys()
    v4_foreign_keys()
    v5_temporal()
    v6_business_rules()
    v7_reality()

    print("\n" + "=" * 74)
    print(f"ERRORS   : {len(errors)}")
    print(f"WARNINGS : {len(warnings_)}")
    print("=" * 74)
    if errors:
        print("\nGATE CLOSED — fix the GENERATOR and regenerate. Never edit CSVs.")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    if warnings_:
        print("\nWarnings (review, not blocking):")
        for w in warnings_:
            print(f"  - {w}")
    print("\nGATE OPEN — proceed to Phase 4: MySQL schema and load.")
    sys.exit(0)


if __name__ == "__main__":
    main()
