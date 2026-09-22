"""
E-Table Foods — synthetic dataset generator: configuration.

Every constant here traces to a Phase 1 locked anchor. Nothing is invented at
generation time. Provenance tags:
  LIVED     - operator recalled it directly
  DERIVED   - computed from LIVED figures
  MODELLED  - chosen by construction to hit a LIVED anchor
"""

from datetime import date

SEED = 20180201

# ---------------------------------------------------------------- timeline
START = date(2018, 2, 1)          # LIVED
END = date(2022, 11, 30)          # LIVED

# ---------------------------------------------------------------- outlets
# rent/utilities LIVED for outlets 1-2; outlet 3 rent MODELLED
OUTLETS = [
    dict(outlet_id=1, outlet_name="E-Table Kandanchavadi", outlet_type="hub",
         locality="Kandanchavadi", opening_date=date(2018, 2, 1), closing_date=date(2022, 11, 30),
         monthly_rent=10000, monthly_utilities=5000, status="closed",
         staff_cost=40000, gas_consumables=4000, procurement=6000, repairs=1000,
         mature_weekday=23, mature_saturday=42, mature_sunday=61,   # LIVED
         ramp_months=12, ramp_start_frac=0.42),
    dict(outlet_id=2, outlet_name="E-Table Outlet 2", outlet_type="spoke",
         locality="Perungudi", opening_date=date(2019, 7, 1), closing_date=date(2022, 11, 30),
         monthly_rent=15000, monthly_utilities=5000, status="closed",
         staff_cost=30000, gas_consumables=3000, procurement=4000, repairs=800,
         mature_weekday=14, mature_saturday=24, mature_sunday=34,
         ramp_months=7, ramp_start_frac=0.44),
    dict(outlet_id=3, outlet_name="E-Table Outlet 3", outlet_type="spoke",
         locality="Thoraipakkam", opening_date=date(2020, 8, 1), closing_date=date(2022, 4, 30),
         monthly_rent=12000, monthly_utilities=5000, status="restructured",
         staff_cost=25000, gas_consumables=3000, procurement=4000, repairs=800,
         mature_weekday=10, mature_saturday=16, mature_sunday=21,  # never ramps: override C2
         ramp_months=18, ramp_start_frac=0.45),
]

CENTRAL_KITCHEN_RENT = 15000      # LIVED, from expansion onward
CENTRAL_KITCHEN_FROM = date(2019, 7, 1)
COMPLIANCE_MONTHLY = 1200         # MODELLED
FOUNDER_DRAWINGS = 20000          # LIVED
FOUNDER_DRAWINGS_FROM = date(2019, 6, 1)

# ---------------------------------------------------------------- platforms
# Restaurant pays commission only. Delivery fee is charged to the CUSTOMER and
# never touches the restaurant P&L. Hard shutdown dates are LIVED.
PLATFORMS = [
    dict(platform_id=1, platform_name="Swiggy", commission_rate=0.28,
         customer_delivery_rate=0.130, other_deduction_rate=0.0070,
         active_from=date(2018, 2, 1), active_to=None, base_share=0.34),
    dict(platform_id=2, platform_name="Zomato", commission_rate=0.28,
         customer_delivery_rate=0.135, other_deduction_rate=0.0070,
         active_from=date(2018, 2, 1), active_to=None, base_share=0.32),
    dict(platform_id=3, platform_name="UberEats", commission_rate=0.28,
         customer_delivery_rate=0.120, other_deduction_rate=0.0065,
         active_from=date(2018, 2, 1), active_to=date(2020, 1, 31), base_share=0.22),
    dict(platform_id=4, platform_name="Foodpanda", commission_rate=0.28,
         customer_delivery_rate=0.125, other_deduction_rate=0.0060,
         active_from=date(2018, 2, 1), active_to=date(2019, 9, 30), base_share=0.12),
]

AGGREGATOR_PREMIUM = 1.15         # LIVED: portfolio average premium over takeaway base
# premium varies by category and platform (spec: "allow it to vary naturally")
CATEGORY_PREMIUM = {"Biryani": 1.18, "Starter": 1.16, "Curry": 1.16, "Meals": 1.15,
                    "Dessert": 1.14, "Beverage": 1.13, "Add-on": 1.14}
