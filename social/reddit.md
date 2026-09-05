# Reddit

What I asked, where, why, and what it changed. The full threads and the replies
are in `discussion-record.md`; this file is the plan behind them.

## The five questions, and why these five

Written 17/08/26, before posting anything. Each one came from a place where my
own reasoning had stopped rather than from a list of things it would be nice to
know. Ordered by what unblocked me soonest.

**1. What actually happens today?** — validates the baseline.

> When a scanner flags a possible key in your repo, what do you actually do
> next? I want to know the real procedure, not the ideal one.

My whole objective rests on the claim that the current procedure is *hand it to
a human to check*. That was a guess. If it is wrong, the baseline is wrong and
every saving I report is measured against something that does not exist.

**2. The fifth state** — the one I could not characterise.

> A scanner flags a string. I can describe four things it turns out to be: a
> live production key, a dead one, a provider-issued test key, or something a
> developer hard-coded that was never real. What am I missing? I suspect there
> is a category of *not a credential at all* but I cannot characterise it.

I would rather have this named by someone who has seen it than invent a
definition and build likelihoods on it.

**3. Live versus dead** — the crux.

> Is there any way to tell a live key from a revoked one without calling the
> provider? Or is that always a phone-a-friend?

If anyone said yes, the problem shrinks to nothing and the project needs
rethinking. Worth finding out early rather than late.

**4. The cost of a bad rotation** — the cost matrix needs it.

> Has rotating a key ever broken something for you? Roughly what did it cost,
> and was the key one anybody had documented?

**5. Escalation tolerance** — sets the target.

> If a tool handed you 50% of alerts to check by hand, would you still use it?
> Where is the cutoff before you switch it off?

## Where, and why there

| Community | Questions | Why |
|---|---|---|
| r/devsecops | 1, 2, 5 | Closest match — people who own the alert queue |
| r/AskNetsec | 2, 3 | Explicitly for questions |
| r/sysadmin | 4 | They feel the outage side, which security people under-weight |
| r/ExperiencedDevs | 1, 5 | They receive the alerts and push back |
| r/sre, r/devops | 4, 5 | Rotation runbooks live here |
| r/netsec | — | Strict. For the finished preprint, not for questions |

## How I posted, after being removed once

My first attempt was removed. What changed: read the sidebar rules first, lead
with the question rather than a repo link, check whether the sub requires
account age or karma, and rewrite the question for the community rather than
pasting the same text everywhere — r/sysadmin cares about the outage, r/devsecops
cares about the queue.

The version that worked asked the question as a thing that happens rather than
as a thing I was building. My first attempt, with the project attached, got one
reply. The same question asked plainly got eight, and two of those changed
published numbers.

## What actually got posted, and what it changed

Two communities, three threads. Recorded in full in `discussion-record.md`.

- **r/sysadmin**, question 4. Answered: rotation does break things, and it breaks
  them when the key had a consumer nobody had documented. No number, but a
  condition, and it is why `find_documented` is a separate cost component.
- **r/devops**, question 4 restated as a cost question. Eight commenters. One
  repriced the probe by a factor of ten, which moved `investigate` from never
  selected to selected on about 4% of findings. One withdrew an assumption I had
  been leaning on — that rotating a key verifies itself — after describing a
  rotation that went green while the old key was still live, baked into an image
  at build time. One established that live-versus-revoked is solved for
  certificates and unsolved for API keys, and separately made the
  public-identifier observation that became the generalisation section of the
  Week 2 paper.
- Question 3 got the most useful answer in the project and the one I least
  wanted: for a credential whose whole string is secret, no, there is no way
  without calling the provider.

**Not done:** questions 1, 2 and 5 were never posted, and three of the six
communities above were never approached. Six of the eight r/devops commenters
have had no reply from me, and two of those gave the most useful comments in the
thread. Against the brief's target of ten contributions across five communities
this is the weakest deliverable in the project, and the gap is recorded here
rather than closed.
