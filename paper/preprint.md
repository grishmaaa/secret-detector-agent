# Cost-Derived Triage of Secret-Scanner Findings When the Credential Cannot Be Verified

## Abstract

A secret scanner reports that a string in a repository looks like an API key. It
does not say whether the key works. The obvious way to find out — calling the
provider with the key — means authenticating with a credential belonging to
someone else, and we rule it out. **This paper studies triage in the
no-direct-verification setting**: the hidden state is not merely unknown, it is
one we have decided not to resolve by the available means. That is a deliberate
scope restriction rather than a property of the domain, and every result below
is conditional on it.

We model the finding as one of three hidden states (live, revoked, fake), price
five candidate actions in engineer-minutes, and select by minimising expected
cost. No threshold is tuned; the decision boundaries fall out of the cost
matrix. Against an idealised escalate-everything baseline, the cost-derived
policy saves 23.2% of modelled engineer-minutes per finding while escalating
nothing. Every figure here is an expectation under our own cost model and
likelihoods, not a measurement of real triage work.

Three results were not designed in. First, the free evidence available inside a
repository cannot distinguish a live key from a revoked one at all: both states
carry identical likelihoods on every free feature, so their posterior ratio is
invariant at 1.778 regardless of what is observed — which also confines the
agent to a one-dimensional slice of the belief simplex, and every boundary we
report is measured on that slice. Second, escalation *as a way of resolving the
hidden state* is never cost-optimal at any belief the agent can reach: a
perfect oracle is worth at most 15.03 minutes there, so a human must cost less
than that to be worth asking on informational grounds alone. Third, and least
flattering to the method, a policy that observes *nothing at all* and acts on
the prior already captures 21.2 of the 23.2 percentage points. The belief model
is worth 1.75 minutes per finding and changes the chosen action on 14.55% of
findings; the cost structure does the rest.

We also report a case where practitioner feedback changed a result: our probe
was priced at ten minutes by guesswork, and a practitioner who uses it offered a
materially different estimate of roughly one minute. Adopting that estimate moved
the investigate action from never selected to selected on 3.98% of findings. We
treat this as sensitivity evidence — one plausible alternative value — rather
than as a measurement of the true cost.

---

## 1 Introduction

Secret scanners are widely deployed and reasonably good at what they do. What
they produce is a finding: *this string, in this file, looks like a credential of
this type*. What they do not produce is the thing a responder actually needs,
which is whether the credential still works.

The gap matters because the actions available differ enormously in cost. Doing
nothing about a live key risks whatever sits behind it. Revoking a key
immediately is cheap and certain, and breaks anything still using it. Rotating
safely avoids the outage and costs a deploy cycle. Handing the finding to a
person is reliable and spends the scarcest resource in the organisation. The
right choice depends on a hidden state, and the standard method for resolving
that state — issuing a request with the found credential — is not one we are
willing to use against a third party's account.

That constraint is the origin of the problem we study. It is our choice, not a
consensus position: three practitioners told us, unprompted, to simply try the
key. We keep it, and we treat it as the paper's most load-bearing assumption.

**Contributions.**

1. A decision-theoretic formulation of secret-scanner triage in which the
   decision boundaries are *derived* from a cost matrix rather than tuned. On
   the slice of the simplex the agent can actually occupy, the derived boundary
   sits at P(live) = 0.066 rather than near the 0.5 an engineer would pick by
   instinct.
2. A structural result: the two free features we model cannot separate live from
   revoked keys, because both states carry identical likelihoods on each of
   them. Given conditional independence this is arithmetic rather than an
   empirical claim — and it is a property of the features chosen, not of
   repository evidence in general.
3. A parametric bound on escalation: a perfect oracle is worth at most 15.03
   minutes at any reachable belief, so escalation cannot be justified on
   information-gathering grounds whenever human triage overhead exceeds that.
   This bounds a human acting as a state oracle; it says nothing about a human
   who supplies authority, ownership or organisational context, none of which
   any VPI calculation can bound.
4. A closed-world comparison showing that most of the improvement over the
   escalate-everything baseline comes from the cost structure rather than from
   the belief model, and that hand-picked thresholds, while not catastrophic
   once given the full action set, respond non-monotonically to a prior we
   cannot pin down.
5. A documented instance of practitioner feedback correcting a model parameter
   by an order of magnitude and thereby changing which actions the agent takes.

## 2 Related Work

**Detector precision is not a constant.** A nine-tool comparison [Basak et al.,
2023] reports precision of about 75% for GitHub's scanner, 46% for Gitleaks, and
below 7% for five of the nine, attributing the spread to over-broad regular
expressions and entropy scoring. The practical consequence for any work in this
area is that there is no such thing as *the* base rate of true positives; it is
a property of which detector fired. We assume GitHub's scanner throughout and
note that assuming one of the weaker detectors would change the problem from
"what should be done about this key" to "is this junk".

