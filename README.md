# Deciding what to do about a possible key in a repository

A cost-aware triage agent for secret-scanner findings. Week 1 project for the AI-native engineering cohort.

## The problem

A scanner reads a repository and reports that some string in it looks like a key. That is the entire input. It does not say what kind of key, and it does not say whether the key works.

> The agent observes a scanner result reporting that a string in the repository looks like a key. It must select **dismiss**, **investigate**, **escalate**, or **remediate**, because whether that string is a live production key, a dead production key, a provider-issued test key, or a fake key hard-coded by a developer is not known.

Four things the string could turn out to be:

1. **A live production key** — real, still authenticates, with real consequences behind it.
2. **A dead production key** — was real once, no longer works.
3. **A provider-issued test key** — the API provider hands these out for testing. They do authenticate, but against a sandbox.
4. **A fake key** — hard-coded by a developer, never authenticated against anything.

I am not confident that list is complete. I think there may be a fifth case: a string that is not a key at all and just happens to look like one, because something else in the code needed a long random-looking string. I cannot characterise it well enough yet to put it in the list, so I have left it out rather than guessing at it. It is one of the things I want to ask about on Reddit.

The four actions:

- **Dismiss** — do nothing.
- **Investigate** — buy more information. The agent still makes the decision afterwards, and it can still escalate later if what it learned did not settle anything.
- **Escalate** — hand it to a human. The human makes the decision.
- **Remediate** — rotate the key.

Investigate and escalate are separate actions because of what happens after them. After investigating, the agent still owns the decision. After escalating, it does not. Folding the two together would hide the difference between spending my own effort and spending someone else's.

## Scope

**Repository level only.** Not cloud configuration, and not credentials in a running process. I wanted something small enough to test and small enough to understand, and the repository is where I can actually see what is going on. The other levels are possible later if there is time.

**A restricted set of providers and key types**, not every key a repository might contain. Telling different providers' key formats apart is substantial work on its own, and the states depend on the provider anyway — so narrowing this is not just a convenience.

**One finding at a time.** The agent decides about a single flagged string. It does not decide whether a repository as a whole is compromised.

I have not chosen the providers yet. The criterion I settled on is to pick providers where all four states can genuinely occur, and to check that they can before committing to them.

## Objective

The baseline is what a person actually does today: find a key, hand it to a human to check whether it is live, act on what they say.

The important property of that baseline is that it is never wrong about the state. A human resolves it correctly every time. So there is no accuracy for the agent to win — it cannot beat a procedure that is already right. The only thing left to compete on is cost: how many human interruptions get spent getting to the same answer. That is why this project is built on cost rather than accuracy, and why reporting an accuracy figure would be close to meaningless here.

So the objective is:

**Does a probabilistic, cost-aware policy reach the same decisions as escalate-everything while spending fewer human interruptions — and under what conditions does it stop doing so?**

The second half is the part I care about. A rule that wins under every assumption I could vary would be evidence that I had built the comparison badly, not evidence that the agent is good.

## Status

| Assignment deliverable | Status |
|---|---|
| §3 problem statement | **Done** — stated above and in `research-file.md` |
| §4 research file | Not started — only the problem and objective sections are filled |
| §5 Reddit discussions | **Not started** |
| §6 X discussions | **Not started** |
| §7 discussion record | Not started — template |
| §8 agent design | Not started |
| §9 experiment | Not started |
| §10 probability decision record | Not started — template |
| §11 AI reviews | Not started — template |
| §13 preprint | Not started |
| §14 publication | Not started |

The public-discussion requirements — §5 and §6 — are essentially unmet, and I would rather say so on the front page than let a marker discover it. They are also the requirements nobody else can do for me, and the ones the cost numbers this agent depends on are supposed to come from. Every other gap above is work I know how to do; that one is not.
