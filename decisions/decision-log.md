# Decision Log

Every choice that shaped this project, in the order I made it, with what else I
could have done and what the choice turned out to cost or buy. I wrote this
partly so I can explain the project commit by commit, and partly because
several of these decisions only revealed what they were worth much later.

The pattern I noticed while assembling it: **most of my useful results came from
decisions that closed something off, not from decisions that added something.**

---

## Commit 1 — Frame the problem

### 1.1 What job the agent does

| | |
|---|---|
| **Options** | Detect secrets in a repository · Verify whether a found secret works · Triage a finding a scanner has already produced |
| **Chose** | Triage |
| **Why** | Detection is solved — scanners exist and I would be rebuilding one. Verification means authenticating with a credential I found, which I had already decided not to do. What is left is the part nobody has automated: deciding what to do about a finding when you cannot check it. |
| **Cost** | I inherit the scanner's precision as a fixed input rather than something I can improve. |
| **What it bought** | The problem became a decision under uncertainty rather than a classification task, which is what made everything after it possible. |

### 1.2 Never authenticate with a credential I found

| | |
|---|---|
| **Options** | Call the provider with the key and see if it works · Refuse, and find evidence some other way |
| **Chose** | Refuse |
| **Why** | It is somebody else's account. Testing a key I found in a repository means using a credential I have no right to use, and I decided that before I knew what it would cost me. |
| **Cost** | Large. It removes the cheapest, most decisive evidence available, and it is the direct reason live-versus-revoked is hard for me. |
| **What I learned later** | Three practitioners have now told me, independently and unprompted, to just try the key. **The constraint is mine, not the field's.** I am keeping it, but I record that it is a choice rather than a consensus, and it is the single assumption that most shapes my results. |

### 1.3 How many hidden states

| | |
|---|---|
| **Options** | Two — real or false positive · Four — live, revoked, provider test key, fake |
| **Chose** | Four |
| **Why** | The two-way split hides the thing that matters. "Harmless" has different causes, and they do not cost the same to establish or to act on. |
| **What it bought** | Once the states were separate I could see that two of them were indistinguishable from inside a repository — which became the central finding. A two-state model would have hidden that. |

### 1.4 A fourth thing I could not describe

I suspected there was a state I was missing — a string that is not a credential
at all and only looks like one. I could not characterise it well enough to give
it a likelihood, so I wrote it down as an open question rather than inventing
numbers for it. That turned out to be the right call for an unexpected reason:
the state I was actually missing was a different one, and somebody handed it to
me five commits later.

---

## Commit 2 — Research, and the first practitioner reply

### 2.1 How to ask

| | |
|---|---|
| **Options** | Post with the project framing and ask for input · Ask a plain question about a thing that happens |
| **Chose** | Framing first, plain question second |
| **Why** | I did not decide this so much as learn it. My first post read as someone doing research and got one reply. My second was just a question, and got four in an hour, then four more. |
| **What it bought** | Eight substantive replies instead of one, and the plain-question format is now how I ask. |

### 2.2 Last-consumer telemetry as candidate evidence

The r/sysadmin reply said rotation breaks things specifically when the key had a
consumer nobody had documented, and to log which consumer last used a
credential. That was the first thing anyone had given me that spoke to
live-versus-dead — the pair I had already written down as having no observable
difference. I recorded it as a candidate rather than adopting it, because I did
not yet know whether it was obtainable.

---

## Commit 3 — Choose a provider, collapse the states, split remediation

### 3.1 Which provider

| | |
|---|---|
| **Options** | Two providers, one issuing test keys and one not · Stripe alone · OpenAI alone |
| **Chose** | OpenAI alone |
| **Why** | Two providers made the complexity compound faster than the insight. Between the remaining two: Stripe documents prefixes for all six key types on one page, which is better evidence, but whether its per-key request logs are reachable from an API is undocumented and I would have had to find out. OpenAI's probe is documented, callable, and I can quote the exact field. |
| **The trade** | **I gave up a hidden state to gain a probe I could verify.** OpenAI issues no separate test key, so the state space collapsed from four to three. |
| **What it cost, seen later** | OpenAI's `last_used_at` returns a timestamp and nothing else. A practitioner described the same probe on AWS IAM returning the service, the region *and* the date per key. Same probe, weaker signal, because of the provider I picked. |

### 3.2 Split remediation into two actions

