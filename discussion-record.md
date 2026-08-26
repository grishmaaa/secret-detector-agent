# Discussion Record

Every public contribution, and what it changed. A link on its own does not count.

## Contributions

| Platform | Community or Account | Link | My First Contribution | Human Answer | My Next Answer | Design Change |
|----------|---------------------|------|-----------------------|-------------|----------------|---------------|
| Reddit | r/sysadmin | https://www.reddit.com/r/sysadmin/comments/1vqomq7/secretscanner_triage/ | Asked whether rotating a credential has ever actually broken something, and roughly what it cost | Yes — and it was always a key nobody had documented as live. Also: do not tune the ratio, verify the key instead; and log which consumer last used the credential | Not yet replied | Adding last-consumer telemetry as a candidate piece of evidence; adding a question about whether that evidence is obtainable at all |

---

## Reddit, r/sysadmin — rotation cost

**What I asked.** Whether rotating a credential had ever broken something for them, and what that cost.

I should record that I asked this in older wording than the framing I have now. My question described the decision as "real exposed key versus false positive or test fixture", which is a two-way split, and I quoted a cost ratio between 5:1 and 100:1 as though I had swept it. Neither is where my project actually stands — I have four states, not two, and I have not run any sweep. The answer I got is a response to the question I asked, so I need to read it with that in mind, and ask the next one in my own current terms.

**The reply, in full:**

> Yes, rotation has broken things for us, and it was always a key nobody had documented as live. That is why I would not tune the ratio first. The cheaper move is to make the key itself tell you: try it. A read-only call against the provider answers live or dead in one request, and that beats any confidence score derived from the string. On mail credentials specifically, we found smtp submission creds that looked like test fixtures in a sample config and were happily authenticating in production, because the published config and the effective one had drifted years earlier. So treat unverifiable-and-rotatable as the only class where your ratio matters, and shrink that class by adding verifiers. And whatever the policy, log which consumer used the credential last so rotation is a decision rather than a bet.

One reply, from one person, about one organisation. I am treating it as testimony that licenses a change to my thinking, not as data.

### Summary

Rotation does break things, and it breaks them under a specific condition: the key had a consumer nobody had written down. Their advice is not to reason about which state the key is in — go and observe it, by calling the provider. And regardless of the policy, record which consumer last used the credential, so that rotating is an informed decision rather than a gamble.

### Where I disagree, or at least where it does not settle things

"Just try the key" is close to the baseline I already have, and it is a strong one. But it answers *live or dead*. It does not tell me whether a key that authenticates is a production key or a provider-issued test key, and those are two of my four states with different consequences. So verification shrinks my problem, it does not remove it.

I also cannot always do it. I decided at the start that I am not going to authenticate against a third party's API with a key I found in a repository, and that constraint is mine regardless of whether it is technically easy.

### New assumption

The cost of a wrong rotation is not the same across all the states I might be wrong about. It concentrates where the key had an undocumented consumer. My thinking so far has treated every unnecessary rotation as equally wasteful, and that is now something I believe is wrong.

### The evidence I did not have

**Last-consumer telemetry** — when did anything last authenticate with this key, and what was it?

This is the first thing anyone has given me that speaks to live-versus-dead, which is the pair I had written down as having no observable difference. Something authenticated two hours ago means the key is live; a dead key cannot authenticate. Nothing has ever used it points the other way.

It also answers the cost question at the same time. It does not only say *whether* something used the key, it says *what* — which is precisely the undocumented-consumer problem that makes rotation expensive.

Two things I need to work out before I can use it:

- It is not free the way a key prefix is. The prefix is in the string. Usage telemetry lives at the provider and someone has to go and fetch it. That makes it something the agent buys, not something it always has.
- I may not be able to get it at all. My agent looks at a repository; the telemetry lives with the provider. Whether I have that access, and for which providers, is now an open question in my research file.

### To verify

- Whether usage or last-authentication data is exposed by the providers I end up choosing, and how much effort it takes to retrieve.
- Whether "the key had no documented consumer" is something observable in advance, or only obvious after the rotation has already broken something. If it is only visible afterwards, it cannot be evidence.

## Result Categories

For each useful answer, one of these. A link without an explanation does not complete this task.

- A new assumption
- A new failure condition
- A new test
- A change to the agent
- A change to the probability model
- No change, with the reason
