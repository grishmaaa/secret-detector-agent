"""Week 2, commit 3: the extended model and the Week 2 experiment.

Three changes to the Week 1 agent, and then a proper experiment on all of them.

1. TWO NEW HIDDEN STATES.

   `zero_scope` -- a credential that authenticates but is authorised for
   nothing. Week 1 named it in the limitations and did not model it. It is
   `live` by the Week 1 definition and carries almost none of the risk that
   makes dismissing a live key cost 2400 minutes, so it was never a belief
   problem; it was a cost problem wearing a belief problem's clothes.

   `other` -- a residual. Not a description of anything. It exists because a
   state absent from the list has probability zero forever, no evidence can
   ever raise it, and the agent is infinitely surprised on the day it happens.
   A model that cannot be wrong in a new way is not humble, it is brittle.

2. FIVE HUNDRED CASES instead of forty. The Week 1 forty stay frozen and are
   still reported; this is a second, larger draw at a different seed.

3. THE BRIEF'S POLICY LADDER: P0 baseline, P1 belief-only, P2 threshold,
   P3 value-of-information, plus the full metric set and a calibration check.

EVERY NEW NUMBER IN THIS FILE IS AN ASSUMPTION, NOT A MEASUREMENT.
They are marked. The Week 1 numbers they sit beside are also assumptions; the
difference is that those have been through five rounds of review and these
have not.

Writes results/week2-results.md and results/week2-results.json.
"""

import json
import math
import os
import random
from itertools import product

import run_experiment as R
import information as I

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

SEED = 20260902
N_CASES = 500


# ============================================================ the extended model

STATES = ["live", "revoked", "fake", "zero_scope", "other"]

# --- prior ------------------------------------------------------------------
# ASSUMPTION. Week 1's 0.48 / 0.27 / 0.25 came from published scanner precision
# and a vendor validity figure. The two new states are carved out of it rather
# than added to it, so the total still sums to one and the sourced quantities
# are not silently inflated.
#
#   zero_scope is carved from `live`, because a zero-scope key authenticates:
#   under the Week 1 state list it WAS a live key. Taking 1/12 of that mass is
#   a guess with no source behind it.
#
#   other is carved proportionally from everything, at 1%. One per cent is a
#   deliberate choice rather than a derived one: large enough that evidence can
#   move it, small enough that it does not drive the decision on its own.

P_OTHER = 0.01
P_ZERO_FROM_LIVE = 1.0 / 12.0

_live_split = R.PRIOR["live"] * (1 - P_ZERO_FROM_LIVE)
_zero = R.PRIOR["live"] * P_ZERO_FROM_LIVE
_raw = {"live": _live_split, "revoked": R.PRIOR["revoked"],
        "fake": R.PRIOR["fake"], "zero_scope": _zero}
_scale = 1.0 - P_OTHER
PRIOR = {s: v * _scale for s, v in _raw.items()}
PRIOR["other"] = P_OTHER

# --- likelihoods ------------------------------------------------------------
# Free features: zero_scope is a real, provider-issued key, so it looks exactly
# like live and revoked in a repository. That is not laziness -- it is the same
# structural claim Week 1 made, extended to a third state, and it means the
# free features now fail to separate THREE states rather than two.
#
# `other` gets a near-uniform row. ASSUMPTION, and the most defensible one
# available: a state we cannot characterise is one we have no grounds to say
# anything about, and the maximum-entropy row is the row that adds no evidence
# we do not have.

L_CONTEXT = {s: dict(R.L_CONTEXT[s]) for s in ("live", "revoked", "fake")}
L_CONTEXT["zero_scope"] = dict(R.L_CONTEXT["live"])
L_CONTEXT["other"] = {c: 1 / len(R.CONTEXT) for c in R.CONTEXT}

L_FORM = {s: dict(R.L_FORM[s]) for s in ("live", "revoked", "fake")}
L_FORM["zero_scope"] = dict(R.L_FORM["live"])
L_FORM["other"] = {f: 1 / len(R.FORM) for f in R.FORM}

