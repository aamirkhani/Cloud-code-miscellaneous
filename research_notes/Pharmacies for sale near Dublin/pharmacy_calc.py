"""Absentee-adjusted economics for pharmacy listings near Dublin, CA.

All listing figures come from search-engine snippets (unverified), seen 2026-10-11.

Assumptions
- Hired pharmacist-in-charge (PIC), loaded cost $190K-$215K/yr (BLS May 2025
  SF-Oakland-Fremont pharmacist median $177,410 plus payroll taxes/benefits and
  a PIC premium). Deducted only where the owner appears to be the working PIC.
- Out-of-pocket = 13% of price (10% SBA equity injection + ~3% closing/fees),
  plus any inventory paid at cost on top of the price (unknown -> flagged).
- SBA 7(a): loan = 90% of price, 10-year amortization, monthly payments.
  Rate 9.75% if loan > $350K; 11.25% for $250K-$350K; 12.75% if <= $250K.
- All-cash yield = absentee cash flow / (price + known extra inventory).
"""

PIC_LOW, PIC_HIGH = 190_000, 215_000


def sba_rate(loan):
    if loan > 350_000:
        return 0.0975
    if loan > 250_000:
        return 0.1125
    return 0.1275


def annual_payment(loan, rate, years=10):
    r, n = rate / 12, years * 12
    return loan * r / (1 - (1 + r) ** -n) * 12


# name, asking, seller cash flow, owner_is_pic, known extra inventory, inventory note
LISTINGS = [
    ("San Ramon retail+compounding (BFS/BizQuest price)", 1_479_505, 595_650, True, 0, "inventory treatment unknown"),
    ("San Ramon retail+compounding (BizBuySell price)", 1_645_950, 635_650, True, 0, "inventory treatment unknown"),
    ("SF Central Richmond retail (headline CF)", 1_525_650, 635_305, True, 0, "inventory treatment unknown"),
    ("SF Central Richmond retail ('net' ~575K)", 1_525_650, 575_000, True, 0, "inventory treatment unknown"),
    ("Sacramento/Larchmont retail (headline CF)", 275_800, 205_600, True, 0, "inventory treatment unknown"),
    ("Sacramento/Larchmont retail (text ~180K)", 275_800, 180_000, True, 0, "inventory treatment unknown"),
    ("Sacramento Co. retail est. 2022 (unverified pairing)", 199_900, 70_022, True, 0, "inventory treatment unknown"),
]


def fmt(x):
    sign = "-" if x < 0 else ""
    x = abs(x)
    return f"{sign}${x/1000:,.0f}K" if x < 1_000_000 else f"{sign}${x/1_000_000:,.2f}M"


def main():
    print("Absentee-adjusted view (PIC range $190K-$215K loaded; '+inv' = add unknown inventory at cost)\n")
    hdr = ("Listing", "Ask", "Seller CF", "Seller x", "Absentee CF", "Absentee x",
           "Out-of-pocket", "Loan @ rate", "Annual pmt", "Left after loan", "All-cash yield")
    print(" | ".join(hdr))
    for name, ask, cf, owner_pic, inv, note in LISTINGS:
        lo_cf = cf - (PIC_HIGH if owner_pic else 0)
        hi_cf = cf - (PIC_LOW if owner_pic else 0)
        loan = 0.9 * ask
        rate = sba_rate(loan)
        pmt = annual_payment(loan, rate)
        oop = 0.13 * ask + inv
        basis = ask + inv
        mult_lo, mult_hi = (basis / hi_cf if hi_cf > 0 else float("nan")), (basis / lo_cf if lo_cf > 0 else float("nan"))
        row = (
            name, fmt(ask), fmt(cf), f"{ask/cf:.2f}x",
            f"{fmt(lo_cf)} to {fmt(hi_cf)}",
            f"{mult_lo:.1f}-{mult_hi:.1f}x" if lo_cf > 0 else ("n/m (CF<=0)" if hi_cf <= 0 else f">{mult_lo:.0f}x"),
            f"{fmt(oop)} +inv",
            f"{fmt(loan)} @ {rate*100:.2f}%",
            fmt(pmt),
            f"{fmt(lo_cf - pmt)} to {fmt(hi_cf - pmt)}",
            f"{lo_cf/basis*100:.0f}% to {hi_cf/basis*100:.0f}%",
        )
        print(" | ".join(row) + f"   [{note}]")

    print("\nDSCR (absentee CF midpoint / annual SBA payment):")
    for name, ask, cf, owner_pic, inv, _ in LISTINGS:
        mid = cf - ((PIC_LOW + PIC_HIGH) / 2 if owner_pic else 0)
        loan = 0.9 * ask
        pmt = annual_payment(loan, sba_rate(loan))
        print(f"  {name}: {mid/pmt:.2f}x")

    print("\nInventory sensitivity (each $100K of inventory paid in cash on top of price):")
    for name, ask, cf, owner_pic, inv, _ in LISTINGS[:4]:
        mid = cf - (PIC_LOW + PIC_HIGH) / 2
        for extra in (100_000, 250_000):
            print(f"  {name} +{fmt(extra)} inv: out-of-pocket {fmt(0.13*ask+extra)}, "
                  f"all-cash yield {mid/(ask+extra)*100:.0f}%, absentee multiple {(ask+extra)/mid:.1f}x")

    print("\nRiba-free installment illustration (40% down, balance over 7 yrs, no interest):")
    for name, ask, cf, owner_pic, inv, _ in LISTINGS[:4:2]:
        mid = cf - (PIC_LOW + PIC_HIGH) / 2
        down, yearly = 0.4 * ask, 0.6 * ask / 7
        print(f"  {name}: down {fmt(down)}, {fmt(yearly)}/yr, coverage {mid/yearly:.1f}x")


if __name__ == "__main__":
    main()
