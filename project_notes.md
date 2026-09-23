# E-Table Foods — Cloud Kitchen Unit Economics
## Master Project Notes

> Internal master notes for the project. This document is broader than the public README and preserves the business context, methodology, findings, recommendations, project decisions, portfolio positioning, interview narrative, and final-quality checklist.

## 1. Project Identity

| Item | Detail |
|---|---|
| Project title | Cloud Kitchen Unit Economics — SQL Analytics |
| Business | E-Table Foods |
| Business type | Delivery-only cloud kitchen |
| Location | Chennai |
| Operating period | February 2018 – November 2022 |
| Role | Co-founder; Operations & Sales |
| Repository | `github.com/manojkumar-dikkala-iitm/cloud-kitchen-unit-economics-sql` |
| Primary stack | MySQL 8.0, MySQL Workbench |
| Supporting stack | Python 3 / pandas for dataset generation and reconciliation; Git |
| Primary deliverable | SQL analytics project |

## 2. Executive Overview

E-Table Foods was a delivery-only cloud kitchen in Chennai operated from February 2018 to November 2022. The business started with one outlet and expanded to three using a hub-and-spoke model.

The original production database, dashboards and reports are no longer accessible. This project therefore reconstructs the transactional layer as a **synthetic dataset calibrated to recalled real-world operating economics**.

The distinction is deliberate:

- Business-level operating anchors are real/recalled.
- Individual transactions are synthetic.
- Customer records are synthetic and platform-scoped.
- Item-level prices and costs are synthetic.
- SQL is the analytical deliverable.
- Python is used for generation and validation, not business analysis.

The generated dataset contains **12 tables and 300,051 rows**, including **65,390 orders**, **111,523 order items**, and **43,838 customer references** across **57 months**.

The generated dataset passed the independent **33/33 reconciliation gate after six calibration passes**.

## 3. Core Project Rules

### SQL is the deliverable

Python exists to manufacture and validate the dataset.

Interview framing:

> The original production database is gone, so I reconstructed a synthetic transactional dataset calibrated to my real operating figures. Generation and reconciliation were done in Python; all business analysis was done in SQL.

### Don't present synthetic transactions as historical records

```text
Real / recalled
    ↓
Business-level operating anchors

Synthetic
    ↓
Transactional detail

Computed
    ↓
SQL analytical outputs
```

### Separate assumptions from findings

```text
Tier 1 → hard constraints
Tier 2 → recalled calibration ranges
Tier 3 → constructed synthetic assumptions
Tier 4 → SQL-derived analytical outputs
```

### Menu Engineering -Do not overclaim as historical practice

Menu engineering was **not** performed at E-Table while the business was operating. The Kasavana-Smith framework is applied retrospectively to the reconstructed dataset.

## 4. Business Context

### Operating model

- Delivery-only cloud kitchen.
- Orders through aggregators.
- Platforms: Swiggy, Zomato, UberEats, Foodpanda.
- Food prepared in the kitchen, packaged, then handed to platform delivery riders.
- Hub-and-spoke expansion from one outlet to three.
- No dine-in or walk-in trade.

### Commercial model

```text
Gross order value
- restaurant-funded discount
- platform commission
- other deductions
- refunds
- food cost
- packaging
= contribution

- outlet operating expenses
= outlet net

- company-level overhead
= company net
```

Two items are deliberately excluded from restaurant P&L treatment:

- Platform-funded discount — customer-visible but funded by the platform.
- Customer delivery fee — paid by the customer to the platform.

## 5. Dataset Architecture

| Table | Grain | Rows |
|---|---|---:|
| `outlets` | one row per physical outlet | 3 |
| `platforms` | one row per platform per commercial-terms period | 4 |
| `menu_items` | one row per menu item | 28 |
| `menu_item_prices` | one row per item × platform × effective price period | 378 |
| `customers` | one row per masked, platform-scoped customer reference | 43,838 |
| `orders` | one row per order | 65,390 |
| `order_items` | one row per line item within an order | 111,523 |
| `promotions` | one row per promotional campaign | 66 |
| `item_availability` | one row per item × outlet × date | 59,465 |
| `wastage` | one row per outlet × date × waste type | 14,604 |
| `expenses` | one row per outlet × month × expense category | 1,101 |
| `daily_operations` | one row per outlet × date | 3,651 |
| **Total** | | **300,051** |

