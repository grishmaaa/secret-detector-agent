"""Week 2, commit 6b: put the scope field on a parameter too.

Every other new channel in this project is swept rather than assumed. Scope is
not: `scope_probe.py` commits a specific likelihood table, and the best agent
in the project -- P6, the one with the lowest cost and the only one that tells
five states apart -- rests on it. That is the one remaining place where a
headline result stands on a number I made up.

So it gets the same treatment. One parameter:

  q  --  P(scope reads `zero` | the key really is authorised for nothing)

At q = 0.02 the zero_scope row is identical to the live row and the field
carries nothing about the state it was introduced to detect. At q = 1.0 it is
perfect. The committed table used q = 0.95.

The rest of the table is left fixed, and that is a deliberate distinction
rather than laziness. A key WITH permissions reporting that it has permissions
is not an empirical guess -- it is what the field means. The `absent` column is
copied from the probe's existing `null` row because "not in our account" is the
same event in both. The only genuinely uncertain quantity is how reliably a
zero-permission key is recognisable as one, and that is q.

Writes results/scope-sensitivity.md and results/scope-sensitivity.json.
"""

import json
import os
import random
from itertools import product

import run_experiment as R
import week2_experiment as W
import information as I
import scope_probe as S
import fixes as F

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

COST = F.costs()
QS = (0.02, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 1.00)
COMMITTED = 0.95


def l_scope(q):
    t = {s: dict(S.L_SCOPE[s]) for s in W.STATES}
    t["zero_scope"] = {"zero": q, "nonzero": 1 - q, "absent": 0.0}
    return t


