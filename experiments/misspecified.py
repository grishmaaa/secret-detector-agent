"""Week 2, commit 7: test the agent in a world that disagrees with it.

Every result in this project so far shares one weakness, and both Week 1's
findings and Section 25.2 of the brief name it: the cases are generated from
the agent's own likelihood tables. The agent is tested in a world that agrees
with it. That measures whether the POLICY is good given the model. It cannot
measure whether the model is any good, and it cannot tell you what happens when
it is wrong -- which it certainly is, because every number in it was estimated.

So: generate the world from DIFFERENT tables and leave the agent unchanged.

Three kinds of wrongness, because they fail differently:

  DRIFT      -- every likelihood row is perturbed by Dirichlet noise. Generic
                mis-estimation: the shape is right, the numbers are off.

  PRIOR      -- the world's base rates differ from the agent's. The agent's
                prior came from two sources measuring different populations,
                so this is the most likely error in practice.

  INVARIANCE -- the world's `live` and `revoked` rows genuinely DIFFER on the
                free features. This is the sharpest test available: the
                project's headline structural result is that they are
                identical, and here that claim is false and the agent does not
                know it.

Against each, two agents run on identical cases: ours, and one that knows the
true tables. The gap between them is the price of being wrong, separated from
the price of not knowing the state.

Writes results/misspecified.md and results/misspecified.json.
"""

import json
import os
import random
import statistics as st
from itertools import product

import run_experiment as R
import week2_experiment as W
import information as I
import scope_probe as S
import fixes as F

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

COST = F.costs()
PT = [W.L_PROBE, S.L_SCOPE]
PS = [R.PROBE, S.SCOPE]
SEEDS = 12
N = 500


# ---------------------------------------------------------------- worlds

def dirichlet(row, alpha, rng):
    """Sample a perturbed row. Large alpha = close to the original."""
    g = {k: rng.gammavariate(max(alpha * p, 1e-6), 1.0) for k, p in row.items()}
    t = sum(g.values())
    return {k: v / t for k, v in g.items()}


def make_world(mode, strength, rng):
    """Return (prior, context, form, probe, scope) as the world really is."""
    prior = dict(W.PRIOR)
    ctx = {s: dict(W.L_CONTEXT[s]) for s in W.STATES}
    frm = {s: dict(W.L_FORM[s]) for s in W.STATES}
    prb = {s: dict(W.L_PROBE[s]) for s in W.STATES}
    scp = {s: dict(S.L_SCOPE[s]) for s in W.STATES}

    if mode == "drift":
        for tab in (ctx, frm, prb, scp):
            for s in W.STATES:
                tab[s] = dirichlet(tab[s], strength, rng)
    elif mode == "prior":
        prior = dirichlet(prior, strength, rng)
    elif mode == "invariance":
        # the world separates live from revoked on context; the agent believes
        # the rows are identical and has proved a theorem on that basis
        d = strength
        ctx["live"] = {"placeholder": max(0.10 - d, 0.001),
                       "neutral": 0.30,
                       "production": 0.60 + d}
        ctx["revoked"] = {"placeholder": 0.10 + d, "neutral": 0.30,
                          "production": max(0.60 - d, 0.001)}
        for k in ("live", "revoked"):
            t = sum(ctx[k].values())
            ctx[k] = {a: b / t for a, b in ctx[k].items()}
    return prior, ctx, frm, prb, scp


def draw(table, s, rng):
    r, acc = rng.random(), 0.0
    for k, p in table[s].items():
        acc += p
        if r <= acc:
            return k
    return k


def make_cases(world, n, rng):
    prior, ctx, frm, prb, scp = world
    out = []
    for _ in range(n):
        r, acc, t = rng.random(), 0.0, W.STATES[-1]
        for s in W.STATES:
            acc += prior[s]
            if r <= acc:
                t = s
                break
        out.append(dict(truth=t, context=draw(ctx, t, rng), form=draw(frm, t, rng),
                        probe=draw(prb, t, rng), scope=draw(scp, t, rng)))
    return out


# ---------------------------------------------------------------- the agent

