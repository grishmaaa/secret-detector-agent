"""Week 2, commit 4c: failure analysis, the feedback loop, and a drift alarm.

Three things the Week 1 agent had none of.

PART 1 -- failure analysis. Five failures of the fixed agent, each answered
against ten questions and classified.

PART 2 -- feedback and belief update. Components 11 and 12 of the brief, the
ones people skip. The agent acts, sometimes finds out it was wrong, and
updates its prior. The catch is that FINDING OUT IS NOT SYMMETRIC: when the
agent remediates something that did not need it, a deploy breaks and somebody
says so within hours. When it dismisses a key that was live, nothing happens
and nobody ever tells it. An agent learning only from what it hears about
learns a distorted world.

PART 3 -- distribution shift. The prior was set from how the world used to be.
Jensen-Shannon divergence between the evidence the agent expects and the
evidence it observes is one workable alarm for the world having moved.

Writes results/feedback.md and results/feedback.json.
"""

import json
import math
import os
import random

import run_experiment as R
import week2_experiment as W
import fixes as F

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

COST = F.costs()
AGENT = F.make_full(COST)

# ASSUMPTION, and the whole point of Part 2. How often the organisation finds
# out that a decision was wrong, by what the agent did and what was true.
#
#   Remediating something that did not need it is LOUD: a deploy breaks, an
#   engineer spends an afternoon, somebody files a ticket.
#
#   Dismissing a key that was live is SILENT: nothing happens today, and if
#   something happens in four months nobody connects it to this finding.
DISCOVERY = {
    ("remediate", "wrong"): 0.80,   # we rotated a dead or fake key -- visible waste
    ("dismiss", "wrong"): 0.05,     # we ignored a live key -- silent until it is not
    ("any", "right"): 0.30,         # correct decisions are confirmed sometimes
}


def discovery_p(action, truth):
    best = min(W.TERMINAL, key=lambda a: COST[a][truth])
    if action == best:
        return DISCOVERY[("any", "right")]
    if action in ("revoke", "rotate"):
        return DISCOVERY[("remediate", "wrong")]
    if action == "dismiss":
        return DISCOVERY[("dismiss", "wrong")]
    return DISCOVERY[("any", "right")]


# ============================================================ part 1

QUESTIONS = [
    "What did the agent believe?", "What was actually true?",
    "Which evidence did it use?", "Which evidence did it never obtain?",
    "Was the probability wrong?", "Was the hidden-state list incomplete?",
    "Was the threshold wrong?", "Was the cost model wrong?",
    "Should it have asked for more information?",
    "Should a human have been involved?",
]


def failures(cases, k=5):
    out = []
    for c in cases:
        a, extra, b = AGENT(c)
        best = min(W.TERMINAL, key=lambda x: COST[x][c["truth"]])
        if a == best:
            continue
        regret = COST[a][c["truth"]] - COST[best][c["truth"]]
        out.append(dict(case=c, action=a, best=best, belief=b,
                        regret=regret, probed=bool(extra)))
    out.sort(key=lambda r: -r["regret"])
    return out


def classify(f):
    """The brief's ten categories, applied by rule rather than by feel."""
    b, t, a = f["belief"], f["case"]["truth"], f["action"]
    if t == "other":
        return ("Missing hidden state",
                "The truth was the residual. No likelihood in the model "
                "describes it, so no evidence could have identified it.")
    if b[t] < 0.05:
        if not f["probed"]:
            return ("Insufficient information",
                    "The agent acted without buying the one check that could "
                    "have moved it, because that check was not worth its price "
                    "at this belief.")
        return ("Misleading evidence",
                "The evidence was correct and pointed the wrong way: this "
                "state produces these observations, just rarely.")
    if b[t] > 0.30 and a in ("revoke", "rotate"):
        return ("Wrong cost assumption",
                "The agent held real probability on the truth and remediated "
                "anyway, because remediation is cheap in every state. The "
                "belief was not the problem.")
    return ("Wrong action policy",
            "Belief and evidence were both reasonable; the mapping from "
            "belief to action is what produced the loss.")


# ============================================================ part 2

