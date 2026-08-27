"""
Section 9 experiment.

Four policies and one baseline, on the same forty findings.

    baseline  escalate everything, the procedure a team actually runs today
    P0        no evidence at all, act on the prior
    P1        free evidence, then the obvious rule: rotate if P(live) > 0.5
    P2        free evidence, then whichever action is cheapest in expectation
    P3        P2, plus buy the probe when it is worth more than it costs

Everything is priced in engineer-minutes. Two numbers are reported for each
policy: the exact expected cost, which is computable in closed form because
there are only six possible pieces of free evidence, and the realised cost on
the frozen forty-case sample, which is what a run actually costs and carries
the sampling noise that goes with forty draws.

Run:  python run_experiment.py
"""

import json
import os
import random
from itertools import product

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "..", "data", "cases.json")
RESULTS = os.path.join(HERE, "..", "results")
SEED = 20260827
N_CASES = 40

# ---------------------------------------------------------------- the model

STATES = ["live", "revoked", "fake"]

PRIOR = {"live": 0.48, "revoked": 0.27, "fake": 0.25}

CONTEXT = ["placeholder", "neutral", "production"]
FORM = ["well-formed", "malformed"]
PROBE = ["recent", "old", "null"]

# P(context | state) -- live and revoked are identical, deliberately
L_CONTEXT = {
    "live":    {"placeholder": 0.10, "neutral": 0.30, "production": 0.60},
    "revoked": {"placeholder": 0.10, "neutral": 0.30, "production": 0.60},
    "fake":    {"placeholder": 0.70, "neutral": 0.25, "production": 0.05},
}

# P(form | state) -- also identical for live and revoked
L_FORM = {
    "live":    {"well-formed": 0.99, "malformed": 0.01},
    "revoked": {"well-formed": 0.99, "malformed": 0.01},
    "fake":    {"well-formed": 0.40, "malformed": 0.60},
}

# P(last_used_at | state) -- the only feature that separates live from revoked
L_PROBE = {
    "live":    {"recent": 0.60, "old": 0.20, "null": 0.20},
    "revoked": {"recent": 0.02, "old": 0.78, "null": 0.20},
    "fake":    {"recent": 0.01, "old": 0.04, "null": 0.95},
}

# engineer-minutes
COST = {
    "dismiss":  {"live": 2400, "revoked":  2, "fake":  2},
    "escalate": {"live":  150, "revoked": 30, "fake": 30},
    "revoke":   {"live":  330, "revoked":  2, "fake":  5},
    "rotate":   {"live":  120, "revoked": 30, "fake": 20},
}

# Four actions are terminal and compete on expected cost. Investigate is not
# terminal -- it buys an answer and then the agent decides again -- so it is
# never in this list and is compared separately, on whether what it buys is
# worth more than what it costs.
TERMINAL = ["dismiss", "escalate", "revoke", "rotate"]

PROBE_COST = 3          # one minute a call, three calls, per two practitioners
NAIVE_THRESHOLD = 0.5   # what P1 uses, because "more likely than not" is obvious

# ---------------------------------------------------------------- machinery


def normalise(d):
    total = sum(d.values())
    return {k: v / total for k, v in d.items()}


def posterior(evidence):
    """evidence is a dict of feature -> value, using only what has been seen."""
    unnorm = {}
    for s in STATES:
        p = PRIOR[s]
        if "context" in evidence:
            p *= L_CONTEXT[s][evidence["context"]]
        if "form" in evidence:
            p *= L_FORM[s][evidence["form"]]
        if "probe" in evidence:
            p *= L_PROBE[s][evidence["probe"]]
        unnorm[s] = p
    return normalise(unnorm)


def expected_cost(belief, action):
    return sum(belief[s] * COST[action][s] for s in STATES)


def cheapest(belief):
    return min(TERMINAL, key=lambda a: expected_cost(belief, a))


def evsi(belief, evidence):
    """What the probe is worth here, before paying for it."""
    now = expected_cost(belief, cheapest(belief))
    after = 0.0
    for outcome in PROBE:
        p_outcome = sum(belief[s] * L_PROBE[s][outcome] for s in STATES)
        if p_outcome <= 0:
            continue
        post = posterior(dict(evidence, probe=outcome))
        after += p_outcome * expected_cost(post, cheapest(post))
    return now - after


