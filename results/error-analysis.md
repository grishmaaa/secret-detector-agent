# Five incorrect decisions, examined

The assignment asks me to look at five decisions the agent got wrong. That
needed a definition first, because a cost-minimising agent has no "correct
action" in the classification sense — it has an action that was cheapest given
what it believed, which is a different thing from the action that was cheapest
given what was actually true.

So I define an **incorrect decision** as one where, knowing the true state
afterwards, a different action would have cost less. The size of the mistake is
the **regret**: what I paid, minus what the best action would have cost in that
state.

    regret = c(chosen, true state) − min_a c(a, true state)

Run over the forty frozen cases with P2.

## The totals

| | Minutes |
|---|---|
| What P2 actually paid | 2018 |
| What a hindsight-perfect agent would have paid | 1620 |
| **Total regret** | **398** |

So the agent gives up **19.7%** to not knowing the state. Fourteen of forty
decisions were exactly right; twenty-six cost something.

## The five worst

| Case | True state | Context | Form | P(live) | Chose | Paid | Best in hindsight | Regret |
|---|---|---|---|---|---|---|---|---|
| 1 | revoked | neutral | well-formed | 0.5754 | rotate | 30 | dismiss | **28** |
| 2 | revoked | neutral | well-formed | 0.5754 | rotate | 30 | dismiss | **28** |
| 14 | revoked | production | well-formed | 0.6329 | rotate | 30 | dismiss | **28** |
| 16 | revoked | production | well-formed | 0.6329 | rotate | 30 | dismiss | **28** |
| 25 | revoked | production | well-formed | 0.6329 | rotate | 30 | dismiss | **28** |

## What I did not expect: they are the same mistake

I went looking for five different errors and found one error five times. Same
true state, same action, same 28 minutes, twice from one evidence bucket and
three times from another. The agent has no idiosyncratic failures on this
sample — it has a single systematic bias, applied consistently.

The bias is this: **a well-formed key in a real-looking file is
indistinguishable from a revoked one, so the agent rotates it, and rotating a
key that was already dead is 28 minutes of wasted work.** That is not a bug in
the policy. It is the invariant ratio showing up as a bill. Nothing the agent
could observe for free would have told it these five were already dead, and it
declined to buy the probe because at P(live) ≈ 0.6 no probe outcome would have
changed the action.

Which means these five decisions were **correct given the information and wrong
given the world**, and that is exactly the situation the whole project is about.

## The full error profile

| Chose | On a key that was | Cases | Total regret |
|---|---|---|---|
| rotate safely | revoked | 11 | 308 |
| rotate safely | fake | 3 | 54 |
| revoke now | fake | 12 | 36 |
| — | — | 14 correct | 0 |

Every single error is the same shape: **the agent remediated something that did
not need remediating.** There is not one case in forty where it under-reacted.

## What did not happen matters more than what did

Two errors were available and neither occurred:

- **Dismissing a live key.** Regret would have been 2 288 minutes — one such
  case would have exceeded the total regret of all twenty-six errors combined
  by a factor of nearly six. It never happened, because P2 never dismisses at
  any belief it can reach.
- **Revoking a live key.** Regret 220. Also never happened on this sample,
  though it is reachable in principle — P2 revokes in the malformed buckets, and
  a live key could land there. With 14 live cases and revoke firing on about
  14.55% of findings, roughly two such cases were expected and zero occurred.
  That is a sampling accident, not a guarantee, and it is one of the places
  forty cases is too few.

## What I take from this

**The error profile is the cost matrix doing what it was built to do.** I priced
dismissing a live key at 2400 and rotating an inert one at 20–30, a ratio of
about 100:1. The agent duly spent 398 minutes of unnecessary remediation to
avoid ever risking the expensive error. Given those numbers that is not a
failure, it is the intended trade — but it is only correct in proportion to how
well I estimated the ratio, and I estimated both sides of it.

**Errors of this shape cannot be fixed with more free evidence.** Eleven of the
twenty-six are rotate-on-revoked, and separating live from revoked is precisely
what the two free features cannot do. The only lever is the probe, and the probe
was correctly declined at these beliefs.

**A cheaper probe would fix some of them.** The five worst all sit at P(live)
between 0.57 and 0.63, where EVSI is 0.00 — no probe outcome changes the action,
so no price makes it worth buying. But the twelve revoke-on-fake errors sit in
the malformed buckets where EVSI is 1.40 and 5.21. Those are the ones a cheaper
probe reaches, and it is consistent with the probe-price sweep: at one minute
the agent buys evidence on 14.55% of findings rather than 3.98%.
