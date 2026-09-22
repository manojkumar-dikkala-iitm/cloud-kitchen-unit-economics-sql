# Insights Summary

Twelve business questions, answered in SQL against a reconstructed transactional dataset covering 57 months of cloud-kitchen operations (Feb 2018 – Nov 2022).

> \\\*\\\*Dataset disclosure.\\\*\\\* Synthetic transactional dataset generated to match the real unit economics of a cloud kitchen I co-founded and operated for four years. Operating figures — order volumes, average order value, platform commission, food-cost ratio, rent, utilities, packaging, staffing, platform history and COVID impact — are real and recalled. Individual transactions, customers, item-level prices and item-level costs are synthetic.

## How to read this

Each entry follows the same six-part structure: the business question, the SQL approach, the result, what it means, what I would do, and what it is worth.

## Definitions

* **Contribution** — order value less restaurant-funded discount, platform commission, other platform deductions, refunds, food cost and packaging. Excludes fixed costs.
* **Outlet net** — contribution less the operating costs assigned to that outlet (staff, rent, utilities, gas, procurement, repairs, advertising).
* **Company net** — outlet net less company-level costs no single outlet carries: central kitchen rent, compliance and founder drawings.
* **Restaurant-funded discount** — promotional cost I bore. Reduces my realisation.
* **Platform-funded discount** — promotional cost the aggregator bore. Visible to the customer, does **not** reduce my realisation.
* **Customer delivery fee** — paid by the customer to the platform. Never deducted from restaurant revenue.

## ⚠️ Scope note — read before comparing any two profit figures

Two different profit measures appear in this document and they are not interchangeable.

**Outlet net** (used in B2, B3, D3) deducts only outlet-assigned expenses. It answers: *did this kitchen cover its own costs?*

**Company net** (used in D1, D2, D5) additionally deducts ₹15.25 L of lifetime company-level cost — central kitchen rent ₹6.15 L, founder drawings ₹8.40 L, compliance ₹0.70 L. It answers: *did the business make money?*

Lifetime reconciliation:

||Amount|
|-|-|
|Sum of outlet net (B2)|**+₹14.01 L**|
|Less company-level costs|**−₹15.25 L**|
|**Company net (D5)**|**−₹1.24 L**|

Both figures are correct. Neither is the answer on its own.

\---

# 1\. D4 — Which days of the week actually made us money?

### 1\. Business question

While running the kitchen I knew weekends were busier, but I wanted to understand **where the profit was actually coming from.** Were weekdays carrying the business because they happened more often, or were weekends generating most of the money despite being only two days in seven?

### 2\. SQL approach

I grouped completed trading days into weekdays and weekends and calculated average daily orders, contribution, and the amount remaining after the daily fixed-cost burden.

I used profit after fixed cost rather than contribution alone because fixed costs are incurred every trading day regardless of volume. The distinction matters: contribution shows what a day's orders generated *toward* fixed costs; the remainder shows what that day actually added to profit.

### 3\. Result

|Measure|Weekday|Weekend|
|:-:|:-:|:-:|
|Trading days|304 (71.5%)|121 (28.5%)|
|Avg. orders/day|24.0|53.6|
|Avg. contribution/day|₹3,484|₹7,853|
|Daily fixed cost|₹3,290|₹3,290|
|**After fixed cost/day**|**₹193**|**₹4,563**|
|**Share of total profit**|**9.6%**|**90.4%**|

Weekends were **28.5% of the calendar** and generated **90.4% of the profit.**

### 4\. Interpretation

This changed how I would describe the business.

At first glance the contribution numbers point the other way. Weekdays generated **52.7% of total contribution** against 47.3% on weekends. It would be easy to conclude that weekdays were carrying the business.

That is not what happened.

The kitchen absorbed roughly **₹3,290 of fixed cost every day**, weekday or weekend. A weekday generated ₹3,484 of contribution, leaving **₹193** — a 6% cushion. One quiet Tuesday put the day underwater. A weekend generated ₹7,853, leaving **₹4,563**.

So the business was not earning its profit evenly across the week. **Weekdays were near-breakeven days; weekends were the profit engine.**

This also explains why the COVID shock was so damaging. The problem was not simply that total orders fell. The model lost the high-volume days that generated almost all of the surplus, while the fixed-cost base remained in place.

The metric choice inverted the conclusion. That is the analytical lesson here as much as the business one.

### 5\. Recommended action

I would manage weekdays and weekends differently rather than treating every trading day as equivalent.

**Weekdays:**

* Keep the operation lean and focus on covering the daily fixed-cost base.
* Avoid adding permanent capacity or staffing purely to lift weekday volume unless the additional demand clearly moves the day beyond marginal profitability.
* Monitor whether weekday volume is consistently approaching the breakeven floor from D3.

**Weekends:**

* Protect availability of the highest-volume items.
* Increase preparation capacity and batch sizes ahead of expected peak demand.
* Prioritise preventing stockouts and delivery-time deterioration — these are the days where a lost order has the highest economic value.
* Treat weekend capacity as profit protection, not merely a response to higher volume.

Plan capacity and inventory around the weekend profit engine while keeping the weekday cost structure disciplined.

### 6\. Business impact

**₹4,563 − ₹193 = ₹4,370 more post-fixed-cost surplus on an average weekend day.**

Aggregate contribution was close to even — weekday ₹10,59,023 against weekend ₹9,50,218. But after the fixed-cost burden, **9.6% of profit came from weekdays and 90.4% from weekends.**

An average weekend day generated roughly **23.6× the post-fixed-cost surplus of an average weekday** (₹4,563 ÷ ₹193).

That is the economic reason weekend demand mattered so much to survival, and the key connection to the COVID analysis: **when the profit engine is concentrated in two days out of seven, a shock that removes weekend demand destroys profitability far faster than the same percentage decline spread evenly across the week.**

\---

# 2\. D3 — Below what volume was an outlet not worth keeping open?

