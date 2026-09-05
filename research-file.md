# Research File

## Problem Statement

> The agent observes a scanner result reporting that a string in the repository looks like an OpenAI key. It must select **dismiss**, **investigate**, **escalate**, **revoke now**, or **rotate safely**, because whether that string is a live key, a revoked key, or a fake key hard-coded by a developer is not known.

### Why the hidden state is not "is this a secret"

My first attempt at the hidden state was "is this string a secret or not". I dropped it because the scanner has already answered that — reporting that a string looks like a key is the whole of what it does. Restating its output as my hidden state would mean the agent adds nothing. It is also not what makes the decision hard. What I cannot see is what the key *is*, and the scanner does not tell me: it does not say what kind of key it found, and it does not say whether the key works.

### The states

Week 1 was built on three. Week 2 added two more. Both are marked below, because
the sequence is the point: I could not characterise states 4 and 5 when I wrote
this section, said so, and added them once I could.

1. **A live key.** Still authenticates, and is authorised to do something. Whatever sits behind it is reachable by anyone who has the string.
2. **A revoked key.** Was real once, no longer works. Harmless now.
3. **A fake key.** Hard-coded by a developer, never authenticated against anything.
4. **A zero-scope key.** *(added in Week 2)* Authenticates, but is authorised for nothing. Live by any test that asks *does this work*, worthless to whoever finds it.
5. **Something else.** *(added in Week 2)* A string that is not a credential at all, that just happens to look like one because something in the code needed a long random-looking string.

The decision is hard because the actions I would take differ across them and what I can see does not tell me which state I am in.

**On state 4.** I originally wrote `live` as one state, and it was doing two jobs: *this authenticates* and *this is dangerous*. Those are different properties, and Stripe's publishable keys — live and safe to expose by design — are the clearest evidence that they come apart. So `zero_scope` is carved out of the live mass (1/12 of it) rather than added beside it. It is the only state added because an existing state was ambiguous rather than because a new case appeared.

**On state 5.** I could not characterise it in Week 1 — what it would look like, or how it would differ from a fake key in anything I can observe — and left it out rather than inventing a definition. Week 2 puts it in at 1% of the prior and uses its own unreliability as the point: because I do not trust the cost model on this state, P(other) crossing 0.05 is one of the two triggers that hands the finding to a human. It is the least understood state in the model and it earns its place by being the reason the agent asks for help.

### The state space depends on the provider, and mine collapsed

I originally wrote down four states. The fourth was a **provider-issued test key** — the kind an API provider hands out so you can test against a sandbox. Working through the list I noticed that state is not universal: it exists only where the provider issues such a key, and where they do not, the space collapses.

That turned out to be more than a footnote. When I came to choose a provider, I had to decide between one that issues test keys and one that does not, and that choice was not only about which key formats I could recognise — **it was a decision about what my hidden states are.**

I chose OpenAI, which issues no separate test key. So the test-key state does not exist for me and I am working with three, not four. The collapse is real and it is recorded here rather than quietly edited out, because it is the clearest evidence I have that the state space is a modelling choice and not a fact about the world.

### The five actions

- **Dismiss** — do nothing.
- **Investigate** — buy more information. The agent still makes the decision afterwards, and it may still escalate later if what it learned did not resolve the uncertainty.
- **Escalate** — hand it to a human. The human makes the decision.
- **Revoke now** — kill the key immediately. Fast and certain, and it breaks anything that was still using it.
- **Rotate safely** — issue a replacement, update whatever was using the old key, confirm nothing is still calling it, then revoke. No outage, but it costs a deploy cycle.

I split remediation into two actions after working out what it actually involves. Revocation is the only thing that makes an exposed string worthless — deleting it from the file achieves nothing, because it is still in the git history and in every clone anyone made. Everything else in the procedure exists to keep the service running, not to secure anything. So if nothing was using the key, remediation is just a revocation and it takes minutes. If something *was* using it, I have to find that thing, give it a new key, deploy, verify, and only then revoke.

Those are different enough in cost and risk that collapsing them into one "remediate" would hide the trade-off the whole project is about. Leaving the system broken to be safe is not obviously the right call, and an agent that cannot express the difference cannot help me decide.

Two things I had to get clear before that made sense:

- The replacement key does **not** go into the repository. It goes into an environment variable or a secrets vault, and the code reads it from there. Otherwise I would be solving the problem by recreating it.
- My agent does not remediate. It decides whether that expensive human procedure is warranted. It is triage, not repair.

There is also a rule that follows from having investigate as an action at all: **investigating is only worth doing if the action might change afterwards.** If I investigate and then take the action I would have taken anyway, the investigation was wasted.

## Project Objective

### The baseline

The baseline is what a person actually does today. Find a key, hand it to a human to check whether it is live, act on what they say.

I also thought through a more careful version of the same procedure: check the key's prefix against the provider's published format first, and only contact a person if it still looks like a live key. That is the same instinct as the investigate rule above — take the cheap action first and the costly one only when it is still needed. The simple escalate-everything version is the baseline I settled on, because it is the one that is actually in use and the one with the property below.

### Why the objective is about cost and not accuracy

The property that decided the shape of this project: **escalate-everything is never wrong about the state.** A human resolves it correctly every time, so the baseline's accuracy is not a number my agent can improve on. There is no headroom there at all.

That leaves cost as the only thing to compete on — how many human interruptions get spent arriving at the same decisions. It is why the project is built on cost, and it is why an accuracy figure in my results would be close to meaningless. I want to state this early, because reporting accuracy is the obvious thing to do and it would look like a result while measuring nothing.

### The objective

**Does a probabilistic, cost-aware policy reach the same decisions as escalate-everything while spending fewer human interruptions — and under what conditions does it stop doing so?**

The second half matters as much as the first. A rule that wins under every assumption I could vary would be evidence that the comparison was built badly, not evidence that the agent is good. I would rather find the conditions where it loses than report that it always wins.

### Scope

- **Findings originate in a repository.** Not cloud configuration, not credentials in a running process. This scopes where the decision *starts*; it does not mean the agent may only look at the repository. Investigate is precisely the action that reaches outside it.
- **One provider: OpenAI.** Settled — see below.
- **One finding at a time.** The agent decides about a single flagged string, not about whether a whole repository is compromised.
- **It is a simulation.** I have no admin credential and the agent makes no live API calls. Every likelihood I write will be my estimate, not a measurement. That is allowed at this scale, but it means the honest result is a sensitivity analysis rather than a point estimate, and I would rather say so now than be caught claiming precision I do not have.

### Choosing the provider

I started intending to use two providers — one that issues test keys and one that does not — so I could show the state space collapsing. I dropped that. The complexity was compounding faster than the insight: six Stripe key types, two sets of prefixes, two different remediation procedures, and a second set of likelihoods to estimate. Cutting to one provider was the right call and I would rather record that I found it too much than pretend I planned it.

**OpenAI, because the evidence is real.** The probe I need is documented, callable from a terminal, and I can quote the exact field:

```
GET /organization/projects/{project_id}/api_keys
Authorization: Bearer $OPENAI_ADMIN_KEY
```

It returns `last_used_at` — a Unix timestamp, second granularity, `null` if the key has never been used. It also returns `created_at`, `redacted_value` (which is how a finding gets matched to a key), and whether the owner's project access is active. There is a separate Usage API that buckets at `1m`, `1h` or `1d` grouped by `api_key_id`.

Critically, this uses an **admin** credential, not the key I found. I decided at the start that I would not authenticate against a third party's API with a credential I found in a repository, and this respects that — I am asking my own account what it knows about a key, not pretending to be that key.

What I gave up by not choosing Stripe: the test-key state, and a much better-documented key lifecycle. Stripe publishes prefixes for all six of its key types on one page. But whether Stripe's per-key request logs are reachable from an API is undocumented, and I would have had to find out. A verified probe was worth more than a preserved state.

### What the probe can and cannot do

This is the part I had to think hardest about.

If `last_used_at` comes back with a **timestamp**, something authenticated with that key. A fake key can never produce a timestamp — it was never real. So a timestamp **eliminates fake outright**. That is the strongest thing my evidence does.

If it comes back **null**, it eliminates nothing. A live key nobody has called yet is null. A fake key is null. A key created and revoked without ever being used is null too. All three survive.

So the probe is sharply asymmetric: **strong when it returns a timestamp, nearly useless when it returns null** — and I cannot know which I will get before I pay for it.

It does a second job I did not expect. It also tells me what remediation will *cost*. Null means nothing was calling the key, so there is no consumer to update and remediation is a revocation that takes minutes. A recent timestamp means something is calling it, so remediation means finding that thing, deploying a new key, and verifying — days. Same call, two answers: which state I am in, and how expensive it will be to act.

### What is free, and why there is so little of it