def run_feedback(n=4000, seed=77, learn=True):
    """Act, sometimes discover the truth, update the prior from what you hear.

    Returns the prior trajectory and what it cost.
    """
    rng = random.Random(seed)
    counts = {s: W.PRIOR[s] * 200 for s in W.STATES}   # pseudo-counts, prior-weighted
    prior = dict(W.PRIOR)
    traj, total, seen = [], 0.0, 0

    for i in range(n):
        # the world does not change; only the agent's picture of it does
        r, acc, truth = rng.random(), 0.0, W.STATES[-1]
        for s in W.STATES:
            acc += W.PRIOR[s]
            if r <= acc:
                truth = s
                break
        case = dict(truth=truth,
                    context=_draw(W.L_CONTEXT, truth, rng),
                    form=_draw(W.L_FORM, truth, rng),
                    probe=_draw(W.L_PROBE, truth, rng))

        b = _posterior_with(prior, case)
        a = W.cheapest(b, COST)
        total += COST[a][truth]

        # The discovery draw is taken unconditionally and only USED when the
        # agent is learning. Guarding the draw itself behind `learn` short-
        # circuits it in the frozen arm, which then consumes a different number
        # of random values from this point on and simulates a different
        # 4,000-finding world. The two arms are meant to differ in one thing;
        # that made them differ in all of them, and it manufactured a
        # 0.57 min/finding advantage for learning that does not exist.
        found = rng.random() < discovery_p(a, truth)
        if learn and found:
            counts[truth] += 1
            seen += 1
            tot = sum(counts.values())
            prior = {s: counts[s] / tot for s in W.STATES}

        if i % 200 == 0:
            traj.append(dict(i=i, prior=dict(prior), action=a))

    return dict(prior=prior, traj=traj, cost=total / n, discovered=seen / n)


def _draw(table, s, rng):
    r, acc = rng.random(), 0.0
    for k, p in table[s].items():
        acc += p
        if r <= acc:
            return k
    return k


def _posterior_with(prior, case):
    u = {}
    for s in W.STATES:
        u[s] = (prior[s] * W.L_CONTEXT[s][case["context"]]
                * W.L_FORM[s][case["form"]])
    t = sum(u.values())
    return {s: v / t for s, v in u.items()}


# ============================================================ part 3

def jsd(p, q):
    """Jensen-Shannon divergence in bits. Symmetric, bounded by 1, and finite
    even when one distribution calls something impossible -- which is why it is
    usable as an alarm and KL divergence is not."""
    m = {k: (p.get(k, 0) + q.get(k, 0)) / 2 for k in set(p) | set(q)}

    def kl(x, y):
        return sum(x[k] * math.log2(x[k] / y[k])
                   for k in x if x.get(k, 0) > 0 and y.get(k, 0) > 0)
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def expected_evidence(prior):
    out = {}
    for c in R.CONTEXT:
        for f in R.FORM:
            out[f"{c}|{f}"] = sum(prior[s] * W.L_CONTEXT[s][c] * W.L_FORM[s][f]
                                  for s in W.STATES)
    return out


def detect_sweep(seeds=8, cal_seeds=8):
    """Can the alarm tell a shift from noise?

    The threshold is calibrated on SEPARATE no-shift runs, which matters: a
    threshold read off the same run you then evaluate is guaranteed to look
    good and means nothing. Detection and false-alarm rates are then measured
    on held-out runs against that fixed threshold.
    """
    out = []
    for window in (250, 500, 1000):
        # calibrate: highest JSD seen across control runs where nothing changes
        cal = []
        for sd in range(cal_seeds):
            d, _ = drift_run(n=4000, shift_at=10 ** 9, seed=900 + sd,
                             window=window, mult=1.0)
            cal += [x["jsd"] for x in d]
        thr = max(cal)

        # false alarms: fresh control runs, same threshold
        fa, fn = 0, 0
        for sd in range(seeds):
            d, _ = drift_run(n=4000, shift_at=10 ** 9, seed=500 + sd,
                             window=window, mult=1.0)
            v = [x["jsd"] for x in d]
            fa += sum(1 for x in v if x > thr)
            fn += len(v)

        for mult in (2.2, 4.0, 8.0):
            hit, tot = 0, 0
            for sd in range(seeds):
                d, _ = drift_run(n=4000, shift_at=2000, seed=100 + sd,
                                 window=window, mult=mult)
                v = [x["jsd"] for x in d if x["i"] >= 2000 + window]
                hit += sum(1 for x in v if x > thr)
                tot += len(v)
            out.append(dict(window=window, mult=mult, threshold=thr,
                            detect=hit / tot, false=fa / fn))
    return out


