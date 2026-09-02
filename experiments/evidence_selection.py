"""Week 2, commit 2: which evidence is worth obtaining.

W2-1 measured what each evidence source is worth in bits. This asks the
question the agent actually faces, which is different: what is each source
worth in engineer-minutes, and is it worth what it costs?

The two rankings do not agree, and that disagreement is the point.

Reuses the Week 1 cost matrix and the W2-1 information machinery. Nothing is
re-parameterised.

Writes results/evidence-selection.md and results/evidence-selection.json.
"""

import json
import os
from itertools import product

import run_experiment as R
import information as I

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

MIN = "min"   # engineer-minutes, the unit everything is priced in


# ------------------------------------------------------------------ value

def expected_cost(belief, action):
    return sum(belief[s] * R.COST[action][s] for s in belief)


def best(belief):
    """Cheapest terminal action, and what it costs."""
    a = min(R.TERMINAL, key=lambda a: expected_cost(belief, a))
    return a, expected_cost(belief, a)


def evsi(belief, tables, spaces):
    """Expected value of sample information, in engineer-minutes.

    What the decision costs now, minus what it would cost on average once the
    evidence has arrived. This is the honest pre-posterior number: it averages
    over outcomes we have not seen yet, weighted by how likely each is.
    """
    _, now = best(belief)
    after = 0.0
    for outcome in product(*spaces):
        po = I.marginal(belief, tables, outcome)
        if po <= 0:
            continue
        post = I.update(belief, tables, outcome)
        after += po * best(post)[1]
    return now - after


def action_changes(belief, tables, spaces):
    """Does any outcome of this evidence change what the agent would do?

    This is the brief's decisive test, and it is not the same as carrying
    information. Returns the set of actions reachable across all outcomes.
    """
    base = best(belief)[0]
    acts = set()
    for outcome in product(*spaces):
        if I.marginal(belief, tables, outcome) <= 0:
            continue
        acts.add(best(I.update(belief, tables, outcome))[0])
    return base, acts, (acts != {base})


# ------------------------------------------------------------------ sources

def sources():
    """The three evidence sources the agent actually has, with real costs.

    Time is wall-clock; cost is engineer-minutes, which is what the model
    prices. They differ: the probe is a fast API call whose cost is the
    engineer's attention around it, not its latency.
    """
    return [
        dict(key="context", label="Repository context (path, name, commit message)",
             tables=[R.L_CONTEXT], spaces=[R.CONTEXT],
             cost=0.0, time="seconds, automated",
             wrong="A production-looking path around a fixture, or a fixture "
                   "path in a repository that deploys from tests"),
        dict(key="form", label="Well-formedness (format match)",
             tables=[R.L_FORM], spaces=[R.FORM],
             cost=0.0, time="milliseconds, regex",
             wrong="An organisation that commits base-encoded real credentials "
                   "by convention inverts this feature rather than weakening it"),
        dict(key="probe", label="Probe: last_used_at from our own admin API",
             tables=[R.L_PROBE], spaces=[R.PROBE],
             cost=float(R.K["probe"]), time="one API call plus the engineer around it",
             wrong="A live key that has been idle for months looks like a dead "
                   "one; the field is silence, and silence is not death"),
    ]


UNPRICED = [
    dict(label="Secret-store hash comparison",
         cost="under 1 min", time="one lookup",
         why="Compare a hash of the finding against the current stored value. "
             "Dispositive when it hits. Absence is uninformative rather than "
             "favourable, because a credential created outside the provisioning "
             "pipeline is absent and may still authenticate."),
    dict(label="expires_at from the same admin call",
         cost="0 additional min", time="already paid for",
         why="Arrives on the call already priced at 3 minutes, and an expiry in "
             "the past is deterministic where last_used_at is only suggestive. "
             "Strictly more information at strictly no extra cost."),
]


# ------------------------------------------------------------------ report

