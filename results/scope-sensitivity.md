# How much of the best agent rests on one invented number?

Every other channel added this week is swept rather than assumed. The
scope field was not: `scope_probe.py` commits a likelihood table, and
P6 -- the cheapest agent in the project, and the only one that tells
five states apart -- stands on it. This puts it on the same footing as
the rest.

The parameter is **q**, the probability that a key authorised for
nothing actually reports zero scope. At q = 0.02 its row is identical
to `live`'s and the field says nothing about the state it exists to
detect. The committed table used q = 0.95.

The rest of the table stays fixed, and that is a distinction rather
than an oversight. A key *with* permissions reporting permissions is
not an empirical guess, it is what the field means; and the `absent`
column is copied from the probe's `null` row because *not in our
account* is the same event in both. Only q is genuinely uncertain.

## The sweep

| q | Regret | Total cost | Probe bought | Balanced acc. | live | revoked | fake | zero_scope |
|---|---|---|---|---|---|---|---|---|
| *no scope* | 10.50 | 60.07 | 1.0% | 0.382 | 0.995 | 0.008 | 0.573 | 0.000 |
| 0.02 | 8.51 | 59.45 | 46.8% | 0.402 | 0.986 | 0.085 | 0.939 | 0.000 |
| 0.10 | 8.51 | 59.45 | 46.8% | 0.402 | 0.986 | 0.085 | 0.939 | 0.000 |
| 0.25 | 8.53 | 59.47 | 46.8% | 0.402 | 0.986 | 0.085 | 0.939 | 0.000 |
| 0.50 | 8.36 | 59.30 | 46.8% | 0.431 | 0.986 | 0.085 | 0.939 | 0.143 |
| 0.75 | 8.22 | 59.16 | 46.8% | 0.459 | 0.986 | 0.085 | 0.939 | 0.286 |
| 0.90 | 8.23 | 59.17 | 46.8% | 0.459 | 0.986 | 0.085 | 0.939 | 0.286 |
| 0.95 **←committed** | 8.23 | 59.17 | 46.8% | 0.459 | 0.986 | 0.085 | 0.939 | 0.286 |
| 1.00 | 8.23 | 59.17 | 46.8% | 0.459 | 0.986 | 0.085 | 0.939 | 0.286 |

## What survives, and it is not what I expected

Read the *no scope* row against the **q = 0.02** row. At q = 0.02 the
field is worthless for the state it was introduced to detect --
`zero_scope` recall is 0.000, identical to not having the field at
all. And yet:

| | no scope | q = 0.02 | q = 0.95 |
|---|---|---|---|
| regret | 10.50 | 8.51 | 8.23 |
| total cost | 60.07 | 59.45 | 59.17 |
| probe bought | 1.0% | 46.8% | 46.8% |
| balanced acc. | 0.382 | 0.402 | 0.459 |
| `fake` recall | 0.573 | 0.939 | 0.939 |
| `zero_scope` recall | 0.000 | 0.000 | 0.286 |

**Almost none of the scope field's value comes from the number I
invented.** Of the 2.27 minutes of regret it removes,
**1.99 arrives at q = 0.02** and only 0.28 more accumulates
across the entire rest of the range -- 88% of
the benefit against 12%.

The reason is the `absent` column, and that column was not invented.
It was copied from the probe's existing `null` row, because *the key
is not in our account* is one event that both fields report. A `fake`
string was never in the account, so scope comes back absent, and that
is what takes `fake` recall from 0.573 to 0.939 and drives the probe's
purchase rate from 1.0% to 46.8%. All of that is present at q = 0.02.

What q actually buys is `zero_scope` recall -- 0.000 up to 0.286 -- on a state holding 4% of the prior. Real, small, and
the only part of the result exposed to a guess.

## The honest reading

I set out to check how much of the best agent rests on one invented
number, expecting to have to defend 0.95. The answer is that the
number carries about 12% of the field's value and
the conclusion does not depend on it at all: **every** value of q in
the sweep, including the one where the field cannot see the state it
was built for, leaves the agent better on regret, cost and balanced
accuracy than not reading scope at all.

There is a lesson in that which is worth more than the sensitivity
check. I introduced the scope field to detect `zero_scope`, argued for
it on those grounds, and reported it as the fix for that state. It
mostly is not. It is a `fake` detector that happens to arrive on the
same call, and it earns its place for a reason I did not anticipate
and would not have found without putting the parameter on a sweep.
**The stated reason a design change works is not always the reason it
works**, and only taking the assumption away shows which is which.

This is the third quantity handled this way -- exploitation
probability, registry coverage and rotation compliance, now scope
reliability. In each case a number I could not defend was replaced by
a sweep, and in each case the useful finding was about where the
conclusion changes rather than what it equals at a point estimate.

