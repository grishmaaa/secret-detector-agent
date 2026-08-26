# Research File

## Problem Statement

> The agent observes a scanner result reporting that a string in the repository looks like an OpenAI key. It must select **dismiss**, **investigate**, **escalate**, **revoke now**, or **rotate safely**, because whether that string is a live key, a revoked key, or a fake key hard-coded by a developer is not known.

### Why the hidden state is not "is this a secret"

My first attempt at the hidden state was "is this string a secret or not". I dropped it because the scanner has already answered that — reporting that a string looks like a key is the whole of what it does. Restating its output as my hidden state would mean the agent adds nothing. It is also not what makes the decision hard. What I cannot see is what the key *is*, and the scanner does not tell me: it does not say what kind of key it found, and it does not say whether the key works.

### The three states

1. **A live key.** Still authenticates. Whatever sits behind it is reachable by anyone who has the string.
2. **A revoked key.** Was real once, no longer works. Harmless now.
3. **A fake key.** Hard-coded by a developer, never authenticated against anything.

The decision is hard because the actions I would take differ across them and what I can see does not tell me which state I am in.

**I am not confident this list is complete.** I think there is probably a fourth case: a string that is not a key at all, that just happens to look like one because something else in the code needed a long random-looking string. I have not worked out how to characterise it — what it would look like, or how it would differ from a fake key in anything I can observe — so I have left it out rather than inventing a definition for it. I want to ask about it rather than name it myself and be wrong.

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

Every one of those mostly attacks **fake**. Nothing free separates live from revoked. So my free evidence and my probe are strong at opposite ends of the state space, and the pair that matters most — live versus revoked — is exactly where I am thinnest. That is uncomfortable and I think it is the real shape of the problem rather than a gap in my design.

### Two things I learned from Stripe's documentation and kept

I read Stripe's key documentation before dropping it, and two things there are worth carrying even though I am not using the provider.

**`pk_live_` is safe to expose.** Stripe's publishable keys are meant to sit in front-end code. A `pk_live_` in a repository is a live production key and finding it is not an incident. So "live" and "dangerous" are not the same property, and my state 1 currently bundles them. Whether blast radius needs to be a separate axis is open — OpenAI's version of the question is an admin key versus a project key.

**The cost of a wrong remediation belongs to the provider, not to the problem.** Stripe gives a seven-day grace period on rotation — old and new keys both work while you migrate. OpenAI revokes in seconds, with no grace. The same mistake costs wildly different amounts depending on who issued the key. My provider choice made remediation harder, and that is worth knowing rather than discovering later.

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

I have only verified one of these so far — r/sysadmin, by posting there and getting a real answer. For the rest I still need to open each one, check the date of the newest post, read the rules, and see whether a technical question gets answered or removed.

| # | Subreddit | Why It Is Relevant | Verified Active? |
|---|-----------|-------------------|-----------------|
| 1 | r/devsecops | The closest match — people who own scanner tooling and the alert queue it produces | [ ] |
| 2 | r/AskNetsec | Explicitly a question subreddit, so a beginner question is on-topic rather than merely tolerated | [ ] |
| 3 | r/sysadmin | The people who feel the cost when a rotation breaks something. My cost thinking is weakest on that side | [x] — posted, got a substantive reply from a practitioner |
| 4 | r/ExperiencedDevs | Developers who receive these alerts and decide whether to act on them | [ ] |
| 5 | r/devops | Rotation runbooks, and who actually does the rotating | [ ] |
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

| # | Handle | Area of Expertise | Why Relevant | Verified? |
|---|--------|--------------------|-------------|-----------|
| 1 |        |                    |             | [ ]       |

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

**4. What is the fourth state?** A string that is not a credential at all. I still cannot characterise it. Not blocking — I am building with three and will add it if someone names it properly.

**5. Revoke now, or rotate safely — what decides it?** I have split remediation into two actions on the reasoning that leaving a system broken is not automatically the safe choice. I do not know what real teams weigh when they choose. **This is the question I most want answered**, because it prices two of my five actions.

**6. Is "the key had an undocumented consumer" knowable in advance?** If it is only obvious after the rotation has already broken something, then it cannot be evidence and my agent cannot use it. This changes what I am allowed to model.

**7. How much escalation would a team tolerate?** There is a rate above which an agent has not automated anything. I do not know where it sits. I can sweep it as a parameter, so it is not blocking.

**8. Does "live" need splitting by blast radius?** Stripe's publishable keys are live and safe to expose, which means live and dangerous are different properties. OpenAI's version is an admin key versus a project key. Noted, not solved.

Questions 5 and 6 are the ones I would most like answered before I write the cost model. Neither strictly blocks it — I am estimating everything and reporting a sensitivity analysis regardless — but they would let me sweep a narrower and more defensible range instead of guessing at the whole space.

## AI Prompts and Important AI Errors

### Prompts Used

| # | Prompt | Response Summary |
|---|--------|-----------------|
| 1 |        |                 |

### AI Errors

| # | Prompt/Context | AI Output | What Was Wrong | Correction |
|---|---------------|-----------|---------------|------------|
| 1 |               |           |               |            |