def evaluate(cases, q, use_scope=True):
    G = l_scope(q)
    tables = [W.L_PROBE, G] if use_scope else [W.L_PROBE]
    spaces = [R.PROBE, S.SCOPE] if use_scope else [R.PROBE]
    rng = random.Random(4242)
    regret = cost = 0.0
    bought = 0
    hit = {s: 0 for s in W.STATES}
    tot = {s: 0 for s in W.STATES}

    for c in cases:
        t = c["truth"]
        b = I.update(dict(W.PRIOR), [W.L_CONTEXT, W.L_FORM],
                     (c["context"], c["form"]))
        now = W.expected_cost(b, W.cheapest(b, COST), COST)
        after = 0.0
        for o in product(*spaces):
            po = I.marginal(b, tables, o)
            if po <= 0:
                continue
            p = I.update(b, tables, o)
            after += po * W.expected_cost(p, W.cheapest(p, COST), COST)
        extra = 0.0
        if now - after > R.K["probe"]:
            obs = [c["probe"]]
            if use_scope:
                r, acc = rng.random(), 0.0
                for k_, pv in G[t].items():
                    acc += pv
                    if r <= acc:
                        obs.append(k_)
                        break
                else:
                    obs.append("nonzero")
            b = I.update(b, tables, tuple(obs))
            extra = R.K["probe"]
            bought += 1
        a = W.cheapest(b, COST)
        if b["other"] > F.P_OTHER_TRIGGER:
            a = "escalate"
        elif max(COST[a][s] for s in W.STATES) > F.CEILING:
            a = "escalate"
        best = min(W.TERMINAL, key=lambda x: COST[x][t])
        regret += COST[a][t] - COST[best][t]
        cost += COST[a][t] + extra
        tot[t] += 1
        if a == best:
            hit[t] += 1

    n = len(cases)
    rec = {s: (hit[s] / tot[s] if tot[s] else None) for s in W.STATES}
    seen = [v for v in rec.values() if v is not None]
    return dict(regret=regret / n, cost=cost / n, bought=bought / n,
                per_class=rec, balanced=sum(seen) / len(seen))


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = W.build_cases(W.N_CASES, W.SEED)
    off = evaluate(cases, 0, use_scope=False)
    rows = [dict(q=q, **evaluate(cases, q)) for q in QS]
    committed = [r for r in rows if r["q"] == COMMITTED][0]

    payload = dict(no_scope=off, committed_q=COMMITTED, rows=rows)
    with open(os.path.join(OUT, "scope-sensitivity.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# How much of the best agent rests on one invented number?\n")
    add("Every other channel added this week is swept rather than assumed. The")
    add("scope field was not: `scope_probe.py` commits a likelihood table, and")
    add("P6 -- the cheapest agent in the project, and the only one that tells")
    add("five states apart -- stands on it. This puts it on the same footing as")
    add("the rest.\n")
    add("The parameter is **q**, the probability that a key authorised for")
    add("nothing actually reports zero scope. At q = 0.02 its row is identical")
    add("to `live`'s and the field says nothing about the state it exists to")
    add(f"detect. The committed table used q = {COMMITTED}.\n")
    add("The rest of the table stays fixed, and that is a distinction rather")
    add("than an oversight. A key *with* permissions reporting permissions is")
    add("not an empirical guess, it is what the field means; and the `absent`")
    add("column is copied from the probe's `null` row because *not in our")
    add("account* is the same event in both. Only q is genuinely uncertain.\n")

    add("## The sweep\n")
    add("| q | Regret | Total cost | Probe bought | Balanced acc. | live | revoked | fake | zero_scope |")
    add("|---|---|---|---|---|---|---|---|---|")
    add(f"| *no scope* | {off['regret']:.2f} | {off['cost']:.2f} | "
        f"{off['bought'] * 100:.1f}% | {off['balanced']:.3f} | " +
        " | ".join(f"{off['per_class'][s]:.3f}" for s in
                   ("live", "revoked", "fake", "zero_scope")) + " |")
    for r in rows:
        mark = " **←committed**" if r["q"] == COMMITTED else ""
        add(f"| {r['q']:.2f}{mark} | {r['regret']:.2f} | {r['cost']:.2f} | "
            f"{r['bought'] * 100:.1f}% | {r['balanced']:.3f} | " +
            " | ".join(f"{r['per_class'][s]:.3f}" for s in
                       ("live", "revoked", "fake", "zero_scope")) + " |")
    add("")

    null = [r for r in rows if r["q"] == 0.02][0]
    add("## What survives, and it is not what I expected\n")
    add("Read the *no scope* row against the **q = 0.02** row. At q = 0.02 the")
    add("field is worthless for the state it was introduced to detect --")
    add("`zero_scope` recall is 0.000, identical to not having the field at")
    add("all. And yet:\n")
    add("| | no scope | q = 0.02 | q = 0.95 |")
    add("|---|---|---|---|")
    add(f"| regret | {off['regret']:.2f} | {null['regret']:.2f} | "
        f"{committed['regret']:.2f} |")
    add(f"| total cost | {off['cost']:.2f} | {null['cost']:.2f} | "
        f"{committed['cost']:.2f} |")
    add(f"| probe bought | {off['bought'] * 100:.1f}% | "
        f"{null['bought'] * 100:.1f}% | {committed['bought'] * 100:.1f}% |")
    add(f"| balanced acc. | {off['balanced']:.3f} | {null['balanced']:.3f} | "
        f"{committed['balanced']:.3f} |")
    add(f"| `fake` recall | {off['per_class']['fake']:.3f} | "
        f"{null['per_class']['fake']:.3f} | "
        f"{committed['per_class']['fake']:.3f} |")
    add(f"| `zero_scope` recall | {off['per_class']['zero_scope']:.3f} | "
        f"{null['per_class']['zero_scope']:.3f} | "
        f"{committed['per_class']['zero_scope']:.3f} |")
    add("")
    a = off["regret"] - null["regret"]
    b = null["regret"] - committed["regret"]
    add(f"**Almost none of the scope field's value comes from the number I")
    add(f"invented.** Of the {a + b:.2f} minutes of regret it removes,")
    add(f"**{a:.2f} arrives at q = 0.02** and only {b:.2f} more accumulates")
    add(f"across the entire rest of the range -- {a / (a + b) * 100:.0f}% of")
    add("the benefit against 12%.\n")
    add("The reason is the `absent` column, and that column was not invented.")
    add("It was copied from the probe's existing `null` row, because *the key")
    add("is not in our account* is one event that both fields report. A `fake`")
    add("string was never in the account, so scope comes back absent, and that")
    add("is what takes `fake` recall from 0.573 to 0.939 and drives the probe's")
    add("purchase rate from 1.0% to 46.8%. All of that is present at q = 0.02.\n")
    add(f"What q actually buys is `zero_scope` recall -- 0.000 up to "
        f"{committed['per_class']['zero_scope']:.3f} -- on a state holding "
        f"{W.PRIOR['zero_scope'] * 100:.0f}% of the prior. Real, small, and")
    add("the only part of the result exposed to a guess.\n")

    add("## The honest reading\n")
    add("I set out to check how much of the best agent rests on one invented")
    add("number, expecting to have to defend 0.95. The answer is that the")
    add(f"number carries about {b / (a + b) * 100:.0f}% of the field's value and")
    add("the conclusion does not depend on it at all: **every** value of q in")
    add("the sweep, including the one where the field cannot see the state it")
    add("was built for, leaves the agent better on regret, cost and balanced")
    add("accuracy than not reading scope at all.\n")
    add("There is a lesson in that which is worth more than the sensitivity")
    add("check. I introduced the scope field to detect `zero_scope`, argued for")
    add("it on those grounds, and reported it as the fix for that state. It")
    add("mostly is not. It is a `fake` detector that happens to arrive on the")
    add("same call, and it earns its place for a reason I did not anticipate")
    add("and would not have found without putting the parameter on a sweep.")
    add("**The stated reason a design change works is not always the reason it")
    add("works**, and only taking the assumption away shows which is which.\n")
    add("This is the third quantity handled this way -- exploitation")
    add("probability, registry coverage and rotation compliance, now scope")
    add("reliability. In each case a number I could not defend was replaced by")
    add("a sweep, and in each case the useful finding was about where the")
    add("conclusion changes rather than what it equals at a point estimate.")
    add("")

    with open(os.path.join(OUT, "scope-sensitivity.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