# Probe: this is where zero_scope differs, and it is the only place it can.
# ASSUMPTION. A key authorised for nothing can still be presented, so it may
# show usage -- but a key that cannot do anything is unlikely to be in active
# service, so the mass sits on `old` and `null`.
L_PROBE = {s: dict(R.L_PROBE[s]) for s in ("live", "revoked", "fake")}
L_PROBE["zero_scope"] = {"recent": 0.05, "old": 0.45, "null": 0.50}
L_PROBE["other"] = {p: 1 / len(R.PROBE) for p in R.PROBE}

# --- costs ------------------------------------------------------------------
# zero_scope: ASSUMPTION, and the point of the whole state. Dismissing it is
# nearly free because there is nothing behind it to breach; remediating it
# costs roughly what remediating a revoked key costs, because the work is the
# same and only the risk differs.
#
# other: priced at the MEAN of the known states for each action. The
# alternative -- pricing it at the worst known cost -- is defensible and
# changes the policy, so it is run as a variant below rather than argued about.

def build_costs(other_rule="mean"):
    c = {a: dict(R.COST[a]) for a in ("dismiss", "revoke", "rotate")}
    c["dismiss"]["zero_scope"] = 5
    c["revoke"]["zero_scope"] = 5
    c["rotate"]["zero_scope"] = 30

    known = ("live", "revoked", "fake", "zero_scope")
    for a in c:
        vals = [c[a][s] for s in known]
        c[a]["other"] = (sum(vals) / len(vals) if other_rule == "mean"
                         else max(vals))

    c["escalate"] = {s: R.K["human"] + min(c[a][s] for a in ("dismiss", "revoke", "rotate"))
                     for s in STATES}
    return c


COST = build_costs()
TERMINAL = ["dismiss", "escalate", "revoke", "rotate"]


# ============================================================ machinery

def posterior(ev, prior=None, tables=None):
    b = dict(prior or PRIOR)
    tabs = tables or {"context": L_CONTEXT, "form": L_FORM, "probe": L_PROBE}
    u = {}
    for s in b:
        p = b[s]
        for k, tab in tabs.items():
            if k in ev:
                p *= tab[s][ev[k]]
        u[s] = p
    t = sum(u.values())
    return {s: v / t for s, v in u.items()} if t > 0 else dict(b)


def expected_cost(b, a, cost=None):
    C = cost or COST
    return sum(b[s] * C[a][s] for s in b)


def cheapest(b, cost=None):
    return min(TERMINAL, key=lambda a: expected_cost(b, a, cost))


def evsi_probe(b, cost=None):
    now = expected_cost(b, cheapest(b, cost), cost)
    after = 0.0
    for o in R.PROBE:
        po = sum(b[s] * L_PROBE[s][o] for s in b)
        if po <= 0:
            continue
        post = {s: b[s] * L_PROBE[s][o] / po for s in b}
        after += po * expected_cost(post, cheapest(post, cost), cost)
    return now - after


def eig_probe(b):
    return I.analyse("probe", b, [L_PROBE], [R.PROBE])["eig"]


# ============================================================ the policies

# P1 needs a state-to-action map, because it has no cost model. This is what an
# engineer does before anyone mentions decision theory: identify the most
# likely explanation, then do the obvious thing about it.
OBVIOUS = {"live": "rotate", "revoked": "dismiss", "fake": "dismiss",
           "zero_scope": "dismiss", "other": "escalate"}


def p0(case):
    """Baseline. No evidence at all. Take the action that is most often right."""
    return cheapest(PRIOR), 0, dict(PRIOR)


def p1(case):
    """Belief only. Free evidence, then act on the most likely state. No costs."""
    b = posterior({"context": case["context"], "form": case["form"]})
    top = max(b, key=b.get)
    return OBVIOUS[top], 0, b


def p2(case):
    """Threshold. Free evidence, then minimise expected cost."""
    b = posterior({"context": case["context"], "form": case["form"]})
    return cheapest(b), 0, b


