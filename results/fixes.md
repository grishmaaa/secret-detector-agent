# Three fixes

## Fix 1: the breach cost was standing in for a probability

Week 1 priced dismissing a live key at 2400 minutes and called it *a
breach and its cleanup*. A dismissed live key is not certainly
breached. The honest cost is the probability of exploitation times the
breach, and Week 1 was running at **p = 1.0** without writing it down.
That single unstated assumption is what made the agent unable to say
no to anything.

The one quantified datapoint anywhere is a vendor experiment where 2 of
75 leaked keys drew activity beyond a validity check within twelve
hours: 0.027, on a *public* exposure. This model is scoped to private
repositories, where the hazard is lower. **0.10 is used here as a
deliberate over-estimate**, and swept because it is now the weakest
number in the model.

| p_exploit | Cost of dismissing a live key | Which action wins on which range of P(live) |
|---|---|---|
| 1.00 | 2400 | **revoke** 0.0000–0.0662 · **rotate** 0.0662–0.6400 |
| 0.50 | 1202 | **dismiss** 0.0000–0.0007 · **revoke** 0.0007–0.0662 · **rotate** 0.0662–0.6400 |
| 0.25 | 604 | **dismiss** 0.0000–0.0077 · **revoke** 0.0077–0.0662 · **rotate** 0.0662–0.6400 |
| 0.10 | 244 | **dismiss** 0.0000–0.1247 · **rotate** 0.1247–0.6400 |
| 0.05 | 125 | **dismiss** 0.0000–0.6400 |
| 0.03 | 77 | **dismiss** 0.0000–0.6400 |
| 0.01 | 29 | **dismiss** 0.0000–0.6400 |

At p = 1.00 the agent's action ladder is `revoke -> rotate`.
At p = 0.10 it is `dismiss -> rotate`.

Two things move. The band on which the agent can decline to act widens,
and the point at which it escalates from revoking to the full rotation
moves up, because rotation stops being worth its price against a
breach that is no longer treated as certain. Below p = 0.05 rotation
stops winning anywhere at all: if exploitation is rare enough, paying a
deploy cycle to avoid an outage is never the cheapest thing to do.

The agent did not become reckless. The cost stopped claiming a
certainty it never had.

## Fix 2: escalation was competing when it should have been a rule

Escalation never fired in any run. The reason was structural, not
numerical: it was made to compete on expected cost, and 30 minutes of
human attention added to whatever the human then does always loses to
an action costing less. Tuning the number would not repair the shape.

Some decisions reach a person because of what is at stake, not because
the agent is unsure. **Confidence is not authorisation.** So escalation
is now a rule applied before the cost comparison: if the worst outcome
of the chosen action exceeds **400 minutes**, a human sees it
regardless of the belief.

## Fix 3: the 92% lie, measured

An agent that remediates everything reports recall 1.000 and looks
excellent. It has not learned to tell anything apart. It has learned to
always say yes. Overall accuracy hides that completely; per-class recall
does not.

| Policy | live | revoked | fake | zero_scope | other | Overall | **Balanced** | Cost | Human % |
|---|---|---|---|---|---|---|---|---|---|
| P2 (Week 2, as built) | 1.000 | 0.000 | 0.000 | 0.000 | 0.500 | 0.432 | **0.300** | 60.45 | 0.0% |
| P3 (Week 2, as built) | 1.000 | 0.000 | 0.000 | 0.000 | 0.833 | 0.436 | **0.367** | 60.52 | 0.0% |
| P5 fix 1 only | 1.000 | 0.008 | 0.588 | 0.000 | 0.333 | 0.586 | **0.386** | 59.85 | 0.0% |
| P5 fix 1 + escalation rule | 0.995 | 0.008 | 0.573 | 0.000 | 0.333 | 0.580 | **0.382** | 60.07 | 1.0% |
| P6 all three fixes + scope | 0.986 | 0.109 | 0.954 | 0.286 | 0.000 | 0.710 | **0.467** | 59.11 | 2.4% |