PLATFORM_PREMIUM_ADJ = {1: 1.000, 2: 1.010, 3: 0.992, 4: 0.988}

# ---------------------------------------------------------------- menu
# base_price is the 2019 takeaway-equivalent. food_cost_pct is against base
# price and averages ~35% across the portfolio (LIVED).
MENU = [
    # id, name, category, veg, base_price_2019, food_cost_pct, launch, delist, weight
    (1, "Chicken Biryani - Boneless", "Biryani", "Non-veg", 309, 0.3408, date(2018, 2, 1), None, 0.132),
    (2, "Chicken Biryani - Fry Piece", "Biryani", "Non-veg", 278, 0.3571, date(2018, 2, 1), None, 0.150),
    (3, "Chicken Biryani - Dum", "Biryani", "Non-veg", 294, 0.3475, date(2018, 2, 1), None, 0.098),
    (4, "Tamil Nadu Style Chicken Biryani", "Biryani", "Non-veg", 268, 0.3533, date(2018, 4, 1), None, 0.072),
    (5, "Chilli Chicken", "Starter", "Non-veg", 237, 0.3168, date(2018, 2, 1), None, 0.104),
    (6, "Chicken Lollipop", "Starter", "Non-veg", 247, 0.3302, date(2018, 2, 1), None, 0.058),
    (7, "Dragon Chicken", "Starter", "Non-veg", 252, 0.3245, date(2018, 5, 1), None, 0.041),
    (8, "Chicken Curry", "Curry", "Non-veg", 247, 0.3341, date(2018, 2, 1), None, 0.106),
    (9, "Dum Chicken Curry", "Curry", "Non-veg", 258, 0.3379, date(2018, 2, 1), None, 0.043),
    (10, "Fry Piece Chicken Curry", "Curry", "Non-veg", 252, 0.3418, date(2018, 2, 1), None, 0.038),
    (11, "Boneless Chicken Curry", "Curry", "Non-veg", 263, 0.3360, date(2018, 2, 1), None, 0.035),
    (12, "Butter Chicken Masala", "Curry", "Non-veg", 283, 0.3763, date(2018, 9, 1), None, 0.014),
    (13, "Veg Thali Meals", "Meals", "Veg", 227, 0.3053, date(2019, 4, 1), None, 0.032),
    (14, "Paneer Fry", "Starter", "Veg", 206, 0.3456, date(2019, 4, 1), None, 0.024),
    (15, "Paneer Masala", "Curry", "Veg", 216, 0.3494, date(2019, 4, 1), None, 0.018),
    (16, "Gobi Manchurian", "Starter", "Veg", 180, 0.2573, date(2019, 6, 1), None, 0.020),
    (17, "Channa Masala", "Curry", "Veg", 170, 0.2458, date(2019, 6, 1), None, 0.015),
    # desserts: trialled and discontinued for wastage (LIVED)
    (18, "Gulab Jamun (2 pc)", "Dessert", "Veg", 90, 0.3264, date(2018, 3, 1), date(2018, 8, 31), 0.000),
    (19, "Rasmalai (2 pc)", "Dessert", "Veg", 110, 0.3571, date(2018, 3, 1), date(2018, 8, 31), 0.000),
    # beverages: ~3 SKUs stocked at a time; Soda and Coke strongest (LIVED)
    (20, "Coke (600ml)", "Beverage", "Veg", 40, 0.5200, date(2018, 2, 1), None, 0.000),
    (21, "Soda (600ml)", "Beverage", "Veg", 25, 0.4000, date(2018, 2, 1), None, 0.000),
    (22, "Sprite (600ml)", "Beverage", "Veg", 40, 0.5200, date(2018, 2, 1), None, 0.000),
    (23, "Pepsi (600ml)", "Beverage", "Veg", 40, 0.5200, date(2018, 2, 1), None, 0.000),
    (24, "7UP (600ml)", "Beverage", "Veg", 40, 0.5200, date(2018, 2, 1), None, 0.000),
    (25, "Fanta (600ml)", "Beverage", "Veg", 40, 0.5200, date(2018, 2, 1), None, 0.000),
    # add-ons
    (26, "Extra Rice", "Add-on", "Veg", 45, 0.2880, date(2018, 2, 1), None, 0.000),
    (27, "Raita", "Add-on", "Veg", 35, 0.3072, date(2018, 2, 1), None, 0.000),
    (28, "Extra Gravy", "Add-on", "Veg", 45, 0.3264, date(2018, 2, 1), None, 0.000),
]

