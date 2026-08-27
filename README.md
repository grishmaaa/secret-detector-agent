# Deciding what to do about a possible key in a repository

A cost-aware triage agent for secret-scanner findings. Week 1 project for the AI-native engineering cohort.

## The problem

A scanner reads a repository and reports that some string in it looks like a key. That is the entire input. It does not say what kind of key, and it does not say whether the key works.

> The agent observes a scanner result reporting that a string in the repository looks like an OpenAI key. It must select **dismiss**, **investigate**, **escalate**, **revoke now**, or **rotate safely**, because whether that string is a live key, a revoked key, or a fake key hard-coded by a developer is not known.

Three things the string could turn out to be:

1. **A live key** — still authenticates. Whatever sits behind it is reachable by anyone holding the string.
2. **A revoked key** — was real once, no longer works. Harmless now.
3. **A fake key** — hard-coded by a developer, never authenticated against anything.

I am not confident that list is complete. I think there may be a fourth case: a string that is not a key at all and just happens to look like one, because something else in the code needed a long random-looking string. I cannot characterise it well enough yet to put it in the list, so I have left it out rather than guessing at it.

The five actions:

- **Dismiss** — do nothing.
- **Investigate** — buy more information. The agent still makes the decision afterwards, and it can still escalate later if what it learned did not settle anything.
- **Escalate** — hand it to a human. The human makes the decision.
- **Revoke now** — kill the key immediately. Fast, certain, and it breaks anything still using it.
- **Rotate safely** — issue a replacement, update whatever used the old key, confirm nothing is still calling it, then revoke. No outage, but it costs a deploy cycle.

Investigate and escalate are separate because of who owns the decision afterwards. Revoke-now and rotate-safely are separate because leaving a system broken in order to be safe is not automatically the right call, and an agent that cannot express that difference cannot help me decide.

Revocation is the only thing that makes an exposed string worthless — deleting it from the file achieves nothing, since it stays in the git history and in every clone anyone made. My agent does not perform any of this. It decides whether the expensive human procedure is warranted. Triage, not repair.

## Scope

**Findings originate in a repository.** Not cloud configuration, not credentials in a running process. This scopes where the decision starts. It does not mean the agent may only look at the repository — investigate is precisely the action that reaches outside it.

**One provider: OpenAI.** I started intending to use two — one that issues test keys and one that does not — and dropped it because the complexity was compounding faster than the insight. OpenAI issues no separate test key, which is why my state space is three rather than four. The trade is deliberate: I gave up a state to gain a probe I could verify.

**One finding at a time.** The agent decides about a single flagged string, not whether a whole repository is compromised.

**It is a simulation.** No admin credential, no live API calls. Every likelihood is my estimate rather than a measurement, so the honest result is a sensitivity analysis, not a point estimate.

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
| §4 research file | **Mostly done** — terms, queries, sources and questions written. The Reddit and X tables are candidates only; nothing verified yet |
| §5 Reddit discussions | **Started** — two posts, five substantive replies. The targets are ten contributions across five communities |
| §6 X discussions | **Not started** |
| §7 discussion record | **Started** — two threads logged, both with design consequences |
| §8 agent design | **Fully designed, nothing built** — all seven parts settled: input, hidden states, beliefs, actions, costs, policy, feedback. No code exists yet |
| §9 experiment | Not started |
| §10 probability decision record | **Done** — one finding worked end to end in `decisions/` |
| §11 AI reviews | Not started — template |
| §13 preprint | Not started |
| §14 publication | Not started |

The public-discussion requirements — §5 and §6 — are essentially unmet, and I would rather say so on the front page than let a marker discover it. They are also the requirements nobody else can do for me, and the ones the cost numbers this agent depends on are supposed to come from. Every other gap above is work I know how to do; that one is not. It is also the reason every number in my cost model is currently invented — those figures are supposed to come from people who have done this, and so far one person has told me anything.
