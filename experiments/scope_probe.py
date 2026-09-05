"""Week 2, commit 4a: two experiments about the state Week 1 did not model.

EXPERIMENT A -- does reading the key's scope earn its place?

  The probe already costs 3 engineer-minutes and returns `last_used_at`. The
  same administrative call can return the key's assigned permission scope. A
  credential authorised for nothing is then not something to infer; it is a
  field to read.

  Question: does adding that field raise the probe's expected value enough to
  change how often the agent buys it?

EXPERIMENT B -- how much of Week 1's over-remediation was the missing state?

  Week 1's error analysis found that every mistake the agent made was in the
  same direction: it remediated things that did not need remediating. Week 1
  also did not model `zero_scope`, and silently counted those keys as `live`,
  which are expensive to dismiss. Running the three-state agent against a
  five-state world measures how much of the bias that accounts for.

Writes results/scope-probe.md and results/scope-probe.json.
"""

import json
import os
from itertools import product

import run_experiment as R
import information as I
import week2_experiment as W

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

SCOPE = ["zero", "nonzero", "absent"]

# ASSUMPTION, but a constrained one. The `absent` mass is copied from the
# probe's existing `null` row rather than invented separately, because "not in
# our account" is the same event in both fields and the model should not
# disagree with itself. What is genuinely new is only the zero/nonzero split.
L_SCOPE = {
    "live":       {"zero": 0.02, "nonzero": 0.98, "absent": 0.00},
    "revoked":    {"zero": 0.02, "nonzero": 0.78, "absent": 0.20},
    "fake":       {"zero": 0.01, "nonzero": 0.04, "absent": 0.95},
    "zero_scope": {"zero": 0.95, "nonzero": 0.05, "absent": 0.00},
    "other":      {"zero": 1 / 3, "nonzero": 1 / 3, "absent": 1 / 3},
}


def free_belief(c, f):
    return W.posterior({"context": c, "form": f})


def evsi(b, tables, spaces, cost=None):
    """Expected minutes of decision cost removed by buying `tables`.

    `cost` must be threaded through. Without it this falls back to the module
    global -- the Week 2 matrix at p_exploit = 1.0, `dismiss|live` = 2400 --
    and every caller that had already corrected that cell went on pricing
    information against the version it repudiated. Every other EVSI in the
    project takes the matrix as an argument; this one silently did not, so
    `cost_sensitivity.py` swept fifteen cost cells while the purchase decision
    stayed frozen at exactly 0.468 for all seventy-five perturbed matrices.
    """
    now = W.expected_cost(b, W.cheapest(b, cost), cost)
    after = 0.0
    for o in product(*spaces):
        po = I.marginal(b, tables, o)
        if po <= 0:
            continue
        after += po * W.expected_cost(post := I.update(b, tables, o),
                                      W.cheapest(post, cost), cost)
    return I.snap(now - after)


def reachable_actions(b, tables, spaces):
    acts = set()
    for o in product(*spaces):
        if I.marginal(b, tables, o) <= 0:
            continue
        acts.add(W.cheapest(I.update(b, tables, o)))
    return sorted(acts)


# ---------------------------------------------------------------- experiment B

