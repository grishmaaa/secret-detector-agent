# Probability Decision Record

One finding, taken all the way through. I chose a case where the answer is genuinely not obvious to me, and where the arithmetic ended up telling me something I would have got wrong by instinct.

## Audit Data

| Field | Value |
|---|---|
| Date | 2026-08-27 |
| Provider | OpenAI, project keys only |
| Detector assumed | GitHub secret scanning (~75% precision) |
| Model version | prior `0.48 / 0.27 / 0.25`; three features; likelihood tables v1 |
| Policy version | expected-cost minimisation over five actions, no tuned threshold |
| Cost version | fifteen cells in engineer-minutes, v1 |
| Status | simulation — no admin credential, no live API call was made |

## Case

A scanner reports a string in `src/services/summariser.py`. It is assigned to a variable called `OPENAI_API_KEY`, it is the right length and character set for an OpenAI project key, and it was added eleven months ago in a commit whose message reads "wire up summarisation".

I do not know whether the key works.

## Evidence

Only the free features. Nothing has been bought yet.

| Feature | Value |
|---|---|
| Placeholder context | `production` — source directory, a real-sounding variable name, a commit message about shipping a feature |
| Well-formedness | `well-formed` |

## Hidden States

1. **Live** — still authenticates
2. **Revoked** — was real, no longer works
3. **Fake** — hard-coded, never authenticated against anything

## Beliefs

Starting from the prior and applying both free features:

| State | Prior | After evidence |
|---|---|---|
| Live | 0.4800 | **0.6329** |
| Revoked | 0.2700 | **0.3560** |
| Fake | 0.2500 | **0.0111** |

Sums to 1.0000.

The evidence did one job well and one job not at all. **Fake collapses** from 0.25 to 0.011 — a well-formed string in a source file with a production-sounding name is very unlikely to be something a developer typed as a placeholder.

**Live versus revoked did not move.** The ratio was 0.48 / 0.27 = 1.778 before and 0.6329 / 0.3560 = 1.778 after. Identical, because those two states have the same likelihood on both features and the multiplication cancels. Nothing I can see in this repository distinguishes a key that works from one that was turned off.

## Event

`Live` is the state that matters. The other two both mean the string is harmless; they differ only in why.

## Actions

Dismiss · Investigate · Escalate · Revoke now · Rotate safely.

## Costs

Expected cost under the belief above, in engineer-minutes:

| Action | Expected cost |
|---|---|
| **Rotate safely** | **86.85** |
| Escalate | 106.68 |
| Revoke now | 209.62 |
| Dismiss | 1519.69 |

## Policy

Choose the action with the lowest expected cost. There is no tuned threshold — the boundaries fall out of the cost matrix:

| P(live) | Cheapest action |
|---|---|
| below 0.00070 | Dismiss |
| 0.00070 – 0.09386 | Revoke now |
| above 0.09386 | Rotate safely |

This finding sits at **P(live) = 0.6329**, which is nearly seven times the rotate-safely boundary. Not a marginal call.

## Should I investigate first?

This is the part I expected to go the other way.

I have a probe available — `last_used_at` from the admin API, ten minutes. The obvious move is to buy it: P(live) is 0.63, I am far from certain, more information sounds better.

So I priced it. For each possible outcome, what would I believe, and what would I then do?

| Outcome | Probability | P(live) after | Best action | Cost |
|---|---|---|---|---|
| `recent` | 0.3870 | 0.9813 | Rotate safely | 118.32 |
| `old` | 0.4047 | 0.3128 | Rotate safely | 58.14 |
| `null` | 0.2083 | 0.6076 | Rotate safely | 84.18 |

**Every outcome leads to the same action.**

Expected cost of acting now: **86.85**
Expected cost after probing: **86.85**
Value of the information: **0.00**

The probe costs ten minutes and is worth nothing, because nothing it could return would change what I do. I would find out more about the world and behave identically.

This is the rule I wrote down when I first split investigate out as its own action — *investigating is only worth doing if the action might change afterwards* — arriving as a consequence rather than as something I asserted. I did not expect it to fire on this case, and my instinct would have been to buy the probe.

## Decision

**Rotate safely. Do not investigate.**

Issue a replacement key into the secrets vault, find and update whatever was using the old one, confirm nothing is still calling it, then revoke.

Not *revoke now*, because at P(live) = 0.63 something is probably depending on this key and the outage would cost more than the deploy. Not *dismiss*, because 0.63 is three orders of magnitude above the dismissal boundary. Not *escalate*, because a human would cost thirty minutes and reach the same answer — and in this case even a perfect oracle would, since rotate-safely is optimal in every outcome.

---

# Bayesian Update

§10 asks me to add one new item of evidence and follow it through. I am doing it with the probe **even though I just showed it is not worth buying**, because the arithmetic is the point and it demonstrates why the answer was zero.

**1. Prior.** Live 0.6329, revoked 0.3560, fake 0.0111. This is the posterior from the free evidence, which becomes the prior for this step.

**2. New evidence.** The probe returns `old` — a timestamp from roughly eight months ago. Something authenticated with this key once, and not recently.

**3. Likelihoods.** `P(old | state)`:

| State | Likelihood |
|---|---|
| Live | 0.20 |
| Revoked | 0.78 |
| Fake | 0.04 |

A revoked key's timestamp freezes at whatever it last did before being turned off, so `old` is what a revoked key usually looks like. A live key that has been idle for months can also produce it. A fake key almost never can, because it was never in the account.

**4. Posterior.**

| State | Before | After |
|---|---|---|
| Live | 0.6329 | **0.3128** |
| Revoked | 0.3560 | **0.6861** |
| Fake | 0.0111 | **0.0011** |

Sums to 1.0000. **The belief flips** — from probably live to probably revoked. The live/revoked ratio goes from 1.778 to 0.456, and one call did all of it. Neither free feature moved that ratio by any amount at all.

**5. Compare with the threshold.** P(live) = 0.3128, still well above the rotate-safely boundary of 0.09386.

**6. New action.** **Rotate safely** — unchanged.

| Action | Before probe | After probe |
|---|---|---|
| **Rotate safely** | **86.85** | **58.14** |
| Escalate | 106.68 | 68.91 |
| Revoke now | 209.62 | 104.59 |
| Dismiss | 1519.69 | 752.02 |

Every action got cheaper because the belief moved away from the expensive state, but the ordering did not change and the decision did not change. Which is exactly what the value-of-information calculation predicted before I spent the ten minutes.

## What I take from this case

**Being much less sure is not the same as being about to act differently.** The probe moved P(live) from 0.63 to 0.31 — it halved my confidence in the state that matters — and the right action was identical before and after. I would have called that impossible before working it through.

**The threshold is not near 0.5.** It is 0.09. Anyone building this by instinct would put the line at "more likely than not", and would then dismiss findings this model rotates. That gap is the experiment I want to run.

**The free evidence and the probe do completely different jobs.** The free features killed *fake*. The probe was the only thing that touched *live versus revoked*. Neither could do the other's work, and on this case the one that did the more dramatic thing was the one not worth paying for.