# ---------------------------------------------------------------- policies
#
# Each policy takes a case and returns (action, extra_minutes_spent).
# extra_minutes is the probe fee, paid whether or not it changes anything.


def policy_baseline(case):
    return "escalate", 0


def policy_p0(case):
    return cheapest(PRIOR), 0


def policy_p1(case):
    ev = {"context": case["context"], "form": case["form"]}
    b = posterior(ev)
    return ("rotate" if b["live"] > NAIVE_THRESHOLD else "dismiss"), 0


def policy_p2(case):
    ev = {"context": case["context"], "form": case["form"]}
    return cheapest(posterior(ev)), 0


def policy_p3(case):
    ev = {"context": case["context"], "form": case["form"]}
    b = posterior(ev)
    if evsi(b, ev) > PROBE_COST:
        ev = dict(ev, probe=case["probe"])
        return cheapest(posterior(ev)), PROBE_COST
    return cheapest(b), 0


POLICIES = [
    ("baseline", "escalate everything", policy_baseline),
    ("P0", "prior only, no evidence", policy_p0),
    ("P1", "evidence, threshold 0.5", policy_p1),
    ("P2", "evidence, cost-derived", policy_p2),
    ("P3", "P2 plus the probe", policy_p3),
]

# ---------------------------------------------------------------- exact answer


def exact(policy_fn):
    """Expected cost and escalation rate, summed over every possible world.

    There are three states times three contexts times two forms times three
    probe outcomes. Fifty-four terms, so this is exact rather than estimated.
    """
    total = 0.0
    escalations = 0.0
    probes = 0.0
    for s, c, f, pr in product(STATES, CONTEXT, FORM, PROBE):
        p = (PRIOR[s] * L_CONTEXT[s][c] * L_FORM[s][f] * L_PROBE[s][pr])
        action, extra = policy_fn({"context": c, "form": f, "probe": pr})
        total += p * (COST[action][s] + extra)
        if action == "escalate":
            escalations += p
        if extra:
            probes += p
    return total, escalations, probes


# ---------------------------------------------------------------- case set


def build_cases(n, seed):
    rng = random.Random(seed)

    def draw(table, state):
        r, acc = rng.random(), 0.0
        for value, p in table[state].items():
            acc += p
            if r < acc:
                return value
        return value

    cases = []
    for i in range(n):
        r, acc = rng.random(), 0.0
        for s in STATES:
            acc += PRIOR[s]
            if r < acc:
                state = s
                break
        cases.append({
            "id": i + 1,
            "true_state": state,
            "context": draw(L_CONTEXT, state),
            "form": draw(L_FORM, state),
            "probe": draw(L_PROBE, state),
        })
    return cases


def load_cases():
    """Frozen on first run. The generator draws from the same likelihood tables
    the agent reasons with, so the agent is being tested on a world that agrees
    with its own assumptions. That is a real limitation and it is why the file
    is written once and then never regenerated."""
    if os.path.exists(CASES):
        with open(CASES) as fh:
            return json.load(fh)
    cases = build_cases(N_CASES, SEED)
    os.makedirs(os.path.dirname(CASES), exist_ok=True)
    with open(CASES, "w") as fh:
        json.dump(cases, fh, indent=2)
    return cases


# ---------------------------------------------------------------- sweeps


def sweep(label, values, apply_fn):
    print(f"\n{label}")
    header = f"{'value':>10s} " + " ".join(f"{n:>9s}" for n, _, _ in POLICIES)
    print(header)
    print("-" * len(header))
    saved = json.dumps([COST, PRIOR, {"probe": PROBE_COST}])
    for v in values:
        apply_fn(v)
        row = [exact(fn)[0] for _, _, fn in POLICIES]
        print(f"{v:>10} " + " ".join(f"{c:9.1f}" for c in row))
    c, p, pc = json.loads(saved)
    COST.update(c)
    PRIOR.update(p)
    globals()["PROBE_COST"] = pc["probe"]