def drift_run(n=3000, shift_at=1500, seed=99, window=250, mult=2.2):
    """Watch JSD between expected and observed evidence, with a shift halfway."""
    rng = random.Random(seed)
    base = expected_evidence(W.PRIOR)
    # ASSUMPTION: the shifted world. Placeholder-looking strings become far more
    # common -- a new scanner ruleset, or a team that started committing fixtures.
    shifted = {s: v for s, v in W.PRIOR.items()}
    shifted["fake"] = shifted["fake"] * mult
    tot = sum(shifted.values())
    shifted = {s: v / tot for s, v in shifted.items()}

    buf, out = [], []
    for i in range(n):
        src = W.PRIOR if i < shift_at else shifted
        r, acc, truth = rng.random(), 0.0, W.STATES[-1]
        for s in W.STATES:
            acc += src[s]
            if r <= acc:
                truth = s
                break
        buf.append(f"{_draw(W.L_CONTEXT, truth, rng)}|{_draw(W.L_FORM, truth, rng)}")
        if len(buf) > window:
            buf.pop(0)
        if i >= window and i % 50 == 0:
            obs = {}
            for k in buf:
                obs[k] = obs.get(k, 0) + 1 / len(buf)
            out.append(dict(i=i, jsd=jsd(base, obs)))
    return out, shifted


# ============================================================ report