MAIN_IDS = list(range(1, 18))
DESSERT_IDS = [18, 19]
BEVERAGE_IDS = [20, 21, 22, 23, 24, 25]
ADDON_IDS = [26, 27, 28]

# Beverage rotation: Soda and Coke always stocked, third slot rotates (LIVED)
BEVERAGE_ALWAYS = [21, 20]
BEVERAGE_ROTATING = [22, 23, 24, 25]
BEVERAGE_PICK_WEIGHTS = {21: 0.40, 20: 0.36, 22: 0.06, 23: 0.06, 24: 0.06, 25: 0.06}

# Price epochs: multiplier on 2019 base. Drives AOV 356 -> 462 (DERIVED).
PRICE_EPOCHS = [
    (date(2018, 2, 1), date(2018, 12, 31), 0.938),
    (date(2019, 1, 1), date(2019, 12, 31), 0.958),
    (date(2020, 1, 1), date(2020, 12, 31), 0.986),
    (date(2021, 1, 1), date(2021, 12, 31), 1.017),
    (date(2022, 1, 1), date(2022, 11, 30), 1.055),
]

# ---------------------------------------------------------------- basket
# Tuned so AOV lands on the LIVED ~400 anchor at 1.65 items/order (LIVED).
BASKET_MIX = [
    ("1 main",                0.400, 1, 0.00, 0.00),
    ("1 main + beverage",     0.220, 1, 1.00, 0.00),
    ("1 main + add-on",       0.060, 1, 0.00, 1.00),
    ("2 mains",               0.220, 2, 0.00, 0.00),
    ("2 mains + beverage",    0.080, 2, 1.00, 0.00),
    ("3 mains",               0.020, 3, 0.00, 0.00),
]

COMBO_RATE = 0.09
COMBO_DISCOUNT = 0.10             # LIVED ~10% vs sum of components

# ---------------------------------------------------------------- costs
PACKAGING_PER_ORDER = 15.0        # LIVED
PACKAGING_EXTRA_MONTHLY = 1000    # MODELLED: bags/cutlery, booked as opex not per-order

# advertising as % of gross, by demand condition (LIVED range 2-5%)
AD_RATE_NORMAL = 0.022
AD_RATE_PROMO = 0.035
AD_RATE_RECOVERY = 0.030

# food cost drift against base price, by year (LIVED trajectory)
FOOD_COST_YEAR_DRIFT = {2018: 1.06, 2019: 1.00, 2020: 1.02, 2021: 1.055, 2022: 1.085}
# first 6 months ran materially worse before optimisation (LIVED)
EARLY_INEFFICIENCY_END = date(2018, 7, 31)
EARLY_FOOD_COST_UPLIFT = 1.10
EARLY_PROCUREMENT = 13500         # LIVED ~12-15k before optimisation
EARLY_WASTAGE_MULTIPLIER = 3.4
WASTAGE_SCALE = 0.54             # calibrates post-optimisation to 5-6 kg/week

# ---------------------------------------------------------------- discounts
DISCOUNT_INCIDENCE = 0.60         # DERIVED: 18% restaurant-funded = 30% of discounted
RESTAURANT_FUNDED_SHARE = 0.30    # LIVED F.6
RESTAURANT_DISCOUNT_DEPTH = 0.12  # LIVED F.1
PLATFORM_DISCOUNT_DEPTH = 0.18    # MODELLED: platform campaigns run deeper

# ---------------------------------------------------------------- behaviour
REPEAT_RATE = 0.33                # LIVED-ish
CANCEL_RATE = 0.027               # MODELLED
REFUND_RATE = 0.015               # MODELLED
LATE_THRESHOLD_MIN = 55           # CORRECTED C8: platform SLA, not the 45-min promise
PREP_MEAN = 20                    # LIVED
DELIVERY_TOTAL_MEAN = 42          # LIVED
NO_RATING_RATE = 0.32             # MODELLED
RATING_DIST = {5: 0.62, 4: 0.23, 3: 0.09, 2: 0.04, 1: 0.02}
STOCKOUT_RATE = 0.025             # LIVED 2-3%

