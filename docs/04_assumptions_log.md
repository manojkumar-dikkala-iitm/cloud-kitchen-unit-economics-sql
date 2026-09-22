# Assumptions Log

## Dataset disclosure

> **Synthetic transactional dataset generated to match the real unit economics of a cloud kitchen I co-founded and operated for four years.**
> 
> The original production database, dashboards and reports are no longer accessible.
> 
> **Real and recalled:** order volumes, average order value, platform commission, food-cost ratio, rent, utilities, packaging cost, staffing, platform history and shutdown dates, outlet expansion, COVID impact, and the survivable order floor.
> 
> **Synthetic:** every transaction row, every customer, every item-level price and cost, discount allocation per order, delivery and preparation times, daily order distribution, and the two synthetic outlet localities.

---

## TIER CLASSIFICATION

### TIER 1 — HARD CONSTRAINTS (may never be violated)

> These are business rules that the dataset must satisfy. They are enforced in the generator or validation process and are not calibration targets.

| Constraint | Value | Enforcement |
|---|---|---|
| Operating period | Feb 2018 – Nov 2022 (57 months) | Generator date bounds |
| Location | Chennai | — |
| Outlet 1 name | Kandanchavadi | Literal |
| Outlet count | 1 → 3, hub-and-spoke | Opening dates |
| Closure | Nov 2022 | Generator terminates |
| Platform commission | 28%, uniform across all platforms | Applied per order |
| Customer delivery charge | 12–15%, customer-paid, EXCLUDED from restaurant P&L | Separate column, never in settlement |
| Food cost basis | 35% of base/takeaway price, not of aggregator gross | Costed off `base_price` |
| Packaging | ₹15.00/order exactly | No inflation permitted |
| Utilities | ₹5,000 per active outlet/month | Per-outlet expense row |
| Rent: central kitchen / Kandanchavadi outlet / Outlet 2 | ₹15,000 / ₹10,000 / ₹15,000 | Expense rows (Outlet 3 rent is Tier 3) |
| Founder drawings | ₹20,000/month from ~Jun 2019 | Company-level, dated |
| Hub staff | ₹40,000/month mature (2 cooks + 1 helper) | Expense row |
| UberEats | Ceases Jan 2020 | Platform effective-dating |
| Foodpanda | Ceases Sep 2019 | Platform effective-dating |
| Customer identity | Masked, platform-scoped, no PII, no cross-platform resolution | Composite key |
| Wastage | Never ₹0 or 0 kg in any period | Floor enforced |
| Desserts | Early experimental window only, then absent | Delist date |
| Menu positioning | Non-veg / chicken / biryani-led | Item weights |
| Veg expansion | Later, customer-driven, limited | Launch dates 2019 |
| Beverages | ~3 SKUs at a time; Soda and Coke strongest | Rotation logic |

**Verified in the loaded database:** 0 UberEats orders after 31 Jan 2020. 0 Foodpanda orders after 30 Sep 2019. 0 months with zero wastage. Packaging exactly ₹15.00 on every fulfilled order. Commission exactly 28.00% of gross (sd 0.000002).

### TIER 2 — CALIBRATION RANGES (must broadly emerge, not be forced)

> These are recalled operating anchors. The generator produces transactions from behavioural assumptions, and the reconciliation process checks whether the resulting business falls within these remembered ranges.

| Anchor | Range | Generated | Status |
|---|---|---|---|
| Mature orders/month, benchmark outlet | 900–950 | 943 mean, 873–1,112 spread, sd 63 | ✓ |
| Monthly gross, mature outlet | ₹3.8–4.0L (envelope ₹3.51–4.28L) | ₹381,844 mean; ₹357,864–441,801 | ✓ |
| AOV envelope | ₹390–450 | ₹409–449 across all five years | ✓ |
| Line items per order | ~1.65 (band 1.55–1.85) | 1.76 | ✓ |
| Normal-good weekday | 25–27 orders | 28.0% of weekdays at 25+; mean 23.1 | ✓ |
| Peak day | 60+ orders | 61 mean Sunday | ✓ |
| Aggregator premium | 10–20%, central ~15% | 1.109–1.193, mean 1.153 | ✓ |
| Food cost vs base price | ~35% | 35.5% | ✓ |
| Advertising | 2–3% normal, 3–5% promo | 2.2% / 3.5% / 3.0% recovery | ✓ |
| Post-optimisation wastage | ~5–6 kg/week | 6.1 kg/week (13.7 in first 6 months) | ✓ |
| Stockout rate | 2–3%, not hard-coded | 2.5% base, weighted to weekends/dinner/peaks | ✓ |
| Restaurant-funded discount | ~18% incidence, ~12% depth | as specified, with monthly variation | ✓ |
| Total discount incidence | ~60% | as specified | ✓ |
| Mature profit, benchmark outlet | ₹40–50K/month (calibration, not target) | ₹44,057 after drawings | ✓ |
| Strong-month benchmark | ₹65K+ | reached in strong pre-COVID months | ✓ |
| Peak profitability | ~₹1 lakh, company-wide scope | ₹97,723 best month | ✓ |
| Wave 1 collapse | ~88% decline | 90.9% | ✓ |
| Late-2020 recovery | ~80% of pre-COVID | 88.5% of Dec 2019 steady state | ✓ |

