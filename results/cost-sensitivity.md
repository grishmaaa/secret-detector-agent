# Is the cost model wrong, or is that what hedging looks like?

The failure analysis put 76.6% of failures in a category I named
*wrong cost assumption*. That name was a guess dressed as a
measurement. The rule behind it only checks that the agent held real
probability on the true state and remediated anyway, which is equally
consistent with a mis-priced matrix and with an insurance premium
correctly paid.

> **Correction.** An earlier version of this analysis reported the
> value of perfect live-versus-revoked knowledge as 61.3% of the
> total. That figure compared an agent that could buy the probe
> against an oracle that could not, so the oracle was handicapped and
> its value understated. Recomputed with the same agent on both sides,
> the correct figure is **82.1%**. See `results/registry.md`.

## Step 1: how much of the regret was ever avoidable?

Regret here is measured against an agent that already knows the
answer. Nobody can match that. The honest question is whether any
policy working from the same information could have done better.

The agent's regret is **8.16 minutes per finding**.
Against every fixed policy on the same cases:

| Policy | Regret per finding |
|---|---|
| **the agent** | **8.16** |
| always rotate | 12.99 |
| always escalate | 30.00 |
| always dismiss | 56.63 |
| always revoke | 94.96 |

Minimising expected cost and minimising expected regret are the same
operation -- they differ by a per-case constant that no policy can
influence. So an agent whose model matches the world is regret-optimal
by construction, and in this simulation the agent's model *is* the
world: the cases were generated from its own likelihood tables.

**So all 8.16 minutes of it are the price of not
knowing the state, and none of it is a mistake** -- conditional on the
costs being right. That conditional is the whole remaining question,
and it is what Step 2 tests.

Where the unavoidable regret falls, by state:

| State | Regret per case of this state |
|---|---|
| live | 0.90 |
| revoked | 24.99 |
| fake | 1.10 |
| zero_scope | 18.33 |
| other | 22.69 |

## Step 2: what does getting a cost wrong actually cost?

The agent decides using a perturbed matrix and is then scored against
the true one. Every cell is scaled from a quarter to four times its
value, one at a time. The span is the worst case minus the best across
that range: how much regret is on the table if this number is wrong.

| Cost cell | True value | x0.25 | x0.5 | x1.0 | x2.0 | x4.0 | **Span** |
|---|---|---|---|---|---|---|---|
| `revoke|live` | 332.0 | 94.24 | 7.02 | 8.16 | 8.16 | 8.16 | **87.22** |
| `dismiss|live` | 244.5 | 56.63 | 24.54 | 8.16 | 16.61 | 17.20 | **48.47** |
| `rotate|live` | 112.0 | 8.16 | 8.16 | 8.16 | 12.93 | 56.63 | **48.47** |
| `rotate|fake` | 20.0 | 11.18 | 8.16 | 8.16 | 6.84 | 6.84 | **4.34** |
| `rotate|revoked` | 30.0 | 9.24 | 8.16 | 8.16 | 9.74 | 12.16 | **4.00** |
| `dismiss|zero_scope` | 5.0 | 6.84 | 6.84 | 8.16 | 8.16 | 8.39 | **1.55** |
| `rotate|zero_scope` | 30.0 | 8.32 | 8.00 | 8.16 | 6.84 | 6.84 | **1.48** |
| `dismiss|revoked` | 2.0 | 6.84 | 8.16 | 8.16 | 8.16 | 8.18 | **1.34** |
| `dismiss|other` | 63.4 | 6.96 | 8.15 | 8.16 | 8.16 | 8.23 | **1.28** |
| `rotate|other` | 48.0 | 8.16 | 8.16 | 8.16 | 6.96 | 6.96 | **1.21** |
| `dismiss|fake` | 2.0 | 8.16 | 8.16 | 8.16 | 8.16 | 9.00 | **0.83** |
| `revoke|fake` | 5.0 | 8.99 | 8.16 | 8.16 | 8.16 | 8.16 | **0.82** |
| `revoke|revoked` | 2.0 | 8.16 | 8.16 | 8.16 | 8.16 | 8.16 | **0.00** |
| `revoke|zero_scope` | 5.0 | 8.16 | 8.16 | 8.16 | 8.16 | 8.16 | **0.00** |
| `revoke|other` | 86.0 | 8.16 | 8.16 | 8.16 | 8.16 | 8.16 | **0.00** |

**3 of 15 cells do not matter at all.** Scaling
them by a factor of sixteen, from a quarter to four times, moves regret
by less than 0.01 minutes per finding. Those are numbers nobody needs
to defend, and arguing about them is wasted effort.

