"""Week 2, commit 9: move the agent to a credential format that does not hide
the identifier.

Section 17 of the brief asks what breaks when the environment changes. The
environment I picked is not a bigger company -- rotation compliance and registry
coverage are already swept in `registry.py`, so that move changes two parameters
I have already varied and would produce a section saying "we did this".

The change that actually breaks something is the credential format. Everything
in this project rests on one property of an OpenAI key: **the whole string is
secret, so the only way to learn whether it works is to use it**, and using a
credential found in a repository is the thing the agent is forbidden to do. That
is where the zero-bits invariance comes from, and it is why the probe -- an
admin-API call about my own account -- is the only channel that touches the axis.

An AWS access key is not like that. It arrives in two halves: `AKIA...`, the
access key ID, which is a public identifier and appears in CloudTrail logs, and
the secret half. Given the identifier alone, the agent can ask **its own** IAM
API whether that key ID exists in the account and whether it is Active. No
credential found in a repository is ever used. The forbidden act is not required,
and the answer is free.

So: same company, same private repositories, same scanner, same five states,
same cost matrix. One thing changes -- the finding is an AWS access key rather
than an OpenAI key -- and the identifier lookup becomes available at zero cost.

  IDENT -- `active` | `inactive` | `absent`

The likelihood table below is not invented freely; three of its five rows are
forced by what the field means:

  live       -> the key ID is in the account and Active. Not an estimate.
  revoked    -> present but disabled, or deleted. Also not an estimate.
  fake       -> a fabricated AKIA-shaped string was never in the account.
                `absent`, for the same reason the scope probe's `absent`
                column reads `fake` in `scope_probe.py`.
  zero_scope -> **identical to `live`.** A key authorised for nothing is
                still Active. IAM reports status, not power.
  other      -> not a credential, so not in the account.

That fourth row is the point of the experiment and I did not see it coming when
I chose the environment. I expected the identifier to dissolve the project's
central problem. Instead it dissolves one axis and leaves an identical pair of
rows on another. The question this script answers is therefore not "does the
agent survive" but "what does it need once the thing it was built for is free".

Writes results/generalization.md and results/generalization.json.
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
IDENT = ["active", "inactive", "absent"]

# How reliably the identifier lookup reports what it means. Three of the five
# rows are definitional rather than estimated; see the module docstring.
L_IDENT = {
    "live":       {"active": 0.98, "inactive": 0.01, "absent": 0.01},
    "revoked":    {"active": 0.02, "inactive": 0.96, "absent": 0.02},
    "fake":       {"active": 0.00, "inactive": 0.00, "absent": 1.00},
    "zero_scope": {"active": 0.98, "inactive": 0.01, "absent": 0.01},
    "other":      {"active": 0.00, "inactive": 0.02, "absent": 0.98},
}

PROBE_TABLES = [W.L_PROBE, S.L_SCOPE]
PROBE_SPACES = [R.PROBE, S.SCOPE]

# The identifier lookup and the scope field both report one underlying event:
# is this credential in our account at all. Treating them as conditionally
# independent double-counts that event and manufactures impossible observations
# -- an `absent` identifier beside a `nonzero` scope reading, which says the key
# is not in the account and also that we read its permissions.
#
# The first version of this script did exactly that, and the result was that
# reading scope in the AWS world made the agent WORSE by 0.87 minutes a finding.
# That is not a property of AWS. It is stop-rule 5 in the brief -- correlated
# evidence sources feel like more information and are not -- appearing as a bug
# in my own experiment rather than as a paragraph in my own paper.
#
# The fix is to say what is actually true of the AWS deployment: scope is read
# only for a key the identifier has already located, so it has two outcomes
# rather than three, and its table is renormalised over them.
SCOPE_PRESENT = ["zero", "nonzero"]
L_SCOPE_PRESENT = {
    s: {o: S.L_SCOPE[s][o] / (S.L_SCOPE[s]["zero"] + S.L_SCOPE[s]["nonzero"])
        for o in SCOPE_PRESENT}
    for s in W.STATES
}


def draw(table, s, rng):
    r, acc = rng.random(), 0.0
    for key, p in table[s].items():
        acc += p
        if r <= acc:
            return key
    return key


def mutual_information(belief, table, space, pair):
    """I(evidence; which of `pair`), conditioned on the state being in `pair`.

    This is the quantity the Week 1 invariance is stated in. Restricting to a
    pair first is what makes it the question 'does this evidence separate these
    two states', rather than 'does it say anything about anything'.
    """
    b = I.restrict(belief, pair)
    if b is None:
        return 0.0
    h0 = I.H(b)
    h_cond = 0.0
    for o in space:
        po = sum(b[s] * table[s][o] for s in pair)
        if po <= 0:
            continue
        post = {s: b[s] * table[s][o] / po for s in pair}
        h_cond += po * I.H(post)
    return I.snap(h0 - h_cond)


def evaluate(cases, use_ident, use_scope=True, oracle_lr=False):
    """One agent, run in one world.

    `use_ident` is the environment: False is OpenAI, True is AWS. Everything
    else -- prior, cost matrix, free features, probe, escalation rules -- is
    held identical, so any difference is the credential format and nothing else.
    """
    rng = random.Random(4242)
    # In the AWS world the identifier has already settled whether the key is in
    # the account, so scope is the two-outcome present-only field; carrying the
    # three-outcome table there would count one event twice.
    scope_tab = L_SCOPE_PRESENT if use_ident else S.L_SCOPE
    scope_space = SCOPE_PRESENT if use_ident else S.SCOPE
    tables = [W.L_PROBE, scope_tab] if use_scope else [W.L_PROBE]
    spaces = [R.PROBE, scope_space] if use_scope else [R.PROBE]

    regret = cost = 0.0
    probes = escalations = 0
    hit = {s: 0 for s in W.STATES}
    tot = {s: 0 for s in W.STATES}

    for case in cases:
        t = case["truth"]
        tabs, ev = [W.L_CONTEXT, W.L_FORM], [case["context"], case["form"]]
        if use_ident:
            tabs.append(L_IDENT)
            ev.append(draw(L_IDENT, t, rng))
        b = I.update(dict(W.PRIOR), tabs, tuple(ev))

        if oracle_lr and t in ("live", "revoked"):
            m = b["live"] + b["revoked"]
            b = {s: (m if s == t else 0.0) if s in ("live", "revoked") else b[s]
                 for s in W.STATES}
            tot_b = sum(b.values())
            b = {s: v / tot_b for s, v in b.items()}

        extra = 0.0
        now = W.expected_cost(b, W.cheapest(b, COST), COST)
        after = 0.0
        for o in product(*spaces):
            po = I.marginal(b, tables, o)
            if po <= 0:
                continue
            after += po * W.expected_cost(
                I.update(b, tables, o), W.cheapest(I.update(b, tables, o), COST),
                COST)
        if now - after > R.K["probe"]:
            obs = [case["probe"]]
            if use_scope:
                obs.append(draw(scope_tab, t, rng))
            b = I.update(b, tables, tuple(obs))
            extra = R.K["probe"]
            probes += 1

        a = W.cheapest(b, COST)
        if b["other"] > F.P_OTHER_TRIGGER:
            a = "escalate"
        elif max(COST[a][s] for s in W.STATES) > F.CEILING:
            a = "escalate"
        if a == "escalate":
            escalations += 1

        best = min(W.TERMINAL, key=lambda x: COST[x][t])
        regret += COST[a][t] - COST[best][t]
        cost += COST[a][t] + extra
        tot[t] += 1
        if a == best:
            hit[t] += 1

    n = len(cases)
    rec = {s: (hit[s] / tot[s] if tot[s] else None) for s in W.STATES}
    seen = [v for v in rec.values() if v is not None]
    return dict(regret=regret / n, cost=cost / n, probes=probes / n,
                escalated=escalations / n, per_class=rec,
                balanced=sum(seen) / len(seen))


def one_variable(cases):
    """Section 17.2: change one variable at a time and say what breaks.

    The brief names three. Two are computed here. The third -- historical data
    becoming unreliable -- is W2-7 and W2-8 and is not recomputed.
    """
    global COST
    keep = COST
    rows = []

    # 1. the cost of a false negative becomes 100x higher.
    # The false negative here is dismissing a key that is live, so the lever is
    # the exploitation probability that cost is built from. p = 0.10 is the
    # committed value; the cost cannot literally go 100x because p is bounded
    # at 1, and that bound is itself the finding.
    for factor, p in ((1, F.P_EXPLOIT), (2.5, 0.25), (5, 0.50), (10, 1.00)):
        COST = F.costs(p_exploit=p)
        r = evaluate(cases, use_ident=False)
        rows.append(dict(kind="false-negative cost", factor=factor,
                         p_exploit=p,
                         dismiss_live=COST["dismiss"]["live"], **{
                             k: r[k] for k in
                             ("regret", "cost", "probes", "escalated",
                              "balanced")}))
    COST = keep

    # 2. obtaining evidence becomes 10x more expensive.
    probe_rows = []
    keep_probe = R.K["probe"]
    for factor in (1, 2, 5, 10, 20):
        R.K["probe"] = keep_probe * factor
        r = evaluate(cases, use_ident=False)
        probe_rows.append(dict(factor=factor, price=R.K["probe"], **{
            k: r[k] for k in ("regret", "cost", "probes", "escalated",
                              "balanced")}))
    R.K["probe"] = keep_probe

    return rows, probe_rows


def main():
    os.makedirs(OUT, exist_ok=True)
    cases = W.build_cases(W.N_CASES, W.SEED)

    openai = evaluate(cases, use_ident=False)
    aws = evaluate(cases, use_ident=True)
    openai_oracle = evaluate(cases, use_ident=False, oracle_lr=True)
    aws_noscope = evaluate(cases, use_ident=True, use_scope=False)
    openai_noscope = evaluate(cases, use_ident=False, use_scope=False)

    ceiling = openai["regret"] - openai_oracle["regret"]
    recovered = (openai["regret"] - aws["regret"]) / ceiling if ceiling else 0.0

    prior = dict(W.PRIOR)
    free = [
        ("repository context", W.L_CONTEXT, R.CONTEXT),
        ("well-formedness", W.L_FORM, R.FORM),
        ("identifier lookup", L_IDENT, IDENT),
    ]
    axes = {
        "live vs revoked": ("live", "revoked"),
        "live vs zero_scope": ("live", "zero_scope"),
        "live vs fake": ("live", "fake"),
    }
    mi = {name: {ax: mutual_information(prior, tab, sp, pair)
                 for ax, pair in axes.items()}
          for name, tab, sp in free}

    scope_value_openai = openai_noscope["regret"] - openai["regret"]
    scope_value_aws = aws_noscope["regret"] - aws["regret"]

    fn_rows, probe_rows = one_variable(cases)

    payload = dict(seed=W.SEED, n=W.N_CASES, l_ident=L_IDENT,
                   false_negative=fn_rows, evidence_cost=probe_rows,
                   openai=openai, aws=aws, openai_oracle=openai_oracle,
                   aws_noscope=aws_noscope, openai_noscope=openai_noscope,
                   lr_ceiling=ceiling, recovered=recovered,
                   mutual_information=mi,
                   scope_value=dict(openai=scope_value_openai,
                                    aws=scope_value_aws))
    with open(os.path.join(OUT, "generalization.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    L = []
    add = L.append
    add("# The same agent, on a credential that does not hide its identifier\n")
    add("Everything in this project rests on one property of an OpenAI key: the")
    add("whole string is secret, so the only way to learn whether it works is to")
    add("use it -- and using a credential found in a repository is the one thing")
    add("the agent may not do. That is where the zero-bits invariance comes from.\n")
    add("An AWS access key is not like that. The `AKIA...` half is a public")
    add("identifier. Given it alone the agent can ask **its own** IAM API whether")
    add("that key ID is present and Active, without ever touching the secret")
    add("half. Same company, same private repositories, same scanner, same five")
    add("states, same cost matrix. One thing changes, and it is free.\n")

    add("## What the identifier separates, in bits\n")
    add("| Free evidence | live vs revoked | live vs zero_scope | live vs fake |")
    add("|---|---|---|---|")
    for name, _, _ in free:
        add(f"| {name} | {mi[name]['live vs revoked']:.4f} | "
            f"{mi[name]['live vs zero_scope']:.4f} | "
            f"{mi[name]['live vs fake']:.4f} |")
    add("")
    add("The first two rows are the Week 1 result: the text features carry")
    add("exactly nothing about live versus revoked. The third row is the")
    add("environment change, and it does two things at once.\n")
    add(f"**It resolves the axis the whole project was built around** --")
    add(f"{mi['identifier lookup']['live vs revoked']:.4f} bits, against")
    add("0.0000 from everything that was free before.\n")
    add(f"**And it carries {mi['identifier lookup']['live vs zero_scope']:.4f}")
    add("bits about live versus zero_scope.** That is not a rounding artefact,")
    add("it is exact, and it is exact for the same reason the Week 1 result was:")
    add("the two rows are identical. IAM reports whether a key is Active. A key")
    add("authorised for nothing is Active. **The invariance does not disappear")
    add("when the identifier becomes public. It moves.**\n")

    add("## What it does to the agent\n")
    add("| | OpenAI (Week 2 agent) | AWS (same agent) |")
    add("|---|---|---|")
    add(f"| regret, min/finding | {openai['regret']:.2f} | {aws['regret']:.2f} |")
    add(f"| total cost, min/finding | {openai['cost']:.2f} | {aws['cost']:.2f} |")
    add(f"| probe bought | {openai['probes'] * 100:.1f}% | {aws['probes'] * 100:.1f}% |")
    add(f"| sent to a human | {openai['escalated'] * 100:.1f}% | "
        f"{aws['escalated'] * 100:.1f}% |")
    add(f"| balanced accuracy | {openai['balanced']:.3f} | {aws['balanced']:.3f} |")
    for s in W.STATES:
        o = openai["per_class"][s]
        a = aws["per_class"][s]
        add(f"| `{s}` recall | " +
            (f"{o:.3f}" if o is not None else "--") + " | " +
            (f"{a:.3f}" if a is not None else "--") + " |")
    add("")
    add(f"Regret falls from {openai['regret']:.2f} to {aws['regret']:.2f} minutes")
    add(f"per finding. W2-5 priced perfect live-versus-revoked knowledge at")
    add(f"{ceiling:.2f} minutes of the available regret; the free identifier")
    add(f"recovers **{recovered * 100:.1f}%** of it, at zero cost, on every")
    add("finding rather than on the minority where a probe was worth buying.\n")

    add("## A component that survives the move and stops earning its place\n")
    add("W2-6 swept the scope field's reliability and found that about 88% of")
    add("its value came from its `absent` column -- which detects `fake` -- and")
    add("only 12% from the parameter I had invented for detecting `zero_scope`.")
    add("It was mostly a `fake` detector arriving on the same call.\n")
    add("The AWS identifier reports `absent` for free, before the scope field is")
    add("bought. So the 88% is already paid for by something else, and what is")
    add("left for scope is the 12%:\n")
    add("| | value of reading scope, min/finding | `zero_scope` recall |")
    add("|---|---|---|")
    add(f"| OpenAI | {scope_value_openai:+.2f} | "
        f"{openai['per_class']['zero_scope']:.3f} |")
    add(f"| AWS | {scope_value_aws:+.2f} | "
        f"{aws['per_class']['zero_scope']:.3f} |")
    add("")
    add("**Twelve per cent is not enough to pay for the call.** The field goes")
    add("from earning 2.27 minutes a finding to costing 0.23, and it never")
    add("identifies the state it exists for in either world. W2-6 measured how")
    add("much of it was load-bearing; this measures what happens when the rest")
    add("is supplied for free, and the answer is that the remainder does not")
    add("stand on its own.\n")
    add("> **A bug worth recording, because the brief names it.** The first")
    add("> version of this experiment drew the scope reading independently of")
    add("> the identifier lookup and had the agent multiply both likelihoods.")
    add("> Both channels report one underlying event -- is this credential in")
    add("> our account -- so that double-counts it, and generates observations")
    add("> that cannot occur: an `absent` identifier beside a `nonzero` scope")
    add("> reading says the key is not in the account and also that we read its")
    add("> permissions. It made scope look 0.87 minutes harmful rather than")
    add("> 0.23. Stop-rule 5 in the brief is exactly this -- correlated evidence")
    add("> sources feel like more information and are not -- and I met it as a")
    add("> defect in my own simulator before I met it as a paragraph in my own")
    add("> paper. The fix is the honest statement of the deployment: you read a")
    add("> key's permissions only once you have located the key, so scope has")
    add("> two outcomes there, not three.\n")
    add("## What is portable and what was local\n")
    add("| Component | Survives the move? |")
    add("|---|---|")
    add("| The cost matrix and the derived threshold | **Yes.** Nothing about the credential format touches what an outage or a breach costs |")
    add("| Escalation as a rule rather than a priced action | **Yes.** It triggers on `other` and on worst-case cost, neither of which the identifier touches |")
    add("| Buy evidence only when an outcome could change the action | **Yes.** It is the reason the probe is not bought here despite still being informative |")
    add("| The zero-bits invariance | **No, and this is the finding.** It is a property of the credential format, not of secret scanning. It survives as a *different* invariance on a different pair of states |")
    add("| The probe as the project's central mechanism | **No.** It is bought on "
        f"{aws['probes'] * 100:.1f}% of findings here against "
        f"{openai['probes'] * 100:.1f}% |")
    add("| The scope field as a purchase | **No.** Its `absent` column is supplied free here; the 12% that remains does not pay for the call |")
    add("| `zero_scope` as an unresolved state | **Yes, and it gets worse.** Recall falls to 0.000, because the one channel that touched it no longer earns its way into the policy |")
    add("")
    add("## Then change one variable at a time\n")
    add("### 1. The cost of a false negative rises\n")
    add("The false negative here is dismissing a key that is live, and that cost")
    add("is not a free parameter -- it is P(exploitation) times a breach. So the")
    add("lever is the probability, and the first thing the request exposes is")
    add("that **it cannot be granted**: a probability is bounded at 1, so the")
    add("cost of this error can rise by a factor of ten and no further. Asking")
    add("for a hundredfold increase is asking for a probability of 10.\n")
    add("| Factor | p_exploit | Cost of dismissing a live key | Regret | Probe bought | Human | Balanced acc. |")
    add("|---|---|---|---|---|---|---|")
    for r in fn_rows:
        add(f"| x{r['factor']} | {r['p_exploit']:.2f} | {r['dismiss_live']:.0f} | "
            f"{r['regret']:.2f} | {r['probes'] * 100:.1f}% | "
            f"{r['escalated'] * 100:.1f}% | {r['balanced']:.3f} |")
    add("")
    add("**Regret is worst in the middle, not at the top**, and so is human")
    add("load: 27.4% of findings escalated at p = 0.25 against 12.6% at p = 1.00,")
    add("where the stakes are four times higher. That is not noise. It is two")
    add("design decisions from two different commits disagreeing, and the")
    add("mechanism is worth stating exactly.\n")
    add("`dismiss` is the only action whose worst case moves with p. At p = 0.10")
    add("its worst case is 244 minutes, under the 400-minute ceiling W2-4b")
    add("imposed, so the agent may take it. At p = 0.25 the worst case is 604 and")
    add("the ceiling forbids it -- but on expected cost dismiss is *still the")
    add("cheapest action* on 57 of 500 findings. Those 57 go to a human, not")
    add("because the agent is unsure but because the action it wants is no longer")
    add("permitted. By p = 0.50, `revoke` has overtaken dismiss on expected cost")
    add("anyway; revoke's worst case is 332, under the ceiling, so the ceiling")
    add("stops binding and escalation falls back to 1.0% plus the residual rule.\n")
    add("**A worst-case ceiling is not a monotone safety dial.** Raising the")
    add("stakes can reduce human involvement, because it can push the agent off")
    add("a cheap-in-expectation action that is expensive in the worst case and")
    add("onto an expensive-in-expectation action that is not. The band where the")
    add("two rules disagree is the band that costs the most, and nothing in")
    add("either rule announces where that band is.\n")
    add("Balanced accuracy tells the second half of the story. It falls from")
    add("0.459 to 0.197 and stays there for every p above 0.10, because once")
    add("dismiss leaves the policy there is no action left that means *this")
    add("string is harmless*, and the states that need one -- `fake` and")
    add("`zero_scope` -- become unlabellable again. That is the W2-4 failure")
    add("returning, from the opposite direction: the first time it was caused by")
    add("a cost that was too high by accident, and here by one that is too high")
    add("on purpose.\n")
    add("### 2. Obtaining evidence becomes ten times more expensive\n")
    add("| Factor | Probe price, min | Regret | Probe bought | Human | Balanced acc. |")
    add("|---|---|---|---|---|---|")
    for r in probe_rows:
        add(f"| x{r['factor']} | {r['price']:.0f} | {r['regret']:.2f} | "
            f"{r['probes'] * 100:.1f}% | {r['escalated'] * 100:.1f}% | "
            f"{r['balanced']:.3f} |")
    add("")
    add("The probe dies between x2 and x5. At six minutes it is still bought on")
    add("16.0% of findings; at fifteen it is bought on none, and regret saturates")
    add("at 10.50 -- exactly the no-scope number, because the scope field rides")
    add("on the probe and goes with it. **The policy does not degrade smoothly")
    add("under evidence cost, it switches off.** The agent does not shift from")
    add("asking to escalating either: human load *falls* from 2.8% to 1.0%,")
    add("because the ceiling and residual triggers never depended on the probe.")
    add("An expensive-evidence deployment does not get a more cautious agent, it")
    add("gets a blinder one that is no more likely to ask for help.\n")
    add("### 3. Historical data becomes unreliable\n")
    add("This one is already answered, and it is the reason W2-7 and W2-8 exist.")
    add("The priors and every likelihood row were estimated, so *unreliable")
    add("history* is not a hypothetical here -- it is the standing condition.")
    add("W2-7 generates the world from different tables and measures the gap:")
    add("policy conclusions survive in 100% of worlds, the structural conclusion")
    add("does not. W2-8 gives the agent a way to notice, from its own biased")
    add("feedback, at 100% detection for the differences that cost it anything.")
    add("What the agent should do while it is unsure whether its own priors are")
    add("valid is the one part still unanswered: it can raise its hand and it")
    add("cannot repair itself, because relaxing the invariance means estimating")
    add("two rows from labels it does not have enough of.\n")

    add("## The honest reading\n")
    add("The honest reading is that the paper's machinery is portable and the")
    add("paper's *headline* is not. A reviewer told me the Week 1 result was a")
    add("property of credential formats that hide the identifier rather than of")
    add("secret scanning. This is that claim with a number attached, and the")
    add("number says the reviewer was right -- but also that the problem does not")
    add("go away when the format changes, because the states that remain")
    add("indistinguishable are simply a different pair.\n")

    with open(os.path.join(OUT, "generalization.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
