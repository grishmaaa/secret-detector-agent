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

| Term | Definition |
|------|------------|
|      |            |
|      |            |
|      |            |

## Search Queries

- [ ] _Query 1_
- [ ] _Query 2_
- [ ] _Query 3_
- [ ] _Query 4_
- [ ] _Query 5_

## Verified Reddit Communities

> Remove a community if it is inactive or not relevant.

| # | Subreddit | Why It Is Relevant | Verified Active? |
|---|-----------|-------------------|-----------------|
| 1 |           |                   | [ ]             |
| 2 |           |                   | [ ]             |
| 3 |           |                   | [ ]             |
| 4 |           |                   | [ ]             |
| 5 |           |                   | [ ]             |

## Relevant X Accounts

> Remove an account if its content is not relevant.

| # | Handle | Area of Expertise | Why Relevant | Verified? |
|---|--------|--------------------|-------------|-----------|
| 1 |        |                    |             | [ ]       |
| 2 |        |                    |             | [ ]       |
| 3 |        |                    |             | [ ]       |

## Useful Papers, Articles, Repositories, or Datasets

| # | Title | Type | Link | Why Useful |
|---|-------|------|------|------------|
| 1 |       |      |      |            |
| 2 |       |      |      |            |
| 3 |       |      |      |            |
| 4 |       |      |      |            |
| 5 |       |      |      |            |

## Questions to Answer

-
-
-

## AI Prompts and Important AI Errors

### Prompts Used

| # | Prompt | Response Summary |
|---|--------|-----------------|
| 1 |        |                 |

### AI Errors

| # | Prompt/Context | AI Output | What Was Wrong | Correction |
|---|---------------|-----------|---------------|------------|
| 1 |               |           |               |            |