def main():
    os.makedirs(OUT, exist_ok=True)
    cases = W.build_cases(W.N_CASES, W.SEED)
    fails = failures(cases)
    learned = run_feedback(learn=True)
    frozen = run_feedback(learn=False)
    drift, shifted = drift_run()
    sweep = detect_sweep()

    pre = [d["jsd"] for d in drift if d["i"] < 1500]
    post = [d["jsd"] for d in drift if d["i"] >= 1750]

    payload = dict(failures=[{k: v for k, v in f.items() if k != "case"} |
                             {"truth": f["case"]["truth"],
                              "context": f["case"]["context"],
                              "form": f["case"]["form"]} for f in fails[:8]],
                   feedback_learned=learned["prior"], feedback_frozen=W.PRIOR,
                   cost_learned=learned["cost"], cost_frozen=frozen["cost"],
                   discovered=learned["discovered"],
                   trajectory=learned["traj"], drift=drift,
                   shifted_world=shifted, detection_sweep=sweep)
    with open(os.path.join(OUT, "feedback.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# Failure analysis, feedback, and drift\n")

    add(f"## Part 1: five failures of the fixed agent\n")
    add(f"{len(fails)} of {len(cases)} decisions were not the hindsight-best")
    add("action. The five most expensive are examined below. This is the P6")
    add("agent -- corrected breach cost, escalation rules, scope on the probe --")
    add("so these are the mistakes that survive every fix so far.\n")

    for n_, f in enumerate(fails[:5], 1):
        c, b = f["case"], f["belief"]
        cat, why = classify(f)
        add(f"### Failure {n_} — {f['regret']:.0f} minutes lost\n")
        add(f"**Category: {cat}.** {why}\n")
        top = sorted(b.items(), key=lambda kv: -kv[1])[:3]
        add("| Question | Answer |")
        add("|---|---|")
        add(f"| {QUESTIONS[0]} | " +
            ", ".join(f"{k} {v:.3f}" for k, v in top) + " |")
        add(f"| {QUESTIONS[1]} | **{c['truth']}** |")
        add(f"| {QUESTIONS[2]} | context `{c['context']}`, form `{c['form']}`"
            + (f", probe `{c['probe']}` + scope" if f["probed"] else "") + " |")
        add(f"| {QUESTIONS[3]} | " +
            ("nothing further was available" if f["probed"]
             else "the probe, which was not worth its price at this belief") + " |")
        add(f"| {QUESTIONS[4]} | P(truth) was {b[c['truth']]:.4f}; "
            + ("yes, the belief was badly wrong" if b[c["truth"]] < 0.05
               else "no, the belief was reasonable") + " |")
        add(f"| {QUESTIONS[5]} | " +
            ("**yes** — the truth was the residual state" if c["truth"] == "other"
             else "no, the true state was in the model") + " |")
        add(f"| {QUESTIONS[6]} | the agent chose `{f['action']}`; "
            f"`{f['best']}` was correct |")
        add(f"| {QUESTIONS[7]} | " +
            ("yes — remediation is cheap in every state, so the agent "
             "remediates even when it holds real probability on a state that "
             "does not need it" if cat == "Wrong cost assumption"
             else "the costs are not what produced this one") + " |")
        add(f"| {QUESTIONS[8]} | " +
            ("it did buy the probe" if f["probed"]
             else "yes, in hindsight — but its expected value was below its "
                  "price, so buying it was the correct decision on the "
                  "information available") + " |")
        add(f"| {QUESTIONS[9]} | " +
            ("**yes** — this is exactly what the residual-state escalation "
             "trigger is for" if c["truth"] == "other"
             else "no — nothing about this case is unusual to the model") + " |")
        add("")

    cats = {}
    for f in fails:
        cats[classify(f)[0]] = cats.get(classify(f)[0], 0) + 1
    add("### All failures by category\n")
    add("| Category | Count | Share of failures |")
    add("|---|---|---|")
    for k, v in sorted(cats.items(), key=lambda kv: -kv[1]):
        add(f"| {k} | {v} | {v / len(fails) * 100:.1f}% |")
    add("")
    add("The distribution is the finding, not any single case. One category")
    add("dominating means the agent has one systematic weakness rather than")
    add("scattered bad luck, and a systematic weakness is fixable.\n")

    add("## Part 2: what the agent learns, and why it is wrong\n")
    add("The agent now acts, sometimes finds out it was wrong, and updates its")
    add("prior. The problem is not the updating. It is what reaches the agent.\n")
    add("| Situation | How often anyone finds out |")
    add("|---|---|")
    add(f"| Remediated something that did not need it | {DISCOVERY[('remediate', 'wrong')]:.0%} |")
    add(f"| Dismissed a key that was live | {DISCOVERY[('dismiss', 'wrong')]:.0%} |")
    add(f"| Decided correctly | {DISCOVERY[('any', 'right')]:.0%} |")
    add("")
    add("A wasted rotation breaks somebody's deploy and generates a ticket the")
    add("same afternoon. A live key left in place does nothing at all today,")
    add("and if it does something in four months nobody connects it back to")
    add("this finding. **The agent hears about its false positives and almost")
    add("never about its false negatives.**\n")
    add(f"Over 4,000 findings, {learned['discovered']:.1%} of outcomes were")
    add("discovered and fed back. Here is what the agent came to believe:\n")
    add("| State | True world | What the agent learned | Error |")
    add("|---|---|---|---|")
    for s in W.STATES:
        t, l = W.PRIOR[s], learned["prior"][s]
        add(f"| {s} | {t:.4f} | {l:.4f} | {l - t:+.4f} |")
    add("")
    worst = max(W.STATES, key=lambda s: abs(learned["prior"][s] - W.PRIOR[s]))
    d = learned["prior"][worst] - W.PRIOR[worst]
    add(f"The largest distortion is **{worst}**, off by {d:+.4f}.")
    add("")
    add("The direction is what matters. The states the agent remediates")
    add("unnecessarily are the ones it keeps being told about, so their counts")
    add("rise; the state it under-reacts to is the one nobody reports, so its")
    add("count lags. An agent learning from this feedback becomes progressively")
    add("more confident that findings are harmless, in a world where they are")
    add("not. **The feedback loop corrects the over-remediation bias and keeps")
    add("going, into the error that costs 2400 minutes instead of 30.**\n")
    add(f"Cost with learning: {learned['cost']:.2f} min/finding. "
        f"Frozen prior: {frozen['cost']:.2f}.")
    add("")
    add("The practical conclusion is not *do not learn*. It is that an agent")
    add("must weight feedback by how likely it was to hear about the outcome at")
    add("all, and this one does not. That is the clearest single improvement")
    add("left in the design, and it is not implemented here.\n")

    add("## Part 3: noticing that the world has moved\n")
    add("The prior was set from how the world used to be. Nothing breaks loudly")
    add("when that stops being true -- the agent keeps producing confident")
    add("answers from beliefs that no longer describe anything.\n")
    add("The alarm compares the evidence distribution the agent *expects* with")
    add("the one it *observes* over a rolling window of 250 findings, using")
    add("Jensen-Shannon divergence. KL divergence is the natural first choice")
    add("and is unusable here: it is asymmetric, so the answer depends on which")
    add("distribution you name first, and it returns infinity the first time a")
    add("genuinely new kind of evidence appears -- which is precisely the")
    add("moment you need a number rather than an overflow. JSD is symmetric,")
    add("bounded by 1 bit, and finite always.\n")
    add(f"At finding 1,500 the world shifts: `fake` becomes "
        f"{shifted['fake'] / W.PRIOR['fake']:.1f}x more common. Nothing tells")
    add("the agent.\n")
    add("| Window ending at | JSD (bits) |")
    add("|---|---|")
    for d_ in drift[::4]:
        mark = " ← shift" if 1500 <= d_["i"] < 1600 else ""
        add(f"| {d_['i']} | {d_['jsd']:.5f}{mark} |")
    add("")
    add(f"Before the shift, JSD sits between {min(pre):.5f} and "
        f"{max(pre):.5f}. After it, the mean is {sum(post) / len(post):.5f} "
        f"and individual windows run from {min(post):.5f} to {max(post):.5f}.\n")
    add("Eyeballing one run is not an answer, and the single run above is")
    add("ambiguous: the ranges overlap. So the alarm is calibrated properly")
    add("instead. The threshold is the highest divergence seen across eight")
    add("**control runs in which nothing changes**, and detection and")
    add("false-alarm rates are then measured on separate held-out runs against")
    add("that fixed threshold. A threshold read off the same run you evaluate")
    add("is guaranteed to look good and means nothing.\n")
    add("| Window | Shift in `fake` | Threshold (bits) | Detection | False alarms |")
    add("|---|---|---|---|---|")
    for r in sweep:
        add(f"| {r['window']} | x{r['mult']:.1f} | {r['threshold']:.5f} | "
            f"**{r['detect']:.0%}** | {r['false']:.1%} |")
    add("")
    add("Two things in that table are worth reading carefully.\n")
    add("**The single run was misleading and the sweep corrected it.** Judging")
    add("by eye off one seed suggested the alarm did not separate signal from")
    add("noise. With a threshold calibrated on held-out control runs it")
    add("separates them cleanly. The difference is not a better alarm; it is a")
    add("better experiment. One run of a stochastic process is an anecdote.\n")
    add("**The threshold falls faster than the window grows.** Doubling the")
    add("window from 250 to 500 findings drops the noise floor from 0.01767 to")
    add("0.00736 bits, better than half, because the divergence of an empirical")
    add("distribution from its source shrinks with sample size while a real")
    add("shift does not shrink at all. That is the whole mechanism: wait longer,")
    add("and the noise goes away while the signal stays.\n")
    add("The cost is latency, and it is the only real trade here. On a queue of")
    add("a few hundred findings a week, a 500-case window means the agent runs")
    add("on stale beliefs for something like a fortnight before the alarm")
    add("clears the floor. It is a smoke detector, not a tripwire, and a paper")
    add("that reports the detection rate without reporting the delay has")
    add("answered half the question.\n")
    add("One limitation I cannot sweep away. This alarm watches the free")
    add("features, which carry zero bits about live-versus-revoked. It will")
    add("therefore notice a shift in how many findings are fake and stay")
    add("completely silent on a shift in how many are still live -- which is")
    add("the shift that would actually cost something. Watching the probe")
    add("channel instead would fix that, and the probe is bought on a minority")
    add("of findings, so the effective window would be several times longer")
    add("again. Detect the drift that matters and wait months, or detect the")
    add("drift that does not and wait weeks. That is not answered here.\n")

    with open(os.path.join(OUT, "feedback.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L[:60]))
    print("...")


if __name__ == "__main__":
    main()
