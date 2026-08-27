# Discussion Record

Every public contribution, and what it changed. A link on its own does not count.

## Contributions

| Platform | Community or Account | Link | My First Contribution | Human Answer | My Next Answer | Design Change |
|----------|---------------------|------|-----------------------|-------------|----------------|---------------|
| Reddit | r/sysadmin | https://www.reddit.com/r/sysadmin/comments/1vqomq7/secretscanner_triage/ | Asked whether rotating a credential has ever actually broken something, and roughly what it cost | Yes — and it was always a key nobody had documented as live. Also: do not tune the ratio, verify the key instead; and log which consumer last used the credential | Not yet replied | Adding last-consumer telemetry as a candidate piece of evidence; adding a question about whether that evidence is obtainable at all |
| Reddit | r/devops | https://www.reddit.com/r/devops/comments/1vzk0v2/cost_of_rotating_a_revoked_key/ | Asked how long it takes to realise a credential you started rotating was already dead or never real | Minutes for revoked, minutes for never-real, hours for an abandoned project. Timebox at 10–15 minutes then verify. Two critiques of what is worth automating. And a PKI answer showing live-versus-revoked is solved for certificates and unsolved for API keys | Not yet replied | Wasted-rotation cost bounded rather than swept; timeboxing recorded as a policy I do not have; the automation critique folded into limitations |

---

## Reddit, r/sysadmin — rotation cost

**What I asked.** Whether rotating a credential had ever broken something for them, and what that cost.

I should record that I asked this in older wording than the framing I have now. My question described the decision as "real exposed key versus false positive or test fixture", which is a two-way split, and I quoted a cost ratio between 5:1 and 100:1 as though I had swept it. Neither is where my project actually stands — I had four states at the time, not two, and I have not run any sweep. (I have since settled on OpenAI and the count has collapsed to three; see `research-file.md`.) The answer I got is a response to the question I asked, so I need to read it with that in mind, and ask the next one in my own current terms.

**The reply, in full:**

> Yes, rotation has broken things for us, and it was always a key nobody had documented as live. That is why I would not tune the ratio first. The cheaper move is to make the key itself tell you: try it. A read-only call against the provider answers live or dead in one request, and that beats any confidence score derived from the string. On mail credentials specifically, we found smtp submission creds that looked like test fixtures in a sample config and were happily authenticating in production, because the published config and the effective one had drifted years earlier. So treat unverifiable-and-rotatable as the only class where your ratio matters, and shrink that class by adding verifiers. And whatever the policy, log which consumer used the credential last so rotation is a decision rather than a bet.

One reply, from one person, about one organisation. I am treating it as testimony that licenses a change to my thinking, not as data.

### Summary

Rotation does break things, and it breaks them under a specific condition: the key had a consumer nobody had written down. Their advice is not to reason about which state the key is in — go and observe it, by calling the provider. And regardless of the policy, record which consumer last used the credential, so that rotating is an informed decision rather than a gamble.

### Where I disagree, or at least where it does not settle things

"Just try the key" is close to the baseline I already have, and it is a strong one. But it answers *live or dead*. It does not tell me whether a key that authenticates is a production key or a provider-issued test key, and at the time those were two of my four states with different consequences.

**Later note.** Choosing OpenAI removed the test-key state, so that particular objection no longer applies to me. What survives is the constraint: I decided I will not authenticate with a credential I found, so "just try it" is not available to my agent whatever its merits. The probe I ended up with asks my own account about the key instead, which respects that.

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

## Reddit, r/devops — how long before you realise it was already dead

**What I asked.** When you have started rotating a credential and then found it was already revoked, or was never a real key — roughly how long had you burned before working that out?

I asked this deliberately without any project framing. My first post read as someone doing research and it showed; this one is just a question about a thing that happens. It got four replies in an hour against one on the first attempt.

### The replies

**tudalex** — the direct answer:

> It was already revoked? Minutes. It was never a real key? Minutes. It was a key with no access anymore because the project was abandoned 2 years ago? Hours, but that key should've been removed either way, but no time spent on rotating it with a new one.

