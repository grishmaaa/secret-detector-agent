"""
Section 9 experiment.

Policies compared on the same findings:

    baseline  escalate everything
    P0        no evidence at all, act on the prior
    P1        free evidence, hand-picked thresholds, all four terminal actions
    P1-trunc  the original P1: threshold 0.5 over {rotate, dismiss} only
    P2        free evidence, whichever action is cheapest in expectation
    P3        P2, plus buy the probe when it is worth more than it costs

Corrections applied after review:

  * Cost cells are now the exact component sums (112, 332), not rounded to
    120 and 330. The rounded and unrounded versions disagreed with each other
    in different sections of the paper.
  * Escalate is defined as 30 + the cost of the best terminal action in that
    state, which is what the prose always claimed: 142 / 32 / 32.
  * Decision boundaries and the VPI bound are reported on the REACHABLE line.
    The free features lock P(live):P(revoked) at 1.778, so the agent never
    occupies the prior-ratio slice the earlier numbers were computed on.
  * P1 is reported both as originally written and with the full action set,
    because the original confounded the threshold with a truncated action set.

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

L_CONTEXT = {
    "live":    {"placeholder": 0.10, "neutral": 0.30, "production": 0.60},
    "revoked": {"placeholder": 0.10, "neutral": 0.30, "production": 0.60},
    "fake":    {"placeholder": 0.70, "neutral": 0.25, "production": 0.05},
}
L_FORM = {
    "live":    {"well-formed": 0.99, "malformed": 0.01},
    "revoked": {"well-formed": 0.99, "malformed": 0.01},
    "fake":    {"well-formed": 0.40, "malformed": 0.60},
}
L_PROBE = {
    "live":    {"recent": 0.60, "old": 0.20, "null": 0.20},
    "revoked": {"recent": 0.02, "old": 0.78, "null": 0.20},
    "fake":    {"recent": 0.01, "old": 0.04, "null": 0.95},
}

# --- cost components, engineer-minutes -------------------------------------
K = dict(revoke=2, issue=10, probe=3, human=30,
         find_documented=30, deploy=60, verify=10, outage=240)

def build_costs():
    """Every live-column cell is a component sum. No rounding."""
    c = {
        "dismiss": {"live": 2400, "revoked": 2, "fake": 2},
        "revoke":  {"live": K["revoke"] + K["outage"] + K["find_documented"] + K["deploy"],
                    "revoked": 2, "fake": 5},
        "rotate":  {"live": K["issue"] + K["find_documented"] + K["deploy"]
                            + K["verify"] + K["revoke"],
                    "revoked": 30, "fake": 20},
    }
    # escalate = human attention + whatever the human then correctly does
    c["escalate"] = {s: K["human"] + min(c[a][s] for a in ("dismiss", "revoke", "rotate"))
                     for s in STATES}
    return c

COST = build_costs()
TERMINAL = ["dismiss", "escalate", "revoke", "rotate"]

RATIO = PRIOR["live"] / PRIOR["revoked"]   # 1.7778, locked by the free features

# ---------------------------------------------------------------- machinery


def normalise(d):
    t = sum(d.values())
    return {k: v / t for k, v in d.items()}


def posterior(ev):
    u = {}
    for s in STATES:
        p = PRIOR[s]
        if "context" in ev: p *= L_CONTEXT[s][ev["context"]]
        if "form" in ev:    p *= L_FORM[s][ev["form"]]
        if "probe" in ev:   p *= L_PROBE[s][ev["probe"]]
        u[s] = p
    return normalise(u)


def expected_cost(b, a):
    return sum(b[s] * COST[a][s] for s in STATES)


def cheapest(b):
    return min(TERMINAL, key=lambda a: expected_cost(b, a))


def evsi(b, ev):
    now = expected_cost(b, cheapest(b))
    after = 0.0
    for o in PROBE:
        po = sum(b[s] * L_PROBE[s][o] for s in STATES)
        if po <= 0:
            continue
        post = posterior(dict(ev, probe=o))
        after += po * expected_cost(post, cheapest(post))
    return now - after


def vpi(b):
    """What a perfect oracle would be worth here. Upper bound on any human."""
    return expected_cost(b, cheapest(b)) - sum(
        b[s] * min(COST[a][s] for a in TERMINAL) for s in STATES)


def reachable_beliefs():
    """The six posteriors the agent can hold after free evidence, with the
    probability of seeing each."""
    out = []
    for c, f in product(CONTEXT, FORM):
        u = {s: PRIOR[s] * L_CONTEXT[s][c] * L_FORM[s][f] for s in STATES}
        out.append((c, f, sum(u.values()), normalise(u)))
    return out


def boundaries_on_reachable_line(steps=400_000):
    """Where the cheapest action changes, walking the line the agent is
    confined to: P(live):P(revoked) fixed at RATIO, fake taking the rest."""
    out, prev = [], None
    for i in range(steps + 1):
        pl = i / steps
        pr = pl / RATIO
        pf = 1 - pl - pr
        if pf < 0:
            break
        a = cheapest({"live": pl, "revoked": pr, "fake": pf})
        if a != prev:
            if prev is not None:
                out.append((prev, a, pl))
            prev = a
    return out


# ---------------------------------------------------------------- policies

NAIVE_HI = 0.5     # "more likely than not" -- what an engineer reaches for
NAIVE_LO = 0.05    # "basically nothing" -- the other hand-picked cut

def policy_baseline(case): return "escalate", 0
def policy_p0(case):       return cheapest(PRIOR), 0

def policy_p1(case):
    """Hand-picked thresholds, but the SAME four actions P2 may use."""
    b = posterior({"context": case["context"], "form": case["form"]})
    pl = b["live"]
    if pl < NAIVE_LO:  return "dismiss", 0
    if pl < NAIVE_HI:  return "revoke", 0
    return "rotate", 0

def policy_p1_trunc(case):
    """The original P1: 0.5 threshold over {rotate, dismiss} only. Kept so the
    confound is visible rather than silently corrected."""
    b = posterior({"context": case["context"], "form": case["form"]})
    return ("rotate" if b["live"] > NAIVE_HI else "dismiss"), 0

def policy_p2(case):
    return cheapest(posterior({"context": case["context"], "form": case["form"]})), 0

def policy_p3(case):
    ev = {"context": case["context"], "form": case["form"]}
    b = posterior(ev)
    if evsi(b, ev) > K["probe"]:
        return cheapest(posterior(dict(ev, probe=case["probe"]))), K["probe"]
    return cheapest(b), 0


POLICIES = [
    ("baseline", "escalate everything",        policy_baseline),
    ("P0",       "prior only, no evidence",    policy_p0),
    ("P1",       "hand-picked, 4 actions",     policy_p1),
    ("P1-trunc", "hand-picked, 2 actions",     policy_p1_trunc),
    ("P2",       "cost-derived",               policy_p2),
    ("P3",       "P2 plus the probe",          policy_p3),
]

# ---------------------------------------------------------------- exact answer


def exact(fn):
    total = esc = probed = 0.0
    for s, c, f, pr in product(STATES, CONTEXT, FORM, PROBE):
        p = PRIOR[s] * L_CONTEXT[s][c] * L_FORM[s][f] * L_PROBE[s][pr]
        a, extra = fn({"context": c, "form": f, "probe": pr})
        total += p * (COST[a][s] + extra)
        if a == "escalate": esc += p
        if extra: probed += p
    return total, esc, probed


# ---------------------------------------------------------------- case set


def build_cases(n, seed):
    rng = random.Random(seed)

    def draw(table, state):
        r, acc = rng.random(), 0.0
        for v, p in table[state].items():
            acc += p
            if r < acc:
                return v
        return v

    out = []
    for i in range(n):
        r, acc = rng.random(), 0.0
        for s in STATES:
            acc += PRIOR[s]
            if r < acc:
                state = s
                break
        out.append({"id": i + 1, "true_state": state,
                    "context": draw(L_CONTEXT, state),
                    "form": draw(L_FORM, state),
                    "probe": draw(L_PROBE, state)})
    return out


def load_cases():
    """Frozen on first run. The generator draws from the same likelihood tables
    the agent reasons with, so this is a closed-world consistency check, not an
    evaluation against independent ground truth."""
    if os.path.exists(CASES):
        with open(CASES) as fh:
            return json.load(fh)
    cases = build_cases(N_CASES, SEED)
    os.makedirs(os.path.dirname(CASES), exist_ok=True)
    with open(CASES, "w") as fh:
        json.dump(cases, fh, indent=2)
    return cases


# ---------------------------------------------------------------- sweeps


def sweep(label, values, apply_fn, names=None):
    names = names or [n for n, _, _ in POLICIES]
    saved = json.dumps([COST, PRIOR, K])
    print(f"\n{label}")
    head = f"{'value':>10s} " + " ".join(f"{n:>9s}" for n in names)
    print(head); print("-" * len(head))
    for v in values:
        apply_fn(v)
        row = [exact(fn)[0] for n, _, fn in POLICIES if n in names]
        print(f"{v:>10} " + " ".join(f"{c:9.1f}" for c in row))
    c, p, k = json.loads(saved)
    COST.update(c); PRIOR.update(p); K.update(k)


def main():
    cases = load_cases()
    counts = {s: sum(1 for c in cases if c["true_state"] == s) for s in STATES}

    print("=" * 76)
    print("SECTION 9 -- policies against escalate-everything")
    print("=" * 76)

    print("\n--- cost matrix (engineer-minutes) ---\n")
    print(f"{'':10s}" + "".join(f"{s:>10s}" for s in STATES))
    for a in ["dismiss", "investigate", "escalate", "revoke", "rotate"]:
        if a == "investigate":
            print(f"{a:10s}" + "".join(f"{K['probe']:10d}" for _ in STATES)
                  + "   <- entry fee, not a terminal cost")
        else:
            print(f"{a:10s}" + "".join(f"{COST[a][s]:10d}" for s in STATES))

    print("\n--- the six beliefs the agent can actually hold ---\n")
    print(f"{'context':13s}{'form':13s}{'P(seen)':>9s}{'P(live)':>9s}"
          f"{'act':>9s}{'EVSI':>7s}{'VPI':>7s}")
    probe_share = 0.0
    for c, f, pe, b in reachable_beliefs():
        ev = {"context": c, "form": f}
        v = evsi(b, ev)
        buy = v > K["probe"]
        if buy: probe_share += pe
        print(f"{c:13s}{f:13s}{pe:9.4f}{b['live']:9.4f}{cheapest(b):>9s}"
              f"{v:7.2f}{vpi(b):7.2f}{'  buy' if buy else ''}")
    print(f"\n   probe bought on {probe_share*100:.2f}% of findings")
    print(f"   max VPI over reachable beliefs = "
          f"{max(vpi(b) for *_, b in reachable_beliefs()):.2f} min "
          f"(a human must cost less than this to be worth asking)")

    print("\n--- decision boundaries on the reachable line ---\n")
    for a, b_, p in boundaries_on_reachable_line():
        print(f"   {a} -> {b_} at P(live) = {p:.5f}")
    print("   (P(live):P(revoked) is locked at "
          f"{RATIO:.4f} by the free features, so this is the only line the "
          "agent walks)")

    print("\n--- exact expected cost per finding ---\n")
    base = exact(policy_baseline)[0]
    rows = {}
    print(f"{'':10s}{'policy':26s}{'cost':>8s}{'vs base':>9s}{'human':>8s}{'probed':>8s}")
    for name, desc, fn in POLICIES:
        cost, esc, prb = exact(fn)
        rows[name] = cost
        d = "--" if name == "baseline" else f"{(cost/base-1)*100:+.1f}%"
        print(f"{name:10s}{desc:26s}{cost:8.2f}{d:>9s}{esc*100:7.1f}%{prb*100:7.1f}%")

    print("\n--- P1 ablation: how much of its cost is the threshold, and how "
          "much is the truncated action set? ---\n")
    for fb in ["dismiss", "revoke", "rotate", "escalate"]:
        t = 0.0
        for s, c, f in product(STATES, CONTEXT, FORM):
            p = PRIOR[s] * L_CONTEXT[s][c] * L_FORM[s][f]
            b = posterior({"context": c, "form": f})
            t += p * COST["rotate" if b["live"] > NAIVE_HI else fb][s]
        print(f"   threshold {NAIVE_HI}, fallback {fb:9s} {t:7.2f}  "
              f"{(t/base-1)*100:+6.1f}%")

    print("\n--- how often does the belief model change the action? ---\n")
    p0a = cheapest(PRIOR)
    for label, fn in [("P2", policy_p2), ("P3", policy_p3)]:
        d = sum(pe for c, f, pe, b in reachable_beliefs()
                if fn({"context": c, "form": f, "probe": "old"})[0] != p0a)
        print(f"   {label} differs from P0 ('{p0a}' always) on {d*100:.2f}% of findings")

    print("\n--- realised cost on the frozen cases ---\n")
    print(f"   {len(cases)} cases, seed {SEED}: "
          + ", ".join(f"{counts[s]} {s}" for s in STATES)
          + f"   (live share {counts['live']/len(cases):.2f} vs prior "
            f"{PRIOR['live']:.2f})")
    bt = sum(COST["escalate"][c["true_state"]] for c in cases)
    print(f"\n{'':10s}{'total':>8s}{'per case':>10s}{'vs base':>9s}")
    for name, desc, fn in POLICIES:
        t = sum(COST[fn(c)[0]][c["true_state"]] + fn(c)[1] for c in cases)
        d = "--" if name == "baseline" else f"{(t/bt-1)*100:+.1f}%"
        print(f"{name:10s}{t:8d}{t/len(cases):10.2f}{d:>9s}")

    print("\n" + "=" * 76)
    print("SENSITIVITY -- exact expected cost per finding")
    print("=" * 76)

    def set_dismiss(v): COST["dismiss"]["live"] = v
    def set_prior(v):
        r = 1 - PRIOR["fake"]
        PRIOR["live"], PRIOR["revoked"] = r * v, r * (1 - v)
    def set_probe(v): K["probe"] = v
    def set_outage(v):
        K["outage"] = v
        COST.update(build_costs())
    def set_rotate_fake(v):
        COST["rotate"]["fake"] = v
        COST["escalate"]["fake"] = K["human"] + min(
            COST[a]["fake"] for a in ("dismiss", "revoke", "rotate"))

    sweep("dismissing a live key costs...", [240, 600, 1200, 2400, 6000, 24000], set_dismiss)
    sweep("share of not-fake keys that are live...", [0.40, 0.50, 0.64, 0.70, 0.80], set_prior)
    sweep("the probe costs...", [1, 2, 3, 5, 10, 20], set_probe)
    sweep("an outage costs...", [0, 60, 120, 240, 480], set_outage)
    sweep("rotating a FAKE key costs...", [0, 10, 20, 60, 120], set_rotate_fake)

    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "summary.json"), "w") as fh:
        json.dump({"exact_expected_cost": rows, "n_cases": len(cases),
                   "seed": SEED, "probe_cost": K["probe"],
                   "cost_matrix": COST,
                   "boundaries_reachable": [
                       {"from": a, "to": b_, "p_live": p}
                       for a, b_, p in boundaries_on_reachable_line()],
                   "max_vpi_reachable": max(vpi(b) for *_, b in reachable_beliefs()),
                   }, fh, indent=2)
    print("\nWrote results/summary.json and data/cases.json")


if __name__ == "__main__":
    main()