With a provider that publishes `sk_test_` and `sk_live_` prefixes, the string itself does real work before I spend anything. OpenAI does not do that. Every key starts `sk-` or `sk-proj-`, whether it is live, revoked, or fake. **The prefix separates nothing.**

What is left that costs me nothing to look at:

- the path — `.env.example`, `test/`, `docs/` versus `src/`
- the surrounding variable name — `OPENAI_API_KEY` versus `DUMMY_KEY`
- whether the string is well-formed, or an obvious placeholder like `sk-xxxxxxxx`
- the commit that introduced it: who, when, and what the message said
- whether the same string appears in other public repositories

Every one of those mostly attacks **fake**. Nothing free separates live from revoked.

So my evidence is lopsided: five pieces pointing at one state and one piece, weakly, at the pair that matters. My first reaction was that this is a gap in my design and that I should go and find more evidence to balance it.

I no longer think that. **The imbalance is the finding.**

A live key and a revoked key are the same string, in the same file, committed by the same person on the same day. Nothing about the repository distinguishes them, because revocation happens somewhere else entirely — at the provider, after the commit was written. There is no observation I could add to the repository side that would separate them, no matter how carefully I looked.

That explains three things I had been treating as separate:

- **Why the human baseline exists at all.** Escalate-everything is not laziness. It is the correct response to a state pair with no local observable — you have to ask the only party that knows.
- **Why the probe carries so much weight.** It is not one evidence source among six. It is the only thing that reaches the side of the problem the repository cannot see, which is why an agent without an investigate action would be close to useless here.
- **Why adding more free evidence would not help.** A seventh signal that attacks *fake* costs me three more invented likelihoods and buys nothing, because that side is already well covered.

I would rather record this as the shape of the problem than quietly go looking for evidence that does not exist.

**And it is a property of API keys, not of credentials generally.** A practitioner answering about certificates pointed out that a certificate carries a CRL distribution point — a pointer to its own revocation list — so you can check almost instantly whether it has been revoked. The credential tells you its own status. Live-versus-revoked, the pair I cannot separate and the pair my probe exists to attack, is a solved problem for a different credential type.

PKI solved it with revocation lists decades ago. An OpenAI key has no equivalent: no revocation list, no status field, nothing in the string. So the imbalance is not a fact about leaked secrets — it is a fact about the credential format I chose, and a different choice would have made the whole project easier and less interesting.

### Two things I learned from Stripe's documentation and kept

I read Stripe's key documentation before dropping it, and two things there are worth carrying even though I am not using the provider.

**`pk_live_` is safe to expose.** Stripe's publishable keys are meant to sit in front-end code. A `pk_live_` in a repository is a live production key and finding it is not an incident. So "live" and "dangerous" are not the same property, and my state 1 currently bundles them. Whether blast radius needs to be a separate axis is open — OpenAI's version of the question is an admin key versus a project key.

**The cost of a wrong remediation belongs to the provider, not to the problem.** Stripe gives a seven-day grace period on rotation — old and new keys both work while you migrate. OpenAI revokes in seconds, with no grace. The same mistake costs wildly different amounts depending on who issued the key. My provider choice made remediation harder, and that is worth knowing rather than discovering later.

### The cost model

Everything is priced in **engineer-minutes**. I picked that unit because it is the one people can actually estimate — someone will tell you "rotating that key took us about two hours", and nobody will tell you it cost 340 units. If I want real numbers from practitioners, I have to ask in a currency they think in.

**What the unit cannot express.** I am pricing a breach as the hours my team would spend responding to it. That is the part I can estimate. It leaves out harm to customers, which does not turn into my team's time, so my number for a missed live key is almost certainly too low.

A practitioner later gave me a second gap I had not thought of: revoking a certificate issued by a public CA costs **actual money**, a few hundred dollars, which is not anyone's time either. And they described a case where no action helps at all — an exposed GPG master signing key with no revocation certificate published in advance. My matrix has a cell for every action in every state; it has no way to say *nothing works*.

**Scope: project keys only.** OpenAI issues admin keys as well, and an admin key is a different problem — it can create keys and act as the organisation, so the damage is unbounded rather than capped by a spend limit. Pricing one cell to cover both would mean either treating every finding as catastrophic or averaging the catastrophic case away. I am modelling project keys and leaving admin keys out.

#### What the cost actually depends on

Before I could put a number on dismissing a live key, I had to work out that it is not one number at all:

> cost = (chance someone finds and uses it) × (damage if they do)

A key in a repository that has been private for years is unlikely to be found. A key in one that was public for two weeks will have been scraped within minutes. And a project key with a spend cap does bounded damage where an admin key does not. Narrowing to project keys pins the second factor; the first is still varying underneath my single number, and that is one reason it is the number I sweep.

#### The components

| Piece | Minutes |
|---|---|
| Revoke a key | 2 |
| Issue a new key | 10 |
| Run the probe — three calls at about a minute each | 3 |
| Human attention | 30 |
| Find the consumers — documented | 30 |
| Find the consumers — undocumented | 480 |
| Deploy | 60 |
| Verify nothing is calling the old key | 10 |
| Production down while someone scrambles | 240 |

#### The matrix

| | Live | Revoked | Fake |
|---|---|---|---|
| **Dismiss** | **2400** | 2 | 2 |
| **Investigate** | 3 | 3 | 3 |
| **Escalate** | 142 | 32 | 32 |
| **Revoke now** | 332 | 2 | 5 |
| **Rotate safely** | **112** | 30 | 20 |

The three cells that needed working out:

- **Rotate safely on a live key = 112.** `10 issue + 30 find + 60 deploy + 10 verify + 2 revoke`. This assumes the consumers are documented.
- **Revoke now on a live key = 332.** `2 revoke + 240 outage + 30 find + 60 deploy`. Exactly the same hunt and the same deploy as rotating safely — but production is down while it happens. **The outage term is the entire difference between my two remediation actions.**
- **Escalate = 30 + whatever the human then correctly does**, giving 142 / 32 / 32. Escalation can never be cheaper than the action the human takes; it is that action plus their attention.

**I rounded these at first and it caused a problem.** An earlier version wrote 120, 330 and 150/30/30, and the rounded values then disagreed with the component arithmetic elsewhere in my own notes — a reviewer found two sections using two different matrices. The sums are exact everywhere now.

Dismissing a revoked or fake key is 2 rather than 0, because the finding comes back on the next scan and someone dismisses it again. Investigating costs the same in every column because the probe is paid for before I know which column I am in.

**The probe was ten minutes until someone who uses it told me otherwise.** I had guessed ten with nothing behind it. A practitioner said checking last-used on a credential first *usually ends the argument in a minute*, and a second one said never to conclude anything from a single response — they work with a source that returns a different answer to half of its identical requests. One minute a call, three calls, three minutes. It is the only cell in this matrix sourced from two people rather than from me.

**Investigate's row is not the same kind of number as the other four.** The other rows are what an action costs. This row is only the entry fee — investigate does not end anything, it buys an answer and then I decide again. If I dropped 3 into the argmin alongside the rest it would win at every belief and the agent would probe forever without ever acting. So four actions compete on expected cost, and investigate competes separately: buy it when what it is worth exceeds what it costs.

**Sanity check.** If I knew a key was live, the ordering is rotate safely (120) < escalate (150) < revoke now (330) < dismiss (2400). That is what it should be: rotating is the right thing, escalating costs a little more because it spends a person, revoking now costs the outage, and dismissing costs the breach.

#### When revoke-now is the right call

If rotating safely were always cheaper, I would not need two remediation actions — I would always rotate safely. The reason to keep both is that something flips it.

That something is **active abuse**. If someone is using the key right now, every minute spent on the careful procedure is another minute of someone else running my account. At that point breaking my own production deliberately costs less than letting the abuse continue.

And the probe tells me which case I am in. Recent activity I do not recognise means abuse in progress. So `last_used_at` does three jobs from one call: which state I am in, what remediation will cost, and which of my two remediation actions to choose.

#### The two numbers I sweep

Everything above is elicited. Two numbers are shakier than the rest and both get swept rather than asserted:

- **Dismissing a live key (2400).** Range 240 to 24,000. It is the largest number in the matrix, it is the one my unit is worst at expressing, and it depends on exposure I have not modelled.
- **Finding the consumers (30).** Originally swept 30 to 480 — an hour if someone wrote it down, a day if nobody did. **A practitioner then suggested timeboxing it**: if the rotation is not going smoothly after ten or fifteen minutes, stop. That caps the tail rather than leaving it open, and it is the answer to a question I thought only a sweep could handle.
- **The live-versus-revoked split inside the prior.** Sweep 40/60 to 80/20, which moves P(live) between roughly 0.30 and 0.60. This one is swept for a reason the others are not: **my evidence cannot correct it.** Live and revoked have identical likelihood rows on both free features, so whatever I assume here flows straight through to every posterior untouched. A prior the evidence cannot move is a prior I am merely asserting.

