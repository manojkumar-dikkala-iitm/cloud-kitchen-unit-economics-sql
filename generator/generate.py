"""
E-Table Foods — synthetic dataset generator.

Bottom-up: demand -> orders -> items -> prices -> discounts -> deductions -> costs.
Monthly P&L is never written to a target. It is whatever the generated behaviour
produces. reconcile.py then checks whether the result falls inside the Phase 1
guardrails. If it does not, behavioural parameters in config.py get tuned and
this is re-run. Outputs are never adjusted after the fact.
"""

import csv
import os
import random
from collections import defaultdict
from datetime import date, timedelta

import config as C

rng = random.Random(C.SEED)


# ---------------------------------------------------------------- helpers
def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def month_key(d):
    return (d.year, d.month)


def price_multiplier(d):
    for lo, hi, m in C.PRICE_EPOCHS:
        if lo <= d <= hi:
            return m
    return 1.0


def covid_phase(d):
    for lo, hi, ph in C.COVID_PHASE:
        if lo <= d <= hi:
            return ph
    return "pre"


def active_platforms(d):
    out = []
    for p in C.PLATFORMS:
        if p["active_from"] <= d and (p["active_to"] is None or d <= p["active_to"]):
            out.append(p)
    return out


def weighted_choice(items, weights):
    return rng.choices(items, weights=weights, k=1)[0]


def truncnorm(mean, sd, lo, hi):
    for _ in range(12):
        v = rng.gauss(mean, sd)
        if lo <= v <= hi:
            return v
    return max(lo, min(hi, mean))


# ---------------------------------------------------------------- dimensions
MENU_BY_ID = {m[0]: m for m in C.MENU}


def build_menu_items():
    rows = []
    for mid, name, cat, veg, base, fcp, launch, delist, _w in C.MENU:
        rows.append(dict(menu_item_id=mid, item_name=name, category=cat,
                         veg_nonveg=veg, base_food_cost_pct=round(fcp, 4),
                         launch_date=launch, delist_date=delist,
                         is_combo=0))
    return rows


def build_menu_item_prices():
    """item x platform x price epoch. Aggregator listed = base x 1.15."""
    rows = []
    pid = 1
    for mid, name, cat, veg, base, fcp, launch, delist, _w in C.MENU:
        for lo, hi, mult in C.PRICE_EPOCHS:
            eff_from = max(lo, launch)
            eff_to = hi if delist is None else min(hi, delist)
            if eff_from > eff_to:
                continue
            base_p = round(base * mult, 2)
            for p in C.PLATFORMS:
                if p["active_to"] is not None and p["active_to"] < eff_from:
                    continue
                prem = (C.CATEGORY_PREMIUM.get(cat, C.AGGREGATOR_PREMIUM)
                        * C.PLATFORM_PREMIUM_ADJ[p["platform_id"]])
                listed = round(base_p * prem, 0)
                rows.append(dict(price_id=pid, menu_item_id=mid,
                                 platform_id=p["platform_id"],
                                 base_price=base_p, listed_price=listed,
                                 effective_from=eff_from, effective_to=eff_to))
                pid += 1
    return rows


PRICE_LOOKUP = {}


def index_prices(price_rows):
    for r in price_rows:
        PRICE_LOOKUP[(r["menu_item_id"], r["platform_id"],
                      r["effective_from"].year)] = r


def get_price(mid, platform_id, d):
    key = (mid, platform_id, d.year)
    r = PRICE_LOOKUP.get(key)
    if r is None:
        for yr in range(d.year, 2017, -1):
            r = PRICE_LOOKUP.get((mid, platform_id, yr))
            if r:
                break
    return r


