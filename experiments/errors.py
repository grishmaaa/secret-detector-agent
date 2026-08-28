import json, os
import run_experiment as R

cases = R.load_cases()
rows = []
for c in cases:
    a, extra = R.policy_p2(c)
    s = c["true_state"]
    paid = R.COST[a][s] + extra
    best_hind = min(R.TERMINAL, key=lambda x: R.COST[x][s])
    ideal = R.COST[best_hind][s]
    b = R.posterior({"context": c["context"], "form": c["form"]})
    rows.append(dict(id=c["id"], state=s, ctx=c["context"], form=c["form"],
                     probe=c["probe"], act=a, paid=paid, hind=best_hind,
                     ideal=ideal, regret=paid-ideal, plive=b["live"], pfake=b["fake"]))

rows.sort(key=lambda r: -r["regret"])
tot_paid = sum(r["paid"] for r in rows)
tot_ideal = sum(r["ideal"] for r in rows)
print(f"total paid {tot_paid}, hindsight-optimal {tot_ideal}, total regret {tot_paid-tot_ideal}")
print(f"top-5 regret = {sum(r['regret'] for r in rows[:5])} "
      f"({sum(r['regret'] for r in rows[:5])/(tot_paid-tot_ideal)*100:.1f}% of all regret)\n")
print(f"{'#':>3s} {'true':8s} {'context':12s} {'form':11s} {'chose':8s} {'paid':>5s} "
      f"{'best':8s} {'ideal':>5s} {'regret':>7s} {'P(live)':>8s}")
for r in rows[:8]:
    print(f"{r['id']:3d} {r['state']:8s} {r['ctx']:12s} {r['form']:11s} {r['act']:8s} "
          f"{r['paid']:5d} {r['hind']:8s} {r['ideal']:5d} {r['regret']:7d} {r['plive']:8.4f}")

from collections import Counter
print("\nregret by (chosen action, true state):")
agg = {}
for r in rows:
    if r["regret"]:
        k = (r["act"], r["state"])
        agg[k] = agg.get(k, [0,0]); agg[k][0]+=1; agg[k][1]+=r["regret"]
for k,v in sorted(agg.items(), key=lambda x:-x[1][1]):
    print(f"   {k[0]:8s} on a {k[1]:8s} key: {v[0]:2d} cases, {v[1]:4d} min regret")
print(f"\n   cases with zero regret: {sum(1 for r in rows if r['regret']==0)}/{len(rows)}")
json.dump(rows, open(os.path.join(R.RESULTS,"errors.json"),"w"), indent=2)
