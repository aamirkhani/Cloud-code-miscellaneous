"""From-scratch re-ranking of businesses for sale near Dublin, CA (asking <= $2M)
for an absentee, very-low-risk, faith-screened buyer.

Every candidate row lives in this file with its source.  Nothing is carried over
by position from earlier lists; every row is re-scored with the same rules.
All money is in $K.  All listing figures are search-snippet figures (unverified).

Columns / formulas
  adjusted CF   = stated cash flow - manager/correction deduction
  adj multiple  = asking / adjusted CF
  all-cash yld  = adjusted CF / asking  (interest-free view; inventory excluded)
  out of pocket = 13% of asking (+ inventory or other extras where known)
  SBA loan      = 90% of asking, 10 yr, monthly amortisation, max variable rate:
                  loan <= $250K 12.75%; $250K-$350K 11.25%; > $350K 9.75%
  left after    = adjusted CF - annual loan payment
  DSCR          = adjusted CF / annual loan payment
  financeable   = 'no financing' / 'cash-only' from the listing, otherwise
                  'SBA-likely' when DSCR >= 1.25, else 'SBA-marginal'

Score (lower = better)
  adj multiple x risk weight x 0.85 if the listing itself states absentee /
  semi-absentee / manager in place x 1.15 if status is stale or figures conflict.
  Risk weights: Low 1.0, Low-Med 1.15, Medium 1.3, Med-High 1.6, High 2.0.
  Only rows with adjusted CF >= $40K are ranked; the rest go to the appendix.

Deduction rules (applied consistently)
  FedEx routes: $75K ops manager, or $15K oversight if manager in place
  Mission Foods routes: $55K driver per route + 5% of sales for truck/fuel/
    insurance/stales (sales imputed as cash flow / 18% where not disclosed,
    because these listings' 'cash flow' is the 17.5-18% gross commission).
    Vallejo uses the dedicated report's realistic planning figure ($135K).
  Pharmacies where the owner is PIC: $200K hired pharmacist-in-charge; inventory extra
  Laundromats: $40K attendant ($60K large attended); $15K oversight if absentee;
    $30K where the seller still works part-time ('partially absentee')
  Franchise store/branch managers: $75K.  Independent shop manager: $55K.
  Office manager $70K; service-company GM $80-90K; plant/mfg GM $100K;
  licensed contractor RME / licensed PI manager $120-150K; car-wash manager $60K.
  Listing states absentee / manager in place: $15K oversight.
"""
import itertools, statistics

RISK_W = {"Low": 1.0, "Low-Med": 1.15, "Medium": 1.3, "Med-High": 1.6, "High": 2.0}

def rate(loan_k):
    if loan_k <= 250: return 12.75
    if loan_k <= 350: return 11.25
    return 9.75

def pmt(L, r, n=10):
    i = r / 100 / 12; N = n * 12
    return L * i / (1 - (1 + i) ** -N) * 12

def f(v):
    if v is None: return "n/a"
    if abs(v) < 0.5: v = 0
    s = "-" if v < 0 else ""
    v = abs(v)
    return f"{s}${v:,.0f}K" if v < 999.5 else f"{s}${v/1000 + 1e-9:.2f}M"

def drive(m):
    return f"{m}m" if m < 60 else f"{m//60}h{m%60:02d}m"

# Source URL shorthands
BBS = "https://www.bizbuysell.com/california/"
BB = "https://www.bizben.com/business-for-sale/"
BQ = "https://www.bizquest.com/"
DS = "https://dealstream.com/california/"