def run(cases, prior, ctx, frm, prb, scp, use_scope=True):
    """One agent, defined entirely by the tables it believes."""
    tabs = [prb, scp] if use_scope else [prb]
    spaces = PS if use_scope else [R.PROBE]
    regret = 0.0
    for c in cases:
        b = I.update(dict(prior), [ctx, frm], (c["context"], c["form"]))
        now = W.expected_cost(b, W.cheapest(b, COST), COST)
        after = 0.0
        for o in product(*spaces):
            po = I.marginal(b, tabs, o)
            if po <= 0:
                continue
            p = I.update(b, tabs, o)
            after += po * W.expected_cost(p, W.cheapest(p, COST), COST)
        if now - after > R.K["probe"]:
            obs = (c["probe"], c["scope"]) if use_scope else (c["probe"],)
            b = I.update(b, tabs, obs)
        a = W.cheapest(b, COST)
        if b["other"] > F.P_OTHER_TRIGGER:
            a = "escalate"
        elif max(COST[a][s] for s in W.STATES) > F.CEILING:
            a = "escalate"
        best = min(W.TERMINAL, key=lambda x: COST[x][c["truth"]])
        regret += COST[a][c["truth"]] - COST[best][c["truth"]]
    return regret / len(cases)


def always(cases, action):
    return sum(COST[action][c["truth"]]
               - COST[min(W.TERMINAL, key=lambda x: COST[x][c["truth"]])][c["truth"]]
               for c in cases) / len(cases)


AGENT = (W.PRIOR, W.L_CONTEXT, W.L_FORM, W.L_PROBE, S.L_SCOPE)


def trial(mode, strength, seed):
    rng = random.Random(seed)
    world = make_world(mode, strength, rng)
    cases = make_cases(world, N, rng)
    ours = run(cases, *AGENT)
    knows = run(cases, *world)
    noscope = run(cases, *AGENT, use_scope=False)
    return dict(ours=ours, knows=knows, gap=ours - knows,
                noscope=noscope, rotate=always(cases, "rotate"),
                scope_helps=ours < noscope, beats_rotate=ours < always(cases, "rotate"))