CANCEL_REASONS = ["customer cancelled", "restaurant delay", "rider unavailable",
                  "item unavailable", "platform technical issue"]

# Deliberately inconsistent spellings: the cleaning exercise (LIVED requirement)
DELIVERY_AREAS = [
    "Kandanchavadi", "Kandanchavadi ", "kandanchavadi", "Kandanchawadi",
    "Perungudi", "perungudi", "Perungudi.", "Perumgudi",
    "Thoraipakkam", "thoraipakkam", "Thoraipakam", "Thoraipakkam OMR",
    "Sholinganallur", "sholinganallur", "Sholinganalur",
    "Karapakkam", "karapakkam", "Navalur", "navalur", "Siruseri",
    "Perungalathur", "Madhavaram", "Velachery", "velachery", "Velacherry",
    "Thiruvanmiyur", "thiruvanmiyur", "Adyar", "Taramani", "taramani",
]

# ---------------------------------------------------------------- COVID
# volume multipliers vs pre-COVID trend (LIVED shape, MODELLED monthly detail)
COVID_MULTIPLIER = {
    (2020, 3): 0.55, (2020, 4): 0.12, (2020, 5): 0.18, (2020, 6): 0.35,
    (2020, 7): 0.52, (2020, 8): 0.63, (2020, 9): 0.72, (2020, 10): 0.80,
    (2020, 11): 0.84, (2020, 12): 0.86,
    (2021, 1): 0.88, (2021, 2): 0.89, (2021, 3): 0.87,
    (2021, 4): 0.55, (2021, 5): 0.40, (2021, 6): 0.50,
    (2021, 7): 0.74, (2021, 8): 0.82, (2021, 9): 0.86, (2021, 10): 0.89,
    (2021, 11): 0.91, (2021, 12): 0.90,
    (2022, 1): 0.88, (2022, 2): 0.89, (2022, 3): 0.88, (2022, 4): 0.86,
    (2022, 5): 0.84, (2022, 6): 0.82, (2022, 7): 0.79, (2022, 8): 0.76,
    (2022, 9): 0.73, (2022, 10): 0.70, (2022, 11): 0.66,
}

COVID_PHASE = [
    (date(2018, 2, 1), date(2020, 2, 29), "pre"),
    (date(2020, 3, 1), date(2020, 5, 31), "wave1"),
    (date(2020, 6, 1), date(2020, 9, 30), "reopening"),
    (date(2020, 10, 1), date(2021, 3, 31), "plateau"),
    (date(2021, 4, 1), date(2021, 6, 30), "wave2"),
    (date(2021, 7, 1), date(2022, 6, 30), "recovery"),
    (date(2022, 7, 1), date(2022, 11, 30), "decline"),
]

# Jan/Feb 2020 exceptional period (LIVED)
PEAK_MONTHS = {(2019, 12): 1.11, (2020, 1): 1.35, (2020, 2): 1.37}

# festival / seasonal uplift, month -> multiplier (MODELLED)
SEASONAL = {1: 1.03, 2: 1.01, 3: 0.99, 4: 1.02, 5: 0.97, 6: 0.98,
            7: 1.00, 8: 1.02, 9: 1.03, 10: 1.06, 11: 1.05, 12: 1.04}

OUTPUT_DIR = r"C:\Users\manoj\Downloads\Documents\E-Table_Analytics_Project\cloud-kitchen-unit-eceonomics-sql\data"

REFUND_RESTAURANT_SHARE = 0.60   # MODELLED: platform absorbs part of refund cost

# Staffing lifecycle multipliers (spec 17: allow variation by phase)
STAFF_PHASE_MULT = {"opening": 1.10, "pre": 1.00, "wave1": 0.55, "reopening": 0.78,
                    "plateau": 0.92, "wave2": 0.72, "recovery": 0.95, "decline": 0.88}