**Credential lifetime.** GitGuardian's 2026 report finds that roughly 64% of
credentials valid in 2022 were still valid in January 2026. This is a vendor
figure and we treat it as a hypothesis rather than a measurement, but it points
the opposite way to intuition: the age of a commit is weak evidence that a key
is dead.

**Classification of secrets with language models.** Recent work [Islam et al.,
2025] reports GPT-4o at 93.29% precision few-shot and a fine-tuned LLaMA-3.1-8B
at 0.985 F1 for deciding whether a string *is* a secret. This is the obvious
alternative technology and it answers a different question: it improves
detection, and says nothing about whether a detected credential is still live,
which is the axis our decision turns on.

**Revocation is solved for a different credential format.** A practitioner
observed during our discussion phase that a certificate carries a CRL
distribution point — a pointer to its own revocation list — so live-versus-revoked
is answered by the credential itself. Public-key infrastructure solved decades
ago the exact problem that motivates this paper. An API key has no equivalent:
no revocation list, no status field, nothing in the string. **Our central
difficulty is a property of API keys specifically, not of leaked credentials in
general**, and we consider this the clearest justification available for the
scope we chose.

## 3 Problem Formulation

### 3.1 Input and hidden state

The agent observes one scanner finding: a string in a repository that matches a
known key format. The hidden state $s$ is one of

- **live** — the credential still authenticates;
- **revoked** — it authenticated once and no longer does;
- **fake** — it was hard-coded by a developer and never authenticated.

We scope to a single provider, OpenAI, and to project keys. This choice
collapses a fourth state that exists for other providers: Stripe issues
distinguishable test keys, OpenAI does not. The trade was deliberate — we gave
up a hidden state to gain a probe whose response shape is documented and
quotable.

Only the first state carries the exposure risk we price. The other two do not,
though "harmless" would be too strong: a revoked key still has audit
implications and may have been reused elsewhere. They differ from each other
only in why they are inert.

### 3.2 Actions

Five actions, of which we will argue only three are terminal:

| Action | What it does |
|---|---|
| Dismiss | Nothing. The finding is closed. |
| Investigate | Buy evidence, then decide again. |
| Escalate | Hand the decision to a human. |
| Revoke now | Kill the key immediately; accept the outage. |
| Rotate safely | Issue a replacement, migrate consumers, verify, then revoke. |

Revoke-now and rotate-safely are kept separate because leaving a system broken
in order to be safe is not automatically correct, and a model that cannot
express the difference cannot inform the choice. This separation is justified a
second time in Section 5.2, from an argument we did not anticipate.

### 3.3 Baseline and objective

Our baseline is an **idealised escalate-everything policy**: every finding goes
to a person, and that person resolves it correctly. We do not claim this is what
teams do today — real pipelines allowlist known fixtures, auto-dismiss, and route
by pattern before any human sees an alert, and we have no citation for the
prevalence of any particular procedure. It is a deliberately favourable
comparator, chosen because it makes the argument of this section clean: **the
baseline is never wrong about the hidden state.** There is therefore no accuracy
for an automated method to win, and reporting an accuracy figure would be close
to meaningless. The only remaining axis is cost. A baseline with a fallible human
and a realistic escalation rate would be a harder and more informative
comparison, and we do not attempt it.

> **Objective.** Does a probabilistic, cost-aware policy reach the same
> decisions as escalate-everything while spending fewer human interruptions —
> and under what conditions does it stop doing so?

The second clause carries most of the weight. A policy that wins under every
assumption we could vary would be evidence that the comparison was built badly.

## 4 Model

### 4.1 Prior

We **construct** a traceable prior from two external estimates rather than
estimating one from representative data. GitHub's scanner reports about 75%
precision, so roughly three-quarters of findings are real credentials. Of those,
about 64% are still valid. This gives

$$P(\text{live}) = 0.75 \times 0.64 = 0.48,\quad
  P(\text{revoked}) = 0.75 \times 0.36 = 0.27,\quad
  P(\text{fake}) = 0.25.$$

Its virtue is not accuracy but traceability: each factor points at a source that
can be disputed. Two caveats belong here rather than in the limitations. The 64%
describes credentials known valid in 2022 and still valid in 2026, which is not
the same population as findings a scanner reports today; and detector precision
counts strings that are not credentials at all, whereas our *fake* state is
defined as a real-format string that never authenticated. We merge those two
populations into one state and its likelihood row is a guess for both.

### 4.2 Evidence

Two features are free — readable from the repository at no cost — and one must
be purchased.

**Placeholder context** (placeholder / neutral / production), from the file
path, the variable name, and the commit message.

**Well-formedness** (well-formed / malformed), whether the string matches the
provider's published format.

**`last_used_at`** (recent / old / null), a timestamp obtained by asking our own
account about the key through the provider's admin API. This is the only
evidence that reaches outside the repository, and it never involves
authenticating *as* the suspect key.