### TIER 3 — SYNTHETIC ASSUMPTIONS (constructed, documented, defensible)

> The following elements were constructed because the original transactional records are no longer available and these details were not retained as reliable historical facts:

* Individual transaction rows
* Individual customer records and masked platform references
* Item-level prices
* Item-level food costs / COGS
* Per-order allocation of restaurant-funded and platform-funded discounts
* Refund and cancellation events
* Delivery and preparation times
* Daily order distribution
* Repeat-customer behaviour
* Monthly expense detail
* Daily operating conditions
* Outlet 3 rent
* Spoke staffing assumptions
* Outlet 2 and Outlet 3 localities
* Daypart distribution
* Rating distribution
* Unrated-order share
* Cancellation and refund rates
* Item-level stockout estimates
* Item-level volume distribution
* Historical price changes across the modeled period

These assumptions were constructed to produce a realistic transactional system that reconciles to the recalled business-level anchors. They are not claims about individual historical transactions.

### TIER 4 — ANALYTICAL OUTPUTS

> These were not used as generator targets. They are conclusions calculated from the reconstructed transactional dataset through SQL analysis:

* Menu-engineering quadrant classification
* Item-level contribution and margin
* Platform-level profitability and contribution
* Revenue-share versus profit-share divergence
* Customer repeat behaviour
* Cohort retention
* Basket distribution
* Fixed versus variable cost behaviour
* Outlet breakeven order floor
* Weekday versus weekend profit concentration
* Stockout-versus-wastage trade-off
* Delivery-time service threshold
* Kitchen-capacity relationship
* Association between kitchen utilisation and late-delivery rate
* Cumulative profitability
* Platform-discount funding exposure
* Platform shutdown volume migration pattern
* Outlet expansion profitability

---
## Reconciliation

The generator does not write directly to target outcomes.

It generates individual transactions from behavioural rules including demand curves, basket composition, price lookups, discount incidence, stockout probability and operating conditions. A separate reconciliation harness then measures whether the resulting business falls within the recalled operating ranges.

**33 reconciliation checks were used. Six calibration passes were required. Behavioural parameters were tuned; outputs were never manually patched.**

The reconciliation report is retained separately in:

`results/reconciliation_report.txt`

The final dataset passed the complete **33/33** reconciliation gate before the SQL analysis was performed.

---
## Contradictions found in my recollection, and how each was resolved

Eleven recalled figures or descriptions were mutually incompatible. Rather than forcing the dataset to satisfy all of them simultaneously, each conflict was resolved by identifying which observation had the stronger factual or operational basis.

