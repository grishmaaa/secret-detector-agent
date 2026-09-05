# How much of each headline is one draw?

Every number in this project comes from a single seed and nothing
reports an interval. Two review rounds said so and I could not answer.
Worse, two of my own scripts disagreed about the same agent -- P6 is
balanced accuracy 0.4669 in `fixes.py` and 0.4942 in
`generalization.py` -- and I had been quoting whichever number the
section needed without noticing they were one configuration run twice.

They differ because P6 has a nuisance random variable nothing else has.
The scope reading is **drawn**, once per purchased probe. The 500 cases
are frozen; this is the only thing moving. So hold the cases and vary
only that draw, 200 times.

## The spread

| Quantity | Committed seed | Mean | SD | 95% interval |
|---|---|---|---|---|
| Regret, min/finding | 8.16 | 8.20 | 0.26 | 7.74 – 8.71 |
| Total cost, min/finding | 59.11 | 59.14 | 0.26 | 58.68 – 59.65 |
| Sent to a human | 0.024 | 0.026 | 0.004 | 0.020 – 0.034 |
| Balanced accuracy | 0.467 | 0.480 | 0.023 | 0.449 – 0.528 |
| `live` recall | 0.986 | 0.987 | 0.006 | 0.972 – 0.995 |
| `revoked` recall | 0.109 | 0.089 | 0.023 | 0.047 – 0.132 |
| `fake` recall | 0.954 | 0.950 | 0.015 | 0.916 – 0.977 |
| `zero_scope` recall | 0.286 | 0.271 | 0.024 | 0.238 – 0.286 |
| `other` recall | 0.000 | 0.103 | 0.112 | 0.000 – 0.333 |

## What survives and what does not

**The `fake` result survives comfortably.** Recall runs
0.901–0.977 across every seed against a
pre-fix value of **0.000**, so the claim that the agent went from
unable to produce the label to producing it reliably does not depend on
the draw. That is the paper's second headline and it holds.

**Balanced accuracy is softer than I reported it.** Mean
0.480, sd 0.023, 95% interval
0.449–0.528. The committed seed gives
0.467. Quoting three decimal places on that was
false precision, and the honest form of the sentence is
**0.300 → 0.48 ± 0.02**.

**`revoked` recall is the number to stop quoting to three decimals.**
Mean 0.089, sd 0.023, range
0.031–0.155. On 129 revoked cases that is a
handful of findings moving. The paper's honest admission -- that the
agent still barely tells revoked from live -- is correct, but the
specific value carries about one significant figure, not three.

**Escalation is stable.** 0.026 ± 0.004, which
is why the 2.4% and 2.8% quoted in different sections are the same
number seen twice rather than a disagreement. Both are inside the
interval; neither should have been quoted alone.

## The limitation this does not remove

Only the scope draw varies here. The 500 cases are themselves one draw
from the prior, and re-drawing them would move everything again --
including P2, which has no scope draw and therefore appears in this
table as a point when it is not one. So these intervals are a **lower
bound on the uncertainty**, not a confidence interval on the result.
They establish that the `fake` finding is not a lucky seed. They do not
establish that any figure here would survive a different case set.

Stating that plainly is the point. A review round asked whether the
headlines were one draw; the answer for the largest of them is no, for
the smallest of them is partly, and for the case set as a whole it is
still unmeasured.