**Educational_Yam_9956** — a policy I do not have:

> I'd just timebox this: if rotation isn't working after 10–15 minutes, stop and first prove the key actually works with a minimal test.

**stobbsm**, and a thread underneath it:

> I have my infra setup to not experience this problem. IaC FTW!

> *tindalos:* The real automation trick isn't automating things that save minutes a day, it's automating the things that save hours logging into servers and looking through certificate stores trying to find a key.

> *arbyyyyh:* But also things that are critical. Is it something that needs to be done exactly right every single time, the first time, or is similarly a short but complex operation? Automate it.

### What this settled

**My estimate was right for the clean cases.** Minutes for revoked, minutes for never-real. That is the 20–30 I guessed, confirmed by someone who has done it.

That matters more than it sounds. Whether my agent ever escalates turns on this single number: below about 40 minutes it never asks a human, above it sometimes does. I was sitting twenty minutes below the boundary on a guess. It is now a guess someone else has made too.

**There is a case I did not have.** A key belonging to a project abandoned two years ago — nobody revoked it, the thing that used it just died. It does not work, but establishing that takes hours because there is nobody left to ask. By my own rule that folds into `revoked`, but it wrecks the assumption that revoked is cheap to *discover*. Same state, wildly different discovery cost.

**And then the timebox answers it.** If you stop after fifteen minutes, the abandoned-project tail never happens. That converts a quantity I was going to sweep into one that is bounded by policy. It is the cleanest thing anyone has given me.

### The design change I am not making, and why it is interesting

The timebox suggestion is a different architecture from mine, not a tweak.

My agent decides, then acts. The timebox says: **start acting, and let the difficulty of acting be evidence.** "This rotation is not going smoothly after fifteen minutes" is itself a signal about the hidden state — it means the key is probably not what you thought. Rotation doubling as a probe.

I am not rebuilding around that. But it is the second time someone has described a workflow that interleaves acting and observing where mine separates them, and I want that on the record rather than quietly ignored.

Note also that they say *prove the key actually works with a minimal test.* That is the thing I ruled out. Two of the three practitioners who have answered me have now said, independently, that you just try the key. My constraint is one I chose; it is not one the field shares.

### The critique, and its rebuttal, from two different people

stobbsm's point is that infrastructure-as-code makes this problem not happen — declare what consumes what and the undocumented-consumer case disappears. That is someone saying my problem is solved by process rather than by triage, and it is fair. **My agent is most valuable exactly where practice is worst.**

tindalos sharpens it: automate what saves hours, not minutes. My agent saves minutes per finding. The expensive part is the hunt, and I am not automating the hunt — I am deciding whether to start it.

arbyyyyh gives the counterweight without being asked: automate what has to be right the first time, every time. That is the other half of the criterion, and it is the half my project sits on. Dismissing a live key is precisely the error that cannot be taken back.

So the thread contains both the critique and its rebuttal, from people arguing with each other rather than with me. I could not have written that exchange myself and it is going in the limitations section as it stands.

### A fourth reply, about certificates, which turned out to be the most useful

**dodexahedron** answered from a PKI perspective rather than an API-key one:

> If using an internal PKI with proper CDP? Should almost instantly know if it was revoked.
>
> If unsure, and there's even a remote suspicion of exposure? Minutes at most. Revoke and replace. Service fallout is less important than security fallout. If you have a bad PKI and can't properly or reliably revoke, blacklist it in AD.
>
> Issued by a public CA? Start thinking of how to explain to your boss why you have to ask for a few hundred bucks, as you are revoking the cert with that CA, and ask once you are done doing that revocation and re-issuance.
>
> GPG identities/keys? Um. Well. I hope you also created and published a revocation cert and that the exposed key was not your master signing key. Otherwise, I hope you do it right next time.

**My hardest problem does not exist for certificates.** A certificate carries a CRL distribution point — a pointer to its own revocation list. The credential tells you whether it has been revoked. Live-versus-revoked, the pair nothing in my repository can separate and the pair my entire probe exists to attack, is a *solved problem* for a different credential type.