**Conditional independence.** We assume the features are conditionally
independent given the hidden state, so that
$P(c, f, r \mid s) = P(c \mid s)\,P(f \mid s)\,P(r \mid s)$. This is what
licenses the multiplication in every posterior below, and it is what makes
Section 4.3's result follow from the rows of the table rather than from a joint
distribution we never specify. It is an assumption of convenience and it is
plainly imperfect: a string that reads as a placeholder from its path and
variable name is more likely to be malformed than the product suggests. We flag
it here because Section 4.3's structural claim depends on it.

$P(e \mid s)$:

| Feature | live | revoked | fake |
|---|---|---|---|
| Context: placeholder / neutral / production | .10 / .30 / .60 | .10 / .30 / .60 | .70 / .25 / .05 |
| Form: well-formed / malformed | .99 / .01 | .99 / .01 | .40 / .60 |
| `last_used_at`: recent / old / null | .60 / .20 / .20 | .02 / .78 / .20 | .01 / .04 / .95 |

### 4.3 A structural consequence

Note the first two rows. **Live and revoked carry identical likelihoods on both
free features.** This is not a modelling convenience; it reflects that nothing
visible inside a repository distinguishes a key that works from one that was
turned off. Identical rows cancel in the update, so the posterior ratio is
invariant:

$$\frac{P(\text{live} \mid e_{\text{free}})}{P(\text{revoked} \mid e_{\text{free}})}
= \frac{0.48}{0.27} = 1.778 \quad \text{for every } e_{\text{free}}.$$

On our worked case the posterior is 0.6329 / 0.3560 / 0.0111, and 0.6329 /
0.3560 = 1.778 to four decimal places. The free evidence does one job
excellently — it collapses *fake* from 0.25 to 0.011 — and the other not at all.

**Neither of these two features can move the ratio that matters**, at any value,
in any combination. That is the result the rest of the paper turns on, and it is
visible only because we kept live and revoked as separate states where most
treatments collapse them into "true positive".

We state it narrowly on purpose. This is a property of the two static text
features we chose, not of repository evidence in general. Section 9 names two we
did not model — repository visibility and commit semantics — that would
plausibly separate the two states, and the claim is safest read as applying to
findings in private repositories where neither is informative.

### 4.4 Costs

Fifteen cells built from nine components, in engineer-minutes, so that a
practitioner can dispute a component rather than a cell.

Components: revoke 2 · issue a new key 10 · run the probe 3 · human attention 30
· find the consumers 30 (documented) or 480 (undocumented) · deploy 60 · verify
10 · production outage 240.

| | live | revoked | fake |
|---|---|---|---|
| Dismiss | **2400** | 2 | 2 |
| Investigate | 3 | 3 | 3 |
| Escalate | 142 | 32 | 32 |
| Revoke now | 332 | 2 | 5 |
| Rotate safely | **112** | 30 | 20 |

The live column is component sums, exactly: rotate-safely is
$10 + 30 + 60 + 10 + 2 = 112$; revoke-now is the same hunt and the same deploy
plus the outage, $2 + 240 + 30 + 60 = 332$. Escalate is defined throughout as
$30 + \min_a c(a, s)$ — human attention plus whatever that human then correctly
does — giving 142 / 32 / 32. An earlier draft rounded these to 120, 330 and
150/30/30 and the rounded values then disagreed with the component arithmetic
elsewhere in the paper; the sums are now used everywhere.

Three cells are direct estimates with no component decomposition: rotating a
revoked key (30) or a fake one (20), and revoking a fake one (5). The
rotate-on-fake figure is the cost of beginning a rotation and discovering there
is nothing to rotate, and it matches the only practitioner estimate we have for
that case ("never a real key? Minutes"). It is load-bearing: Section 7.6 shows
that setting it to zero makes the belief model worth exactly nothing.

The cost of dismissing a live key is itself a product — the chance someone finds
and uses the key, times the damage if they do — and both factors vary with facts
we do not observe. It is therefore the first quantity we sweep.

### 4.5 Investigate is not a terminal action

The investigate row is not the same kind of number as the other four. The others
are what an action *costs*; this one is an entry fee. Investigate does not close
the case — it buys an answer and returns the decision to the agent. Placing 3
into the minimisation alongside the rest would make it win at every belief, and
the agent would probe forever without acting.

We therefore minimise over the four **terminal** actions, and compare investigate
separately by whether the expected value of the information it buys exceeds its
price. The general rule: *a sequence of steps may be collapsed into a single
action when no observation inside the sequence changes what is done next.*
Rotate-safely observes but does not branch, so it collapses. Investigate exists
only to branch, so it cannot.

## 5 Policy

### 5.1 Selection

$$a^\star = \arg\min_{a \in \mathcal{A}_{\text{terminal}}}
\sum_{s} P(s \mid e)\, c(a, s)$$

No threshold appears in this expression. Thresholds are a consequence of it.

### 5.2 The derived regimes

With three states, $P(\text{live})$ alone does not determine the cheapest
action — the split of the remaining mass between revoked and fake matters too.
A boundary is therefore only meaningful relative to a path through the simplex,
and Section 4.3 tells us which path: the free features lock
$P(\text{live}) : P(\text{revoked})$ at 1.778, so the agent walks one line and
never leaves it. All boundaries below are measured on that line.

