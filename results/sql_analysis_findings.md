# E-Table Foods — SQL Analytics Findings Summary

**Project:** Cloud Kitchen Unit Economics — SQL Analytics
**Dataset:** 12 tables, ~300,000 rows, 57 months (Feb 2018 – Nov 2022)
**Status:** Phase 5 complete. All figures verified against source data.

> **Dataset disclosure.** Synthetic transactional dataset generated to match the real unit economics of a cloud kitchen I co-founded and operated for four years. Operating figures — order volumes, average order value, platform commission, food-cost ratio, rent, utilities, packaging, staffing, platform history and COVID impact — are real and recalled. Individual transactions, customers, item-level prices and item-level costs are synthetic.

---

## Headline finding

**The business earned its profit on weekends.** Weekdays averaged 24 orders and cleared their daily fixed cost by ₹193. Weekends averaged 54 and cleared it by ₹4,563. **28.5% of the calendar produced 90.4% of the profit.**

This was not visible while the business was operating, and it reframes everything that followed.

---

## Module A — Data Quality & Business Baseline

| Query | Finding |
|---|---|
| **A1 — Outlet scale & lifecycle** | Kandanchavadi: 43,972 orders / ₹1.87 Cr gross across the full 57 months. Outlet 2: 17,100 orders / ₹73.28 L from Jul 2019. Outlet 3: 4,318 orders / ₹18.83 L from Aug 2020 to Apr 2022. Different operating windows mean lifetime revenue alone cannot rank outlets. *(Counts include cancelled orders; revenue analysis uses `order_status <> 'cancelled'` — 42,701 / 16,630 / 4,198.)* |
| **A2 — Delivery-area cleaning** | 30 raw delivery-area variants collapse to 19 real areas after `LOWER`/`TRIM`/punctuation normalisation. Raw cardinality ≠ business cardinality. Cleaning belongs in the analytical layer, not in the source data. |
| **A3 — Order status** | 95.67% completed, 2.85% cancelled, 1.18% partially refunded, 0.31% fully refunded. Total refunded ₹1.15 L. |
| **A4 — Cancellation drivers** | Customer cancellation 34.2%, restaurant delay 24.1%, rider unavailable 18%, item unavailability 14.3%. Roughly 38% of cancellations were operationally controllable. |
| **A5 — Missing data** | 34.1% of ratings are NULL. This is not dirty data — it means the customer did not rate. Coercing NULL to 0 would have destroyed the average rating. Cancellation-reason NULLs are structural: the field applies only to cancelled orders. |

**Takeaway:** Data quality here is semantic, not mechanical. The correct handling of a NULL depends on what the NULL means, and that is a business question before it is a SQL question.

---

## Module B — Unit Economics

| Query | Finding |
|---|---|
| **B1 — Monthly P&L** | Kandanchavadi opened at a ₹38.2K loss in Feb 2018 and reached profitability by Jul 2018. The inflection coincides with the move to direct wholesale sourcing and batch-sized production. |
| **B2 — Revenue share vs profit share** | Kandanchavadi generated **66.9% of revenue and 137% of company profit** — above 100% because the other two outlets were net-negative across their lifetimes. Revenue share and profit share are different measures. **Expansion consumed the hub's profitability.** |
| **B3 — Outlet economics** | Outlet 3 was loss-making in 21 of 21 months. It opened in Aug 2020, into the pandemic, and never reached the volume needed to cover its own rent, staff and utilities. The failure was one of timing, not management — but the decision to open at all was not tested against achievable volume. |
| **B4 — Discount attribution** | Customers saw discounts averaging **10–11% of gross**. Restaurant-funded discount was only **2–3%**. The platform funded roughly three quarters of the discount depth the customer experienced. **Discounted gross is not lost revenue.** Treating the full customer-visible discount as a promotional cost overstates it by roughly 4x. |
| **B5 — Platform shutdown migration** | UberEats ceased Jan 2020, Foodpanda Sep 2019. Volume migrated to Swiggy and Zomato rather than disappearing. The subsequent collapse was COVID, not platform exit — two effects that overlap in time and must be separated before either is interpreted. |

**Takeaway:** Volume drove revenue, but profitability was determined by contribution margin, fixed-cost absorption, and who actually funded the discount.

---

## Module C — Product & Menu Economics

| Query | Finding |
|---|---|
| **C1 — Item volume & margin** | Chicken Biryani – Fry Piece led on volume at 12,843 units and ~₹41.85 L gross. Biryani and chicken products dominate both volume and contribution. |
| **C2 — Menu engineering (Kasavana-Smith)** | Across 17 main-menu items: **6 Stars, 3 Plowhorses, 3 Puzzles, 5 Dogs.** Classification uses volume against 70% of the menu average (the published convention) and contribution per unit against the menu mean. |
| **C2b — Classification robustness** | Mean and median contribution per unit are close, so the quadrant boundaries do not depend on a small number of extreme items. `PERCENTILE_CONT` is unavailable in MySQL 8; median was computed via `ROW_NUMBER()` with `FLOOR`/`CEIL` on the midpoint. |
| **C3 — Dessert discontinuation** ⚠️ | Weekly wastage fell from **16.1 kg to 5.5 kg** in the month desserts were delisted (Aug 2018). **This cannot be attributed to the menu decision.** The same window contains the procurement and batch-sizing change. Desserts were ~5% of order lines and cannot plausibly explain a 65% drop. Two interventions, one observable effect, not separable from this data. Operator judgement: procurement did most of the work — stated as judgement, not evidence. |
| **C4 — Vegetarian expansion** | Vegetarian revenue grew from ₹1.17 L (2018) to ₹7.63 L (2022). Non-veg remained dominant throughout, so the expansion added incremental demand rather than cannibalising the core. |

