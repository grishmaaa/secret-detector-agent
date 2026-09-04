# The same agent, on a credential that does not hide its identifier

Everything in this project rests on one property of an OpenAI key: the
whole string is secret, so the only way to learn whether it works is to
use it -- and using a credential found in a repository is the one thing
the agent may not do. That is where the zero-bits invariance comes from.

An AWS access key is not like that. The `AKIA...` half is a public
identifier. Given it alone the agent can ask **its own** IAM API whether
that key ID is present and Active, without ever touching the secret
half. Same company, same private repositories, same scanner, same five
states, same cost matrix. One thing changes, and it is free.

## What the identifier separates, in bits

| Free evidence | live vs revoked | live vs zero_scope | live vs fake |
|---|---|---|---|
| repository context | 0.0000 | 0.0000 | 0.3531 |
| well-formedness | 0.0000 | 0.0000 | 0.3637 |
| identifier lookup | 0.8400 | 0.0000 | 0.8981 |

The first two rows are the Week 1 result: the text features carry
exactly nothing about live versus revoked. The third row is the
environment change, and it does two things at once.

**It resolves the axis the whole project was built around** --
0.8400 bits, against
0.0000 from everything that was free before.

**And it carries 0.0000
bits about live versus zero_scope.** That is not a rounding artefact,
it is exact, and it is exact for the same reason the Week 1 result was:
the two rows are identical. IAM reports whether a key is Active. A key
authorised for nothing is Active. **The invariance does not disappear
when the identifier becomes public. It moves.**

## What it does to the agent

| | OpenAI (Week 2 agent) | AWS (same agent) |
|---|---|---|
| regret, min/finding | 8.23 | 2.77 |
| total cost, min/finding | 59.17 | 52.43 |
| probe bought | 46.8% | 4.0% |
| sent to a human | 2.8% | 2.2% |
| balanced accuracy | 0.459 | 0.579 |
| `live` recall | 0.986 | 0.981 |
| `revoked` recall | 0.085 | 0.961 |
| `fake` recall | 0.939 | 0.954 |
| `zero_scope` recall | 0.286 | 0.000 |
| `other` recall | 0.000 | 0.000 |

Regret falls from 8.23 to 2.77 minutes
per finding. W2-5 priced perfect live-versus-revoked knowledge at
6.75 minutes of the available regret; the free identifier
recovers **80.8%** of it, at zero cost, on every
finding rather than on the minority where a probe was worth buying.

## A component that survives the move and stops earning its place

W2-6 swept the scope field's reliability and found that about 88% of
its value came from its `absent` column -- which detects `fake` -- and
only 12% from the parameter I had invented for detecting `zero_scope`.
It was mostly a `fake` detector arriving on the same call.

The AWS identifier reports `absent` for free, before the scope field is
bought. So the 88% is already paid for by something else, and what is
left for scope is the 12%:

| | value of reading scope, min/finding | `zero_scope` recall |
|---|---|---|
| OpenAI | +2.27 | 0.286 |
| AWS | -0.23 | 0.000 |

**Twelve per cent is not enough to pay for the call.** The field goes
from earning 2.27 minutes a finding to costing 0.23, and it never
identifies the state it exists for in either world. W2-6 measured how
much of it was load-bearing; this measures what happens when the rest
is supplied for free, and the answer is that the remainder does not
stand on its own.

> **A bug worth recording, because the brief names it.** The first
> version of this experiment drew the scope reading independently of
> the identifier lookup and had the agent multiply both likelihoods.
> Both channels report one underlying event -- is this credential in
> our account -- so that double-counts it, and generates observations
> that cannot occur: an `absent` identifier beside a `nonzero` scope
> reading says the key is not in the account and also that we read its
> permissions. It made scope look 0.87 minutes harmful rather than
> 0.23. Stop-rule 5 in the brief is exactly this -- correlated evidence
> sources feel like more information and are not -- and I met it as a
> defect in my own simulator before I met it as a paragraph in my own
> paper. The fix is the honest statement of the deployment: you read a
> key's permissions only once you have located the key, so scope has
> two outcomes there, not three.

## What is portable and what was local

| Component | Survives the move? |
|---|---|
| The cost matrix and the derived threshold | **Yes.** Nothing about the credential format touches what an outage or a breach costs |
| Escalation as a rule rather than a priced action | **Yes.** It triggers on `other` and on worst-case cost, neither of which the identifier touches |
| Buy evidence only when an outcome could change the action | **Yes.** It is the reason the probe is not bought here despite still being informative |
| The zero-bits invariance | **No, and this is the finding.** It is a property of the credential format, not of secret scanning. It survives as a *different* invariance on a different pair of states |
| The probe as the project's central mechanism | **No.** It is bought on 4.0% of findings here against 46.8% |
| The scope field as a purchase | **No.** Its `absent` column is supplied free here; the 12% that remains does not pay for the call |
| `zero_scope` as an unresolved state | **Yes, and it gets worse.** Recall falls to 0.000, because the one channel that touched it no longer earns its way into the policy |