| $P(\text{live})$ | Cheapest action |
|---|---|
| below 0.00145 | Dismiss |
| 0.00145 – 0.06588 | Revoke now |
| above 0.06588 | Rotate safely |

Two observations. **The boundary is at 0.066, not 0.5.** An engineer building
this by instinct places the line at "more likely than not" and dismisses
findings this model rotates; Section 7 measures what that costs.

And **revoke-now owns an entire regime on its own**. We introduced it because
outages are not automatically acceptable; the arithmetic justifies it from a
completely different direction, and a model with a single remediation action
would never have exposed that region.

### 5.3 A bound on escalation

Rather than test escalation at particular beliefs, we bound it. At each belief
we compute the value of perfect information — the cost saved by an oracle that
reveals the true state. This is an upper bound on what a human who *only
resolves the hidden state* could be worth, however skilled.

Over the whole simplex the maximum is 24.78 minutes, but that maximiser lies at
$b \approx (0.12, 0.88, 0.00)$, which the agent cannot reach. Over the six
beliefs it can hold:

$$\max_{b \in \mathcal{B}_{\text{reachable}}} \mathrm{VPI}(b) = 15.03
\text{ minutes}$$

So escalation is dominated whenever a human costs more than 15.03 minutes. At
our assumed 30 it loses comfortably; at the 10–15 minutes a dedicated triage
analyst might cost, it does not, and the conclusion reverses. **This is a
parametric result, not a structural one**, and it bounds only the informational
value of a human. A person who supplies authority to act on another team's
credential, or organisational context the model has no representation for, is
not bounded by any VPI calculation.

### 5.4 Uncertainty is not the trigger

It is natural to escalate when confused. We tested the most confused belief
available, $(1/3, 1/3, 1/3)$ at 1.585 bits, the maximum entropy on three states.
Rotate-safely costs 54.00; escalate costs 68.67.

**Entropy measures confusion. It does not measure whether the confusion is
expensive.** Two roads at a fork are maximally uncertain and the choice does not
matter; a fire alarm that is probably faulty is barely uncertain and urgently
needs a person. Entropy retains a role — counting the bits a probe removes — but
the escalation trigger is the cost of being wrong.

### 5.5 When to buy the probe

Because there are three context values and two form values, the agent can reach
exactly **six** posterior beliefs after free evidence. This is small enough to
enumerate rather than sample, so the value of the probe is computed exactly at
every belief the agent can hold.

| Context | Form | $P(\text{seen})$ | $P(\text{live})$ | Act now | EVSI | VPI |
|---|---|---|---|---|---|---|
| placeholder | well-formed | .1442 | .3294 | rotate | 0.00 | 13.92 |
| placeholder | malformed | .1057 | .0045 | revoke | 1.40 | 3.98 |
| neutral | well-formed | .2477 | .5754 | rotate | 0.00 | 10.88 |
| neutral | malformed | .0398 | .0362 | revoke | **5.21** | 10.80 |
| production | well-formed | .4505 | .6329 | rotate | 0.00 | 10.17 |
| production | malformed | .0120 | .2400 | rotate | 0.00 | **15.03** |

At the four beliefs where rotate-safely is already optimal, every probe outcome
leaves it optimal, so the information is worth exactly nothing. Value
concentrates at the two beliefs sitting near a boundary.

**The price of the probe determines whether investigate exists.** We initially
priced it at ten minutes by guesswork, under which it is never bought. During
the discussion phase a practitioner described this exact probe, unprompted, as
the first thing they do, and priced it at about one minute; a second warned
against concluding anything from a single response, having worked with a source
that answers half of its identical requests differently. One minute per call,
three calls, gives three minutes.

Because EVSI takes only **two** non-zero values across the reachable set —
1.4012 and 5.2118 — the probe's price does not tune behaviour continuously. It
selects one of exactly three regimes:

| Probe price | Bought at | Share of findings | P3 gain over P2 |
|---|---|---|---|
| below 1.40 | both malformed buckets | 14.55% | up to 0.30 min |
| **1.40 – 5.21** | neutral / malformed only | **3.98%** | 0.01 – 0.15 min |
| above 5.21 | nowhere | 0.00% | 0.00 |

Evaluated at specific prices:

| Price | 0.5 | 1 | 1.5 | 2 | **3** | 5 | 10 |
|---|---|---|---|---|---|---|---|
| Findings probed | 14.55% | 14.55% | 3.98% | 3.98% | **3.98%** | 3.98% | 0% |
| Saving, min/finding | 0.283 | 0.210 | 0.148 | 0.128 | **0.088** | 0.008 | 0.000 |

Two things follow. **Investigation becomes rational at 5.21 minutes** — that is
the price below which some belief justifies buying evidence, and it is a
property of the cost matrix rather than of the probe. Our earlier estimate of
ten minutes sat above it, which is why the action appeared dead.

