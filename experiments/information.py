"""Week 2, commit 1: the information layer.

Week 1 said the two free features "cannot separate live from revoked". That was
stated in probability language. This script states it in bits, where it becomes
exact rather than descriptive.

Everything here is computed from the Week 1 model in run_experiment.py. No
parameter is changed and no new number is invented.

Four things:

  1. Entropy of the belief, before and after each observation, in bits.
  2. Information gain, kept carefully apart from EXPECTED information gain.
     The first is what you learned after seeing a result; the second is what
     the check is worth before you run it, and it is the one that ranks
     evidence. Confusing them is the error the brief warns about.
  3. Mutual information between each evidence source and the hidden state,
     including the restriction to the live-versus-revoked axis, which is the
     axis the decision actually turns on.
  4. Whether any single outcome INCREASES entropy -- the agent learning
     something and becoming more confused.

Writes results/information.md and results/information.json.
"""

import json
import math
import os
from itertools import product

import run_experiment as R

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results")


# ---------------------------------------------------------------- primitives

def snap(x, tol=1e-12):
    """Floating-point noise around zero is noise, not a number. Several
    quantities here are analytically exactly zero -- identical likelihood rows
    cannot discriminate -- and printing -0.000000 for them would misrepresent
    an exact result as an approximate one."""
    return 0.0 if abs(x) < tol else x


def H(belief):
    """Shannon entropy in bits. Zero-probability states contribute nothing."""
    return -sum(p * math.log2(p) for p in belief.values() if p > 0)


def restrict(belief, states):
    """Condition the belief on the hidden state being one of `states`."""
    t = sum(belief[s] for s in states)
    if t <= 0:
        return None
    return {s: belief[s] / t for s in states}


def marginal(belief, tables, outcome):
    """P(outcome | belief) = sum over states of b[s] * prod of likelihoods."""
    total = 0.0
    for s in belief:
        p = belief[s]
        for tab, o in zip(tables, outcome):
            p *= tab[s][o]
        total += p
    return total


def update(belief, tables, outcome):
    """Posterior after observing `outcome`, or None if the outcome is impossible."""
    u = {}
    for s in belief:
        p = belief[s]
        for tab, o in zip(tables, outcome):
            p *= tab[s][o]
        u[s] = p
    t = sum(u.values())
    if t <= 0:
        return None
    return {s: v / t for s, v in u.items()}


def analyse(name, belief, tables, spaces):
    """Full information analysis of one evidence source against one belief.

    Returns the prior entropy, every outcome with its probability, posterior
    entropy and per-outcome gain, the conditional entropy, and the expected
    information gain.
    """
    h0 = H(belief)
    rows = []
    h_cond = 0.0
    for outcome in product(*spaces):
        po = marginal(belief, tables, outcome)
        if po <= 0:
            continue
        post = update(belief, tables, outcome)
        h1 = H(post)
        h_cond += po * h1
        rows.append(dict(outcome=list(outcome), p=po, h_after=h1,
                         gain=snap(h0 - h1), posterior=post))
    return dict(name=name, h_before=h0, h_conditional=h_cond,
                eig=snap(h0 - h_cond), outcomes=rows)


# ---------------------------------------------------------------- the analyses