### 1\. Business question

I remembered that an outlet needed roughly 20 orders a day to remain viable. I wanted to test that recollection against the reconstructed unit economics and identify the daily order floor at which an outlet stopped covering its costs.

### 2\. SQL approach

I used outlet-level contribution per order together with the monthly fixed-cost base to calculate the orders required to reach breakeven, then converted the monthly requirement to a daily figure.

**Two scopes, deliberately.** Outlet-level fixed costs answer whether the kitchen covered its own costs. Adding company overhead — central kitchen rent, compliance, founder drawings — answers whether it covered its share of the business. Both are legitimate; the answer differs and the difference is the point.

**Window:** Jan 2019 – Feb 2020, the mature pre-COVID period. Thoraipakkam opened in August 2020 and is therefore outside this window — it never had a mature pre-COVID period, which is itself the finding in B2.

### 3\. Result

Outlet-level scope:

|Outlet|Contribution/order|Monthly fixed cost|Breakeven orders/month|Breakeven orders/day|
|:-:|:-:|:-:|:-:|:-:|
|E-Table Velachery|₹145.02|₹65,356|451|**14.8**|
|E-Table Kandanchavadi|₹145.68|₹77,525|532|**17.5**|

Kandanchavadi with company overhead loaded on:

|Basis|Monthly fixed cost|Breakeven orders/day|
|:-:|:-:|:-:|
|Outlet costs only|₹77,525|**17.5**|
|Outlet + company overhead (₹22,629/mo)|₹1,00,153|**22.6**|

### 4\. Interpretation

**My remembered figure of \~20 orders/day falls between the two derived breakeven points.**

This is the strongest validation in the project. The \~20/day figure was recalled with no cost breakdown in front of me. The 17.5 and 22.6 figures were derived independently — from separately recalled fixed costs and a contribution margin computed from transaction-level data. Two independent routes converging on the same region is the best evidence available when reconstructing a business from memory.

It also explains *why* my recollection sat where it did. As an operator I was feeling both constraints at once: enough volume to keep the kitchen comfortable, not quite enough to cover the business.

More importantly, the calculation shows that **order volume alone was not the threshold.** The same volume produces different outcomes depending on fixed costs and contribution per order. Kandanchavadi needed about 2.7 more orders per day than Velachery purely because of its higher fixed-cost base.

This changes how I would read a low-volume period. An outlet at 10–12 orders/day was not having a weak sales day; it was operating below the level required to recover its fixed costs. Moving from 15 to 18 orders/day mattered far more than the word "growing" suggests.

This is a reconstructed breakeven estimate, not a historical operating rule the business explicitly used at the time.

### 5\. Recommended action

Establish outlet-specific monitoring thresholds rather than one common target:

1. **\~15 orders/day** as the warning threshold for a lower-fixed-cost outlet such as Velachery.
2. **\~18 orders/day** for a higher-fixed-cost outlet such as Kandanchavadi.
3. **\~23 orders/day** as the threshold at which the outlet is covering its share of company overhead, not just its own costs. Use this one for capital-allocation decisions.
4. If an outlet stays below its threshold for a sustained period, review staffing, hours and other fixed costs before spending more on demand generation.
5. Use contribution per order and fixed cost together — never revenue or order count alone.

### 6\. Business impact

The immediate value is the ability to quantify the minimum volume required. For Kandanchavadi:

**₹77,525 ÷ ₹145.68 = 532 orders/month ≈ 17.5 orders/day** (outlet costs)
**₹1,00,153 ÷ ₹145.68 = 688 orders/month ≈ 22.6 orders/day** (with company overhead)

For illustration at 10 orders/day the outlet generates about **₹1,457/day** of contribution against **₹2,549/day** needed at the 17.5-order floor — a gap of **₹1,092/day**, roughly **₹33,250 over a 30.44-day month**, before any change to the cost structure.

This makes the floor a management trigger. Once volume falls materially below it, the question shifts from *"how do we get more orders?"* to *"can this outlet's cost structure support the current demand?"*

\---

# 3\. F1 — Was it cheaper to run out of food or to throw it away?

### 1\. Business question

I deliberately preferred smaller production batches because throwing food away felt more expensive than occasionally running out of an item.

The question: **was that actually the cheaper decision, or was I protecting a visible cost in the bin while losing more money through unavailable food?**

### 2\. SQL approach

I grouped days by the number of items that sold out and measured both sides of the decision: waste avoided, and orders and contribution lost because customers could no longer buy the unavailable items.

The comparison is at daily level because stockout and wastage are decisions made during individual trading days, not monthly accounting effects. Both sides are expressed in rupees — comparing "4.41 lost orders" against "0.02 kg saved" is not a comparison.

### 3\. Result

|Stockout level|Days|Lost orders/day|Waste cost/day|Lost contribution/day|Net|
|:-:|:-:|:-:|:-:|:-:|:-:|
|None|996|0.00|₹125|₹0|**baseline**|
|1–2 items out|720|4.41|₹123|₹642|**−₹640**|
|3+ items out|48|10.38|₹137|₹1,511|**−₹1,524**|

On days with 1–2 items sold out, the business gave up **₹642 of contribution to save ₹2 of waste** — approximately **₹640 of net economic loss per affected day.**

The 3+ category was worse on both sides: more orders lost *and* higher waste, indicating that stockouts clustered on high-demand days when the rest of the menu was also being over-prepared.

### 4\. Interpretation

This is one of the operating decisions I got wrong.

I was optimising the cost I could **see** — food in the bin at the end of a shift — against revenue I could not see, because the customer simply saw "unavailable" and ordered elsewhere. The trade-off was nowhere close: **₹2 of waste saving against ₹642 of foregone contribution.**

The more damaging point is that stockouts were not happening on quiet days. They clustered on busy ones. That makes the decision worse: an item running out during a peak prevents a valuable order from completing, while the remaining menu still generates preparation and waste.