| | |
|---|---|
| **Options** | One remediation action · Revoke now and rotate safely as separate actions |
| **Chose** | Two |
| **Why** | Leaving a system broken in order to be safe is not automatically the right call, and an agent that cannot express the difference cannot help me decide. |
| **What it bought, from a direction I did not expect** | When I later derived the thresholds from the cost matrix, revoke-now turned out to **own an entire regime** of belief on its own. If I had kept one remediation action I would never have found that region existed. The justification I wrote down and the justification the arithmetic produced were completely different arguments for the same decision. |

---

## Commit 4 — Price the decision

### 4.1 Cost, not accuracy

| | |
|---|---|
| **Options** | Measure whether the agent classifies findings correctly · Measure what the agent costs |
| **Chose** | Cost |
| **Why** | The baseline is what a team does today — hand it to a human, who resolves it correctly every time. There is no accuracy to win against a procedure that is already right. The only thing left to compete on is how many human interruptions get spent reaching the same answer. |
| **What it bought** | This is the decision the whole project rests on. Reporting an accuracy figure here would have been close to meaningless, and choosing cost is what made thresholds derivable instead of tunable. |

### 4.2 Engineer-minutes as the unit

| | |
|---|---|
| **Options** | Money · Engineer-minutes · An abstract utility scale |
| **Chose** | Engineer-minutes |
| **Why** | It is the only unit I could actually estimate, and the only one a practitioner could confirm or correct. Asking someone "how long did that take you" gets an answer; asking what it cost does not. |
| **What it cannot express** | Harm falling on customers rather than on the team. Actual money — revoking a certificate with a public CA costs a few hundred dollars, which is nobody's time. And the case where **no action helps at all**, which a practitioner raised about GPG master keys. My matrix has no cell for that. |

### 4.3 Every cell shows its working

I priced nine components and built fifteen cells out of them rather than writing
fifteen numbers down directly. This caught an arithmetic error — I had escalate
on a live key not adding up, and it was only visible because the components were
written out. It also meant that when one component was later corrected by a
practitioner, exactly one number changed and everything downstream followed.

---

## Commit 5 — Build the belief

### 5.1 Six features down to three

| | |
|---|---|
| **Options** | Keep all six candidate features · Cut to the ones I could put numbers on |
| **Chose** | Three — placeholder context, well-formedness, and the bought probe |
| **Why** | Same reason as the provider decision: complexity was compounding faster than insight, and I would have been inventing eighteen more likelihoods with nothing behind them. |
| **One I got wrong first** | I had "does this string appear in other public repositories" filed as free evidence. It is not — it means searching outside my repository, which is the same kind of act as calling an API. It is a second probe, and it would need its own cost and its own likelihoods with nothing to base them on. Identified, priced out, deferred. |

### 5.2 The consequence I did not choose

Live and revoked have **identical likelihood rows** on both free features,
because nothing visible in a repository distinguishes a key that works from one
that was turned off. I did not decide this. It fell out of writing the tables
honestly.

What it produces is arithmetic, not opinion: the live-to-revoked ratio is
`0.48 / 0.27 = 1.778` before any free evidence and `0.6329 / 0.3560 = 1.778`
after. Identical to four decimal places, because identical rows cancel in the
multiplication. **No amount of free evidence can ever move that ratio.**

This is the finding the whole project turns on, and it exists because I wrote
down two states that other people collapse into one.

### 5.3 An upgrade I dropped after checking

I wanted to split the probe's `null` outcome, because it was doing two jobs at
once — *the key is in my account and was never used*, and *the key is not in my
account at all*. Whether that was worth building depended on one fact: does
OpenAI keep revoked keys in the project list marked inactive, or delete them?

It deletes them. So absence is ambiguous in four different ways, and the split
would have made the probe look sharper than it is. **Dropped after one lookup,
which is cheaper than dropped after building it.**

---

## Commit 6 — Derive the policy

### 6.1 Derive the threshold rather than choose it

| | |
|---|---|
| **Options** | Pick a threshold that feels right and tune it · Take the action with the lowest expected cost and see where the boundaries land |
| **Chose** | Derive |
| **Why** | A tuned threshold is a number I would have to defend, and I have nothing to defend it with. A derived one is a consequence of the cost matrix, so arguing with it means arguing with a cost, which is a much more productive argument to have. |
| **What fell out** | Three regimes, unasked for: dismiss below 0.00145, revoke now up to 0.06588, rotate safely above. **The boundary is at 0.066, not 0.5.** Anyone building this by instinct puts the line at "more likely than not" and dismisses everything this model rotates. |

### 6.2 Entropy is not the escalation trigger