### Normalisation

The model is designed in 3NF with two deliberate point-in-time snapshot exceptions:

1. `orders.commission_amount`
2. `order_items.unit_food_cost`

These preserve historical financial values at order time instead of requiring current reference values to recreate historical economics.

## 6. Final Validation

### Reconciliation status

**33/33 checks passed**

**Calibration passes:** 6

**Dataset scale**

- Orders: 65,390
- Order items: 111,523
- Customers: 43,838

**Cumulative company net:** −₹123,965

**Peak cumulative pre-COVID position:** ₹654,873 in February 2020

**Amount given back during COVID:** ₹778,838

### Key reconciliation outputs

| Metric | Actual |
|---|---:|
| Kandanchavadi mature orders/month (2019 mean) | 944 |
| Weekday orders/day (2019) | 23 |
| Sunday orders/day (2019) | 61 |
| AOV 2019 | ₹410 |
| Line items/order | 1.76 |
| Food cost % of gross (2019) | 29.6% |
| Commission % of gross (2019) | 28.0% |
| Contribution % of gross (2019) | 35.4% |
| Mature company net, Oct–Dec 2019 | ₹36,463 |
| Kandanchavadi outlet net, Oct–Dec 2019 | ₹70,975 |
| Kandanchavadi net after founder drawings | ₹50,975 |
| Jan/Feb 2020 company net mean | ₹96,280 |
| Wave 1 company net, Apr–May 2020 mean | −₹95,094 |
| Wave 2 company net, May 2021 | −₹91,970 |
| Whole-period profit/order | −₹1.95 |
| Mature profit/order, Kandanchavadi post-drawings | ₹68.65 |
| Wave 1 volume decline vs Feb 2020 | 90.9% |
| Late-2020 recovery vs Dec 2019 | 88.5% |
| Cancellation rate | 2.85% |
| Refund rate | 1.49% |
| Unrated orders | 34.1% |
| Late orders | 9.9% |
| Repeat-customer order share | 58.6% |
| AOV minimum, all years | ₹409 |
| AOV maximum, all years | ₹449 |
| Packaging/order | ₹15.00 |
| Food cost % of BASE price | 35.5% |
| Weekdays at 25+ orders | 28.0% |
| UberEats orders after Jan 2020 | 0 |
| Foodpanda orders after Sep 2019 | 0 |
| Months with zero wastage | 0 |
| Outlet 3 average orders/day | 6.6 |
| Outlet 3 loss-making months | 21 of 21 |

### Reconciliation methodology

> The generator does not write directly to target outcomes. It generates individual transactions from behavioural rules such as demand curves, basket composition, price lookups, discount incidence, stockout probability and operating conditions. A separate reconciliation harness measures whether the resulting business falls within recalled operating ranges. Behavioural parameters were tuned; outputs were never manually patched.

## 7. Phase 6 — Business Findings

### A1 — Outlet scale & lifecycle

Kandanchavadi: 43,972 orders / ₹1.87 Cr gross across the full 57 months.

Outlet 2: 17,100 orders / ₹73.28 L from July 2019.

Outlet 3: 4,318 orders / ₹18.83 L from August 2020 to April 2022.

Different operating windows mean lifetime revenue alone cannot rank outlets.

Revenue analysis uses non-cancelled orders:

- Kandanchavadi: 42,701
- Outlet 2: 16,630
- Outlet 3: 4,198

### A2 — Delivery-area cleaning

30 raw delivery-area variants collapse to 19 real areas after lower/trim/punctuation normalisation.

Key lesson:

> Raw cardinality is not business cardinality.

### A3 — Order status

- 95.67% completed
- 2.85% cancelled
- 1.18% partially refunded
- 0.31% fully refunded
- Total refunded: ₹1.15 L

### A4 — Cancellation drivers