def build_promotions():
    rows = []
    pid = 1
    templates = [
        ("Flat 100 off above 399", "flat", 100, 399, 1.00),
        ("Weekend 15% off", "percentage", 0.15, 299, 1.00),
        ("Free beverage above 499", "free_item", 45, 499, 1.00),
        ("Platform festive 40% off", "percentage", 0.40, 199, 0.00),
        ("Platform 50% up to 100", "percentage", 0.50, 149, 0.00),
        ("Super saver combo", "combo", 0.10, 0, 1.00),
        ("Platform recovery 30% off", "percentage", 0.30, 249, 0.00),
    ]
    windows = [
        (date(2018, 3, 1), date(2018, 12, 31)),
        (date(2019, 1, 1), date(2019, 12, 31)),
        (date(2020, 1, 1), date(2020, 3, 15)),
        (date(2020, 7, 1), date(2020, 12, 31)),
        (date(2021, 1, 1), date(2021, 3, 31)),
        (date(2021, 7, 1), date(2021, 12, 31)),
        (date(2022, 1, 1), date(2022, 11, 30)),
    ]
    for (name, dtype, dval, mov, rfp) in templates:
        for (ws, we) in windows:
            for p in C.PLATFORMS:
                if p["active_to"] is not None and p["active_to"] < ws:
                    continue
                if rng.random() < 0.45:
                    continue
                rows.append(dict(promotion_id=pid, platform_id=p["platform_id"],
                                 promotion_name=name, discount_type=dtype,
                                 discount_value=dval, min_order_value=mov,
                                 restaurant_funded_pct=rfp,
                                 start_date=ws, end_date=we))
                pid += 1
    return rows


# ---------------------------------------------------------------- demand
def outlet_open(o, d):
    return o["opening_date"] <= d <= (o["closing_date"] or C.END)


def maturity_factor(o, d):
    months_open = (d.year - o["opening_date"].year) * 12 + (d.month - o["opening_date"].month)
    if months_open >= o["ramp_months"]:
        return 1.0
    frac = months_open / o["ramp_months"]
    return o["ramp_start_frac"] + (1.0 - o["ramp_start_frac"]) * frac


def base_orders(o, d):
    dow = d.weekday()
    if dow == 6:
        base = o["mature_sunday"]
    elif dow == 5:
        base = o["mature_saturday"]
    else:
        base = o["mature_weekday"]

    f = maturity_factor(o, d)
    f *= C.SEASONAL[d.month]
    mk = month_key(d)
    f *= C.COVID_MULTIPLIER.get(mk, 1.0)
    f *= C.PEAK_MONTHS.get(mk, 1.0)

    # outlet 3 never gets to ramp: opened into the pandemic (override C2)
    if o["outlet_id"] == 3:
        f *= 0.88

    # weather / local disruption
    if rng.random() < 0.05:
        f *= rng.uniform(0.70, 0.88)
    # occasional festival / promo spike
    if rng.random() < 0.035:
        f *= rng.uniform(1.20, 1.55)

    n = base * f * rng.uniform(0.86, 1.14)
    return max(0, int(round(n)))


# ---------------------------------------------------------------- customers
class CustomerPool:
    def __init__(self):
        self.by_platform = defaultdict(list)
        self.rows = []
        self.next_id = 1

    def get(self, platform_id, d, area):
        pool = self.by_platform[platform_id]
        if pool and rng.random() < C.REPEAT_RATE:
            k = min(len(pool), 600)
            return pool[-rng.randint(1, k)]
        cid = self.next_id
        self.next_id += 1
        ref = f"P{platform_id}-{cid:06d}"
        self.rows.append(dict(customer_id=cid, platform_id=platform_id,
                              platform_customer_ref=ref, first_order_date=d,
                              delivery_area=area))
        pool.append(cid)
        return cid


# ---------------------------------------------------------------- availability
def stocked_beverages(d):
    third = weighted_choice(C.BEVERAGE_ROTATING, [1, 1, 1, 1])
    seed_day = (d - C.START).days // 21
    third = C.BEVERAGE_ROTATING[seed_day % len(C.BEVERAGE_ROTATING)]
    return C.BEVERAGE_ALWAYS + [third]


def available_mains(d):
    out = []
    for mid in C.MAIN_IDS:
        m = MENU_BY_ID[mid]
        launch, delist = m[6], m[7]
        if launch <= d and (delist is None or d <= delist):
            out.append(mid)
    return out


def dessert_available(d):
    return any(MENU_BY_ID[i][6] <= d <= (MENU_BY_ID[i][7] or C.END) for i in C.DESSERT_IDS)