|ID|Conflict|Resolution|Basis|
|-|-|-|-|
|**C1**|**28% commission + 12–15% delivery charge** appeared to imply a **40–43% platform take** from restaurant economics.|The **12–15% delivery charge is customer-paid** and therefore does not enter the restaurant P&L. The **28% commission remains the restaurant charge**.|Corrected settlement model; customer delivery fee is stored separately and excluded from restaurant economics.|
|**C2**|Outlet 3 recalled as a residual/very-low-volume outlet, which would imply **under 5 orders/day for roughly two years**.|Outlet 3 opened in **mid 2020**, operates at roughly **6–14 orders/day**, never reaches a mature-volume phase, and is restructured in **April 2022**.|The observed operating window and pandemic launch timing make a sustained sub-5-order interpretation implausible.|
|**C3**|**25–27 weekday orders + Sunday 62 + Saturday 70% of Sunday + 900–950 monthly orders** cannot all represent simple arithmetic averages.|**25–27 orders** is treated as a **normal-good weekday level**, not the arithmetic weekday mean. The **900–950 monthly figure is binding**.|Arithmetic: 26 orders/day on weekdays combined with the weekend figures implies approximately **1,022 orders/month**, above the recalled 900–950 range.|
|**C4**|A flat **₹400 AOV** conflicts with price changes occurring over a **57-month** period.|A **₹390–450 AOV envelope** is used, allowing AOV to emerge from item mix and price history rather than forcing a flat ₹400 transaction value.|Operator revision; the monthly and yearly AOV results are generated bottom-up.|
|**C5**|Recalled **₹65K+ monthly profit** and **~₹1 lakh profit** could not both represent per-outlet steady-state profit.|These figures are treated as **company-wide / strong-month observations**, while per-outlet mature profit is calibrated separately.|At 28% commission and ~35% food cost, approximately 63% of gross is consumed before fixed costs, making a sustained ₹1 lakh per outlet inconsistent with the other anchors.|
|**C6**|**₹20K founder drawings** were remembered both as an expense and as part of reported profit.|Profit is reported **before and after founder drawings separately**.|Counting the same ₹20K as both an expense and profit would double-count the same rupees.|
|**C7**|Hub-level costs were initially being applied uniformly to spoke outlets.|The model keeps separate outlet structures: **hub ₹67,203; spokes ₹59,909 and ₹49,805, all excluding advertising, which is volume-linked at 2–3% of gross. Including advertising the mature figures are ₹77,525 and ₹65,356, which are the values used in the D3 breakeven analysis**.|Follows the recalled hub-and-spoke operating model and separate outlet cost structures.|
|**C8**|A recalled **42-minute average delivery time** conflicts with a recalled **13% late rate at a 45-minute threshold**.|**45 minutes** is treated as the customer promise; **55 minutes** is treated as the operational/service threshold identified in the reconstructed analysis.|A 42-minute mean would imply substantially more than 13% of observations above 45 minutes under a plausible distribution.|
|**C9**|Recalled **₹30–35 profit/order** conflicts with the reconstructed whole-period economics.|The dataset produces approximately **₹68 per order of outlet net in the mature period** and **−₹1.95 per order of company net across the full period** (−₹123,965 across 63,529 completed orders).|The business accumulated profit before COVID but ultimately gave it back; a single whole-period ₹30–35 figure does not describe either period correctly.|
|**C10**|Recalled recovery to **80% of pre-COVID** was ambiguous because the comparison baseline was unclear.|Recovery is measured against the **December 2019 steady-state baseline**, producing **88.5%** rather than comparing against the exceptional February 2020 peak.|December 2019 is a more representative pre-COVID operating baseline than the February 2020 peak month.|
|**C11**|Beverage food cost recalled at **64% of base price** was inconsistent with a wholesale-cost interpretation.|Beverage food cost is modelled at **40–52%**, reflecting plausible wholesale cost relative to the selling price.|Example anchor: a ₹40 cola with approximately ₹20–22 wholesale cost implies roughly 50–55%, not 64%.|

---
## Independent validation

I recalled a survivable floor of roughly 20 orders per day, with no cost breakdown in front of me. Breakeven computed from separately recalled fixed costs and a contribution margin derived from transaction data gives **17.5 orders/day against outlet costs and 22.6 orders/day against full company overhead**. The recalled figure falls between the two.

Two independent recollections converging is the strongest evidence available when reconstructing a business from memory.

## Limitations

1. Transaction rows are synthetic. Individual orders and individual customer behaviours are therefore not historical facts.
2. Item-level prices and food costs are derived to reconcile with business-level anchors; they were not individually recalled.
3. Cross-platform customer identity is impossible to establish because aggregator customer references are platform-scoped.
4. Promotional incrementality cannot be measured because the dataset contains no holdout/control group.
5. Menu engineering was **not** used while the business was operating. The Kasavana–Smith framework is applied retrospectively to the reconstructed dataset.
6. Two of the three outlet localities are synthetic and must not be interpreted as historical E-Table locations.
7. The dataset can identify relationships and patterns within the reconstructed model, but it cannot prove that every historical operational decision would have produced the same result under real-world conditions.
8. Causal claims are limited where multiple changes occurred at the same time. For example, the wastage reduction coincided with both procurement/batch-sizing changes and dessert delisting.

---
## Why I am comfortable presenting a synthetic reconstruction

> I would rather present a reconstruction I can fully explain than a downloaded dataset I did not build.