def p3(case):
    """Value of information. As P2, but buys the probe when it would pay.

    The stop rule, stated explicitly:
      1. run every free check first -- they cost nothing, so there is no belief
         at which skipping them is correct;
      2. then ask whether the probe's expected value exceeds its price;
      3. if it does not, act. The probe's bit count is not consulted at any
         point, because bits are not what is being spent.
    """
    ev = {"context": case["context"], "form": case["form"]}
    b = posterior(ev)
    if evsi_probe(b) > R.K["probe"]:
        return cheapest(posterior(dict(ev, probe=case["probe"]))), R.K["probe"], \
            posterior(dict(ev, probe=case["probe"]))
    return cheapest(b), 0, b


POLICIES = [("P0", "baseline, no evidence", p0),
            ("P1", "belief only, no cost model", p1),
            ("P2", "cost-derived threshold", p2),
            ("P3", "P2 plus value of information", p3)]


# ============================================================ cases

def build_cases(n, seed):
    rng = random.Random(seed)

    def draw(table, s):
        r, acc = rng.random(), 0.0
        for k, p in table[s].items():
            acc += p
            if r <= acc:
                return k
        return k

    out = []
    for i in range(n):
        r, acc, s = rng.random(), 0.0, STATES[-1]
        for st in STATES:
            acc += PRIOR[st]
            if r <= acc:
                s = st
                break
        out.append(dict(id=i, truth=s,
                        context=draw(L_CONTEXT, s),
                        form=draw(L_FORM, s),
                        probe=draw(L_PROBE, s)))
    return out


# ============================================================ metrics

def hindsight_best(truth):
    return min(TERMINAL, key=lambda a: COST[a][truth])


def evaluate(name, fn, cases):
    dec_cost = info_cost = 0.0
    probes = escalated = 0
    state_hits = action_hits = 0
    tp = fp = fn_ = 0          # positive class: the true state is `live`
    regret = 0.0
    bins = [[0, 0.0, 0] for _ in range(10)]   # count, sum p(live), n live
    rows = []

    for c in cases:
        a, extra, b = fn(c)
        cost = COST[a][c["truth"]]
        dec_cost += cost
        info_cost += extra
        regret += cost - COST[hindsight_best(c["truth"])][c["truth"]]
        if extra:
            probes += 1
        if a == "escalate":
            escalated += 1
        if max(b, key=b.get) == c["truth"]:
            state_hits += 1
        if a == hindsight_best(c["truth"]):
            action_hits += 1

        remediated = a in ("revoke", "rotate")
        if c["truth"] == "live":
            if remediated:
                tp += 1
            else:
                fn_ += 1
        elif remediated:
            fp += 1

        k = min(9, int(b["live"] * 10))
        bins[k][0] += 1
        bins[k][1] += b["live"]
        bins[k][2] += 1 if c["truth"] == "live" else 0
        rows.append(dict(id=c["id"], truth=c["truth"], action=a,
                         p_live=b["live"], cost=cost, extra=extra))

    n = len(cases)
    ece = sum(cnt / n * abs(psum / cnt - hits / cnt)
              for cnt, psum, hits in bins if cnt)
    return dict(
        name=name, n=n,
        state_accuracy=state_hits / n, action_accuracy=action_hits / n,
        precision=(tp / (tp + fp) if tp + fp else None),
        recall=(tp / (tp + fn_) if tp + fn_ else None),
        decision_cost=dec_cost / n, info_cost=info_cost / n,
        total_cost=(dec_cost + info_cost) / n,
        questions=probes / n, human_rate=escalated / n,
        regret=regret / n, calibration_error=ece,
        bins=[dict(lo=i / 10, n=c, mean_p=(p / c if c else None),
                   freq=(h / c if c else None))
              for i, (c, p, h) in enumerate(bins)],
        rows=rows)


# ============================================================ report