And **it never becomes important.** Even at half a minute — a probe that is
effectively free — the aggregate saving is 0.283 minutes per finding, four
tenths of one percent of P2's cost. The correction moved investigate from never
selected to selected on one finding in twenty-five, a behaviour we did not
design; it did not move the total. Information here is sometimes worth buying
and never worth much, and those are separate facts.

## 6 Simulation Study

Five policies on identical findings:

| | Policy |
|---|---|
| baseline | Escalate every finding |
| P0 | Act on the prior; observe nothing |
| P1 | Free evidence, then hand-picked thresholds (dismiss below 0.05, revoke below 0.5, else rotate) over all four terminal actions |
| P1-trunc | Free evidence, then rotate if $P(\text{live}) > 0.5$, else dismiss |
| P2 | Free evidence, then minimise expected cost |
| P3 | P2, plus buy the probe when EVSI exceeds its price |

P1 is the comparison that matters: hand-picked thresholds, but otherwise the
same information and the same actions available to P2, so the comparison
isolates *where the boundaries came from* and nothing else. P1-trunc is an
earlier version of that comparison which also restricted the action set to two;
we report it because it produces a dramatic result for the wrong reason, and
Section 7.3 separates the two effects. P0 is the control we nearly omitted and
which turned out to be the most informative row.

Two numbers are reported for each policy. **Expected cost** is computed in
closed form over all 54 possible worlds (3 states × 3 contexts × 2 forms × 3
probe outcomes) and carries no sampling error. **Realised cost** is measured on
40 cases drawn once with a fixed seed and frozen thereafter. Forty is few enough
that a single dismissed live key moves the total by more than half, and we
report both rather than allow either to stand alone.

### 6.1 Why the study is a simulation rather than an experiment

The obvious alternative is SecretBench [Basak et al., 2023b], a labelled corpus
of 97,479 candidate secrets drawn from public repositories, 15,084 of them
confirmed real. We list it in related work and do not use it, and the reason is
specific rather than convenient.

**SecretBench labels whether a string is a secret. It does not label whether
that secret still works.** Its fields include `label` (true or false),
`is_template`, `entropy`, `character_set`, `length` and `file_path` — enough to
ground our *fake* state, the 0.25 of prior mass assigned to it, and both free
feature rows, since `is_template` is close to our placeholder context and the
entropy and character-set fields are what our well-formedness feature encodes.
There is no field for live versus revoked.

That is the axis this paper turns on. Fitting the free features to real data
would sharpen the half of the model that already works — the collapse of *fake*
from 0.25 to 0.011 — and leave the half that matters exactly where it is. It
would improve the numbers we are least worried about.

We therefore record the gap as evidence rather than as an obstacle. **The
largest public corpus of real leaked credentials does not record whether they
still authenticate**, and the reason is the one that motivates this paper:
establishing it would mean testing each key against its provider. The label is
missing from the dataset for precisely the reason the state is hidden from our
agent, which is the strongest external support we have for the problem being
real. Access is also non-trivial — the corpus is released under a signed data
protection agreement and hosted on Google Cloud — but that is a scheduling cost
and not the reason.

Grounding the free-feature likelihoods against SecretBench remains the single
most valuable extension we can name. It would raise the credibility of the prior
and of Section 4.3's *fake* collapse. It cannot validate the live/revoked
invariance, and no public dataset we are aware of can.

## 7 Simulation Results

### 7.1 Main comparison

| | Policy | Expected cost | vs baseline | Escalates | Probes | Differs from P0 |
|---|---|---|---|---|---|---|
| baseline | escalate everything | 84.80 | — | 100% | 0% | — |
| P0 | prior only | 66.86 | −21.2% | 0% | 0% | — |
| P1 | hand-picked, 4 actions | 77.79 | −8.3% | 0% | 0% | 14.55% |
| P1-trunc | hand-picked, 2 actions | 181.78 | **+114.4%** | 0% | 0% | 14.55% |
| P2 | cost-derived | 65.11 | **−23.2%** | 0% | 0% | **14.55%** |
| P3 | P2 + probe | 65.03 | −23.3% | 0% | 4.0% | 10.57% |

The last column is the share of findings on which the policy chooses a different
action from P0's constant "rotate safely". It is the honest measure of how much
the belief model does.

On the 40 frozen cases: baseline 2820 minutes, P2 2018, a 28.4% saving. That
draw contains 14 live keys out of 40, a live share of 0.35 against a prior of
0.48 — 1.6 standard deviations low — so the sampled figure is not
interchangeable with the exact one.

### 7.2 The cost structure does the work, not the evidence

P0 observes nothing whatsoever. It knows the base rates, concludes that
rotate-safely is cheapest in expectation, and applies it to every finding. It
beats the baseline by 21.2%.

The full belief model reaches 23.2%. **The evidence is worth 1.75 minutes per
finding, and the remaining 21 points come from a single decision: stop asking a
human.** The belief model does change the action on 14.55% of findings — it is
not inert — but the action it changes to is cheap enough that the aggregate
difference is small.

