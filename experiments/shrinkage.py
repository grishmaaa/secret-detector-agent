"""Correlation shrinkage on the free features.

The posterior in run_experiment.py multiplies the context and well-formedness
likelihoods, which assumes they are conditionally independent given the state.
They are not: a tests/fixtures/ path and a dummy_key variable name are close to
the same observation counted twice.

The standard correction is to weight each channel's log-likelihood by w < 1.
w = 1 is the naive independent product; w = 0 ignores the free evidence
entirely. This script sweeps w and reports what survives.

Writes results/shrinkage.md and results/shrinkage.json.
"""

import json
import os
from itertools import product

import run_experiment as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")   # same convention as run_experiment.py

WS = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.0]


def posterior_w(ev, w):
    """Free-feature likelihoods raised to the power w. The probe, if present,
    is a separate measurement from a different system and is not shrunk."""
    u = {}
    for s in R.STATES:
        p = R.PRIOR[s]
        if "context" in ev:
            p *= R.L_CONTEXT[s][ev["context"]] ** w
        if "form" in ev:
            p *= R.L_FORM[s][ev["form"]] ** w
        if "probe" in ev:
            p *= R.L_PROBE[s][ev["probe"]]
        u[s] = p
    return R.normalise(u)


def reachable_w(w):
    """The six beliefs after free evidence, with the probability of each.

    Note the marginal P(context, form) is a fact about the world and does not
    depend on w. Shrinkage changes what the agent believes on seeing the
    evidence, not how often it sees it.
    """
    out = []
    for c, f in product(R.CONTEXT, R.FORM):
        pc = sum(R.PRIOR[s] * R.L_CONTEXT[s][c] * R.L_FORM[s][f] for s in R.STATES)
        out.append((c, f, pc, posterior_w({"context": c, "form": f}, w)))
    return out


def exact_w(fn, w):
    """Closed-form expected cost over all 54 worlds, under shrinkage w."""
    total = esc = probed = 0.0
    for s, c, f, pr in product(R.STATES, R.CONTEXT, R.FORM, R.PROBE):
        p = R.PRIOR[s] * R.L_CONTEXT[s][c] * R.L_FORM[s][f] * R.L_PROBE[s][pr]
        a, extra = fn({"context": c, "form": f, "probe": pr}, w)
        total += p * (R.COST[a][s] + extra)
        if a == "escalate":
            esc += p
        if extra:
            probed += p
    return total, esc, probed


def p2_w(case, w):
    return R.cheapest(posterior_w({"context": case["context"],
                                   "form": case["form"]}, w)), 0