I expected uncertainty to be the thing that summons a human, because that is how
everyone talks about it. So I checked the most uncertain point available — a
third of the belief on each state, 1.585 bits, maximum possible confusion.
Rotate safely still wins, 54.00 against escalate's 68.67.

**Uncertainty measures confusion. It does not measure whether the confusion is
expensive.** Two roads at a fork are maximally uncertain and it does not matter
which you take; a fire alarm that is probably faulty is barely uncertain and
desperately needs a person. Entropy still has a job here — measuring how many
bits a probe removes — but it is not the trigger. **The cost of being wrong is.**

### 6.3 Escalation never wins, anywhere

Rather than test escalation at a few beliefs I swept the entire simplex and
computed the value of a *perfect* oracle — the absolute ceiling on what any
amount of human insight could be worth. Maximum across every possible belief:
**15.03 minutes** at any belief I can actually reach, against a human who costs
30. (24.78 over the whole simplex, but that maximiser sits at a belief my free
features rule out — an earlier version of this log quoted the simplex figure,
which answered a question I was not asking.)

Even an infallible expert is not worth asking *at thirty minutes*. That caveat
turned out to carry the whole result: see the review round below.

---

## Commit 7 — Work one finding end to end

I took a single case all the way through: a well-formed string, in a source
file, in a variable called `OPENAI_API_KEY`, committed eleven months ago.

I expected to buy the probe. P(live) was 0.63, I was far from certain, and more
information sounds better. So I priced it first — for each outcome, what would I
believe, and what would I then do?

All three outcomes lead to rotate safely. **Value of the information: 0.00.**

The rule I had written down five commits earlier — *investigating is only worth
doing if the action might change afterwards* — arrived as a consequence rather
than as something I asserted, on a case where my instinct said the opposite.

What I took from it: **being much less sure is not the same as being about to
act differently.** The probe halves my confidence in the state that matters and
the right action is identical before and after.

---

## Commit 8 — Reprice the probe

### 8.1 The correction

I had priced the probe at ten minutes with nothing behind it. A practitioner
described exactly this probe, unprompted, as the first thing you do — and said
it *usually ends the argument in a minute*. A second one warned never to
conclude anything from a single response, because they work with a source that
answers half of its identical requests differently. One minute a call, three
calls: **three minutes.**

| Probe price | Investigate is bought at | Share of findings |
|---|---|---|
| 10 min — my guess | nowhere | 0.00% |
| 5 min | nowhere | 0.00% |
| **3 min — sourced** | **neutral / malformed** | **3.98%** |
| 1 min | both malformed branches | 14.55% |

**Investigate was never a dead action. My probe was overpriced by a factor of
ten.** The agent now buys evidence on about one finding in twenty-five —
specifically the case where it sits closest to a threshold. That is a policy I
did not design; it fell out of a corrected number.

Escalate was unaffected, because it loses structurally rather than on price.

### 8.2 Investigate is not the same kind of thing as the other four

Repricing forced me to notice something that was wrong the whole time. My
fifteen-cell matrix has a row that does not mean what the others mean. The other
four rows are what an action *costs*. Investigate's row is only the **entry
fee** — it does not end anything, it buys an answer and then I decide again.

If I put 3 into the argmin alongside the rest it would win at every belief and
the agent would probe forever without acting. So: **four terminal actions
compete on expected cost, and investigate is compared separately**, on whether
what it buys exceeds what it costs. My decision record had already done this
correctly by instinct; the matrix was mislabelling what it held.

The general rule I got out of it: *an action may be collapsed from a sequence of
steps when no observation inside the sequence changes what you do next.* Rotate
safely reveals information but does not branch on it, so it collapses.
Investigate exists only to branch, so it cannot.

### 8.3 An assumption I withdrew

I had been telling myself that rotate safely verifies itself — you confirm
nothing is still calling the old key, so you learn the true state for free as a
side effect of acting.

A practitioner rotated a credential, watched the deploy go green, saw nothing
break, and was wrong: the old value was still live because it had been baked in
at image build time rather than read at startup. **Nothing breaking is not
evidence that the rotation took.**

So the confirmation step can silently lie, and my by-product-observation
argument is withdrawn. Their fix — have the app log a short fingerprint of
whatever credential it loaded on boot — is the second time somebody has told me
the answer is telemetry you have to set up in advance.

### 8.4 A fourth state, from somebody else

The same thread gave me the state I could not describe in commit 1, and it was
not the one I guessed. A practitioner refused to collapse authentication
failures: **401 means the credential was rejected; 403 means it authenticated
fine and simply is not allowed to do that.** A 403 is a real, live, working key
that can reach nothing.

