"""Reconstructed P&L sanity check for the downtown San Mateo absentee boba franchise.

All inputs are assumptions drawn from the research notes in this folder (ranges, not
verified seller financials). Run: python3 boba_pnl.py
"""

RENT = 7_400 * 12            # listing: $7,400/mo incl. NNN -> $88,800/yr
BURDEN = 1.15                # payroll taxes, workers' comp, CA sick leave (assumption)
# Manager modeled as a full-time hourly store lead at $25/h x 2080 h = $52,000 (a salaried
# exempt manager would cost more: CA exempt floor = 2 x $16.90 x 2080 = $70,304 in 2026).
MGR_SALARY = 52_000
MGR_COST = MGR_SALARY * BURDEN
MGR_FLOOR_HOURS = 40         # manager's own weekly hours on the floor
CARD_RATE = 0.03             # card processing on non-delivery sales
DELIVERY_COMMISSION = 0.25   # DoorDash/Uber Eats "Plus" tier
OTHER_FIXED = 24_000         # utilities, insurance, POS/tech, repairs, accounting, permits
OTHER_VAR = 0.015            # misc. variable costs as share of sales

SCENARIOS = {
    # name: (COGS %, royalty+marketing %, delivery share of sales)
    "Good": (0.25, 0.06, 0.10),
    "Base": (0.30, 0.075, 0.15),
    "Poor": (0.35, 0.09, 0.25),
}
WAGES = {"$18.60 (San Mateo city)": 18.60, "$20.00 (AB 1228, 60+ units)": 20.00}
SALES_LEVELS = [300_000, 450_000, 600_000]


def weekly_hours(sales):
    """Staffed labor-hours/week: 98 h at $300K (14 h/day: one person all day plus a second
    at peaks), +30 h per extra $150K (about $66-73 of sales per labor-hour at $450-600K)."""
    return 98 + (sales - 300_000) / 150_000 * 30


def pnl(sales, wage, cogs, roy, deliv_share, royalty=True, rent=RENT, manager=True):
    hours = weekly_hours(sales)
    crew_hours = max(hours - (MGR_FLOOR_HOURS if manager else 0), 0)
    crew = crew_hours * 52 * wage * BURDEN
    labor = crew + (MGR_COST if manager else 0)
    fees = deliv_share * sales * DELIVERY_COMMISSION + (1 - deliv_share) * sales * CARD_RATE
    lines = {
        "COGS": cogs * sales,
        "Labor (crew + manager)": labor,
        "Rent": rent,
        "Royalty + marketing": roy * sales if royalty else 0,
        "Card + delivery fees": fees,
        "Other opex": OTHER_FIXED + OTHER_VAR * sales,
    }
    return lines, sales - sum(lines.values())


def annual_payment(principal, rate, years=10):
    r = rate / 12
    n = years * 12
    return principal * r / (1 - (1 + r) ** -n) * 12


def money(x):
    return f"-${abs(x):,.0f}" if x < 0 else f"${x:,.0f}"