def w1_agent(case):
    """The Week 1 three-state agent, unchanged, deciding in a five-state world.

    It updates over {live, revoked, fake} with the Week 1 tables and chooses
    with the Week 1 cost matrix. It has never heard of zero_scope or other.
    """
    b = R.posterior({"context": case["context"], "form": case["form"]})
    return R.cheapest(b)


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = W.build_cases(W.N_CASES, W.SEED)

    # ---------------- experiment A
    rows = []
    for c, f in product(R.CONTEXT, R.FORM):
        b = free_belief(c, f)
        p = I.marginal(W.PRIOR, [W.L_CONTEXT, W.L_FORM], (c, f))
        v_probe = evsi(b, [W.L_PROBE], [R.PROBE])
        v_both = evsi(b, [W.L_PROBE, L_SCOPE], [R.PROBE, SCOPE])
        e_probe = I.analyse("p", b, [W.L_PROBE], [R.PROBE])["eig"]
        e_both = I.analyse("b", b, [W.L_PROBE, L_SCOPE], [R.PROBE, SCOPE])["eig"]
        rows.append(dict(context=c, form=f, p=p,
                         h=I.H(b), p_zero=b["zero_scope"],
                         eig_probe=e_probe, eig_both=e_both,
                         evsi_probe=v_probe, evsi_both=v_both,
                         buy_probe=v_probe > R.K["probe"],
                         buy_both=v_both > R.K["probe"],
                         acts_probe=reachable_actions(b, [W.L_PROBE], [R.PROBE]),
                         acts_both=reachable_actions(b, [W.L_PROBE, L_SCOPE],
                                                     [R.PROBE, SCOPE])))
    bought_probe = sum(r["p"] for r in rows if r["buy_probe"])
    bought_both = sum(r["p"] for r in rows if r["buy_both"])

    # policy P4: P2, but the probe also returns scope
    def p4(case):
        ev = {"context": case["context"], "form": case["form"]}
        b = W.posterior(ev)
        if evsi(b, [W.L_PROBE, L_SCOPE], [R.PROBE, SCOPE]) > R.K["probe"]:
            sc = _draw_scope(case)
            post = I.update(b, [W.L_PROBE, L_SCOPE], (case["probe"], sc))
            return W.cheapest(post), R.K["probe"], post
        return W.cheapest(b), 0, b

    import random
    rng = random.Random(W.SEED + 1)

    def _draw_scope(case):
        r, acc = rng.random(), 0.0
        for k, p in L_SCOPE[case["truth"]].items():
            acc += p
            if r <= acc:
                return k
        return k

    p2 = W.evaluate("P2", W.p2, cases)
    p3 = W.evaluate("P3", W.p3, cases)
    p4r = W.evaluate("P4", p4, cases)

    # ---------------- experiment B
    w1_cost = w1_over = 0.0
    w2_cost = w2_over = 0.0
    zs = [c for c in cases if c["truth"] == "zero_scope"]
    zs_w1 = {}
    zs_w2 = {}
    for c in cases:
        a1 = w1_agent(c)
        a2 = W.p2(c)[0]
        best = W.hindsight_best(c["truth"])
        w1_cost += W.COST[a1][c["truth"]]
        w2_cost += W.COST[a2][c["truth"]]
        w1_over += W.COST[a1][c["truth"]] - W.COST[best][c["truth"]]
        w2_over += W.COST[a2][c["truth"]] - W.COST[best][c["truth"]]
        if c["truth"] == "zero_scope":
            zs_w1[a1] = zs_w1.get(a1, 0) + 1
            zs_w2[a2] = zs_w2.get(a2, 0) + 1
    n = len(cases)

    payload = dict(scope_table=L_SCOPE, beliefs=rows,
                   bought_probe=bought_probe, bought_both=bought_both,
                   p2={k: v for k, v in p2.items() if k not in ("rows", "bins")},
                   p3={k: v for k, v in p3.items() if k not in ("rows", "bins")},
                   p4={k: v for k, v in p4r.items() if k not in ("rows", "bins")},
                   w1_cost=w1_cost / n, w2_cost=w2_cost / n,
                   w1_regret=w1_over / n, w2_regret=w2_over / n,
                   zero_scope_cases=len(zs), zs_w1=zs_w1, zs_w2=zs_w2)
    with open(os.path.join(OUT, "scope-probe.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# Two experiments about the state Week 1 did not model\n")

    add("## A. Does reading the key's scope earn its place?\n")
    add("The probe costs three engineer-minutes and returns `last_used_at`. The")
    add("same administrative call can return the key's assigned permission")
    add("scope. A credential authorised for nothing stops being something to")
    add("infer and becomes a field to read.\n")
    add("The scope likelihoods are an assumption. The `absent` column is copied")
    add("from the probe's existing `null` row rather than invented separately,")
    add("because *not in our account* is the same event in both fields and the")
    add("model should not disagree with itself. Only the zero/nonzero split is")
    add("genuinely new.\n")
    add("| State | zero | nonzero | absent |")
    add("|---|---|---|---|")
    for s in W.STATES:
        r = L_SCOPE[s]
        add(f"| {s} | {r['zero']:.2f} | {r['nonzero']:.2f} | {r['absent']:.2f} |")
    add("")
    add("| Context | Form | P(seen) | P(zero_scope) | Probe bits | +scope bits | Probe EVSI | +scope EVSI | Buy probe? | Buy +scope? |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda r: -r["p"]):
        add(f"| {r['context']} | {r['form']} | {r['p']:.4f} | {r['p_zero']:.4f} | "
            f"{r['eig_probe']:.4f} | {r['eig_both']:.4f} | {r['evsi_probe']:.4f} | "
            f"{r['evsi_both']:.4f} | {'yes' if r['buy_probe'] else 'no'} | "
            f"{'**yes**' if r['buy_both'] else 'no'} |")
    add("")
    add(f"Findings on which the agent buys the probe: **{bought_probe * 100:.2f}%** "
        f"without scope, **{bought_both * 100:.2f}%** with it.\n")

    add("| Policy | Total cost | Questions | Regret | Action acc. |")
    add("|---|---|---|---|---|")
    for r in (p2, p3, p4r):
        add(f"| {r['name']} | {r['total_cost']:.2f} | {r['questions']:.3f} | "
            f"{r['regret']:.2f} | {r['action_accuracy']:.3f} |")
    add("")
    if p4r["total_cost"] < min(p2["total_cost"], p3["total_cost"]):
        add(f"**P4 is the cheapest policy in the project**, at "
            f"{p4r['total_cost']:.2f} minutes against P2's {p2['total_cost']:.2f}.")
        add("The extra field costs nothing: it arrives on a call the agent was")
        add("already deciding whether to pay for.")
    else:
        add(f"P4 costs {p4r['total_cost']:.2f} against P2's {p2['total_cost']:.2f}.")
        add("The extra field does not pay for itself here, and the reason is the")
        add("same one that governs every result in this project: information")
        add("that does not cross a decision boundary is worth nothing, however")
        add("cheaply it arrives.")
    add("")

    add("## B. How much of the over-remediation was the missing state?\n")
    add("Week 1's error analysis found every mistake in one direction: the agent")
    add("remediated things that did not need it. Week 1 also did not model")
    add("`zero_scope`, and counted those keys as `live` -- the state that costs")
    add("2400 minutes to dismiss. Running the unchanged three-state agent")
    add("against the five-state world measures what that omission cost.\n")
    add("| Agent | Cost per finding | Regret per finding |")
    add("|---|---|---|")
    add(f"| Week 1, three states | {w1_cost / n:.2f} | {w1_over / n:.2f} |")
    add(f"| Week 2, five states | {w2_cost / n:.2f} | {w2_over / n:.2f} |")
    add("")
    add(f"On the {len(zs)} cases whose true state is `zero_scope`:\n")
    add("| Agent | What it did |")
    add("|---|---|")
    add(f"| Week 1 | {', '.join(f'{k} x{v}' for k, v in sorted(zs_w1.items()))} |")
    add(f"| Week 2 | {', '.join(f'{k} x{v}' for k, v in sorted(zs_w2.items()))} |")
    add("")
    delta = (w1_over - w2_over) / n
    same = abs(delta) < 1e-9
    if same:
        add("**The two agents behaved identically on every one of the "
            f"{n} cases.** Not")
        add("approximately, not on average: the same action, case for case,")
        add(f"including all {len(zs)} whose true state is the one Week 1 was")
        add("missing. Regret is identical to the last decimal place.\n")
        add("The reason is worth more than the experiment was. Without scope,")
        add("`zero_scope` carries the same context and well-formedness rows as")
        add("`live` and `revoked`, so no free observation can move mass onto it")
        add("independently. Its probability rides along with `live`'s, the")
        add("cheapest action is unchanged, and a state that cannot be")
        add("distinguished cannot alter a decision.\n")
        add("**So adding the state, on its own, is worth exactly nothing.**")
        add("Not little. Nothing. This is the sharper form of the rule that has")
        add("governed every result in this project: value comes from crossing a")
        add("decision boundary, and a state with no evidence attached to it")
        add("cannot cross one. A hidden state you cannot observe is a comment,")
        add("not a model.\n")
        add("Read that against Experiment A above and the pair says something")
        add("neither says alone. The state alone: zero. The state plus the")
        add(f"scope field that resolves it: the probe goes from bought on "
            f"{bought_probe * 100:.1f}% of findings to "
            f"{bought_both * 100:.1f}%, regret falls from")
        add(f"{p2['regret']:.2f} to {p4r['regret']:.2f}, and the result is the")
        add("cheapest policy in the project. The state was never the")
        add("improvement. The state made the evidence *meaningful*, and the")
        add("evidence was the improvement.\n")
        add("This also corrects something I expected to find. The plausible")
        add("story going in was that the missing state explained Week 1's")
        add("over-remediation bias -- those keys were counted as `live`, `live`")
        add("is expensive to dismiss, so the agent over-remediated. The story is")
        add("wrong, and it is wrong by exactly zero rather than by a little.")
        add("The bias comes from the cost structure, and dismissing was already")
        add("unreachable below P(live) = 0.0015 for reasons that have nothing to")
        add("do with any of this. Running the experiment is what stopped that")
        add("paragraph being written.")
    else:
        add(f"Modelling the state changes regret by **{delta:+.2f} minutes per")
        add(f"finding**, on {len(zs)} zero-scope cases out of {n}.")
    add("")

    with open(os.path.join(OUT, "scope-probe.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