The objective should not have been **minimum possible waste.** It should have been **minimum total economic loss from waste and lost sales combined.**

**Robustness.** Breakeven would require waste savings above ₹642/day against an observed saving of ₹2/day. The lost-order estimate is a modelled parameter, so the exact ₹642 is not load-bearing — but the conclusion holds at essentially any lost-order rate above zero. It does not depend on a finely balanced estimate.

### 5\. Recommended action

1. **Increase batch sizes for the top five items by volume**, particularly on expected high-demand days.
2. Accept some additional waste as an intentional cost of availability rather than treating every discarded portion as a failure.
3. Monitor stockouts separately for high-volume items instead of applying one conservative batch rule to the whole menu.
4. Use **lost contribution versus waste avoided** as the decision metric — not waste kilograms or food cost.
5. Treat repeated stockouts on high-demand days as a stronger warning signal than small increases in end-of-day waste.

The practical rule: **if preventing a stockout costs a few rupees of additional waste but the contribution at risk is hundreds of rupees, produce the additional batch.**

### 6\. Business impact

Eliminating 1–2 item stockouts across the 720 affected days recovers approximately:

**4.41 × ₹145.68 × 720 = ₹4.63 L of contribution** over the analysed period

against additional waste cost in the low tens of thousands. Roughly **₹19,500/month per outlet** — about a quarter of Kandanchavadi's ₹77,525 fixed-cost base.

\---

# 4\. B4 — Were platform discounts actually costing us money?

### 1\. Business question

Customers were regularly seeing discounts, so it was easy to assume the business was giving away 10–11% of sales through promotions.

The more specific question: **how much of that discount actually came out of the restaurant's pocket?**

### 2\. SQL approach

I separated the customer-visible discount into restaurant-funded and platform-funded components and compared each against gross order value.

This distinction was necessary because the discount shown to the customer is not automatically a restaurant cost. Only the restaurant-funded portion reduces my realisation. The schema stores them as two separate columns precisely so they cannot be conflated.

### 3\. Result

|Measure|Finding|
|:-:|:-:|
|Customer-visible discount|**10.93%** of gross|
|Restaurant-funded discount|**2.50%** of gross|
|Platform-funded discount|**8.44%** of gross|
|Platform share of discount depth|**77.2%**|
|Overstatement if full discount treated as our cost|**4.38×**|

In rupees, across 57 months on ₹2.71 Cr of gross:

|Promotional expense line|Amount|
|:-:|:-:|
|What the platform dashboard displayed|**₹29.63 L**|
|What actually came out of my pocket|**₹6.77 L**|
|**Phantom cost**|**₹22.86 L**|

### 4\. Interpretation

The obvious reading would have been: *"we are giving customers 10–11% discounts, so promotions cost us 10–11% of revenue."* That would have been wrong by a factor of 4.38.

**Why the ₹22.86 L matters, given that it never touched my P\&L.** It is not a benefit I received — it is the size of an accounting error I could have made. Booked as my own promotional cost it works out to **₹40,100 per month**, against a pre-COVID company net of **₹26,195 per month.**

Had I recorded the dashboard figure as my cost, **my P\&L would have shown a loss in every month of the business's life, including the profitable ones.** I would have concluded promotions were destroying the business. The rational response — cutting promotional participation — would have reduced volume, and therefore contribution, against a fixed-cost base already committed.

That is not an accounting curiosity. It is a decision I could plausibly have got wrong, and ₹22.86 L is the size of the trap.

**The second reading is exposure, not windfall.** 42.2% of orders, carrying **₹1.14 Cr of gross revenue**, arrived with a platform-funded discount attached. That is a dependency: two-fifths of revenue rested on promotional spend I did not control, could not forecast and had no contractual claim to. If a platform reduced campaign intensity, that volume moved with no action on my part.

**What this analysis does not establish.** It measures who funded the discount, not whether the discount generated incremental profitable demand. Without a holdout group I cannot separate demand the promotion *created* from demand it merely *subsidised* — many of those orders would not have existed at full price. So I would not describe the ₹22.86 L as value the platforms delivered to me.

I also cannot claim that platform discounting was withdrawn. In this dataset platform-funded discount as a share of gross **rises** across the period, from 7.78% in 2018 to 8.98% in 2022. The exposure existed; a withdrawal is not something I observed.

### 5\. Recommended action

1. **Stop treating customer-visible discount percentage as restaurant promotional cost.**
2. Track restaurant-funded and platform-funded discount as separate financial fields — as this schema does.
3. Evaluate promotions on the restaurant-funded amount and the resulting contribution, not the headline discount.
4. Before increasing restaurant-funded promotions, verify that the additional volume generates enough contribution to justify the discount.
5. Recognise the platform-funded share as a revenue dependency and monitor it. Two-fifths of revenue resting on someone else's promotional budget is a risk that belongs on the register, whether or not it ever materialised.

### 6\. Business impact

**10.93% customer-visible − 2.50% restaurant-funded = 8.44 percentage points funded by the platform**, a **4.38× overstatement** if the full discount is booked as my cost.

The correction to the unit-economics model: promotional cost should carry **₹6.77 L**, not **₹29.63 L** — a **₹22.86 L** difference over 57 months, or **₹40,100 per month** against a pre-COVID monthly net of ₹26,195.

The dependency figure is the other half: **₹1.14 Cr of gross revenue (42.2% of orders) arrived on platform-discounted orders.**

\---

# 5\. D2 — When revenue fell 90%, which costs fell with it?

### 1\. Business question

**When lockdown removed almost all demand, how much of the cost base actually went away with it?**

### 2\. SQL approach

I indexed both revenue and cost to February 2020, the last normal pre-COVID month, and tracked each as a percentage of that baseline through the lockdown period. Costs were grouped by the `cost\\\_behaviour` classification — fixed, semi-variable, variable — held in the `expenses` table, which turns the analysis into a single grouped comparison rather than a hand-maintained set of conditions.

### 3\. Result