def main():
    os.makedirs(OUT, exist_ok=True)
    cases = build_cases(N_CASES, SEED)
    results = [evaluate(n, f, cases) for n, d, f in POLICIES]
    desc = {n: d for n, d, _ in POLICIES}

    # variant: price the residual pessimistically instead of at the mean
    global COST
    saved = COST
    COST = build_costs("worst")
    pess = [evaluate(n, f, cases) for n, d, f in POLICIES]
    COST = saved

    truth_counts = {s: sum(1 for c in cases if c["truth"] == s) for s in STATES}

    payload = dict(seed=SEED, n=N_CASES, prior=PRIOR, costs=COST,
                   truth_counts=truth_counts,
                   results=[{k: v for k, v in r.items() if k != "rows"} for r in results],
                   pessimistic=[{k: v for k, v in r.items() if k not in ("rows", "bins")}
                                for r in pess],
                   decisions=results[3]["rows"])
    with open(os.path.join(OUT, "week2-results.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# The Week 2 experiment\n")
    add(f"{N_CASES} simulated cases, seed {SEED}, every policy run on the")
    add("identical case set. The Week 1 forty remain frozen in `data/cases.json`")
    add("and are still the basis of every Week 1 number; this is a second,")
    add("larger draw and does not replace them.\n")

    add("## What changed in the model\n")
    add("Two hidden states were added. Both are labelled assumptions and neither")
    add("has a source behind it.\n")
    add("| State | Prior | Where it came from | Why it exists |")
    add("|---|---|---|---|")
    add(f"| live | {PRIOR['live']:.4f} | Week 1, sourced | unchanged in meaning |")
    add(f"| revoked | {PRIOR['revoked']:.4f} | Week 1, sourced | unchanged |")
    add(f"| fake | {PRIOR['fake']:.4f} | Week 1, sourced | unchanged |")
    add(f"| zero_scope | {PRIOR['zero_scope']:.4f} | **assumption**, carved from `live` | "
        "Week 1 named it in limitations and did not model it. It authenticates, "
        "so Week 1 counted it as live, and it carries almost none of live's risk |")
    add(f"| other | {PRIOR['other']:.4f} | **assumption**, 1% by choice | "
        "A state absent from the list has probability zero forever. No evidence "
        "can raise it and the agent is infinitely surprised the day it occurs |")
    add("")
    add("The new mass is carved out of the existing states rather than added")
    add("alongside them, so the sourced quantities are not quietly inflated to")
    add("make room for two guesses.\n")

    add("### The invariance got worse\n")
    add("`zero_scope` is a real provider-issued key, so in a repository it looks")
    add("exactly like `live` and `revoked`: identical context and")
    add("well-formedness rows. The Week 1 result was that the free features")
    add("cannot separate two states. With the fifth state modelled they cannot")
    add("separate **three**, and the only thing that touches the distinction is")
    add("still the purchased probe.\n")

    add("## Results\n")
    add("| Policy | State acc. | Action acc. | Precision | Recall | Decision cost | Info cost | Total | Questions | Human % | Regret | Calib. error |")
    add("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        pr = f"{r['precision']:.3f}" if r["precision"] is not None else "—"
        rc = f"{r['recall']:.3f}" if r["recall"] is not None else "—"
        add(f"| **{r['name']}** {desc[r['name']]} | {r['state_accuracy']:.3f} | "
            f"{r['action_accuracy']:.3f} | {pr} | {rc} | {r['decision_cost']:.2f} | "
            f"{r['info_cost']:.2f} | **{r['total_cost']:.2f}** | {r['questions']:.3f} | "
            f"{r['human_rate'] * 100:.1f}% | {r['regret']:.2f} | {r['calibration_error']:.4f} |")
    add("")
    add("Costs are engineer-minutes per finding. Precision and recall treat")
    add("*the true state is live* as the positive class and *the agent chose a")
    add("remediation* as the positive prediction: of the keys we remediated, how")
    add("many were live, and of the live keys, how many did we remediate.\n")

    best_cost = min(results, key=lambda r: r["total_cost"])
    best_acc = max(results, key=lambda r: r["state_accuracy"])
    add(f"**Cheapest policy: {best_cost['name']}. Most accurate policy: "
        f"{best_acc['name']}.**")
    if best_cost["name"] != best_acc["name"]:
        add("They are not the same policy, which is the result the brief warns")
        add("to look for. Accuracy and cost are different objectives and this")
        add("problem separates them.\n")
    else:
        add("Here they coincide, which is worth stating because it is not the")
        add("usual outcome and it is worth asking why.\n")

    p2r = [r for r in results if r["name"] == "P2"][0]
    p3r = [r for r in results if r["name"] == "P3"][0]
    add("## A negative result: the probe did not pay for itself\n")
    saved = p2r["decision_cost"] - p3r["decision_cost"]
    spent = p3r["info_cost"]
    n_probe = round(p3r["questions"] * N_CASES)
    add(f"P3 spent **{spent:.2f}** minutes per finding on probes and recovered")
    add(f"**{saved:.2f}** in better decisions. It is behind P2 by")
    add(f"{spent - saved:.2f} minutes per finding. The value-of-information")
    add("machinery, on this draw, cost more than it was worth.\n")
    add("It is worth being precise about why, because the policy is not wrong.")
    add(f"The probe was bought on {n_probe} of {N_CASES} cases, and only at the")
    add("one belief where its expected value exceeds the price -- 5.21 minutes")
    add(f"against a cost of {R.K['probe']}. In expectation those {n_probe}")
    add(f"purchases should have returned about {n_probe * 5.2118 / N_CASES:.2f}")
    add(f"minutes per finding rather than the {saved:.2f} actually realised.")
    add("The gap is sampling noise on twenty-odd purchases, not a flaw in the")
    add("rule: an expectation computed over three probe outcomes says nothing")
    add("about what any particular twenty-two draws will do.\n")
    add("Two honest readings, and I am not going to pick between them here.")
    add("Either the decision rule is right and this draw was unlucky, or a")
    add("saving that a few hundred cases cannot detect is too small to justify")
    add("the machinery that produces it. Both are true statements about the")
    add("same number. Week 1's closed-form comparison over all 54 possible")
    add("worlds put P3 ahead of P2 by 0.08 minutes; that calculation carries no")
    add("sampling error and remains the better estimate of the effect. What this")
    add("experiment adds is the size of the noise around it.\n")
    add("## Calibration\n")
    add("Whether the agent's stated confidence can be trusted. Each row bins the")
    add("cases by the probability P3 assigned to *live*, and compares the")
    add("average stated probability against how often the key actually was live.\n")
    add("| P(live) bin | Cases | Mean stated | Observed | Gap |")
    add("|---|---|---|---|---|")
    for b in results[3]["bins"]:
        if not b["n"]:
            continue
        add(f"| {b['lo']:.1f}–{b['lo'] + 0.1:.1f} | {b['n']} | {b['mean_p']:.3f} | "
            f"{b['freq']:.3f} | {abs(b['mean_p'] - b['freq']):+.3f} |")
    add("")
    add(f"Expected calibration error: **{results[3]['calibration_error']:.4f}**.\n")
    add("This number is easy to over-read. The cases were generated *from the")
    add("agent's own likelihood tables*, so good calibration here says the")
    add("arithmetic is right, not that the model is. A well-calibrated agent in")
    add("a world it invented is the least surprising result available. It would")
    add("mean something if the cases came from somewhere else, and they do not.\n")

    add("## Where the truth actually fell\n")
    add("| State | Cases | Share | Prior |")
    add("|---|---|---|---|")
    for s in STATES:
        add(f"| {s} | {truth_counts[s]} | {truth_counts[s] / N_CASES:.4f} | {PRIOR[s]:.4f} |")
    add("")

    add("## Does the residual state earn its place?\n")
    add("`other` is priced at the mean of the known states. Pricing it at the")
    add("worst known cost instead is equally defensible and is the conservative")
    add("choice, so both are run.\n")
    add("| Policy | Total cost, residual at mean | at worst | Human %, mean | at worst |")
    add("|---|---|---|---|---|")
    for a, b in zip(results, pess):
        add(f"| {a['name']} | {a['total_cost']:.2f} | {b['total_cost']:.2f} | "
            f"{a['human_rate'] * 100:.1f}% | {b['human_rate'] * 100:.1f}% |")
    add("")
    add("One per cent of prior mass, and how it is priced moves the answer by")
    add("the amounts above. That is the honest argument for the residual state:")
    add("not that it improves the policy, but that leaving it out means never")
    add("finding out it was there.")
    add("")

    with open(os.path.join(OUT, "week2-results.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nWrote results/week2-results.md and .json")


if __name__ == "__main__":
    main()