That is worth stating plainly in the preprint: **my central difficulty is a property of API keys specifically, not of leaked credentials in general.** PKI solved it with CRLs and OCSP decades ago. An OpenAI key has no equivalent — no revocation list, no status field, nothing in the string. It validates the scope I chose and explains why the problem is hard, from someone who was not trying to do either.

**They disagree with my policy, and I am recording the disagreement rather than resolving it.** My model says rotate safely under uncertainty — 120 against 330 for revoking now. They say revoke immediately, because *service fallout is less important than security fallout*. Same situation, opposite call, and the difference is entirely in how we price an outage. My `C_OUTAGE` of 240 says an outage is expensive; they say it is not, next to the alternative. My sweep should cover the range where they are right.

**Two more things engineer-minutes cannot express.** I already knew it misses harm falling on customers. Revoking a certificate with a public CA costs *actual money* — a few hundred dollars — which is not anyone's time at all. And the GPG master-signing-key case is worse than expensive: if no revocation certificate was published in advance, there is nothing to be done. My matrix has no cell for *no action helps*.

**An action I do not have.** "If you can't properly or reliably revoke, blacklist it in AD." When revocation is unavailable, block the credential somewhere else — at the directory, the gateway, the network. Neither of my two remediation actions covers that, and for API keys there may be no equivalent, which is itself worth knowing.

I am not adding any of this to the model. It is a different credential type with different mechanics, and my scope is one provider's API keys. But the reply is the clearest external evidence I have for *why* this problem is shaped the way it is, and it goes in the limitations section rather than being quietly dropped for being off-topic.

## Questions queued to ask

Written after settling on OpenAI, so these are in my current framing — three states, five actions — rather than the wording I used in my first post.

| # | Question | Where I plan to ask | Why it matters |
|---|---|---|---|
| 1 | Revoke now, or find the consumers first and rotate cleanly? What decides it? | r/sysadmin, r/devops | **Prices two of my five actions.** Highest value question I have |
| 2 | Is "the key had an undocumented consumer" knowable before you rotate, or only after it breaks? | r/sysadmin | If it is only visible afterwards it cannot be evidence, and I am not allowed to model it |
| 3 | What is the state I am missing? | r/devsecops, r/AskNetsec | I can describe live, revoked and fake. I think there is a fourth and cannot characterise it |
| 4 | When a scanner flags a key in your repo, what do you actually do first — the real procedure, not the ideal one | r/devsecops | Validates my baseline. I asked a version of this already but in older wording, so the answer addressed a different question |
| 5 | If a triage tool handed back half its findings for a human to check, would you still run it? | r/devsecops | Sets the escalation rate above which the agent has not automated anything |

Drafts, to be rewritten in my own words before posting:

**1.** When you find an exposed API key, do you revoke it immediately and accept whatever breaks, or find the consumers first and rotate cleanly? What decides it for you — the provider, the blast radius, how sure you are that it leaked?

**2.** Someone told me that rotation breaks things when the key had a consumer nobody had documented. Is that knowable before you rotate, or does it only become obvious once something has already broken?

**3.** A scanner flags a string in a repository. I can describe three things it turns out to be: a live key, a revoked key, or something a developer hard-coded that was never real. I think there is a fourth — a string that is not a credential at all and only looks like one — but I cannot characterise it well enough to use. What am I missing?

**4.** When a scanner flags an OpenAI key in your repo, what is the first thing you actually do? I am after the real procedure rather than the one in the runbook.

**5.** If a triage tool handed you half its findings to check by hand, would you keep running it? Where is the cutoff before you switch it off?

Ask 1 and 2 first. They are the ones my cost model needs and the ones nothing I can do alone will produce.

Before posting: read the sidebar, lead with the question rather than a link, and check whether the subreddit requires account age or karma. I have had a post removed once already.

## Result Categories

For each useful answer, one of these. A link without an explanation does not complete this task.

- A new assumption
- A new failure condition
- A new test
- A change to the agent
- A change to the probability model
- No change, with the reason