**Takeaway:** Menu decisions need margin and waste evidence, not just sales rank. And where two changes coincide, the honest answer is that the effects are not separable.

---

## Module D — COVID Shock & Profitability

| Query | Finding |
|---|---|
| **D1 — P&L by COVID phase** | Pre-COVID monthly net averaged **+₹26.2K**. Wave 1 fell to **−₹65.8K**. Recovery averaged **−₹3.4K** — near breakeven, never restored. |
| **D2 — Fixed vs variable cost behaviour** | April 2020: revenue at **9.6%** of the Feb 2020 baseline; fixed costs at **101.1%**. The gap between those two figures *is* the loss. Cost rigidity, not demand loss alone, produced the scale of the shock. |
| **D3 — Survivable order floor** | Breakeven depends on which costs the outlet carries. Against **outlet-level fixed costs (₹77,525/mo): 17.5 orders/day.** Against **outlet plus company overhead including founder drawings (₹100,153/mo): 22.6 orders/day.** Contribution per order: ₹145.68. My operating recollection was ~20/day — **which falls between the two.** Recalled with no reference to any cost breakdown, it converges on figures derived independently from separately recalled costs and transaction-level margin. This is the strongest validation in the project. |
| **D4 — Weekday vs weekend** ★ | Daily fixed cost ₹3,290. **Weekday: 24.0 orders, ₹3,484 contribution/day, +₹193 after fixed cost, 9.6% of profit. Weekend: 53.6 orders, ₹7,853 contribution/day, +₹4,563 after fixed cost, 90.4% of profit.** Weekdays were 71.5% of the calendar and produced under a tenth of the profit. |
| **D5 — Cumulative profitability** | Accumulated net peaked at **₹6.55 L in Feb 2020**, turned negative in **Jun 2021**, and closed at **−₹1.24 L**. The business built ₹6.55 L of retained profit across two pre-COVID years and gave all of it back. |
| **D6 — Growth & contraction** | Peak month Feb 2020: 1,968 orders / ₹8.22 L gross. Orders fell **58.0% MoM in March** and a further **77.2% in April** — a 90.9% cumulative decline. Recovery began May–Oct 2020. |

**Takeaway — and the core of the project:** The weekend concentration in D4 explains the severity in D2 and D5. Breakeven sat at 17.5–22.6 orders/day, so weekday trading was always marginal and the model depended on two days in seven. Lockdown did not remove demand evenly — it removed the weekend surge, which *was* the profit engine, while fixed costs held at 101%. A volume loss concentrated in weekends is far worse than the same percentage spread across the week.

---

## Module E — Customer Economics

| Query | Finding |
|---|---|
| **E1 — Repeat behaviour** | Repeat customers generated the majority of orders on every platform. Swiggy strongest: **38.2% of customers repeated, generating 58.5% of orders.** Zomato 36.8% / 56.9%. Foodpanda 35.2% / 56.4%. UberEats 34.4% / 54.4%. Average 1.44–1.49 orders per customer. Note the two measures answer different questions: *share of customers who repeated* is not *share of orders from repeaters*. |
| **E2 — Cohort retention** ⚠️ | Month-1 retention averaged **~17% across 2019 cohorts**. The apparent rise from 10.8% (Jan) to 26.6% (Nov) **correlates with monthly order volume at r = 0.946** and is a mechanical consequence of a growing customer base, not a behavioural improvement. **Reported as a level, not a trend.** No intervention occurred that would explain a 2.5x improvement, and claiming one would not survive questioning. |
| **E3 — Basket distribution** | Bimodal. **₹250–349: 45.7% of orders, 33.0% of revenue** (single main dish). **₹600–799: 18.9% of orders, 29.2% of revenue** (two mains). A single AOV of ₹409 describes almost no actual order. |

**Structural limitation, stated deliberately:** Aggregators never supplied customer PII to restaurants. Customer references here are masked and platform-scoped, so repeat behaviour is measurable *within* a platform and cross-platform identity is impossible. That is a real constraint of the business model, modelled rather than assumed away — on aggregators you do not own the customer relationship.

**Takeaway:** A meaningful repeat base exists, but the business competed on operations and menu rather than loyalty, because it had no channel through which loyalty could be built. The basket bimodality is the more actionable finding: moving single-main orders into the two-main band is worth more than chasing new customers.

---

## Module F — Operations

