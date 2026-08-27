# Section 9 — what the experiment said

Four policies and the baseline, forty frozen cases, seed `20260827`. Two numbers
for each policy: the exact expected cost, which I can compute in closed form
because there are only fifty-four possible worlds, and the realised cost on the
sample, which is what forty findings actually cost and carries the noise that
comes with forty draws.

Run it with `python experiments/run_experiment.py`.

## The table

| | Policy | Expected cost | vs baseline | Escalates | Probes |
|---|---|---|---|---|---|
| baseline | escalate everything | 87.60 | — | 100% | 0% |
| P0 | prior only, no evidence | 70.70 | −19.3% | 0% | 0% |
| P1 | evidence, threshold 0.5 | 185.21 | **+111.4%** | 0% | 0% |
| P2 | evidence, cost-derived | 68.94 | **−21.3%** | 0% | 0% |
| P3 | P2 plus the probe | 68.86 | −21.4% | 0% | 4.0% |

On the forty cases: baseline 2880 minutes, P2 2130, a 26% saving.

## What I did not expect

**Almost none of the saving comes from the evidence.** P0 looks at nothing at
all — it knows the base rates and rotates every finding — and it already beats
the baseline by 19.3%. P2 reads both free features and gets to 21.3%. So the
evidence is worth **1.76 minutes per finding**, and the other nineteen points
come from a single decision: stop asking a human. My whole belief model buys
less than a tenth of the improvement. The cost structure does the work.

**The obvious threshold is worse than the procedure it replaces.** P1 is the
policy a sensible engineer writes on the first afternoon: work out the
probability, rotate if it is more likely than not, dismiss otherwise. It costs
**more than twice** the baseline. My real threshold is 0.09, not 0.5, so
everything between those two numbers gets dismissed instead of rotated — and
dismissing a live key costs 2400. One case in the forty accounts for 2400 of
P1's 4292 minutes.

**And P1 is not just bad, it is unstable.** Sweeping the live-versus-revoked
split, P1 costs 185 at 64% live and **901 at 50%**. A modest change in an input
I am not sure about flips the largest bucket of findings from rotate to dismiss
and multiplies the bill by five. P2 moves from 68.9 to 59.4 across the same
range — smoothly, and in the direction you would expect. A policy that reads a
threshold off the cost matrix cannot fall off this cliff, because the threshold
moves when the costs move.

**The probe changes behaviour without changing the total.** Repricing it from
ten minutes to three made P3 buy it — but only on the neutral/malformed
bucket, which is 4% of findings, worth about five minutes each. Aggregate gain
over P2: **0.08 minutes per finding.** So the probe is genuinely worth buying
where it fires, and it barely registers in the total. Both halves are true and
I would rather report both than lead with the one that sounds better.

**Evidence is worthless when one action dominates.** With the outage priced at
zero, revoke-now is cheapest in every state, and P0 and P2 both cost exactly
46.0 — identical to two decimal places. Reading the features changes nothing,
because there is nothing they could say that would change the action. That is
the same thing the value-of-information calculation says about the probe, one
level up: information is worth what it changes.

**No policy ever escalates.** Zero percent across all four, which is the
simplex result showing up in a simulation rather than in an argument.

## What is wrong with this experiment

The case generator draws from the same likelihood tables the agent reasons
with, so the agent is being tested in a world that agrees with its own
assumptions. That flatters every policy that uses evidence, and it is the
reason `data/cases.json` is written once and never regenerated. A real test
needs findings whose true states came from somewhere other than my model, and
I do not have those.

Forty cases is also few enough that one dismissed live key moves the total by
more than half. The exact expected costs do not have that problem, which is why
both are reported.
