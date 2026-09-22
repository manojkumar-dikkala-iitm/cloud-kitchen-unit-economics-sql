"""
Reconciliation harness.

Asserts the generated dataset against Phase 1 locked guardrails. This runs
BEFORE anything is loaded into MySQL. If a check fails, behavioural parameters
in config.py get tuned and the generator re-runs. Outputs are never patched.
"""

import os
import pandas as pd

OUT = "C:/Users/manoj/Downloads/Documents/E-Table_Analytics_Project/cloud-kitchen-unit-eceonomics-sql/data"

orders = pd.read_csv(f"{OUT}/orders.csv", parse_dates=["order_datetime"])
items = pd.read_csv(f"{OUT}/order_items.csv")
exp = pd.read_csv(f"{OUT}/expenses.csv", parse_dates=["expense_month"])
waste = pd.read_csv(f"{OUT}/wastage.csv", parse_dates=["wastage_date"])
plat = pd.read_csv(f"{OUT}/platforms.csv")

orders["ym"] = orders["order_datetime"].dt.to_period("M")
exp["ym"] = exp["expense_month"].dt.to_period("M")
waste["ym"] = waste["wastage_date"].dt.to_period("M")

done = orders[orders.order_status != "cancelled"].copy()

# food cost per order from items
fc = items.assign(fc=items.unit_food_cost * items.quantity) \
          .groupby("order_id")["fc"].sum().rename("food_cost")
done = done.join(fc, on="order_id")
done["food_cost"] = done["food_cost"].fillna(0)

# contribution per order: restaurant side only. Customer delivery fee excluded.
done["contribution"] = (done.gross_order_value
                        - done.platform_funded_discount * 0
                        - done.restaurant_funded_discount
                        - done.commission_amount
                        - done.other_deductions
                        - done.refund_amount
                        - done.food_cost
                        - done.packaging_cost)

results = []


def check(name, actual, lo, hi, fmt="{:,.0f}"):
    ok = (actual >= lo) and (actual <= hi)
    results.append((name, fmt.format(actual), f"{fmt.format(lo)} – {fmt.format(hi)}",
                    "PASS" if ok else "FAIL"))
    return ok


# ------------------------------------------------------------ 1. volume
k_2019 = done[(done.outlet_id == 1) & (done.ym.dt.year == 2019)]
mo = k_2019.groupby("ym").size()
check("Kandanchavadi mature orders/month (2019 mean)", mo.mean(), 880, 970)

wd = k_2019.copy()
wd["dow"] = wd.order_datetime.dt.weekday
per_day = wd.groupby([wd.order_datetime.dt.date, "dow"]).size().reset_index(name="n")
check("Weekday orders/day (2019)", per_day[per_day.dow < 5].n.mean(), 22, 29)
check("Sunday orders/day (2019)", per_day[per_day.dow == 6].n.mean(), 55, 70)

# ------------------------------------------------------------ 2. AOV & basket
check("AOV 2019 (Kandanchavadi)", k_2019.gross_order_value.mean(), 385, 450)
ipo = items.groupby("order_id").quantity.sum().mean()
check("Line items per order", ipo, 1.55, 1.85, "{:.2f}")

# ------------------------------------------------------------ 3. cost ratios
check("Food cost % of gross (2019)",
      100 * k_2019.food_cost.sum() / k_2019.gross_order_value.sum(), 28.0, 33.0, "{:.1f}")
check("Commission % of gross (2019)",
      100 * k_2019.commission_amount.sum() / k_2019.gross_order_value.sum(), 27.0, 28.5, "{:.1f}")
check("Contribution % of gross (2019)",
      100 * k_2019.contribution.sum() / k_2019.gross_order_value.sum(), 30.0, 38.0, "{:.1f}")

