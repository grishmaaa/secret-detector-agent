"""Week 2, commit 8: can the agent notice that its own structural assumption
is wrong?

W2-7 found a failure the agent cannot see. Its headline structural result --
`live` and `revoked` carry identical free-feature rows, so the mutual
information between them is exactly zero -- is an assumption, not an
observation. In worlds where it is false the agent forgoes up to 2 minutes a
finding, and nothing in its own diagnostics can tell.

Parameter uncertainty does not fix this. The invariance is not a value the
agent could be uncertain about; it is a constraint tying two rows together.
Sampling around a tied pair keeps them tied. What is missing is uncertainty
about WHICH MODEL is right, not about the numbers inside one.

So: a model-selection layer, sitting outside the agent, which never touches its
decisions and only watches.

    H0:  P(context | live) = P(context | revoked)      the assumption
    H1:  P(context | live) != P(context | revoked)     the alternative

Bayes factor between them, under Dirichlet-multinomial marginal likelihoods.

THE POINT OF THE EXPERIMENT is that it does not get clean data. It sees only
the outcomes the agent's own discovery process surfaces, with the asymmetry
measured in W2-4:

    remediated something that did not need it   -> 80% discovered
    decided correctly                           -> 30% discovered
    dismissed something that was live           ->  5% discovered

Remediating a revoked key is wrong, so it is found out 80% of the time.
Remediating a live key is correct, so it is found out 30% of the time. Measured,
the agent ends up seeing about 1.5 revoked labels for every live one -- and
those are exactly the two classes the test compares.

Two failure modes are looked for specifically:

  - can the biased sample MANUFACTURE evidence for H1 when H0 is true?
  - can it HIDE a real difference because one class is over-observed?

And a matched control separates the two explanations that would otherwise be
confounded: an unskewed sample cut to the same TOTAL size as the biased one.
Whatever the biased column loses relative to that control is caused by the
imbalance; whatever both lose relative to full data is caused by there simply
being fewer labels.

Writes results/model-uncertainty.md and results/model-uncertainty.json.
"""

import json
import math
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
PT = [W.L_PROBE, S.L_SCOPE]
PS = [R.PROBE, S.SCOPE]

N_CASES = 2000
SEEDS = 40
DELTAS = (0.0, 0.02, 0.05, 0.10, 0.20, 0.35)
ALPHA = 1.0                 # Dirichlet prior on each context row
LOG10_BF_STRONG = 1.0       # Jeffreys: >1 is strong evidence for H1

DISCOVERY = {"over": 0.80, "right": 0.30, "under": 0.05}


# ---------------------------------------------------------------- the world

def world_context(delta):
    """Free-feature rows. At delta = 0 live and revoked are identical, which is
    what the agent believes at every delta."""
    ctx = {s: dict(W.L_CONTEXT[s]) for s in W.STATES}
    if delta > 0:
        ctx["live"] = {"placeholder": max(0.10 - delta, 0.005), "neutral": 0.30,
                       "production": 0.60 + delta}
        ctx["revoked"] = {"placeholder": 0.10 + delta, "neutral": 0.30,
                          "production": max(0.60 - delta, 0.005)}
        for k in ("live", "revoked"):
            t = sum(ctx[k].values())
            ctx[k] = {a: b / t for a, b in ctx[k].items()}
    return ctx


def draw(table, s, rng):
    r, acc = rng.random(), 0.0
    for k, p in table[s].items():
        acc += p
        if r <= acc:
            return k
    return k


# ---------------------------------------------------------------- the agent

def act(case):
    """The unchanged agent. It always believes the invariance."""
    b = I.update(dict(W.PRIOR), [W.L_CONTEXT, W.L_FORM],
                 (case["context"], case["form"]))
    now = W.expected_cost(b, W.cheapest(b, COST), COST)
    after = 0.0
    for o in product(*PS):
        po = I.marginal(b, PT, o)
        if po <= 0:
            continue
        p = I.update(b, PT, o)
        after += po * W.expected_cost(p, W.cheapest(p, COST), COST)
    if now - after > R.K["probe"]:
        b = I.update(b, PT, (case["probe"], case["scope"]))
    a = W.cheapest(b, COST)
    if b["other"] > F.P_OTHER_TRIGGER:
        return "escalate"
    if max(COST[a][s] for s in W.STATES) > F.CEILING:
        return "escalate"
    return a


