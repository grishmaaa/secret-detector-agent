# Correlation shrinkage on the free features

The posterior multiplies the context and well-formedness likelihoods,
which assumes they are conditionally independent given the state. They
are not. A `tests/fixtures/` path and a `dummy_key` variable name are
close to the same observation counted twice. Weighting each channel's
log-likelihood by *w* < 1 is the standard correction. Below, *w* = 1 is
what the paper reports and *w* = 0 discards the free evidence.

Baseline (escalate everything): **84.80** min.
P0 (prior only, no evidence): **66.86** min.

| *w* | P(fake), production + well-formed | P(fake), placeholder + malformed | live:revoked | P2 | P3 | probe bought | P2 differs from P0 |
|---|---|---|---|---|---|---|---|
| 1.0 | 0.0111 | 0.9929 | 1.7778 | 65.11 | 65.03 | 3.97% | 14.55% |
| 0.9 | 0.0155 | 0.9871 | 1.7778 | 65.11 | 65.03 | 3.97% | 14.55% |
| 0.8 | 0.0216 | 0.9767 | 1.7778 | 65.38 | 65.03 | 3.97% | 10.57% |
| 0.7 | 0.0301 | 0.9581 | 1.7778 | 65.38 | 65.34 | 14.55% | 10.57% |
| 0.6 | 0.0418 | 0.9259 | 1.7778 | 65.38 | 65.34 | 14.55% | 10.57% |
| 0.5 | 0.0576 | 0.8723 | 1.7778 | 66.86 | 65.70 | 10.57% | 0.00% |
| 0.0 | 0.2500 | 0.2500 | 1.7778 | 66.86 | 66.86 | 0.00% | 0.00% |

## What survives

**The live:revoked invariance is untouched, and could not have been.**
The two states carry identical free-feature rows, so raising both to
the same power leaves them identical. The ratio sits at
1.7778 at every *w*, including *w* = 0. This is worth
stating precisely because it is the one thing shrinkage cannot reach:
the invariance follows from two rows being equal, not from the
independence assumption, and it is the only free-feature result that is
safe from this critique.

**The *fake* collapse is not robust, and it is the headline number.**
On the most informative evidence the paper reports P(fake) falling
from 0.25 to 0.0111. A 20% shrinkage puts it at
0.0216, roughly double. Halving the weight puts it at
0.0576, five times the reported figure. The 0.011
should be read as the most favourable end of a range, not as a
measurement.

**The policy barely notices, which is the useful part.**
P2 moves from 65.11 to 65.38 minutes at *w* = 0.8,
against a baseline of 84.80. Every conclusion about the cost
structure survives untouched, because those conclusions never depended
on the belief being sharp.

**But the belief model dies before the free evidence does.**
At *w* = 0.5 the share of findings on which P2 departs from
P0's constant action reaches 0.00%, and P2's cost
is 66.86, which is P0 exactly. Discounting the free evidence
by half does not degrade the belief model gradually; it removes it. The
agent falls back to acting on the prior alone and loses nothing but the
2.1 percentage points the belief model
was contributing in the first place.

**Probe purchase is not monotone in *w*.**
The probe is bought on 3.97% of findings at
*w* = 1, rises to 14.55% in the
middle of the range, and falls to zero once the free evidence is gone.
Shrinkage first makes the agent uncertain enough to want the probe, then
uncertain enough that the probe can no longer move it across a boundary.

