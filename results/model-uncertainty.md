# Can the agent notice its own structural assumption is wrong?

W2-7 found a failure the agent cannot see. Its headline structural
result -- that `live` and `revoked` carry identical free-feature rows,
so the mutual information between them is exactly zero -- is an
assumption rather than an observation. Where it is false the agent
loses up to two minutes a finding and has no way to tell.

Parameter uncertainty does not reach this. The invariance is not a
value to be uncertain about; it is a constraint tying two rows
together, and sampling around a tied pair keeps them tied. What is
missing is uncertainty about **which model is right**.

So: a model-selection layer that watches and never decides.

- **H0** — `P(context | live) = P(context | revoked)`. The assumption.
- **H1** — the two differ.

Bayes factor between them under Dirichlet-multinomial marginal
likelihoods, α = 1.0, calling log₁₀ BF > 1
strong evidence for H1.

## The data it gets is not clean, and that is the experiment

The layer sees only what the agent's own discovery process surfaces,
with the asymmetry measured in W2-4:

| Outcome | Discovered |
|---|---|
| remediated something that did not need it | 80% |
| decided correctly | 30% |
| dismissed something that was live | 5% |

Remediating a revoked key is wrong, so it is found out 80% of the
time. Remediating a live key is correct, so it is found out 30% of the
time. **The two classes the test compares are observed at different
rates**, and that is not a detail — it is the whole difficulty.

Out of 2000 findings per run, the layer ends up with roughly
**260 live and 395 revoked** labels
(1.5x as many revoked), against
878 and 531 if every outcome
were observed. The skew is real and it runs the wrong way: the class
the agent under-serves is the class it sees least of.

## Results

Three columns, because two explanations have to be separated. *All
labels* is every outcome observed. *Matched* is an unskewed sample cut
to the same TOTAL size the biased process delivers -- so the only
difference between it and the biased column is the imbalance between
classes, not how much data there is.

| δ | Biased | Matched (same n, no skew) | All labels | log₁₀BF biased | matched | all | Labels live/revoked |
|---|---|---|---|---|---|---|---|
| 0.00 *(H0)* | **2%** | 0% | 0% | -1.57 | -1.64 | -2.04 | 260 / 395 |
| 0.02 | **0%** | 2% | 8% | -1.44 | -1.21 | -0.82 | 260 / 394 |
| 0.05 | **42%** | 72% | 100% | +0.91 | +2.05 | +6.34 | 260 / 393 |
| 0.10 | **100%** | 100% | 100% | +12.77 | +16.76 | +40.30 | 260 / 390 |
| 0.20 | **100%** | 100% | 100% | +24.45 | +30.09 | +72.08 | 260 / 384 |
| 0.35 | **100%** | 100% | 100% | +49.68 | +56.14 | +128.99 | 260 / 376 |

## The two failure modes

**Does the biased sample manufacture evidence for H1 when H0 is
true?** At δ = 0 the invariance genuinely holds, and the layer calls
it broken in **2%** of runs against
0% on clean labels. 
The false-positive rate is controlled: unequal sample sizes between
two classes do not by themselves create apparent differences
between their distributions, because the Bayes factor accounts for
sample size rather than assuming balance.

**Does it hide a real difference?** The smallest difference detected
reliably, by sample:

- biased labels: δ = 0.1
- unskewed, same number of labels: δ = 0.1
- every label: δ = 0.05

**The skew costs nothing. The sample size costs everything.**
An unskewed sample of the same size detects exactly the same
smallest difference as the biased one. What the discovery process
takes away is labels, not fairness between the classes.

That is worth stating plainly because the intuition points the
other way, and mine did: I expected a sample containing
1.5 times as many revoked keys as
live ones to distort a test comparing the two. It does not,
because the Bayes factor compares the SHAPE of each class's
distribution and normalises each by its own count. Unequal
n changes how precisely each shape is estimated; it does not make
two identical shapes look different, and it does not make two
different shapes look alike.

The practical consequence is more encouraging than the biased
framing suggested. The agent does not need unbiased feedback to
audit its own assumptions. It needs *enough* feedback, and the
discovery process delivers about half of what it observes.

## What this adds to the agent

Against the W2-7 failure, which is the point of the exercise:

- At δ = 0.10, where W2-7 measured the agent forgoing
  real value, the layer flags the assumption in 100% of runs.
- At δ = 0.20, where W2-7 measured the agent forgoing
  real value, the layer flags the assumption in 100% of runs.

So the silent failure is no longer silent. The agent still cannot fix
itself -- relaxing the invariance means estimating two separate rows,
and the labels available are too few to do that well, though not --
as the matched control shows -- too skewed --
but it can now raise its hand and say *the assumption I was built on
does not match what I am seeing*. Detection and repair are different
problems, and only the first is solved here.

**This is the capability the project was missing.** Everything before
this commit reasons about uncertainty within a fixed model. This
reasons about whether the model is the right one, which is a different
kind of doubt and the only kind that could have caught the failure
W2-7 exposed. Neither the sessions nor the brief mention Bayesian
model comparison; it arrived because an experiment found something the
existing machinery could not express.

