"""Top 100 businesses for sale near Dublin, CA (asking <= $2M), absentee buyer.

Positions 1-30 come unchanged from top30_calc.py (its lists and formulas are
executed here and the printed rows are checked cell-for-cell).  Positions
31-100 are new listings from the research notes, ranked by a risk-weighted
absentee-adjusted multiple.  All money figures are in $K.

Formulas (identical to top30_calc.py):
  adjusted CF   = cash flow - estimated manager cost
  adj multiple  = asking / adjusted CF
  out of pocket = 13% of asking
  loan          = 90% of asking, at the SBA 7(a) max variable rate
                  (prime 6.75%: <=$50K +6.5, <=$250K +6, <=$350K +4.5, else +3)
  annual pmt    = 10-year fully amortising payment x 12
  left after    = adjusted CF - annual payment
  all-cash yld  = adjusted CF / asking   (interest-free / no-loan view)

Ranking key for 31-100 = adj multiple x risk weight x absentee factor
  risk weight: Low 1.0, Low-Med 1.15, Medium 1.3, Med-High 1.5, High 1.8
  absentee factor: 0.85 when the listing itself says absentee / manager in place
Rows with adjusted CF <= 0 cannot be ranked and go below the cut.
"""
import contextlib, io, os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- 1. Load the fixed top 30 exactly as top30_calc.py builds them ---------
ns = {}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(open(os.path.join(HERE, "top30_calc.py")).read(), ns)
TOP30_LINES = [l for l in buf.getvalue().splitlines() if l.startswith("| ") and l[2].isdigit()]
rate, pmt, top30_rows = ns["rate"], ns["pmt"], ns["rows"]
assert len(top30_rows) == 30 and len(TOP30_LINES) == 30

def f(v):
    if abs(v) < 0.5: v = 0
    s = "-" if v < 0 else ""
    v = abs(v)
    return f"{s}${v:,.0f}K" if v < 1000 else f"{s}${v/1000:.2f}M"