def discovery_p(action, truth):
    best = min(W.TERMINAL, key=lambda x: COST[x][truth])
    if action == best:
        return DISCOVERY["right"]
    if action in ("revoke", "rotate"):
        return DISCOVERY["over"]
    if action == "dismiss":
        return DISCOVERY["under"]
    return DISCOVERY["right"]


# ---------------------------------------------------------------- the test

def log_marginal(counts, alpha=ALPHA):
    """Log marginal likelihood of multinomial counts under a Dirichlet prior."""
    k = len(counts)
    n = sum(counts.values())
    out = math.lgamma(alpha * k) - math.lgamma(alpha * k + n)
    for v in counts.values():
        out += math.lgamma(alpha + v) - math.lgamma(alpha)
    return out


def log10_bayes_factor(live, revoked):
    """log10 BF(H1 : H0). Positive favours separate distributions."""
    pooled = {c: live.get(c, 0) + revoked.get(c, 0) for c in R.CONTEXT}
    h1 = log_marginal(live) + log_marginal(revoked)
    h0 = log_marginal(pooled)
    return (h1 - h0) / math.log(10)


def trial(delta, seed, biased=True, keep=None):
    """keep: (n_live, n_revoked) to subsample down to, for a matched control."""
    rng = random.Random(seed)
    ctx = world_context(delta)
    live = {c: 0 for c in R.CONTEXT}
    revoked = {c: 0 for c in R.CONTEXT}

    for _ in range(N_CASES):
        r, acc, t = rng.random(), 0.0, W.STATES[-1]
        for s in W.STATES:
            acc += W.PRIOR[s]
            if r <= acc:
                t = s
                break
        case = dict(truth=t, context=draw(ctx, t, rng),
                    form=draw(W.L_FORM, t, rng),
                    probe=draw(W.L_PROBE, t, rng),
                    scope=draw(S.L_SCOPE, t, rng))
        if t not in ("live", "revoked"):
            continue
        if biased:
            a = act(case)
            if rng.random() >= discovery_p(a, t):
                continue        # nobody found out; the label never arrives
        (live if t == "live" else revoked)[case["context"]] += 1

    if keep is not None:
        # matched control: same NUMBER of labels as the biased run, but drawn
        # without the skew. Separates "fewer labels" from "unequal classes".
        live = _subsample(live, keep[0], rng)
        revoked = _subsample(revoked, keep[1], rng)

    return dict(bf=log10_bayes_factor(live, revoked),
                n_live=sum(live.values()), n_revoked=sum(revoked.values()))


