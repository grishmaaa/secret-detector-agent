"""Week 2, commit 4b: three fixes to things that were assumptions pretending
to be results.

FIX 1 -- the exploitation probability.

  Week 1 priced dismissing a live key at 2400 minutes: a breach and its
  cleanup. That number silently assumes every dismissed live key IS breached.
  It will not be. A leaked credential in a private repository is exploited with
  some probability, and the honest cost is that probability times the breach,
  not the breach itself. Week 1 was running with p_exploit = 1.0 without ever
  writing it down. It is the single assumption that made the agent unable to
  say no to anything.

FIX 2 -- escalation as a rule, not a competitor.

  Escalation never fired because it was made to compete on expected cost, and
  human attention priced at 30 minutes always loses to an action that costs
  less. That is the wrong shape. Some decisions go to a person because of what
  is at stake, not because the agent is unsure -- confidence is not
  authorisation. So escalation becomes a ceiling rule applied BEFORE the cost
  comparison: if the worst outcome of the chosen action exceeds a ceiling, a
  human sees it regardless of how confident the agent is.

FIX 3 -- measuring the 92% lie.

  An agent that remediates everything scores recall 1.000 and looks excellent.
  It has not learned to tell anything apart; it has learned to always say yes.
  Overall accuracy hides this completely. Per-class recall does not, so every
  policy is now scored per state.

Writes results/fixes.md and results/fixes.json.
"""

import json
import os

import run_experiment as R
import week2_experiment as W
import information as I
import scope_probe as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

# ASSUMPTION, and now an explicit one. The one quantified datapoint anywhere is
# a vendor experiment in which 2 of 75 leaked keys drew activity beyond a
# validity check inside 12 hours. That is 0.027, on a public exposure, over a
# short window. This model is scoped to private repositories, where the hazard
# is lower. 0.10 is a deliberate over-estimate of that figure, chosen to be
# conservative rather than favourable, and swept below because it is the
# weakest number in the model.
P_EXPLOIT = 0.10

# ASSUMPTION. A wrong decision whose worst outcome exceeds this many minutes
# goes to a person whatever the agent believes.
CEILING = 400


def costs(p_exploit=P_EXPLOIT):
    """The Week 2 cost matrix with the breach cost put behind its probability.

    The residual state's price MUST be recomputed after the breach cost moves.
    It is defined as the mean over the known states, so leaving it at its old
    value silently smuggles the un-discounted 2400 back in through a state that
    is supposed to represent ignorance. That bug cost an afternoon: the residual
    was priced at 602 minutes to dismiss, which blocked every dismissal the fix
    was meant to unlock.
    """
    c = {a: dict(W.COST[a]) for a in W.COST}
    breach = R.COST["dismiss"]["live"]          # 2400, the full breach
    residual = 5                                 # audit work even when unexploited
    c["dismiss"]["live"] = p_exploit * breach + (1 - p_exploit) * residual
    c["dismiss"]["zero_scope"] = 5
    known = ("live", "revoked", "fake", "zero_scope")
    for a in ("dismiss", "revoke", "rotate"):
        c[a]["other"] = sum(c[a][s] for s in known) / len(known)
    c["escalate"] = {s: R.K["human"] + min(c[a][s] for a in ("dismiss", "revoke", "rotate"))
                     for s in W.STATES}
    return c


def worst_case(action, cost):
    return max(cost[action][s] for s in W.STATES)


P_OTHER_TRIGGER = 0.05


def make_policy(cost, escalation=False):
    """P5: cost-derived, with the probe, plus escalation as a RULE.

    Two triggers, both taken from the brief's list, and neither of them a cost
    comparison. Escalation stopped competing on expected cost because it always
    loses that competition; it now fires on what is at stake and on what the
    model cannot represent.
    """
    def policy(case):
        ev = {"context": case["context"], "form": case["form"]}
        b = W.posterior(ev)
        extra = 0
        if W.evsi_probe(b, cost) > R.K["probe"]:
            b = W.posterior(dict(ev, probe=case["probe"]))
            extra = R.K["probe"]
        a = W.cheapest(b, cost)
        if escalation:
            # trigger 1: this case may be a state the model does not have
            if b["other"] > P_OTHER_TRIGGER:
                return "escalate", extra, b
            # trigger 2: what is at stake exceeds a ceiling, however sure we are
            exposure = sum(b[s] * cost[a][s] for s in W.STATES
                           if cost[a][s] > CEILING)
            if exposure > 0 and max(cost[a][s] for s in W.STATES) > CEILING:
                return "escalate", extra, b
        return a, extra, b
    return policy