- Customer cancellation: 34.2%
- Restaurant delay: 24.1%
- Rider unavailable: 18.0%
- Item unavailability: 14.3%

Roughly 38% of cancellations were operationally controllable.

### A5 — Missing data

34.1% of ratings are NULL. This means the customer did not rate; NULL should not be converted to 0.

### B1 — Monthly P&L

Kandanchavadi opened at a ₹38.2K loss in February 2018 and reached profitability by July 2018. The inflection coincides with direct wholesale sourcing and batch-sized production.

### B2 — Revenue share vs profit share

Kandanchavadi generated 66.9% of revenue but 137.3% of company profit.

The newer outlets were net-negative across their observed operating periods.

### B3 — Outlet economics

Outlet 3 was loss-making in all 21 observed months. It opened in August 2020 and never reached the volume needed to cover its own rent, staff and utilities.

### B4 — Discount attribution

Customers saw discounts averaging about 10–11% of gross. Restaurant-funded discount was only about 2–3%. The platform funded roughly three quarters of the discount depth.

Key lesson:

> Customer-visible discount is not the same thing as restaurant cost.

### B5 — Platform shutdown migration

UberEats ceased in January 2020 and Foodpanda had already ceased restaurant delivery in September 2019.

Aggregate order volume continued through Swiggy and Zomato rather than showing a persistent post-exit disappearance.

Limitation: the data cannot prove individual customer migration because customer identity is platform-scoped.

### C1 — Item volume & margin

Chicken Biryani – Fry Piece led volume at 12,843 units and ~₹41.85 L gross.

Biryani and chicken products dominate both volume and contribution.

### C2 — Menu engineering

Across 17 main-menu items:

- 6 Stars
- 3 Plowhorses
- 3 Puzzles
- 5 Dogs

Popularity uses 70% of the menu-average volume threshold.

Profitability uses contribution per unit against the menu mean.

### C2b — Classification robustness

Mean contribution: ₹200.02

Median contribution: ₹200.11

The closeness of mean and median indicates that the classification is not driven by a small number of extreme-margin items.

### C3 — Dessert discontinuation

Weekly wastage fell from 16.1 kg to 5.5 kg in the month desserts were delisted.

The effect is not causally attributable to dessert removal because procurement and batch-size changes occurred in the same period.

### C4 — Vegetarian expansion

Vegetarian revenue grew from ₹1.17 L in 2018 to ₹7.63 L in 2022.

Non-veg remained dominant. The vegetarian range appears to have added incremental demand rather than cannibalising the core.

### D1 — P&L by COVID phase

- Pre-COVID monthly net: +₹26.2K
- Wave 1: −₹65.8K
- Recovery: −₹3.4K

Recovery came close to breakeven but did not restore prior profitability.

### D2 — Fixed vs variable cost behaviour

April 2020:

- Revenue = 9.6% of February 2020 baseline
- Fixed cost = 101.1% of February 2020 baseline

Key lesson:

> Cost rigidity, not demand loss alone, produced the scale of the shock.

### D3 — Survivable order floor

- 17.5 orders/day against outlet-level costs
- 22.6 orders/day including full company overhead
- Contribution/order: ₹145.68
- Recalled operating floor: ~20 orders/day

The recalled figure falls between the two independently derived thresholds.

### D4 — Weekday vs weekend

Daily fixed cost: ₹3,290

Weekday:

- 24.0 orders/day
- ₹3,484 contribution/day
- +₹193 after fixed cost
- 9.6% of profit

Weekend:

- 53.6 orders/day
- ₹7,853 contribution/day
- +₹4,563 after fixed cost
- 90.4% of profit

Weekends were 28.5% of trading days but generated 90.4% of profit.

### D5 — Cumulative profitability

- Peak cumulative position: ₹6.55 L in February 2020
- Turned negative: June 2021
- Final cumulative position: −₹1.24 L

The business built a retained profit cushion before COVID and then gave it back.

### D6 — Growth and contraction

Peak month:

- February 2020
- 1,968 orders
- ₹8.22 L gross