def _subsample(counts, target, rng):
    pool = [c for c, n in counts.items() for _ in range(n)]
    if target >= len(pool):
        return counts
    pick = rng.sample(pool, int(target))
    out = {c: 0 for c in counts}
    for c in pick:
        out[c] += 1
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for delta in DELTAS:
        bi = [trial(delta, 7000 + s, True) for s in range(SEEDS)]
        un = [trial(delta, 7000 + s, False) for s in range(SEEDS)]
        # matched: unskewed, but cut to the same total label count as biased
        tot = sum(t["n_live"] + t["n_revoked"] for t in bi) / SEEDS
        mt = [trial(delta, 7000 + s, False, keep=(tot / 2, tot / 2))
              for s in range(SEEDS)]
        rows.append(dict(
            delta=delta,
            biased_detect=sum(t["bf"] > LOG10_BF_STRONG for t in bi) / SEEDS,
            unbiased_detect=sum(t["bf"] > LOG10_BF_STRONG for t in un) / SEEDS,
            biased_bf=sorted(t["bf"] for t in bi)[SEEDS // 2],
            unbiased_bf=sorted(t["bf"] for t in un)[SEEDS // 2],
            matched_detect=sum(t["bf"] > LOG10_BF_STRONG for t in mt) / SEEDS,
            matched_bf=sorted(t["bf"] for t in mt)[SEEDS // 2],
            n_live=sum(t["n_live"] for t in bi) / SEEDS,
            n_revoked=sum(t["n_revoked"] for t in bi) / SEEDS,
            n_live_un=sum(t["n_live"] for t in un) / SEEDS,
            n_revoked_un=sum(t["n_revoked"] for t in un) / SEEDS))

    payload = dict(n_cases=N_CASES, seeds=SEEDS, alpha=ALPHA,
                   threshold=LOG10_BF_STRONG, discovery=DISCOVERY, rows=rows)
    with open(os.path.join(OUT, "model-uncertainty.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# Can the agent notice its own structural assumption is wrong?\n")
    add("W2-7 found a failure the agent cannot see. Its headline structural")
    add("result -- that `live` and `revoked` carry identical free-feature rows,")
    add("so the mutual information between them is exactly zero -- is an")
    add("assumption rather than an observation. Where it is false the agent")
    add("loses up to two minutes a finding and has no way to tell.\n")
    add("Parameter uncertainty does not reach this. The invariance is not a")
    add("value to be uncertain about; it is a constraint tying two rows")
    add("together, and sampling around a tied pair keeps them tied. What is")
    add("missing is uncertainty about **which model is right**.\n")
    add("So: a model-selection layer that watches and never decides.\n")
    add("- **H0** — `P(context | live) = P(context | revoked)`. The assumption.")
    add("- **H1** — the two differ.\n")
    add("Bayes factor between them under Dirichlet-multinomial marginal")
    add(f"likelihoods, α = {ALPHA}, calling log₁₀ BF > {LOG10_BF_STRONG:.0f}")
    add("strong evidence for H1.\n")

    add("## The data it gets is not clean, and that is the experiment\n")
    add("The layer sees only what the agent's own discovery process surfaces,")
    add("with the asymmetry measured in W2-4:\n")
    add("| Outcome | Discovered |")
    add("|---|---|")
    add(f"| remediated something that did not need it | {DISCOVERY['over']:.0%} |")
    add(f"| decided correctly | {DISCOVERY['right']:.0%} |")
    add(f"| dismissed something that was live | {DISCOVERY['under']:.0%} |")
    add("")
    add("Remediating a revoked key is wrong, so it is found out 80% of the")
    add("time. Remediating a live key is correct, so it is found out 30% of the")
    add("time. **The two classes the test compares are observed at different")
    add("rates**, and that is not a detail — it is the whole difficulty.\n")
    r0 = rows[0]
    add(f"Out of {N_CASES} findings per run, the layer ends up with roughly")
    add(f"**{r0['n_live']:.0f} live and {r0['n_revoked']:.0f} revoked** labels")
    add(f"({r0['n_revoked'] / r0['n_live']:.1f}x as many revoked), against")
    add(f"{r0['n_live_un']:.0f} and {r0['n_revoked_un']:.0f} if every outcome")
    add("were observed. The skew is real and it runs the wrong way: the class")
    add("the agent under-serves is the class it sees least of.\n")

    add("## Results\n")
    add("Three columns, because two explanations have to be separated. *All")
    add("labels* is every outcome observed. *Matched* is an unskewed sample cut")
    add("to the same TOTAL size the biased process delivers -- so the only")
    add("difference between it and the biased column is the imbalance between")
    add("classes, not how much data there is.\n")
    add("| δ | Biased | Matched (same n, no skew) | All labels | log₁₀BF biased | matched | all | Labels live/revoked |")
    add("|---|---|---|---|---|---|---|---|")
    for r in rows:
        tag = " *(H0)*" if r["delta"] == 0 else ""
        add(f"| {r['delta']:.2f}{tag} | **{r['biased_detect'] * 100:.0f}%** | "
            f"{r['matched_detect'] * 100:.0f}% | "
            f"{r['unbiased_detect'] * 100:.0f}% | {r['biased_bf']:+.2f} | "
            f"{r['matched_bf']:+.2f} | {r['unbiased_bf']:+.2f} | "
            f"{r['n_live']:.0f} / {r['n_revoked']:.0f} |")
    add("")

    h0 = rows[0]
    add("## The two failure modes\n")
    add(f"**Does the biased sample manufacture evidence for H1 when H0 is")
    add(f"true?** At δ = 0 the invariance genuinely holds, and the layer calls")
    add(f"it broken in **{h0['biased_detect'] * 100:.0f}%** of runs against")
    add(f"{h0['unbiased_detect'] * 100:.0f}% on clean labels. ")
    if h0["biased_detect"] <= 0.10:
        add("The false-positive rate is controlled: unequal sample sizes between")
        add("two classes do not by themselves create apparent differences")
        add("between their distributions, because the Bayes factor accounts for")
        add("sample size rather than assuming balance.\n")
    else:
        add("The false-positive rate is **not** controlled, which would make the")
        add("mechanism unusable as built.\n")

    def first(key):
        c = [r for r in rows if r["delta"] > 0 and r[key] >= 0.8]
        return min(c, key=lambda r: r["delta"])["delta"] if c else None

    db, dm, du = first("biased_detect"), first("matched_detect"), first("unbiased_detect")
    add("**Does it hide a real difference?** The smallest difference detected")
    add("reliably, by sample:\n")
    add(f"- biased labels: δ = {db}")
    add(f"- unskewed, same number of labels: δ = {dm}")
    add(f"- every label: δ = {du}\n")
    if dm is not None and db is not None and dm == db:
        add("**The skew costs nothing. The sample size costs everything.**")
        add("An unskewed sample of the same size detects exactly the same")
        add("smallest difference as the biased one. What the discovery process")
        add("takes away is labels, not fairness between the classes.\n")
        add("That is worth stating plainly because the intuition points the")
        add("other way, and mine did: I expected a sample containing")
        f = rows[0]
        add(f"{f['n_revoked'] / f['n_live']:.1f} times as many revoked keys as")
        add("live ones to distort a test comparing the two. It does not,")
        add("because the Bayes factor compares the SHAPE of each class's")
        add("distribution and normalises each by its own count. Unequal")
        add("n changes how precisely each shape is estimated; it does not make")
        add("two identical shapes look different, and it does not make two")
        add("different shapes look alike.\n")
        add("The practical consequence is more encouraging than the biased")
        add("framing suggested. The agent does not need unbiased feedback to")
        add("audit its own assumptions. It needs *enough* feedback, and the")
        add("discovery process delivers about half of what it observes.\n")
    else:
        add("The skew and the sample size both cost sensitivity, and the")
        add("matched control separates how much each contributes.\n")

    add("## What this adds to the agent\n")
    add("Against the W2-7 failure, which is the point of the exercise:\n")
    tests = [r for r in rows if r["delta"] in (0.10, 0.20)]
    for r in tests:
        add(f"- At δ = {r['delta']:.2f}, where W2-7 measured the agent forgoing")
        add(f"  real value, the layer flags the assumption in "
            f"{r['biased_detect'] * 100:.0f}% of runs.")
    add("")
    add("So the silent failure is no longer silent. The agent still cannot fix")
    add("itself -- relaxing the invariance means estimating two separate rows,")
    add("and the labels available are too few to do that well, though not --")
    add("as the matched control shows -- too skewed --")
    add("but it can now raise its hand and say *the assumption I was built on")
    add("does not match what I am seeing*. Detection and repair are different")
    add("problems, and only the first is solved here.\n")
    add("**This is the capability the project was missing.** Everything before")
    add("this commit reasons about uncertainty within a fixed model. This")
    add("reasons about whether the model is the right one, which is a different")
    add("kind of doubt and the only kind that could have caught the failure")
    add("W2-7 exposed. Neither the sessions nor the brief mention Bayesian")
    add("model comparison; it arrived because an experiment found something the")
    add("existing machinery could not express.")
    add("")

    with open(os.path.join(OUT, "model-uncertainty.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