April 2020 against the February 2020 baseline:

|Measure|% of Feb 2020|
|:-:|:-:|
|Revenue|**9.6%**|
|Fixed costs|**101.1%**|

### 4\. Interpretation

The problem was not simply that we lost 90% of revenue. **Almost none of the fixed-cost burden disappeared with it.**

Revenue moved from 100% to 9.6% while fixed costs stayed slightly above baseline at 101.1%. The business lost the contribution that normally absorbed rent, salaries, utilities and other commitments, while those commitments continued unchanged.

So the shock was **a cost-rigidity problem as much as a demand problem.**

This connects directly to D4. The business was already dependent on a small number of high-volume weekend days to generate its profit, with weekdays clearing costs by only ₹193. When COVID removed weekend demand there was no weekday surplus available to absorb the fixed-cost base.

I would not describe April 2020 as *"sales collapsed because of lockdown."* The useful operator interpretation is: **the business had a cost structure designed for normal trading volume, and revenue disappeared far faster than costs could be reduced.**

### 5\. Recommended action

Build an explicit **low-volume survival plan** rather than assuming normal cost behaviour during a crisis:

1. Identify which costs can genuinely be reduced within days, weeks and months.
2. Stop treating all operating costs as equally fixed — separate unavoidable commitments from costs that can be renegotiated or scaled.
3. Establish a minimum operating model for periods of sharp demand loss.
4. Use the D3 breakeven level as an early warning point rather than waiting for monthly losses to accumulate.
5. Before any expansion, test the business against a severe volume contraction.

The expansion question should not only be *"can this outlet make money at expected volume?"* but **"what happens if volume falls by 50%, 70% or 90%?"**

### 6\. Business impact

**Revenue retained = 9.6%. Fixed costs retained = 101.1%.**

The revenue-to-fixed-cost relationship deteriorated by approximately **101.1 ÷ 9.6 ≈ 10.5×**. Relative to February 2020, the same fixed-cost burden was being supported by roughly one-tenth of the revenue base.

That is why the business moved from normal profitability to severe loss within weeks. Not simply lower sales — **high operating leverage combined with a sudden loss of demand.**

\---

# 6\. C2 — Which menu items should we have delisted, and when?

### 1\. Business question

The menu had a few items that sold regularly and many that contributed much less volume.

**If I had applied a proper margin-versus-volume framework while operating, which items would have been delisting candidates, and which should I have protected?**

### 2\. SQL approach

I applied the **Kasavana–Smith menu-engineering framework** to the reconstructed item-level data. Each item was classified on two dimensions: popularity, based on whether its volume exceeded 70% of the menu average (the published convention), and profitability, based on whether contribution per unit exceeded the menu average.

I checked the contribution boundary against the median as well. Mean contribution was **₹200.02** and median **₹200.11**, so the classification is not being driven by a few extreme-margin items. `PERCENTILE\\\_CONT` is unavailable in MySQL 8, so the median was computed with `ROW\\\_NUMBER()` and a `FLOOR`/`CEIL` midpoint selection.

### 3\. Result

17 main-menu items. Menu average contribution **₹200.02/unit**; popularity threshold **3,508 units** (70% of the 5,011-unit average).

|Quadrant|Items|Count|
|:-:|:-:|:-:|
|⭐ **Stars**|Chicken Biryani – Fry Piece (12,843 u, ₹222.06), Boneless (11,377 u, ₹252.28), Dum (8,436 u, ₹237.67), TN Style Chicken Biryani (6,255 u, ₹215.67), Dum Chicken Curry (3,828 u, ₹205.78), Dragon Chicken (3,517 u, ₹205.34)|6|
|**Plowhorses**|Chicken Curry (9,214 u, ₹198.33), Chilli Chicken (9,030 u, ₹194.63), Chicken Lollipop (5,011 u, ₹199.30)|3|
|**Puzzles**|Fry Piece Chicken Curry (3,341 u, ₹200.11), Boneless Chicken Curry (3,150 u, ₹210.74), Butter Chicken Masala (1,172 u, ₹216.27)|3|
|**Dogs**|Veg Thali Meals (2,336 u, ₹189.21), Paneer Fry (1,809 u, ₹165.33), Paneer Masala (1,359 u, ₹172.17), Gobi Manchurian (1,387 u, ₹160.79), Channa Masala (1,118 u, ₹154.62)|5|

### 4\. Interpretation

The obvious temptation is *"Dogs should have been removed."* I would be more careful.

The analysis says these five were the weakest combination of volume and contribution. That makes them the **first candidates for review**, because they neither generated enough demand nor compensated for low demand with above-average contribution.

The stronger signal is the contrast with the Stars. The three main biryanis alone accounted for 32,656 units at ₹222–252 contribution each — high volume *and* above-average margin simultaneously.

Note how close the Plowhorses sit to the boundary: ₹194.63 to ₹199.30 against a ₹200.02 average. They are popular items falling marginally short on margin, which makes them candidates for a price or recipe adjustment rather than removal. A ₹5–6 improvement in contribution per unit would reclassify all three.

The Puzzles matter most. Fry Piece Chicken Curry, Boneless Chicken Curry and Butter Chicken Masala had above-average contribution but low volume. Their unit economics were not the problem — demand was. I would not delist these; they need positioning, visibility, pricing or promotion.

So the retrospective lesson is not *"remove low sellers."* It is: **concentrate the menu around items that already demonstrate both demand and economics, and challenge low-volume items that do not earn their place.**

**Most importantly, this is a retrospective analytical exercise, not evidence that these exact delistings should have happened on a particular date.** The item-level prices and costs are synthetic, so assigning a precise historical delisting date would overstate what the data can support. Menu engineering was not used while the business was operating; it is being applied retrospectively to reconstructed data.

### 5\. Recommended action

A staged decision rather than deleting every Dog:

1. **Review the five Dogs first** — the strongest delisting candidates on both dimensions.
2. Check whether any serve a strategic purpose, such as satisfying a specific customer segment or completing a meal category. Four of the five are vegetarian, which was added in response to repeated customer requests — that is a strategic reason to retain at least some coverage.
3. If no strategic reason exists, **test removing the weakest items first** rather than cutting all five at once.
4. **Protect the Stars.** They combine the two characteristics the business needs most.
5. **Attempt the Puzzles before delisting them** — their contribution economics are already above average.
6. **Review the Plowhorses for pricing, portion or food-cost improvement.** All three are within ₹6 of the average; small adjustments reclassify them.

I would **not** claim the SQL identifies an exact historical month for each removal. The defensible conclusion is that the Dogs are retrospective delisting candidates; the timing would require a time-series item-level analysis and a business decision threshold this query does not establish.

### 6\. Business impact

The five Dogs generated contribution per unit of ₹189.21, ₹172.17, ₹165.33, ₹160.79 and ₹154.62 — all below the ₹200.02 menu average, with Channa Masala 22.7% below it.

I would **not** assign a rupee saving to delisting them from this query alone. Delisting does not convert existing orders into savings: some customers substitute another item, others abandon the basket entirely. Estimating the split requires substitution data this dataset does not contain.

The defensible impact is therefore: **the analysis identifies five items for delisting review and three items whose margin is within ₹6 of reclassification — not ₹X of guaranteed savings.**

The larger opportunity is menu concentration: protect the six Stars, unlock the three Puzzles, improve the three Plowhorses, challenge the five Dogs.

\---

# 7\. B2 — Did opening more outlets make us more money?

### 1\. Business question

Opening additional outlets increased footprint and total sales. But: **did expansion make the business more profitable, or did we add revenue while taking on outlets that could not cover their own costs?**

### 2\. SQL approach

I compared each outlet's completed-order revenue with the contribution generated by those orders, then deducted the outlet-level operating costs assigned to it.

I looked at both revenue share and net profit share, because revenue alone cannot show whether expansion created or destroyed value.

> \\\*\\\*Scope: outlet net.\\\*\\\* These figures deduct only outlet-assigned expenses. They exclude ₹15.25 L of lifetime company-level cost — central kitchen rent ₹6.15 L, founder drawings ₹8.40 L, compliance ₹0.70 L. Deducting those brings company lifetime net to \\\*\\\*−₹1.24 L\\\*\\\*, the figure D5 tracks. Both measures are correct: outlet net asks whether each kitchen covered its own costs; company net asks whether the business made money.

### 3\. Result

|Outlet|Orders|Lifetime gross|Revenue share|**Outlet net**|Share of outlet net|
|-|:-:|:-:|:-:|:-:|:-:|
|E-Table Kandanchavadi|42,701|₹1.81 Cr|66.9%|**+₹19.23 L**|137.3%|
|E-Table Velachery|16,630|₹71.29 L|26.3%|**−₹0.46 L**|−3.3%|
|E-Table Thoraipakkam|4,198|₹18.30 L|6.8%|**−₹4.77 L**|−34.0%|
|**Sum of outlet net**|**63,529**|**₹2.71 Cr**|**100%**|**+₹14.01 L**|**100%**|
|Less company-level costs||||**−₹15.25 L**||
|**Company lifetime net**||||**−₹1.24 L**||

**Both spoke outlets were net-negative over their operating periods.** Expansion increased revenue and did not increase profit.

### 4\. Interpretation

This is the clearest case in the project where **revenue growth and value creation diverged.**

Kandanchavadi generated 66.9% of revenue and **137.3% of outlet net.** The figure above 100% is not an error: the two newer outlets were collectively loss-making, so the hub had to generate enough to offset them.

The two spokes together lost **₹45,940 + ₹4,76,609 = ₹5,22,549.** They added roughly **₹89.6 L of gross revenue** and a combined lifetime net loss of about **₹5.23 L.**

Thoraipakkam was the larger problem: **₹18.30 L of lifetime gross against a ₹4.77 L loss across 21 months.** It opened in August 2020, into the pandemic, and never reached the volume required to cover its own rent, staffing and utilities. It was loss-making in every one of its 21 months.

This changes how I read the expansion decision. **Opening another outlet was not automatically growth. It was an investment that needed to prove it could reach sufficient demand to absorb its fixed-cost base.**

Two limitations. The outlets opened at different times and ran for different durations, so lifetime revenue or profit cannot rank outlet quality directly. And the result shows the expansion outlets were loss-making over their actual windows — it does not prove what a different location, timing or demand scenario would have produced. Thoraipakkam in particular is confounded with COVID: it never had a normal trading period.

### 5\. Recommended action

I would **not open a second or third outlet based primarily on the success of the first.** Before committing to another fixed-cost location I would require:

1. A realistic demand estimate for the new catchment.
2. A calculated breakeven order volume using expected contribution per order and the new outlet's fixed costs — the D3 method, applied before signing rather than after.
3. A defined ramp-up period with explicit stop-loss criteria.
4. A review point before committing further capital if the outlet remains below its order floor.
5. Evidence the new outlet can become independently profitable, rather than assuming the hub's economics transfer.

For a third outlet in particular, sustained inability to reach viable volume should have triggered reduction or closure rather than continuing to carry the fixed cost.

### 6\. Business impact

The two expansion outlets generated **₹71.29 L + ₹18.30 L = ₹89.59 L** of gross revenue and produced **−₹0.46 L − ₹4.77 L = −₹5.23 L** of lifetime outlet net.

Approximately **₹5.23 L of profit was absorbed by the two spokes.** Kandanchavadi's 137.3% profit share against the spokes' combined −37.3% is the same fact stated as a ratio.

The answer to the business question:

> \\\*\\\*No. Expansion increased the size of the business but not its lifetime profitability. The hub generated the profit; the newer outlets consumed part of it.\\\*\\\*

The lesson is not *"never expand."* It is: **don't confuse additional revenue with additional profit, and don't expand fixed costs until the new unit has a credible path to breakeven.**

