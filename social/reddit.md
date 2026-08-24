17/08/26

Five questions have come out of your own reasoning so far. Ordered by what unblocks you soonest.

**1. What actually happens today?** — validates your baseline
> When a scanner flags a possible key in your repo, what do you actually do next? I want to know the real procedure, not the ideal one.

You guessed "hand it to a human to check." If that's wrong, your baseline is wrong and everything downstream shifts.

**2. The fifth state** — you said you'd rather have it named by someone who's seen it
> A scanner flags a string. I can describe four things it turns out to be: a live production key, a dead one, a provider-issued test key, or something a developer hard-coded that was never real. What am I missing? I suspect there's a category of "not a credential at all" but I can't characterise it.

**3. Live vs dead** — the crux
> Is there any way to tell a live key from a revoked one without calling the provider? Or is that always a phone-a-friend?

If someone says yes, your whole problem shrinks. Worth knowing early.

**4. The cost question** — you'll need this for the cost matrix
> Has rotating a key ever broken something for you? Roughly what did it cost, and was the key one anybody had documented?

**5. Escalation tolerance** — sets your target
> If a tool handed you 50% of alerts to check by hand, would you still use it? Where's the cutoff before you switch it off?

---

**Communities.** I can't confirm current activity or mod rules — check each before posting.

| Where | Best question | Note |
|---|---|---|
| r/devsecops | 1, 2, 5 | Closest match — people who own the alert queue |
| r/AskNetsec | 2, 3 | Explicitly for questions; beginner-safe |
| r/sysadmin | 4 | They feel the outage side, which security folk under-weight |
| r/ExperiencedDevs | 1, 5 | They receive the alerts and push back |
| r/sre or r/devops | 4, 5 | Rotation runbooks live here |
| r/netsec | — | Save for sharing the finished preprint. Strict; don't open here |

You got removed last time, so: read the sidebar rules first, lead with the question and no repo link, and check whether the sub requires account age or karma. Rewrite each question for its community — r/sysadmin cares about the outage, r/devsecops cares about the queue.

Question 1 is the one to post today. Replies take days, and you can keep reading while it sits.