def make_full(cost):
    """P6: everything. Corrected breach cost, escalation as a rule, and the
    scope field on the probe that was already being paid for.

    This is the agent the three fixes produce together, and it is the only one
    that can distinguish a key authorised for nothing from a key that works --
    or a revoked key from a live one, since `absent` appears in the scope
    column for revoked keys and never for live ones.
    """
    import random
    rng = random.Random(W.SEED + 1)

    def draw_scope(case):
        r, acc = rng.random(), 0.0
        for k, p in S.L_SCOPE[case["truth"]].items():
            acc += p
            if r <= acc:
                return k
        return k

    def policy(case):
        ev = {"context": case["context"], "form": case["form"]}
        b = W.posterior(ev)
        extra = 0
        if S.evsi(b, [W.L_PROBE, S.L_SCOPE], [R.PROBE, S.SCOPE]) > R.K["probe"]:
            b = I.update(b, [W.L_PROBE, S.L_SCOPE], (case["probe"], draw_scope(case)))
            extra = R.K["probe"]
        a = W.cheapest(b, cost)
        if b["other"] > P_OTHER_TRIGGER:
            return "escalate", extra, b
        if max(cost[a][s] for s in W.STATES) > CEILING:
            return "escalate", extra, b
        return a, extra, b
    return policy


def boundary(cost):
    """The intervals of P(live) on which each action wins, along the line the
    agent can actually occupy (live:revoked locked at the invariant ratio)."""
    segs, prev, start = [], None, 0.0
    pl = 0.0
    for i in range(200001):
        pl = i / 200000
        pr = pl / R.RATIO
        rest = 1 - pl - pr
        if rest < 0:
            break
        b = {"live": pl, "revoked": pr, "fake": rest * 0.93,
             "zero_scope": rest * 0.06, "other": rest * 0.01}
        a = W.cheapest(b, cost)
        if a != prev:
            if prev is not None:
                segs.append((prev, start, pl))
            prev, start = a, pl
    segs.append((prev, start, pl))
    return segs


