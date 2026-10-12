# San Mateo boba franchise fails the math

**Pass on the downtown San Mateo "absentee franchise boba shop" at ~$350K unless the seller proves, with tax returns and POS data, sales close to $1 million a year. Nothing found so far suggests that.** The listing appears on BizQuest as BW2447990 (and on BizBuySell). It confirms a 990 sq ft retail floor over a 990 sq ft basement, a 6-ft Type 1 hood and **rent of $7,400 a month including NNN** ([BizQuest](https://www.bizquest.com/business-for-sale/absentee-run-franchise-boba-tea-shop-for-sale-in-downtown-san-mateo/BW2447990)). No search snippet confirmed the ~$350K price or the ~$180K cash flow you saw. One summary showed $250K and another showed $370K. The brand is not named anywhere. The same footprint (990 sq ft plus an equal basement, branded franchise, absentee-run) matches a downtown San Mateo franchise that SellingRestaurants marks **sold at $125K on about $300K of yearly sales** ([SellingRestaurants](https://sellingrestaurants.com/restaurant-for-sale/branded-boba-tea-franchise-for-sale-in-downtown-san-mateo)). At $300K of sales, rent alone is **29.6% of revenue**, and $180K of cash flow would be **60% of revenue**, which a boba shop cannot produce. My reconstructed P&L, with a paid manager, needs roughly **$0.9M–$1.6M of sales** to reach $180K. A 990 sq ft shop in a block with 8–10 competing tea shops is very unlikely to do that. The Cupertino and San Jose comps fail the same test in different ways. For a Dublin buyer who wants very low risk, an absentee setup and a low real multiple, none of the three is the right asset. **Standing caveat: every listing figure here comes from search-result snippets, because the listing pages were blocked. Verify each number with the broker before you rely on it.**

## The listing: what is confirmed and what is not

The match to your listing rests on title wording and BizBuySell syndication. The "BW" prefix on the BizQuest ID points to BizBuySell as the source, and the same "downtown San Matero" typo appears on BizBuySell's San Mateo County pages ([BizBuySell San Mateo County p.2](https://www.bizbuysell.com/california/san-mateo-county-businesses-for-sale/2/)). The price and cash flow rest on your own reading of the page on 2026-10-11.

| Item | Status | Detail |
|---|---|---|
| Title / ID | **Confirmed (snippet)** | "Absentee run Franchise boba tea shop for sale in Downtown San Mateo", BizQuest BW2447990 |
| Space | **Confirmed** | ~1,980 sq ft total: 990 sq ft retail + 990 sq ft basement |
| Kitchen | **Confirmed** | Commercial kitchen with a 6-ft Type 1 hood |
| Rent | **Confirmed** | $7,400/mo including NNN, which is **$88,800/yr** |
| Operating model | **Confirmed** | "Absentee-owner model" |
| Asking price ~$350K | **Unconfirmed** | Seen by you only. Snippets show $250K and a $370K figure that may belong to another listing |
| Cash flow ~$180K | **Unconfirmed** | Not in any snippet. Unknown whether it is SDE (owner labor included) or net of a manager |
| Sales, lease term, staff, franchise term, transfer fee, seller financing, broker | **Unknown** | Shown only on the blocked listing page |
| Brand | **Unknown** | Not named in any snippet |
| Earlier sale of same shop | **Possible, unconfirmed** | SellingRestaurants: "Branded Boba Tea franchise", downtown San Mateo, **SOLD at $125K**, ~**$300K yearly sales**, absentee, 990 sq ft + same-size basement, 2 years left on lease, total rent **$6,158/mo**. A search summary named Tommy Tran (Grand Realty Group) as broker, which could not be verified ([SellingRestaurants](https://sellingrestaurants.com/restaurant-for-sale/branded-boba-tea-franchise-for-sale-in-downtown-san-mateo)) |

Suppose the earlier listing is the same shop. Then it sold for $125K on ~$300K of sales and is now offered at about 2.8x that price with a claimed $180K of cash flow. For that to be true, sales must have roughly tripled, or the cash-flow figure is something other than what an absentee owner would actually take home. The rent change fits a new or renewed lease: the old listing showed $6,158 with two years left, and today's figure is $7,400. That also means the buyer may inherit a recently reset, higher rent. Other downtown boba listings set the local price range. One bubble-tea shop asks **$218K** with $7,160/mo rent. A "branded boba tea and snacks shop" expired unsold at **$168K** with $5,430/mo rent ([BizBuySell San Mateo County food](https://www.bizbuysell.com/california/san-mateo-county/restaurants-and-food-businesses-for-sale/); [SellingRestaurants](https://sellingrestaurants.com/restaurant-for-sale/branded-boba-tea-and-snacks-shop-for-sale-in-downtown-san-mateo)). At least four downtown boba shops have been listed for sale at the same time. That is a turnover signal, not a sign of a healthy cluster.

## Rebuilding the P&L shows $180K needs about $1M in sales

Industry benchmarks put boba COGS at **25–35%** and labor at **25–35%**, with a "typical" net margin near 15% ([DojoBusiness](https://dojobusiness.com/blogs/news/tool-revenue-boba-tea); [Toast](https://pos.toasttab.com/blog/on-the-line/how-much-do-boba-shops-make)). Those labor figures assume the owner works in the shop. An absentee owner pays for every hour. The model in `research_notes/San Mateo boba franchise/boba_pnl.py` therefore uses these inputs:

- Crew wage of either the City of San Mateo's **$18.60/hr** 2026 minimum ([City of San Mateo](https://cityofsanmateo.org/3278)) or the **$20/hr AB 1228 fast-food wage**. The $20 rate applies to franchised limited-service brands with more than 60 US establishments, and DIR says the type of drink, boba included, does not matter ([DIR FAQ](https://www.dir.ca.gov/dlse/Fast-Food-Minimum-Wage-FAQ.htm); [CA DFPI](https://dfpi.ca.gov/legislative-changes-in-2024-for-franchisors/)).
- A 15% payroll burden.
- A full-time store lead at $25/hr ($52K, or $59.8K with burden).
- Staffing of 98 labor-hours a week at $300K of sales, rising by 30 hours for each additional $150K.
- The listing's $88.8K rent.
- Royalty plus marketing of **6% / 7.5% / 9%**.
- Delivery-app commission of 25% on 10–25% of sales, in line with DoorDash's 15/25/30% tiers ([DoorDash](https://merchants.doordash.com/en-us/products/pricing)), plus 3% card fees.
- Other costs of $24K plus 1.5% of sales.

These are my assumptions, not seller data. The output is reproduced verbatim:

```
==============================================================================
1. Detailed base-case P&L (COGS 30%, royalty+mkt 7.5%, 15% delivery), with manager
==============================================================================

Crew wage $18.60 (San Mateo city)
Line                            $300K sales      $450K sales      $600K sales
COGS                         $90,000 (30.0%)  $135,000 (30.0%)  $180,000 (30.0%)
Labor (crew + manager)      $124,312 (41.4%)  $157,681 (35.0%)  $191,049 (31.8%)
Rent                         $88,800 (29.6%)   $88,800 (19.7%)   $88,800 (14.8%)
Royalty + marketing          $22,500 ( 7.5%)   $33,750 ( 7.5%)   $45,000 ( 7.5%)
Card + delivery fees         $18,900 ( 6.3%)   $28,350 ( 6.3%)   $37,800 ( 6.3%)
Other opex                   $28,500 ( 9.5%)   $30,750 ( 6.8%)   $33,000 ( 5.5%)
OWNER CASH FLOW             -$73,012 (-24.3%)  -$24,331 (-5.4%)   $24,351 ( 4.1%)

Crew wage $20.00 (AB 1228, 60+ units)
Line                            $300K sales      $450K sales      $600K sales
COGS                         $90,000 (30.0%)  $135,000 (30.0%)  $180,000 (30.0%)
Labor (crew + manager)      $129,168 (43.1%)  $165,048 (36.7%)  $200,928 (33.5%)
Rent                         $88,800 (29.6%)   $88,800 (19.7%)   $88,800 (14.8%)
Royalty + marketing          $22,500 ( 7.5%)   $33,750 ( 7.5%)   $45,000 ( 7.5%)
Card + delivery fees         $18,900 ( 6.3%)   $28,350 ( 6.3%)   $37,800 ( 6.3%)
Other opex                   $28,500 ( 9.5%)   $30,750 ( 6.8%)   $33,000 ( 5.5%)
OWNER CASH FLOW             -$77,868 (-26.0%)  -$31,698 (-7.0%)   $14,472 ( 2.4%)

==============================================================================
2. Owner cash flow (pre-debt, manager paid) across scenarios
==============================================================================
Scenario / wage                                $300K       $450K       $600K
Good, $18.60 (San Mateo city)               -$50,212      $9,869     $69,951
Good, $20.00 (AB 1228, 60+ units)           -$55,068      $2,502     $60,072
Base, $18.60 (San Mateo city)               -$73,012    -$24,331     $24,351
Base, $20.00 (AB 1228, 60+ units)           -$77,868    -$31,698     $14,472
Poor, $18.60 (San Mateo city)               -$99,112    -$63,481    -$27,849
Poor, $20.00 (AB 1228, 60+ units)          -$103,968    -$70,848    -$37,728

==============================================================================
3. Sales needed for the claimed $180K cash flow (manager paid)
==============================================================================
Good, $18.60 (San Mateo city)            ~$875,000
Good, $20.00 (AB 1228, 60+ units)        ~$915,000
Base, $18.60 (San Mateo city)            ~$1,080,000
Base, $20.00 (AB 1228, 60+ units)        ~$1,140,000
Poor, $18.60 (San Mateo city)            ~$1,475,000
Poor, $20.00 (AB 1228, 60+ units)        ~$1,590,000

Rent at $300K sales = 29.6% of sales; $180K CF at $300K = 60% of sales

==============================================================================
4. Financing at $350K asking price
==============================================================================
SBA 7(a): 10% down $35,000, loan $315,000 @ 11.25%/10 yr -> $52,606/yr ($4,384/mo)
  + franchise transfer fee (est. $10K-$42.5K; use $10K): $10,000
  + working capital + inventory: $20,000
  + legal, diligence, SBA/closing, health permit: $15,000
  ~ SBA out-of-pocket: $80,000 (23% of price)
All-cash out-of-pocket: ~$395,000
Interest-free seller note: 40% down $140,000, $210,000 over 4 yrs at 0% -> $52,500/yr

Owner CF (Base)                         CF  All-cash yld  Price/CF   After SBA  After 0% note
Listing claim (as stated)         $180,000           51%      1.9x    $127,394       $127,500
$300K, $18.60                     -$73,012          -21%       n/m   -$125,618      -$125,512
$300K, $20.00                     -$77,868          -22%       n/m   -$130,474      -$130,368
$450K, $18.60                     -$24,331           -7%       n/m    -$76,937       -$76,831
$450K, $20.00                     -$31,698           -9%       n/m    -$84,304       -$84,198
$600K, $18.60                      $24,351            7%     14.4x    -$28,255       -$28,149
$600K, $20.00                      $14,472            4%     24.2x    -$38,134       -$38,028

==============================================================================
5. Comps
==============================================================================
Cupertino Base costs (no royalty, $18.60, manager paid): CF before rent $155,082 -> claim exceeds modeled CF even at ZERO rent, by $101,298
Cupertino Good costs (no royalty, $18.60, manager paid): CF before rent $191,213 -> claim exceeds modeled CF even at ZERO rent, by $65,167
  Cupertino price/CF as claimed: 1.56x; CF margin 43%
  SBA on $400K (90% @ 9.75%, >$350K tier): $56,493/yr
San Jose Gong Cha: $298K / $90K CF = 3.3x; if $90K is SDE, minus $60K manager -> $30,200 absentee CF
San Mateo as claimed: $350K / $180K = 1.94x
```

The model is deliberately middle-of-the-road. The "Good" row already assumes 25% COGS, the lowest royalty band and light delivery dependence. Even there, a manager-run shop at the earlier listing's ~$300K of sales **loses about $50K a year**. At $450K it roughly breaks even, and only around $600K does it pay the owner $60–70K. Three explanations for the $180K figure fit these numbers. It may be **SDE that includes a working owner's or family's unpaid labor**. It may be **a short period annualized**, a pattern already seen in another boba franchise resale that reported 8 months of SDE ([BizQuest BW2375745](https://www.bizquest.com/business-for-sale/turnkey-boba-franchise-priced-for-quick-sale/BW2375745)). Or the store genuinely does **$900K+ in sales**. The third is the only one that justifies the price, and it is the one the broker should be asked to prove first. Adding back the full $59.8K manager cost to the base case still leaves the shop needing roughly $800K+ of sales to show $180K of SDE.

## Brand is unknown, and every likely candidate pays $20 an hour

None of the snippets names the franchisor. The confirmed franchise or chain boba shops downtown are **Teaspoon** (128 E 3rd Ave), **TP Tea** (65 E 4th Ave), **Sharetea** (220 Main St) and **Molly Tea** (153 S B St) ([Yelp Teaspoon](https://www.yelp.com/biz/teaspoon-san-mateo-san-mateo-2); [Sharetea](https://www.1992sharetea.com/san-mateo-california); [Yelp Molly Tea](https://www.yelp.com/biz/molly-tea-san-mateo-2)). Molly Tea is new and busy, so it is an unlikely seller. Searches found no downtown Gong Cha, Yi Fang, Happy Lemon or Tea Top. The earlier listing's line "training and recipes included" weakly suggests a smaller franchisor. The fastest way to identify the brand is to ask the broker, or to match the basement and Type 1 hood against listing photos and assessor records.

| Brand | Royalty | Marketing | Transfer fee | US units | $20 AB 1228 wage? |
|---|---|---|---|---|---|
| Kung Fu Tea | 4% gross | 2% | not found | ~350–375 | **Yes** |
| Gong Cha | ~6% net (5.5%, 4–7% also reported) | 1–2% | not found | ~240+ | **Yes** |
| Sharetea | 6% gross, **$1,200/mo minimum** | ~3% planned (2019) | **$10K flat** | ~150+ | **Yes** |
| Happy Lemon | 7% gross | not found | $10K (2025 summary) | not found | Likely, verify count |
| Tiger Sugar | 7% net | not found | **50% of initial fee (~$42.5K)** | not found | Verify count |
| Teaspoon / TP Tea | not researched | — | — | not found | Verify count |
| Molly Tea | not franchised in US (assumed) | — | — | ~5 | **No** (state/local minimum) |

Sources: Kung Fu Tea ([FranchiseOverview](https://franchiseoverview.com/company/kung-fu-tea); [PulseRevOps](https://pulserevops.com/knowledge/q14704)); Gong Cha ([FranchiseOverview](https://franchiseoverview.com/company/gong-cha); [Mobile Cuisine](https://mobile-cuisine.com/franchise/gong-cha/)); Sharetea ([FDD Exchange 2019](https://fddexchange.com/fdd/sharetea-2019/); [FDD Exchange 2024](https://fddexchange.com/fdd/sharetea-2024/)); Tiger Sugar ([FDD Exchange 2022](https://fddexchange.com/fdd/tiger-sugar-2022/)); Happy Lemon ([FranchiseVerdict](https://franchiseverdict.com/brand/happy-lemon)); unit counts ([GrowthFactor](https://www.growthfactor.ai/resources/blog/boba-tea-franchise); [Asia News Network](https://asianews.network/chinas-new-style-tea-brands-find-a-hot-new-market-in-us/)). These come from aggregators, not FDDs I read. Pull the current FDD from CA DFPI before relying on any of them.

The fee spread matters at this size. Royalty plus marketing runs from 6% to 10%, which is $18K–$30K a year at $300K of sales and $36K–$60K at $600K. Sharetea's $1,200 monthly minimum royalty works out to more than 6% for any store under $240K. The wage question is close to settled. Any brand with more than 60 US units pays at least **$20/hr**, and the Fast Food Council's proposed raise to $20.70 was never adopted. As of May 2026 the council had no chair and had not met in over a year ([CalMatters](https://calmatters.org/economy/2026/05/fast-food-council-no-chairperson/)). In the model the $20 wage costs $5K–$10K a year more than San Mateo's $18.60. That gap is real, but it matters less than sales volume. Absentee ownership is allowed or barred in each FDD's **Item 15**, and that item was not found for any brand.

## Ten tea shops within walking distance, and Chinese chains still arriving

The demand base is genuine. San Mateo has a **$152,669 median household income**, is **27% Asian**, and has about 103K residents ([Census QuickFacts](https://census.gov/quickfacts/fact/table/sanmateocitycalifornia,discoverybaycdpcalifornia/PST045224)). Downtown foot traffic reportedly rose 20% from 2024 to 2025, and ridership at the downtown Caltrain station has doubled since 2023 ([The Almanac](https://www.almanacnews.com/ae/2026/05/21/renowned-restaurants-historic-architecture-and-a-car-free-corridor-heres-what-downtown-san-mateo-has-in-store/)). The supply side is the problem. Roughly **8–10 tea or boba concepts** sit within a few blocks of B St and 3rd/4th Ave: Teaspoon, Boba Bless, TP Tea, Heeretea, Tong Sui, Meet Fresh, Sweet Moment, Molly Tea, Sharetea and Tiger Tea. Hillsdale adds three more ([Best of San Mateo 2026](https://bestofsanmateo.org/place/category/best-boba-shops/); [DSMA Boba Day 2026](https://dsma.org/event/smbobaday2026/)). Molly Tea, a Chinese chain, rates **4.7 stars on 624 reviews** two blocks away, against Teaspoon's 3.8 and TP Tea's 4.1. Nationally, US boba shops roughly doubled from 2022 to 2024. HeyTea, Chagee, Mixue and Lelecha all entered California in 2025, aiming at the same young Asian-American customer ([Asia News Network](https://asianews.network/chinas-new-style-tea-brands-find-a-hot-new-market-in-us/); [NRN](https://www.nrn.com/restaurant-finance/chagee-adjusts-after-a-tough-2025-with-big-goals-for-the-u-s-)).

Several further risks affect this deal specifically:

- **Central Park.** Its main lawn, picnic areas and playgrounds closed in June 2025 for 18–24 months, so any 2025–26 trailing sales are depressed or will rebound only after the park reopens ([The Almanac](https://www.almanacnews.com/ae/2026/05/21/renowned-restaurants-historic-architecture-and-a-car-free-corridor-heres-what-downtown-san-mateo-has-in-store/)).
- **Office vacancy.** Peninsula office vacancy is still **22.5%** ([Cushman & Wakefield](https://www.cushmanwakefield.com/en/united-states/insights/us-marketbeats/san-francisco-peninsula-marketbeats)).
- **Packaging rules.** San Mateo County's foodware ordinance bans plastic and PLA disposables in adopting cities and requires fiber straws, given only on request ([SMC Sustainability](https://sustainability.smcgov.org/waste-reduction/food-service-ware-ordinance)). Franchise-mandated sealed plastic cups and wide straws may conflict with it. Whether the City of San Mateo has adopted the ordinance is unconfirmed.
- **Health permit.** The county health permit is **not transferable**. You must file a change-of-ownership application and get written approval before operating ([SMC Health](https://WWW.SMCHEALTH.ORG/sites/main/files/file-attachments/application_for_new_business_or_change_of_ownership.pdf)).
- **Delivery commissions.** At 15–30%, they cut into every app order ([DoorDash](https://merchants.doordash.com/en-us/products/pricing)).

## Halal checklist: toppings, creamers and the supply contract

Pearls, nata de coco and most teas are generally plant-based. The gelatin risk sits in **puddings, some fruit jellies, popping-boba skins and some dessert syrups**, and formulations vary by supplier. Treat any gelatin of unconfirmed source as non-halal ([HalalFoodAI](https://halalfoodai.onrender.com/blog/is-boba-tea-halal); [Froth Tea SG](https://www.frothtea.sg/?p=1187); [Halal MUI](https://halalmui.org/boba-meticulous-halal/)). Labels can contradict themselves; one retail "agar boba" is described as both gelatin and plant-derived ([Walmart](https://www.walmart.com/ip/5343757741)). No US halal-certified boba chain turned up.

Get the spec sheet for every SKU on the menu and check these items:

- **Pudding** (egg or custard pudding is often set with gelatin)
- **Fruit and coffee jellies**, which may use gelatin, agar, konjac or carrageenan
- **Popping boba**
- **Cheese or milk foam** and its stabilizers
- **Non-dairy creamers**, for mono- and diglycerides of unknown origin
- **Flavor syrups**, for alcohol-based extracts
- **Ice cream, mochi and marshmallow add-ons**
- **Glazes on pearls**

Pudding, cheese foam, creamer and extract are my own precautionary additions, not sourced findings. Then check two things in the franchise agreement. **Item 8 (required suppliers)** usually forces proprietary toppings, so dropping or replacing a non-halal item needs franchisor approval. Also confirm that no brand promotion or limited-time menu involves alcohol, and that the franchisor will let you omit items permanently. If the franchisor refuses, you will be selling non-halal products under your ownership, and that should end the deal.

## Out-of-pocket cash and three ways to pay

| Structure | Cash at close | Annual debt cost | Riba-free? |
|---|---|---|---|
| All cash at $350K | **~$395K** (price + ~$45K transfer fee, working capital, legal/permit) | $0 | Yes |
| SBA 7(a), 10% down, $315K at 11.25% for 10 yrs | **~$80K** (23% of price) | **$52.6K/yr** ($4,384/mo) | No |
| Seller installment, 40% down, $210K at 0% over 4 yrs | ~$185K | $52.5K/yr | Yes, if structured as a fixed-price installment sale with no interest-bearing late fees |

The SBA rate tier ($250K–$350K at prime + 4.5% = 11.25%) follows the earlier Dublin research ([sba7a.loans](https://www.sba7a.loans/sba-7a-loans-small-business-blog/what-is-the-sba-7a-loan-interest-rate/)). Note that both financed routes cost about **$52.5K a year**. The base-case shop does not cover that at any sales level modeled, so the debt would be paid from your own pocket. An interest-free seller note is worth requesting for a different reason: a seller confident in $180K would accept being paid out of it. Refusal is itself diligence information. Islamic lenders (UIF/LARIBA, Bank of Whittier) were not confirmed to fund goodwill-heavy acquisitions.

## How the Cupertino and San Jose comps compare

| Listing | Price | Sales | Claimed CF | Claimed multiple | Model view |
|---|---|---|---|---|---|
| San Mateo franchise (absentee) | ~$350K | unknown (~$300K in prior sale) | ~$180K | 1.9x | Needs ~$0.9–1.6M sales; at $300–450K, absentee CF is negative |
| Cupertino independent (manager-run) | $400K | **$592,318** | **$256,380** | 1.56x | No royalty and possibly local wage only. Even so, modeled CF before any rent is $155–191K, so the claim exceeds the model by $65–101K at zero rent |
| San Jose Gong Cha (since 2023) | $298K | not shown | $90K | 3.3x | If $90K is SDE, about $30K after a manager, roughly 10x absentee |

Sources: [DealStream Santa Clara](https://dealstream.com/california/santa-clara-county/absentee-owned-businesses-for-sale); [BizBen Cupertino](https://www.bizben.com/business-for-sale/cupertino-california-ca); [BizBuySell CA cafes p.2](https://www.bizbuysell.com/california/coffee-shops-and-cafes-for-sale/2/).

**Cupertino** is the most credible of the three because it discloses sales. It is not a franchise, so there is no royalty and no transfer fee, and possibly no $20 wage if it is a small independent. Its **43% margin** still needs costs far below the industry ranges: very low COGS, short hours and lean staffing. The listing itself admits as much: an owner-operator "can easily increase profits by working at the store in place of the manager and opening longer." It deserves a phone call and a request for the P&L, the lease and the brand or recipe ownership. **The San Jose Gong Cha** is the most honestly priced at 3.3x, but it pays the $20 wage and Gong Cha royalties, and almost nothing remains for an absentee owner. All three need an explicit no-alcohol and halal-topping confirmation.

## Questions for the broker and due-diligence steps

Ask the broker for these before any meeting or offer:

1. The brand and franchisor, and confirmation that it is the store sold via SellingRestaurants for $125K.
2. Three years of **tax returns and POS sales reports** (monthly), plus delivery-platform payout statements.
3. Exactly how the $180K was calculated: SDE or net of a manager, the period it covers, and the add-backs.
4. Current staffing, hours and pay rates, whether a manager is in place, and the reason for sale.
5. Whether the store pays $20/hr (AB 1228 compliance), and any wage claims.
6. Lease expiry, options, escalators, the personal guarantee and landlord consent to assignment.
7. Franchise term remaining, transfer fee, required remodel, and Item 15 on whether absentee ownership is allowed.
8. Willingness to carry an interest-free installment note.
9. Whether the brand is on the SBA franchise directory.

Diligence should then cover these:

- Pull the current FDD (Items 6, 8, 15, 17, 19 and 20) from CA DFPI and call five former franchisees from Item 20.
- Spend two weekday and two weekend afternoons counting cups at this store and at Molly Tea.
- Confirm the health change-of-ownership timeline at (650) 372-6200.
- Check foodware-ordinance compliance of the franchise cups and straws.
- Collect the halal spec sheets listed above.
- Make the purchase contingent on sales verification, franchisor approval, lease assignment and the new health permit.

## Conclusion

The headline 1.9x multiple is a measure of missing information, not a bargain. Once a manager is paid at San Mateo wages, the claimed $180K needs about three times the sales this footprint last reported. The rent and fees are fixed, so each lost cup hurts more than a gained cup helps, and that matters in a cluster where newer chains are winning the reviews. At verified sales of $300–450K, the business is worth roughly its lease and equipment, in line with the **$85K–$218K** downtown comps and the $125K prior sale. It is not worth $350K. My recommendation is **do not pursue at the asking price**. Spend one email getting the brand, the tax returns and the definition of cash flow. Re-engage only if the verified records show sales near $1M, or if the seller will accept roughly $100K–$150K, all cash or on an interest-free installment note, with halal-topping substitution approved in writing. That is the same conclusion the wider Dublin search reached. For a buyer who will not work in the business, low-risk absentee assets trade at about 3–5x real earnings. Manager-run route and franchise-service businesses deliver that more reliably than food retail with $20 labor and $89K rent.