We report this as the paper's least flattering result and its most important
one. The mechanism is that rotate-safely costs 120 / 30 / 20 — it is nearly
state-blind, and tolerable whichever state obtains. When a hedge that good is
available, identifying the state buys very little. This is the same principle as
the EVSI result, one level up: information is worth what it changes.

### 7.3 What hand-picked thresholds actually cost

An earlier version of this comparison reported that the naive 0.5 threshold
costs more than twice the baseline, and treated that as the paper's strongest
argument for deriving boundaries. **That comparison was confounded**, and we
report the correction rather than the original claim.

P1-trunc changes two things at once: it moves the boundary to 0.5 *and* it
restricts the action set to {rotate, dismiss}, withholding revoke-now — which
Section 5.2 shows owns a regime of its own. Holding the threshold fixed at 0.5
and varying only the fallback separates the two effects:

| Threshold 0.5, fallback | Expected cost | vs baseline |
|---|---|---|
| dismiss | 181.78 | +114.4% |
| escalate | 71.13 | −16.1% |
| revoke now | 74.25 | −12.4% |
| rotate safely | 66.86 | −21.2% |

**The catastrophe is caused by dismissing, not by thresholding.** The same 0.5
boundary with a safe fallback beats the baseline. Given the full four actions
and a second hand-picked cut at 0.05, P1 costs 77.79 — 8.3% better than the
baseline, and 19.5% worse than P2. That is the honest size of the effect.

What does survive is a difference in how the two policies respond to a prior we
cannot pin down:

| live share | baseline | P0 | P1 | P2 |
|---|---|---|---|---|
| 0.40 | 65.0 | 52.1 | **103.8** | 50.2 |
| 0.50 | 73.2 | 58.3 | **129.2** | 56.4 |
| 0.64 | 84.8 | 66.9 | 77.8 | 65.1 |
| 0.70 | 89.8 | 70.5 | 83.1 | 68.8 |
| 0.80 | 98.0 | 76.7 | 91.9 | 75.1 |

P1 is **non-monotonic**: it gets more expensive as the world gets safer, and at
a live share of 0.40 it costs 60% *more* than the baseline it beat at 0.64.
P2 falls smoothly from 75.1 to 50.2 across the same range. So a hand-picked
threshold is not catastrophic, but its sign relative to the baseline depends on
a quantity we do not know — **a fixed boundary cannot track a moving prior,
whereas one read off the cost matrix moves when the costs move.** That is a
weaker claim than the paper originally made and it is the one the numbers
support.

### 7.4 Evidence is worthless when one action wins everywhere

Priced at zero outage, revoke-now is optimal at every belief the agent can
reach, and P0 and P2 then cost *exactly* 46.0 — identical to two decimal places.
Reading the features changes nothing, because nothing they could say would
change the action. (Revoke-now is not cheaper than every alternative in every
*state* — dismiss is cheaper on fake — but it wins at every reachable belief,
which is what matters.)

### 7.5 Information concentrates at decision boundaries

In the same sweep, the probe is worth 1.0 minutes when an outage costs 60 and
0.08 minutes when it costs 240. A cheap outage puts revoke-now and rotate-safely
into close competition, which creates the boundary region where knowing one more
thing changes the answer.

The converse also holds and refutes an extension we tested. Probing *which
systems consume the credential* — apparently attractive, since the
documented/undocumented split is the largest uncertainty in the cost model — has
no value for choosing between the remediation actions. The consumer hunt appears
identically in both: $c(\text{rotate}, \text{live}) = 82 + F$ and
$c(\text{revoke}, \text{live}) = 302 + F$, so their difference is 220 for every
$F$, and the boundary sits at 0.06588 for $F \in \{30, 60, 120, 240, 480\}$ —
the same value Section 5.2 reports, because it is the same line.
**Information that changes what you pay, but not the ordering of what you might
do, is worth nothing.**

The same invariance disposes of a related worry. Scaling the cost of dismissing
a live key from 2 400 to 120 000 minutes leaves the revoke/rotate boundary at
0.06588 throughout, because that component appears in neither action; only the
dismiss boundary moves, from 0.00145 to 0.00003, and no reachable belief is near
it.

### 7.6 The belief model's value lives in one cost cell

Rotating a *fake* key is priced at 20 minutes — the cost of starting a rotation
and discovering there is nothing to rotate. Varying it:

| $c(\text{rotate}, \text{fake})$ | P0 | P2 | P2 differs from P0 on |
|---|---|---|---|
| 0 | 61.86 | 61.86 | 0.00% |
| 10 | 64.36 | 63.86 | 14.55% |
| 20 | 66.86 | 65.11 | 14.55% |
| 60 | 76.86 | 68.79 | 14.55% |
| 120 | 84.80 | 70.62 | 15.83% |

At zero the two policies are **identical**, and the belief model is worth
nothing at all. Every result in Section 7.2 therefore rests on a single
estimated cell, and we would rather state that than let the 1.75-minute figure
stand unqualified.

### 7.7 Where the policy loses, and what it never does

