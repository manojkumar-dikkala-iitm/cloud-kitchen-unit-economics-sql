# Business Context

## The business

E-Table Foods was a cloud kitchen in Chennai. I co-founded it and ran operations and sales from February 2018 until it ceased operations in November 2022.

Delivery only. No dine-in, no counter, no walk-in trade. Everything came through the food aggregators. We started with one kitchen in Kandanchavadi and grew to three locations.

The menu was biryani-led. Chicken biryani in a few variations was the core of the business, with curries, starters and a small beverage range around it. We were heavily non-vegetarian at the start. A vegetarian range came later, after we kept getting asked for it.

## How the business actually worked

An order came in on a platform tablet. The kitchen cooked it, packed it, and a platform rider collected it. We never saw the customer and never spoke to one.

That last point matters more than it sounds. On aggregators you do not own the customer relationship. The platform does. We could not see who our repeat customers were, could not contact them, and could not tell whether a Swiggy customer and a Zomato customer were the same person. We competed on food, price and speed, because loyalty was not a lever available to us.

As we grew we ran hub-and-spoke. The main kitchen handled most of the core production and the other two locations did final assembly and dispatch. The logic was that a spoke needs less space and fewer cooks than a hub, so it should carry lower fixed costs.

## Platforms

We were on four: Swiggy, Zomato, UberEats and Foodpanda.

Two of them disappeared during our operating period, which is not something we controlled or expected. Foodpanda stopped being relevant to us in 2019. UberEats India shut down in January 2020 and moved its restaurants over to Zomato. By early 2020 we had two channels instead of four, and no channel of our own.

## Where the money went

This is the part I got wrong in my own head for a long time, so I want to be precise about it.

The customer pays two things: the food value and a delivery fee. **The delivery fee goes to the platform. It was never our revenue and it was never our cost.** For a while I had been mentally treating it as a cost we bore, which made the business look far worse than it was.

What we actually paid out of the food value:

| | |
|---|---|
| Platform commission | 28% of gross |
| Payment and other platform deductions | around 0.7% |
| Food cost | around 35% of our base price |
| Packaging | ₹15 per order |
| Restaurant-funded discounts | when we ran our own offers |

We listed prices on the aggregators roughly 15% above what a takeaway price would have been, to absorb the commission. Everybody did this.

There were also discounts we did not pay for. The platforms ran their own campaigns, and the customer saw a discount that came out of the platform's budget, not ours. That distinction turned out to matter a lot, and I did not track it properly at the time.

Fixed costs per outlet were staff, rent, utilities, gas and consumables, procurement and travel, repairs, and platform advertising at 2–3% of sales. On top of that the company carried the central kitchen rent, compliance costs, and what I drew as salary.

## Batch cooking

We cooked in limited batches against a rough forecast rather than preparing to cover any possible demand. Popular items sometimes sold out before the end of service.

That was a deliberate choice. Throwing food away felt expensive and visible, and running out felt like a smaller problem. I now think that was the wrong call, and F1 in the insights summary works out what it cost.

## Who cared about what

Between the two of us as founders, we watched unit economics, whether to open another location, and cash.

The kitchen team cared about prep load and how many portions to cook. Aggregator account managers cared about our order volume, whether we were joining their promotions, and our ratings. Customers cared about price, delivery time and whether the item they wanted was actually available.

## What we tracked, and what we did not

We looked at daily order counts, average order value, monthly sales, food cost percentage, and whatever the platform dashboards showed us on ratings, cancellations and delays.

We did not track contribution margin per order. We did not know what a weekday earned versus a weekend. We had no item-level margin. We had never calculated how many orders a day an outlet needed just to cover its costs.

Those four are exactly what this project reconstructs, and it is the reason a fairly large fact about the business went unnoticed for four years.

## The questions I actually had at the time

1. Which items should come off the menu?
2. Should we open another outlet?
3. Are the discounts making money or losing money?
4. How many orders a day does an outlet need to survive?
5. Is it cheaper to run out of food or to throw it away?
6. Do we need a bigger kitchen?

I answered all six on instinct and whatever the platform dashboards told me. This project answers them with data.

## What the analysis cannot tell me

Worth being upfront about the limits.

The platforms gave us no customer identity, so repeat behaviour can only be measured inside a single platform. Cross-platform identity is not just missing from the data, it is impossible.

We had no competitor data, no market share, and no visibility into how the platform ranked us against other restaurants nearby.

And there was no control group for any promotion we ran. So I can work out who funded a discount, but not whether that discount brought in orders that would not otherwise have happened.

## A note on the data

The original production database, the platform dashboards and the reports are all gone. What I still had were the operating figures I remembered from running the place: order volumes, average order value, commission, food cost, rent, staffing, what happened during COVID, and roughly what order volume an outlet needed to stay open.

So I rebuilt it. The transactional data in this project is synthetic, generated to reconcile against those remembered figures, and validated by a harness that checks the generated business falls inside the ranges I actually operated in. The full disclosure is in `docs/04_assumptions_log.md`.

The numbers I remembered turned out to contradict each other in eleven places. Sorting that out took longer than writing the queries.