def main():
    os.makedirs(OUT, exist_ok=True)
    prior = dict(R.PRIOR)
    pair = ["live", "revoked"]
    b2 = I.restrict(prior, pair)

    rows = []
    for s in sources():
        info = I.analyse(s["label"], prior, s["tables"], s["spaces"])
        t2 = [{k: t[k] for k in pair} for t in s["tables"]]
        axis = I.analyse(s["label"], b2, t2, s["spaces"])
        v = evsi(prior, s["tables"], s["spaces"])
        base, acts, changed = action_changes(prior, s["tables"], s["spaces"])
        v = I.snap(v)
        rows.append(dict(key=s["key"], label=s["label"], cost=s["cost"],
                         time=s["time"], wrong=s["wrong"],
                         eig=info["eig"], eig_axis=axis["eig"], evsi=v,
                         base_action=base, actions=sorted(acts),
                         changes_action=changed,
                         bits_per_min=(None if s["cost"] == 0 else info["eig"] / s["cost"]),
                         value_ratio=(None if s["cost"] == 0 else v / s["cost"])))

    # the probe, evaluated where the agent actually stands rather than at the prior
    per_belief = []
    for c, f in product(R.CONTEXT, R.FORM):
        po = I.marginal(prior, [R.L_CONTEXT, R.L_FORM], (c, f))
        b = I.update(prior, [R.L_CONTEXT, R.L_FORM], (c, f))
        info = I.analyse("probe", b, [R.L_PROBE], [R.PROBE])
        v = evsi(b, [R.L_PROBE], [R.PROBE])
        base, acts, changed = action_changes(b, [R.L_PROBE], [R.PROBE])
        per_belief.append(dict(context=c, form=f, p=po, h=I.H(b),
                               eig=info["eig"], evsi=I.snap(v),
                               base_action=base, actions=sorted(acts),
                               changes_action=changed,
                               buy=v > R.K["probe"]))

    payload = dict(prior=prior, sources=rows, probe_by_belief=per_belief,
                   probe_price=R.K["probe"])
    with open(os.path.join(OUT, "evidence-selection.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# Which evidence is worth obtaining\n")
    add("W2-1 asked what each source is worth in bits. This asks what each is")
    add("worth in engineer-minutes. The two answers rank the sources")
    add("differently, and the disagreement is the finding.\n")

    add("## The comparison table\n")
    add("| Evidence | Exp. gain (bits) | Bits about live-vs-revoked | Cost | Time | EVSI (min) | Can it change the action? | If it is wrong |")
    add("|---|---|---|---|---|---|---|---|")
    for r in rows:
        cost = "free" if r["cost"] == 0 else f"{r['cost']:.0f} min"
        add(f"| {r['label']} | {r['eig']:.4f} | {r['eig_axis']:.4f} | {cost} | "
            f"{r['time']} | {r['evsi']:.4f} | "
            f"{'yes' if r['changes_action'] else '**no**'} | {r['wrong']} |")
    add("")
    add("EVSI is measured at the prior, before anything has been observed. The")
    add("probe is measured again below at each belief the agent can actually")
    add("hold, which is the number that governs whether it gets bought.\n")

    ranked_bits = sorted(rows, key=lambda r: -r["eig"])
    ranked_val = sorted(rows, key=lambda r: -r["evsi"])
    add("## The two rankings\n")
    add("| Rank | By bits | By minutes saved |")
    add("|---|---|---|")
    for i, (a, b) in enumerate(zip(ranked_bits, ranked_val), 1):
        add(f"| {i} | {a['label'].split('(')[0].strip()} ({a['eig']:.4f} bits) | "
            f"{b['label'].split('(')[0].strip()} ({b['evsi']:.4f} min) |")
    add("")

    probe = [r for r in rows if r["key"] == "probe"][0]
    ctx = [r for r in rows if r["key"] == "context"][0]
    add(f"The probe is the most informative source in the table — "
        f"{probe['eig']:.4f} bits, and the only one carrying anything at all")
    add("about live versus revoked. It is also the only one that costs money.")
    add(f"Repository context carries {ctx['eig']:.4f} bits, less than the probe,")
    add("and carries exactly none of them about the axis the decision turns on —")
    add("yet it is free, so its value per minute spent is unbounded and it")
    add("should always be read first. Order follows from cost, not from bits.\n")

    add("## Evidence I can name but cannot price\n")
    add("Two channels came out of the practitioner discussions and are not in")
    add("the model. I am listing them without bits, deliberately: I have no")
    add("likelihood tables for them, and inventing tables so that they could")
    add("appear in the comparison would produce numbers that look measured and")
    add("are not. **You cannot price evidence you have not modelled**, and the")
    add("honest form of that is an empty cell rather than a plausible one.\n")
    add("| Channel | Cost | Time | Why it matters |")
    add("|---|---|---|---|")
    for u in UNPRICED:
        add(f"| {u['label']} | {u['cost']} | {u['time']} | {u['why']} |")
    add("")

    add("## The critical question: is the most informative check always the best one?\n")
    add("No, and this model answers it twice, in opposite directions.\n")

    form = [r for r in rows if r["key"] == "form"][0]
    add("### Case one — where bits and value agree\n")
    add("Compare the two free features against each other. Well-formedness")
    add(f"carries {form['eig']:.4f} bits against repository context's")
    add(f"{ctx['eig']:.4f}, and it is also worth more: {form['evsi']:.4f} minutes")
    add(f"against {ctx['evsi']:.4f}. Ranking those two by bits gives the right")
    add("answer, because a malformed string collapses *fake* hard enough to")
    add("cross a decision boundary, and the movement and the crossing happen")
    add("together. When evidence moves a belief across a line, more movement is")
    add("more value and the two rankings coincide.\n")

    changed = [p for p in per_belief if p["changes_action"]]
    unchanged = [p for p in per_belief if not p["changes_action"]]
    add("### Case two — it is not\n")
    add("Now ask where the agent actually stands. After the free features it")
    add("holds one of six beliefs. The probe is worth its price in exactly one")
    add("of them, and the ordering by bits is close to the reverse of the")
    add("ordering by value.\n")
    add("| Context | Form | P(seen) | Entropy | Probe bits | Probe EVSI (min) | Action now | Actions reachable | Buy at 3 min? |")
    add("|---|---|---|---|---|---|---|---|---|")
    for p in sorted(per_belief, key=lambda p: -p["p"]):
        add(f"| {p['context']} | {p['form']} | {p['p']:.4f} | {p['h']:.4f} | "
            f"{p['eig']:.4f} | {p['evsi']:.4f} | {p['base_action']} | "
            f"{', '.join(p['actions'])} | {'**yes**' if p['buy'] else 'no'} |")
    add("")
    by_bits = sorted(per_belief, key=lambda p: -p["eig"])
    by_val = sorted(per_belief, key=lambda p: -p["evsi"])
    add("| Rank | Most bits | Most minutes saved |")
    add("|---|---|---|")
    for i, (a, b) in enumerate(zip(by_bits, by_val), 1):
        add(f"| {i} | {a['context']}+{a['form']} ({a['eig']:.4f} bits) | "
            f"{b['context']}+{b['form']} ({b['evsi']:.4f} min) |")
    add("")
    add("**The two orderings are almost exactly reversed.** The belief where the")
    add("probe carries the most information is the one where it is worth")
    add("nothing, and the belief where it carries the least is the one where it")
    add("is worth the most. This is not a coincidence in the arithmetic: a")
    add("belief with high entropy is one where the agent is unsure *among")
    add("states*, and a belief near a boundary is one where it is unsure *among")
    add("actions*. Those are different kinds of doubt, and only the second one")
    add("is worth money.\n")
    if unchanged:
        u = max(unchanged, key=lambda p: p["eig"])
        add(f"Read the row `{u['context']} + {u['form']}`. The probe carries")
        add(f"**{u['eig']:.4f} bits** there — real information, more than either")
        add("free feature carries anywhere — and its value is")
        add(f"**{u['evsi']:.4f} minutes**, because no outcome of it changes what")
        add(f"the agent does. Every branch still ends in `{u['base_action']}`.")
        add("")
        add("So the agent would pay three minutes to become measurably better")
        add("informed and then take the action it was already going to take. The")
        add("information is real. The value is zero. Buying it is a pure loss of")
        add(f"{R.K['probe']:.0f} minutes.\n")
    add("**The rule that falls out.** Bits measure how much a belief moves.")
    add("Value measures whether the movement crosses a line that matters. A")
    add("belief can travel a long way inside one decision region and arrive")
    add("nowhere. Before buying evidence the question is not *how much will I")
    add("learn* but *is there an answer to this that would make me act")
    add("differently* — and if there is not, the price of the check is the whole")
    add("of its cost and none of its benefit, however many bits it carries.\n")

    add("## Why this matters more here than in most problems\n")
    add(f"The agent's decision boundary sits at P(live) = 0.06588, and the")
    add("cheapest remediation is tolerable in every state. That combination")
    add("makes the decision region enormous: almost every belief the agent can")
    add("reach falls inside it, so almost every piece of evidence moves the")
    add("belief without moving the decision. A problem with a boundary near 0.5")
    add("would buy evidence far more often. **The value of information is a")
    add("property of the cost matrix, not of the evidence.**")
    add("")

    with open(os.path.join(OUT, "evidence-selection.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print("\nWrote results/evidence-selection.md and .json")


if __name__ == "__main__":
    main()