def main():
    print("=" * 78)
    print("1. Detailed base-case P&L (COGS 30%, royalty+mkt 7.5%, 15% delivery), with manager")
    print("=" * 78)
    for wname, wage in WAGES.items():
        print(f"\nCrew wage {wname}")
        print(f"{'Line':26}" + "".join(f"{'$'+str(s//1000)+'K sales':>17}" for s in SALES_LEVELS))
        results = [pnl(s, wage, *SCENARIOS["Base"]) for s in SALES_LEVELS]
        for key in results[0][0]:
            row = "".join(
                f"{money(r[0][key]):>10} ({r[0][key]/s:5.1%})" for r, s in zip(results, SALES_LEVELS)
            )
            print(f"{key:26}{row}")
        row = "".join(f"{money(r[1]):>10} ({r[1]/s:5.1%})" for r, s in zip(results, SALES_LEVELS))
        print(f"{'OWNER CASH FLOW':26}{row}")

    print("\n" + "=" * 78)
    print("2. Owner cash flow (pre-debt, manager paid) across scenarios")
    print("=" * 78)
    print(f"{'Scenario / wage':40}" + "".join(f"{'$'+str(s//1000)+'K':>12}" for s in SALES_LEVELS))
    for sname, params in SCENARIOS.items():
        for wname, wage in WAGES.items():
            cfs = [pnl(s, wage, *params)[1] for s in SALES_LEVELS]
            print(f"{sname + ', ' + wname:40}" + "".join(f"{money(c):>12}" for c in cfs))

    print("\n" + "=" * 78)
    print("3. Sales needed for the claimed $180K cash flow (manager paid)")
    print("=" * 78)
    for sname, params in SCENARIOS.items():
        for wname, wage in WAGES.items():
            s = 200_000
            while pnl(s, wage, *params)[1] < 180_000 and s < 3_000_000:
                s += 5_000
            print(f"{sname + ', ' + wname:40} ~{money(s)}")
    print(f"\nRent at $300K sales = {RENT/300_000:.1%} of sales; $180K CF at $300K = {180/300:.0%} of sales")

    print("\n" + "=" * 78)
    print("4. Financing at $350K asking price")
    print("=" * 78)
    price = 350_000
    loan = price * 0.90
    pay = annual_payment(loan, 0.1125)
    down = price - loan
    print(f"SBA 7(a): 10% down {money(down)}, loan {money(loan)} @ 11.25%/10 yr -> {money(pay)}/yr ({money(pay/12)}/mo)")
    extras = {"franchise transfer fee (est. $10K-$42.5K; use $10K)": 10_000,
              "working capital + inventory": 20_000,
              "legal, diligence, SBA/closing, health permit": 15_000}
    oop = down + sum(extras.values())
    for k, v in extras.items():
        print(f"  + {k}: {money(v)}")
    print(f"  ~ SBA out-of-pocket: {money(oop)} ({oop/price:.0%} of price)")
    print(f"All-cash out-of-pocket: ~{money(price + sum(extras.values()))}")
    note_down, note_years = 0.40, 4
    note = price * (1 - note_down)
    note_pay = note / note_years
    print(f"Interest-free seller note: {note_down:.0%} down {money(price*note_down)}, "
          f"{money(note)} over {note_years} yrs at 0% -> {money(note_pay)}/yr")

    print(f"\n{'Owner CF (Base)':32}{'CF':>10}{'All-cash yld':>14}{'Price/CF':>10}{'After SBA':>12}{'After 0% note':>15}")
    cases = [("Listing claim (as stated)", 180_000)]
    for s in SALES_LEVELS:
        for wname, wage in WAGES.items():
            cases.append((f"${s//1000}K, {wname.split()[0]}", pnl(s, wage, *SCENARIOS["Base"])[1]))
    for label, cf in cases:
        mult = f"{price/cf:.1f}x" if cf > 0 else "n/m"
        print(f"{label:32}{money(cf):>10}{cf/price:>14.0%}{mult:>10}{money(cf-pay):>12}{money(cf-note_pay):>15}")

    print("\n" + "=" * 78)
    print("5. Comps")
    print("=" * 78)
    # Cupertino independent: $592,318 sales, $256,380 CF claimed, manager-run, no royalty.
    cs = 592_318
    for label, params in (("Base", (0.30, 0.0, 0.15)), ("Good", (0.25, 0.0, 0.10))):
        _, before_rent = pnl(cs, 18.60, *params, royalty=False, rent=0)
        gap = before_rent - 256_380
        verdict = (f"rent could be at most {money(gap)}/yr ({money(gap/12)}/mo)" if gap > 0
                   else f"claim exceeds modeled CF even at ZERO rent, by {money(-gap)}")
        print(f"Cupertino {label} costs (no royalty, $18.60, manager paid): CF before rent "
              f"{money(before_rent)} -> {verdict}")
    print(f"  Cupertino price/CF as claimed: {400_000/256_380:.2f}x; CF margin {256_380/cs:.0%}")
    print(f"  SBA on $400K (90% @ 9.75%, >$350K tier): {money(annual_payment(360_000, 0.0975))}/yr")
    print(f"San Jose Gong Cha: $298K / $90K CF = {298/90:.1f}x; if $90K is SDE, minus ${MGR_COST/1000:.0f}K manager "
          f"-> {money(90_000 - MGR_COST)} absentee CF")
    print(f"San Mateo as claimed: $350K / $180K = {350/180:.2f}x")


if __name__ == "__main__":
    main()