Orders fell 58.0% MoM in March and another 77.2% in April, producing a 90.9% cumulative decline from February.

### E1 — Repeat behaviour

Repeat customers generated the majority of orders on every platform.

Examples:

- Swiggy: 38.2% of customers repeated; repeaters generated 58.5% of orders.
- Zomato: 36.8% / 56.9%.
- Foodpanda: 35.2% / 56.4%.
- UberEats: 34.4% / 54.4%.

Average: 1.44–1.49 orders per customer.

### E2 — Cohort retention

Month-1 retention averaged about 17% across 2019 cohorts.

The apparent rise from 10.8% to 26.6% correlates strongly with monthly order volume (r = 0.946) and is interpreted as a denominator/base-size effect rather than a demonstrated behavioural improvement.

### E3 — Basket distribution

Bimodal structure:

- ₹250–349: 45.7% of orders, 33.0% of revenue
- ₹600–799: 18.9% of orders, 29.2% of revenue

A mean AOV of around ₹409 describes very few actual orders.

### F1 — Stockout vs wastage

On days with 1–2 items sold out:

- 4.41 lost orders
- ₹642 foregone contribution
- ₹2 waste saved
- net economic difference ≈ −₹640/day

The analysis supports increasing batch sizes for high-volume items.

### F2 — Delivery time and ratings

Ratings remained around 4.38–4.39 through 55 minutes.

Above 55 minutes:

- rating fell to 3.45
- 1–2 star ratings rose to 26.3%

This is a service cliff rather than a smooth gradient.

### F3 — Capacity utilisation

Preparation time remained around 20–21 minutes in normal utilisation ranges.

At 132% utilisation:

- 29.2-minute average preparation time
- roughly 42% longer than a 20.5-minute baseline

The analysis supports managing peak utilisation before investing in permanent additional kitchen capacity.

### F4 — Wastage optimisation

Weekly waste fell from roughly 13–16 kg to 5–7 kg around month 6 and remained sustained afterward.

### G1–G4 — Query optimisation

G1: the heavy monthly aggregation scanned 65,390 rows, with 11,654 matching the filter, and materialised a temporary table.

G2: composite index `(outlet_id, order_datetime)` enables index range access on both predicates.

G3: `YEAR(order_datetime) = 2019` prevents effective range use; a direct date range is sargable.

G4: `v_order_economics` centralises order-level food-cost and contribution logic used by 11 of 24 queries. No unsupported performance claim is made without execution evidence.

## 8. Headline Business Story

> **The business earned most of its profit on weekends.**

Supporting chain:

```text
Weekend concentration
        ↓
Weekdays barely cover fixed cost
        ↓
Business depends on peak-day surplus
        ↓
COVID removes peak demand
        ↓
Revenue collapses to 9.6% of baseline
        ↓
Fixed costs remain at 101.1%
        ↓
Accumulated profit cushion is consumed
        ↓
Cumulative position turns negative
        ↓
Business closes in Nov 2022
```

## 9. Expansion Story

More outlets increased revenue, but did not improve lifetime profitability.

Kandanchavadi generated 66.9% of revenue but 137.3% of company profit.

Later outlets were net-negative:

- Velachery: −₹45,940
- Thoraipakkam: −₹4,76,609

Thoraipakkam was loss-making in 21 of 21 observed months.

Important nuance:

- Outlet timing differed.
- Thoraipakkam opened during COVID.
- Therefore expansion alone should not be presented as causal proof of the losses.

Defensible conclusion:

> Expansion added revenue but reduced lifetime outlet profitability under the observed operating conditions.

## 10. Inventory / Operations Story

Original intuition:

> Small batches reduce visible waste.

SQL finding:

> Small batches can create a much larger invisible cost through lost contribution when high-demand items stock out.

Observed comparison:

```text
₹2 waste saved
        vs
₹642 contribution at risk
```

Operational decision:

- Raise batches for high-volume items.
- Accept controlled additional waste.
- Coordinate inventory with kitchen capacity.
- Protect weekend throughput.

## 11. Menu Story

Retrospective menu analysis:

- Stars → protect
- Plowhorses → improve economics
- Puzzles → promote/reposition
- Dogs → review first for possible delisting

Important disclaimer:

> Menu engineering was applied retrospectively. It was not performed at E-Table during the operating period.

## 12. Customer Story

### Opportunity

Repeat customers accounted for the majority of orders on all four platforms.

### Limitation

Customer references are platform-scoped.

Therefore:

- Within-platform repeat behaviour can be analysed.
- Cross-platform customer identity cannot be established.
- The business did not own the customer relationship in the same way a direct-order channel would.

## 13. Master Recommendations

1. Raise batch sizes on high-volume items — F1.
2. Test breakeven before opening another outlet — B2, D3.
3. Manage weekdays and weekends differently — D4.
4. Separate restaurant-funded and platform-funded discounts — B4.
5. Use outlet-specific breakeven thresholds — D3.
6. Protect the 55-minute service threshold — F2.
7. Concentrate the menu around proven economics — C2.
8. Manage peak capacity before adding permanent kitchen capacity — F3.
9. Target larger baskets rather than headline AOV — E3.
10. Treat platform concentration as a standing risk — B5.

Full recommendation detail belongs in `docs/06_recommendations.md`.

## 14. What the Project Rejects

### Build a bigger kitchen immediately

Capacity constraints appeared primarily at high utilisation. Lower-cost peak management should be tested first.

### Delist all five Dogs immediately

C2 is a review trigger, not an automatic deletion rule. Category coverage and strategic demand matter.

### Chase weekday growth indiscriminately

Weekdays produced only 9.6% of profit.

### Treat platform-funded discounts as free growth

Funding attribution and promotional incrementality are different questions.

### Treat cumulative accounting profit as cash reserve

D5 measures accumulated company net, not a bank balance.

## 15. Analytical Discipline

### Contribution ≠ profit

Weekdays generated 52.7% of contribution but only 9.6% of profit after fixed cost.

### Customer-visible discount ≠ restaurant cost

Customers saw ~10–11% discounts while the restaurant funded only ~2–3%.

### Correlation ≠ behavioural improvement

Cohort retention appeared to rise but tracked customer/order-base growth closely.

### Two changes, one effect

Dessert delisting and procurement improvement coincided, so the waste reduction cannot be causally assigned to either intervention alone.

### Scope changes the breakeven answer

17.5 orders/day against outlet costs versus 22.6 against full company overhead.

### Mean AOV can hide basket structure

The distribution is bimodal; the mean sits between the important basket modes.

## 16. Portfolio / Hiring Value

This project should be positioned as a **business analytics project**, not a coding demonstration.

### What it demonstrates

- Relational data modelling
- SQL joins and aggregation
- CTEs
- Window functions
- Cohort analysis
- Financial modelling
- Unit economics
- Data-quality reasoning
- Operational analytics
- Menu engineering
- Query optimisation
- Index reasoning
- Sargability
- Views
- Documentation
- Analytical judgement

### Differentiators

1. Real operating context
2. Synthetic-data disclosure
3. Independent reconciliation
4. Business-driven SQL questions
5. Financial settlement modelling
6. Operator hindsight
7. Explicit limitations
8. Recommendations tied to quantified evidence

### What not to claim

- The transaction dataset is historical.
- The project recovered the original database.
- Menu engineering was performed at E-Table.
- Cross-platform customer identity is known.
- Promotional incrementality was proven.
- Synthetic outlet localities are historical E-Table locations.

## 17. Recruiter 20-Second Explanation

> I co-founded and ran a cloud kitchen in Chennai. The original production database is gone, so I reconstructed the transactional layer as synthetic data calibrated to the business economics I remember. I validated the reconstruction with 33 independent checks and then used SQL to analyse unit economics, outlet profitability, menu performance, COVID cost behaviour, customer behaviour, operations and query performance. The strongest finding was that weekends generated about 90% of the profit even though they represented about 28% of the calendar.

## 18. Interview — 90-Second Project Story