# ---------------------------------------------------------------- order build
def pick_daypart():
    r = rng.random()
    if r < 0.05:
        return rng.randint(7, 10), 59
    if r < 0.39:
        return rng.randint(11, 14), 59
    if r < 0.55:
        return rng.randint(15, 18), 59
    if r < 0.95:
        return rng.randint(19, 22), 30
    return 22, 59


def build_order_items(d, platform_id, mains_avail, bevs_avail, sold_out):
    label, _p, n_main, p_bev, p_add = weighted_choice(
        [b for b in C.BASKET_MIX], [b[1] for b in C.BASKET_MIX])

    weights = []
    pool = []
    for mid in mains_avail:
        if mid in sold_out:
            continue
        pool.append(mid)
        weights.append(MENU_BY_ID[mid][8])
    if not pool:
        return None, label

    lines = []
    chosen = []
    for _ in range(n_main):
        mid = weighted_choice(pool, weights)
        chosen.append(mid)
    for mid in chosen:
        lines.append((mid, 1))

    if rng.random() < p_bev:
        bev = weighted_choice(bevs_avail, [C.BEVERAGE_PICK_WEIGHTS[b] for b in bevs_avail])
        qty = 1 if rng.random() < 0.82 else 2
        lines.append((bev, qty))
    if rng.random() < p_add:
        lines.append((weighted_choice(C.ADDON_IDS, [0.45, 0.30, 0.25]), 1))
    # occasional dessert while it existed
    if dessert_available(d) and rng.random() < 0.05:
        lines.append((rng.choice(C.DESSERT_IDS), 1))

    return lines, label


def food_cost_multiplier(d):
    m = C.FOOD_COST_YEAR_DRIFT.get(d.year, 1.0)
    if d <= C.EARLY_INEFFICIENCY_END:
        m *= C.EARLY_FOOD_COST_UPLIFT
    return m


