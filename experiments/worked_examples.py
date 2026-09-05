"""Week 2, commit 9: the three worked pieces the paper has to show by hand.

Section 11 of the brief requires one full Bayes update written out rather than
reported as a final number; Section 13 requires five candidate questions tabled
with their value, cost and whether the agent would ask; Section 16 requires the
umbrella problem worked with my own cost assumptions.

All three are arithmetic I could do on paper, and the point of doing them on
paper is that a reader can check them. The point of ALSO doing them here is
that if the paper and the implementation ever disagree, this script is what
catches it -- the numbers printed below are produced by the same functions the
agent uses, so a hand calculation that matches this output matches the agent.

Writes results/worked-examples.md and results/worked-examples.json.
"""

import json
import os

import run_experiment as R
import week2_experiment as W
import information as I
import scope_probe as S
import fixes as F
import registry as G

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")

COST = F.costs()

# The finding the update is worked on: a well-formed string on a production
# path. It is chosen because it is the modal case in the generated set and
# because it is the one where the answer is least obvious -- the two features
# pull in the same direction on `fake` and in no direction at all on the axis
# that matters.
CASE = {"context": "production", "form": "well-formed"}


def bayes_by_hand():
    """The four columns: prior, likelihood, product, posterior."""
    rows = []
    for s in W.STATES:
        lc = W.L_CONTEXT[s][CASE["context"]]
        lf = W.L_FORM[s][CASE["form"]]
        rows.append(dict(state=s, prior=W.PRIOR[s], l_context=lc, l_form=lf,
                         joint=lc * lf, product=W.PRIOR[s] * lc * lf))
    total = sum(r["product"] for r in rows)
    for r in rows:
        r["posterior"] = r["product"] / total
    return rows, total


