# Section 9 — what the experiment said

Four policies and the baseline, forty frozen cases, seed `20260827`. Two numbers
for each policy: the exact expected cost, which I can compute in closed form
because there are only fifty-four possible worlds, and the realised cost on the
sample, which is what forty findings actually cost and carries the noise that
comes with forty draws.

Run it with `python experiments/run_experiment.py`.

## The table

| | Policy | Expected cost | vs baseline | Escalates | Probes | Differs from P0 |
|---|---|---|---|---|---|---|
| baseline | escalate everything | 84.80 | — | 100% | 0% | — |
| P0 | prior only, no evidence | 66.86 | −21.2% | 0% | 0% | — |
| P1 | hand-picked thresholds, 4 actions | 77.79 | −8.3% | 0% | 0% | 14.55% |
| P1-trunc | hand-picked, 2 actions only | 181.78 | **+114.4%** | 0% | 0% | 14.55% |
| P2 | cost-derived | 65.11 | **−23.2%** | 0% | 0% | **14.55%** |
| P3 | P2 plus the probe | 65.03 | −23.3% | 0% | 4.0% | 10.57% |

On the forty frozen cases: baseline 2820 minutes, P2 2018, a 28.4% saving. That
draw holds 14 live keys out of 40 — a live share of 0.35 against a prior of
0.48, about 1.6 standard deviations low — so the sampled figure and the exact
one are not interchangeable.

## What I did not expect

**Almost none of the saving comes from the evidence.** P0 looks at nothing at
all — it knows the base rates and rotates every finding — and it already beats
the baseline by 21.2%. P2 reads both free features and gets to 23.2%. So the
evidence is worth **1.75 minutes per finding**, and the other twenty-one points
come from a single decision: stop asking a human. It does change the action on
14.55% of findings, so it is not inert; the action it changes to is just cheap
enough that the total barely moves.

**My first version of the threshold comparison was confounded, and I am
reporting the correction rather than the original.** P1 was defined as
"threshold 0.5, else dismiss", which changed the boundary *and* removed
revoke-now from the action set. Holding the threshold at 0.5 and varying only
the fallback:

| Fallback | Cost | vs baseline |
|---|---|---|
| dismiss | 181.78 | +114.4% |
| escalate | 71.13 | −16.1% |
| revoke now | 74.25 | −12.4% |
| rotate safely | 66.86 | −21.2% |

**The catastrophe was dismissing, not thresholding.** Given all four actions and
a second hand-picked cut at 0.05, P1 costs 77.79 — 8.3% better than the
baseline, and 19.5% worse than P2. That is the honest size of the effect, and it
is a much smaller claim than the one I made first.

**What does survive is the response to a prior I cannot pin down.** P1 is
non-monotonic: 103.8 at a live share of 0.40, against a baseline of 65.0 — 60%
*worse* than the baseline it beat at 0.64. P2 falls smoothly from 75.1 to 50.2
across the same range. A fixed boundary cannot track a moving prior; one read
off the cost matrix moves when the costs move.

**Evidence is worth nothing when one action wins everywhere.** Price the outage
at zero and revoke-now is optimal at every reachable belief — P0 and P2 then
cost *exactly* 46.0. Reading the features changes nothing because nothing they
could say would change the action.

**The probe matters most where the decision is closest.** It is worth 1.0
minutes when an outage costs 60 and 0.08 when it costs 240 — twelve times more
valuable when a cheap outage puts revoke-now and rotate-safely into close
competition. Value of information concentrates at decision boundaries.

**Every error is over-remediation.** Defining regret as what a hindsight-perfect
agent would have saved, P2 gives up 398 minutes of 2018 — 19.7%. The five worst
errors are the *same* error five times: a well-formed key in a real-looking
file, rotated, already revoked, 28 minutes wasted each. Not one case in forty
under-reacts. Full analysis in `error-analysis.md`.

**And none of the magnitudes are stable.** Sampling the whole cost model jointly
— 40,000 draws — the saving runs from 0.5% to 51%, and "escalate is chosen
nowhere" holds in only 70% of them. The claims that survive are about ordering,
not size. Full analysis in `robustness.md`.

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