# ------------------------------------------------------------ 4. monthly P&L
contrib = done.groupby(["ym", "outlet_id"]).contribution.sum().rename("contribution")
outlet_exp = exp[exp.outlet_id.notna()].groupby(["ym", "outlet_id"]).amount.sum().rename("opex")
outlet_pl = pd.concat([contrib, outlet_exp], axis=1).fillna(0)
outlet_pl["net"] = outlet_pl.contribution - outlet_pl.opex

company_exp = exp[exp.outlet_id.isna()].groupby("ym").amount.sum().rename("company_opex")
company = outlet_pl.groupby("ym").net.sum().rename("outlet_net").to_frame()
company = company.join(company_exp).fillna(0)
company["company_net"] = company.outlet_net - company.company_opex

k_2019_net = outlet_pl.xs(1, level="outlet_id").loc["2019-01":"2019-12"]
mature = company.loc["2019-10":"2019-12", "company_net"]
check("Mature monthly company net (Oct–Dec 2019 mean)", mature.mean(), 18000, 75000)

k_only = outlet_pl.xs(1, level="outlet_id").loc["2019-10":"2019-12", "net"]
check("Kandanchavadi outlet net (Oct–Dec 2019 mean)", k_only.mean(), 45000, 80000)
check("Kandanchavadi net after founder drawings", k_only.mean() - 20000, 40000, 55000)

peak = company.loc["2020-01":"2020-02", "company_net"]
check("Jan/Feb 2020 company net (mean)", peak.mean(), 88000, 118000)

w1 = company.loc["2020-04":"2020-05", "company_net"]
check("Wave 1 company net (Apr–May 2020 mean)", w1.mean(), -140000, -55000)

w2 = company.loc["2021-05":"2021-05", "company_net"]
check("Wave 2 company net (May 2021)", w2.mean(), -105000, -10000)

# ------------------------------------------------------------ 5. profit / order
whole = company.company_net.sum() / len(done)
check("Whole-period profit per order", whole, -12, 20, "{:.2f}")
mat_ord = done[(done.ym >= "2019-10") & (done.ym <= "2019-12")]
check("Mature profit/order (Kandanchavadi, post-drawings)", (k_only.mean()-20000)/(len(mat_ord)/3/2), 25, 75, "{:.2f}")

# ------------------------------------------------------------ 6. COVID shape
feb20 = done[done.ym == "2020-02"].shape[0]
apr20 = done[done.ym == "2020-04"].shape[0]
check("Wave 1 volume decline vs Feb 2020 (%)", 100 * (1 - apr20 / feb20), 82, 92, "{:.1f}")
dec19 = done[done.ym == "2019-12"].shape[0]
nov20 = done[done.ym == "2020-11"].shape[0]
check("Late-2020 recovery vs Dec 2019 steady state (%)", 100 * nov20 / dec19, 68, 92, "{:.1f}")

# ------------------------------------------------------------ 7. behaviour
check("Cancellation rate (%)",
      100 * (orders.order_status == "cancelled").mean(), 2.2, 3.6, "{:.2f}")
check("Refund rate (%)",
      100 * orders.order_status.str.startswith("refunded").mean(), 1.0, 2.2, "{:.2f}")
check("Unrated orders (%)", 100 * orders.rating.isna().mean(), 28, 40, "{:.1f}")
late = (done.prep_minutes + done.delivery_minutes) > 55
check("Late orders (%)", 100 * late.mean(), 9, 20, "{:.1f}")
rep = orders.groupby("customer_id").size()
check("Repeat-customer order share (%)",
      100 * (orders.customer_id.isin(rep[rep > 1].index)).mean(), 40, 62, "{:.1f}")

# ------------------------------------------ 7b. newly locked spec inputs
done["yr"] = done.order_datetime.dt.year
aov_y = done.groupby("yr").gross_order_value.mean()
check("AOV envelope min (all years)", aov_y.min(), 390, 450)
check("AOV envelope max (all years)", aov_y.max(), 390, 450)
check("Packaging per order (Rs)", done.packaging_cost.mean(), 15.0, 15.0, "{:.2f}")
check("Food cost % of BASE price",
      100 * 1.15 * done.food_cost.sum() / done.gross_order_value.sum(), 33.5, 36.5, "{:.1f}")