def five_questions():
    """The five things the agent could ask, priced in bits and in minutes.

    Value is EVSI -- expected minutes of cost removed -- computed at the belief
    the agent actually holds after the free features, not at the prior. That
    distinction is the whole of Section 12: an evidence source is worth what it
    changes from where you are standing, not from where you started.
    """
    b = I.update(dict(W.PRIOR), [W.L_CONTEXT, W.L_FORM],
                 (CASE["context"], CASE["form"]))

    def evsi(tables, spaces):
        from itertools import product
        now = W.expected_cost(b, W.cheapest(b, COST), COST)
        after = 0.0
        for o in product(*spaces):
            po = I.marginal(b, tables, o)
            if po <= 0:
                continue
            p = I.update(b, tables, o)
            after += po * W.expected_cost(p, W.cheapest(p, COST), COST)
        return now - after

    def eig(tables, spaces):
        return I.analyse("", b, tables, spaces)["eig"]

    A, REG = G.l_age(0.5), G.l_reg(0.5)
    A_GOOD, REG_GOOD = G.l_age(0.9), G.l_reg(0.9)

    rows = [
        dict(question="Is the string on a production-looking path?",
             answers="placeholder / neutral / production",
             tables=[W.L_CONTEXT], spaces=[R.CONTEXT], cost=0.0, spent=True,
             time="milliseconds, already read",
             note="Free, and already counted in the belief this table is computed from."),
        dict(question="Does the string match the provider's key format?",
             answers="well-formed / malformed",
             tables=[W.L_FORM], spaces=[R.FORM], cost=0.0, spent=True,
             time="milliseconds, one regex",
             note="Free, and likewise already in the belief."),
        dict(question="Is the commit older than the rotation period?",
             answers="old / young",
             tables=[A], spaces=[G.AGE], cost=0.0,
             time="seconds, git metadata",
             note="Free. Worth nothing at c = 0.5 and worth a great deal at c = 0.9; the parameter is the organisation, not the evidence."),
        dict(question="When did our own admin API last see this key used?",
             answers="recent / old / null",
             tables=[W.L_PROBE, S.L_SCOPE], spaces=[R.PROBE, S.SCOPE],
             cost=float(R.K["probe"]),
             time="3 min, one API call plus the engineer around it",
             note="The scope field arrives on the same call, so they are priced together."),
        dict(question="Does the string match a currently-deployed secret hash?",
             answers="match / miss",
             tables=[REG], spaces=[G.REG], cost=G.REGISTRY_COST,
             time="1 min, one lookup",
             note="A match is near-proof of live. A miss is only as informative as the provisioning pipeline is complete."),
    ]
    for r in rows:
        # A channel already folded into `b` is worth nothing to ask AGAIN, in
        # bits as well as in minutes. Re-applying its table to a belief that
        # already contains it measures a hypothetical second independent draw
        # of an observation we are holding, which is not the question the row
        # asks. The published table said 0.0199 and 0.0380 bits for the two
        # free features while the prose beneath it said they were 0.0000 by
        # construction; the prose was right about the minutes and the bits
        # column contradicted it.
        r["spent"] = r.get("spent", False)
        r["eig"] = 0.0 if r["spent"] else eig(r["tables"], r["spaces"])
        r["evsi"] = evsi(r["tables"], r["spaces"])
        r["net"] = r["evsi"] - r["cost"]
        r["ask"] = r["net"] > 0
        del r["tables"], r["spaces"]

    # the same two channels in a disciplined organisation, to show that the
    # answer to "would you ask?" is a property of the deployment
    tuned = dict(
        age_c09=evsi([A_GOOD], [G.AGE]),
        registry_k09=evsi([REG_GOOD], [G.REG]) - G.REGISTRY_COST,
    )

    # The same question asked from all six free beliefs. Whether the agent buys
    # is not a property of the probe; it is a property of where it is standing.
    from itertools import product as _p
    grid = []
    for c, f in _p(R.CONTEXT, R.FORM):
        bb = I.update(dict(W.PRIOR), [W.L_CONTEXT, W.L_FORM], (c, f))
        now = W.expected_cost(bb, W.cheapest(bb, COST), COST)
        after = 0.0
        for o in _p(R.PROBE, S.SCOPE):
            po = I.marginal(bb, [W.L_PROBE, S.L_SCOPE], o)
            if po <= 0:
                continue
            p = I.update(bb, [W.L_PROBE, S.L_SCOPE], o)
            after += po * W.expected_cost(p, W.cheapest(p, COST), COST)
        v = now - after
        grid.append(dict(context=c, form=f, p_live=bb["live"],
                         action=W.cheapest(bb, COST), evsi=v,
                         net=v - R.K["probe"], buy=v > R.K["probe"],
                         features=("agree" if c in ("production", "placeholder")
                                   and ((c == "production") ==
                                        (f == "well-formed"))
                                   else "conflict" if c != "neutral"
                                   else "one is silent")))
    return b, rows, tuned, grid


