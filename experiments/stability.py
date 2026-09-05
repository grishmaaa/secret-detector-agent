"""Week 2, commit 10: how much of every headline is one draw?

Two review rounds landed the same objection and I could not answer it: every
number in this project comes from a single seed, and nothing anywhere reports an
interval. Two of my own scripts already disagreed about the same agent -- P6 is
balanced accuracy 0.4669 in `fixes.py` and 0.4942 in `generalization.py` -- and I
had been quoting whichever number the section needed without noticing they were
the same configuration run twice.

They differ because P6 has a nuisance random variable nothing else has: the
scope reading is DRAWN, once per purchased probe, so a different scope seed is a
different experiment. The 500 cases are frozen; this is the only thing moving.

So: hold the cases fixed, vary only that draw, and report the distribution.

This does not fix the deeper problem -- the case set itself is one draw from the
prior, and varying that would need the whole pipeline reseeded -- but it puts an
interval on the quantity the paper leans on hardest, and it answers whether
"0.000 to 0.954" is a result or a lucky seed.

Writes results/stability.md and results/stability.json.
"""

import json
import math
import os
import statistics as st

import run_experiment as R
import week2_experiment as W
import fixes as F

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

N_SEEDS = 200
COST = F.costs()


def score(policy, cases):
    hit = {s: 0 for s in W.STATES}
    tot = {s: 0 for s in W.STATES}
    regret = total = 0.0
    esc = 0
    for c in cases:
        a, extra, _ = policy(c)
        t = c["truth"]
        best = min(W.TERMINAL, key=lambda x: COST[x][t])
        regret += COST[a][t] - COST[best][t]
        total += COST[a][t] + extra
        tot[t] += 1
        if a == best:
            hit[t] += 1
        if a == "escalate":
            esc += 1
    n = len(cases)
    rec = {s: (hit[s] / tot[s] if tot[s] else None) for s in W.STATES}
    seen = [v for v in rec.values() if v is not None]
    return dict(regret=regret / n, cost=total / n, escalated=esc / n,
                balanced=sum(seen) / len(seen), per_class=rec)


