# Testing the agent in a world that disagrees with it

Every result so far draws its cases from the agent's own likelihood
tables. That measures whether the policy is good given the model. It
says nothing about whether the model is any good, and nothing about
what happens when it is wrong -- which it is, because every number in
it was estimated.

So the world is generated from different tables and the agent is left
alone. Two agents run on identical cases: ours, and one that knows the
true tables. The gap is the price of being wrong, separated from the
price of not knowing the state.

Median over 12 seeds, 500 cases each. The agent's regret in a
world that agrees with it is **8.43** minutes per finding.

| Wrongness | Strength | Our agent | Agent that knows | Gap | Worst gap | Scope still helps | Still beats always-rotate |
|---|---|---|---|---|---|---|---|
| Dirichlet noise on every row (α) | 200 | 8.64 | 8.68 | **+0.01** | +2.23 | 100% | 100% |
| Dirichlet noise on every row (α) | 50 | 8.77 | 8.53 | **+0.20** | +2.43 | 100% | 100% |
| Dirichlet noise on every row (α) | 20 | 8.23 | 7.19 | **+0.66** | +2.94 | 100% | 100% |
| Dirichlet noise on every row (α) | 8 | 8.44 | 7.51 | **+1.20** | +4.67 | 92% | 100% |
| wrong base rates (α) | 200 | 7.95 | 7.86 | **+0.27** | +2.12 | 100% | 100% |
| wrong base rates (α) | 50 | 7.05 | 6.74 | **+0.29** | +2.43 | 100% | 100% |
| wrong base rates (α) | 20 | 6.44 | 5.67 | **+0.41** | +2.63 | 100% | 100% |
| live/revoked really differ (δ) | 0.02 | 8.58 | 8.58 | **+0.00** | +0.00 | 100% | 100% |
| live/revoked really differ (δ) | 0.05 | 8.42 | 8.33 | **+0.29** | +0.60 | 100% | 100% |
| live/revoked really differ (δ) | 0.1 | 8.34 | 6.85 | **+1.47** | +2.00 | 100% | 100% |
| live/revoked really differ (δ) | 0.2 | 8.15 | 6.07 | **+1.99** | +2.61 | 100% | 100% |

Lower α is more perturbation; higher δ is a bigger real difference
between the two states the agent believes are identical.

## What survives

**Generic mis-estimation is cheap, and it degrades gracefully.** Under
Dirichlet noise the gap runs from +0.01
to +1.20 minutes per finding as the
perturbation grows. At α = 8 -- every row substantially wrong -- the
agent still beats always-rotate in 100% of worlds and reading scope
still helps in 92%. The gap grows
smoothly with the error rather than falling off a cliff, which is the
property you want and is not guaranteed.

**Wrong likelihoods cost more than wrong base rates**, which is the
opposite of what I expected. The prior gap tops out at
+0.41 against +1.20
for the likelihoods. The prior is the number I would have said was
most at risk -- it is assembled from two sources measuring different
populations -- and it turns out to be the one the agent is most
forgiving about. Free evidence washes a wrong prior out; nothing
washes out a wrong likelihood, because the likelihood is what does the
washing.

One caution on reading those prior rows. The agent's absolute regret
*falls* as the prior is perturbed (7.95 down to 6.44), because some perturbed worlds are simply
easier than the real one. The gap against an agent that knows the
truth is the measure that means anything here; the absolute column is
not comparable across rows.

## The test that matters

The invariance rows are the sharp ones. The project's headline
structural result is that `live` and `revoked` carry identical
free-feature rows, so the mutual information between them is exactly
zero. In these worlds that is false: the two states really do differ,
the free evidence really does carry signal about the axis, and the
agent has proved a theorem saying otherwise and acts on it.

| δ | Our agent | Agent that knows | What the agent leaves on the table |
|---|---|---|---|
| 0.02 | 8.58 | 8.58 | +0.00 |
| 0.05 | 8.42 | 8.33 | +0.29 |
| 0.10 | 8.34 | 6.85 | +1.47 |
| 0.20 | 8.15 | 6.07 | +1.99 |

At δ = 0.20 -- a substantial real difference --
the agent forgoes 1.99 minutes per finding by refusing
to look for a signal that is there. The failure is silent: nothing in
the agent's own diagnostics can detect it, because the invariance is
an assumption about the likelihood tables rather than an observation,
and the agent never observes its own tables being wrong.

**That is the honest limitation of the whole project, stated with a
number attached.** The zero-bits result is exact given the tables and
worth nothing if the tables are wrong, and the only way to find out is
to measure the likelihoods against real labelled findings, which is
the one thing this project has never been able to do.

## Conclusions that hold, and the one that does not

| Claim | Verdict under mis-specification |
|---|---|
| The agent beats always-rotate | holds in 100–100% of worlds |
| Reading scope helps | holds in 92–100% of worlds |
| Free features carry zero bits about live vs revoked | **fails whenever the world says otherwise, undetectably** |

The policy conclusions are robust to the model being wrong. The
structural conclusion is not, and cannot be, because it is a statement
about the model rather than about the world. Both belong in the paper,
and only one of them should be stated as a finding about secret
scanning rather than as a finding about this model of it.