# Status / flag / source for the fixed top 30 (keyed by rank)
BBS = "https://www.bizbuysell.com/california/"
T30 = {
 1: ("Active ('Hot Listing'); **cash only, no financing**", "NOTE: later research showed $451K is 18% *gross commission*; realistic absentee net ~$95-175K", "[BizQuest BW2368281](https://www.bizquest.com/business-for-sale/mission-foods-master-distributorship-for-sale-vallejo-ca-619-000/BW2368281)"),
 2: ("Now **$275K 'cash only'** on BizQuest; leased (no property)", "NOTE: price now $275K cash-only; leased site; realistic absentee net ~$40-75K", "[BizQuest Fairfield](https://images.bizquest.com/car-washes-for-sale-in-fairfield-ca)"),
 3: ("Unverified", "", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 4: ("Unverified", "", f"[BizBuySell SF]({BBS}san-francisco-businesses-for-sale/)"),
 5: ("Unverified", "", f"[BizBuySell routes]({BBS}san-francisco-bay-area/routes-for-sale/)"),
 6: ("Current per Bay Advisors", "", "[Bay Advisors](https://thebayadvisors.com/profitable-fedex-routes-for-sale-san-francisco-bay-area/)"),
 7: ("Unverified", "", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)"),
 8: ("Unverified", "", f"[BizBuySell routes]({BBS}san-francisco-bay-area/routes-for-sale/)"),
 9: ("Unverified", "", "[MergerPlace](https://www.mergerplace.com/business-for-sale/buy/san-jose)"),
 10: ("Unverified", "", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 11: ("May be stale", "", "[BusinessBroker.net](https://www.businessbroker.net/city/san-jose-ca-businesses-for-sale.aspx)"),
 12: ("Unverified", "", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)"),
 13: ("Unverified", "**EXCLUDED - alcohol**", f"[BizBuySell retail]({BBS}san-francisco-bay-area/retail-businesses-for-sale/)"),
 14: ("Unverified (city confidential)", "", "[BizQuest SC2186](https://www.bizquest.com/business-for-sale/recession-resistant-mail-center-franchise-in-norcal-sc2186/BW2253936)"),
 15: ("Unverified", "", f"[BizBuySell Sacramento]({BBS}sacramento-established-businesses-for-sale/2/)"),
 16: ("Unverified", "", f"[BizBuySell services]({BBS}san-francisco-bay-area/service-businesses-for-sale/)"),
 17: ("Unverified", "", f"[BizBuySell mfg]({BBS}san-francisco-bay-area/manufacturing-businesses-for-sale/)"),
 18: ("Unverified", "", f"[BizBuySell Sac Co.]({BBS}sacramento-county-businesses-for-sale/)"),
 19: ("Unverified", "**EXCLUDED - alcohol** (beer & wine; c-store)", f"[BizBuySell San Joaquin]({BBS}san-joaquin-county-businesses-for-sale/)"),
 20: ("Unverified", "", "[BizQuest Santa Cruz](https://www.bizquest.com/mid-market-businesses-for-sale-in-santa-cruz-county-ca/)"),
 21: ("Unverified", "", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 22: ("Unverified", "", "[Rejigg SF](https://www.rejigg.com/for-sale/california/san-francisco)"),
 23: ("Unverified", "", f"[BizBuySell Sacramento]({BBS}sacramento-businesses-for-sale/)"),
 24: ("Unverified", "", f"[BizBuySell routes]({BBS}san-francisco-bay-area/routes-for-sale/)"),
 25: ("Unverified (alt. $1.375M listing)", "", f"[BizBuySell Sonoma]({BBS}sonoma-county-businesses-for-sale/)"),
 26: ("Unverified", "", "[DealStream Napa](https://dealstream.com/california/napa/small-businesses-for-sale)"),
 27: ("**Offer pending**", "", f"[BizBuySell IT]({BBS}san-francisco-bay-area/it-and-software-service-businesses-for-sale/)"),
 28: ("Unverified", "Alcohol unknown - verify", f"[BizBuySell SF restaurants]({BBS}san-francisco/restaurants-and-food-businesses-for-sale/)"),
 29: ("Unverified", "**EXCLUDED - alcohol** (ABC Type 47)", f"[BizBuySell Santa Cruz]({BBS}santa-cruz-county-businesses-for-sale/)"),
 30: ("Unverified", "Alcohol unknown - verify", f"[BizBuySell SF restaurants]({BBS}san-francisco/restaurants-and-food-businesses-for-sale/)"),
}

# Manager-cost basis labels for the top-30 amounts (amounts themselves are top30_calc.py's)
T30B = dict(enumerate(["route drivers/mgr", "site mgr", "licensed RME", "pharmacist-in-charge + mgr",
    "ops mgr", "ops mgr", "ops mgr", "ops mgr", "shop mgr", "salon/school mgr", "store mgr",
    "licensed tech-mgr", "store mgr", "store mgr", "ops mgr", "spa mgr", "plant mgr", "licensed RME",
    "store mgr", "lab mgr", "ops mgr", "GM in place (residual)", "GM", "ops mgr", "licensed RME",
    "franchise mgr", "service mgr", "restaurant mgr", "restaurant mgr", "restaurant mgr"], 1))

# ---- 2. New candidate listings (31-100 pool) --------------------------------
# (name, drive, asking $K, cash flow $K, mgr $K, mgr basis, risk, absentee_stated, status/flag, source)
BB = "https://www.bizben.com/business-for-sale/"
BQ = "https://www.bizquest.com/"
DS = "https://dealstream.com/california/"
C = [
 # Alameda / Contra Costa (new notes)
 ("FedEx Ground 13 routes, San Leandro", "20m", 1600, 481.5, 75, "ops mgr", "Low", 0, "Unverified; same page as 10-route pkg", f"[BizBen 289956]({BB}fedex-ground-routes-for-sale-in-san-leandro-california-289956)"),
 ("FedEx Ground 10 routes, San Leandro", "20m", 1000, 360.2, 75, "ops mgr", "Low", 0, "Unverified; same seller as 13-route pkg?", f"[BizBen 289956]({BB}fedex-ground-routes-for-sale-in-san-leandro-california-289956)"),
 ("FedEx routes, SBA pre-qual, Contra Costa", "25m", 1125, 438.4, 75, "ops mgr", "Low", 0, "Unverified; broker marks many sold", "[Bay Advisors](https://thebayadvisors.com/fedex-routes-sba-pre-qualified-newer-fleet-sales-of-2-1m-contra-costa-country/)"),
 ("The UPS Store, Newark", "20m", 849, 262.4, 70, "franchise mgr", "Low-Med", 0, "**SALE PENDING** (backup offer)", "[BizBuySell 2393051](https://www.bizbuysell.com/business-opportunity/the-ups-store-franchise-in-alameda-county-ca/2393051/)"),
 ("Absentee coin laundry, Martinez", "30m", 671.6, 116.9, 15, "absentee oversight", "Low-Med", 1, "Possibly stale (~333 days); lease to 2029", f"[BizBen CA laundromats]({BB}coin-laundry-laundromats-businesses-for-sale-type-california-ca)"),
 ("Simple coin/card laundry, Pinole", "40m", 320, 66, 40, "attendant", "Low-Med", 0, "Just listed", f"[BizBen 4435250]({BB}simple-coincard-laundry-for-sale-in-pinole-contra-costa-county-ca-4435250)"),
 ("Well-managed coin laundry, Alameda Co.", "25m", 159.95, 34.5, 40, "attendant", "Low-Med", 0, "Stale (Apr 2025)", f"[BizBen 283018]({BB}coin-laundry-for-sale-in-alameda-county-california-283018.php)"),
 ("Coin laundry in shopping ctr, Oakland", "30m", 160, 38.3, 40, "attendant", "Low-Med", 0, "**IN CONTRACT**", f"[BizBen 4453837]({BB}simple-coin-laundry-in-shopping-center-in-oakland-4453837)"),
 ("Landscaping co. (30 yrs), Alameda Co.", "20m", 700, 220, 90, "service GM", "Medium", 0, "Unverified", f"[BizBuySell Alameda]({BBS}alameda-county-businesses-for-sale/)"),
 ("HVAC, home-based, Contra Costa", "25m", 195, 105.6, 120, "licensed RME", "Med-High", 0, "Unverified", f"[BizBuySell HVAC]({BBS}hvac-businesses-for-sale/)"),
 ("HVAC + real estate, Concord", "25m", 1024, 133, 120, "licensed RME", "Med-High", 0, "Unverified; pitched to a technician", f"[BizBuySell HVAC]({BBS}hvac-businesses-for-sale/)"),
 ("Cabinet-finishing mfr, 'absentee', Contra Costa", "25m", 1150, 241.5, 15, "absentee oversight", "Medium", 1, "Unverified; SBA-ready", "[BizBuySell CC mfg](https://m.bizbuysell.com/california/contra-costa-county/manufacturing-businesses-for-sale)"),
 ("Preschool, San Ramon", "10m", 299, 90, 70, "director", "Medium", 0, "Unverified", f"[BizBuySell education]({BBS}san-francisco-bay-area/education-and-child-related-businesses-for-sale/)"),
 ("Print shop, Berkeley", "35m", 250, 90, 55, "shop mgr", "Medium", 0, "Unverified", f"[BizBen print]({BB}printing-businesses-for-sale-type-california-ca)"),
 ("Vending business, Alameda Co.", "20m", 52, 28.3, 20, "PT restocker", "Medium", 0, "Unverified", f"[BizQuest vending]({BQ}vending-machines-and-routes-businesses-for-sale-in-alameda-county-ca)"),
 ("Takeout pizza, 'absentee', Concord", "25m", 149, 83.5, 15, "absentee oversight", "High", 1, "Alcohol unknown - verify", "[BizBuySell CC](https://m.bizbuysell.com/california/contra-costa-county-businesses-for-sale)"),
 ("Franchise bakery, Concord", "25m", 190, 74, 70, "franchise mgr", "Medium", 0, "Unverified", "[BizBuySell CC bakeries](https://m.bizbuysell.com/california/contra-costa-county/bakeries-for-sale/)"),
 ("Bento/fried chicken, absentee, Pleasanton", "10m", 185, 75.3, 15, "absentee oversight", "High", 1, "Stale (Jun 2025); alcohol unknown", f"[BizBen Pleasanton]({BB}pleasanton-alameda-county-cafe-restaurant-for-sale-260855.php)"),
 # North Bay
 ("FedEx Ground 8 routes, Fairfield", "45m", 1175, 345.3, 75, "ops mgr", "Low", 0, "Unverified (newer ID)", f"[BizBen 287395]({BB}fedex-ground-routes-for-sale-in-fairfield-california-287395)"),
 ("Tanning franchise, 4 units, 'absentee', Santa Rosa", "1h15m", 1795, 528.7, 15, "absentee oversight", "Med-High", 1, "CF not clearly tied to listing", f"[BizQuest absentee]({BQ}absentee-businesses-for-sale-in-santa-rosa-ca)"),
 ("Laundromat, low rent, Solano Co.", "45m", 350, 145.9, 40, "attendant", "Low-Med", 0, "Unverified; **cash-only sale**; lease to 2031", f"[BizBen Solano]({BB}solano-county-california-ca)"),
 ("Owner-absentee laundromat, Solano Co.", "45m", 490, 37.7, 15, "absentee oversight", "Low-Med", 1, "Price/CF pairing uncertain", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)"),
 ("Mission Foods route, Napa", "50m", 90, 83.7, 55, "route driver", "Medium", 0, "Unverified; no financing on Mission routes", f"[BizBuySell Napa]({BBS}napa-county-businesses-for-sale/)"),
 ("Mission Foods multi-route, Napa", "50m", 300, 210.2, 110, "2 drivers", "Medium", 0, "Unverified; no financing", f"[BizBuySell routes p6]({BBS}routes-for-sale/6/)"),
 ("Mission Foods route, Sonoma", "1h05m", 129, 95.3, 55, "route driver", "Medium", 0, "Unverified; no financing", f"[BizBuySell Sonoma]({BBS}sonoma-county-businesses-for-sale/)"),
 ("Mission Foods route (7 accts), Santa Rosa", "1h15m", 179, 123.5, 55, "route driver", "Medium", 0, "Possibly stale (~340 days); no financing", "[RoutesRUs 70548](https://routesrus.com/mission-foods-santa-rosa-ca-ca-70548/)"),
 ("Staffing agency, San Rafael", "50m", 215, 96, 70, "office mgr", "Medium", 0, "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Home-care franchise (non-medical), Marin", "55m", 375, 95, 70, "franchise mgr", "Medium", 0, "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Bookkeeping practice, San Rafael", "50m", 240, 104, 70, "office mgr", "Medium", 0, "Unverified", f"[BizBuySell accounting]({BBS}san-francisco-bay-area/accounting-businesses-and-tax-practices-for-sale/)"),
 ("Door-to-door airport shuttle, San Rafael", "50m", 202, 125, 60, "driver-mgr", "Med-High", 0, "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Background investigation co., Novato", "55m", 599, 175, 120, "licensed PI mgr", "Medium", 0, "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Window screen install/repair, Santa Rosa", "1h15m", 525, 191.5, 70, "ops mgr", "Medium", 0, "Price reduced; alt SDE $235K", "[BizBuySell 2297146](https://www.bizbuysell.com/business-opportunity/window-screen-installation-and-repair-price-reduced/2297146/)"),
 ("Landscape company, Solano Co.", "45m", 550, 161, 90, "service GM", "Medium", 0, "Unverified", f"[BizQuest Solano]({BQ}landscaping-services-businesses-for-sale-in-solano-county-ca)"),
 ("Junk-hauling franchise, Petaluma", "1h", 265, 70, 70, "franchise mgr", "Medium", 0, "CF alt $101.8K", f"[BizBuySell waste]({BBS}waste-management-and-recycling-businesses-for-sale/)"),
 ("True REST float spa franchise, Napa", "50m", 135, 75.1, 70, "franchise mgr", "Medium", 0, "Unverified", f"[BizBuySell Napa]({BBS}napa-county-businesses-for-sale/)"),
 ("Juice bar franchise, Napa Co.", "50m", 299, 93.7, 70, "franchise mgr", "Medium", 0, "Unverified; same as 'Napa Health Cafe'?", f"[BizBuySell Napa]({BBS}napa-county-businesses-for-sale/)"),
 ("Dry cleaners, San Rafael", "50m", 249, 10, 55, "shop mgr", "Med-High", 0, "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Spa (50% seller financing), Novato", "55m", 495, 150, 70, "shop mgr", "Medium", 0, "Unverified; seller finance offered", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 # South Bay / Peninsula / SF
 ("FedEx Ground 13 routes, San Jose ($1.1M + veh. fin.)", "30m", 1275, 580.6, 75, "ops mgr", "Low-Med", 0, "Figures conflict across versions", f"[BizBen 288357]({BB}fedex-ground-routes-for-sale-in-san-jose-california-288357)"),
 ("FedEx Ground 10 P&D routes, San Jose", "30m", 1035, 305, 75, "ops mgr", "Low-Med", 0, "Not tied to a specific listing", f"[BizQuest SJ routes]({BQ}routes-for-sale-in-san-jose-ca/)"),
 ("Mission Foods route, San Jose", "30m", 179, 125.8, 55, "route driver", "Medium", 0, "Reduced; no financing", f"[BizBuySell SJ distribution]({BBS}san-jose/wholesale-and-distribution-businesses-for-sale/)"),
 ("Vending, 10 warranted machines, San Jose", "30m", 130, 86.4, 25, "PT restocker", "Med-High", 0, "CF/machine looks high - verify", f"[DealStream Santa Clara]({DS}santa-clara-county-businesses-for-sale)"),
 ("Absentee coin laundry, San Jose", "30m", 160, 31.7, 15, "absentee oversight", "Low-Med", 1, "Stale? (posted 3/2025)", f"[BizBen SJ laundromats]({BB}laundromat-for-sale-in-san-jose-california-290105.php)"),
 ("Commercial cleaning/janitorial, Santa Clara Co.", "35m", 700, 200, 80, "service GM", "Medium", 0, "Unverified", f"[BizBuySell cleaning]({BBS}san-francisco-bay-area/cleaning-businesses-for-sale/)"),
 ("HOA cleaning company, Santa Clara Co.?", "35m", 675, 190, 80, "service GM", "Medium", 0, "Location uncertain", f"[BizBuySell CA cleaning]({BBS}cleaning-businesses-for-sale/)"),
 ("Residential plumbing, Santa Clara Co.", "35m", 697, 423, 140, "licensed RME", "Medium", 0, "Price conflict ($697K/$797K)", f"[BizBuySell plumbing]({BBS}plumbing-businesses-for-sale/)"),
 ("HVAC company (since 2015), Bay Area", "~35m", 1000, 350, 140, "licensed RME", "Medium", 0, "County unknown", f"[BizBuySell HVAC]({BBS}san-francisco-bay-area/hvac-businesses-for-sale/)"),
 ("Printing shop, South Bay", "35m", 495, 191.2, 80, "service GM", "Medium", 0, "Unverified", f"[DealStream Santa Clara]({DS}santa-clara-county-businesses-for-sale)"),
 ("Auto service franchise, **mgr in place**, South Bay", "35m", 145, 105, 15, "mgr in place", "Medium", 1, "Unverified", f"[DealStream auto]({DS}santa-clara-county/auto-repair-businesses-for-sale)"),
 ("Tuxedo rental, Santa Clara Co.", "35m", 620, 182.4, 70, "shop mgr", "Med-High", 0, "Figures conflict (alt $645K/$168.6K)", f"[DealStream Santa Clara]({DS}santa-clara-county-businesses-for-sale)"),
 ("Absentee boba tea shop, Santa Clara Co.", "35m", 400, 256.4, 15, "absentee oversight", "Medium", 1, "Unverified; confirm no alcohol", f"[DealStream Santa Clara]({DS}santa-clara-county-businesses-for-sale)"),
 ("Multi-location tutoring, Milpitas", "25m", 450, 222, 70, "center director", "Medium", 0, "Price $450K/$500K pairing uncertain", f"[BizBuySell Milpitas]({BBS}milpitas-businesses-for-sale/)"),
 ("Large preschool, SBA eligible, Milpitas", "25m", 750, 173, 70, "director", "Medium", 0, "Alt price $520K", f"[BizQuest BW2439415]({BQ}business-for-sale/preschool-business-for-sale-milpitas/BW2439415)"),
 ("Express Employment franchise, South SF", "45m", 425, 319.3, 80, "branch mgr", "Medium", 0, "Unverified", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 ("Dry cleaner, Redwood City", "45m", 120, 75.3, 55, "shop mgr", "Med-High", 0, "Unverified", f"[BizBuySell dry cleaners]({BBS}san-francisco-bay-area/dry-cleaners-for-sale/)"),
 ("Children's play & party center, San Mateo", "40m", 1200, 273, 70, "shop mgr", "Medium", 0, "Unverified", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 ("Absentee boba franchise, San Mateo", "40m", 350, 180, 15, "absentee oversight", "Medium", 1, "Unverified; confirm no alcohol", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 ("Corporate catering, **manager-operated**, SF", "45m", 325, 155.4, 15, "mgr in place", "Medium", 1, "Confirm no alcohol service", f"[BizBuySell SF Co.]({BBS}san-francisco-county-businesses-for-sale/)"),
 # Valley / Sacramento / Santa Cruz / San Benito
 ("FedEx linehaul 4 routes, **FT mgr in place**, Stockton", "50m", 1275, 422.8, 15, "mgr in place", "Low", 1, "Active? (cash price)", "[BusinessBroker.net Stockton](https://www.businessbroker.net/city/stockton-ca-businesses-for-sale.aspx)"),
 ("Partially absentee coin laundry, Sacramento", "1h20m", 350, 70.3, 30, "partial absentee", "Low-Med", 1, "Active? (also seen at $400K)", f"[BizBen 2810644]({BB}coin-laundry-as-absentee-owners-run-for-sale-in-sacramento-2810644)"),
 ("Laundromat, high traffic, Modesto", "1h", 650, 108, 40, "attendant", "Low-Med", 0, "Active? (seller 'net')", f"[BizBen 277572]({BB}laundromat-for-sale-in-modesto-california-277572.php)"),
 ("Laundromat, 100+ machines, Modesto", "1h", 1700, 268, 60, "attended mgr", "Low-Med", 0, "Listing page not found on re-search", f"[BizBuySell Modesto]({BBS}modesto-merced-area-businesses-for-sale/)"),
 ("Juice bar franchise, 'absentee-owned', Modesto", "1h", 349, 70.5, 15, "absentee oversight", "Medium", 1, "Active?", f"[BizBuySell Modesto]({BBS}modesto-merced-area-businesses-for-sale/)"),
 ("HVAC service, 200+ maint. accts, Sacramento Co.", "1h20m", 250, 124.4, 120, "licensed RME", "Med-High", 0, "Active?", f"[BizBuySell Sac HVAC]({BBS}sacramento-county/hvac-businesses-for-sale/)"),
 ("HVAC & refrigeration, Sacramento Co.", "1h20m", 500, 184.1, 120, "licensed RME", "Medium", 0, "Active?; SBA eligible", f"[BizBuySell Sac HVAC]({BBS}sacramento-county/hvac-businesses-for-sale/)"),
 ("Wholesale/distribution, Stockton", "50m", 300, 180, 70, "ops mgr", "Med-High", 0, "Products unknown - verify no alcohol/tobacco", f"[BizQuest Stockton]({BQ}wholesale-and-distribution-businesses-for-sale-in-stockton-ca/)"),
 ("ServiceMaster franchise group, Santa Cruz Co.", "1h10m", 1200, 245, 80, "service GM", "Medium", 0, "Active?", f"[BizBen Santa Cruz]({BB}santa-cruz-county-california-ca)"),
 ("OEM wiring-harness manufacturer, Santa Cruz", "1h10m", 1100, 365.7, 100, "mfg GM", "Medium", 0, "Active?", f"[BizBuySell Santa Cruz mfg]({BBS}santa-cruz/manufacturing-businesses-for-sale/)"),
 ("Salsa manufacturer/wholesaler, Watsonville", "1h15m", 98, 51.8, 55, "shop mgr", "Medium", 0, "Active?", f"[BizQuest Watsonville]({BQ}businesses-for-sale-in-watsonville-ca)"),
 ("Firewood & lumber **with property**, Watsonville", "1h15m", 600, 174.8, 70, "yard mgr", "Medium", 0, "Active?; RE included", f"[BizBuySell Santa Cruz]({BBS}santa-cruz-county-businesses-for-sale/)"),
 ("Bicycle retail & repair, Hollister", "1h15m", 349.9, 120, 55, "shop mgr", "Med-High", 0, "Active?", f"[BizBuySell San Benito]({BBS}san-benito-county-businesses-for-sale/)"),
 ("Tax & bookkeeping practice, Lodi", "1h", 410, 137, 90, "EA/CTEC mgr", "Med-High", 0, "Verify not a CPA firm", f"[BizBuySell accounting p2]({BBS}accounting-businesses-and-tax-practices-for-sale/2/)"),
 # Absentee-category notes
 ("Absentee-run coin laundry (#2488231), Oakland", "30m", 449.9, 83.4, 15, "absentee oversight", "Low-Med", 1, "Presumed active; owner retiring", "[BizBuySell 2488231](https://www.bizbuysell.com/business-opportunity/simple-coin-laundry-as-absentee-owner-s-run-for-sale-in-oakland/2488231/)"),
 ("Absentee coin laundry #2, Oakland", "30m", 563, 92.4, 15, "absentee oversight", "Low-Med", 1, "Presumed active; no listing ID", f"[BizBuySell Oakland]({BBS}oakland/laundromats-and-coin-laundry-businesses-for-sale/)"),
 ("Owner-absentee laundromat, Santa Clara Co.", "35m", 220, 94.1, 15, "absentee oversight", "Medium", 1, "Cash offer only; rent ~41% of rev.", "[BizBen 2134986](https://www.bizben.com/business-for-sale/owner-absentee-laundromatbusy-area-with-parking-2134986)"),
 ("Absentee-run coin laundry, Carmichael (edge)", "1h25m", 791.5, 131.9, 15, "absentee oversight", "Low-Med", 1, "Presumed active; lease to 2040", f"[BizBen Sacramento]({BB}laundromat-for-sale-sacramento-california-192539.php)"),
 ("Gutter franchise, semi-absentee, Alameda Co.", "20m", 400, 162.9, 30, "partial absentee", "Medium", 1, "Est. 2024; verify CSLB qualifier; $60K down", "[FCBB 234-25087](https://sfbay.fcbb.com/listing-property/construction-alameda-county-ca-high-growth-gutter-services-franchise-1.35m-revenue-absentee-friendly-234-25087)"),
 ("Non-medical home care franchise, Alameda Co.", "20m", 888.9, 318, 80, "office mgr", "Medium", 0, "Presumed active; gov't payers", f"[BizBuySell assisted living]({BBS}san-francisco-bay-area/assisted-living-and-nursing-homes-for-sale/)"),
 # Earlier bay_area.md rows not in the top 30
 ("Freight forwarder/NVOCC, San Mateo Co.", "45m", 150, 81.6, 70, "ops mgr", "Med-High", 0, "Unverified; 4% margin", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 ("Auto repair (40+ yrs), Fremont", "20m", 150, 94, 80, "shop mgr", "Med-High", 0, "Unverified", f"[BizBuySell Alameda auto]({BBS}alameda-county/auto-repair-and-service-shops-for-sale/)"),
 ("Auto repair shop, Fremont", "20m", 175, 110, 80, "shop mgr", "Med-High", 0, "Unverified", f"[BizBuySell Alameda auto]({BBS}alameda-county/auto-repair-and-service-shops-for-sale/)"),
 ("Auto body shop, San Francisco", "45m", 275, 126.4, 80, "shop mgr", "Med-High", 0, "Unverified", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)"),
 ("Catering business, San Francisco", "45m", 449, 155, 70, "kitchen mgr", "High", 0, "Alcohol unknown - verify", f"[BizBuySell SF services]({BBS}san-francisco/service-businesses-for-sale/)"),
 ("Boba/tea shop, San Jose", "30m", 450, 120, 55, "shop mgr", "Medium", 0, "Unverified; new lease needed", f"[BizBen San Jose]({BB}san-jose-city-california-ca-businesses-for-sale)"),
 ("Paving contractor, Marin", "55m", 495, 150, 120, "licensed RME", "Med-High", 0, "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Subway franchise, Fairfield", "45m", 275, 98.4, 70, "franchise mgr", "Medium", 0, "Unverified; menu has pork items", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)"),
 ("Downtown restaurant, Vacaville", "50m", 510, 125, 70, "restaurant mgr", "High", 0, "Alcohol unknown - verify", f"[BizBuySell Solano food]({BBS}solano-county/restaurants-and-food-businesses-for-sale/)"),
 ("Indian restaurant, San Jose", "30m", 850, 245, 70, "restaurant mgr", "High", 0, "Alcohol unknown - verify", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)"),
 ("Moving & storage co., Santa Rosa", "1h15m", 842.4, 210.6, 80, "ops mgr", "Medium", 0, "Unverified; 8% margin", f"[BizBuySell Santa Rosa]({BBS}santa-rosa-businesses-for-sale/)"),
 ("Pizzeria, San Mateo Co.", "45m", 199, 65.9, 55, "restaurant mgr", "High", 0, "Alcohol unknown - verify", f"[BizBuySell San Mateo food]({BBS}san-mateo-county/restaurants-and-food-businesses-for-sale/)"),
 # Earlier norcal_central.md rows in radius, not in top 30
 ("Trucking co., dedicated routes, Stockton", "50m", 190, 95, 70, "dispatcher-mgr", "Med-High", 0, "Unverified", f"[BizQuest San Joaquin]({BQ}businesses-for-sale-in-san-joaquin-county-ca/)"),
 ("Snack food route, San Joaquin Co.", "50m", 230, 77.5, 55, "route driver", "Medium", 0, "Unverified", f"[BizBuySell distribution p3]({BBS}wholesale-and-distribution-businesses-for-sale/3/)"),
 ("Mexican restaurant, Modesto", "1h", 1075, 306, 70, "restaurant mgr", "High", 0, "Alcohol unknown - verify", f"[BizBuySell Modesto]({BBS}modesto-businesses-for-sale/)"),
 ("Teriyaki restaurant, Sacramento", "1h20m", 1000, 393.3, 70, "restaurant mgr", "High", 0, "Alcohol unknown - verify", f"[BizBuySell Sacramento]({BBS}sacramento-established-businesses-for-sale/2/)"),
 # UPS Store / mail-center notes
 ("The UPS Store, Napa Co.", "50m", 699, 222.1, 70, "franchise mgr", "Low-Med", 0, "Possibly **PENDING** (Franchise Clearly)", "[BizBuySell 2393047](https://www.bizbuysell.com/business-opportunity/the-ups-store-franchise-in-napa-county-ca/2393047/)"),
 ("The UPS Stores, Marin/Sonoma seller (bundle snippet)", "45m-1h15m", 630, 196.1, 70, "franchise mgr", "Low-Med", 0, "Price/CF pairing uncertain", f"[BizBuySell UPS]({BBS}ups-stores-for-sale/)"),
 ("Silicon Valley mail center franchise (SC2248)", "35m", 174.9, 20, 70, "franchise mgr", "Low-Med", 0, "Unverified", f"[BizQuest SC2248]({BQ}business-for-sale/recession-resistant-silicon-valley-mail-center-franchise-sc2248/BW2441517)"),
]

W = {"Low": 1.0, "Low-Med": 1.15, "Medium": 1.3, "Med-High": 1.5, "High": 1.8}

def calc(p, cf, m):
    adj = cf - m; L = p * 0.9; r = rate(L * 1000); a = pmt(L, r); oop = p * 0.13
    mult = p / adj if adj > 0 else None
    return adj, mult, oop, L, r, a, adj - a, adj / p * 100

HDR = ("| # | Business | Drive | Asking | Cash flow | Mgr cost (basis) | Adj. CF | Adj. multiple | "
       "All-cash yield | Out of pocket | Loan (rate) | Annual loan pmt | Left after loan | Risk | Status / flag | Source |")
SEP = "|" + "---|" * 16

def row(n, name, d, p, cf, m, basis, risk, status, src):
    adj, mult, oop, L, r, a, left, y = calc(p, cf, m)
    ms = f"{mult:.1f}x" if mult else "n/m"
    return (f"| {n} | {name} | {d} | {f(p)} | {f(cf)} | {f(m)} ({basis}) | {f(adj)} | {ms} | {y:.0f}% | "
            f"~{f(oop)} | {f(L)} ({r:.2f}%) | {f(a)} | {f(left)} | {risk} | {status} | {src} |")

# ---- 3. Verify top-30 numbers match top30_calc.py output exactly -----------
for n, ((name, d, p, cf, m, risk), line) in enumerate(zip(top30_rows, TOP30_LINES), 1):
    adj, mult, oop, L, r, a, left, y = calc(p, cf, m)
    expect = (f"| {n} | {name} ({d}) | {f(p)} | {f(cf)} | {f(adj)} | {p/adj:.1f}x | ~{f(oop)} | "
              f"{f(L)} ({r:.2f}%) | {f(a)} | {f(adj-a)} | {risk} |")
    assert line == expect, (line, expect)

# ---- 4. Rank the new pool --------------------------------------------------
ranked, below = [], []
for c in C:
    name, d, p, cf, m, basis, risk, ab, status, src = c
    adj, mult, *_ = calc(p, cf, m)
    if mult is None:
        below.append((float("inf"), c)); continue
    score = mult * W[risk] * (0.85 if ab else 1.0)
    ranked.append((score, c))
ranked.sort(key=lambda t: t[0])
top70, below_cut = ranked[:70], ranked[70:] + below

if __name__ == "__main__":
    print("## Positions 1-30 (fixed; verbatim top30_calc.py figures)\n")
    print(HDR); print(SEP)
    for n, (name, d, p, cf, m, risk) in enumerate(top30_rows, 1):
        status, flag, src = T30[n]
        nm = name + (f" - {flag}" if flag else "")
        basis = T30B[n]
        print(row(n, nm, d, p, cf, m, basis, risk, status, src))
    print("\n## Positions 31-100 (new; ranked by risk-weighted adjusted multiple)\n")
    print(HDR + " Score |")
    print(SEP + "---|")
    for n, (score, c) in enumerate(top70, 31):
        name, d, p, cf, m, basis, risk, ab, status, src = c
        if ab: name += " [A]"
        print(row(n, name, d, p, cf, m, basis, risk, status, src)[:-1] + f"| {score:.1f} |")
    print(f"\n## Qualified but below the cut ({len(below_cut)} rows)\n")
    print("| Business | Drive | Asking | Cash flow | Mgr cost | Adj. CF | Adj. multiple | All-cash yield | Risk | Status | Source |")
    print("|" + "---|" * 11)
    for score, c in below_cut:
        name, d, p, cf, m, basis, risk, ab, status, src = c
        adj, mult, *_r, y = calc(p, cf, m)
        ms = f"{mult:.1f}x" if mult else "n/m (CF <= mgr cost)"
        print(f"| {name} | {d} | {f(p)} | {f(cf)} | {f(m)} | {f(adj)} | {ms} | {y:.0f}% | {risk} | {status} | {src} |")
    print(f"\n<!-- pool={len(C)} ranked={len(ranked)} top70={len(top70)} below={len(below_cut)} -->")
