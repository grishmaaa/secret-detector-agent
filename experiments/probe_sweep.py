import run_experiment as R
from itertools import product

B = R.reachable_beliefs()
rows = []
for c, f, pe, b in B:
    rows.append((f"{c}/{f}", pe, b["live"], R.cheapest(b),
                 R.evsi(b, {"context": c, "form": f})))

print("=== gross value of the probe at each reachable belief ===\n")
print(f"{'evidence':26s}{'P(seen)':>9s}{'P(live)':>9s}{'act now':>9s}{'EVSI':>9s}")
for n, pe, pl, a, v in sorted(rows, key=lambda r: -r[4]):
    print(f"{n:26s}{pe:9.4f}{pl:9.4f}{a:>9s}{v:9.4f}")

cuts = sorted({round(v, 6) for *_, v in rows if v > 1e-9})
print(f"\nEVSI takes only these non-zero values: {', '.join(f'{c:.4f}' for c in cuts)}")
print("so the probe price only matters at those two points -- everywhere else\n"
      "the behaviour is flat.\n")

def state_at(price):
    fire = [(n, pe) for n, pe, *_ , v in [(r[0], r[1], r[2], r[3], r[4]) for r in rows] if v > price]
    return fire, sum(pe for _, pe in fire)

print("=== behaviour at the prices asked for ===\n")
print(f"{'price':>7s}{'buys at':>9s}{'% findings':>12s}{'P2':>9s}{'P3':>9s}{'net gain':>10s}   where")
p2 = R.exact(R.policy_p2)[0]
for price in [0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0]:
    R.K["probe"] = price
    p3 = R.exact(R.policy_p3)[0]
    fire, share = state_at(price)
    where = ", ".join(n.split("/")[0][:4] + "/" + n.split("/")[1][:4] for n, _ in fire) or "nowhere"
    print(f"{price:7.1f}{len(fire):9d}{share*100:11.2f}%{p2:9.2f}{p3:9.2f}{p2-p3:10.3f}   {where}")
R.K["probe"] = 3

print("\n=== the exact crossovers ===\n")
prev = None
lo, hi = 0.0, 6.0
for i in range(6001):
    price = lo + (hi - lo) * i / 6000
    _, share = state_at(price)
    if prev is not None and abs(share - prev) > 1e-12:
        print(f"   at {price:.4f} min the probe stops being bought on one bucket "
              f"-> {share*100:.2f}% of findings")
    prev = share
print(f"\n   below 1.40 min : bought on 14.55% of findings (both malformed buckets)")
print(f"   1.40 to 5.21   : bought on  3.98% (neutral/malformed only)")
print(f"   above 5.21     : never bought")