#### Two things this matrix cannot say

**It adds minutes belonging to different people.** Mine, the reviewer's, the on-call engineer's, and — inside the breach number — time that is really the customer's problem rather than anyone's minutes at all. They are not the same currency. An agent that spends someone else's time to save its own would look good by this measure, and I have not guarded against that.

**It cannot tell expensive apart from permanent.** A wrong dismissal of a fake key is caught by the next scan. A wrong revocation takes production down for hours and then everything is fine. A missed live key that gets used never unwinds. One number per cell cannot express that difference. I am leaving it as one number and sweeping the missed-live cost across a wide range instead, which covers the "worse than the minutes suggest" case without adding machinery I would then have to justify.

### The belief

The agent has to hold a probability over the three states and update it as evidence arrives. This is where the numbers get invented most heavily, so I want the reasoning next to them.

#### The prior

Before looking at anything about a particular finding:

| State | Prior |
|---|---|
| Live | 0.48 |
| Revoked | 0.27 |
| Fake | 0.25 |

This is derived rather than guessed, which is its only real virtue. GitHub's scanner reports about 75% precision, so roughly three-quarters of findings are real credentials and a quarter are not. GitGuardian reports that around 64% of credentials valid in 2022 were still valid in 2026, so of the real ones, roughly two-thirds are still live. That gives 0.75 × 0.64 = 0.48 live, 0.75 × 0.36 = 0.27 revoked, and 0.25 fake.

**Choosing GitHub's scanner made my problem easier, and that is a scope decision.** At 75% precision most findings are real keys. Had I assumed one of the open-source scanners the same study measured at under 7%, fake would dominate and the agent's main job would be filtering junk instead of deciding what to do. Different detector, different problem.

**The mapping is not clean.** Precision counts a finding as a false positive when it is *not a credential*. My fake state means *a developer hard-coded something that was never real* — and a well-formed fake still matches the pattern, so a scanner would count it as a hit. So my 0.25 is really covering two things: fake keys, and the fourth state I could not characterise. I have been forced to lump them together because that is the only figure available. It is a concrete reason the fourth state matters.

#### Collapsing the evidence

I started with six pieces of evidence and cut them to three, for two different reasons.

**Three of them were one thing wearing three hats.** File path, surrounding variable name, and commit message almost always agree: a key in `.env.example` is called `YOUR_KEY_HERE` and was committed as "add example config". Treating them as three independent votes would make the model count the same evidence three times and grow more confident while getting no better informed. They are now one feature, **placeholder context**.

**One was miscategorised.** Checking whether the same string appears in other public repositories is not free — it means searching somewhere outside my repository, which is the same kind of act as calling the API. It is a second probe, not free evidence, and it would need its own cost and its own likelihoods with nothing to base them on. Identified, priced out, and deferred.

That leaves:

| Feature | Values | Free or bought |
|---|---|---|
| Placeholder context | placeholder / neutral / production | Free |
| Well-formedness | well-formed / malformed | Free |
| `last_used_at` | recent / old / null | Bought |

Twenty-four invented numbers instead of the fifty-odd the original six would have needed, and none of them counting the same thing twice.

#### The likelihoods

`P(evidence | state)`. Every row sums to 1.

**Placeholder context**

| | placeholder | neutral | production |
|---|---|---|---|
| Live | 0.10 | 0.30 | 0.60 |
| Revoked | 0.10 | 0.30 | 0.60 |
| Fake | 0.70 | 0.25 | 0.05 |

A real key is committed by accident into wherever the code actually lives, so it skews production. The 0.10 on placeholder is not zero because of the config-drift case the practitioner described — a real key sitting in a sample file because the published config and the effective one diverged years earlier.

**Well-formedness**

| | well-formed | malformed |
|---|---|---|
| Live | 0.99 | 0.01 |
| Revoked | 0.99 | 0.01 |
| Fake | 0.40 | 0.60 |

Real keys are always well-formed; they came from OpenAI. Fakes split, because some people type `sk-xxxxxxxx` and others copy a realistic-looking string out of the documentation.

**`last_used_at`**

| | recent | old | null |
|---|---|---|---|
| Live | 0.60 | 0.20 | 0.20 |
| Revoked | 0.02 | 0.78 | 0.20 |
| Fake | 0.01 | 0.04 | 0.95 |

A revoked key cannot produce recent activity, but its timestamp is frozen at whenever it last worked, so it skews old. Fake is overwhelmingly null because the key was never in the account at all.

#### What these tables say out loud

**On both free features, live and revoked have identical rows.** Not similar — identical. I did not impose that; it is what I believe to be true, and it is the evidence-imbalance finding turned into numbers. Nothing observable in a repository distinguishes a live key from a revoked one.

#### The update rule

Standard Bayes. For each state, multiply the prior by the likelihood of every piece of evidence observed, then normalise so the three sum to 1:

```
posterior(s) ∝ prior(s) × P(context | s) × P(form | s) × P(probe | s)
```

Worked through, on a finding in production context with a well-formed string:

**With free evidence only**

| State | Prior | × context | × form | Posterior |
|---|---|---|---|---|
| Live | 0.48 | 0.60 | 0.99 | **0.6329** |
| Revoked | 0.27 | 0.60 | 0.99 | **0.3560** |
| Fake | 0.25 | 0.05 | 0.40 | **0.0111** |

Fake is crushed from 0.25 to 0.011 — the free evidence does its job well. But look at the ratio of live to revoked: it was 0.48/0.27 = **1.778** before, and it is 0.6329/0.3560 = **1.778** after.

Identical. To four decimal places. The free evidence moved the live-versus-revoked balance **not at all**, because both states have the same likelihood on both features, so the multiplication cancels. My finding is not a claim about the model — it is arithmetic.

**Then the probe returns `old`**

| State | Posterior before | × probe | Posterior after |
|---|---|---|---|
| Live | 0.6329 | 0.20 | **0.3128** |
| Revoked | 0.3560 | 0.78 | **0.6861** |
| Fake | 0.0111 | 0.04 | **0.0011** |

The ratio goes from 1.778 to 0.456 — the belief flips from probably-live to probably-revoked, and one call did all of it. That is what it means for a single piece of evidence to be load-bearing.

#### Two states or three?

Worth recording that I checked. My cost matrix gives revoked and fake nearly identical rows — every action costs about the same whichever it is — so for choosing an *action*, they are effectively one state and I could have collapsed to live / not-live.

I kept three. Not because the costs earn it, but because the evidence separates them cleanly for free, and because "this was never a key" and "this key is dead" are different things to tell a person. A model that can only say *dismissable* is less useful to a human than one that can say why.

#### An upgrade I checked and then dropped

My `null` outcome does two jobs: *the key is in my account and was never used*, and *the key is not in my account at all*. Splitting them looked like the obvious way to strengthen my only probe, and whether it was worth building depended on one thing — does OpenAI keep revoked keys in the project list marked inactive, or delete them?

I looked it up. **It deletes them.** The delete endpoint returns `{"deleted": true, "object": "organization.project.api_key.deleted"}`, which is the shape of a removal rather than a status change.

Worse, there is a case I had not considered. A developer reported a key that still worked but did not appear in the API keys tab at all — it turned out to be a *legacy user-level key*, which lives at a different endpoint from project keys. Nobody from OpenAI explained why.

So "not in the list" covers four things: the key was fake, the key was revoked and deleted, the key belongs to another account, or **the key is real and live and sitting at an endpoint I did not query.** One of those points the opposite way from the other three.

I am not building the split. Absence is ambiguous four ways and the three-value `last_used_at` I already have is the honest model. Recording it because a lookup that closes an option is as useful as one that opens it, and I would otherwise have spent a day on it.

### The policy

#### The rule

```
a* = argmin over actions of   Σ  P(state) × cost(action, state)
                            states
```

That is the whole thing. **I never chose a threshold.** I set fifteen costs for reasons that had nothing to do with where a decision boundary should sit, and the boundary came out of them.

At my prior — 0.48 live, 0.27 revoked, 0.25 fake:

| Action | Expected cost |
|---|---|
| Dismiss | 1153.04 |
| Escalate | 84.80 |
| Revoke now | 161.15 |
| **Rotate safely** | **66.86** |

#### Three regimes I did not design

Asking which action is cheapest as P(live) rises. With three states a boundary
only means something relative to a path through the belief space, and my free
features lock live:revoked at 1.778 — so the agent walks one line and never
leaves it. These are measured on that line. (An earlier version measured them
on a different slice and reported 0.0007 and 0.0939, which describe beliefs the
agent cannot hold. A reviewer caught it.)