Defining an incorrect decision as one a hindsight-perfect agent would have made
differently, and its size as the regret
$c(a, s) - \min_{a'} c(a', s)$, P2 pays 2 018 minutes on the forty frozen cases
against a hindsight-optimal 1 620. **Total regret 398 minutes, 19.7%** — the
price of not knowing the state.

The five costliest errors turn out to be the *same* error five times: a
well-formed key in a real-looking file, rotated, and already revoked. 28 minutes
of wasted remediation each. The agent has no idiosyncratic failures on this
sample, only one systematic bias applied consistently — and the bias is the
invariant ratio of Section 4.3 arriving as a bill. Those five decisions were
correct given the information and wrong given the world.

| Chose | On a key that was | Cases | Regret |
|---|---|---|---|
| rotate safely | revoked | 11 | 308 |
| rotate safely | fake | 3 | 54 |
| revoke now | fake | 12 | 36 |
| *(correct)* | — | 14 | 0 |

**Every error is over-remediation. Not one case in forty under-reacts.** The two
expensive errors available — dismissing a live key (regret 2 288) and revoking
one (220) — did not occur. The first cannot: P2 never dismisses at a reachable
belief. The second can, and roughly two were expected on this draw; zero
occurred, which is a sampling accident rather than a property.

This profile is the cost matrix behaving as designed. A 100:1 ratio between
dismissing a live key and rotating an inert one buys exactly this: 398 minutes
of unnecessary work to never risk the expensive mistake. Full analysis in
`results/error-analysis.md`.

### 7.8 Joint sensitivity: what survives when the model is wrong at once

Every sweep above varies one component and holds twelve fixed, which flatters
the model. We therefore sampled the whole specification jointly — 40 000 draws,
each quantity from a two-piece lognormal whose most-likely value is the median
and whose stated low and high are the 5th and 95th percentiles — and ran it
twice: once with the evidence model fixed, and once with every likelihood row
also perturbed (Dirichlet, α = 40), the live and revoked rows independently, so
that the identical-rows property behind Section 4.3 is deliberately broken.

| Claim | costs uncertain | costs *and* evidence uncertain |
|---|---|---|
| P2 costs less than escalate-everything | **98.02%** | **98.64%** |
| Revoke/rotate boundary below 0.5 | **93.26%** | **93.24%** |
| Belief model worth under 5 min per finding | **91.34%** | 88.13% |
| P0 also costs less than the baseline | 79.20% | 79.20% |
| **Escalate is chosen nowhere** | **70.29%** | 69.75% |
| The probe is bought somewhere | 59.29% | 57.98% |

These are shares of sampled draws, not confidence levels, and components are
drawn independently — an assumption that is certainly false, since a deployment
that is hard to run is probably also hard to verify.

**Perturbing the evidence model breaks the invariance and changes almost
nothing.** The live-to-revoked log-ratio drift across buckets rises from exactly
0.000 to a median of 2.53 — a factor of roughly twelve, meaning the free
features do separate the two states in most of those worlds — and no conclusion
moves by more than 3.2 percentage points. Section 4.3's invariance is an
idealisation, and the conclusions that appear to rest on it do not need it:
rotate-safely stays cheap in every state either way.

**Escalation, tested rather than observed.** Holding every other component at
its point estimate and varying only the cost of human attention:

| Human attention | Findings escalated |
|---|---|
| ≤ 3 min | **100.00%** |
| 5 – 10 min | 89.42% |
| 12 min | 15.62% |
| 15 min | 1.20% |
| ≥ 20 min | **0.00%** |

Escalation goes from every finding to none across a twenty-minute range, with
the crossover between 12 and 20 minutes. **Section 5.3's result is a
consequence of pricing human attention at 30 minutes**, not of the structure of
the problem, and we withdraw any reading of it as structural.

| Quantity | 5th | Median | 95th | Point estimate |
|---|---|---|---|---|
| P2 saving vs baseline | 0.53% | 19.23% | 51.27% | 23.2% |
| Value of the belief model (min) | 0.00 | 0.87 | 6.31 | 1.75 |
| Revoke/rotate boundary | −0.136 | 0.059 | 0.600 | 0.0659 |
| Max VPI, reachable beliefs | 1.37 | 12.12 | 32.12 | 15.03 |

Every point estimate sits near its median, so our cost model is not an outlier
among plausible ones; the intervals are nonetheless very wide. **The claims
worth keeping are about ordering rather than magnitude** — the boundary is far
below 0.5, the belief model is worth little, and cost-derived selection beats
escalate-everything. "23.2%", "1.75 minutes" and "never escalates" do not
survive as stated. Full analysis in `results/robustness.md`.

## 8 Discussion

Three of this paper's results are negative, and we think that is the point. The
free evidence cannot separate the states that matter; escalation is never
optimal; the probe is usually not worth buying. Each was established by
computation rather than assertion, and each was contrary to the authors'
expectation before it was computed.