**12 cells matter**, and the damage is wildly asymmetric.
For each, how much regret rises if the number is set too low
against how much it rises if it is set too high:

| Cell | Span | Too low costs | Too high costs |
|---|---|---|---|
| `revoke|live` | 87.22 | +86.07 | +0.00 |
| `dismiss|live` | 48.47 | +48.47 | +9.04 |
| `rotate|live` | 48.47 | +0.00 | +48.47 |
| `rotate|fake` | 4.34 | +3.01 | +-1.33 |
| `rotate|revoked` | 4.00 | +1.08 | +4.00 |
| `dismiss|zero_scope` | 1.55 | +-1.33 | +0.23 |
| `rotate|zero_scope` | 1.48 | +0.15 | +-1.33 |
| `dismiss|revoked` | 1.34 | +0.00 | +0.01 |
| `dismiss|other` | 1.28 | +-0.02 | +0.07 |
| `rotate|other` | 1.21 | +0.00 | +-1.21 |
| `dismiss|fake` | 0.83 | +0.00 | +0.83 |
| `revoke|fake` | 0.82 | +0.82 | +0.00 |

**The dangerous direction is not the same for every cell, and the
split is not random.**

For `rotate` -- the action the agent takes by default -- over-pricing is what hurts and under-pricing is free:

- `rotate|live`: too low +0.00, too high **+48.47**
- `rotate|fake`: too low +3.01, too high **+-1.33**
- `rotate|revoked`: too low +1.08, too high **+4.00**
- `rotate|zero_scope`: too low +0.15, too high **+-1.33**
- `rotate|other`: too low +0.00, too high **+-1.21**

For `revoke` and `dismiss` -- actions it rarely takes -- it is the
other way round:

- `revoke|live`: too low **+86.07**, too high +0.00
- `dismiss|live`: too low **+48.47**, too high +9.04
- `dismiss|zero_scope`: too low **+-1.33**, too high +0.23
- `dismiss|revoked`: too low **+0.00**, too high +0.01
- `dismiss|other`: too low **+-0.02**, too high +0.07

That is 10 cells. The remaining 2 live cells have spans under a minute per finding
(`dismiss|fake` 0.83, `revoke|fake` 0.82) and do not follow the pattern in either direction. At that size
they are sampling noise on 500 cases and I am not going to read
anything into their signs.

The mechanism is the same in both halves. An error is expensive
exactly when it pushes the agent off the action that was correct:
over-pricing the default drives it away from something that was
working, and under-pricing an alternative lures it onto something
that was not. Errors in the other direction confirm a decision the
agent was already making and cost nothing.

Which gives a rule that is actually usable when you are guessing a
number: **be generous towards the action you expect to take, and
harsh towards the ones you do not.** A conservative estimate is
not uniformly high or uniformly low; it is whichever direction
keeps the agent where it already was.

The magnitudes are worth stating too. `revoke|live` set to a
quarter of its value costs 86 minutes per
finding against a base of 8.16 -- an order of
magnitude worse than the total regret being analysed. Getting one
cell badly wrong is more damaging than every hedging decision the
agent makes put together.

## The answer

**7 cell(s) score measurably better at a different
value:**

- `revoke|live` at x0.5, improving regret by 1.14 min/finding
- `rotate|fake` at x2.0, improving regret by 1.33 min/finding
- `dismiss|zero_scope` at x0.25, improving regret by 1.33 min/finding
- `rotate|zero_scope` at x2.0, improving regret by 1.33 min/finding
- `dismiss|revoked` at x0.25, improving regret by 1.33 min/finding
- `dismiss|other` at x0.25, improving regret by 1.21 min/finding
- `rotate|other` at x2.0, improving regret by 1.21 min/finding

Judge those against the size of the effect before acting on them. The largest is 1.33 minutes per
finding, on a base of 8.16 — under a percent, and on states with few
enough cases in 500 that sampling noise is a live explanation. I
would not change a number on that evidence.

So the 76.6% figure was mis-labelled, and I am correcting it rather
than leaving it in the paper. Those failures are not the cost model
being wrong. They are the agent buying insurance it turned out not to
need, on cases where refusing to buy it would have been the worse bet.
Regret against a hindsight-perfect agent counts every premium as a
mistake, and an agent that never pays a premium is one that gets
wiped out the first time it is unlucky.

The category should be read as **irreducible hedging cost**, not as an
error. What the sweep adds on top is the more useful engineering
finding: only 12 of the 15 numbers in this matrix
are worth arguing about, and the rest can be wrong by a factor of four
in either direction without anybody noticing.