def main():
    cases = load_cases()
    counts = {s: sum(1 for c in cases if c["true_state"] == s) for s in STATES}

    print("=" * 74)
    print("SECTION 9 -- four policies against escalate-everything")
    print("=" * 74)
    print(f"\n{len(cases)} frozen cases, seed {SEED}: "
          + ", ".join(f"{counts[s]} {s}" for s in STATES))
    print(f"probe priced at {PROBE_COST} min; P1 threshold {NAIVE_THRESHOLD}")

    print("\n--- exact expected cost per finding, engineer-minutes ---\n")
    print(f"{'':9s} {'policy':26s} {'cost':>8s} {'vs base':>9s} "
          f"{'human':>7s} {'probed':>7s}")
    base = exact(policy_baseline)[0]
    exact_rows = {}
    for name, desc, fn in POLICIES:
        cost, esc, prb = exact(fn)
        exact_rows[name] = cost
        delta = "--" if name == "baseline" else f"{(cost/base - 1)*100:+.1f}%"
        print(f"{name:9s} {desc:26s} {cost:8.2f} {delta:>9s} "
              f"{esc*100:6.1f}% {prb*100:6.1f}%")

    print("\n--- realised cost on the forty cases, total minutes ---\n")
    print(f"{'':9s} {'total':>8s} {'per case':>9s} {'vs base':>9s} "
          f"{'human':>7s} {'worst single case':>20s}")
    base_total = sum(COST[policy_baseline(c)[0]][c["true_state"]] for c in cases)
    for name, desc, fn in POLICIES:
        total = 0
        esc = 0
        worst = (0, None, None)
        for c in cases:
            a, extra = fn(c)
            paid = COST[a][c["true_state"]] + extra
            total += paid
            if a == "escalate":
                esc += 1
            if paid > worst[0]:
                worst = (paid, a, c["true_state"])
        delta = "--" if name == "baseline" else f"{(total/base_total - 1)*100:+.1f}%"
        w = f"{worst[0]} ({worst[1]} a {worst[2]})"
        print(f"{name:9s} {total:8d} {total/len(cases):9.2f} {delta:>9s} "
              f"{esc*100//len(cases):6.0f}% {w:>20s}")

    print("\n--- where each policy sends each kind of finding ---\n")
    for name, desc, fn in POLICIES:
        if name == "baseline":
            continue
        picks = {}
        for c, f in product(CONTEXT, FORM):
            a, extra = fn({"context": c, "form": f, "probe": "old"})
            picks.setdefault(a + ("*" if extra else ""), []).append(f"{c[:4]}/{f[:4]}")
        print(f"{name:9s} " + "  ".join(
            f"{a}: {len(v)}/6" for a, v in sorted(picks.items())))
    print("\n           * = probe bought first")

    # ------------------------------------------------------------ sweeps

    print("\n" + "=" * 74)
    print("SENSITIVITY -- exact expected cost per finding")
    print("=" * 74)

    def set_dismiss(v):
        COST["dismiss"]["live"] = v

    def set_prior(v):
        rest = 1 - PRIOR["fake"]
        PRIOR["live"], PRIOR["revoked"] = rest * v, rest * (1 - v)

    def set_probe(v):
        globals()["PROBE_COST"] = v

    def set_outage(v):
        COST["revoke"]["live"] = 92 + v      # 2 revoke + 30 find + 60 deploy

    sweep("dismissing a live key costs...", [240, 600, 1200, 2400, 6000, 24000],
          set_dismiss)
    sweep("share of not-fake keys that are live...",
          [0.40, 0.50, 0.64, 0.70, 0.80], set_prior)
    sweep("the probe costs...", [1, 2, 3, 5, 10, 20], set_probe)
    sweep("an outage costs...", [0, 60, 120, 240, 480], set_outage)

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "summary.json"), "w") as fh:
        json.dump({"exact_expected_cost": exact_rows,
                   "n_cases": len(cases), "seed": SEED,
                   "probe_cost": PROBE_COST}, fh, indent=2)
    print(f"\nWrote results/summary.json and data/cases.json")


if __name__ == "__main__":
    main()
