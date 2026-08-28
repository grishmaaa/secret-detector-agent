# Joint sensitivity: does any of this survive if the model is wrong?

Three reviewers made the same point — sweeping one cost at a time cannot
establish robustness when a dozen inputs are uncertain together. A fourth then
read the code and found a bug in how I was sampling. This file is the corrected
analysis, and it now asks two questions rather than one.

## The sampler was wrong, and I am recording what it did

My first version set a single spread from `log(high/low)` and multiplied the
estimate by it. That makes the stated range correct **only when the estimate is
the geometric midpoint of low and high**. Eight of my fourteen quantities are
not, so the ranges I published were not the ranges I sampled:

| Quantity | I claimed | I actually sampled |
|---|---|---|
| human attention | 5 – 60 | **8.7 – 103.9** |
| outage | 30 – 480 | 60 – 960 |
| rotate a fake key | 1 – 60 | 2.6 – 154.9 |
| deploy | 10 – 180 | 14.1 – 254.6 |
| issue a new key | 1 – 25 | 2.0 – 50.0 |

Only `dismiss_live` was correct, by accident — 2400 happens to be the geometric
midpoint of 240 and 24 000.

The fix is a two-piece lognormal: separate spreads above and below the estimate,
so the most-likely value is the median and low and high are the 5th and 95th
percentiles **exactly**. All numbers below use it.

I expected this to make the escalation result look worse, since I had been
over-sampling expensive humans. It went the other way — 67.2% to 70.3% — because
the old sampler also inflated deploy, outage and rotate-on-fake, which made
remediation look costly and escalation comparatively attractive. Reasoning about
one skewed input in isolation was the wrong instinct.

## Two experiments

**A. Costs uncertain, evidence model fixed.** 40 000 draws over thirteen cost
components and the live share.

**B. Costs and evidence both uncertain.** The same, plus Dirichlet perturbation
(α = 40) of every likelihood row and the fake rate. Crucially the live and
revoked rows are perturbed **independently**, so the identical-rows property
that produces the invariant ratio is deliberately broken.

## What survives

| Claim | A: costs | B: costs + evidence |
|---|---|---|
| P2 costs less than escalate-everything | **98.02%** | **98.64%** |
| Revoke/rotate boundary below 0.5 | **93.26%** | **93.24%** |
| Belief model worth under 5 min per finding | **91.34%** | 88.13% |
| P0 also costs less than the baseline | 79.20% | 79.20% |
| **Escalate is chosen nowhere** | **70.29%** | 69.75% |
| The probe is bought somewhere | 59.29% | 57.98% |
| P0 chooses rotate-safely | 66.37% | 66.56% |

Read these as *"this share of sampled draws had that property"*. They are not
confidence levels, and not probabilities that a claim is true. And the draws are
independent across components, which is certainly false in reality — a
deployment that is hard to run is probably also hard to verify. These are 40 000
draws from an uncertainty model I chose, not 40 000 plausible organisations.

## The result I did not expect

Perturbing the evidence model **breaks the invariance and changes almost
nothing**.

| | A | B |
|---|---|---|
| live:revoked log-drift across buckets (median) | **0.0000** | **2.5294** |

In experiment B the live-to-revoked ratio moves by a factor of roughly twelve
between evidence buckets — the free features genuinely separate the two states
in most of these worlds. And not one conclusion moves by more than 3.2
percentage points.

That is a stronger answer than the one I had to the reviewers who pointed out
that repository visibility and commit semantics might distinguish live from
revoked. **Even when free evidence can separate them, it barely changes what
the agent does**, because rotate-safely remains cheap in every state. The
invariance is an idealisation; the conclusion that rests on it does not need it.

## Escalation, tested properly rather than observed

Saying escalation is "dominated by" the human cost was a causal claim taken
from an observational slice. So I held every other component at its point
estimate and varied only that one:

| Human attention | Actions chosen | Findings escalated |
|---|---|---|
| ≤ 3 min | escalate only | **100.00%** |
| 5 – 10 min | escalate, revoke | 89.42% |
| 12 min | escalate, revoke, rotate | 15.62% |
| 15 min | escalate, revoke, rotate | 1.20% |
| ≥ 20 min | revoke, rotate | **0.00%** |

Now the claim is earned. With everything else fixed, escalation goes from every
finding to no finding across a twenty-minute range, and the crossover sits
between 12 and 20 minutes. My assumed 30 is comfortably past it; a Tier-1
analyst at 2–5 minutes is comfortably before it.

## Where the point estimates sit

| Quantity | 5th | Median | 95th | Paper |
|---|---|---|---|---|
| P2 saving vs baseline | 0.53% | 19.23% | 51.27% | 23.2% |
| Value of the belief model (min) | 0.00 | 0.87 | 6.31 | 1.75 |
| Revoke/rotate boundary | −0.136 | 0.059 | 0.600 | 0.0659 |
| Max VPI, reachable beliefs | 1.37 | 12.12 | 32.12 | 15.03 |
| Findings probed | 0.0% | 3.98% | 89.4% | 4.0% |

Every point estimate is near the median of its distribution, so my cost model
is not an outlier among plausible ones. The intervals are nonetheless very wide:
the saving could be half a percent or fifty.

*(A negative boundary means revoke-now never wins in that world — rotate-safely
takes the whole line. Degenerate, not an error.)*

## What I am changing in the paper

**Dropping "escalation is never optimal" as an absolute.** It holds under the
point-estimate cost model and in 70% of sampled worlds, and it is a function of
one number I guessed. The controlled sweep is the honest version.

**Demoting "P0 captures ≥80% of P2's saving."** That criterion divides by P2's
saving, which is sometimes near zero, so the ratio is unstable by construction.
The stable quantity is the difference — **0.87 minutes per finding at the
median, 0 to 6.3 over the interval** — and that is what I report now.

**Keeping 23.2% but never without its interval.** The point estimate is fine;
quoting it alone implies a precision the model does not have.

**Softening "the shape of the behaviour is stable."** Production/well-formed
rotates in 76.5% of worlds, which means it does something else in a quarter of
them. The evidence buckets have consistent directional tendencies; the exact
action does not.

## What is still missing

Correlations between components. Anything resembling real data. And a
justification for lognormal shapes over triangular or PERT ones — my inputs are
expert guesses with plausible bounds, which is the natural shape for a PERT
distribution and not obviously the natural shape for a lognormal.
