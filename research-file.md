# Research File

## Problem Statement

> The agent observes a scanner result reporting that a string in the repository looks like a key. It must select **dismiss**, **investigate**, **escalate**, or **remediate**, because whether that string is a live production key, a dead production key, a provider-issued test key, or a fake key hard-coded by a developer is not known.

### Why the hidden state is not "is this a secret"

My first attempt at the hidden state was "is this string a secret or not". I dropped it because the scanner has already answered that — reporting that a string looks like a key is the whole of what it does. Restating its output as my hidden state would mean the agent adds nothing. It is also not what makes the decision hard. What I cannot see is what the key *is*, and the scanner does not tell me: it does not say what kind of key it found, and it does not say whether the key works.

### The four states

1. **A live production key.** Real, still authenticates, with real consequences behind it.
2. **A dead production key.** Was real once, no longer works.
3. **A provider-issued test key.** The API provider hands these out for testing. They do authenticate, but against a sandbox.
4. **A fake key.** Hard-coded by a developer, never authenticated against anything.

Those four are what I can currently describe well enough to build on. The decision is hard because the actions I would take differ across them and what I can see does not tell me which state I am in.

**I am not confident this list is complete.** I think there is probably a fifth case: a string that is not a key at all, that just happens to look like one because something else in the code needed a long random-looking string. I have not worked out how to characterise it — what it would look like, or how it would differ from a fake key in anything I can observe — so I have left it out of the list rather than inventing a definition for it. This is one of the things I want to ask about on Reddit. I would rather have the state named by someone who has seen it than name it myself and be wrong.

### The number of states depends on the provider

Working through the list, I noticed that state 3 is not universal. Some API providers issue a separate test key, and for those providers a provider-issued test key is a genuinely distinct thing the string could be. For providers that do not issue one, that state simply does not exist and the space collapses.

That was not what I expected to find, and it changes what choosing providers means. Picking which providers to work with is not only a question of which key formats I can recognise — it is partly a decision about what my hidden states even are. A provider set chosen carelessly could leave me with a state that never occurs in my own data.

### The four actions

- **Dismiss** — do nothing.
- **Investigate** — buy more information. The agent still makes the decision afterwards, and it may still escalate later if what it learned did not resolve the uncertainty.
- **Escalate** — hand it to a human. The human makes the decision.
- **Remediate** — rotate the key.

There is a rule that follows from having investigate as an action at all: **investigating is only worth doing if the action might change afterwards.** If I investigate and then take the action I would have taken anyway, the investigation was wasted. That is easy to write down and I expect it to be the thing that is hardest to get right in practice.

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

Three decisions, each with a reason I want on the record:

- **Repository level only** — not cloud configuration, and not credentials in a running process. I wanted something small enough to test and small enough to understand, and the repository is where I can actually see what is going on. The other levels are possible later if there is time.
- **A restricted set of providers and key types**, rather than every key a repository might contain. Telling different providers' key formats apart is substantial work in itself, and the states depend on the provider anyway, so this is not only about keeping the workload down.
- **One finding at a time.** The agent decides about a single flagged string, not about whether a whole repository is compromised.

**Which providers is still open.** The criterion I settled on is to pick providers where all four states can genuinely occur, and to verify that they can before committing to them rather than assuming it. Until that check is done I am not fixing the provider list.

## Technical Terms

| Term | What it means, as I understand it |
|------|------------|
| Secret scanning | Automatically searching a repository for strings that look like credentials. This is what produces the finding my agent has to act on. |
| Pattern detection | Matching a string against a known key format — a prefix, a length, a character set. Works when the provider publishes a format, useless when they do not. |
| Entropy detection | Scoring how random a string looks and flagging the random-looking ones. Catches keys nobody wrote a pattern for, and also catches every hash and identifier in the repository. |
| Shannon entropy | The measure used for that: how unpredictable a string is. A key looks unpredictable. So does a commit hash. |
| False positive | A finding that is not a credential at all. From what I have read this is the dominant failure of scanners, not missed keys. |
| Key prefix | The provider-assigned start of a key, such as Stripe's `sk_live_` and `sk_test_`. Free evidence — it separates test from production without asking anyone. |
| Validity check | Asking the provider whether a key still authenticates. The only thing I know of that separates a live key from a dead one. |
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

Ordered by how much the answer would change what I build.

**1. Which providers should I work with?**
The criterion I settled on is that all four of my states have to be able to occur — which means the provider issues a separate test key, and I can tell live from test by looking. This is the one blocking my scope, and it is answerable from provider documentation rather than from people. Doing it first.

**2. What does a person actually do when a scanner flags a key?**
My baseline is a guess: find it, hand it to someone to check whether it is live, act on what they say. If that is not what people really do, my baseline is wrong and everything I measure against it shifts. Asking on Reddit.

**3. What is the fifth state?**
I think there is a category of string that is not a credential at all and only looks like one, but I cannot characterise it well enough to put it in the list. I would rather have it named by someone who has seen it in a real queue than invent a definition.

**4. Is there any way to tell a live key from a revoked one without calling the provider?**
This is the crux. If the answer is yes, most of my uncertainty disappears and the project shrinks. If it is no, then that pair is the irreducible part of the problem and the reason the baseline has to phone a human.

**5. What does a bad rotation actually cost?**
I need a number, or at least a story, for what happens when someone rotates a key that something still depended on. I have no basis for this at all right now, and it is one half of the trade-off the whole agent is built around.

**6. How much escalation would a real team tolerate?**
If an agent handed back half its findings for a human to check, would anyone keep using it? There is a rate above which the agent has not automated anything, and I do not know where it is.

**7. Can I actually observe how a key was last used?**
This came out of a Reddit reply rather than from me: log which consumer last authenticated with the credential, so that rotating is a decision rather than a bet. It would speak to live-versus-dead, which nothing else I have does, and it would also tell me what breaks if I rotate. But it is not free the way a prefix is — the prefix sits in the string, and usage data sits with the provider. So I need to know whether that data is exposed at all, for which providers, and how much work it takes to get. If it turns out to be unavailable, the agent has to reason without it, and I would rather find that out now than design around evidence I cannot obtain.

Questions 1 and 7 are for documentation. Questions 2 to 6 are for people, which means they need to be asked early — replies take days and I cannot write the cost model without 5. Question 5 is now partly answered; see `discussion-record.md`.

## AI Prompts and Important AI Errors

### Prompts Used

| # | Prompt | Response Summary |
|---|--------|-----------------|
| 1 |        |                 |

### AI Errors

| # | Prompt/Context | AI Output | What Was Wrong | Correction |
|---|---------------|-----------|---------------|------------|
| 1 |               |           |               |            |