def main():
    os.makedirs(OUT, exist_ok=True)

    C, F, P = R.L_CONTEXT, R.L_FORM, R.L_PROBE
    CS, FS, PS = R.CONTEXT, R.FORM, R.PROBE
    prior = dict(R.PRIOR)

    # --- 1. the full three-state analysis --------------------------------
    full = [
        analyse("context", prior, [C], [CS]),
        analyse("well-formedness", prior, [F], [FS]),
        analyse("both free features", prior, [C, F], [CS, FS]),
        analyse("probe (last_used_at)", prior, [P], [PS]),
        analyse("everything", prior, [C, F, P], [CS, FS, PS]),
    ]

    # --- 2. the same, restricted to the axis the decision turns on -------
    # Condition on the string being a real credential, then ask how much each
    # source tells us about live versus revoked.
    pair = ["live", "revoked"]
    b2 = restrict(prior, pair)
    C2 = {s: C[s] for s in pair}
    F2 = {s: F[s] for s in pair}
    P2 = {s: P[s] for s in pair}
    axis = [
        analyse("context", b2, [C2], [CS]),
        analyse("well-formedness", b2, [F2], [FS]),
        analyse("both free features", b2, [C2, F2], [CS, FS]),
        analyse("probe (last_used_at)", b2, [P2], [PS]),
    ]

    # --- 3. does any single outcome raise entropy? -----------------------
    raises = []
    for a in full:
        for r in a["outcomes"]:
            if r["gain"] < 0:
                raises.append(dict(source=a["name"], outcome=r["outcome"],
                                   p=r["p"], h_before=a["h_before"],
                                   h_after=r["h_after"], gain=r["gain"]))

    # --- 4. the agent's own six reachable beliefs ------------------------
    reach = []
    for c, f in product(CS, FS):
        po = marginal(prior, [C, F], (c, f))
        post = update(prior, [C, F], (c, f))
        probe_here = analyse("probe", post, [P], [PS])
        reach.append(dict(context=c, form=f, p=po, posterior=post,
                          h=H(post),
                          ratio=post["live"] / post["revoked"],
                          probe_eig=probe_here["eig"]))

    payload = dict(prior=prior, h_prior=H(prior),
                   h_prior_axis=H(b2), prior_axis=b2,
                   full=full, axis=axis, entropy_raising=raises,
                   reachable=reach)
    with open(os.path.join(OUT, "information.json"), "w") as fh:
        json.dump(payload, fh, indent=2)

    # ---------------------------------------------------------------- report
    L = []
    add = L.append
    add("# The information layer\n")
    add("Every number here is computed from the Week 1 model. Nothing was")
    add("re-parameterised. Log base 2 throughout, so the unit is bits and one")
    add("bit is one good yes/no question's worth of uncertainty.\n")

    add(f"Prior over the three hidden states: "
        f"live {prior['live']}, revoked {prior['revoked']}, fake {prior['fake']}.")
    add(f"Its entropy is **{H(prior):.4f} bits**, against a maximum of "
        f"{math.log2(3):.4f} for three equally likely states. The agent starts")
    add("only slightly better informed than knowing nothing.\n")

    add("## What each evidence source is worth\n")
    add("The distinction that matters: *gain* is what you learned after seeing")
    add("one particular result. *Expected* gain is the average over the results")
    add("you might get, weighted by how likely each is, and it is the number")
    add("that decides which check to run, because you have to choose before")
    add("you know the answer.\n")
    add("| Evidence | H before | H after (expected) | **Expected gain** | Best single outcome | Worst single outcome |")
    add("|---|---|---|---|---|---|")
    for a in full:
        best = max(a["outcomes"], key=lambda r: r["gain"])
        worst = min(a["outcomes"], key=lambda r: r["gain"])
        add(f"| {a['name']} | {a['h_before']:.4f} | {a['h_conditional']:.4f} | "
            f"**{a['eig']:.4f}** | {'+'.join(best['outcome'])} "
            f"({best['gain']:+.4f}) | {'+'.join(worst['outcome'])} "
            f"({worst['gain']:+.4f}) |")
    add("")

    add("## The same question, asked about the axis that matters\n")
    add("The three-state numbers above are flattering, because most of what the")
    add("free features do is rule out *fake*. The decision, though, turns on")
    add("live versus revoked. So condition on the string being a real")
    add("credential and ask the question again.\n")
    add(f"On that restriction the prior is live {b2['live']:.4f}, "
        f"revoked {b2['revoked']:.4f}, and its entropy is "
        f"**{H(b2):.4f} bits**.\n")
    add("| Evidence | Expected gain about live-vs-revoked | Fraction of the 0.9427 bits |")
    add("|---|---|---|")
    for a in axis:
        add(f"| {a['name']} | **{a['eig']:.6f}** | {a['eig'] / H(b2) * 100:.2f}% |")
    add("")

    free_axis = [a for a in axis if a["name"] == "both free features"][0]
    probe_axis = [a for a in axis if a["name"].startswith("probe")][0]
    add("**This is the Week 1 invariance, restated exactly.** Section 4.3 of the")
    add("Week 1 paper says the two free features cannot separate live from")
    add("revoked, and shows the posterior ratio staying at 1.778. In bits the")
    add(f"same statement is that the mutual information between those features")
    add(f"and the live-versus-revoked distinction is **{free_axis['eig']:.6f} bits**.")
    add("")
    add("Exactly zero, not approximately zero. It is not a small number that")
    add("happened to come out near nothing; it is a consequence of the two")
    add("states carrying identical likelihood rows, and identical rows cannot")
    add("discriminate between the states they belong to. The computation")
    add("returns floating-point noise around 1e-16, which this script snaps to")
    add("zero rather than printing, because reporting it as a tiny non-zero")
    add("quantity would misrepresent an exact result as a measured one.")
    add("")
    add(f"The probe carries **{probe_axis['eig']:.4f} bits** about the same axis, "
        f"which is {probe_axis['eig'] / H(b2) * 100:.1f}% of everything there is")
    add("to know about it. That is the whole asymmetry of this problem in two")
    add("numbers: the free evidence carries none of what the decision needs, and")
    add("the evidence that carries it has to be bought.\n")

    add("## Does any observation make the agent more confused?\n")
    if raises:
        add("Yes. Expected information gain is never negative, but the gain from a")
        add("*single* outcome can be, and here it is:\n")
        add("| Evidence | Outcome | P(outcome) | H before | H after | Change |")
        add("|---|---|---|---|---|---|")
        for r in raises:
            add(f"| {r['source']} | {'+'.join(r['outcome'])} | {r['p']:.4f} | "
                f"{r['h_before']:.4f} | {r['h_after']:.4f} | "
                f"**{r['gain']:+.4f}** |")
        add("")
        add("This is not an arithmetic error. The prior leans towards *live*; an")
        add("outcome that knocks the leading explanation down without promoting a")
        add("single replacement leaves the belief flatter than it found it. The")
        add("agent has correctly moved from a confident guess to an honest")
        add("admission that it does not know, and entropy is the number that")
        add("records the change.")
    else:
        add("No. Every outcome of every evidence source in this model lowers")
        add("entropy or leaves it unchanged. Worth stating explicitly, because it")
        add("is a property of these likelihood tables rather than a law: a")
        add("single outcome is perfectly capable of raising entropy, and only the")
        add("*expected* gain is guaranteed non-negative.")
    add("")

    add("## The six beliefs the agent can actually hold\n")
    add("After the free features, and before any purchase.\n")
    add("| Context | Form | P(seen) | live | revoked | fake | Entropy | live:revoked | Probe EIG here |")
    add("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(reach, key=lambda r: -r["p"]):
        b = r["posterior"]
        add(f"| {r['context']} | {r['form']} | {r['p']:.4f} | {b['live']:.4f} | "
            f"{b['revoked']:.4f} | {b['fake']:.4f} | {r['h']:.4f} | "
            f"{r['ratio']:.4f} | {r['probe_eig']:.4f} |")
    add("")
    add("The live:revoked column is the invariance seen directly: identical to")
    add("four decimal places in every row the agent can reach, including rows")
    add("where the entropy differs by more than a bit.")
    add("")
    add("The last column is worth reading against the Week 1 result that the")
    add("probe is bought on about 4% of findings. The probe carries useful bits")
    add("in every row. It is worth *paying* for in almost none of them, because")
    add("bits and value are different quantities and only one of them is what")
    add("the agent is spending minutes on. Commit W2-2 prices that difference.")
    add("")

    with open(os.path.join(OUT, "information.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")

    print("\n".join(L))
    print("\nWrote results/information.md and results/information.json")


if __name__ == "__main__":
    main()