\---

# 8\. D5 — Why did the business close?

### 1\. Business question

**Why did the business ultimately close, even though it had been profitable before COVID?**

### 2\. SQL approach

I tracked monthly company net and computed the **cumulative net position** across the full 57 months using a running total — `SUM(...) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)`. The frame clause is what makes it cumulative rather than a repeated grand total.

This shows whether the business built a financial cushion during profitable periods, and how the shock and recovery affected it.

> \\\*\\\*Scope: company net.\\\*\\\* Includes company-level costs. See the scope note above for reconciliation with B2.

### 3\. Result

|Point in time|Cumulative company net|
|:-:|:-:|
|Feb 2020 — peak|**+₹6.55 L**|
|Jun 2021 — crosses zero|**≈ −₹0.1 L**|
|Nov 2022 — closure|**−₹1.24 L**|

The business built roughly **₹6.55 L** of accumulated profit by February 2020. The COVID period progressively consumed it. The cumulative position turned negative in **June 2021** and the business closed at approximately **−₹1.24 L.**

### 4\. Interpretation

The closure was **not because the business had never been profitable.** It generated a meaningful surplus across two pre-COVID years.

The problem was that it entered the pandemic with a model dependent on sufficient volume to cover relatively rigid operating costs. The shock consumed the accumulated cushion, and the recovery never restored earlier profitability — the recovery phase averaged **−₹3,431 per month**, near breakeven but never rebuilding.

From an operator's perspective the failure was **not the absence of a profitable model under normal demand. It was insufficient financial and operating resilience when demand collapsed and stayed below the required level.**

D4 explains why the shock hit so hard: the business had only a ₹193/day weekday surplus and depended on weekends for profit. A prolonged volume shock concentrated in exactly those days was particularly damaging.

This cumulative line is the answer to "why did it close" — and it is evidence rather than narrative.

### 5\. Recommended action

I would not use monthly profit alone as the survival metric. I would maintain a **minimum cash reserve tied to fixed costs** — at ₹1 L/month of company fixed cost, six months of reserve is ₹6 L, roughly the peak cushion this business actually held. That framing makes the reserve a decision rather than an accident.

I would also set a clear stop-loss rule for any prolonged period below the required order floor, and test survivability against a severe volume reduction before expanding.

### 6\. Business impact

The business moved from **+₹6.55 L to −₹1.24 L**, a deterioration of approximately **₹7.79 L** of accumulated financial position.

This is a reconstructed synthetic dataset built on remembered operating economics. It should be presented as an analytical reconstruction, not as the company's accounting record.

\---

# 9\. B5 — When UberEats shut down, where did those orders go?

### 1\. Business question

**When UberEats stopped operating, did we lose that demand, or did those orders move to the other platforms?**

### 2\. SQL approach

I compared platform-level monthly order volumes across the UberEats exit window, using conditional aggregation to place each platform in its own column so the transition is readable in a single result set.

### 3\. Result

Monthly completed orders by platform, Nov 2019 – Apr 2020:

|Month|Swiggy|Zomato|UberEats|Foodpanda|Total|
|:-:|:-:|:-:|:-:|:-:|:-:|
|Nov 2019|523|529|328|0|1,380|
|Dec 2019|655|563|445|0|1,663|
|Jan 2020|758|699|486|0|1,943|
|**Feb 2020**|**1,000**|**968**|**0**|**0**|**1,968**|
|Mar 2020|412|405|0|0|817|
|Apr 2020|93|86|0|0|179|



Foodpanda had already ceased for the business in September 2019.

UberEats represented roughly \~25% of orders in its final months. In February 2020, Swiggy and Zomato both rose in absolute terms while total volume held near the pre-exit level.

### 4\. Interpretation

The concern would have been that losing a platform means losing its customers. **The data does not support that conclusion here.**

UberEats volume was largely absorbed by the two platforms that remained important to the business. Total February 2020 orders were the highest of any month in the dataset despite one platform disappearing entirely. So I would not treat the UberEats shutdown as a major operational failure.

More importantly, **the later fall in orders must not be attributed to UberEats leaving.** The demand shock came in March and April 2020 — a 58% and then 77% month-over-month collapse. Two events fall close together in time and have entirely different causes; conflating them would misattribute a pandemic to a platform exit.

The operator conclusion: **UberEats leaving changed where orders came from. It was not the reason the business subsequently lost demand.**

This is consistent with the market event — UberEats India discontinued operations on 21 January 2020 and directed its restaurants, delivery partners and users to Zomato.

### 5\. Recommended action

If a major platform exits again, track **orders, contribution per order and platform mix weekly for the following 4–8 weeks.** The priority is retaining demand, not replacing the platform one-for-one.

I would also treat platform concentration as a standing risk. By March 2020 the business had two channels instead of four, and no direct channel of its own — which meant no route to the customer that did not depend on an aggregator's commercial decisions.

### 6\. Business impact

The practical impact was **demand migration rather than demand destruction.** The business continued receiving orders through Swiggy and Zomato after the exit, so the correct response was to protect those channels rather than treat the lost UberEats volume as permanent revenue loss.

**Important limitation:** this dataset can show the platform mix and its change over time, but it cannot identify individual UberEats customers and prove that a specific UberEats customer later ordered through Swiggy or Zomato. Customer references are masked and platform-scoped, because aggregators never supplied customer identity to restaurants. **"Orders migrated" is the supported interpretation; customer-level migration is not measurable here.**

\---

# 10\. F2 — At what point does a late delivery start costing us?

### 1\. Business question

**At what delivery time does customer satisfaction drop sharply enough that we should treat it as a service problem?**

### 2\. SQL approach

I grouped completed orders into delivery-time bands and compared average rating and the share of 1–2 star ratings in each. Banding rather than correlating was deliberate: the question is where experience *changes*, not whether each additional minute has a uniform effect.