My cost matrix charges 2400 to dismiss a live key precisely because whatever
sits behind it is reachable. For this one, nothing is. Another reply described
the same animal from a different angle — a key with no access left because the
project died two years ago.

I am recording it as an open state rather than adding it. Three states is what I
can price.

---

## Commit 9 — Run the experiment

### 9.1 What to compare against

| | |
|---|---|
| **Options** | Compare my policy against nothing · Against a naive threshold · Against what teams actually do |
| **Chose** | All three, plus a policy that looks at no evidence at all |
| **Why** | P0 — acting on the prior with no evidence — is the control I nearly left out, and it turned out to be the most informative row in the table. |

### 9.2 Report both an exact number and a sampled one

There are only fifty-four possible worlds here, so expected cost is computable
in closed form rather than estimated. I report that *and* the realised cost on
forty cases, because forty draws is few enough that one dismissed live key moves
the total by more than half — and hiding that would misrepresent what a run
actually costs.

### 9.3 What the experiment said

| | Policy | Expected cost | vs baseline |
|---|---|---|---|
| baseline | escalate everything | 84.80 | — |
| P0 | prior only, no evidence | 66.86 | −21.2% |
| P1 | hand-picked, all four actions | 77.79 | −8.3% |
| P2 | evidence, cost-derived | 65.11 | **−23.2%** |
| P3 | P2 plus the probe | 65.03 | −23.3% |

**Almost none of the saving comes from the evidence.** P0 looks at nothing at
all and already beats the baseline by 21.2%. My full belief model gets to 23.2%.
The evidence is worth **1.75 minutes per finding**; the other twenty-one points
come from one decision — stop asking a human. This is the least flattering
result in the project and it is the one I would lead with.

**The obvious threshold is worse than the procedure it replaces.** P1 is what a
sensible engineer writes on the first afternoon, and it costs more than twice
the baseline. Worse, it is *unstable*: sweep the live-versus-revoked split and
P1 goes from 185 to **901**, because the largest bucket of findings flips from
rotate to dismiss. P2 moves smoothly from 68.9 to 59.4 over the same range. **A
threshold read off the cost matrix cannot fall off that cliff, because it moves
when the costs move.**

**Evidence is worth nothing when one action dominates.** Price the outage at
zero and revoke-now is cheapest in every state — P0 and P2 then cost *exactly*
46.0. Reading the features changes nothing because nothing they could say would
change the action. That is the value-of-information result one level up.

**The probe matters most where the decision is closest.** In the outage sweep,
the probe is worth 1.0 minutes when an outage costs 60 and 0.08 when it costs
240 — twelve times more valuable when a cheap outage puts revoke-now and rotate
safely in close competition. Value of information concentrates near decision
boundaries, which I had suspected and had not shown.

### 9.4 The generator problem, recorded rather than hidden

My case generator draws from the same likelihood tables the agent reasons with,
so the agent is being tested in a world that agrees with its own assumptions.
That flatters every policy that uses evidence. It is why `data/cases.json` is
written once and never regenerated, and it is a real limitation rather than an
implementation detail.

---

## After commit 9 — two ideas tested rather than adopted

### A. Escalation is a permission boundary, not a priced action

I priced escalate as *epistemic* — thirty minutes of human attention, and then
they do the right thing. Under that model it can never win, and my simplex sweep
proves it.

But escalation might exist for a completely different reason: the agent is not
**permitted** to revoke a key belonging to another team. If that is what it is
for, it was never competing on cost at all — it is a constraint on the action
space, not an option inside it.

Which is the same shape as what I found about investigate. **Two of my five
actions are not the same kind of object as the other three.** Only dismiss,
revoke now and rotate safely are terminal actions competing on expected cost.
Investigate is a decision point. Escalate is a permission gate.

### B. Probing the action instead of the state — checked, and it does not work

The suggestion: instead of asking *is this key live*, ask *which systems consume
it*, which might pay off even when the state is certain.

I tested it. The rotate-versus-revoke boundary sits at the same place for every
value of the consumer hunt from 30 minutes to 480:

```
find-consumers   30 → boundary 0.06588
                 60 → boundary 0.06588
                120 → boundary 0.06588
                240 → boundary 0.06588
                480 → boundary 0.06588
```

Because the hunt appears **identically** in both remediation actions:
`rotate(live) = 82 + F`, `revoke(live) = 302 + F`, difference always exactly 220
— the outage, and nothing else. Whatever I learn about the consumers I learn
about both options equally, so it cannot choose between them.