| Query | Finding |
|---|---|
| **F1 — Stockout vs wastage** ★ | We deliberately preferred occasional stockouts over guaranteed wastage. Priced out, that preference was expensive. Days with 1–2 items sold out: **4.41 lost orders (₹642 of foregone contribution) to save ₹2 of waste — net −₹640/day**, roughly ₹19,500/month against a ₹77,525 outlet fixed-cost base. Days with 3+ items out were worse on *both* sides: 10.38 lost orders **and higher waste**, because stockouts cluster on high-demand days when the rest of the menu is also over-prepared. **Robustness:** breakeven would require waste savings above ₹642/day against actual savings of ₹2/day, so the conclusion holds at almost any lost-order estimate. |
| **F2 — Delivery time & ratings** | Ratings held at **4.38–4.39 up to 55 minutes**, then fell to **3.45**, with 1–2 star ratings rising to **26.3%**. A service cliff, not a gradient. |
| **F3 — Capacity utilisation** | Prep time held at 20–21 minutes to roughly 70–80% utilisation, then degraded sharply, reaching **29.2 minutes at 132%**. Peak-capacity management matters more than adding permanent capacity. |
| **F4 — Wastage optimisation** | Weekly waste fell from **13–16 kg to 5–7 kg** around month 6 and the improvement was sustained for the remainder of the business. |

**Takeaway:** F1, F2 and F3 connect. Stockouts and long delivery times both cost real money — one in foregone contribution, one in rating damage that feeds platform ranking. The objective was never zero waste or maximum utilisation; it was controlled inventory risk and keeping delivery under the 55-minute cliff.

**F1 is a decision I got wrong.** I optimised the cost I could see in the bin over the revenue I never saw because the item was unavailable. The recommendation is to raise batch sizes on the top five items by volume and accept the additional waste.

---

## Module G — SQL Optimisation

| Query | Finding |
|---|---|
| **G1 — Baseline plan** | The heavy monthly-aggregation query scanned all 65,390 rows and materialised a temporary table, though only 11,654 rows matched the filter. |
| **G2 — Composite index** | `(outlet_id, order_datetime)` converted the access path to an index range scan, letting MySQL narrow on both predicates. |
| **G3 — Sargability** | `YEAR(order_datetime) = 2019` prevents index use; the equivalent range predicate `>= '2019-01-01' AND < '2020-01-01'` preserves it. Same result, different plan. The fix is a rewrite, not a new index. |
| **G4 — Economics view** | `v_order_economics` centralises the order-level food-cost and contribution calculation used by 11 of 24 queries. It encodes the settlement model in one place and makes the delivery-fee exclusion impossible to get wrong by accident. Maintainability and correctness benefit; **no performance claim is made without an execution result.** |

**Takeaway:** Correctness is necessary but not sufficient. Controlling *how* the engine reaches the answer — through plan analysis, indexing, sargable predicates and reusable financial logic — is the difference between a query that works and one that belongs in production.

---

## Overall project finding

**The business earned its profit on weekends.** Weekdays averaged 24 orders and cleared their fixed costs by ₹193 a day; weekends averaged 54 and cleared them by ₹4,563. Twenty-eight percent of the calendar produced ninety percent of the profit.

That structure explains everything that followed. Breakeven sat at **17.5 orders/day against outlet costs and 22.6 against full overhead** — so weekday trading was always marginal and the model depended on two days in seven. When COVID removed the weekend surge, revenue fell to **9.6%** of the February 2020 baseline while fixed costs held at **101.1%**. Accumulated profit peaked at **₹6.55 L** in February 2020, turned negative in June 2021, and closed at **−₹1.24 L**.

Two further findings sharpen it. **Expansion destroyed value:** Kandanchavadi produced 137% of company profit because the newer outlets were net-negative across their lifetimes, and Outlet 3 lost money in every one of its 21 months. **Limited-batch production, adopted to control waste, cost roughly ₹640 a day in foregone contribution to save ₹2 a day in waste** — optimising a visible cost over an invisible one.

None of this was visible while the business was running. All of it was visible in the data within a week of asking the right questions.

---

## Analytical discipline notes

Three places where the obvious reading was wrong, recorded because the reasoning matters more than the result.

**Contribution is not profit (D4).** Weekdays produced 52.7% of *contribution*, which reads as "weekdays carry the business." After subtracting fixed cost — which accrues every day regardless of volume — weekdays produced 9.6% of *profit*. The metric choice inverted the conclusion.

**Two changes, one effect (C3).** Desserts were delisted in the same month procurement changed. The waste drop cannot be assigned to either. Naming a confounder is more useful than choosing the more flattering explanation.

**A trend that tracks volume is not a trend (E2).** Cohort retention appeared to improve 2.5x across 2019. It correlates with order volume at r = 0.946 and no intervention occurred. Reported as a level.

**Scope determines the answer (D3).** The breakeven figure changes from 17.5 to 22.6 orders/day depending on whether company overhead is loaded onto the outlet. Neither is wrong; the question has to specify which costs the unit is asked to carry.