Unrated orders were excluded from the rating averages. A NULL rating means the customer did not rate — treating it as zero would have destroyed the average.

### 3\. Result

|Delivery time|Orders|Avg. rating|1–2 star share|
|:-:|:-:|:-:|:-:|
|≤ 55 min|56,383|**4.38**|**6.1%**|
|> 55 min|6,173|**3.45**|**26.3%**|

The service-quality break is at roughly **55 minutes.**

### 4\. Interpretation

Up to 55 minutes ratings held around **4.4/5** with 1–2 star ratings at 6.1%. Past that point the average fell to **3.45** and **more than one in four ratings was 1–2 stars** — a **4.3× increase** in severely negative ratings.

It is a cliff, not a gradient. That is the operationally useful shape: there is a threshold to defend rather than a continuous trade-off to optimise.

From an operator's perspective, **55 minutes should have been the warning threshold** rather than waiting for deliveries to become extremely late.

This does not prove delivery time alone caused the lower ratings — order accuracy, food temperature and packaging condition all deteriorate with time and are not separable here. But the pattern is strong enough to justify 55 minutes as an operational trigger.

### 5\. Recommended action

Set **55 minutes as the internal service-alert threshold:**

* **≤ 45 min** — normal
* **45–55 min** — monitor
* **> 55 min** — intervene: prioritise the order, investigate kitchen or rider delay, identify the bottleneck

The objective is to prevent orders from crossing 55 minutes, not to recover satisfaction after a delivery is already late.

This connects to F3: prep time degrades above 70–80% kitchen utilisation, which is the mechanism pushing orders past the threshold on peak days. And to D4: those peak days are weekends, where a lost or damaged order carries 23.6× the economic weight of a weekday one.

### 6\. Business impact

**4.38 − 3.45 = 0.93 rating points**, roughly a **21% drop** relative to the sub-55-minute level. The 1–2 star share rises from **6.1% to 26.3%** — a **4.3× increase** in severely negative ratings.

The dataset does not support converting rating deterioration into a reliable rupee revenue impact — that would require platform ranking and conversion data the restaurant never received. So I would not invent one.

**The defensible impact is the 0.93-point service-quality deterioration and the 4.3× increase in severely negative ratings past 55 minutes.**

\---

# 11\. F3 — Did we need a bigger kitchen?

### 1\. Business question

**At what level of demand did the kitchen start struggling, and did that mean we needed a bigger kitchen?**

### 2\. SQL approach

I joined daily order counts to the recorded kitchen capacity in `daily\\\_operations`, computed utilisation, and compared average preparation time across utilisation bands. The objective was to locate the operational threshold before deciding whether physical capacity was the answer.

### 3\. Result

|Kitchen utilisation|Avg. preparation time|
|:-:|:-:|
|1-10%|14.91 min|
|50–70%|\~20 min|
|70–80%|\~21 min|
|80–100%|\~23 min|
|100–120%|\~26 min|
|\~132%|**29.2 min**|



Preparation time held stable to roughly **70–80% utilisation**, then degraded, starts from avg prep time =\~15min at 10min to reaching **29.2 minutes at 132%**.

### 4\. Interpretation

The data shows a **capacity constraint**, but the first response should not automatically have been a bigger kitchen.

The important thing is the shape of the relationship. Below roughly 70–80% utilisation, prep time is flat — additional volume is absorbed at no service cost. Beyond it, prep time rises, and since prep time feeds total delivery time, this provides a plausible operational pathway by which high utilisation could contribute to orders crossing the 55-minute threshold identified in F2.

So my interpretation: **we did not necessarily need a bigger kitchen as the first solution; we needed to manage the demand/capacity balance.** If high utilisation had been persistent, additional capacity would have been justified. Occurring mainly at peaks, it is addressable through scheduling, batch planning and order throttling.

This also reframes F1. Raising batch sizes on high-volume items reduces stockouts, but on days already above 80% utilisation it consumes the same constrained kitchen time. The two recommendations interact, and the sequencing matters: fix batch sizing on normal days first, and treat peak days as a scheduling problem rather than a batching one.

### 5\. Recommended action

Before expanding the physical kitchen:

1. Keep normal operating utilisation around **70–80%.**
2. Track preparation time whenever utilisation approaches the threshold.
3. For sustained periods above capacity, first test **staffing and batch scheduling, and peak-hour order controls.**
4. Because peak utilisation coincides with weekends — where an order carries 23.6× the weekday economic weight — prioritise weekend throughput over weekday capacity.
5. Consider a larger kitchen only if demand consistently exceeds existing capacity after those measures.

### 6\. Business impact

At **132% utilisation**, preparation time reached **29.2 minutes** against roughly 20–21 minutes at normal utilisation. Using 20.5 as the midpoint:

**29.2 − 20.5 = 8.7 additional minutes**, approximately a **42% increase** in preparation time.

Those 8.7 minutes matter because they push total delivery time toward the 55-minute threshold from F2, where the 1–2 star rate rises 4.3×. The capacity constraint therefore has a service cost even where it has no direct rupee cost.

The dataset does not establish that a larger kitchen would have produced a specific rupee return, so **I would not claim a financial ROI for kitchen expansion** from this analysis.

\---

# 12\. E3 — What does our average order value actually hide?

> \\\*\\\*Draft.\\\*\\\* The numbers are verified; rewrite the interpretation in your own words before publishing, because you will have to say it out loud.

### 1\. Business question

We tracked average order value as a headline metric and used it to judge whether baskets were improving. **But does a single AOV describe what customers were actually ordering, or is it averaging across genuinely different order types?**

### 2\. SQL approach

I banded completed orders by gross order value and compared each band's share of orders against its share of revenue, then added average line items per order to test whether the bands correspond to different order compositions rather than arbitrary price cuts.

Comparing order share against revenue share is the point: if they diverge, the average is concealing structure.

### 3\. Result