> I rebuilt the unit economics of a cloud kitchen I used to run as a SQL analytics project.
>
> The production database and dashboards were gone. I documented the operating figures I could reliably recall, separated hard constraints from calibration ranges, designed a relational schema, and generated a synthetic transactional dataset from behavioural rules.
>
> I then built a separate reconciliation harness with 33 checks. It took six calibration passes. I tuned behavioural parameters rather than patching outputs.
>
> After the dataset passed, the analysis itself was SQL. I covered unit economics, platform-funded versus restaurant-funded discounts, menu engineering, COVID cost behaviour, customer cohorts, operations, stockouts, delivery time and query optimisation.
>
> The finding I care about most is one I did not know while operating the business: weekends represented only 28.5% of trading days but generated 90.4% of profit. Weekdays averaged 24 orders and cleared fixed costs by ₹193, while weekends cleared them by ₹4,563.
>
> That explained why COVID was so damaging. We lost the weekend profit engine while fixed costs remained largely in place.
>
> The project also changed some of my operating assumptions. Most notably, I would have increased batch sizes for high-volume items because the data showed that avoiding a few rupees of waste could cost hundreds of rupees of contribution through stockouts.

## 19. Difficult Interview Questions

### “This data is fake. Why should I care?”

> The transactions are synthetic, and I disclose that prominently. The value is in the model and reasoning: the dataset is calibrated to operating economics I actually experienced, independently reconciled, and analysed through business-driven SQL. I would rather present a reconstruction I can fully explain than a public dataset I did not build.

### “How do you know your numbers are right?”

> I do not claim the synthetic transactions are historically exact. I validate whether the resulting business falls inside the operating ranges I remember. The reconciliation harness has 33 checks, and all 33 passed after six calibration passes.

### “Did you really do menu engineering at E-Table?”

> No. I ran the kitchen using intuition and platform dashboards. I never had a formal margin-by-volume framework. I applied the Kasavana-Smith framework retrospectively to the reconstructed dataset to see what I would have done differently.

### “Why don't your customer records represent real customers?”

> Aggregators did not give restaurants usable customer PII. The project therefore uses masked, platform-scoped references. That lets me analyse repeat behaviour within a platform without pretending I can identify the same person across platforms.

### “Why is customer delivery fee excluded?”

> It was paid by the customer to the platform, not retained by the restaurant. Including it in restaurant P&L would distort the economics.

### “Why is food-cost basis different from gross-order basis?”

> The business priced above takeaway on aggregators. Food cost was tied to the base price, not the aggregator-listed gross. The denominator matters.

### “Why not just use revenue to rank outlets?”

> Because revenue and profit are different. Kandanchavadi generated 66.9% of revenue but 137.3% of company profit because the other outlets were loss-making.

### “Why did the business close?”

> It had built a positive cumulative position before COVID, but the demand shock consumed that cushion. Revenue fell to 9.6% of the February 2020 baseline while fixed costs remained at 101.1%, and recovery never restored the previous economics.

## 20. Resume Positioning

### Project title

**Cloud Kitchen Unit Economics — SQL Analytics**

### Project framing

**Problem:** Reconstructed the unit economics of a previously operated cloud-kitchen business after the original production database became unavailable.

**Approach:** Designed a 12-table MySQL model, generated synthetic transactional data in Python, independently reconciled it using 33 checks, and performed all business analysis in SQL.

**Analysis:** Unit economics, outlet profitability, platform discount attribution, menu engineering, COVID cost behaviour, customer cohorts, operational capacity, stockouts, delivery performance and SQL optimisation.

**Result:** Identified that weekends generated 90.4% of profit, established a 17.5–22.6 orders/day breakeven range, quantified stockout versus waste trade-offs, and identified the profitability impact of multi-outlet expansion.

## 21. LinkedIn / Portfolio Positioning

Lead with the business problem and insight.

Preferred sequence:

```text
Real operating experience
    ↓
Data unavailable
    ↓
Reconstruction
    ↓
Validation
    ↓
SQL analysis
    ↓
Business insight
    ↓
Decision
```

Avoid opening with a list of SQL features.