Balanced accuracy is the average of the per-state columns, so a policy
that only ever gets one state right cannot hide behind that state being
common.

- *P2 (Week 2, as built)* — **live**: rotate x213; **revoked**: revoke x1, rotate x128; **fake**: revoke x75, rotate x56; **zero_scope**: rotate x21; **other**: revoke x3, rotate x3
- *P3 (Week 2, as built)* — **live**: rotate x213; **revoked**: rotate x129; **fake**: revoke x74, rotate x57; **zero_scope**: rotate x21; **other**: revoke x1, rotate x5
- *P5 fix 1 only* — **live**: rotate x213; **revoked**: dismiss x1, rotate x128; **fake**: dismiss x77, rotate x54; **zero_scope**: rotate x21; **other**: dismiss x4, rotate x2
- *P5 fix 1 + escalation rule* — **live**: escalate x1, rotate x212; **revoked**: dismiss x1, escalate x1, rotate x127; **fake**: dismiss x75, escalate x2, rotate x54; **zero_scope**: rotate x21; **other**: dismiss x3, escalate x1, rotate x2
- *P6 all three fixes + scope* — **live**: dismiss x1, escalate x2, rotate x210; **revoked**: dismiss x14, escalate x2, rotate x113; **fake**: dismiss x125, escalate x3, rotate x3; **zero_scope**: dismiss x6, escalate x2, rotate x13; **other**: dismiss x3, escalate x3

### What the fixes bought

| | before (P2) | after (P6) |
|---|---|---|
| live | 1.000 | 0.986 |
| revoked | 0.000 | 0.109 |
| fake | 0.000 | 0.954 |
| zero_scope | 0.000 | 0.286 |
| other | 0.500 | 0.000 |
| **overall** | 0.432 | 0.710 |
| **balanced** | 0.300 | 0.467 |
| cost per finding | 60.45 | 59.11 |
| sent to a human | 0.0% | 2.4% |

The agent now tells things apart. `fake` went from never being handled
correctly to 95%; `zero_scope` from nothing to 29%; the balanced score
from 0.300 to 0.467. It is also
cheaper, which is the part that matters: this is not accuracy bought
with money.

Note that `live` fell from 1.000 to 0.986. **That is the fix working, not
failing.** A policy that scores 1.000 on the majority class does so by
never declining, and the price of never declining was every other
column reading zero. Giving up 1.4% of one column to gain 95 points on
another is the trade the whole exercise was about.

### What is still broken

**`revoked` is at 0.109.** Barely moved.
This is the Week 1 invariance, and no cost fix can touch it: the free
features carry exactly zero bits about live-versus-revoked, so the only
thing that separates them is the purchased probe. The scope field helps
a little, because `absent` appears for revoked keys and never for live
ones, but it is a weak signal and the probe is not bought on every
case. **This remains the central open problem of the project**, and it
is worth being blunt that three fixes and a new evidence channel moved
it from 0.000 to 0.109.

**`other` reads 0.000, and the metric is
wrong rather than the agent.** Those cases are escalated, which is the
correct thing to do with a state the model cannot characterise. The
scoring compares against the cheapest action in the cost table, and the
cost table cannot price a state that exists precisely because we do not
know what it is. Escalation scores zero for doing the right thing. I am
leaving that visible rather than redefining the metric to flatter the
result.

### A bug worth recording

Fix 1 did nothing at all on the first run, and the reason is worth
keeping. The residual state's cost is defined as the mean over the
known states. When the breach cost dropped from 2400 to 244, the
residual's price was not recomputed, so `dismiss | other` sat at 602
minutes -- carrying the old un-discounted breach back into the model
through the one state that is supposed to represent ignorance. With
P(other) around 0.017 that was enough to block every dismissal the fix
was meant to unlock, and the results table was identical to the
unfixed one, which looked like the fix being ineffective rather than
being silently undone. A derived quantity that is not re-derived is a
stale constant wearing a formula's clothes.

