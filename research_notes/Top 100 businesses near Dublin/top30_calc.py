def rate(loan):
    prime=6.75
    if loan<=50e3: return prime+6.5
    if loan<=250e3: return prime+6
    if loan<=350e3: return prime+4.5
    return prime+3
def pmt(L,r,n=10):
    i=r/100/12; N=n*12
    return L*i/(1-(1+i)**-N)*12
top8=[("Mission Foods route, Vallejo","40m",619,451,80,"Low-Med"),
("Full-service car wash, Fairfield","45m",300,141,60,"Low-Med"),
("Plumbing contractor, Marin","55m",547,310,140,"Medium"),
("Pharmacy, San Francisco","40m+",1525.65,635.3,190,"Medium"),
("FedEx Ground 8 routes, Hayward","15m",1100,349,75,"Low"),
("FedEx Ground 13 vehicles, Solano","45m",1400,412.2,75,"Low"),
("FedEx route, Contra Costa","25m",1800,473.5,75,"Low"),
("FedEx Ground 7 routes, Fremont/Newark","20m",925,243,75,"Low")]
tierA=[("S&S Welding, San Jose (verify numbers)","30m",300,323.6,110,"Med-High"),
("Hair salon & beauty school, Marin","55m",649,352.7,120,"Medium"),
("Liquor & market, Pacific Heights SF","45m",420,185.25,70,"Medium"),
("Locksmith, Vallejo","40m",200,135,80,"Medium"),
("Flooring retailer, San Jose (may be stale)","30m",252,139.8,70,"Medium"),
("Mail center franchise, Napa","50m",200,108,55,"Low-Med"),
("Pool safety fence co., Sacramento (borderline)","1h20m",274.5,140,70,"Medium"),
("Day spa, San Francisco","45m",200,119.1,70,"Medium"),
("Grocery food manufacturer, SF","45m",695,262,100,"Medium"),
("Concrete polishing/waterproofing, Sacramento (borderline)","1h20m",849,316.4,120,"Medium"),
("Gas station + land + house, Stockton","50m",450,171.8,70,"Med-High"),
("Soil testing lab, Central Coast","~1h10m",1200,385.5,120,"Medium"),
("Towing & repair, San Mateo County","35m",720,233,85,"Medium"),
("CNC fabricator, GM in place, SF/NorCal","~45m",1000,247.6,50,"Low-Med"),
("FedEx Ground 9 routes, Fairfield","45m",1650,397.5,75,"Low"),
("Marketing/print services, Sacramento (borderline)","1h20m",765,250,100,"Medium"),
("Commercial electrical contractor, Sonoma Co.","1h15m",1290,400,150,"Medium"),
("Sign & print franchise, south Napa Co.","45m",775,228.9,80,"Low-Med"),
("IT services/MSP, Alameda Co. (offer pending)","15m",735,253.7,120,"Medium")]
tierB=[("Pizza restaurant, San Francisco","45m",350,280,80,"High"),
("Restaurant w/ liquor license, Watsonville","1h15m",197,154.5,70,"High"),
("Turnkey restaurant, San Francisco","45m",1350,444.7,100,"High")]
k=lambda x:x[2]/(x[3]-x[4])
rows=top8+sorted(tierA,key=k)+sorted(tierB,key=k)
print("| # | Business (drive) | Asking | Cash flow | Adj. cash flow | Adj. multiple | Out of pocket | Loan (rate) | Annual loan pmt | Left after loan | Risk |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
f=lambda v:f"${v:,.0f}K" if v<1000 else f"${v/1000:.2f}M"
for n,(name,d,p,cf,m,risk) in enumerate(rows,1):
    adj=cf-m; L=p*0.9; r=rate(L*1000); a=pmt(L,r); oop=p*0.13
    print(f"| {n} | {name} ({d}) | {f(p)} | {f(cf)} | {f(adj)} | {p/adj:.1f}x | ~{f(oop)} | {f(L)} ({r:.2f}%) | {f(a)} | {f(adj-a)} | {risk} |")