def per_class(name, fn, cases, cost):
    """The 92% lie detector: did the agent take the right action for EACH state?"""
    tot = {s: 0 for s in W.STATES}
    hit = {s: 0 for s in W.STATES}
    acts = {s: {} for s in W.STATES}
    total_cost = 0.0
    esc = 0
    for c in cases:
        a, extra, _ = fn(c)
        t = c["truth"]
        best = min(W.TERMINAL, key=lambda x: cost[x][t])
        tot[t] += 1
        if a == best:
            hit[t] += 1
        acts[t][a] = acts[t].get(a, 0) + 1
        total_cost += cost[a][t] + extra
        if a == "escalate":
            esc += 1
    recalls = {s: (hit[s] / tot[s] if tot[s] else None) for s in W.STATES}
    seen = [v for v in recalls.values() if v is not None]
    return dict(name=name, per_class=recalls, actions=acts, counts=tot,
                overall=sum(hit.values()) / len(cases),
                balanced=sum(seen) / len(seen),
                cost=total_cost / len(cases),
                human_rate=esc / len(cases))


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = W.build_cases(W.N_CASES, W.SEED)
    old = costs(1.0)          # what Week 1 was actually assuming
    new = costs(P_EXPLOIT)

    sweep = []
    for p in (1.0, 0.50, 0.25, 0.10, 0.05, 0.03, 0.01):
        c = costs(p)
        sweep.append(dict(p=p, dismiss_live=c["dismiss"]["live"],
                          segments=boundary(c)))

    policies = [
        ("P2 (Week 2, as built)", W.p2, old, None),
        ("P3 (Week 2, as built)", W.p3, old, None),
        ("P5 fix 1 only", make_policy(new), new, None),
        ("P5 fix 1 + escalation rule", make_policy(new, True), new, CEILING),
        ("P6 all three fixes + scope", make_full(new), new, CEILING),
    ]
    rows = [per_class(n, f, cases, c) for n, f, c, _ in policies]

    payload = dict(p_exploit=P_EXPLOIT, ceiling=CEILING, sweep=sweep,
                   policies=[{k: v for k, v in r.items()} for r in rows])
    with open(os.path.join(OUT, "fixes.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# Three fixes\n")

    add("## Fix 1: the breach cost was standing in for a probability\n")
    add("Week 1 priced dismissing a live key at 2400 minutes and called it *a")
    add("breach and its cleanup*. A dismissed live key is not certainly")
    add("breached. The honest cost is the probability of exploitation times the")
    add("breach, and Week 1 was running at **p = 1.0** without writing it down.")
    add("That single unstated assumption is what made the agent unable to say")
    add("no to anything.\n")
    add("The one quantified datapoint anywhere is a vendor experiment where 2 of")
    add("75 leaked keys drew activity beyond a validity check within twelve")
    add("hours: 0.027, on a *public* exposure. This model is scoped to private")
    add("repositories, where the hazard is lower. **0.10 is used here as a")
    add("deliberate over-estimate**, and swept because it is now the weakest")
    add("number in the model.\n")
    add("| p_exploit | Cost of dismissing a live key | Which action wins on which range of P(live) |")
    add("|---|---|---|")
    for s in sweep:
        seg = " · ".join(f"**{a}** {lo:.4f}–{hi:.4f}" for a, lo, hi in s["segments"])
        add(f"| {s['p']:.2f} | {s['dismiss_live']:.0f} | {seg} |")
    add("")
    top = sweep[0]["segments"]
    mid = [s for s in sweep if s["p"] == P_EXPLOIT][0]["segments"]
    add(f"At p = 1.00 the agent's action ladder is `"
        + " -> ".join(a for a, _, _ in top) + "`.")
    add(f"At p = {P_EXPLOIT:.2f} it is `" + " -> ".join(a for a, _, _ in mid) + "`.")
    add("")
    add("Two things move. The band on which the agent can decline to act widens,")
    add("and the point at which it escalates from revoking to the full rotation")
    add("moves up, because rotation stops being worth its price against a")
    add("breach that is no longer treated as certain. Below p = 0.05 rotation")
    add("stops winning anywhere at all: if exploitation is rare enough, paying a")
    add("deploy cycle to avoid an outage is never the cheapest thing to do.\n")
    add("The agent did not become reckless. The cost stopped claiming a")
    add("certainty it never had.\n")

    add("## Fix 2: escalation was competing when it should have been a rule\n")
    add("Escalation never fired in any run. The reason was structural, not")
    add("numerical: it was made to compete on expected cost, and 30 minutes of")
    add("human attention added to whatever the human then does always loses to")
    add("an action costing less. Tuning the number would not repair the shape.\n")
    add("Some decisions reach a person because of what is at stake, not because")
    add("the agent is unsure. **Confidence is not authorisation.** So escalation")
    add(f"is now a rule applied before the cost comparison: if the worst outcome")
    add(f"of the chosen action exceeds **{CEILING} minutes**, a human sees it")
    add("regardless of the belief.\n")

    add("## Fix 3: the 92% lie, measured\n")
    add("An agent that remediates everything reports recall 1.000 and looks")
    add("excellent. It has not learned to tell anything apart. It has learned to")
    add("always say yes. Overall accuracy hides that completely; per-class recall")
    add("does not.\n")
    hdr = " | ".join(W.STATES)
    add(f"| Policy | {hdr} | Overall | **Balanced** | Cost | Human % |")
    add("|---" * (len(W.STATES) + 5) + "|")
    for r in rows:
        cells = " | ".join(
            f"{r['per_class'][s]:.3f}" if r["per_class"][s] is not None else "—"
            for s in W.STATES)
        add(f"| {r['name']} | {cells} | {r['overall']:.3f} | "
            f"**{r['balanced']:.3f}** | {r['cost']:.2f} | "
            f"{r['human_rate'] * 100:.1f}% |")
    add("")
    add("Balanced accuracy is the average of the per-state columns, so a policy")
    add("that only ever gets one state right cannot hide behind that state being")
    add("common.\n")
    for r in rows:
        acts = r["actions"]
        summary = "; ".join(
            f"**{s}**: " + ", ".join(f"{a} x{n}" for a, n in sorted(acts[s].items()))
            for s in W.STATES if acts[s])
        add(f"- *{r['name']}* — {summary}")
    add("")

    base, fixed = rows[0], rows[-1]
    add("### What the fixes bought\n")
    add("| | before (P2) | after (P6) |")
    add("|---|---|---|")
    for s_ in W.STATES:
        a, b = base["per_class"][s_], fixed["per_class"][s_]
        add(f"| {s_} | {a:.3f} | {b:.3f} |")
    add(f"| **overall** | {base['overall']:.3f} | {fixed['overall']:.3f} |")
    add(f"| **balanced** | {base['balanced']:.3f} | {fixed['balanced']:.3f} |")
    add(f"| cost per finding | {base['cost']:.2f} | {fixed['cost']:.2f} |")
    add(f"| sent to a human | {base['human_rate'] * 100:.1f}% | {fixed['human_rate'] * 100:.1f}% |")
    add("")
    add("The agent now tells things apart. `fake` went from never being handled")
    add("correctly to 95%; `zero_scope` from nothing to 29%; the balanced score")
    add(f"from {base['balanced']:.3f} to {fixed['balanced']:.3f}. It is also")
    add("cheaper, which is the part that matters: this is not accuracy bought")
    add("with money.\n")
    add("Note that `live` fell from 1.000 to "
        f"{fixed['per_class']['live']:.3f}. **That is the fix working, not")
    add("failing.** A policy that scores 1.000 on the majority class does so by")
    add("never declining, and the price of never declining was every other")
    add("column reading zero. Giving up 1.4% of one column to gain 95 points on")
    add("another is the trade the whole exercise was about.\n")

    add("### What is still broken\n")
    add(f"**`revoked` is at {fixed['per_class']['revoked']:.3f}.** Barely moved.")
    add("This is the Week 1 invariance, and no cost fix can touch it: the free")
    add("features carry exactly zero bits about live-versus-revoked, so the only")
    add("thing that separates them is the purchased probe. The scope field helps")
    add("a little, because `absent` appears for revoked keys and never for live")
    add("ones, but it is a weak signal and the probe is not bought on every")
    add("case. **This remains the central open problem of the project**, and it")
    add("is worth being blunt that three fixes and a new evidence channel moved")
    add("it from 0.000 to 0.109.\n")
    add(f"**`other` reads {fixed['per_class']['other']:.3f}, and the metric is")
    add("wrong rather than the agent.** Those cases are escalated, which is the")
    add("correct thing to do with a state the model cannot characterise. The")
    add("scoring compares against the cheapest action in the cost table, and the")
    add("cost table cannot price a state that exists precisely because we do not")
    add("know what it is. Escalation scores zero for doing the right thing. I am")
    add("leaving that visible rather than redefining the metric to flatter the")
    add("result.\n")

    add("### A bug worth recording\n")
    add("Fix 1 did nothing at all on the first run, and the reason is worth")
    add("keeping. The residual state's cost is defined as the mean over the")
    add("known states. When the breach cost dropped from 2400 to 244, the")
    add("residual's price was not recomputed, so `dismiss | other` sat at 602")
    add("minutes -- carrying the old un-discounted breach back into the model")
    add("through the one state that is supposed to represent ignorance. With")
    add("P(other) around 0.017 that was enough to block every dismissal the fix")
    add("was meant to unlock, and the results table was identical to the")
    add("unfixed one, which looked like the fix being ineffective rather than")
    add("being silently undone. A derived quantity that is not re-derived is a")
    add("stale constant wearing a formula's clothes.")
    add("")

    with open(os.path.join(OUT, "fixes.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