wk = done[(done.outlet_id == 1) & (done.yr == 2019)].copy()
wk["dow"] = wk.order_datetime.dt.weekday
wkd = wk[wk.dow < 5].groupby(wk.order_datetime.dt.date).size()
check("Share of weekdays at 25+ orders (%)", 100 * (wkd >= 25).mean(), 20, 55, "{:.1f}")

# ------------------------------------------------------------ 8. hard constraints
pmap = dict(zip(plat.platform_id, plat.platform_name))
orders["pname"] = orders.platform_id.map(pmap)
ue = orders[(orders.pname == "UberEats") & (orders.order_datetime >= "2020-02-01")]
results.append(("UberEats orders after Jan 2020", f"{len(ue):,}", "0", "PASS" if len(ue) == 0 else "FAIL"))
fp = orders[(orders.pname == "Foodpanda") & (orders.order_datetime >= "2019-10-01")]
results.append(("Foodpanda orders after Sep 2019", f"{len(fp):,}", "0", "PASS" if len(fp) == 0 else "FAIL"))

zero_waste_months = waste.groupby("ym").quantity_kg.sum()
results.append(("Months with zero wastage", f"{(zero_waste_months <= 0).sum()}", "0",
                "PASS" if (zero_waste_months <= 0).sum() == 0 else "FAIL"))

o3 = done[done.outlet_id == 3]
o3_daily = o3.groupby(o3.order_datetime.dt.date).size().mean()
check("Outlet 3 orders/day (mean)", o3_daily, 5, 16, "{:.1f}")
o3_net = outlet_pl.xs(3, level="outlet_id").net
results.append(("Outlet 3 loss-making months",
                f"{(o3_net < 0).sum()} of {len(o3_net)}", "majority",
                "PASS" if (o3_net < 0).mean() > 0.5 else "FAIL"))

# ------------------------------------------------------------ report
print("\n" + "=" * 92)
print("RECONCILIATION HARNESS — generated data vs Phase 1 locked guardrails")
print("=" * 92)
print(f"{'Check':<48}{'Actual':>14}{'Guardrail':>22}{'':>4}")
print("-" * 92)
for name, actual, band, status in results:
    mark = "PASS" if status == "PASS" else "FAIL"
    print(f"{name:<48}{actual:>14}{band:>22}  {mark}")
print("-" * 92)
npass = sum(1 for r in results if r[3] == "PASS")
print(f"{npass}/{len(results)} checks passed")
print("=" * 92)

print("\nScale:")
print(f"  orders          {len(orders):>9,}")
print(f"  order_items     {len(items):>9,}")
print(f"  customers       {len(pd.read_csv(f'{OUT}/customers.csv')):>9,}")

cum = company.company_net.cumsum()
print(f"\nCumulative company net over 57 months: {company.company_net.sum():,.0f}")
print(f"  peak cumulative (pre-COVID high): {cum.max():,.0f} in {cum.idxmax()}")
print(f"  given back during COVID:          {cum.max() - company.company_net.sum():,.0f}")
print("\nCompany monthly net by phase (₹):")
ph = {"pre": ("2018-02", "2020-02"), "wave1": ("2020-03", "2020-05"),
      "reopening": ("2020-06", "2020-09"), "plateau": ("2020-10", "2021-03"),
      "wave2": ("2021-04", "2021-06"), "recovery": ("2021-07", "2022-06"),
      "decline": ("2022-07", "2022-11")}
for k, (a, b) in ph.items():
    seg = company.loc[a:b, "company_net"]
    print(f"  {k:<11} mean {seg.mean():>12,.0f}   min {seg.min():>12,.0f}   max {seg.max():>12,.0f}")