|Value band|Orders|% of orders|% of revenue|Avg. items/order|
|:-:|:-:|:-:|:-:|:-:|
|Under ₹250|1,701|2.7%|1.4%|1.19|
|₹250–349|29,030|**45.7%**|33.0%|1.33|
|₹350–449|12,345|19.4%|17.4%|1.86|
|₹450–599|7,204|11.3%|14.8%|2.17|
|₹600–799|12,008|**18.9%**|**29.2%**|2.41|
|₹800+|1,241|2.0%|4.2%|3.03|

**Mean AOV ₹427. Median ₹353. Only 4.7% of orders fall between ₹390 and ₹430.**

### 4\. Interpretation

**The average order value describes almost no actual order.** The mean sits at ₹427; the median is ₹353; fewer than one order in twenty falls anywhere near the mean.

The distribution is bimodal, and the item counts explain why. The ₹250–349 band averages 1.33 items — that is a single main dish, sometimes with a beverage. The ₹600–799 band averages 2.41 items — two mains. These are not variations on a typical order. **They appear to represent materially different basket types — roughly single-main orders versus larger multi-item baskets.**

That reframes the metric. A rise in AOV could mean baskets are genuinely growing, or simply that the mix shifted toward multi-person orders while neither group changed behaviour. Tracking the mean cannot distinguish those, and they call for opposite responses.

The revenue concentration makes the stakes concrete. The ₹600–799 band is **18.9% of orders and 29.2% of revenue.** The ₹250–349 band is **45.7% of orders and 33.0% of revenue.** Nearly half of all orders produce a third of revenue.

The single-main band is therefore the largest addressable opportunity in the business — not because those customers are unprofitable, but because the gap between the two modes is roughly ₹350 of gross, and the mechanism for closing it is already visible in the data: a second main dish.

### 5\. Recommended action

1. **Stop using mean AOV as the headline basket metric.** Report the median alongside it, and report band mix separately. A mean between two modes is not a description of anything.
2. **Target the ₹250–349 band specifically** — 45.7% of orders sitting one main dish below the high-revenue mode.
3. **Set minimum-order-value thresholds just above the single-main band.** A "free beverage above ₹399" or "₹100 off above ₹449" offer prompts exactly the movement the distribution suggests is available, and the restaurant-funded cost of doing so is small against ₹350 of incremental gross.
4. **Bundle two-main combos explicitly** rather than relying on customers to add a second item themselves.
5. Cross-reference with C2: the Puzzles — high-margin, low-volume items — are natural candidates for the second slot in a bundle. That addresses two findings with one intervention.

### 6\. Business impact

Moving 10% of the ₹250–349 band (2,903 orders) into the ₹600–799 band represents roughly:

**2,903 × (₹659.60 − ₹307.80) = ₹10.2 L of incremental gross** across the analysed period

At the observed contribution rate of roughly 35% of gross, that is approximately **₹3.6 L of incremental contribution**, before any restaurant-funded discount cost required to prompt the shift.

**This is an illustrative sizing, not a forecast.** It assumes the shift is achievable and does not model the discount depth needed to trigger it, or whether those customers would have ordered a second main regardless. The defensible finding is the structural one: **45.7% of orders sit in a band producing 33.0% of revenue, one main dish below the mode that produces 29.2% of revenue from 18.9% of orders.**

\---

# Overall project finding

**The business earned its profit on weekends.** Weekdays averaged 24 orders and cleared their daily fixed costs by ₹193; weekends averaged 54 and cleared them by ₹4,563. **28.5% of the calendar produced 90.4% of the profit.**

That structure explains everything that followed. Breakeven sat at **17.5 orders/day against outlet costs and 22.6 against full overhead** — my remembered figure of \~20/day falls between the two. Weekday trading was always marginal, and the model depended on two days in seven. When COVID removed the weekend surge, revenue fell to **9.6%** of the February 2020 baseline while fixed costs held at **101.1%**. Accumulated profit peaked at **₹6.55 L**, crossed zero in June 2021, and closed at **−₹1.24 L**.

Three further findings sharpen it.

**Expansion added revenue but reduced lifetime outlet profitability. All of these patterns became visible once I reconstructed the operating economics and asked the right questions.** Kandanchavadi produced 137.3% of outlet net because both spokes were net-negative; Thoraipakkam lost money in all 21 of its months.

**Limited-batch production cost more than it saved** — roughly ₹640/day in foregone contribution against ₹2/day of waste avoided, about ₹19,500/month. I was optimising a visible cost against an invisible one.

**And the metrics themselves were misleading.** Contribution said weekdays carried the business; profit said they did not. Mean AOV described almost no real order. The customer-visible discount overstated our promotional cost 4.38×, and had I booked it as my own, the P\&L would have shown a loss in every month of the business's life.

None of this was visible while the business was running. All of it was visible in the data within a week of asking the right questions.

\---

# Analytical discipline notes

Six places where the obvious reading was wrong. Recorded because the reasoning matters more than the result.

**Contribution is not profit (D4).** Weekdays produced 52.7% of contribution and 9.6% of profit. The metric choice inverted the conclusion.

**Scope determines the answer (D3, B2).** Breakeven moves from 17.5 to 22.6 orders/day, and lifetime net from +₹14.01 L to −₹1.24 L, depending on whether company overhead is loaded onto the outlet. Neither figure is wrong; the question has to specify which costs the unit is asked to carry.

**Two changes, one effect (C3).** Desserts were delisted in the same month procurement changed. The waste drop cannot be assigned to either from this data.

**A trend that tracks volume is not a trend (E2).** Cohort retention appeared to improve 2.5× across 2019. It correlates with order volume at r = 0.946 and no intervention occurred. Reported as a level.

**Who funded it is not whether it worked (B4).** The analysis establishes that platforms funded 77.2% of discount depth. It does not establish that those promotions generated incremental profitable demand — that requires a holdout group this dataset does not contain.

**A mean between two modes describes nothing (E3).** AOV ₹427, median ₹353, and 4.7% of orders near the mean.