| P(live) | Cheapest action |
|---|---|
| below 0.00145 | Dismiss |
| 0.00145 – 0.06588 | **Revoke now** |
| above 0.06588 | **Rotate safely** |

The middle band is the one I did not expect. If a key is *probably dead*, revoking now is cheaper than rotating safely — there are no consumers to migrate, so you skip the deploy entirely and just kill it.

Each of my two remediation actions owns a region, and neither dominates. That is a justification for splitting them that arrived after the fact, from a completely different direction than the argument I made at the time. I find that more convincing than the argument I made.

#### The agent never escalates, and I can prove it

Escalate does not appear in that table at any value of P(live). My first thought was that the model must be overconfident. It is not.

Take the belief where the agent is *maximally* confused — 1/3, 1/3, 1/3, entropy 1.585 bits, the most uncertain a three-state belief can be:

| Action | Expected cost |
|---|---|
| **Rotate safely** | **54.00** |
| Escalate | 68.67 |
| Revoke now | 113.00 |
| Dismiss | 801.33 |

The agent knows nothing at all and still does not want a human.

The reason is that **rotate-safely is a hedge**. It costs 112 / 30 / 20 — tolerable in every state. When one action is decent no matter what is true, being confused costs almost nothing, so there is nothing worth paying to resolve.

Put precisely: the value of perfect information — what an oracle telling me the true state would be worth — is at most **15.03 engineer-minutes at any belief I can actually reach** (24.78 over the whole simplex, but the maximiser there is a belief my free features rule out). A human costs 30, so even a perfect oracle is not worth asking.

**This is a statement about my thirty-minute human, not about the problem.** Holding every other cost fixed and varying only that number: at 30 minutes the agent escalates nothing; at 12 it escalates 15.6% of findings; at 3 minutes or less it escalates everything. The crossover sits between 12 and 20. I wrote "the agent never escalates and I can prove it" above, and what I can actually prove is narrower — escalation is dominated *when interrupting a person costs more than about fifteen minutes*.

#### What I got wrong about entropy

I assumed high entropy was what should trigger escalation. That is the obvious rule and it is what I would have built. It is wrong, and the reason is worth stating because I will otherwise make the mistake again.

Two roads at a fork, 50/50, no idea which. Maximum uncertainty. Do you phone someone for directions? Not if both roads lead to the same town.

A fire alarm you are 95% sure is real. Very low entropy. Do you want a human deciding whether to evacuate five hundred people? Badly.

**Entropy measures how confused I am. It does not measure whether my confusion is expensive.** Those come apart, and when they do, entropy sends you to the wrong answer. My agent is at the fork.

Entropy still has a job in this project — measuring how many bits a probe removes — but it is not the escalation trigger. **The cost of being wrong is.**

#### The knife-edge

Escalation lives or dies on one number: what it costs to rotate something that did not need rotating.

| Wasted rotation | Max VPI | Escalation ever optimal? |
|---|---|---|
| 20 min | 16.74 | no |
| 30 min | 24.92 | no |
| **~40 min** | **~30** | **the boundary** |
| 50 min | 39.36 | yes |
| 100 min | 67.17 | yes |

I estimated 20–30 minutes. The boundary is about 40. **I am sitting roughly twenty minutes below a result flipping**, on a number that was one of the softest guesses in the whole matrix.

So I asked. A practitioner's answer: already revoked, minutes; never a real key, minutes; a key belonging to a project abandoned two years ago, hours — but no rotation attempted. Another suggested timeboxing at ten to fifteen minutes. Between them that puts me below 40 for practical reasons rather than by assumption, and escalation stays out.

It stays in the action set regardless. Removing it would mean I could not express my own baseline, and "the agent never escalates" is only sayable if it could have.

#### The four policies

The ladder, each rung adding exactly one thing, so the experiment can measure what each one buys:

| | What it uses | Threshold |
|---|---|---|
| **P0** | The prior only, no evidence | none — one action for everything |
| **P1** | Free evidence, Bayes, hand-picked threshold | P(live) > 0.5, because 0.5 feels right |
| **P2** | Free evidence, Bayes, expected cost | **0.06588**, derived |
| **P3** | P2 plus the probe, bought when it pays | Week 2 |

**Baseline:** escalate-everything. Never wrong, always costs a human.

P1 against P2 is the comparison worth running. They see identical evidence and form identical beliefs. The only difference is where the line sits — 0.5 versus 0.06588, a factor of about eight. Every finding I am between 10% and 50% confident about, P1 walks away from and P2 acts on.

That makes the experiment answer something sharper than "does probability help", which is obvious and boring. It answers: **does deriving the threshold from costs, rather than picking a round number, change what the agent does?**

### Feedback

The last of §8's seven parts, and the honest answer is uncomfortable.

| Action | What comes back |
|---|---|
| Rotate safely | The true state, reliably — I look the key up to issue a replacement and find out what it was |
| Revoke now | Whether it was live, via what broke |
| Escalate | The human's answer, if the system captures it |
| **Dismiss** | **Nothing. Ever.** |

Rotating reveals the truth as a *side effect* of acting. Nobody designed that; it falls out of the procedure. Dismissing reveals nothing at all — I close the finding and walk away, and the only way I ever learn a dismissal was wrong is a breach, which is late, expensive and rare.

**That asymmetry is the finding.** An agent learning from its own outcomes would only ever learn about findings it chose to act on. It would get steadily better at keys it rotates and never once discover it was wrong about the ones it dismissed — which are exactly the errors that matter. It would drift toward dismissing, because dismissals never generate contradicting evidence.

Structural confirmation bias, not a bug I could fix by being more careful. So the loop exists and I am documenting why I do not close it.

**Investigate is not part of this table**, and it took me a moment to see why. The other four are terminal — the case closes and whatever comes back arrives afterwards, by accident. Investigate returns *evidence*, immediately, into the same decision. It is not feedback; it is an input, and I have already modelled it in the likelihood tables.

Which points at something worth noticing: **investigate is the only channel whose return I designed.** Everything the other four teach me is a by-product of doing something else.

## Technical Terms

| Term | What it means, as I understand it |
|------|------------|
| Secret scanning | Automatically searching a repository for strings that look like credentials. This is what produces the finding my agent has to act on. |
| Pattern detection | Matching a string against a known key format — a prefix, a length, a character set. Works when the provider publishes a format, useless when they do not. |
| Entropy detection | Scoring how random a string looks and flagging the random-looking ones. Catches keys nobody wrote a pattern for, and also catches every hash and identifier in the repository. |
| Shannon entropy | The measure used for that: how unpredictable a string is. A key looks unpredictable. So does a commit hash. |
| False positive | A finding that is not a credential at all. From what I have read this is the dominant failure of scanners, not missed keys. |
| Key prefix | The provider-assigned start of a key. Some providers publish different prefixes per mode, and then the prefix is free evidence. OpenAI does not — every key starts `sk-` or `sk-proj-`, so for me the prefix separates nothing. |
| Validity check | Asking the provider whether a key still authenticates. Direct, and I have ruled it out — I will not authenticate with a credential I found. |
| Admin key | A separate, higher-privilege credential (`sk-admin-...`) that can ask about other keys. What my probe uses, so I never act as the suspect key. |
| `last_used_at` | The field my probe reads. Unix timestamp of the last authentication, `null` if the key was never used. |
| Rotation | Replacing a credential: revoke the old one, issue a new one, update everything that used it. What "remediate" actually costs in practice. |
| Revocation | Turning a key off. What makes a live key into a dead one. |
| Hidden state | The thing that decides which action is right and that I cannot observe. Here, which of the four kinds of key I am looking at. |
| Prior | What I believe about the hidden state before looking at any evidence from this particular finding. |
| Likelihood | How probable a piece of evidence is under each hidden state. What makes evidence informative or useless. |
| Posterior | What I believe after combining the prior with the evidence. |
| Expected cost | For each action, the average cost across the hidden states, weighted by how likely each state is. The thing I want to minimise. |
| Decision rule | The rule that turns a belief into an action. Mine picks the action with the lowest expected cost. |
| Baseline | The thing I have to beat. Mine is escalate-everything. |
| Deferral | Handing the decision to a human rather than making it. Escalation, priced as an action instead of treated as free. |

I am confident about the first half of this list. The second half I can define but have not used yet, so those definitions may turn out to be too neat once I try to write them down as code.

## Search Queries

The strings I actually typed, and what came back.