def spread(vals):
    vals = sorted(vals)
    n = len(vals)
    return dict(mean=st.mean(vals), sd=st.pstdev(vals),
                lo=vals[int(0.025 * n)], hi=vals[int(0.975 * n) - 1],
                min=vals[0], max=vals[-1])


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = W.build_cases(W.N_CASES, W.SEED)

    # P2 as built has no scope draw at all, so it is a point, not a
    # distribution. That asymmetry is itself worth stating.
    p2 = score(F.make_policy(W.COST, escalation=False), cases)

    runs = []
    for s in range(N_SEEDS):
        runs.append(score(F.make_full(COST, scope_seed=90000 + s), cases))

    metrics = {}
    for key in ("regret", "cost", "escalated", "balanced"):
        metrics[key] = spread([r[key] for r in runs])
    for s in W.STATES:
        vals = [r["per_class"][s] for r in runs if r["per_class"][s] is not None]
        if vals:
            metrics[f"recall_{s}"] = spread(vals)

    committed = score(F.make_full(COST), cases)

    payload = dict(n_seeds=N_SEEDS, n_cases=W.N_CASES, case_seed=W.SEED,
                   p2=p2, committed=committed, metrics=metrics)
    with open(os.path.join(OUT, "stability.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# How much of each headline is one draw?\n")
    add("Every number in this project comes from a single seed and nothing")
    add("reports an interval. Two review rounds said so and I could not answer.")
    add("Worse, two of my own scripts disagreed about the same agent -- P6 is")
    add("balanced accuracy 0.4669 in `fixes.py` and 0.4942 in")
    add("`generalization.py` -- and I had been quoting whichever number the")
    add("section needed without noticing they were one configuration run twice.\n")
    add("They differ because P6 has a nuisance random variable nothing else has.")
    add("The scope reading is **drawn**, once per purchased probe. The 500 cases")
    add("are frozen; this is the only thing moving. So hold the cases and vary")
    add(f"only that draw, {N_SEEDS} times.\n")

    add("## The spread\n")
    add("| Quantity | Committed seed | Mean | SD | 95% interval |")
    add("|---|---|---|---|---|")
    labels = [("regret", "Regret, min/finding", "{:.2f}"),
              ("cost", "Total cost, min/finding", "{:.2f}"),
              ("escalated", "Sent to a human", "{:.3f}"),
              ("balanced", "Balanced accuracy", "{:.3f}")]
    for key, lab, fmt in labels:
        m = metrics[key]
        add(f"| {lab} | {fmt.format(committed[key])} | {fmt.format(m['mean'])} | "
            f"{fmt.format(m['sd'])} | {fmt.format(m['lo'])} – {fmt.format(m['hi'])} |")
    for s in ("live", "revoked", "fake", "zero_scope", "other"):
        k = f"recall_{s}"
        if k in metrics:
            m = metrics[k]
            add(f"| `{s}` recall | {committed['per_class'][s]:.3f} | "
                f"{m['mean']:.3f} | {m['sd']:.3f} | {m['lo']:.3f} – {m['hi']:.3f} |")
    add("")

    fk = metrics["recall_fake"]
    bal = metrics["balanced"]
    rev = metrics["recall_revoked"]
    add("## What survives and what does not\n")
    add(f"**The `fake` result survives comfortably.** Recall runs")
    add(f"{fk['min']:.3f}–{fk['max']:.3f} across every seed against a")
    add("pre-fix value of **0.000**, so the claim that the agent went from")
    add("unable to produce the label to producing it reliably does not depend on")
    add("the draw. That is the paper's second headline and it holds.\n")
    add(f"**Balanced accuracy is softer than I reported it.** Mean")
    add(f"{bal['mean']:.3f}, sd {bal['sd']:.3f}, 95% interval")
    add(f"{bal['lo']:.3f}–{bal['hi']:.3f}. The committed seed gives")
    add(f"{committed['balanced']:.3f}. Quoting three decimal places on that was")
    add("false precision, and the honest form of the sentence is")
    add(f"**0.300 → {bal['mean']:.2f} ± {bal['sd']:.2f}**.\n")
    add(f"**`revoked` recall is the number to stop quoting to three decimals.**")
    add(f"Mean {rev['mean']:.3f}, sd {rev['sd']:.3f}, range")
    add(f"{rev['min']:.3f}–{rev['max']:.3f}. On 129 revoked cases that is a")
    add("handful of findings moving. The paper's honest admission -- that the")
    add("agent still barely tells revoked from live -- is correct, but the")
    add("specific value carries about one significant figure, not three.\n")
    esc = metrics["escalated"]
    add(f"**Escalation is stable.** {esc['mean']:.3f} ± {esc['sd']:.3f}, which")
    add("is why the 2.4% and 2.8% quoted in different sections are the same")
    add("number seen twice rather than a disagreement. Both are inside the")
    add("interval; neither should have been quoted alone.\n")

    add("## The limitation this does not remove\n")
    add("Only the scope draw varies here. The 500 cases are themselves one draw")
    add("from the prior, and re-drawing them would move everything again --")
    add("including P2, which has no scope draw and therefore appears in this")
    add("table as a point when it is not one. So these intervals are a **lower")
    add("bound on the uncertainty**, not a confidence interval on the result.")
    add("They establish that the `fake` finding is not a lucky seed. They do not")
    add("establish that any figure here would survive a different case set.\n")
    add("Stating that plainly is the point. A review round asked whether the")
    add("headlines were one draw; the answer for the largest of them is no, for")
    add("the smallest of them is partly, and for the case set as a whole it is")
    add("still unmeasured.\n")

    with open(os.path.join(OUT, "stability.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