## Then change one variable at a time

### 1. The cost of a false negative rises

The false negative here is dismissing a key that is live, and that cost
is not a free parameter -- it is P(exploitation) times a breach. So the
lever is the probability, and the first thing the request exposes is
that **it cannot be granted**: a probability is bounded at 1, so the
cost of this error can rise by a factor of ten and no further. Asking
for a hundredfold increase is asking for a probability of 10.

| Factor | p_exploit | Cost of dismissing a live key | Regret | Probe bought | Human | Balanced acc. |
|---|---|---|---|---|---|---|
| x1 | 0.10 | 244 | 8.23 | 46.8% | 2.8% | 0.459 |
| x2.5 | 0.25 | 604 | 15.56 | 46.8% | 27.4% | 0.197 |
| x5 | 0.50 | 1202 | 15.28 | 58.2% | 26.6% | 0.198 |
| x10 | 1.00 | 2400 | 11.70 | 46.8% | 12.6% | 0.197 |

**Regret is worst in the middle, not at the top**, and so is human
load: 27.4% of findings escalated at p = 0.25 against 12.6% at p = 1.00,
where the stakes are four times higher. That is not noise. It is two
design decisions from two different commits disagreeing, and the
mechanism is worth stating exactly.

`dismiss` is the only action whose worst case moves with p. At p = 0.10
its worst case is 244 minutes, under the 400-minute ceiling W2-4b
imposed, so the agent may take it. At p = 0.25 the worst case is 604 and
the ceiling forbids it -- but on expected cost dismiss is *still the
cheapest action* on 57 of 500 findings. Those 57 go to a human, not
because the agent is unsure but because the action it wants is no longer
permitted. By p = 0.50, `revoke` has overtaken dismiss on expected cost
anyway; revoke's worst case is 332, under the ceiling, so the ceiling
stops binding and escalation falls back to 1.0% plus the residual rule.

**A worst-case ceiling is not a monotone safety dial.** Raising the
stakes can reduce human involvement, because it can push the agent off
a cheap-in-expectation action that is expensive in the worst case and
onto an expensive-in-expectation action that is not. The band where the
two rules disagree is the band that costs the most, and nothing in
either rule announces where that band is.

Balanced accuracy tells the second half of the story. It falls from
0.459 to 0.197 and stays there for every p above 0.10, because once
dismiss leaves the policy there is no action left that means *this
string is harmless*, and the states that need one -- `fake` and
`zero_scope` -- become unlabellable again. That is the W2-4 failure
returning, from the opposite direction: the first time it was caused by
a cost that was too high by accident, and here by one that is too high
on purpose.

### 2. Obtaining evidence becomes ten times more expensive

| Factor | Probe price, min | Regret | Probe bought | Human | Balanced acc. |
|---|---|---|---|---|---|
| x1 | 3 | 8.23 | 46.8% | 2.8% | 0.459 |
| x2 | 6 | 9.20 | 16.0% | 1.4% | 0.405 |
| x5 | 15 | 10.50 | 0.0% | 1.0% | 0.382 |
| x10 | 30 | 10.50 | 0.0% | 1.0% | 0.382 |
| x20 | 60 | 10.50 | 0.0% | 1.0% | 0.382 |

The probe dies between x2 and x5. At six minutes it is still bought on
16.0% of findings; at fifteen it is bought on none, and regret saturates
at 10.50 -- exactly the no-scope number, because the scope field rides
on the probe and goes with it. **The policy does not degrade smoothly
under evidence cost, it switches off.** The agent does not shift from
asking to escalating either: human load *falls* from 2.8% to 1.0%,
because the ceiling and residual triggers never depended on the probe.
An expensive-evidence deployment does not get a more cautious agent, it
gets a blinder one that is no more likely to ask for help.

### 3. Historical data becomes unreliable

This one is already answered, and it is the reason W2-7 and W2-8 exist.
The priors and every likelihood row were estimated, so *unreliable
history* is not a hypothetical here -- it is the standing condition.
W2-7 generates the world from different tables and measures the gap:
policy conclusions survive in 100% of worlds, the structural conclusion
does not. W2-8 gives the agent a way to notice, from its own biased
feedback, at 100% detection for the differences that cost it anything.
What the agent should do while it is unsure whether its own priors are
valid is the one part still unanswered: it can raise its hand and it
cannot repair itself, because relaxing the invariance means estimating
two rows from labels it does not have enough of.

## The honest reading

The honest reading is that the paper's machinery is portable and the
paper's *headline* is not. A reviewer told me the Week 1 result was a
property of credential formats that hide the identifier rather than of
secret scanning. This is that claim with a number attached, and the
number says the reviewer was right -- but also that the problem does not
go away when the format changes, because the states that remain
indistinguishable are simply a different pair.