| Query | Outcome |
|-------|---------|
| `secret detection tools comparative study precision recall` | The best result of the set — found the nine-tool comparison that gave me real precision figures |
| `SecretBench dataset software secrets` | A labelled dataset, plus a companion collection of false positives |
| `false positives secret detection benchmark` | Overlapped heavily with the two above |
| `secret detection large language models source code` | Recent work on whether an LLM beats regex at this |
| `stripe api key live test prefix documentation` | Confirms that providers publish distinguishable prefixes |
| `how long do leaked API keys stay valid` | Mostly vendor blog posts. Useful as a lead, not as evidence |
| `credential rotation broke production postmortem` | For the cost side. Thin results — this is a question for people, not for search engines |
| `secret scanning triage workflow false positive` | Practitioner write-ups rather than papers |

What I noticed about searching this topic: security-vendor content dominates the results and it is written to sell something. The academic papers were harder to surface and more useful once I found them.

## Verified Reddit Communities

I have verified two of these so far — r/sysadmin and r/devops, by posting in each and getting real answers. For the rest I still need to open each one, check the date of the newest post, read the rules, and see whether a technical question gets answered or removed.

| # | Subreddit | Why It Is Relevant | Verified Active? |
|---|-----------|-------------------|-----------------|
| 1 | r/devsecops | The closest match — people who own scanner tooling and the alert queue it produces | [ ] |
| 2 | r/AskNetsec | Explicitly a question subreddit, so a beginner question is on-topic rather than merely tolerated | [ ] |
| 3 | r/sysadmin | The people who feel the cost when a rotation breaks something. My cost thinking is weakest on that side | [x] — posted, got a substantive reply from a practitioner |
| 4 | r/ExperiencedDevs | Developers who receive these alerts and decide whether to act on them | [ ] |
| 5 | r/devops | Rotation runbooks, and who actually does the rotating | [x] — posted, four substantive replies including the PKI one |
| 6 | r/netsec | Strict and link-oriented. Better for sharing a finished preprint than for asking questions | [ ] |
| 7 | r/cybersecurity | Large and generalist. Useful for the consequence questions, possibly too broad for depth | [ ] |

I already had a post removed by moderation, so before posting again: read the sidebar, lead with the question rather than a link, and check whether the subreddit requires account age or karma.

## Relevant X Accounts

I am not filling in handles I have not opened. Handles change, accounts go quiet, and a wrong `@` in a submitted file is a real error rather than a small one.

Starting points I am confident exist as organisations, whose current handles I will take from their own websites rather than from memory: GitGuardian, Truffle Security (TruffleHog), Gitleaks, GitHub Security, Snyk, Semgrep, HashiCorp Vault, Doppler, OWASP.

How I intend to build the list:

1. Follow those organisations, then look at their engineering and developer-relations staff — those are the accounts that actually reply to people.
2. Search `secret scanning`, `secrets sprawl` and `leaked API key` filtered to Latest, and follow whoever is posting substance rather than marketing.
3. Take the author names from the papers below, search each one, and confirm the account matches their institution page before following.
4. Deliberately include people who are sceptical of scanning, or who think rotation is more dangerous than exposure. My cost reasoning is weakest where the only voices are vendors selling scanners.

Twenty followed. Grouped by what they are for, because the groups are not
equally close to my problem and pretending otherwise would be dishonest.

**Detection and credential state — the core of my problem**

| # | Handle | Area of Expertise | Why Relevant | Verified? |
|---|--------|--------------------|-------------|-----------|
| 1 | `@GitGuardian` | Secrets detection, secrets sprawl research | Publishes the credential-survival figure my prior is built from | [x] |
| 2 | `@trufflesec` | TruffleHog: find, verify and analyse leaked credentials | Verification is their product, so they are the clearest statement of the position my constraint rejects. They have also published static detection of AWS canary tokens and a permissions analyser | [x] |
| 3 | `@semgrep` | Static analysis, AppSec rules | The detection layer my agent takes as given | [x] |
| 4 | `@snyksec` | SCA and secret scanning | One of the tools in the precision comparison I cite | [x] |
| 5 | `@step_security` | GitHub Actions and CI/CD supply chain | Posts on live attacks that harvest CI/CD secrets from runner memory. The closest account on this list to the moment a credential actually leaks | [x] |
| 6 | `@GHSecurityLab` | GitHub's security research | Owns the scanner whose findings are my agent's input | [x] |
| 7 | `@github` | Platform | Publishes the partner-pattern table my premise cites | [x] |
| 8 | `@GHchangelog` | Product changes | Where a change to secret-scanning validity checks would appear first, and such a change would weaken my premise | [ ] |
| 9 | `@owasp` | Application security guidance | Broad, but the community that frames remediation practice | [ ] |
| 10 | `@0xdabbad00` | Scott Piper, independent AWS security | The public-identifier point is his territory: an `AKIA` access key ID is not secret, so key status is readable from your own admin API without touching the secret half | [x] |
| 11 | `@troyhunt` | Have I Been Pwned, breach data | The clearest working example of my unanswered question about who bears the cost of an incorrect action — his entire project exists because third parties carry the loss from someone else's exposure | [x] |
| 12 | `@clintgibler` | tl;dr sec, AppSec research summaries | Reads papers and replies to people. The most likely account on this list to engage with a decision-theoretic argument | [x] |

**Offensive side — the people who find and use the keys**

| # | Handle | Area of Expertise | Why Relevant | Verified? |
|---|--------|--------------------|-------------|-----------|
| 13 | `@Jhaddix` | Bug bounty, recon | Finds exposed credentials as a matter of routine. Useful counterweight to defender assumptions about how long exposure lasts | [x] |
| 14 | `@_JohnHammond` | Malware and incident analysis | Same reason. Attacker-side timelines are the evidence my public-exposure scope condition rests on | [ ] |
| 15 | `@PhillipWylie` | Offensive security, pentesting | Same group | [ ] |

**Prevention and detection-avoidance — the position that my problem should not exist**

| # | Handle | Area of Expertise | Why Relevant | Verified? |
|---|--------|--------------------|-------------|-----------|
| 19 | `@doppler` | Secrets management, credential delivery | Added deliberately as the counter-position. Three people answered my Reddit question about evidence by saying the secret should never have been in the repository. Short-lived credentials are the strongest form of that argument, because they do not merely prevent the leak, they dissolve my hidden state: a credential that expires in an hour is *revoked* by the time anyone triages it | [x] |
| 20 | `@ThinkstCanary` | Canary tokens, deception-based detection | The operational reason my constraint exists, now cited in the limitations. A canary token is a credential designed to be authenticated with, so testing a found key can alert whoever planted it. They also maintain the account IDs that make such tokens detectable offline | [x] |

**Agent construction — relevant to how the agent is built, not to secrets**

| # | Handle | Area of Expertise | Why Relevant | Verified? |
|---|--------|--------------------|-------------|-----------|
| 16 | `@bcherny` | Claude Code | Agent tooling. Not adjacent to my problem domain | [x] |
| 17 | `@hwchase17` | LangChain | Agent frameworks. My one genuine question for this group: where the credential-handling boundary sits when an agent processes a repository, since a commenter asked me directly whether secret values reach a language model | [x] |
| 18 | `@jerryjliu0` | LlamaIndex | Same question | [ ] |

**On the composition of this list, including what it was missing.** My criterion
above says to deliberately include people who are sceptical of scanning, or who
think rotation is more dangerous than exposure. The first eighteen accounts did
not contain one: every account built scanners, broke into things, or built
agents. That is a real bias and I only noticed it when I wrote the groups out.
Entries 19 and 20 were added to correct it — one for the prevention argument
that my problem should not exist, one for the reason my constraint is
operational rather than only ethical.

Still absent and worth noting: `@zricethezav`, who wrote gitleaks, a tool named
in my own precision comparison, and the rest of the secrets-management field
beyond a single representative. One account is representation, not balance.

The three agent-construction accounts are the furthest from my problem and I am
not going to pretend otherwise. They earn their place through one specific
question rather than through the domain: a commenter asked me directly whether
secret values reach a language model, and my answer — that they do not, because
the decision layer is an `argmin` over a cost matrix and only extracted features
cross the boundary — is a claim about agent architecture that the people
building those frameworks are better placed to challenge than anyone else here.

## Useful Papers, Articles, Repositories, or Datasets