## 22. GitHub Reviewer Journey

The reviewer should be able to understand the project in this order:

```text
README
  ↓
What problem?
  ↓
What did you find?
  ↓
Is the data honestly disclosed?
  ↓
Can I reproduce it?
  ↓
Does the schema make sense?
  ↓
Can I inspect the SQL?
  ↓
Are findings documented?
  ↓
Are assumptions and limitations explicit?
```

Important repository files:

```text
README.md
docs/01_business_context.md
docs/02_data_dictionary.md
docs/03_er_diagram.md
docs/04_assumptions_log.md
docs/05_insights_summary.md
docs/06_recommendations.md
results/reconciliation_report.txt
sql/
generator/
```

## 23. Final Quality Checklist

### Data integrity

- [ ] Synthetic disclosure is prominent.
- [ ] 33/33 reconciliation report exists.
- [ ] No transaction data is described as historical fact.
- [ ] No PII is published.
- [ ] UberEats date constraint remains correct.
- [ ] Foodpanda date constraint remains correct.
- [ ] No zero-wastage periods.
- [ ] ₹15 packaging constraint remains exact.
- [ ] 28% commission constraint remains exact.

### Analytical integrity

- [ ] Platform-funded and restaurant-funded discounts remain separate.
- [ ] Customer delivery fee remains excluded from restaurant P&L.
- [ ] Food-cost denominator is explicit.
- [ ] Contribution is not called profit.
- [ ] Accounting profit is not called cash.
- [ ] Correlation is not presented as causation.
- [ ] Retrospective menu engineering is disclosed.
- [ ] Synthetic outlet localities are disclosed.
- [ ] Customer identity limitations are disclosed.

### GitHub quality

- [ ] README renders cleanly.
- [ ] ER diagram image renders.
- [ ] All Markdown links resolve.
- [ ] No TODOs remain.
- [ ] No broken encoding characters such as `ΓÇ`.
- [ ] No unnecessary duplicate documentation.
- [ ] Code files are named consistently.
- [ ] `.gitignore` is present.
- [ ] Reconciliation report is committed.
- [ ] Final commit history reflects meaningful milestones.

### Interview quality

- [ ] Can explain the project in 20 seconds.
- [ ] Can explain it in 90 seconds.
- [ ] Can explain CTEs.
- [ ] Can explain window functions.
- [ ] Can explain the running total.
- [ ] Can explain sargability.
- [ ] Can explain why the view exists.
- [ ] Can explain the two intentional snapshots.
- [ ] Can defend the 17.5–22.6 orders/day range.
- [ ] Can explain the weekend 90.4% finding.
- [ ] Can explain why the stockout decision was wrong.
- [ ] Can explain why synthetic data is still useful.

## 24. Current Phase 7 Status

### Completed

- [x] Phase 5 SQL analytics
- [x] Phase 6 business interpretation
- [x] `docs/02_data_dictionary.md`
- [x] `docs/04_assumptions_log.md`
- [x] `docs/06_recommendations.md`
- [x] `results/reconciliation_report.txt`
- [x] `README.md` draft
- [x] `docs/er_diagram.png`

### Verify / finalise

- [ ] `docs/03_er_diagram.md`
- [ ] `docs/01_business_context.md`
- [ ] README final link/image audit
- [ ] Markdown rendering audit
- [ ] repository structure audit
- [ ] final Git status
- [ ] meaningful final commit
- [ ] GitHub push
- [ ] public repository review from the perspective of a recruiter

## 25. Final Project Positioning

This project is a bridge between operator experience and analytics:

```text
Operator
    ↓
Understands the business problem
    ↓
Analyst
    ↓
Structures the data
    ↓
Tests assumptions
    ↓
Uses SQL to quantify the problem
    ↓
Makes a recommendation
```

The strongest story is not:

> “I learned SQL and built a project.”

It is:

> **“I had operated a real business, realised that many of my decisions were made without analytical visibility, and rebuilt the economics of that business so I could interrogate those decisions properly.”**

That is the portfolio narrative to protect throughout the README, resume, LinkedIn profile and interviews.