# ---------------------------------------------------------------------------
# 1. CANDIDATE POOL: in radius (<= ~80 min off-peak), asking <= $2M, both an
#    asking price and a cash flow, not sold/pending, passes faith & licence
#    screens (or 'verify'), not an obvious data error.
# Fields: name, city, drive_min, ask, cf, ded, basis, category, risk,
#         absentee_stated, stale_or_conflict, financing, faith, status, source, extra
# ---------------------------------------------------------------------------
P = [
 # ---- FedEx routes ----
 ("FedEx Ground 13 vehicles, BC manager + team of 12 (Bay Advisors ZBB2305)", "Solano Co.", 45, 1400, 412.2, 15, "mgr in place", "FedEx routes", "Low", 1, 0, "SBA", "OK", "Current per Bay Advisors", "[Bay Advisors](https://thebayadvisors.com/profitable-fedex-routes-for-sale-san-francisco-bay-area/)", ""),
 ("FedEx linehaul 4 routes + 4 trucks, FT manager in place", "Stockton", 50, 1275, 422.844, 15, "mgr in place", "FedEx routes", "Low", 1, 0, "SBA", "OK", "Active? (cash price)", "[BusinessBroker.net Stockton](https://www.businessbroker.net/city/stockton-ca-businesses-for-sale.aspx)", ""),
 ("FedEx routes, SBA pre-qualified, newer fleet", "Contra Costa Co.", 25, 1125, 438.421, 75, "ops mgr", "FedEx routes", "Low", 0, 0, "SBA", "OK", "Unverified; broker marks many sold", "[Bay Advisors CC](https://thebayadvisors.com/fedex-routes-sba-pre-qualified-newer-fleet-sales-of-2-1m-contra-costa-country/)", ""),
 ("FedEx Ground 10 routes (BizBen 289956)", "San Leandro", 20, 1000, 360.189, 75, "ops mgr", "FedEx routes", "Low", 0, 0, "SBA", "OK", "Unverified", f"[BizBen 289956]({BB}fedex-ground-routes-for-sale-in-san-leandro-california-289956)", ""),
 ("FedEx Ground 13 routes (BizBen 289956)", "San Leandro", 20, 1600, 481.508, 75, "ops mgr", "FedEx routes", "Low", 0, 0, "SBA", "OK", "Unverified; same listing as 10-route", f"[BizBen 289956]({BB}fedex-ground-routes-for-sale-in-san-leandro-california-289956)", ""),
 ("FedEx Ground 8 routes (BizBen 287395)", "Fairfield", 45, 1175, 345.325, 75, "ops mgr", "FedEx routes", "Low", 0, 0, "SBA", "OK", "Unverified", f"[BizBen 287395]({BB}fedex-ground-routes-for-sale-in-fairfield-california-287395)", ""),
 ("FedEx route package", "Contra Costa Co.", 25, 1800, 473.472, 75, "ops mgr", "FedEx routes", "Low", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)", ""),
 ("FedEx Ground 8 routes", "Hayward", 15, 1100, 349.0, 75, "ops mgr", "FedEx routes", "Low", 0, 1, "SBA", "OK", "Same $1.1M/$349K pair also shown for Windsor", f"[BizBuySell routes]({BBS}san-francisco-bay-area/routes-for-sale/)", ""),
 ("FedEx Ground 13 routes ($1.1M + ~$175K vehicle fin.)", "San Jose", 30, 1275, 580.565, 75, "ops mgr", "FedEx routes", "Low-Med", 0, 1, "SBA", "OK", "Figures conflict; 2 older posts inactive", f"[BizBen 288357]({BB}fedex-ground-routes-for-sale-in-san-jose-california-288357)", ""),
 ("FedEx Ground 10 P&D routes", "San Jose", 30, 1035, 305.0, 75, "ops mgr", "FedEx routes", "Low", 0, 1, "SBA", "OK", "Not tied to a specific listing", f"[BizQuest SJ routes]({BQ}routes-for-sale-in-san-jose-ca/)", ""),
 ("FedEx Ground 9 routes", "Fairfield", 45, 1650, 397.526, 75, "ops mgr", "FedEx routes", "Low", 0, 1, "SBA", "OK", "Alt. $1.224M version without CF", f"[BizBuySell routes]({BBS}san-francisco-bay-area/routes-for-sale/)", ""),
 ("FedEx Ground 7 routes", "Fremont/Newark", 20, 925, 243.0, 75, "ops mgr", "FedEx routes", "Low", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell routes]({BBS}san-francisco-bay-area/routes-for-sale/)", ""),
 # ---- Pharmacies ----
 ("Retail pharmacy, Central Richmond, ~200 Rx/day (BFS 3906930)", "San Francisco", 55, 1525.65, 635.305, 200, "hired PIC", "Pharmacies", "Medium", 0, 1, "SBA", "Verify front store", "Appears active; CF conflict (text says ~$575K)", "[BusinessesForSale](https://us.businessesforsale.com/us/retail-pharmacy-in-san-francisco.aspx)", "+inventory at cost (unknown)"),
 ("Retail + non-sterile compounding pharmacy (BFS 3906867)", "San Ramon", 10, 1479.505, 595.65, 200, "hired PIC", "Pharmacies", "Medium", 0, 1, "SBA", "Verify front store", "Appears active; price conflict ($1.48M/$1.65M)", "[BusinessesForSale](https://us.businessesforsale.com/us/retail-compounding-pharmacy-east-bay-n-california.aspx)", "+inventory at cost (unknown)"),
 # ---- Laundromats ----
 ("Laundromat, low rent, lease to 2031 (owner-operated)", "Solano Co.", 45, 350, 145.923, 40, "attendant", "Laundromats", "Low-Med", 0, 0, "cash-only", "OK", "Unverified; cash-only sale", f"[BizBen Solano]({BB}solano-county-california-ca)", ""),
 ("Owner-absentee laundromat, busy plaza (BizBen 2134986)", "Santa Clara Co.", 35, 220, 94.139, 15, "absentee oversight", "Laundromats", "Medium", 1, 1, "cash-only", "OK", "Cash offer only; 'no financials'; rent ~41% of rev.", f"[BizBen 2134986]({BB}owner-absentee-laundromatbusy-area-with-parking-2134986)", ""),
 ("Absentee coin laundry, lease to 2029", "Martinez", 30, 671.632, 116.857, 15, "absentee oversight", "Laundromats", "Low-Med", 1, 1, "SBA", "OK", "Possibly stale (~333 days)", f"[BizBen CA laundromats]({BB}coin-laundry-laundromats-businesses-for-sale-type-california-ca)", ""),
 ("Absentee-run coin laundry (BizBuySell 2488231)", "Oakland", 30, 449.9, 83.447, 15, "absentee oversight", "Laundromats", "Low-Med", 1, 0, "SBA", "OK", "Presumed active; owner retiring", "[BizBuySell 2488231](https://www.bizbuysell.com/business-opportunity/simple-coin-laundry-as-absentee-owner-s-run-for-sale-in-oakland/2488231/)", ""),
 ("Absentee coin laundry #2", "Oakland", 30, 563, 92.366, 15, "absentee oversight", "Laundromats", "Low-Med", 1, 1, "SBA", "OK", "No listing ID; pairing unverified", f"[BizBuySell Oakland]({BBS}oakland/laundromats-and-coin-laundry-businesses-for-sale/)", ""),
 ("Partially absentee coin laundry (BizBen 2810644)", "Sacramento", 80, 350, 70.284, 30, "partial absentee", "Laundromats", "Low-Med", 1, 1, "SBA", "OK", "Also seen at $400K (same numbers)", f"[BizBen 2810644]({BB}coin-laundry-as-absentee-owners-run-for-sale-in-sacramento-2810644)", ""),
 ("Laundromat, 100+ Speed Queen machines", "Modesto", 60, 1700, 268, 60, "attended mgr", "Laundromats", "Low-Med", 0, 1, "SBA", "OK", "Listing page not found on re-search", f"[BizBuySell Modesto]({BBS}modesto-merced-area-businesses-for-sale/)", ""),
 ("Laundromat, high traffic (seller 'net')", "Modesto", 60, 650, 108, 40, "attendant", "Laundromats", "Low-Med", 0, 1, "SBA", "OK", "Active? seller 'net' figure", f"[BizBen 277572]({BB}laundromat-for-sale-in-modesto-california-277572.php)", ""),
 # ---- Car washes ----
 ("Full-service hand car wash, 'oldest in Fairfield', leased", "Fairfield", 45, 275, 141.201, 60, "site mgr", "Car washes", "Med-High", 0, 0, "cash-only", "OK", "$275K 'cash only' (was $300K)", "[BizQuest Fairfield](https://images.bizquest.com/car-washes-for-sale-in-fairfield-ca)", "report range $40-75K net"),
 ("Full-service car wash, semi-absentee, remodeled (ID 2089342)", "Fairfield", 45, 799, 225, 90, "mgr $60K + rent step-up $30K", "Car washes", "Med-High", 1, 1, "SBA", "OK", "Rent/acreage conflict; assumable $500K EIDL", "[LoopNet 2089342](https://www.loopnet.com/biz/Business-Opportunity/full-service-car-wash-for-sale-in-fairfield-california/2089342/)", "SBA 30% down or EIDL assumption"),
 # ---- Boba ----
 ("Absentee-operated boba tea shop ($592K sales)", "Cupertino", 40, 400, 256.38, 158.38, "P&L-model haircut to ~$98K", "Boba", "Medium", 1, 0, "SBA", "Verify toppings", "Unverified; 43% margin not credible", f"[DealStream SCC absentee]({DS}santa-clara-county/absentee-owned-businesses-for-sale)", ""),
 ("Boba/tea shop, new lease (~$453K sales)", "San Jose", 30, 450, 120, 55, "shop mgr", "Boba", "Medium", 0, 0, "SBA", "Verify toppings", "Unverified; new lease needed", f"[BizBen San Jose]({BB}san-jose-city-california-ca-businesses-for-sale)", ""),
 # ---- Other routes ----
 ("Mission Foods 4-route master distributorship, 45 accts", "Vallejo", 40, 619, 451.386, 316.386, "4 drivers + truck/fuel/stales (report planning fig.)", "Routes (Mission/vending)", "Medium", 0, 0, "no financing", "OK", "Active 'Hot Listing'; old ID", "[BizQuest BW2368281](https://www.bizquest.com/business-for-sale/mission-foods-master-distributorship-for-sale-vallejo-ca-619-000/BW2368281)", "+2 trucks & 4 inventory deposits"),
 ("Mission Foods multi-route, 8 accts, $1.20M sales", "Napa", 50, 300, 210.246, 170.07, "2 drivers $110K + 5% of $1.20M sales", "Routes (Mission/vending)", "Medium", 0, 0, "no financing", "OK", "Unverified", "[BizQuest BW2530493](https://www.bizquest.com/business-for-sale/mission-foods-multi-route-distributorship-for-sale-napa-ca/BW2530493/)", "+truck & deposits"),
 ("Vending, 10 warranted machines", "San Jose", 30, 130, 86.4, 25, "PT restocker", "Routes (Mission/vending)", "Med-High", 0, 1, "SBA", "OK", "CF per machine looks high", f"[DealStream SCC]({DS}santa-clara-county-businesses-for-sale)", ""),
 # ---- Franchises ----
 ("The UPS Stores, Marin/Sonoma multi-center seller (bundle snippet)", "Marin/Sonoma", 60, 630, 196.066, 75, "franchise mgr", "Franchises", "Low-Med", 0, 1, "SBA", "OK", "Price/CF pairing uncertain", f"[BizBuySell UPS]({BBS}ups-stores-for-sale/)", ""),
 ("Express Employment staffing franchise", "South San Francisco", 45, 425, 319.27, 75, "franchise branch mgr", "Franchises", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)", ""),
 ("Auto service franchise, manager + team in place", "South Bay", 35, 145, 105.02, 15, "mgr in place", "Franchises", "Med-High", 1, 0, "SBA", "OK", "Unverified", f"[DealStream SCC auto]({DS}santa-clara-county/auto-repair-businesses-for-sale)", ""),
 ("Tanning franchise, 4 locations, 'absentee ownership'", "Santa Rosa", 75, 1795, 528.745, 15, "absentee oversight", "Franchises", "Med-High", 1, 1, "SBA", "OK", "CF not clearly tied to listing", f"[BizQuest SR absentee]({BQ}absentee-businesses-for-sale-in-santa-rosa-ca)", ""),
 ("Gutter services franchise, semi-absentee, est. 2024 (FCBB 234-25087)", "Alameda Co.", 20, 400, 162.89, 30, "partial absentee", "Franchises", "Med-High", 1, 0, "SBA", "OK", "Presumed active; $60K down; verify CSLB qualifier", "[FCBB 234-25087](https://sfbay.fcbb.com/listing-property/construction-alameda-county-ca-high-growth-gutter-services-franchise-1.35m-revenue-absentee-friendly-234-25087)", ""),
 ("Non-medical home care franchise", "Alameda Co.", 20, 888.888, 318.035, 75, "franchise office mgr", "Franchises", "Medium", 0, 0, "SBA", "OK", "Presumed active; gov't payers", f"[BizBuySell assisted living]({BBS}san-francisco-bay-area/assisted-living-and-nursing-homes-for-sale/)", ""),
 ("Large-format sign & print franchise", "South Napa Co.", 45, 775, 228.882, 75, "franchise mgr", "Franchises", "Low-Med", 0, 0, "SBA", "OK", "Unverified", f"[DealStream Napa]({DS}napa/small-businesses-for-sale)", ""),
 ("Juice bar franchise, 'absentee-owned'", "Modesto", 60, 349, 70.489, 15, "absentee oversight", "Franchises", "Medium", 1, 0, "SBA", "OK", "Active?", f"[BizBuySell Modesto]({BBS}modesto-merced-area-businesses-for-sale/)", ""),
 ("ServiceMaster franchise group (~$830K rev.)", "Santa Cruz Co.", 70, 1200, 245, 75, "franchise GM", "Franchises", "Medium", 0, 0, "SBA", "OK", "Active?", f"[BizBen Santa Cruz]({BB}santa-cruz-county-california-ca)", ""),
 # ---- Services ----
 ("Multi-location tutoring", "Milpitas", 25, 450, 222, 70, "center director", "Services", "Medium", 0, 1, "SBA", "OK", "Price $450K/$500K pairing uncertain", f"[BizBuySell Milpitas]({BBS}milpitas-businesses-for-sale/)", ""),
 ("Door-to-door airport shuttle", "San Rafael", 50, 202.002, 125.022, 60, "driver-mgr", "Services", "Med-High", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)", ""),
 ("Hair salon & beauty school", "Marin Co.", 55, 649, 352.715, 120, "salon/school mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)", ""),
 ("Towing & repair ($911K rev.)", "San Mateo Co.", 35, 720, 233, 85, "ops mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)", ""),
 ("Soil testing laboratory", "Central Coast", 70, 1200, 385.484, 120, "lab mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizQuest Santa Cruz]({BQ}mid-market-businesses-for-sale-in-santa-cruz-county-ca/)", ""),
 ("Window screen install & repair (est. 1989)", "Santa Rosa", 75, 525, 191.5, 70, "ops mgr", "Services", "Medium", 0, 1, "SBA", "OK", "Price reduced; alt. SDE $235K", "[BizBuySell 2297146](https://www.bizbuysell.com/business-opportunity/window-screen-installation-and-repair-price-reduced/2297146/)", ""),
 ("Printing shop", "South Bay", 35, 495, 191.216, 80, "service GM", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[DealStream SCC]({DS}santa-clara-county-businesses-for-sale)", ""),
 ("Landscaping company, 30-yr reputation", "Alameda Co.", 20, 700, 220, 90, "service GM", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified; verify C-27 need", f"[BizBuySell Alameda]({BBS}alameda-county-businesses-for-sale/)", ""),
 ("Commercial cleaning / janitorial", "Santa Clara Co.", 35, 700, 200, 80, "service GM", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell cleaning]({BBS}san-francisco-bay-area/cleaning-businesses-for-sale/)", ""),
 ("Marketing / print services ($950K rev.)", "Sacramento", 80, 765, 250, 90, "service GM", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Sacramento]({BBS}sacramento-businesses-for-sale/)", ""),
 ("Spa (50% seller financing offered)", "Novato", 55, 495, 150, 70, "shop mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified; seller finance", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)", ""),
 ("HOA cleaning company", "Santa Clara Co.?", 35, 675, 190, 80, "service GM", "Services", "Medium", 0, 1, "SBA", "OK", "Location uncertain", f"[BizBuySell CA cleaning]({BBS}cleaning-businesses-for-sale/)", ""),
 ("Children's play & party center", "San Mateo", 40, 1200, 273, 70, "shop mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)", ""),
 ("Moving & storage ($2.49M rev.)", "Santa Rosa", 75, 842.388, 210.597, 80, "ops mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified; 8% margin", f"[BizBuySell Santa Rosa]({BBS}santa-rosa-businesses-for-sale/)", ""),
 ("Large preschool, SBA eligible (BW2439415)", "Milpitas", 25, 750, 173, 70, "director", "Services", "Medium", 0, 1, "SBA", "OK", "Alt. price $520K in same snippet", f"[BizQuest BW2439415]({BQ}business-for-sale/preschool-business-for-sale-milpitas/BW2439415)", ""),
 ("Locksmith", "Vallejo", 40, 200, 135, 80, "licensed tech-mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)", ""),
 ("Day spa", "San Francisco", 45, 200, 119.111, 70, "spa mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell services]({BBS}san-francisco-bay-area/service-businesses-for-sale/)", ""),
 ("Landscape company", "Solano Co.", 45, 550, 161, 90, "service GM", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizQuest Solano]({BQ}landscaping-services-businesses-for-sale-in-solano-county-ca)", ""),
 ("Background investigation co. (licensed PI)", "Novato", 55, 599, 175, 120, "licensed PI mgr", "Services", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)", ""),
 ("Tuxedo rental", "Santa Clara Co.", 35, 620, 182.434, 70, "shop mgr", "Services", "Med-High", 0, 1, "SBA", "OK", "Figures conflict (alt $645K/$168.6K)", f"[DealStream SCC]({DS}santa-clara-county-businesses-for-sale)", ""),
 ("Auto body shop", "San Francisco", 45, 275, 126.368, 80, "shop mgr", "Services", "Med-High", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)", ""),
 ("Tax & bookkeeping practice (verify not CPA)", "Lodi", 60, 410, 137, 90, "EA/CTEC mgr", "Services", "Med-High", 0, 0, "SBA", "OK", "Verify not a CPA firm", f"[BizBuySell accounting p2]({BBS}accounting-businesses-and-tax-practices-for-sale/2/)", ""),
 # ---- Contractors ----
 ("Residential plumbing, SBA pre-qualified", "Santa Clara Co.", 35, 697, 423, 140, "licensed RME", "Contractors", "Medium", 0, 1, "SBA", "OK", "Price conflict ($697K/$797K)", f"[BizBuySell plumbing]({BBS}plumbing-businesses-for-sale/)", ""),
 ("Plumbing contractor", "Marin Co.", 55, 547, 310, 140, "licensed RME", "Contractors", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)", ""),
 ("Concrete polishing & waterproofing ($2.41M rev.)", "Sacramento", 80, 849, 316.39, 120, "licensed RME", "Contractors", "Medium", 0, 0, "SBA", "OK", "Unverified", f"[BizBuySell Sac Co.]({BBS}sacramento-county-businesses-for-sale/)", ""),
 ("Commercial electrical contractor ($3.63M rev.)", "Sonoma Co.", 75, 1290, 400, 150, "licensed RME", "Contractors", "Medium", 0, 1, "SBA", "OK", "Alt. listing $1.375M/$423.7K", f"[BizBuySell Sonoma]({BBS}sonoma-county-businesses-for-sale/)", ""),
 ("HVAC company (since 2015)", "Bay Area (county ND)", 35, 1000, 350, 140, "licensed RME", "Contractors", "Medium", 0, 1, "SBA", "OK", "County unknown", f"[BizBuySell HVAC]({BBS}san-francisco-bay-area/hvac-businesses-for-sale/)", ""),
 ("HVAC & refrigeration, SBA eligible", "Sacramento Co.", 80, 500, 184.098, 120, "licensed RME", "Contractors", "Medium", 0, 0, "SBA", "OK", "Active?", f"[BizBuySell Sac HVAC]({BBS}sacramento-county/hvac-businesses-for-sale/)", ""),
 # ---- Manufacturing / distribution ----
 ("Precision CNC fabricator, GM in place, $1.1M backlog", "SF metro", 45, 1000, 247.6, 15, "GM in place", "Manufacturing/distribution", "Medium", 1, 0, "SBA", "OK", "Unverified", "[Rejigg SF](https://www.rejigg.com/for-sale/california/san-francisco)", ""),
 ("Cabinet-finishing manufacturer, 'absentee, SBA-ready'", "Contra Costa Co.", 25, 1150, 241.501, 15, "absentee oversight", "Manufacturing/distribution", "Medium", 1, 0, "SBA", "OK", "Unverified", "[BizBuySell CC mfg](https://m.bizbuysell.com/california/contra-costa-county/manufacturing-businesses-for-sale)", ""),
 ("OEM wiring-harness manufacturer", "Santa Cruz", 70, 1100, 365.697, 100, "mfg GM", "Manufacturing/distribution", "Medium", 0, 0, "SBA", "OK", "Active?", f"[BizBuySell SC mfg]({BBS}santa-cruz/manufacturing-businesses-for-sale/)", ""),
 ("Grocery food manufacturer, proprietary brands", "San Francisco", 45, 695, 262, 100, "plant mgr", "Manufacturing/distribution", "Medium", 0, 0, "SBA", "Verify products", "Unverified", f"[BizBuySell mfg]({BBS}san-francisco-bay-area/manufacturing-businesses-for-sale/)", ""),
 ("Wholesale / distribution", "Stockton", 50, 300, 180, 70, "ops mgr", "Manufacturing/distribution", "Med-High", 0, 0, "SBA", "Verify products", "Unverified", f"[BizQuest Stockton]({BQ}wholesale-and-distribution-businesses-for-sale-in-stockton-ca/)", ""),
 ("Firewood & lumber, real estate included", "Watsonville", 75, 600, 174.785, 70, "yard mgr", "Manufacturing/distribution", "Medium", 0, 0, "SBA", "OK", "Active?", f"[BizBuySell Santa Cruz]({BBS}santa-cruz-county-businesses-for-sale/)", ""),
 # ---- Retail ----
 ("Flooring retailer ($822K rev.)", "San Jose", 30, 251.999, 139.804, 70, "store mgr", "Retail", "Medium", 0, 1, "SBA", "OK", "May be stale", "[BusinessBroker.net SJ](https://www.businessbroker.net/city/san-jose-ca-businesses-for-sale.aspx)", ""),
 ("Bicycle retail & repair", "Hollister", 75, 349.9, 119.97, 55, "shop mgr", "Retail", "Med-High", 0, 0, "SBA", "OK", "Active?", f"[BizBuySell San Benito]({BBS}san-benito-county-businesses-for-sale/)", ""),
 # ---- Food service (alcohol / pork status must be verified) ----
 ("Corporate catering & meal prep, manager-operated", "San Francisco", 45, 325, 155.398, 15, "mgr in place", "Food service", "Medium", 1, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell SF Co.]({BBS}san-francisco-county-businesses-for-sale/)", ""),
 ("Taiwanese bento / fried chicken, absentee-run", "Pleasanton", 10, 185, 75.268, 15, "absentee oversight", "Food service", "High", 1, 1, "SBA", "Verify pork/alcohol", "Stale (posted Jun 2025)", f"[BizBen Pleasanton]({BB}pleasanton-alameda-county-cafe-restaurant-for-sale-260855.php)", ""),
 ("Teriyaki restaurant, 15+ yrs", "Sacramento", 80, 999.999, 393.299, 70, "restaurant mgr", "Food service", "High", 0, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell Sacramento]({BBS}sacramento-established-businesses-for-sale/2/)", ""),
 ("Turnkey restaurant", "San Francisco", 45, 1350, 444.68, 100, "restaurant mgr", "Food service", "High", 0, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell SF restaurants]({BBS}san-francisco/restaurants-and-food-businesses-for-sale/)", ""),
 ("Restaurant", "Petaluma", 60, 350, 150, 70, "restaurant mgr", "Food service", "High", 0, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell Petaluma]({BBS}petaluma-businesses-for-sale/)", ""),
 ("Mexican restaurant, prime shopping center", "Modesto", 60, 1075, 306, 70, "restaurant mgr", "Food service", "High", 0, 0, "SBA", "Verify pork/alcohol", "Unverified", f"[BizBuySell Modesto]({BBS}modesto-businesses-for-sale/)", ""),
 ("Indian restaurant", "San Jose", 30, 850, 245, 70, "restaurant mgr", "Food service", "High", 0, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)", ""),
 ("Catering business", "San Francisco", 45, 449, 155, 70, "kitchen mgr", "Food service", "High", 0, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell SF services]({BBS}san-francisco/service-businesses-for-sale/)", ""),
 ("Downtown restaurant", "Vacaville", 50, 510, 125, 70, "restaurant mgr", "Food service", "High", 0, 0, "SBA", "Verify alcohol", "Unverified", f"[BizBuySell Solano food]({BBS}solano-county/restaurants-and-food-businesses-for-sale/)", ""),
]

# Rows that are in radius, priced and pass the screens but cannot cover the
# deduction to >= $40K adjusted CF (computed, then sent to the appendix).
LOW = [
 ("Mission Foods single route (sales imputed)", "Napa", 50, 90, 83.697, 55 + 0.05 * 83.697 / 0.18, "driver + 5% imputed sales", "Routes (Mission/vending)", f"[BizQuest Napa](https://images.bizquest.com/business-for-sale/mission-foods-route-for-sale-napa-ca-90-000/BW2435645)"),
 ("Mission Foods single route (sales imputed)", "Sonoma", 65, 129, 95.346, 55 + 0.05 * 95.346 / 0.18, "driver + 5% imputed sales", "Routes (Mission/vending)", f"[BizBuySell Sonoma]({BBS}sonoma-county-businesses-for-sale/)"),
 ("Mission Foods route, reduced (sales imputed)", "San Jose", 30, 179, 125.77, 55 + 0.05 * 125.77 / 0.18, "driver + 5% imputed sales", "Routes (Mission/vending)", f"[BizBuySell SJ distribution]({BBS}san-jose/wholesale-and-distribution-businesses-for-sale/)"),
 ("Snack food route to independent grocers", "San Joaquin Co.", 50, 230, 77.524, 55, "route driver", "Routes (Mission/vending)", f"[BizBuySell distribution p3]({BBS}wholesale-and-distribution-businesses-for-sale/3/)"),
 ("Turnkey vending business", "Alameda Co.", 20, 52, 28.26, 20, "PT restocker", "Routes (Mission/vending)", f"[BizQuest vending]({BQ}vending-machines-and-routes-businesses-for-sale-in-alameda-county-ca)"),
 ("Absentee franchise boba shop (BW2447990), claimed $350K/$180K", "San Mateo", 40, 350, 180, 156, "P&L model: ~$24K at $600K sales (manager paid)", "Boba", "[BizQuest BW2447990](https://www.bizquest.com/business-for-sale/absentee-run-franchise-boba-tea-shop-for-sale-in-downtown-san-mateo/BW2447990)"),
 ("Gong Cha franchise (since 2023)", "San Jose", 30, 298, 90, 75, "franchise mgr", "Boba", f"[BizBuySell cafes p2]({BBS}coffee-shops-and-cafes-for-sale/2/)"),
 ("Mail center franchise, NorCal (SC2186), city confidential", "Napa? (confidential)", 50, 200, 108, 75, "franchise mgr", "Franchises", "[BizQuest SC2186](https://www.bizquest.com/business-for-sale/recession-resistant-mail-center-franchise-in-norcal-sc2186/BW2253936)"),
 ("Silicon Valley mail center franchise (SC2248)", "Silicon Valley", 35, 174.9, 20, 75, "franchise mgr", "Franchises", f"[BizQuest SC2248]({BQ}business-for-sale/recession-resistant-silicon-valley-mail-center-franchise-sc2248/BW2441517)"),
 ("Franchise bakery", "Concord", 25, 190, 74, 75, "franchise mgr", "Franchises", "[BizBuySell CC bakeries](https://m.bizbuysell.com/california/contra-costa-county/bakeries-for-sale/)"),
 ("Juice bar franchise", "Napa Co.", 50, 299, 93.666, 75, "franchise mgr", "Franchises", f"[BizBuySell Napa]({BBS}napa-county-businesses-for-sale/)"),
 ("True REST float spa franchise", "Napa", 50, 135, 75.113, 75, "franchise mgr", "Franchises", f"[BizBuySell Napa]({BBS}napa-county-businesses-for-sale/)"),
 ("Junk-hauling franchise (alt CF $101.8K)", "Petaluma", 60, 265, 70, 75, "franchise mgr", "Franchises", f"[BizBuySell waste]({BBS}waste-management-and-recycling-businesses-for-sale/)"),
 ("Home-care franchise (non-medical)", "Marin Co.", 55, 375, 95, 75, "franchise mgr", "Franchises", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Staffing agency", "San Rafael", 50, 215, 96, 70, "office mgr", "Services", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Bookkeeping practice", "San Rafael", 50, 240, 104, 70, "office mgr", "Services", f"[BizBuySell accounting]({BBS}san-francisco-bay-area/accounting-businesses-and-tax-practices-for-sale/)"),
 ("Preschool, Crow Canyon corridor", "San Ramon", 10, 299, 90, 70, "director", "Services", f"[BizBuySell education]({BBS}san-francisco-bay-area/education-and-child-related-businesses-for-sale/)"),
 ("Print shop ($144K rev.)", "Berkeley", 35, 250, 90, 55, "shop mgr", "Services", f"[BizBen print]({BB}printing-businesses-for-sale-type-california-ca)"),
 ("Service business (type not shown)", "San Francisco", 45, 229, 85, 70, "mgr", "Services", f"[BizBuySell SF services]({BBS}san-francisco/service-businesses-for-sale/)"),
 ("Freight forwarder / NVOCC (4% margin)", "San Mateo Co.", 45, 150, 81.557, 70, "ops mgr", "Services", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 ("Trucking co., dedicated routes", "Stockton", 50, 190, 95, 70, "dispatcher-mgr", "Services", f"[BizQuest San Joaquin]({BQ}businesses-for-sale-in-san-joaquin-county-ca/)"),
 ("Dry cleaner", "Redwood City", 45, 120, 75.34, 55, "shop mgr", "Services", f"[BizBuySell dry cleaners]({BBS}san-francisco-bay-area/dry-cleaners-for-sale/)"),
 ("Dry cleaners", "San Rafael", 50, 249, 10, 55, "shop mgr", "Services", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Auto repair (40+ yrs)", "Fremont", 20, 150, 93.971, 80, "shop mgr", "Services", f"[BizBuySell Alameda auto]({BBS}alameda-county/auto-repair-and-service-shops-for-sale/)"),
 ("Auto repair shop", "Fremont", 20, 175, 110, 80, "shop mgr", "Services", f"[BizBuySell Alameda auto]({BBS}alameda-county/auto-repair-and-service-shops-for-sale/)"),
 ("Auto repair franchise resale (dated 10/2023)", "Alameda Co.", 20, 200, 76, 80, "shop mgr", "Services", f"[BizBuySell Alameda auto]({BBS}alameda-county/auto-repair-and-service-shops-for-sale/)"),
 ("Paving contractor", "Marin Co.", 55, 495, 150, 120, "licensed RME", "Contractors", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Child safety pool fence co. (70% margin)", "Sacramento", 80, 274.5, 140, 120, "licensed RME", "Contractors", f"[BizBuySell Sacramento]({BBS}sacramento-established-businesses-for-sale/2/)"),
 ("HVAC service, 200+ maintenance accts", "Sacramento Co.", 80, 250, 124.396, 120, "licensed RME", "Contractors", f"[BizBuySell Sac HVAC]({BBS}sacramento-county/hvac-businesses-for-sale/)"),
 ("HVAC + real estate, pitched to a technician", "Concord", 25, 1024, 132.973, 120, "licensed RME", "Contractors", f"[BizBuySell HVAC]({BBS}hvac-businesses-for-sale/)"),
 ("HVAC, home-based", "Contra Costa Co.", 25, 195, 105.622, 120, "licensed RME", "Contractors", f"[BizBuySell HVAC]({BBS}hvac-businesses-for-sale/)"),
 ("Salsa manufacturer / wholesaler", "Watsonville", 75, 98, 51.762, 55, "shop mgr", "Manufacturing/distribution", f"[BizQuest Watsonville]({BQ}businesses-for-sale-in-watsonville-ca)"),
 ("Simple coin/card laundry, just listed", "Pinole", 40, 320, 66, 40, "attendant", "Laundromats", f"[BizBen 4435250]({BB}simple-coincard-laundry-for-sale-in-pinole-contra-costa-county-ca-4435250)"),
 ("Owner-absentee laundromat (pairing uncertain)", "Solano Co.", 45, 490, 37.728, 15, "absentee oversight", "Laundromats", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)"),
 ("Absentee-run coin laundry (posted 3/2025)", "San Jose", 30, 160, 31.662, 15, "absentee oversight", "Laundromats", f"[BizBen SJ]({BB}laundromat-for-sale-in-san-jose-california-290105.php)"),
 ("Well-managed coin laundry (Apr 2025)", "Alameda Co.", 25, 159.95, 34.536, 40, "attendant", "Laundromats", f"[BizBen 283018]({BB}coin-laundry-for-sale-in-alameda-county-california-283018.php)"),
 ("Coin laundry, 'long lease' (58x stated CF)", "Vacaville", 50, 725, 12.6, 40, "attendant", "Laundromats", f"[BizBuySell Solano laundromats]({BBS}solano-county/laundromats-and-coin-laundry-businesses-for-sale/)"),
 ("Retail pharmacy, owner-PIC (lease expiring)", "Rancho Cordova area", 75, 275.8, 205.6, 200, "hired PIC", "Pharmacies", "[BusinessesForSale](https://us.businessesforsale.com/us/well-established-retail-pharmacy-in-sacramento.aspx)"),
 ("Retail pharmacy est. 2022 (pairing unverified)", "Sacramento Co.", 80, 199.9, 70.022, 200, "hired PIC", "Pharmacies", f"[BizBuySell Sac Co.]({BBS}sacramento-county/pharmacies-for-sale/)"),
 ("Retail pharmacy est. 2017 ($100 CF)", "Rancho Cordova area", 75, 135, 0.1, 200, "hired PIC", "Pharmacies", "[BFS search](https://us.businessesforsale.com/us/search/drug-stores-and-pharmacies-for-sale-in-california)"),
]

# Sold / pending / in contract: backup-offer candidates (numbers computed)
BACKUP = [
 ("The UPS Store (BizBuySell 2393051), $585K rev.", "Newark", 20, 849, 262.363, 75, "Low-Med", "**Sale Pending**", "[BizBuySell 2393051](https://www.bizbuysell.com/business-opportunity/the-ups-store-franchise-in-alameda-county-ca/2393051/)"),
 ("The UPS Store (BizBuySell 2393047), $760K rev.", "Napa Co.", 50, 699, 222.102, 75, "Low-Med", "**Pending** on Franchise Clearly", "[Franchise Clearly 25710](https://members.franchiseclearly.com/seller/recast/summary/25710/public)"),
 ("IT services / MSP ($735K rev.)", "Alameda Co.", 15, 735, 253.652, 120, "Medium", "**Offer pending**", f"[BizBuySell IT]({BBS}san-francisco-bay-area/it-and-software-service-businesses-for-sale/)"),
 ("Mission Foods route, 7 accts (RoutesRUs 70548)", "Santa Rosa", 75, 179, 123.469, 55 + 0.05 * 123.469 / 0.18, "Medium", "**Sale Pending** (BW2400815)", f"[BizQuest BW2400815]({BQ}business-for-sale/mission-foods-route-for-sale-santa-rosa-ca-179-000-sale-pending/BW2400815)"),
 ("Mission Foods single route", "Vacaville", 50, 105, 97.852, 55 + 0.05 * 97.852 / 0.175, "Medium", "**Sale Pending**", "[BizQuest BW2476487](https://www.bizquest.com/business-for-sale/mission-foods-route-for-sale-vacaville-ca-105-000-sale-pending/BW2476487)"),
 ("Simple coin laundry in shopping center (BizBen 4453837)", "Oakland", 30, 160, 38.294, 40, "Low-Med", "**In Contract**", f"[BizBen 4453837]({BB}simple-coin-laundry-in-shopping-center-in-oakland-4453837)"),
 ("High-volume laundromat (BizBen 271664)", "W. Contra Costa", 40, 460, 89.495, 40, "Low-Med", "**In escrow** (2023)", f"[BizBen 271664]({BB}well-established-high-volume-laundromat-for-sale-in-contra-costa-california-271664.php)"),
]
BACKUP_NOFIN = [
 ("Simple coin laundry, $470K", "Hayward", "In contract; CF ND", f"[BizBen CA laundromats]({BB}coin-laundry-laundromats-businesses-for-sale-type-california-ca)"),
 ("Downtown SF pharmacy, $250K on ~$140K sales", "San Francisco", "Under contract; CF ND", "[BizQuest BW2489527](https://www.bizquest.com/business-for-sale/san-francisco-downtown-pharmacy-for-sale/BW2489527/)"),
 ("Bay Advisors FedEx SF Bay Area, $1.1M / $404.7K", "Bay Area", "SOLD (comp: 2.72x)", "[Bay Advisors](https://thebayadvisors.com/profitable-fedex-routes-for-sale-san-francisco-bay-area/)"),
 ("Bay Advisors FedEx '100% absentee' ZBB2197", "Alameda Co.", "SOLD", "[Bay Advisors](https://thebayadvisors.com/fedex-routes-for-sale-100-absentee-run-newer-fleet/)"),
 ("FedEx 17 vehicles, $950K / $182.6K", "Alameda Co.", "SOLD", "[BizBen 259389](https://bizben.com/business-for-sale/san-francisco-bay-area-fedex-route-for-sale-259389)"),
 ("FedEx Santa Clara Co., $1.75M / $454.3K", "Santa Clara Co.", "SOLD", "[Bay Advisors SCC](https://thebayadvisors.com/profitable-fedex-routes-for-sale-santa-clara-county-sba-pre-qualified-current-listing/)"),
 ("Rockridge laundromat $750-850K; San Mateo card laundromat $1M/~$200K; Signal Corner $250K/~$60K; SJ $725K/$18.4K", "Oakland / San Mateo / San Jose", "Escrow, inactive or off market", f"[BizBen 231018]({BB}coin-laundry-for-sale-san-mateo-california-231018.php)"),
 ("Hayward smog station $78K / $42K; Marin tax practice $310K", "Hayward / Marin", "Off market / pending", f"[BizBen Hayward]({BB}hayward-auto-repair-shop-for-sale-193806.php)"),
]

# Faith-screen failures (alcohol, tobacco/vape, lottery, gambling, cannabis, pork-heavy)
FAITH = [
 ("Liquor & market, Pacific Heights", "San Francisco", "$420K / $185K", "Alcohol", f"[BizBuySell retail]({BBS}san-francisco-bay-area/retail-businesses-for-sale/)"),
 ("Gas station + land + house, beer & wine", "Stockton", "$450K / $172K", "Alcohol (and c-store)", f"[BizBuySell San Joaquin]({BBS}san-joaquin-county-businesses-for-sale/)"),
 ("Turnkey restaurant, ABC Type 47", "Watsonville", "$197K / $154.5K", "Full liquor licence", f"[BizBuySell Santa Cruz]({BBS}santa-cruz-county-businesses-for-sale/)"),
 ("Liquor store", "Livermore", "$585K / $305K", "Alcohol", "[BizQuest Livermore](https://www.bizquest.com/liquor-stores-for-sale-in-livermore-ca)"),
 ("Mediterranean restaurant, Type 47", "Oakland", "$345K / $175K", "Liquor licence", f"[BizBuySell Alameda]({BBS}alameda-county-businesses-for-sale/)"),
 ("Restaurant & bar (S. Marin); San Rafael event catering", "Marin", "$249K/$124K; $135K/$55K", "Bar / event alcohol", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("Pizza restaurant; takeout pizza 'absentee'; pizzeria", "SF; Concord; San Mateo Co.", "$350K/$280K; $149K/$83.5K; $199K/$65.9K", "Pork-heavy menu (pepperoni/sausage/ham), like Subway; reinstate only if halal", f"[BizBuySell SF restaurants]({BBS}san-francisco/restaurants-and-food-businesses-for-sale/)"),
 ("Subway franchise", "Fairfield", "$275K / $98.4K", "Pork-heavy menu", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)"),
 ("Korean restaurant (absentee); BBQ-chicken franchise (absentee)", "Santa Clara Co.", "$350K/$160K; $1.05M/$325K", "Soju/beer typical; reinstate if no licence", f"[BizBen 287666]({BB}korean-restaurant-for-sale-in-santa-clara-county-california-287666.php)"),
 ("SF grocery market", "San Francisco", "$694K / $105K EBITDA", "Beer/wine & lottery likely", f"[BizBuySell health page]({BBS}san-francisco-bay-area/health-care-and-fitness-businesses-for-sale/)"),
 ("Smoke shop + mini-market; Lodi & Ceres liquor; Turlock c-store; Turlock Italian (ABC); Santa Cruz wine bar", "Central Valley / Santa Cruz", "e.g. $850K/$319K; $115K/$96.6K; $725K/$299K", "Tobacco, alcohol", f"[BizBuySell Modesto-Merced]({BBS}modesto-merced-area-businesses-for-sale/)"),
 ("Owner-absentee laundromat", "Modesto", "$275K / ND", "Income includes gaming machines", "[SellingRestaurants](https://sellingrestaurants.com/restaurant-for-sale/coin-laundry-business-for-sale-modesto-ca)"),
 ("Cannabis trucking", "Santa Cruz Co.", "$695K / $245K", "Cannabis", f"[BizBuySell Santa Cruz]({BBS}santa-cruz-county-businesses-for-sale/)"),
 ("Carnitas; ramen; tamale maker", "Hollister; Elk Grove; Sacramento", "$160K/$140K; $160K/~$140K; $199-270K/$119K", "Pork-focused", f"[BizBuySell Hollister]({BBS}hollister/restaurants-and-food-businesses-for-sale/)"),
 ("Liquor store + pharmacy, semi-absentee (inactive 2023)", "San Francisco", "$450-650K / ~$182K", "Alcohol", f"[BizBen 273164]({BB}liquor-store-pharmacy-for-sale-in-san-francisco-county-california-273164.php)"),
]

# Licensed-owner professions
LICENSED = [
 ("Internal medicine practice", "Oakland", "$264K / $117K", f"[BizBuySell Alameda]({BBS}alameda-county-businesses-for-sale/)"),
 ("Dental practices (SF $395K/$480K; Santa Rosa $500K/$250K)", "SF / Santa Rosa", "see left", f"[BizBuySell health]({BBS}san-francisco-bay-area/health-care-and-fitness-businesses-for-sale/)"),
 ("Acupuncture practice", "Mill Valley", "$195K / $160K", f"[BizBuySell Marin]({BBS}marin-county-businesses-for-sale/)"),
 ("CPA practices (Novato $350K/$129K and $800K; Lodi $720K/$193K; Manteca $600K/$250K); San Rafael EA firm $250K", "Marin / San Joaquin", "see left", f"[BizBuySell accounting p2]({BBS}accounting-businesses-and-tax-practices-for-sale/2/)"),
 ("Physical therapy ($1.1M, CF ~$264-293K) and sports PT ($400K/$150K)", "San Jose", "see left", f"[DealStream health]({DS}santa-clara-county/health-care-businesses-for-sale)"),
 ("Veterinary hospital (needs hired DVM)", "Hollister", "$1.0M / ND", f"[BizQuest San Benito]({BQ}businesses-for-sale-in-san-benito-county-ca/)"),
 ("Firearms training & retail (FFL-dependent)", "San Mateo", "$325K / $134.7K", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
]

# Implausible figures / data errors / duplicates
DATAERR = [
 ("S&S Welding", "San Jose", "$300K / $323.6K", "Cash flow above asking price", "[MergerPlace](https://www.mergerplace.com/business-for-sale/buy/san-jose)"),
 ("Property restoration", "Pleasanton", "$525K / $475K", "1.1x; one-off catastrophe year or owner labor", "[BizQuest Pleasanton](https://images.bizquest.com/other-services-businesses-for-sale-in-pleasanton-ca)"),
 ("Dry-cleaner agency", "Alameda", "$150K / $210K", "CF above price; revenue inconsistent", f"[BizBen 3335112]({BB}dry-cleaner-agencythriving-businesslots-foot-traffic-3335112)"),
 ("Attended laundromat, Lake Merritt", "Oakland", "$499K / $240K on $360K rev", "67% margin; stale; conflated", f"[BizBen]({BB}coin-operated-laundry-for-sale-in-alameda-county-california-292283.php)"),
 ("Home-based HVAC", "Contra Costa", "$1.0M or $149K / $219K", "Two prices", f"[BizBuySell HVAC]({BBS}hvac-businesses-for-sale/)"),
 ("Preschool, 120 kids", "Fremont", "$1.975M/$192K vs $245K/$50K", "Two figure sets", f"[BizBuySell Fremont]({BBS}fremont/education-and-child-related-businesses-for-sale/)"),
 ("Pool routes (Brentwood, Vacaville, Hollister)", "various", "$41K/$44K; $125K/$468K; $120K/$138K", "CF >= price", f"[BizBuySell Solano]({BBS}solano-county-businesses-for-sale/)"),
 ("Commercial fleet service", "Napa", "$100K / $300K", "CF 3x price", f"[BizBuySell Napa]({BBS}napa-businesses-for-sale/)"),
 ("Home-services franchise", "San Mateo Co.", "$550K / $743.5K", "CF above price (likely revenue)", f"[BizBuySell San Mateo]({BBS}san-mateo-county-businesses-for-sale/)"),
 ("Building-wash service", "Stockton", "$375K / $342.9K", "Identical listing in Boston; templated", "[BusinessBroker.net 1005995](https://www.businessbroker.net/business-for-sale/building-washing-stockton-california/1005995.aspx)"),
 ("Carpet cleaning", "Mountain House", "~$150K / $130K on ~$144K rev", "90% margin; pairing uncertain", f"[BizQuest Lathrop]({BQ}businesses-for-sale-in-lathrop-ca)"),
 ("Express Employment NW Sacramento; ACP home care Walnut Creek", "Sacramento; Walnut Creek", "$200K/$240K; $94K/$100K", "CF above price", f"[BizBuySell staffing]({BBS}staffing-agencies-for-sale/)"),
 ("Swagat Indian; Charlie's Rim Repair", "Stockton; Modesto", "$200K/$200K; $109K/$125.6K", "CF >= price", f"[DealStream Stockton]({DS}stockton-businesses-for-sale)"),
 ("13 FedEx routes Windsor; 16 FedEx routes Santa Rosa", "Sonoma", "$1.1M/$349K; $1.9M/$633K", "Pair copied from Hayward row; second never reconfirmed", "[BizBuySell 2259176](https://www.bizbuysell.com/business-opportunity/13-fedex-ground-routes-santa-rosa-windsor-ca/2259176/)"),
 ("Auto repair, 30+ yrs", "Campbell", "$300K / $93,971", "CF identical to a Fremont listing", f"[DealStream auto]({DS}santa-clara-county/auto-repair-businesses-for-sale)"),
 ("Licensed mail centers in retail stores", "Napa $150K; Sacramento $74.9K", "both $135K rev / $35K", "Identical figures (conflated); also < $40K", f"[DealStream Napa]({DS}napa/small-businesses-for-sale)"),
 ("GMP supplement manufacturer", "Alameda Co.", "CF $90K/$275K/$800K/$335K", "Four cash flows across sites", f"[BizBuySell mfg]({BBS}san-francisco-bay-area/manufacturing-businesses-for-sale/)"),
 ("PostalAnnex-type center", "Walnut Creek", "$220K or $425K / $145K?", "CF may belong to a neighbouring listing", f"[BizBuySell CC]({BBS}contra-costa-county-businesses-for-sale/)"),
 ("Oakdale restaurant", "Oakdale", "$100-115K / ~$30K", "Pairing unclear (and < $40K)", f"[BizBuySell Stanislaus]({BBS}stanislaus-county-businesses-for-sale/)"),
 ("Duplicates removed: 'absentee boba, Santa Clara Co.' = Cupertino; Napa Mission $99K/$91.6K; 'Napa Health Cafe' $299K/$100.5K; Truckee-page background investigation; Martinez alt $199K/$105K", "-", "-", "Same business as a ranked or appendix row", f"[DealStream SCC]({DS}santa-clara-county-businesses-for-sale)"),
]

OVER2M = [
 ("FedEx routes, FT manager in place, semi-absentee", "Hayward", "$2.125M / $764.4K", "Worth a call to negotiate under the cap", f"[BizBen Alameda routes]({BB}route-sales-service-for-sale-alameda-county-california-ca)"),
 ("FedEx 12 routes ($1.725M cash + financing)", "Fairfield", "$2.1M total / $561.3K", "Total consideration over cap", f"[BizBuySell routes p2]({BBS}routes-for-sale/2/)"),
 ("FedEx 17 routes; 10 routes", "San Jose", "$2.45M/$765K; $3.5M/$950K", "Over cap", f"[BizQuest SJ routes]({BQ}routes-for-sale-in-san-jose-ca/)"),
 ("FedEx 5 linehaul routes", "Sacramento", "$2.15M / $720-755K", "Over cap", "[BizBen 1453237](https://www.bizben.com/business-for-sale/5-fedex-linehaul-routes-sacramento-ca-highly-profitable-1453237)"),
 ("Absentee-run new laundromat", "Contra Costa", "$2.95M / $421K EBITDA", "Over cap (a $325K figure also seen)", f"[BizBuySell laundromats]({BBS}san-francisco-bay-area/laundromats-and-coin-laundry-businesses-for-sale/)"),
 ("'Run totally absentee' car wash (with RE); other Sac washes", "Sacramento", "$2.46M/$360K; $2.55M/$380K; $2.6M/$275K", "Over cap", f"[DealStream Sac car washes]({DS}sacramento-county/car-washes-for-sale)"),
 ("Car washes; two-location day spa", "Santa Rosa", "$2.6M/$274.7K; $2.25M/$764-783K", "Over cap", f"[BizBuySell CA car washes]({BBS}car-washes-for-sale/)"),
 ("eMaids; Amazon DSP; laundromat pair; Asian food distributor", "NorCal / SF Bay / San Jose", "$2.495M/$574K; $2.3M/$636K; $2.4M; $2.5M/~$1M", "Over cap", f"[BizBen 279667]({BB}amazon-logistics-company-for-sale-in-san-francisco-bay-area-california-279667)"),
 ("Underground contractor; European auto + RE; SF fitness studio; Walnut Creek auto detail + apt; Santa Cruz restaurant", "various", "$2.16M/$636K; $2.175M; $4.24M; $3.3M; $2.5M/$337K", "Over cap", f"[BizBuySell Bay Area]({BBS}san-francisco-bay-area-businesses-for-sale/)"),
 ("Preschools with RE", "Dixon / Vacaville", "$3M; $6.9M", "Over cap", f"[BizBuySell Dixon]({BBS}dixon-businesses-for-sale/)"),
]

OUTRADIUS = [
 ("Absentee-run coin laundry, lease to 2040", "Carmichael (~1h25m)", 791.5, 131.9, 15, "Edge of radius; would score ~6.6 (about #50) if accepted", f"[BizBen Sacramento]({BB}laundromat-for-sale-sacramento-california-192539.php)"),
 ("Independent NorCal mail center (SC2253)", "City confidential", 449, 175, 75, "Location unknown", "[BizQuest SC2253](https://www.bizquest.com/business-for-sale/mail-center-with-built-in-expansion-and-licensing-fee-potential-sc2253/BW2462361/)"),
 ("Semi-absentee staffing firm", "California (city ND)", 1300, 612, 30, "Location unknown", "[BusinessBroker.net staffing](https://www.businessbroker.net/keyword/california/staffing-and-human-resources-businesses-for-sale.aspx)"),
 ("Absentee kitchen-hood cleaning", "NorCal (Tahoe page)", 399, 90, 15, "Location unknown / Tahoe", f"[BizQuest S. Lake Tahoe]({BQ}business-services-businesses-for-sale-in-south-lake-tahoe-ca)"),
 ("Two remodeled UPS Stores ($1.38M rev.)", "Not stated", 989, 207.5, 150, "Location unknown", "[BizQuest BW2480345](https://www.bizquest.com/business-for-sale/two-remodeled-ups-store-franchise-1-38m-revenue/BW2480345)"),
 ("FedEx Ground 10 routes (+~$275K vehicle fin.)", "Redding (~3h)", 725, 447.6, 75, "Out of radius", "[BusinessBroker.net Redding](https://www.businessbroker.net/city/redding-ca-businesses-for-sale.aspx)"),
 ("Tahoe 3-laundromat package; Tahoe City laundromat", "Tahoe (~3h)", 750, 240.4, 45, "Out of radius", "[BizBuySell CA laundry](https://www.bizbuysell.com/california-businesses-for-sale/?q=az1sYXVuZHJ5Jmx0PTMwLDQwLDgw)"),
 ("Fresno, Bakersfield, SLO, Santa Barbara, Chico, LA/OC, San Diego/Inland Empire rows (~140 listings)", "2-6 h", None, None, None, "Out of radius (see the statewide report)", f"[BizBuySell CA]({'https://www.bizbuysell.com/california-businesses-for-sale/4/'})"),
]

PARTIAL = [
 ("Pest control, 20+ yrs, recurring", "Sacramento", "2024 adj. CF $314.7K; price ND", "[Business Team SA11215](https://www.business-team.com/buy-a-business/business-for-sale.aspx?LID=SA11215&From=Search)"),
 ("Hospice/LTC closed-door pharmacy, non-operator owner, $2M rev.", "Sacramento area", "Price on request; ~$0.9M at 0.45x revenue", "[BizTrader 2433408](https://www.biztrader.com/listing/profitable-hospice-ltc-closed-door-pharmacy/)"),
 ("Mail center, 35 yrs", "Elk Grove", "$175K CF on $550K rev; price ND", "[BusinessBroker.net Elk Grove](https://www.businessbroker.net/city/elk-grove-ca-businesses-for-sale.aspx)"),
 ("Franchise postal store (BizBen 272748)", "Sacramento area", "$140K CF; $395K down; price ND", "[BizBen](https://www.bizben.com/business-for-sale/ups-store-for-sale-sacramento-area-california-ca-123385.php)"),
 ("Landscape design-build (since 2014); pressure washing", "Contra Costa", "$340K CF '~$100K down'; $144.7K CF on $535.8K", f"[DealStream CC]({DS}contra-costa-county-businesses-for-sale)"),
 ("Tree care; landscape construction & maintenance", "Sacramento Co.", "EBITDA $460K; CF $580K; prices ND", f"[BizBuySell CA landscaping]({BBS}landscaping-and-yard-service-businesses-for-sale/)"),
 ("Coffee shop, fully absentee, managers in place", "Santa Clara Co.", "$850K on $1.233M rev; CF ND", f"[BizBen 289935]({BB}coffee-shop-for-sale-in-santa-clara-county-california-289935.php)"),
 ("Major franchise tire shop, absentee", "Santa Clara Co.", "$450K + inventory; CF ND", f"[BizBen 286167](https://m.bizben.com/business-for-sale/major-franchise-tire-shop-for-sale-in-santa-clara-county-california-286167.php)"),
 ("Semi-absentee tea shop in a mall", "San Mateo", "Seller claims $65K/mo sales, $18K/mo net; price ND", f"[BizBen SM boba]({BB}boba-shop-boba-cafe-for-sale-san-mateo-county-california-ca)"),
 ("Laundromat 'never required on-site staff' (Ocean Ave)", "San Francisco", "$300K; CF ND", f"[BizBuySell absentee]({BBS}san-francisco-bay-area/absentee-run-businesses-for-sale/)"),
 ("Laundromat, all-cash deal", "Manteca", "$299K on ~$156K rev; CF ND", f"[BizBuySell Manteca]({BBS}manteca-businesses-for-sale/)"),
 ("Salon suites, 20 tenants", "San Ramon", "$1.35M; CF ND", f"[BizBuySell CC]({BBS}contra-costa-county-businesses-for-sale/)"),
 ("Cleaning co., 'management will stay' (est. 2024)", "Sonoma Co.", "$225-275K; CF ND", f"[DealStream janitorial]({DS}janitorial-businesses-for-sale)"),
 ("FedEx 13 routes; FedEx linehaul 1 route", "Sacramento; Tracy", "$1.575M CF ND; $83.7K CF price ND", f"[BizQuest Sac FedEx]({BQ}fedex-businesses-for-sale-in-sacramento-ca/)"),
 ("Amazon DSP", "San Jose", "$1.45M; CF ND", f"[BizQuest CA DSP]({BQ}amazon-dsp-businesses-for-sale-in-california/)"),
 ("Individual Marin/Sonoma UPS Stores; Sacramento UPS Store (lease date passed)", "Petaluma/Santa Rosa/Mill Valley; Sacramento", "$470-540K each; $310K on $430K rev; CF ND", "[theupsstorefranchise.com](https://www.theupsstorefranchise.com/ups-store-for-sale/california-marin-sonoma-counties)"),
 ("Two-restaurant absentee package (alcohol to verify)", "Turlock", "$450K; CF ND", f"[BizBuySell Modesto-Merced p2]({BBS}modesto-merced-area-established-businesses-for-sale/2/)"),
 ("Semi-absentee math franchise; preschools with non-owner directors", "Millbrae; SF; Sacramento Co.", "$159K; prices ND", f"[BizBen 280641]({BB}preschool-and-child-development-center-for-sale-in-san-francisco-california-280641)"),
 ("Self-storage building (RE)", "Sacramento", "$1.8M or $2.95M; CF ND", "[LoopNet Sacramento](https://www.loopnet.com/search/self-storage-facilities/sacramento-ca/for-sale/)"),
]

# ---------------------------------------------------------------------------
def calc(ask, cf, ded):
    adj = cf - ded
    L = ask * 0.9; r = rate(L); a = pmt(L, r)
    mult = ask / adj if adj > 0 else None
    return adj, mult, L, r, a, adj - a, (adj / a if a else 0), adj / ask * 100

def fin_label(fin, dscr):
    if fin in ("no financing", "cash-only"): return fin
    return "SBA-likely" if dscr >= 1.25 else "SBA-marginal"

rows = []
for p in P:
    (name, city, dm, ask, cf, ded, basis, cat, risk, A, S, fin, faith, status, src, extra) = p
    adj, mult, L, r, a, left, dscr, y = calc(ask, cf, ded)
    assert adj >= 40, (name, adj)
    assert dm <= 80 and ask <= 2000
    score = mult * RISK_W[risk] * (0.85 if A else 1) * (1.15 if S else 1)
    rows.append(dict(name=name, city=city, dm=dm, ask=ask, cf=cf, ded=ded, basis=basis, cat=cat,
                     risk=risk, A=A, S=S, fin=fin_label(fin, dscr), faith=faith, status=status,
                     src=src, extra=extra, adj=adj, mult=mult, L=L, r=r, a=a, left=left,
                     dscr=dscr, y=y, score=score))
rows.sort(key=lambda d: d["score"])

def oop(d):
    s = f"~{f(d['ask'] * 0.13)}"
    return s + (f" {d['extra']}" if d["extra"].startswith("+") else "")

def print_main():
    print("| # | Business | City | Drive | Asking | Stated CF | Deduction (basis) | Adj. CF | Adj. x | All-cash yld | "
          "Out of pocket | SBA loan (rate) | Annual pmt | Left after loan | DSCR | Financeable | Risk | Faith | Status | Source | Score |")
    print("|" + "---|" * 21)
    for n, d in enumerate(rows, 1):
        nm = d["name"] + (" [A]" if d["A"] else "") + (" [S]" if d["S"] else "")
        print(f"| {n} | {nm} | {d['city']} | {drive(d['dm'])} | {f(d['ask'])} | {f(d['cf'])} | {f(d['ded'])} ({d['basis']}) | "
              f"{f(d['adj'])} | {d['mult']:.1f}x | {d['y']:.0f}% | {oop(d)} | {f(d['L'])} ({d['r']:.2f}%) | {f(d['a'])} | "
              f"{f(d['left'])} | {d['dscr']:.2f} | {d['fin']} | {d['risk']} | {d['faith']} | {d['status']} | {d['src']} | {d['score']:.2f} |")

def print_low():
    print("| Business | City | Drive | Asking | Stated CF | Deduction (basis) | Adj. CF | Category | Source |")
    print("|" + "---|" * 9)
    out = []
    for (name, city, dm, ask, cf, ded, basis, cat, src) in LOW:
        adj = cf - ded
        assert adj < 40, name
        out.append((adj, f"| {name} | {city} | {drive(dm)} | {f(ask)} | {f(cf)} | {f(ded)} ({basis}) | {f(adj)} | {cat} | {src} |"))
    for adj, line in sorted(out, key=lambda t: -t[0]):
        print(line)

def print_backup():
    print("| Business | City | Drive | Asking | Stated CF | Deduction | Adj. CF | Adj. x | All-cash yld | Risk | Status | Source |")
    print("|" + "---|" * 12)
    for (name, city, dm, ask, cf, ded, risk, status, src) in BACKUP:
        adj = cf - ded
        mx = f"{ask/adj:.1f}x" if adj > 0 else "n/m"
        print(f"| {name} | {city} | {drive(dm)} | {f(ask)} | {f(cf)} | {f(ded)} | {f(adj)} | {mx} | {adj/ask*100:.0f}% | {risk} | {status} | {src} |")
    for (name, city, status, src) in BACKUP_NOFIN:
        print(f"| {name} | {city} | - | - | - | - | - | - | - | - | {status} | {src} |")

def simple(tbl, hdr):
    print("| " + " | ".join(hdr) + " |"); print("|" + "---|" * len(hdr))
    for t in tbl: print("| " + " | ".join(str(x) for x in t) + " |")

def print_out():
    print("| Business | Location | Asking | Stated CF | Deduction | Adj. CF | Adj. x | Reason | Source |")
    print("|" + "---|" * 9)
    for (name, loc, ask, cf, ded, why, src) in OUTRADIUS:
        if ask is None:
            print(f"| {name} | {loc} | - | - | - | - | - | {why} | {src} |"); continue
        adj = cf - ded
        print(f"| {name} | {loc} | {f(ask)} | {f(cf)} | {f(ded)} | {f(adj)} | {ask/adj:.1f}x | {why} | {src} |")

def categories():
    print("| Category | Ranked rows | Best rank | Median adj. multiple | Median all-cash yield | Median score | Total asking of ranked rows |")
    print("|---|---|---|---|---|---|---|")
    cats = {}
    for n, d in enumerate(rows, 1):
        cats.setdefault(d["cat"], []).append((n, d))
    for c, lst in sorted(cats.items(), key=lambda kv: min(n for n, _ in kv[1])):
        print(f"| {c} | {len(lst)} | #{min(n for n,_ in lst)} | {statistics.median(d['mult'] for _,d in lst):.1f}x | "
              f"{statistics.median(d['y'] for _,d in lst):.0f}% | {statistics.median(d['score'] for _,d in lst):.2f} | {f(sum(d['ask'] for _,d in lst))} |")

def combos():
    # All-cash (riba-free) portfolios <= $2M built only from ranked rows rated Low or Low-Med, faith 'OK',
    # and without a stale/conflicting-figures flag; one to three businesses; ranked by total adjusted CF.
    pool = [d for d in rows if d["risk"] in ("Low", "Low-Med") and d["faith"] == "OK" and not d["S"]]
    res = []
    for k in (1, 2, 3):
        for c in itertools.combinations(pool, k):
            tot = sum(d["ask"] for d in c)
            if tot <= 2000:
                res.append((sum(d["adj"] for d in c), tot, c))
    res.sort(key=lambda t: -t[0])
    print("| Combination (all cash, no loan) | Total price | Adjusted CF | All-cash yield | Managers needed | Notes |")
    print("|---|---|---|---|---|---|")
    seen = 0
    for adj, tot, c in res:
        names = " + ".join(f"{d['name'].split(' (')[0]} ({d['city']})" for d in c)
        notes = "; ".join(sorted(set(d["fin"] for d in c)))
        print(f"| {names} | {f(tot)} | {f(adj)} | {adj/tot*100:.1f}% | {len(c)} | if financed instead: {notes} |")
        seen += 1
        if seen == 6: break
    # Pharmacy-led and backup-offer combinations for reference
    def get(nm, city):
        return next(d for d in rows if d["name"].startswith(nm) and d["city"] == city)
    sr = get("Retail + non-sterile", "San Ramon"); sl = get("Laundromat, low rent", "Solano Co.")
    print(f"| San Ramon pharmacy + Solano laundromat (Medium + Low-Med) | {f(sr['ask']+sl['ask'])} + inventory | "
          f"{f(sr['adj']+sl['adj'])} | {(sr['adj']+sl['adj'])/(sr['ask']+sl['ask'])*100:.1f}% | 2 (PIC + attendant) | inventory and CHOW reserve not included |")
    st = get("FedEx linehaul", "Stockton")
    napa_adj = 222.102 - 75; newark_adj = 262.363 - 75
    print(f"| Stockton linehaul + Napa UPS Store (backup offer) | {f(st['ask']+699)} | {f(st['adj']+napa_adj)} | "
          f"{(st['adj']+napa_adj)/(st['ask']+699)*100:.1f}% | 2 | Napa is pending |")
    cc = get("FedEx routes, SBA pre-qualified", "Contra Costa Co.")
    print(f"| Contra Costa FedEx + Newark UPS Store (backup offer) | {f(cc['ask']+849)} | {f(cc['adj']+newark_adj)} | "
          f"{(cc['adj']+newark_adj)/(cc['ask']+849)*100:.1f}% | 2 | Newark is pending |")

if __name__ == "__main__":
    print(f"<!-- pool ranked={len(rows)} below40={len(LOW)} backup={len(BACKUP)+len(BACKUP_NOFIN)} -->\n")
    print("### Ranked list\n"); print_main()
    print("\n### Category summary\n"); categories()
    print("\n### Interest-free (all-cash) combinations under $2M\n"); combos()
    print("\n### Appendix A: in radius and priced, but adjusted CF < $40K\n"); print_low()
    print("\n### Appendix B: sold / pending / in contract (backup-offer candidates and comps)\n"); print_backup()
    print("\n### Appendix C: faith-screen failures\n"); simple(FAITH, ["Listing", "Location", "Asking / CF", "Reason", "Source"])
    print("\n### Appendix D: licensed-owner professions\n"); simple(LICENSED, ["Listing", "Location", "Asking / CF", "Source"])
    print("\n### Appendix E: implausible figures, data errors, duplicates\n"); simple(DATAERR, ["Listing", "Location", "Figures", "Problem", "Source"])
    print("\n### Appendix F: over the $2M cap\n"); simple(OVER2M, ["Listing", "Location", "Asking / CF", "Note", "Source"])
    print("\n### Appendix G: out of radius or location unknown\n"); print_out()
    print("\n### Appendix H: partial-data leads (not ranked)\n"); simple(PARTIAL, ["Lead", "Location", "What is known", "Source"])