| # | Title | Type | Link | Why Useful |
|---|-------|------|------|------------|
| 1 | A Comparative Study of Software Secrets Reporting by Secret Detection Tools | Paper | https://arxiv.org/abs/2307.00714 | Compares nine tools. Precision of 75% for GitHub's scanner, 46% for Gitleaks, and below 7% for five of the nine. Names over-broad regex and entropy scoring as the causes. The most useful thing I have found: there is no such thing as "the" base rate of true positives, because it depends on which scanner fired. |
| 2 | SecretBench: A Dataset of Software Secrets | Dataset | https://arxiv.org/abs/2303.06729 | Labelled secrets from public repositories, with a companion collection of false positives from nine tools. A possible source of realistic cases so I am not inventing all my test data. I need to check the licence and confirm nothing in it is live before touching it. |
| 3 | Secret Breach Detection in Source Code with Large Language Models | Paper | https://arxiv.org/abs/2504.18784 | Asks directly whether an LLM beats regex at this. Reports GPT-4o at 93.29% precision few-shot and a fine-tuned LLaMA-3.1-8B at 0.985 F1, against roughly 50% precision for regex alone on a balanced set. Relevant because it is the obvious alternative to what I am building, and I should be able to say why mine is a different question — it classifies whether a string is a secret, not what to do about it, and it says nothing about live versus dead. |
| 4 | GitHub Docs — Supported secret scanning patterns | Documentation | https://docs.github.com/en/code-security/secret-scanning/introduction/supported-secret-scanning-patterns | The list of providers whose key formats are recognised, and which support validity checking. This is where I go to answer my own provider question, because it shows which providers publish distinguishable formats. |
| 5 | GitGuardian, The State of Secrets Sprawl 2026 | Vendor report | https://blog.gitguardian.com/the-state-of-secrets-sprawl-2026/ | Reports 28.65 million new hardcoded secrets on public GitHub in 2025, and that roughly 64% of credentials found valid in 2022 were still valid in January 2026. That second figure matters to me directly: it means an old commit is weak evidence that a key is dead, which is the opposite of what I assumed. This is a vendor selling secret scanning, so I am treating it as a hypothesis to check rather than as evidence. |
| 6 | Stripe API — API keys, live and test mode | Documentation | https://docs.stripe.com/keys | A concrete provider that issues separate live and test keys with published, distinguishable prefixes. Useful for settling whether all four of my states can occur for a given provider. |

I have read enough of 1, 3 and 5 to describe them as above. I have not read 2 in full, and I will not cite it in the preprint until I have.

## Questions to Answer

Updated after choosing OpenAI. Marked by whether they still block anything.

**Answered, or answered enough to move on**

**1. Which provider?** — **Settled.** OpenAI, and only OpenAI. The reasoning is in the Project Objective section above.

**2. Is last-use data obtainable?** — **Settled.** Yes, via the admin API, second granularity, `null` when never used. Verified against OpenAI's own reference documentation.

**3. What does a bad rotation cost?** — **Partly answered** by a practitioner on r/sysadmin; see `discussion-record.md`. Rotation does break things, and it breaks them when the key had a consumer nobody had documented. I still have no number, only a condition.

**Still open, and I am proceeding without them**

**4. What is the fourth state?** — **Settled in Week 2, and there were two of them.** `other` is the residual I could not characterise, added at 1% of the prior and used as an escalation trigger precisely because I still cannot price it. `zero_scope` — authenticates but is authorised for nothing — came out of splitting `live`, which I had been using to mean two things at once. Neither state changed a single action on its own; the scope field that resolves them is what moved regret from 10.91 to 8.43. See `results/week2-results.md` and `results/scope-probe.md`.

**5. Revoke now, or rotate safely — what decides it?** I have split remediation into two actions on the reasoning that leaving a system broken is not automatically the safe choice. I do not know what real teams weigh when they choose. **This is the question I most want answered**, because it prices two of my five actions.

**6. Is "the key had an undocumented consumer" knowable in advance?** If it is only obvious after the rotation has already broken something, then it cannot be evidence and my agent cannot use it. This changes what I am allowed to model.

**7. How much escalation would a team tolerate?** There is a rate above which an agent has not automated anything. I do not know where it sits. I can sweep it as a parameter, so it is not blocking.

**8. Does "live" need splitting by blast radius?** Stripe's publishable keys are live and safe to expose, which means live and dangerous are different properties. OpenAI's version is an admin key versus a project key. Noted, not solved.

Questions 5 and 6 are the ones I would most like answered before I write the cost model. Neither strictly blocks it — I am estimating everything and reporting a sensitivity analysis regardless — but they would let me sweep a narrower and more defensible range instead of guessing at the whole space.

## The Ten Questions About the Selected Problem

Answered in one place, because they are otherwise scattered across this file and
the paper. Two of them I had not answered anywhere before writing this section.

**What can the agent observe?** The scanner's finding, and the repository around
it. Concretely: the file path, the variable or identifier name, the commit
message, and whether the string matches the published OpenAI project key format.
It can also buy one thing from outside the repository — `last_used_at` from my
own organisation's admin API.

**What information is hidden?** Whether the credential still authenticates.
Nothing in a repository records revocation, because revocation happens at the
provider. This is the whole problem.

**What will a human observe that the agent cannot?** Three things. Whether a key
was discussed in a thread or a ticket the agent cannot read. Whether the team
that owns the repository already knows. And organisational authority — whether
revoking another team's credential is permitted at all, which is a constraint on
the action space rather than a fact about the key. My escalation bound covers a
human acting as a state oracle and says nothing about these.

**What must the agent remember?** Very little in the version I built, and that
is a limitation rather than a design choice. It decides one finding at a time
with no memory between findings. The thing it should remember is a registry of
credentials already rotated, held as salted hashes, because my regret analysis
shows the five costliest errors are the same error five times — rotating a key
that was already dead. A memory of past remediations would catch exactly that
case, and a practitioner independently proposed the same structure.

**When must the agent ask a question?** When buying evidence changes what it
does. That is the EVSI test, and it fires on about 4% of findings. Uncertainty
alone is not the trigger — the agent can be very unsure and still have nothing
worth asking, because a belief far from every boundary cannot be moved across
one. It escalates to a human when the expected cost of doing so is lowest, which
under my cost model never happens while a human interruption costs more than
15.03 minutes.

**Which incorrect action can be corrected?** Rotate-safely and escalate are
recoverable — you spend time you did not need to spend. Revoke-now is
recoverable but expensively, because the outage has already happened by the time
you learn it was unnecessary. Dismiss is the only action that cannot be
corrected by the agent, because nothing revisits a closed finding; the correction
arrives as a breach. That asymmetry is why the dismiss-live cell is priced at
2400 minutes and why the agent, correctly, never reaches it.

**Who has the cost of an incorrect action?** Not the same person for each error,
and this is the part my cost matrix hides by expressing everything in one unit.
Over-remediation is paid by the responder and by whichever team gets the deploy
cycle — engineer-minutes, visible, and internal. Under-remediation is paid by
the organisation and by whoever sits behind the credential, which for a
third-party key includes people who are not in my organisation at all. Summing
both into "engineer-minutes" treats an hour of my time and an hour of somebody
else's exposure as the same quantity, and it is not. Recorded as a limitation.

**Which evidence changes the belief?** The free features move `fake` sharply and
`live`-versus-`revoked` not at all: both real states carry identical likelihoods
on both features, so the ratio stays at 1.778 whatever is observed. Only the
purchased probe touches the axis the decision turns on. Three further channels
would, none of which I model: a secret-store hash comparison, provider inventory
status where the credential format exposes a public identifier, and passive
usage telemetry.

**Is the historical evidence comparable?** Partly, and I have been careful about
this. The scanner-precision figure comes from a nine-tool comparison on a
labelled corpus, which is comparable. The credential-survival figure comes from a
vendor retest of a four-year-old cohort, which is a different population from
freshly flagged findings, so combining the two into one prior mixes sources that
were not measuring the same thing. That is why the prior is swept rather than
asserted.

**How does the agent learn after an action?** In the built version, it does not.
The feedback loop is specified — the outcome of a remediation is observable and
would update the likelihood tables — but nothing implements it, and the
one-shot formulation is the honest ceiling on this project. A sequential version
would find value the current model cannot see, and the rotation that silently
fails on an undocumented consumer is the case that most needs it.

## AI Prompts and Important AI Errors

Where an error changed a published number, I say which.

### Prompts Used