def p3_w(case, w):
    ev = {"context": case["context"], "form": case["form"]}
    b = posterior_w(ev, w)
    # EVSI computed against the shrunken belief, since that is what the agent holds
    now = R.expected_cost(b, R.cheapest(b))
    after = 0.0
    for o in R.PROBE:
        po = sum(b[s] * R.L_PROBE[s][o] for s in R.STATES)
        if po <= 0:
            continue
        post = posterior_w(dict(ev, probe=o), w)
        after += po * R.expected_cost(post, R.cheapest(post))
    if now - after > R.K["probe"]:
        return R.cheapest(posterior_w(dict(ev, probe=case["probe"]), w)), R.K["probe"]
    return R.cheapest(b), 0


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []

    for w in WS:
        reach = reachable_w(w)

        # the strongest fake-collapsing cell: production context, well-formed
        strong = [b for c, f, _, b in reach
                  if c == "production" and f == "well-formed"][0]
        # the strongest fake-supporting cell
        weak = [b for c, f, _, b in reach
                if c == "placeholder" and f == "malformed"][0]

        ratios = {round(b["live"] / b["revoked"], 6) for _, _, _, b in reach}

        p2, _, _ = exact_w(p2_w, w)
        p3, _, p3_probed = exact_w(p3_w, w)

        # share of findings on which P2 departs from P0's constant action
        p0_action = R.cheapest(R.PRIOR)
        differ = sum(pc for c, f, pc, b in reach
                     if R.cheapest(b) != p0_action)

        rows.append(dict(w=w,
                         fake_strong=strong["fake"], fake_weak=weak["fake"],
                         ratios=sorted(ratios), p2=p2, p3=p3,
                         p3_probed=p3_probed, differ=differ))

    base = R.exact(R.policy_baseline)[0]
    p0 = R.exact(R.policy_p0)[0]

    with open(os.path.join(OUT, "shrinkage.json"), "w") as fh:
        json.dump(dict(baseline=base, p0=p0, rows=rows), fh, indent=2)

    lines = []
    add = lines.append
    add("# Correlation shrinkage on the free features\n")
    add("The posterior multiplies the context and well-formedness likelihoods,")
    add("which assumes they are conditionally independent given the state. They")
    add("are not. A `tests/fixtures/` path and a `dummy_key` variable name are")
    add("close to the same observation counted twice. Weighting each channel's")
    add("log-likelihood by *w* < 1 is the standard correction. Below, *w* = 1 is")
    add("what the paper reports and *w* = 0 discards the free evidence.\n")
    add(f"Baseline (escalate everything): **{base:.2f}** min.")
    add(f"P0 (prior only, no evidence): **{p0:.2f}** min.\n")
    add("| *w* | P(fake), production + well-formed | P(fake), placeholder + malformed | live:revoked | P2 | P3 | probe bought | P2 differs from P0 |")
    add("|---|---|---|---|---|---|---|---|")
    for r in rows:
        rs = ", ".join(f"{x:.4f}" for x in r["ratios"])
        add(f"| {r['w']:.1f} | {r['fake_strong']:.4f} | "
            f"{r['fake_weak']:.4f} | {rs} | {r['p2']:.2f} | {r['p3']:.2f} | "
            f"{r['p3_probed'] * 100:.2f}% | {r['differ'] * 100:.2f}% |")
    add("")
    add("## What survives\n")
    r1 = rows[0]
    r08 = [r for r in rows if r["w"] == 0.8][0]
    r05 = [r for r in rows if r["w"] == 0.5][0]
    r0 = rows[-1]

    add("**The live:revoked invariance is untouched, and could not have been.**")
    add(f"The two states carry identical free-feature rows, so raising both to")
    add(f"the same power leaves them identical. The ratio sits at")
    add(f"{r1['ratios'][0]:.4f} at every *w*, including *w* = 0. This is worth")
    add("stating precisely because it is the one thing shrinkage cannot reach:")
    add("the invariance follows from two rows being equal, not from the")
    add("independence assumption, and it is the only free-feature result that is")
    add("safe from this critique.\n")

    add("**The *fake* collapse is not robust, and it is the headline number.**")
    add(f"On the most informative evidence the paper reports P(fake) falling")
    add(f"from 0.25 to {r1['fake_strong']:.4f}. A 20% shrinkage puts it at")
    add(f"{r08['fake_strong']:.4f}, roughly double. Halving the weight puts it at")
    add(f"{r05['fake_strong']:.4f}, five times the reported figure. The 0.011")
    add("should be read as the most favourable end of a range, not as a")
    add("measurement.\n")

    add("**The policy barely notices, which is the useful part.**")
    add(f"P2 moves from {r1['p2']:.2f} to {r08['p2']:.2f} minutes at *w* = 0.8,")
    add(f"against a baseline of {base:.2f}. Every conclusion about the cost")
    add("structure survives untouched, because those conclusions never depended")
    add("on the belief being sharp.\n")

    add("**But the belief model dies before the free evidence does.**")
    add(f"At *w* = {r05['w']:.1f} the share of findings on which P2 departs from")
    add(f"P0's constant action reaches {r05['differ'] * 100:.2f}%, and P2's cost")
    add(f"is {r05['p2']:.2f}, which is P0 exactly. Discounting the free evidence")
    add("by half does not degrade the belief model gradually; it removes it. The")
    add("agent falls back to acting on the prior alone and loses nothing but the")
    add(f"{(p0 - r1['p2']) / base * 100:.1f} percentage points the belief model")
    add("was contributing in the first place.\n")

    add("**Probe purchase is not monotone in *w*.**")
    add(f"The probe is bought on {r1['p3_probed'] * 100:.2f}% of findings at")
    add(f"*w* = 1, rises to {max(r['p3_probed'] for r in rows) * 100:.2f}% in the")
    add("middle of the range, and falls to zero once the free evidence is gone.")
    add("Shrinkage first makes the agent uncertain enough to want the probe, then")
    add("uncertain enough that the probe can no longer move it across a boundary.")
    add("")

    with open(os.path.join(OUT, "shrinkage.md"), "w") as fh:
        fh.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print("\nWrote results/shrinkage.md and results/shrinkage.json")


if __name__ == "__main__":
    main()