def generate():
    rng.seed(C.SEED)

    menu_items = build_menu_items()
    price_rows = build_menu_item_prices()
    index_prices(price_rows)
    promotions = build_promotions()

    pool = CustomerPool()
    orders, order_items, availability, wastage, daily_ops = [], [], [], [], []

    order_id = 1
    item_id = 1
    avail_id = 1
    waste_id = 1

    monthly_gross = defaultdict(float)

    for d in daterange(C.START, C.END):
        phase = covid_phase(d)
        pmult = price_multiplier(d)
        fmult = food_cost_multiplier(d)
        mains_avail = available_mains(d)
        bevs_avail = stocked_beverages(d)
        plats = active_platforms(d)
        if not plats:
            continue
        pweights = [p["base_share"] for p in plats]

        for o in C.OUTLETS:
            if not outlet_open(o, d):
                continue

            n_orders = base_orders(o, d)

            # limited-batch production: prepare to a forecast, not to demand
            forecast = int(round(n_orders * rng.uniform(0.93, 1.05)))
            capacity = int(round(o["mature_sunday"] * 1.35))

            # decide which items sell out today
            sold_out = set()
            for mid in mains_avail:
                w = MENU_BY_ID[mid][8]
                p_out = C.STOCKOUT_RATE * (1 + 2.6 * w) * (1.9 if d.weekday() >= 5 else 1.0)
                if n_orders > capacity * 0.82:
                    p_out *= 1.7
                if rng.random() < p_out:
                    sold_out.add(mid)

            # item availability rows for the mains
            for mid in mains_avail:
                prepared = max(1, int(round(forecast * MENU_BY_ID[mid][8] * 1.08)))
                so_time = None
                lost = 0
                if mid in sold_out:
                    hh = rng.randint(19, 22)
                    so_time = f"{hh:02d}:{rng.randint(0, 59):02d}:00"
                    lost = rng.randint(1, 6)
                availability.append(dict(
                    availability_id=avail_id, outlet_id=o["outlet_id"],
                    menu_item_id=mid, availability_date=d,
                    batch_prepared_qty=prepared, sold_out_time=so_time,
                    estimated_lost_orders=lost))
                avail_id += 1

            day_orders = 0
            day_prep_total = 0
            day_refunds = 0

            for _ in range(n_orders):
                p = weighted_choice(plats, pweights)
                platform_id = p["platform_id"]
                area = rng.choice(C.DELIVERY_AREAS)
                cid = pool.get(platform_id, d, area)

                lines, basket_label = build_order_items(
                    d, platform_id, mains_avail, bevs_avail, sold_out)
                if not lines:
                    continue

                gross = 0.0
                item_rows = []
                for mid, qty in lines:
                    pr = get_price(mid, platform_id, d)
                    if pr is None:
                        continue
                    listed = pr["listed_price"]
                    fc_base = pr["base_price"] * MENU_BY_ID[mid][5] * fmult
                    line_total = listed * qty
                    gross += line_total
                    item_rows.append(dict(
                        order_item_id=item_id, order_id=order_id,
                        menu_item_id=mid, quantity=qty,
                        unit_listed_price=round(listed, 2),
                        unit_food_cost=round(fc_base, 2),
                        item_discount=0.0,
                        line_total=round(line_total, 2)))
                    item_id += 1
                if not item_rows:
                    continue

                # combo pricing: distribute the discount across the line items
                # so sum(line_total) always reconciles to gross_order_value
                is_combo_order = 0
                if rng.random() < C.COMBO_RATE and len(item_rows) >= 2:
                    is_combo_order = 1
                    for r in item_rows:
                        disc = round(r["line_total"] * C.COMBO_DISCOUNT, 2)
                        r["item_discount"] = disc
                        r["line_total"] = round(r["line_total"] - disc, 2)
                    gross = sum(r["line_total"] for r in item_rows)

                # discounts
                plat_disc = 0.0
                rest_disc = 0.0
                if rng.random() < C.DISCOUNT_INCIDENCE:
                    if rng.random() < C.RESTAURANT_FUNDED_SHARE:
                        depth = truncnorm(C.RESTAURANT_DISCOUNT_DEPTH, 0.04, 0.05, 0.25)
                        rest_disc = gross * depth
                    else:
                        depth = truncnorm(C.PLATFORM_DISCOUNT_DEPTH, 0.07, 0.05, 0.45)
                        plat_disc = gross * depth
                # discount intensity rises during recovery
                if phase in ("reopening", "plateau", "recovery", "decline"):
                    rest_disc *= 1.22
                    plat_disc *= 1.15

                net = gross - plat_disc - rest_disc

                # restaurant deductions: commission only. Delivery is charged to
                # the customer and never enters the restaurant P&L.
                commission = gross * p["commission_rate"]
                other_ded = gross * p["other_deduction_rate"]
                cust_delivery_fee = round(gross * p["customer_delivery_rate"], 2)

                # status
                status = "completed"
                cancel_reason = None
                refund = 0.0
                r = rng.random()
                cancel_p = C.CANCEL_RATE * (1.6 if phase in ("wave1", "wave2") else 1.0)
                if r < cancel_p:
                    status = "cancelled"
                    cancel_reason = weighted_choice(
                        C.CANCEL_REASONS, [0.34, 0.24, 0.18, 0.14, 0.10])
                elif r < cancel_p + C.REFUND_RATE:
                    if rng.random() < 0.78:
                        status = "refunded_partial"
                        refund = net * rng.uniform(0.25, 0.50) * C.REFUND_RESTAURANT_SHARE
                    else:
                        status = "refunded_full"
                        refund = net * C.REFUND_RESTAURANT_SHARE

                # timing
                load = n_orders / max(1, capacity)
                prep = truncnorm(C.PREP_MEAN * (1 + 0.55 * max(0, load - 0.6)), 5, 8, 70)
                deliv = truncnorm(22 * (1 + 0.30 * max(0, load - 0.6)), 7, 8, 65)
                if rng.random() < 0.06:
                    deliv *= rng.uniform(1.3, 2.0)
                prep, deliv = int(round(prep)), int(round(deliv))
                promised = 40 if d.weekday() < 5 else 45

                # rating
                rating = None
                if rng.random() > C.NO_RATING_RATE and status != "cancelled":
                    late = (prep + deliv) > C.LATE_THRESHOLD_MIN
                    dist = dict(C.RATING_DIST)
                    if late:
                        dist = {5: 0.30, 4: 0.24, 3: 0.20, 2: 0.15, 1: 0.11}
                    if status.startswith("refunded"):
                        dist = {5: 0.10, 4: 0.15, 3: 0.22, 2: 0.28, 1: 0.25}
                    rating = weighted_choice(list(dist), list(dist.values()))

                packaging = C.PACKAGING_PER_ORDER if status != "cancelled" else 0.0

                settlement = net - commission - other_ded - refund

                hh, mm_cap = pick_daypart()
                dt = f"{d.isoformat()} {hh:02d}:{rng.randint(0, mm_cap):02d}:{rng.randint(0,59):02d}"

                orders.append(dict(
                    order_id=order_id, customer_id=cid, outlet_id=o["outlet_id"],
                    platform_id=platform_id, order_datetime=dt,
                    order_status=status, cancellation_reason=cancel_reason,
                    gross_order_value=round(gross, 2),
                    platform_funded_discount=round(plat_disc, 2),
                    restaurant_funded_discount=round(rest_disc, 2),
                    net_order_value=round(net, 2),
                    commission_amount=round(commission, 2),
                    other_deductions=round(other_ded, 2),
                    customer_delivery_fee=cust_delivery_fee,
                    refund_amount=round(refund, 2),
                    restaurant_settlement=round(settlement, 2),
                    packaging_cost=round(packaging, 2),
                    promised_minutes=promised, prep_minutes=prep,
                    delivery_minutes=deliv, rating=rating,
                    basket_type=basket_label, is_combo_order=is_combo_order))
                order_items.extend(item_rows)
                if status != "cancelled":
                    monthly_gross[(month_key(d), o["outlet_id"])] += gross
                if status.startswith("refunded"):
                    day_refunds += 1
                order_id += 1
                day_orders += 1
                day_prep_total += prep

            # wastage: never zero (LIVED)
            early = d <= C.EARLY_INEFFICIENCY_END
            wm = C.EARLY_WASTAGE_MULTIPLIER if early else 1.0
            unsold = max(0, forecast - day_orders)
            for wtype, kg_base in (("prep_waste", 0.55), ("unsold_cooked", 0.30),
                                   ("spoilage", 0.10), ("returned_order", 0.05)):
                kg = kg_base * wm * rng.uniform(0.6, 1.5) * C.WASTAGE_SCALE
                if wtype == "unsold_cooked":
                    kg += unsold * 0.055 * wm * C.WASTAGE_SCALE
                if wtype == "returned_order":
                    # each returned order is roughly 0.5-0.9 kg of unsellable food
                    kg = day_refunds * rng.uniform(0.5, 0.9)
                kg = max(0.02, kg)
                cost = kg * rng.uniform(105, 155)
                wastage.append(dict(
                    wastage_id=waste_id, outlet_id=o["outlet_id"],
                    wastage_date=d, waste_type=wtype,
                    quantity_kg=round(kg, 2), estimated_cost=round(cost, 2),
                    reason="pre-optimisation batch sizing" if early else "routine"))
                waste_id += 1

            staff = 3 if o["outlet_id"] == 1 else 2
            if phase in ("wave1", "wave2"):
                staff = max(1, staff - 1)
            daily_ops.append(dict(
                outlet_id=o["outlet_id"], operation_date=d,
                staff_on_shift=staff, kitchen_capacity_orders=capacity,
                weather_flag=weighted_choice(["normal", "rain", "extreme"],
                                             [0.86, 0.12, 0.02]),
                covid_phase=phase))

    expenses = build_expenses(monthly_gross)

    return dict(outlets=build_outlets(), platforms=build_platforms(),
                menu_items=menu_items, menu_item_prices=price_rows,
                customers=pool.rows, orders=orders, order_items=order_items,
                promotions=promotions, item_availability=availability,
                wastage=wastage, expenses=expenses, daily_operations=daily_ops)