| # | Prompt | Response Summary |
|---|---|---|
| 1 | Research prep: what are the hidden states behind a secret-scanner finding, and what does the field already know | Gave me the scanner-precision literature and the GitGuardian survival figure. Both are now the two factors in my prior |
| 2 | Help me price fifteen cost cells from components rather than writing the cells down directly | Produced the nine-component decomposition. Also produced an arithmetic error I caught (entry 1 below) |
| 3 | Sweep the entire belief simplex and tell me the maximum value of perfect information | Gave 24.64 minutes. Correct for the simplex, wrong for the question I was asking (entry 5) |
| 4 | Work one finding end to end, price the probe before buying it | Produced the §10 decision record. EVSI came out at exactly 0.00, which I did not expect |
| 5 | Review this preprint as a hostile IJCAI reviewer | Four models, four reviews, one verdict of reject. Logged in `review-record.md` |
| 6 | Sample the whole cost model jointly rather than one axis at a time | Produced the robustness analysis, and a sampler bug I did not catch until a fifth review read the code (entry 7) |
| 7 | Verify the author list on every reference against the primary source before I submit anything | Found two fabricated author lists in my own bibliography (entry 11). The most productive single prompt in the project per minute spent |
| 8 | My problem statement says *ignore, verify, remove* and my agent has five actions. Are these the same problem? | Started three rounds of argument that nearly made me rebuild the model. The answer was a relabel and a mapping table, not a rebuild (entry 13) |
| 9 | Rebuild this decision model from scratch with every parameter traced to a published source, and mark the ones that cannot be | Produced an independent parameterisation in dollars rather than engineer-minutes. Its indifference point is 0.079%; my unreachable-dismiss boundary is 0.15%. Two different models, same conclusion — the strongest external check the project has had |
| 10 | My posterior assumes the two free features are conditionally independent. Test what happens when they are not | Produced the shrinkage sweep. The invariance survives at every weight; the *fake* collapse does not (entry 14) |
| 11 | Measure the invariance rather than argue for it, and report it in bits | Mutual information came out at exactly 0.000000. The measurement agrees with the Week 1 proof, which is the point — the proof was untested until now |
| 12 | Rank my available evidence by information, then rank it by value, and tell me whether the orders match | They do not. Near-opposite orders, and the belief where the probe is most informative is the belief where it is worth nothing. Generalised the Week 1 consumer-probe result |
| 13 | The agent is getting 92% of cases right by taking one action on everything. Find the assumption that lets it do that | Found the unstated `p_exploit = 1.0` inside the 2400-minute breach cost. The single most valuable prompt of Week 2 (entry 20) |
| 14 | Generate the test cases from tables the agent does *not* use, and run a second agent that knows the truth | Produced the mis-specification study. Separated the price of being wrong from the price of not knowing (entries 24, 25) |
| 15 | Parameter uncertainty cannot express doubt about a structural constraint. What can? | Bayesian model comparison — a Bayes factor between the invariance and its negation. Neither the sessions nor the brief mention it; it arrived because an experiment found something the existing machinery could not say |
| 16 | Before the paper: run a staleness check across the whole repository | Found three uncommitted commits, a results JSON generated by code that no longer existed, and a result file contradicted by a later one (entries 26, 27) |

### AI Errors