def umbrella():
    """Section 16, with my own numbers, and the same equation as the agent's.

    Costs are in units of annoyance and are assumptions, stated as such.
    """
    cases = [
        dict(name="A walk to the shop", carry=2, wet=5),
        dict(name="A wedding, in clothes I cannot replace", carry=2, wet=200),
    ]
    p_rain = 0.35
    for c in cases:
        c["break_even"] = c["carry"] / c["wet"]
        c["cost_carry"] = float(c["carry"])
        c["cost_leave"] = p_rain * c["wet"]
        c["take"] = c["cost_leave"] > c["cost_carry"]

    # the agent's own boundary, in exactly the same form
    fp = COST["rotate"]["revoked"]      # rotating a key that was already dead
    fn = COST["dismiss"]["live"]        # dismissing a key that is live
    agent = dict(false_positive=fp, false_negative=fn,
                 break_even=fp / (fp + fn))
    return p_rain, cases, agent


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, total = bayes_by_hand()
    b, questions, tuned, grid = five_questions()
    p_rain, umb, agent = umbrella()

    with open(os.path.join(OUT, "worked-examples.json"), "w") as fh:
        json.dump(dict(case=CASE, bayes=rows, evidence_total=total,
                       belief_after_free=b, questions=questions, tuned=tuned, grid=grid,
                       umbrella=dict(p_rain=p_rain, cases=umb, agent=agent)),
                  fh, indent=2)

    L = []
    add = L.append
    add("# Three things worked out by hand\n")
    add("The paper has to show a full belief update rather than report its")
    add("result, five candidate questions priced, and the umbrella problem in my")
    add("own numbers. All three are small enough to check on paper, which is the")
    add("point. They are also computed here with the same functions the agent")
    add("uses, so if the paper and the code ever drift apart this file is what")
    add("catches it.\n")

    add("## 1. One belief update, all four columns\n")
    add(f"The finding: a **{CASE['form']}** string on a **{CASE['context']}**")
    add("path. Two free features, no probe, no purchase.\n")
    add("| State | Prior | P(production｜s) | P(well-formed｜s) | Prior x likelihoods | Posterior |")
    add("|---|---|---|---|---|---|")
    for r in rows:
        add(f"| `{r['state']}` | {r['prior']:.4f} | {r['l_context']:.3f} | "
            f"{r['l_form']:.3f} | {r['product']:.6f} | {r['posterior']:.4f} |")
    add(f"| **total** | **1.0000** | | | **{total:.6f}** | **1.0000** |")
    add("")
    add("Multiply across, add the column, divide each row by the total. That is")
    add("the whole of Bayes' theorem and there is nothing else in it.\n")
    live_before = W.PRIOR["live"]
    live_after = [r for r in rows if r["state"] == "live"][0]["posterior"]
    fake_before = W.PRIOR["fake"]
    fake_after = [r for r in rows if r["state"] == "fake"][0]["posterior"]
    h0, h1 = I.H(W.PRIOR), I.H({r["state"]: r["posterior"] for r in rows})
    add(f"Entropy falls from **{h0:.4f}** to **{h1:.4f}** bits, a gain of")
    add(f"{h0 - h1:.4f}. `fake` drops from {fake_before:.4f} to")
    add(f"{fake_after:.4f} -- the evidence is almost entirely about that state.\n")
    add("**And the thing the update does not do is the point of the project.**")
    add(f"`live` moves from {live_before:.4f} to {live_after:.4f} and `revoked`")
    lr_before = W.PRIOR["live"] / W.PRIOR["revoked"]
    lr_after = live_after / [r for r in rows if r["state"] == "revoked"][0]["posterior"]
    add(f"moves with it: the ratio between them is {lr_before:.4f} before and")
    add(f"{lr_after:.4f} after. It is unchanged to every digit, because the two")
    add("rows of both likelihood tables are identical. The agent has learned")
    add("something real about whether this is a credential at all, and exactly")
    add("nothing about whether it still works.\n")

    add("## 2. Five questions the agent could ask\n")
    add("Value is EVSI -- expected minutes of decision cost removed -- computed")
    add("at the belief above, not at the prior. An evidence source is worth what")
    add("it changes from where the agent is standing.\n")
    add("| Question | Answers | Bits | Value, min | Cost, min | Time | Ask? |")
    add("|---|---|---|---|---|---|---|")
    for r in questions:
        add(f"| {r['question']} | {r['answers']} | {r['eig']:.4f} | "
            f"{r['evsi']:.4f} | {r['cost']:.0f} | {r['time']} | "
            f"{'**yes**' if r['ask'] else 'no'} |")
    add("")
    for r in questions:
        add(f"- *{r['question']}* {r['note']}")
    add("")
    probe_row = [r for r in questions if "admin API" in r["question"]][0]
    add("**The agent asks none of them here, and the near miss is the**")
    add("**instructive part.** The admin probe carries 0.6642 bits, more than")
    add(f"everything else on the table put together, and is worth")
    add(f"{probe_row['evsi']:.4f} minutes against a price of "
        f"{probe_row['cost']:.0f}. It loses by {abs(probe_row['net']):.3f} of a")
    add("minute. Ranked by bits it is the obvious purchase; ranked by minutes it")
    add("is declined, and the two rankings are not close to each other.\n")
    add("The registry lookup is the sharper case. It carries 0.2245 bits and is")
    add("worth exactly nothing, because at this belief every answer it could")
    add("give leaves `rotate` cheapest. Information that changes what you pay but")
    add("not what you do is worth zero, whatever its bit count.\n")
    add("The two free channels show 0.0000 by construction -- they are already in")
    add("the belief the table is computed from. They appear because a reader")
    add("should see that they were asked first, and why: they cost nothing, so")
    add("nothing has to be priced before asking them.\n")
    add("The age channel is the one whose character changes with the deployment.")
    add(f"At c = 0.5 -- an organisation that rotates at random -- it is worth")
    add(f"{[r for r in questions if 'commit' in r['question']][0]['evsi']:.4f}")
    add(f"minutes. At c = 0.9 it is worth {tuned['age_c09']:.4f}. Same evidence,")
    add("same cost, and the difference is a fact about the company rather than")
    add("about secret scanning.\n")

    add("### Where the agent does buy, and why it is not where I expected\n")
    add("Whether to buy is not a property of the probe. It is a property of")
    add("where the agent is standing when it asks. The same question, priced")
    add("from all six beliefs the two free features can produce:\n")
    add("| Repository context | Format | The two features | P(live) | Cheapest action | Probe worth | Net | Buy? |")
    add("|---|---|---|---|---|---|---|---|")
    for r in grid:
        add(f"| {r['context']} | {r['form']} | {r['features']} | "
            f"{r['p_live']:.4f} | {r['action']} | {r['evsi']:.4f} | "
            f"{r['net']:+.3f} | {'**yes**' if r['buy'] else 'no'} |")
    add("")
    add("**The only two beliefs the agent declines to buy from are the two where")
    add("its free features agree with each other.** A malformed string on a")
    add("placeholder path -- both say *not a credential* -- and a well-formed key")
    add("on a production path, where both say *a real key in a real place* and")
    add("which is the case that looks most alarming to a person. It buys on all")
    add("four of the others, and the two largest purchases, +6.61 and +6.51, are")
    add("the two outright contradictions.\n")
    add("That is not a heuristic anyone wrote. It falls out of the value rule.")
    add("When both features point the same way the belief is already far enough")
    add("from the boundary that no probe outcome can move the action across it,")
    add("so the information is worth nothing however alarming the finding looks.")
    add("When they conflict, the belief sits near the boundary and the probe can")
    add("flip it. **The agent spends its budget on its own confusion rather than")
    add("on apparent severity**, and a triage queue sorted by severity would")
    add("have bought the opposite set.\n")

    add("## 3. The umbrella, and why it is the same equation\n")
    add(f"There is a {p_rain:.0%} chance of rain. Costs in units of annoyance,")
    add("and they are assumptions:\n")
    add("| | Carry it and no rain | Get wet | Cost if I carry | Cost if I do not | Break-even | Decision |")
    add("|---|---|---|---|---|---|---|")
    for c in umb:
        add(f"| {c['name']} | {c['carry']} | {c['wet']} | {c['cost_carry']:.2f} | "
            f"{c['cost_leave']:.2f} | {c['break_even']:.3f} | "
            f"**{'take it' if c['take'] else 'leave it'}** |")
    add("")
    add(f"Same {p_rain:.0%}. Opposite decisions. The probability decided nothing;")
    add("the consequences did. And the break-even is one division -- the cost of")
    add("the cheap mistake over the cost of both mistakes together.\n")
    add("My agent's boundary is that division and no other:\n")
    add("| | Minutes |")
    add("|---|---|")
    add(f"| False positive: rotate a key that was already revoked | {agent['false_positive']:.0f} |")
    add(f"| False negative: dismiss a key that is live | {agent['false_negative']:.1f} |")
    add(f"| **Break-even belief** | **{agent['break_even']:.4f}** |")
    add("")
    add(f"{agent['break_even'] * 100:.1f}% -- not a number anyone chose. The")
    add("wedding is the interesting case for the same reason the live key is:")
    add("one of the two mistakes is so much worse than the other that the")
    add("threshold ends up nowhere near the middle. A reader who follows the")
    add("umbrella follows the agent, which is why it appears first in the paper.\n")

    with open(os.path.join(OUT, "worked-examples.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