My own principle firing on somebody else's idea: **information that changes what
you pay but not what you do is worth nothing.**

---

## The review round — where four models found what I could not

I put the preprint in front of four AI reviewers with different briefs, then
tested every claim I could. This is the part of the project where the most
numbers changed.

### R.1 The threshold comparison was confounded

| | |
|---|---|
| **What I had** | P1 = "threshold 0.5, else dismiss", costing 111% more than the baseline, presented as my strongest argument for deriving boundaries |
| **What was wrong** | It changed the threshold *and* removed revoke-now from the action set. Two reviewers found this independently |
| **What is true** | The same 0.5 threshold with a revoke fallback **beats** the baseline by 12.4%. With all four actions P1 costs 77.79 — 8.3% better than the baseline, 19.5% worse than P2 |
| **What survives** | P1 is non-monotonic under the prior: 60% worse than the baseline at a live share of 0.40, 8% better at 0.64. A fixed boundary cannot track a moving prior. Smaller claim, and the true one |

### R.2 I measured the boundaries on a line the agent cannot occupy

Three states means a boundary is only defined relative to a path through the
simplex. My free features lock live:revoked at 1.778, so the agent walks one
line — and I had computed on a different one. **0.09386 → 0.06588** for the
decision boundary, **24.64 → 15.03** for the VPI bound. I had noticed the
discrepancy myself hours earlier and not chased it.

### R.3 Escalation was never structural

Holding every other cost at its point estimate and varying only what a human
costs: 100% of findings escalated at 3 minutes, 15.6% at 12, zero at 20 and
above. My "the agent never escalates and I can prove it" was a statement about
one number I guessed. The controlled sweep replaces it.

### R.4 The whole belief-model result lives in one cell

A reviewer asked why rotating a *fake* key costs 20 minutes when there is
nothing to rotate. Testing it: at zero, P0 and P2 become **identical** and the
belief model is worth precisely nothing. Every number in my headline finding
rests on that one estimate.

### R.5 One-at-a-time sweeps were flattering me

Sampling all thirteen costs jointly, 40,000 draws: P2 beats the baseline in 98%
of them, the boundary sits below 0.5 in 93%, and "escalate is chosen nowhere"
holds in only 70%. The saving runs 0.5% to 51%. **The claims worth keeping are
about ordering, not magnitude.**

My first sampler was also wrong — a single lognormal spread that only produces
the stated range when the estimate is the geometric midpoint of low and high.
Eight of fourteen quantities were not, so the published ranges were not the
sampled ones.

### R.6 Perturbing the evidence model changed almost nothing

The best result of the round, and I did not expect it. Perturbing every
likelihood row — live and revoked independently, deliberately breaking the
identical-rows property — moves the live:revoked ratio by a factor of twelve
across buckets, and **no conclusion shifts by more than 3.2 points.** So the
invariance is an idealisation and the conclusions resting on it do not need it.
That is the answer to every reviewer who said repository visibility or commit
semantics might separate the two states: even when something does, it barely
changes what the agent does.

### R.7 Two reviewer claims I tested and rejected

**"GitHub's validity checks make your premise false."** GitHub's own pattern
table marks OpenAI API Key as a partner pattern *without* validity-check
support. Rejected on the facts — and the check now appears in the paper as a
citation defending the premise rather than an assumption.

**"Scaling the breach cost collapses the policies."** It does not. The
revoke/rotate boundary holds at 0.06588 whether dismissing a live key costs
2,400 or 120,000, because that component appears in neither action.

## What I would tell someone starting this

**Closing options produced more than adding them.** One provider, three states,
three features, no authentication with a found key. Every one of those made the
model smaller, and every one of them made a finding visible that a bigger model
would have buried.

**Derive numbers, do not choose them.** The threshold, the three regimes, the
invariant ratio, the entropy result and the value of the probe are all
consequences. None of them is a parameter I set, which means none of them is
something I have to defend on my own authority.

**Ask plainly.** My question with the project attached got one reply. The same
question asked as a thing that happens got eight, and two of them changed
results — one repriced a number by a factor of ten, one withdrew an assumption I
was leaning on.

**The results that argued with me were the useful ones.** Escalation never
winning, evidence being worth 1.75 minutes, the probe I was sure I should buy
being worth exactly nothing. A model that agreed with me everywhere would have
told me only what I already believed.

**And check the code, not just the conclusions.** Four reviewers read the paper
and found real problems. The fifth read the *implementation* and found that my
sampler had been drawing from ranges I had not published. Every review that
only saw the write-up missed it, because the write-up described what I intended
rather than what ran.