def build_outlets():
    return [dict(outlet_id=o["outlet_id"], outlet_name=o["outlet_name"],
                 outlet_type=o["outlet_type"], locality=o["locality"],
                 opening_date=o["opening_date"], closing_date=o["closing_date"],
                 monthly_rent=o["monthly_rent"], monthly_utilities=o["monthly_utilities"],
                 status=o["status"]) for o in C.OUTLETS]


def build_platforms():
    return [dict(platform_id=p["platform_id"], platform_name=p["platform_name"],
                 commission_rate=p["commission_rate"],
                 customer_delivery_rate=p["customer_delivery_rate"],
                 other_deduction_rate=p["other_deduction_rate"],
                 active_from=p["active_from"], active_to=p["active_to"])
            for p in C.PLATFORMS]


def build_expenses(monthly_gross):
    rows = []
    eid = 1
    months = []
    d = date(C.START.year, C.START.month, 1)
    while d <= C.END:
        months.append(d)
        d = date(d.year + (d.month == 12), (d.month % 12) + 1, 1)

    for m in months:
        phase = covid_phase(m)
        for o in C.OUTLETS:
            if not (o["opening_date"] <= m <= (o["closing_date"] or C.END)):
                continue
            gross = monthly_gross.get(((m.year, m.month), o["outlet_id"]), 0.0)

            months_open = (m.year - o["opening_date"].year) * 12 + (m.month - o["opening_date"].month)
            key = "opening" if months_open < 3 else phase
            staff = o["staff_cost"] * C.STAFF_PHASE_MULT.get(key, 1.0)

            proc = C.EARLY_PROCUREMENT if m <= C.EARLY_INEFFICIENCY_END else o["procurement"]
            if m.year >= 2021:
                proc *= 1.15

            if phase in ("wave1", "wave2"):
                ad_rate = 0.012
            elif phase in ("reopening", "recovery", "decline"):
                ad_rate = C.AD_RATE_RECOVERY
            elif (m.year, m.month) in C.PEAK_MONTHS:
                ad_rate = C.AD_RATE_PROMO
            else:
                ad_rate = C.AD_RATE_NORMAL

            items = [
                ("staff", staff, "semi_variable"),
                ("rent", o["monthly_rent"], "fixed"),
                ("utilities", o["monthly_utilities"] * (0.8 if phase == "wave1" else 1.0), "semi_variable"),
                ("gas_consumables", o["gas_consumables"] * (0.5 if phase == "wave1" else 1.0), "semi_variable"),
                ("procurement_travel", proc, "semi_variable"),
                ("repairs", o["repairs"] * rng.uniform(0.4, 2.2), "fixed"),
                ("packaging_extra", C.PACKAGING_EXTRA_MONTHLY * rng.uniform(0.7, 1.3), "variable"),
                ("advertising", gross * ad_rate, "variable"),
            ]
            for cat, amt, beh in items:
                rows.append(dict(expense_id=eid, outlet_id=o["outlet_id"],
                                 expense_month=m, expense_category=cat,
                                 amount=round(amt, 2), cost_behaviour=beh))
                eid += 1

        # company-level
        comp = [("compliance", C.COMPLIANCE_MONTHLY, "fixed")]
        if m >= C.CENTRAL_KITCHEN_FROM:
            comp.append(("kitchen_rent", C.CENTRAL_KITCHEN_RENT, "fixed"))
        if m >= C.FOUNDER_DRAWINGS_FROM:
            comp.append(("founder_drawings", C.FOUNDER_DRAWINGS, "fixed"))
        for cat, amt, beh in comp:
            rows.append(dict(expense_id=eid, outlet_id=None, expense_month=m,
                             expense_category=cat, amount=round(amt, 2),
                             cost_behaviour=beh))
            eid += 1
    return rows


def write_csv(tables):
    os.makedirs(C.OUTPUT_DIR, exist_ok=True)
    for name, rows in tables.items():
        if not rows:
            continue
        path = os.path.join(C.OUTPUT_DIR, f"{name}.csv")
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"  {name:22s} {len(rows):>9,} rows")


if __name__ == "__main__":
    print("Generating E-Table synthetic dataset...")
    tables = generate()
    print("\nTables written:")
    write_csv(tables)