| # | Context | AI Output | What Was Wrong | Correction |
|---|---|---|---|---|
| 1 | Pricing the cost matrix | "Escalate on a live key = 30 + 180 = 150" | The arithmetic does not work, and rotate-safely on live was 120 not 180. I noticed the table and the explanation disagreed | Rotate-safely fixed to 112, escalate to 30 + 112 = 142. Every cell now shows its components |
| 2 | Writing the README | An unprompted "honesty note" saying the repository had been rewritten into a clean order | I had not asked for it, and it framed normal practice as a confession | Removed. Only the pre-registration claim depends on chronology, and that is better made as a property of the committed case file |
| 3 | Writing commit 1 | "This repository will be about twenty commits" | Nobody knows the commit count at commit one. It is a tell that the file was written from the end | Fixed count dropped entirely |
| 4 | Writing commit 1 | A four-part taxonomy of when credential verification is unsafe, and a reference to "an earlier draft" that never existed | Asserted domain knowledge I did not have and cited something imaginary | Rewritten from my own stated reasoning only, with a standing rule: if a sentence needs knowledge I have not demonstrated, cut the sentence |
| 5 | The escalation bound | "Max VPI = 24.64 minutes anywhere on the simplex, so escalation never wins" | True but not the right question. The maximiser sits at a belief my free features make unreachable | **Changed a published number.** The bound at reachable beliefs is 15.03. Same for the decision boundary: 0.09386 on the wrong slice, 0.06588 on the line the agent walks |
| 6 | Comparing policies | P1 defined as "threshold 0.5, else dismiss", reported at +111.4% against the baseline | Confounded. It changed the threshold *and* removed two actions. The catastrophe came from dismissing, not thresholding | **Changed a result.** Same threshold with a revoke fallback beats the baseline by 12.4%. P1 with the full action set costs 77.79, not 181.78 |
| 7 | Monte Carlo sampler | A single lognormal sigma derived from `log(high/low)` | Only correct when the estimate is the geometric midpoint of low and high. Eight of fourteen quantities were not, so the sampled ranges were not the published ones — `human` sampled 8.7–103.9 while claiming 5–60 | Two-piece lognormal: the estimate is the median, low and high are the 5th and 95th exactly. Survival percentages moved by 1–10 points |
| 8 | Monte Carlo output | `json.dump(..., open("../results/...", "w"))` | Relative to the working directory, not the script. Crashed when run from the repository root | Anchored to the script's own directory with `makedirs` |
| 9 | An extension suggested by a reviewer | "Probe which systems consume the credential — it may pay off even when the state is certain" | Plausible and wrong. The consumer hunt appears identically in both remediation actions, so it cannot choose between them | Tested and refuted. The boundary is invariant at 0.06588 for every value of the hunt from 30 to 480 minutes. Recorded as a result |
| 10 | A reviewer's domain claim | "GitHub's validity checks make your premise false — the scanner tells you if the key is live" | Half right. GitHub does run validity checks, but its own pattern table marks OpenAI API Key as a partner pattern **without** validity-check support | Rejected on the facts, and the check now appears in §2 as a citation defending the premise. The same reply's *other* point — that OpenAI being a partner means public-repo leaks get reported and revoked — was accepted |
| 11 | Building the bibliography | Two reference entries with confident, complete, wrong author lists: the ESEM secret-detection study attributed to Lorenzo Neil, and arXiv:2504.18784 attributed to an invented "Islam, Md. Nazmul" | The first copied the author list from a *different* paper by the same first author. The second was fabricated outright. Both looked exactly like the correct entries around them | Verified every entry against arXiv. Cox for the first, Rahman et al. for the second. The lesson is that a citation is the easiest thing for a model to invent and the hardest for a reader to check |
| 12 | Compiling the bibliography | Editorial reminders left in `note` fields — "Verify author list before submission" — printed inside the reference list in the PDF | `named.bst` renders `note`. The reminder about checking my references was itself published as a reference | Moved to `%` comments. Caught by reading the compiled PDF rather than the source |
| 13 | Reframing to the problem statement | "Your hidden state is wrong. *Possible secret* means the state is real-versus-placeholder; collapse live and revoked and rebuild" | Read one word of the problem statement and ignored the one next to it. *Verify* sits in the same action list and only makes sense against a state the free evidence cannot settle. A second model, reading the paper cold, took *verify* to mean exactly my live/revoked probe | Reversed. The model was never wrong; what was missing was a sentence mapping my five actions onto the three. **Nearly cost a rebuild of a working model on the strength of a misread.** |
| 14 | Testing conditional independence | Nothing — this is an error the *test* found in my own published number | My §4.3 reports *fake* collapsing from 0.25 to 0.011 under the naive independent product. The two features are correlated: a `tests/fixtures/` path and a placeholder-looking name are close to one observation counted twice | **Changed how a published number is stated.** A 20% shrinkage doubles it to 0.022 and a 50% shrinkage gives 0.058. The 0.011 is now reported as the favourable end of a range. The live/revoked invariance is untouched at every weight, because it comes from two rows being equal rather than from independence |
| 15 | A review of my robustness table | "The policy ordering P2 < P0 < P1 < baseline is robust across 98.64% of joint perturbations" | 98.64% is real but belongs to a single pairwise claim — P2 beating the baseline under sweep B. The compound ordering is limited by its weakest link, P0 beating the baseline at 79.20%, and P1 was never in that sweep at all | Rejected before it reached the paper. A correct number attached to the wrong claim is harder to catch than a wrong number, because checking the figure against the results file confirms it |
| 16 | Three separate review outputs | Repeated proposals to classify the key by whether the provider returns 403 rather than 401, framed as passive metadata | That requires sending the found credential to the provider. It is the one thing the paper forbids, and one of the same models had criticised a different answer for proposing it two messages earlier | Rejected each time. Also corrected the reasoning: a zero-scope key does not shift the belief, it lowers the breach cost — a cost-matrix change, not evidence. Recorded because a constraint stated in the abstract was violated three times by models that had read the abstract |
| 17 | Checking someone else's review | "The cost matrix has 12 cells built from 8 components, not 15 and 9" | My own paper says fifteen and nine and my own paper is right: the table includes the investigate row, and the consumer hunt is priced twice, documented and undocumented. The count came from the code's `K` dictionary rather than from the paper | The review being corrected was right and the correction was wrong. Logged because it is the failure mode of checking a claim against the nearest artefact instead of the one the claim was about |
| 18 | Writing `shrinkage.py` | `OUT = os.path.join(HERE, "results")` | The same class of bug as entry 8, eight rounds later. Every other script writes to `HERE/../results`; this one would have written to `experiments/results/` once it was in the repository, and worked in the flat scratch directory purely by accident | Fixed to match the existing convention. Caught by a full file audit rather than by running it |
| 19 | Valuing the live-versus-revoked axis | "Perfect knowledge of live vs revoked is worth 61.3% of total regret" | Confounded, and in the same shape as entry 6. It compared an agent *with* the probe against an oracle *without* it — two changes at once | **Changed a number I was about to publish.** The correct figure is 82.1%. `results/cost-sensitivity.md` carries a visible correction block rather than a silent edit, because 61.3% had already been quoted elsewhere |
| 20 | Auditing the cost matrix | The 2400-minute price for dismissing a live key, presented as "a breach and its cleanup" | It was a breach cost times an unstated certainty of exploitation. Week 1 had been running at p = 1.0 without writing it down, and nothing about the number 2400 looks like a probability, so nothing prompted the check | **The most consequential fix in the project.** Making it explicit at p = 0.10 took `fake` recall from 0.000 to 0.954 and balanced accuracy from 0.300 to 0.467 |
| 21 | Applying the p_exploit fix | The fix appeared to do nothing | The residual state's price is derived from the breach cost and was not recomputed. `dismiss` on `other` stayed at 602 minutes and blocked every dismissal the fix existed to unlock | Recomputed. **A derived quantity that is not recomputed looks exactly like a fix that did not work**, which is why the comment explaining it stays in `costs()` |
| 22 | Reading the cost-cell sweep | Cells reported as improvements | Exact ties were being counted as improvements | Fixed with an epsilon threshold |
| 23 | Advice on mis-pricing | "When in doubt, guess high on the costs" | Contradicted by the table directly beneath it. Over-pricing the *default* action and under-pricing an *alternative* are the two dangerous directions; the rule is per-action, not global | Replaced with the per-action rule |
| 24 | First run of the drift alarm | "The Jensen–Shannon alarm does not work" | Declared off a single seed with an uncalibrated threshold | Wrong. A held-out threshold sweep gives 100% detection at a 500-case window, 0% false positives |
| 25 | Predicting the mis-specification result | "Wrong base rates will cost more than wrong likelihoods" | The table shows the reverse: +0.41 for the prior against +1.20 for the likelihoods. Free evidence washes out a wrong prior; nothing washes out a wrong likelihood, because the likelihood is what does the washing | Prediction removed from the write-up and the finding stated as measured |
| 26 | Designing the W2-8 feedback test | "The discovery process will deliver about 2.5× as many revoked labels as live, and that skew is the difficulty" | Measured 1.5×, and the matched control showed the skew costs no sensitivity at all — biased and unskewed samples of the same size detect the same smallest difference. **The experiment's own premise was wrong** | Rewritten. The finding is that sample size costs everything and skew costs nothing, which is the opposite of what it was built to show, and more encouraging |
| 27 | Attributing the scope field's value | "The scope field earns its place by detecting `zero_scope`" | 88% of the value is present at q = 0.02, where the field cannot see `zero_scope` at all. It is mostly a `fake` detector, via the `absent` column I copied rather than the number I invented | Corrected. **The stated reason a design change works is not always the reason it works**, and only sweeping the parameter away showed which was which |
| 28 | Reporting Week 2 status | "W2-6, W2-7 and W2-8 are committed and pushed" | They were on disk only. The reflog ended at W2-5, and `results/registry.json` had been generated by a version of `registry.py` that no longer existed, so it disagreed with its own markdown | Caught by a staleness audit that re-ran every script in a clean tree and diffed the output. Committed, and the JSON regenerated |
| 29 | Writing the Week 2 abstract | "Making p_exploit explicit at 0.10 took fake recall from 0.000 to 0.954" | Credits one fix with three fixes' work. `fixes.json` says fix 1 alone gives 0.588; 0.954 needs the escalation rule and the scope field too. The decomposition was in my own results file the whole time | **Changed a headline.** Abstract and §10 rewritten; the figure now has three bars instead of two |
| 30 | The policy ladder | P1 reported at 114.12 minutes of regret, "nine times worse" than acting on expected cost | Scored against the 2400-minute cell that the same paper spends a section repudiating. Rescored on the corrected matrix P1 is 13.89, so the true factor is 1.27. P0, P2 and P3 were unaffected because none of them ever dismisses a live key, which is exactly why nothing looked wrong | **Changed a headline.** Every row now scored on one matrix, and the correction is stated in the section rather than silently applied |
| 31 | Writing the failure section | The drift alarm's "100% detection at a 500-window" attached to the belief drift in P(live) | A detection rate from one experiment attached to a failure from another. `feedback.md` says the alarm watches the free features, which carry zero bits about live versus revoked — the exact axis the drift is on. My own file contradicted the claim in the file the number came from | **Changed a claim.** The paper now says the agent has a working alarm for the cheap drift and none for the expensive one |
| 32 | Writing Results from the results files | The P3 negative result omitted entirely | `week2-results.md` has a section headed "the probe did not pay for itself" — P3 spends 0.132 min and recovers 0.066, ending behind P2. The paper's ladder had no cost column, so it could not be seen | Restored as a finding, with the cost column that makes it visible |
| 33 | `feedback.py` | `if learn and rng.random() < discovery_p(...)` | Short-circuit. The frozen arm never consumes the discovery draw, so from the first live case the two arms simulate different 4,000-finding worlds. The published "learning saves 0.57 min/finding" was entirely stream divergence | **Deleted a result.** Paired, both arms cost 60.4703. The learned prior changes the action on 0 of 4000 findings, so a difference was impossible |
| 34 | `registry.py` | One `random.Random(4242)` shared by the age, scope and registry draws | An arm that switches a channel off consumes fewer draws and therefore sees different observations on the channels it still has. At c = 0.5 the age rows are identical across states — provably uninformative — and the table still showed it moving regret by −0.8%. That was the stream, not the evidence. The docstring directly above the bug warns about this exact confound | One stream per channel. Age-only at c = 0.5 is now exactly 0.0% |
| 35 | `scope_probe.evsi()` | Signature takes no cost matrix and falls through to the module global | So the best agent in the project decided what to *buy* under `dismiss\|live` = 2400 and what to *do* under 244.5 — the assumption the whole commit removes, left running in the half of the decision nobody inspected. The probe purchase rate was 0.468 for all 75 perturbed matrices in the cost sweep and nobody asked why a sweep produced a constant | Threaded through. "6 of 15 cost cells do not matter" became 3 of 15 |
| 36 | Assessing the review rounds | "The reviews that read only the paper missed what the code reviewers found" | Wrong, and the user caught it. The evaluative round had full code access, reran four scripts, and cited line numbers in files nobody had pointed it at. The difference was the brief, not the access — it ran a *reproduction* check, and every defect found was deterministic and reproduces byte-identically forever | Corrected in `review-record.md`. The sharper lesson: reading the code is not sufficient either, you have to be told what class of thing to look for |

**What I take from this table.** Fourteen of the thirty-six changed a published
number or a published claim, and most of those were found by an AI reviewing
another AI's work, or by an experiment contradicting the write-up that had been
built around it, rather than by me reading carefully.

The errors sort into three kinds, and the split is more useful than the count.

**Arithmetic and plumbing** — entries 1, 8, 18, 21, 22, 33, 34, 35. This is now the largest class, and Week 2's three are all the same shape: a random-number stream or a cost matrix silently shared where two things were meant to be independent. None of them would fail a test that checks the output is reproducible, because all three reproduce perfectly. Cheap to fix, always
caught eventually, and caught by running things rather than by reading them.

**Confident claims about things nobody checked** — entries 4, 11, 12, 17, 28, 36.
Fabricated author lists, an imaginary earlier draft, a cell count contradicted by
my own paper, three commits reported as pushed that were sitting on disk. These
are the ones that would have survived into a submission, because they read
exactly like the true sentences around them.

**A number moved from a results file into a sentence it does not support** — entries 29, 30, 31, 32. This class did not exist until I wrote the paper, and it is now the most dangerous one: in all four cases the results file was *more careful than the paper written from it*. The measurement was right and the write-up was wrong.

**Predictions stated before the measurement, then not revisited** — entries 19,
23, 24, 25, 26, 27. This is the class that grew in Week 2 and the one I now
watch for. Every entry in it has the same shape: a claim made while designing the
experiment, left in the write-up, and falsified by the experiment's own output.
The 2.5× skew that measured 1.5×, the scope field's value attributed to the
wrong column, the base-rate prediction that came out backwards, the "undetectable"
failure that W2-8 detected in 100% of runs. Nothing external is needed to catch
any of them — the contradicting number is already in the file.

The two I caught unaided (1 and 3) were both cases where a document contradicted
itself on its own page. That is still the only class of error I reliably notice
without running something.
