# Can organisational metadata recover the live/revoked ceiling?

The current agent's regret is **7.77** minutes per finding.
Perfect knowledge of live-versus-revoked would remove **6.38** of that. Nothing in the model reaches it. Two
channels from the practitioner discussion might.

Both the baseline and the ceiling above are computed with the same
agent used everywhere below, so nothing here is compared across
architectures.

Neither is given an invented likelihood table. Each reduces to one
parameter, and both are swept from nothing to perfect:

- **k, registry coverage** — the share of credentials in use that went
  through the provisioning pipeline that maintains the hash table.
- **c, rotation compliance** — the share of keys genuinely rotated on
  the stated schedule.

Age is **free**: commit timestamps are already in the repository. The
registry lookup is priced at 1 minute and the agent
buys it only when its expected value exceeds that.

## Commit age alone, at zero cost

| Rotation compliance *c* | Regret | Recovered |
|---|---|---|
| 0.00 | 1.83 | +93.2% |
| 0.20 | 6.67 | +17.3% |
| 0.40 | 8.07 | -4.7% |
| 0.50 | 7.77 | +0.0% |
| 0.60 | 7.28 | +7.7% |
| 0.80 | 5.78 | +31.2% |
| 0.95 | 4.12 | +57.3% |
| 1.00 | 1.96 | +91.1% |

At *c* = 0.50 the channel carries nothing by construction — a
organisation that rotates at random makes age uninformative, and the
two likelihood rows become identical. That is the invariance
reappearing in a new place, and it is the correct behaviour rather
than a modelling artefact.

Away from 0.50 it recovers up to **93.2%** of the live/revoked ceiling, at *c* = 0.00, **for free**.

Note that *c* = 0 is as informative as *c* = 1. An organisation that
reliably never rotates tells you as much as one that reliably always
does; what destroys the signal is inconsistency, not laxity. That is
worth saying to a practitioner, because it inverts the intuition that
better security hygiene is what makes the evidence work.

## Registry alone, with age uninformative

| Coverage *k* | Regret | Bought on | Recovered |
|---|---|---|---|
| 0.00 | 7.77 | 0.8% | +0.0% |
| 0.20 | 7.77 | 0.8% | +0.0% |
| 0.40 | 7.98 | 4.6% | -3.3% |
| 0.50 | 7.98 | 4.6% | -3.3% |
| 0.60 | 7.98 | 4.6% | -3.3% |
| 0.80 | 7.85 | 15.6% | -1.2% |
| 0.95 | 2.49 | 88.6% | +82.8% |
| 1.00 | 1.56 | 88.6% | +97.5% |

**A partial registry is close to worthless, and the cliff is sharp.**
At coverage 0.80 the agent buys the lookup on 16% of
findings and recovers -1%. At 0.95 it buys on
89% and recovers 83%. Four-fifths of the way to full
coverage buys you almost none of the value.

The reason is the asymmetry the practitioner and I both flagged in the
thread. A *match* is dispositive at any coverage -- if the string is
the deployed value, the key is live. But most findings are misses, and
a miss only means *revoked* if you can rule out *never provisioned
through the pipeline*. At k = 0.8 one credential in five was never in
the table to begin with, and that residual doubt is enough to leave the
belief on the same side of every boundary. The lookup is not worth its
minute, so the agent does not buy it, so it recovers nothing.

That is a concrete instruction for anyone building this: **near-total
coverage or do not bother.** A registry covering most of your
credentials has most of the maintenance burden and almost none of the
benefit.

## Both together

Recovered share of the 6.38-minute live/revoked ceiling.

| *c* \ *k* | 0.00 | 0.20 | 0.40 | 0.50 | 0.60 | 0.80 | 0.95 | 1.00 |
|---|---|---|---|---|---|---|---|---|
| **0.00** | 93% | 93% | 93% | 93% | 93% | 92% | 93% | 98% |
| **0.20** | 17% | 17% | 42% | 42% | 34% | 57% | 66% | 97% |
| **0.40** | -5% | -5% | -5% | 26% | 26% | 40% | 80% | 97% |
| **0.50** | 0% | 0% | -3% | -3% | -3% | -1% | 83% | 97% |
| **0.60** | 8% | 8% | 7% | 15% | 20% | 27% | 81% | 97% |
| **0.80** | 31% | 31% | 31% | 39% | 45% | 49% | 55% | 97% |
| **0.95** | 57% | 57% | 64% | 61% | 69% | 84% | 85% | 90% |
| **1.00** | 91% | 91% | 91% | 91% | 91% | 94% | 93% | 97% |

**Peak: 98% of the ceiling**, at *k* = 1.00, *c* = 0.00, regret 1.50 against a base of 7.77.

A realistic organisation is not at the corners. For coverage
between 0.4 and 0.8 and compliance between 0.6 and 0.95 — an
organisation with a provisioning pipeline that most teams use and a
rotation policy that mostly happens — the recovered share runs from
**7% to 84%**.

## What this answers

The question was whether organisational registry and rotation metadata
can recover a substantial fraction of the 82.0%. On this model the
answer is **yes, and mostly from the free channel**.

The result worth carrying forward is not the peak number. It is that
commit age costs nothing, is already present in every repository this
agent will ever see, and speaks directly to the one axis that every
static text feature is silent on. The Week 1 invariance said repository
evidence cannot separate live from revoked. The correct statement is
narrower: **static text cannot, because text does not change when a
key is revoked.** Revocation is an event in time, and the repository
records time.

The two channels also fail in different places, which is why the
combined table is not the maximum of the two. Age dies at c = 0.5 and
the registry dies below k = 0.9, so an organisation that rotates
erratically and provisions incompletely gets almost nothing from
either -- the 5% corner of the realistic band. One that is disciplined
in either direction gets most of the ceiling. **The evidence available
to this agent is a function of how the organisation runs itself, not
of what the agent is allowed to look at.**

What stops this being a solved problem is that the whole surface is
conditional on two numbers nobody has measured. Every figure here is a
function of *k* and *c*, and neither is known for any real
organisation. The contribution is the shape of the dependence and the
identification of a free channel, not a recovered quantity.