The methodological observation we would defend is narrower than the one an
earlier draft made. Deriving a boundary rather than choosing it does not make
the policy dramatically cheaper — Section 7.3 shows a hand-picked threshold with
a sensible fallback beats the baseline too. What it changes is **what an
objection looks like**. A tuned threshold can only be defended by authority; a
derived one can only be attacked through a cost, which is a claim a practitioner
can correct. One did, by an order of magnitude, and the correction changed which
actions the agent takes. And a derived boundary moves when the world moves,
which is why P2 responds monotonically to the prior where P1 does not.

The result we would most like to see contradicted is Section 7.2. If the belief
model is worth 1.75 minutes, then most of what makes this agent useful is the
decision to stop escalating, which requires no probabilistic machinery at all.
That would be a real finding about the domain rather than a failure of the
method. But Section 7.6 shows it rests on a single estimated cell — the cost of
rotating a fake key — and at zero that cell makes the belief model worth
precisely nothing. The finding and its weakest input are the same input.

## 9 Limitations

Given in full in the accompanying limitations document; the load-bearing ones:

**The refusal to test the key is ours alone.** Three practitioners advised
simply calling the provider with the found credential. Every downstream result
— the invariant ratio, the probe, the whole value-of-information analysis —
exists because of a choice the field does not share.

**Eight of nine cost components are our estimates.** The ninth was corrected by
practitioners and changed a result, which is the best available evidence that
the other eight are also wrong in unknown directions.

**The case generator draws from the agent's own likelihood tables**, so the
agent is evaluated in a world that agrees with its assumptions. This flatters
every policy that uses evidence.

**Actions are atomic; the world is sequential.** Rotate-safely is really six
steps with evidence arriving partway through, and a sequential formulation would
find value for investigation that this model cannot see.

**Escalation may be a permission boundary rather than a priced option.** Our
sweep shows escalation never wins *on cost*. It does not show escalation is
unnecessary: an agent may lack the authority to revoke another team's
credential, which is a constraint on the action space and not a candidate
inside it.

**A fourth state is known and unmodelled.** A credential that authenticates
successfully but is authorised for nothing — a 403 rather than a 401 — is live
by our definition yet carries none of the risk that makes dismissing a live key
cost 2400.

**No live call was made.** No admin credential was held, and the repository
contains no credential material; every string in it is a synthetic feature
descriptor.

**Conditional independence is assumed and unstated in the model.** The posterior
multiplies the feature likelihoods, so Section 4.3's invariance follows from
identical *marginals* plus independence. Identical marginals alone would not
give identical joints. We believe the joint claim — a repository does not reveal
whether a key still authenticates — but it is a claim, not a derivation.

**The free feature set is not the whole repository.** Two features we did not
model would plausibly separate live from revoked: repository visibility (OpenAI
is a partner in GitHub's programme, so leaks in public repositories are reported
to the provider and may be revoked without us) and commit semantics (a deletion
commit reading "remove leaked key" is strong evidence of revocation). **Section
4.3's invariance is a property of the two static text features we chose, not of
repository evidence in general**, and it is safest read as a private-repository
claim.

**The probe requires a privileged credential.** Reading `last_used_at` means the
scanning pipeline holds an organisation-wide admin key in order to triage a
single project key. That is a high-severity credential introduced to resolve a
low-severity finding, and the model prices the probe's minutes without pricing
that asymmetry.

**Boundaries are slice-dependent, and an earlier draft reported them from the
wrong slice.** With three states a boundary is defined relative to a path
through the simplex. The free features confine the agent to one line; figures
computed on the prior-ratio slice (0.09386 for the revoke/rotate boundary, 24.64
minutes for the VPI bound) describe beliefs the agent cannot hold. The
corresponding reachable figures are 0.06588 and 15.03.

## 10 Conclusion

We formulated secret-scanner triage as a decision under uncertainty in which the
hidden state cannot be observed without doing something we are unwilling to do,
and showed that the decision is nonetheless tractable because the *costs* are
knowable even when the state is not.

The policy saves 23.2% of modelled engineer-minutes against escalate-everything
while never escalating. But the honest headline is smaller and more interesting:
a policy observing nothing at all captures 21.2 of those points. In this domain, a
safe action that is cheap in every state does most of the work that a belief
model appears to be doing — and the contribution of decision theory here is less
the posterior than the discipline of pricing the actions before choosing between
them.

## References

[Basak et al., 2023] *A Comparative Study of Software Secrets Reporting by
Secret Detection Tools*. arXiv:2307.00714.

[Basak et al., 2023b] *SecretBench: A Dataset of Software Secrets*.
arXiv:2303.06729.

[Islam et al., 2025] *Secret Breach Detection in Source Code with Large Language
Models*. arXiv:2504.18784.

[GitGuardian, 2026] *The State of Secrets Sprawl 2026*. Vendor report.

[GitHub, 2026] *Supported secret scanning patterns*. GitHub Documentation.

[OpenAI, 2026] *Administration API — project API keys*. OpenAI Documentation.

*Author names on the arXiv entries need checking against the papers before
submission; the identifiers are correct and were used throughout.*
