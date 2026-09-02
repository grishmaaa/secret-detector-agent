# The Week 2 experiment

500 simulated cases, seed 20260902, every policy run on the
identical case set. The Week 1 forty remain frozen in `data/cases.json`
and are still the basis of every Week 1 number; this is a second,
larger draw and does not replace them.

## What changed in the model

Two hidden states were added. Both are labelled assumptions and neither
has a source behind it.

| State | Prior | Where it came from | Why it exists |
|---|---|---|---|
| live | 0.4356 | Week 1, sourced | unchanged in meaning |
| revoked | 0.2673 | Week 1, sourced | unchanged |
| fake | 0.2475 | Week 1, sourced | unchanged |
| zero_scope | 0.0396 | **assumption**, carved from `live` | Week 1 named it in limitations and did not model it. It authenticates, so Week 1 counted it as live, and it carries almost none of live's risk |
| other | 0.0100 | **assumption**, 1% by choice | A state absent from the list has probability zero forever. No evidence can raise it and the agent is infinitely surprised the day it occurs |

The new mass is carved out of the existing states rather than added
alongside them, so the sourced quantities are not quietly inflated to
make room for two guesses.

### The invariance got worse

`zero_scope` is a real provider-issued key, so in a repository it looks
exactly like `live` and `revoked`: identical context and
well-formedness rows. The Week 1 result was that the free features
cannot separate two states. With the fifth state modelled they cannot
separate **three**, and the only thing that touches the distinction is
still the purchased probe.

## Results

| Policy | State acc. | Action acc. | Precision | Recall | Decision cost | Info cost | Total | Questions | Human % | Regret | Calib. error |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **P0** baseline, no evidence | 0.426 | 0.438 | 0.426 | 1.000 | 62.53 | 0.00 | **62.53** | 0.000 | 0.0% | 12.99 | 0.0096 |
| **P1** belief only, no cost model | 0.612 | 0.648 | 0.560 | 0.897 | 163.66 | 0.00 | **163.66** | 0.000 | 0.0% | 114.12 | 0.0068 |
| **P2** cost-derived threshold | 0.612 | 0.432 | 0.426 | 1.000 | 60.45 | 0.00 | **60.45** | 0.000 | 0.0% | 10.91 | 0.0068 |
| **P3** P2 plus value of information | 0.612 | 0.436 | 0.426 | 1.000 | 60.38 | 0.13 | **60.52** | 0.044 | 0.0% | 10.85 | 0.0064 |

Costs are engineer-minutes per finding. Precision and recall treat
*the true state is live* as the positive class and *the agent chose a
remediation* as the positive prediction: of the keys we remediated, how
many were live, and of the live keys, how many did we remediate.

**Cheapest policy: P2. Most accurate policy: P1.**
They are not the same policy, which is the result the brief warns
to look for. Accuracy and cost are different objectives and this
problem separates them.

## A negative result: the probe did not pay for itself

P3 spent **0.13** minutes per finding on probes and recovered
**0.07** in better decisions. It is behind P2 by
0.07 minutes per finding. The value-of-information
machinery, on this draw, cost more than it was worth.

It is worth being precise about why, because the policy is not wrong.
The probe was bought on 22 of 500 cases, and only at the
one belief where its expected value exceeds the price -- 5.21 minutes
against a cost of 3. In expectation those 22
purchases should have returned about 0.23
minutes per finding rather than the 0.07 actually realised.
The gap is sampling noise on twenty-odd purchases, not a flaw in the
rule: an expectation computed over three probe outcomes says nothing
about what any particular twenty-two draws will do.

Two honest readings, and I am not going to pick between them here.
Either the decision rule is right and this draw was unlucky, or a
saving that a few hundred cases cannot detect is too small to justify
the machinery that produces it. Both are true statements about the
same number. Week 1's closed-form comparison over all 54 possible
worlds put P3 ahead of P2 by 0.08 minutes; that calculation carries no
sampling error and remains the better estimate of the effect. What this
experiment adds is the size of the noise around it.

## Calibration

Whether the agent's stated confidence can be trusted. Each row bins the
cases by the probability P3 assigned to *live*, and compares the
average stated probability against how often the key actually was live.

| P(live) bin | Cases | Mean stated | Observed | Gap |
|---|---|---|---|---|
| 0.0–0.1 | 79 | 0.009 | 0.000 | +0.009 |
| 0.1–0.2 | 5 | 0.193 | 0.200 | +0.007 |
| 0.2–0.3 | 75 | 0.298 | 0.280 | +0.018 |
| 0.5–0.6 | 341 | 0.557 | 0.560 | +0.003 |

Expected calibration error: **0.0064**.

This number is easy to over-read. The cases were generated *from the
agent's own likelihood tables*, so good calibration here says the
arithmetic is right, not that the model is. A well-calibrated agent in
a world it invented is the least surprising result available. It would
mean something if the cases came from somewhere else, and they do not.

## Where the truth actually fell

| State | Cases | Share | Prior |
|---|---|---|---|
| live | 213 | 0.4260 | 0.4356 |
| revoked | 129 | 0.2580 | 0.2673 |
| fake | 131 | 0.2620 | 0.2475 |
| zero_scope | 21 | 0.0420 | 0.0396 |
| other | 6 | 0.0120 | 0.0100 |

## Does the residual state earn its place?

`other` is priced at the mean of the known states. Pricing it at the
worst known cost instead is equally defensible and is the conservative
choice, so both are run.

| Policy | Total cost, residual at mean | at worst | Human %, mean | at worst |
|---|---|---|---|---|
| P0 | 62.53 | 63.30 | 0.0% | 0.0% |
| P1 | 163.66 | 181.77 | 0.0% | 0.0% |
| P2 | 60.45 | 62.06 | 0.0% | 0.0% |
| P3 | 60.52 | 61.65 | 0.0% | 0.0% |

One per cent of prior mass, and how it is priced moves the answer by
the amounts above. That is the honest argument for the residual state:
not that it improves the policy, but that leaving it out means never
finding out it was there.