def main():
    os.makedirs(OUT, exist_ok=True)
    baseline = st.median(trial("drift", 1e9, s)["ours"] for s in range(SEEDS))

    settings = [("drift", a) for a in (200, 50, 20, 8)] + \
               [("prior", a) for a in (200, 50, 20)] + \
               [("invariance", d) for d in (0.02, 0.05, 0.10, 0.20)]

    rows = []
    for mode, strength in settings:
        ts = [trial(mode, strength, 1000 + s) for s in range(SEEDS)]
        rows.append(dict(
            mode=mode, strength=strength,
            ours=st.median(t["ours"] for t in ts),
            knows=st.median(t["knows"] for t in ts),
            gap=st.median(t["gap"] for t in ts),
            worst_gap=max(t["gap"] for t in ts),
            scope_helps=sum(t["scope_helps"] for t in ts) / len(ts),
            beats_rotate=sum(t["beats_rotate"] for t in ts) / len(ts)))

    payload = dict(baseline=baseline, seeds=SEEDS, n=N, rows=rows)
    with open(os.path.join(OUT, "misspecified.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# Testing the agent in a world that disagrees with it\n")
    add("Every result so far draws its cases from the agent's own likelihood")
    add("tables. That measures whether the policy is good given the model. It")
    add("says nothing about whether the model is any good, and nothing about")
    add("what happens when it is wrong -- which it is, because every number in")
    add("it was estimated.\n")
    add("So the world is generated from different tables and the agent is left")
    add("alone. Two agents run on identical cases: ours, and one that knows the")
    add("true tables. The gap is the price of being wrong, separated from the")
    add("price of not knowing the state.\n")
    add(f"Median over {SEEDS} seeds, {N} cases each. The agent's regret in a")
    add(f"world that agrees with it is **{baseline:.2f}** minutes per finding.\n")

    add("| Wrongness | Strength | Our agent | Agent that knows | Gap | Worst gap | Scope still helps | Still beats always-rotate |")
    add("|---|---|---|---|---|---|---|---|")
    labels = {"drift": "Dirichlet noise on every row (α)",
              "prior": "wrong base rates (α)",
              "invariance": "live/revoked really differ (δ)"}
    for r in rows:
        add(f"| {labels[r['mode']]} | {r['strength']} | {r['ours']:.2f} | "
            f"{r['knows']:.2f} | **{r['gap']:+.2f}** | {r['worst_gap']:+.2f} | "
            f"{r['scope_helps'] * 100:.0f}% | {r['beats_rotate'] * 100:.0f}% |")
    add("")
    add("Lower α is more perturbation; higher δ is a bigger real difference")
    add("between the two states the agent believes are identical.\n")

    drift = [r for r in rows if r["mode"] == "drift"]
    prior = [r for r in rows if r["mode"] == "prior"]
    inv = [r for r in rows if r["mode"] == "invariance"]

    add("## What survives\n")
    add("**Generic mis-estimation is cheap, and it degrades gracefully.** Under")
    add(f"Dirichlet noise the gap runs from {min(r['gap'] for r in drift):+.2f}")
    add(f"to {max(r['gap'] for r in drift):+.2f} minutes per finding as the")
    add("perturbation grows. At α = 8 -- every row substantially wrong -- the")
    add(f"agent still beats always-rotate in "
        f"{drift[-1]['beats_rotate'] * 100:.0f}% of worlds and reading scope")
    add(f"still helps in {drift[-1]['scope_helps'] * 100:.0f}%. The gap grows")
    add("smoothly with the error rather than falling off a cliff, which is the")
    add("property you want and is not guaranteed.\n")
    add("**Wrong likelihoods cost more than wrong base rates**, which is the")
    add("opposite of what I expected. The prior gap tops out at")
    add(f"{max(r['gap'] for r in prior):+.2f} against {max(r['gap'] for r in drift):+.2f}")
    add("for the likelihoods. The prior is the number I would have said was")
    add("most at risk -- it is assembled from two sources measuring different")
    add("populations -- and it turns out to be the one the agent is most")
    add("forgiving about. Free evidence washes a wrong prior out; nothing")
    add("washes out a wrong likelihood, because the likelihood is what does the")
    add("washing.\n")
    add("One caution on reading those prior rows. The agent's absolute regret")
    add(f"*falls* as the prior is perturbed ({prior[0]['ours']:.2f} down to "
        f"{prior[-1]['ours']:.2f}), because some perturbed worlds are simply")
    add("easier than the real one. The gap against an agent that knows the")
    add("truth is the measure that means anything here; the absolute column is")
    add("not comparable across rows.\n")
    add("## The test that matters\n")
    add("The invariance rows are the sharp ones. The project's headline")
    add("structural result is that `live` and `revoked` carry identical")
    add("free-feature rows, so the mutual information between them is exactly")
    add("zero. In these worlds that is false: the two states really do differ,")
    add("the free evidence really does carry signal about the axis, and the")
    add("agent has proved a theorem saying otherwise and acts on it.\n")
    add("| δ | Our agent | Agent that knows | What the agent leaves on the table |")
    add("|---|---|---|---|")
    for r in inv:
        add(f"| {r['strength']:.2f} | {r['ours']:.2f} | {r['knows']:.2f} | "
            f"{r['gap']:+.2f} |")
    add("")
    worst = max(inv, key=lambda r: r["gap"])
    add(f"At δ = {worst['strength']:.2f} -- a substantial real difference --")
    add(f"the agent forgoes {worst['gap']:.2f} minutes per finding by refusing")
    add("to look for a signal that is there. The failure is silent: nothing in")
    add("the agent's own diagnostics can detect it, because the invariance is")
    add("an assumption about the likelihood tables rather than an observation,")
    add("and the agent never observes its own tables being wrong.\n")
    add("**That is the honest limitation of the whole project, stated with a")
    add("number attached.** The zero-bits result is exact given the tables and")
    add("worth nothing if the tables are wrong, and the only way to find out is")
    add("to measure the likelihoods against real labelled findings, which is")
    add("the one thing this project has never been able to do.\n")

    add("## Conclusions that hold, and the one that does not\n")
    add("| Claim | Verdict under mis-specification |")
    add("|---|---|")
    allr = rows
    add(f"| The agent beats always-rotate | holds in "
        f"{min(r['beats_rotate'] for r in allr) * 100:.0f}–"
        f"{max(r['beats_rotate'] for r in allr) * 100:.0f}% of worlds |")
    add(f"| Reading scope helps | holds in "
        f"{min(r['scope_helps'] for r in allr) * 100:.0f}–"
        f"{max(r['scope_helps'] for r in allr) * 100:.0f}% of worlds |")
    add(f"| Free features carry zero bits about live vs revoked | **fails "
        "whenever the world says otherwise, undetectably** |")
    add("")
    add("The policy conclusions are robust to the model being wrong. The")
    add("structural conclusion is not, and cannot be, because it is a statement")
    add("about the model rather than about the world. Both belong in the paper,")
    add("and only one of them should be stated as a finding about secret")
    add("scanning rather than as a finding about this model of it.")
    add("")

    with open(os.path.join(OUT, "misspecified.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
