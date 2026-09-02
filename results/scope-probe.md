# Two experiments about the state Week 1 did not model

## A. Does reading the key's scope earn its place?

The probe costs three engineer-minutes and returns `last_used_at`. The
same administrative call can return the key's assigned permission
scope. A credential authorised for nothing stops being something to
infer and becomes a field to read.

The scope likelihoods are an assumption. The `absent` column is copied
from the probe's existing `null` row rather than invented separately,
because *not in our account* is the same event in both fields and the
model should not disagree with itself. Only the zero/nonzero split is
genuinely new.

| State | zero | nonzero | absent |
|---|---|---|---|
| live | 0.02 | 0.98 | 0.00 |
| revoked | 0.02 | 0.78 | 0.20 |
| fake | 0.01 | 0.04 | 0.95 |
| zero_scope | 0.95 | 0.05 | 0.00 |
| other | 0.33 | 0.33 | 0.33 |

| Context | Form | P(seen) | P(zero_scope) | Probe bits | +scope bits | Probe EVSI | +scope EVSI | Buy probe? | Buy +scope? |
|---|---|---|---|---|---|---|---|---|---|
| production | well-formed | 0.4477 | 0.0525 | 0.3699 | 0.6642 | 0.0000 | 2.4297 | no | no |
| neutral | well-formed | 0.2469 | 0.0476 | 0.4800 | 0.9118 | 0.0000 | 3.4299 | no | **yes** |
| placeholder | well-formed | 0.1445 | 0.0271 | 0.6406 | 1.1165 | 0.0000 | 8.5131 | no | **yes** |
| placeholder | malformed | 0.1064 | 0.0004 | 0.0525 | 0.0957 | 0.5906 | 2.6464 | no | no |
| neutral | malformed | 0.0410 | 0.0029 | 0.2033 | 0.3537 | 5.4835 | 7.0092 | yes | **yes** |
| production | malformed | 0.0135 | 0.0175 | 0.5539 | 1.0099 | 0.0000 | 7.3432 | no | **yes** |

Findings on which the agent buys the probe: **4.10%** without scope, **44.60%** with it.

| Policy | Total cost | Questions | Regret | Action acc. |
|---|---|---|---|---|
| P2 | 60.45 | 0.000 | 10.91 | 0.432 |
| P3 | 60.52 | 0.044 | 10.85 | 0.436 |
| P4 | 59.37 | 0.468 | 8.43 | 0.536 |

**P4 is the cheapest policy in the project**, at 59.37 minutes against P2's 60.45.
The extra field costs nothing: it arrives on a call the agent was
already deciding whether to pay for.

## B. How much of the over-remediation was the missing state?

Week 1's error analysis found every mistake in one direction: the agent
remediated things that did not need it. Week 1 also did not model
`zero_scope`, and counted those keys as `live` -- the state that costs
2400 minutes to dismiss. Running the unchanged three-state agent
against the five-state world measures what that omission cost.

| Agent | Cost per finding | Regret per finding |
|---|---|---|
| Week 1, three states | 60.45 | 10.91 |
| Week 2, five states | 60.45 | 10.91 |

On the 21 cases whose true state is `zero_scope`:

| Agent | What it did |
|---|---|
| Week 1 | rotate x21 |
| Week 2 | rotate x21 |

**The two agents behaved identically on every one of the 500 cases.** Not
approximately, not on average: the same action, case for case,
including all 21 whose true state is the one Week 1 was
missing. Regret is identical to the last decimal place.

The reason is worth more than the experiment was. Without scope,
`zero_scope` carries the same context and well-formedness rows as
`live` and `revoked`, so no free observation can move mass onto it
independently. Its probability rides along with `live`'s, the
cheapest action is unchanged, and a state that cannot be
distinguished cannot alter a decision.

**So adding the state, on its own, is worth exactly nothing.**
Not little. Nothing. This is the sharper form of the rule that has
governed every result in this project: value comes from crossing a
decision boundary, and a state with no evidence attached to it
cannot cross one. A hidden state you cannot observe is a comment,
not a model.

Read that against Experiment A above and the pair says something
neither says alone. The state alone: zero. The state plus the
scope field that resolves it: the probe goes from bought on 4.1% of findings to 44.6%, regret falls from
10.91 to 8.43, and the result is the
cheapest policy in the project. The state was never the
improvement. The state made the evidence *meaningful*, and the
evidence was the improvement.

This also corrects something I expected to find. The plausible
story going in was that the missing state explained Week 1's
over-remediation bias -- those keys were counted as `live`, `live`
is expensive to dismiss, so the agent over-remediated. The story is
wrong, and it is wrong by exactly zero rather than by a little.
The bias comes from the cost structure, and dismissing was already
unreachable below P(live) = 0.0015 for reasons that have nothing to
do with any of this. Running the experiment is what stopped that
paragraph being written.

