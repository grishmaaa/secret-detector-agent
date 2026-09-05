# Review Record

Three independent AI reviews of the preprint, each given the paper cold with a
different brief, one for each of the three required review types:

| Review type | Brief given to the reviewer | Reviewer |
|---|---|---|
| **Practitioner review** | Unrealistic assumptions, missing stakeholders, deployment risk, actions that cause harm, actions that cause unnecessary work | Reviewer B — domain realism |
| **Probability review** | Hidden states, prior, likelihoods, thresholds, error costs, calibration, evidence for alternative explanations | Reviewer A — methods and correctness |
| **Preprint review** | Problem statement, new information, methods, test design, baseline, repeatability, limitations, ethics, unevidenced claims, questions for the next version | Reviewer C — venue acceptance |

A fourth exchange with ChatGPT earlier in the project is included at the end
because it produced two substantive points, and three later rounds against the
compiled paper are recorded further down.

**On independence.** All three reviewers are Claude instances with fresh
context — no memory of how the project was built. That removes investment in
the work but not model diversity, and I am recording that rather than claiming
three different systems. The ChatGPT entry is the one genuinely different model.

## Review Checklist

- [x] Clear problem statement — passed all three
- [x] New information — **failed.** Reviewer C: textbook expected-cost minimisation on a hand-built instance
- [x] Correct methods — **failed.** Two arithmetic inconsistencies and one unstated assumption
- [x] Test design — **failed.** P1 is confounded; the comparison does not test what it claims
- [x] Baseline quality — **failed.** Escalate-everything is uncited and priced so it cannot win
- [x] Repeatable results — partial. Numbers reproduce; case data and code are not distributed
- [x] Limitations — present but deferred to a file reviewers cannot read
- [x] Ethics — **contradiction found.** The refusal to test the key and the admin-API probe assume different owners
- [x] Claims without evidence — several, listed below
- [x] Questions for the next version — recorded

## Review Table

> Do not accept each AI review comment automatically.

| AI Tool | Review Comment | Accept or Reject | Reason | Change | Evidence |
|---|---|---|---|---|---|
| Claude A (methods) | P1's +111% comes from removing actions, not from the 0.5 threshold | **Accept** | Verified. It is the single biggest error in the paper | Re-run P1 with all four actions; rewrite §7.3 and contribution 4 | Threshold 0.5 with dismiss fallback = 185.21; with revoke fallback = **77.56 (−11.5% vs baseline)**; with rotate fallback = 70.70 |
| Claude C (venue) | Same finding, independently | **Accept** | Two reviewers found it separately | As above | As above |
| Claude A | The 0.094 boundary is on a slice the agent cannot occupy | **Accept** | Verified, and I had noticed it and not acted | Report the reachable-line boundary as the headline | Prior slice: 0.00070 / 0.09385. Reachable line: 0.00145 / **0.06891** |
| Claude A | Cost components do not sum to the matrix | **Accept** | 10+30+60+10+2 = 112, not 120; 2+240+30+60 = 332, not 330 | Pick one matrix, regenerate every derived number | §7.5's `82+F` / `302+F` implies 112/332; the code uses 120/330 |
| Claude A | The escalate row is inconsistent with its own justification | **Accept** | escalate = 30 on revoked/fake, but 30 + best-other = 32 | Set escalate to 150/32/32 and recompute the baseline | Verified per state |
| Claude A | §5.4's entropy figure is wrong | **Accept** | The matrix gives 70.00 at (1/3,1/3,1/3), not 71.33 | Correct the number; the conclusion is unchanged | rotate 56.67 · escalate **70.00** · revoke 112.33 · dismiss 801.33 |
| Claude A | Conditional independence is never stated | **Accept** | It is load-bearing and almost certainly violated | State it at §4.2 and add to limitations | Placeholder context and malformedness are plainly correlated |
| Claude B (domain) | GitHub validity checks make the premise false | **Reject on the facts** | GitHub's table marks OpenAI API Key as **partner ✓ but validity check ✗** | Cite this explicitly — it defends the premise | GitHub Docs, supported secret scanning patterns |
| Claude B | Repository visibility is a free feature that separates live from revoked | **Accept** | OpenAI *is* a partner, so GitHub reports public-repo leaks to OpenAI, which may revoke | Add visibility as a scope condition; the invariant ratio is a private-repo claim | Same source: partner alerts go directly to the provider |
| Claude B + Claude A | The ownership regime is incoherent — admin API implies it is your own key | **Accept** | Two reviewers, independently. If it is your key the ethics argument weakens; if not, three actions vanish | State the ownership regime in §3.1 | — |
| Claude B | Rotate-safely leaves the key live for a deploy cycle and prices that at zero | **Accept** | If exposure justifies 2400, two more hours is not free | Add an exposure-duration term, or state the omission | — |
| Claude B | The escalate-everything baseline is a strawman | **Accept, partially** | Real pipelines allowlist and auto-dismiss first. But it is what my own §3.3 argument assumes | Soften to "the procedure this replaces", add a rules-then-escalate baseline as future work | — |
| Claude B | Missing actions: notify owner, check usage logs, announce-then-revoke, purge history | **Accept for notify and purge; defer the rest** | Purge-history is missing from *every* cell, which is a real omission. Notify-owner is the only action available if the key is not yours | Add purge as a component; record notify-owner as unmodelled | — |
| Claude B | Findings are malformed only rarely, since the scanner matched a pattern | **Accept** | This is sharp. The entire investigate result lives in the malformed branch | Define what malformed means beyond the pattern that fired, or re-estimate | Probe is bought only at neutral/malformed, 3.98% of findings |
| Claude C | Related work omits POMDPs, VOI, cost-sensitive learning, alert triage | **Accept** | Fatal for IJCAI as written | Add Howard 1966, Raiffa & Schlaifer, Kaelbling et al. 1998, Elkan 2001, Domingos 1999, Turney 2000, alert-fatigue literature | — |
| Claude C | Escalation cannot win by construction | **Accept, partially** | escalate = 30 + optimal on live, so §5.3 is near-tautological there. But it is *cheaper* than the tax implies on revoked and fake, so not purely definitional | State that escalate is priced as attention plus the correct action, and that the result follows largely from that | Verified per state |
| Claude C | SecretBench is in the references and never used | **Accept** | Embarrassing. A dataset of real secrets sits unused beside a fully synthetic evaluation | Either use it to ground the likelihoods or say in §6 why not | arXiv:2303.06729 |
| Claude C | The P0-vs-P2 action disagreement rate is never reported | **Accept** | Easy to compute and the reader needs it | Add to §7.1 | **14.55%** — the two malformed branches |
| Claude C | 21.3% presented in the abstract as if measured | **Accept** | No engineer-minutes were measured | Qualify every headline as "under our cost model" | — |
| Claude C | Practitioner feedback listed as a contribution is n=3 anecdote | **Accept** | And the same three rejected the paper's premise | Demote from contribution 5 to a methodological note | — |
| Claude A | The prior's first factor conflates detector precision with P(not fake) | **Accept** | Precision counts non-credentials; *fake* is defined as a real-format hardcoded key | Either split fake, or state the merge plainly | — |
| Claude A | 40 cases with one seed; the draw is 1.65 SD low on live | **Accept** | 14/40 live against a prior of 0.48 | Report over many seeds or drop the realised figures | σ = 3.16 |
| Claude A | §7.4's "revoke-now is cheapest in every state" is false | **Accept** | Dismiss is cheaper on fake (2 vs 5) | Restate as "optimal at every *reachable* belief" | Verified |
| ChatGPT | Escalation is a permission boundary, not a priced action | **Accept** | Already folded into limitations | Keep | — |
| ChatGPT | Probe the action's feasibility instead of the state | **Reject** | Tested and refuted: the consumer hunt appears identically in both remediation actions | Record the refutation as a result | Boundary invariant at 0.06588 for F ∈ {30…480} |
| ChatGPT (2nd pass) | Identical *marginals* do not give identical *joints* | **Accept — sharper than reviewer A's version** | A said the independence assumption is unstated; this says the structural result *depends* on it. Correct | State the claim as one about the joint distribution, not as a consequence of the two tables | If P(C,F\|live) ≠ P(C,F\|revoked) the ratio moves, even with equal marginals |
| ChatGPT | "Derive the prior" overstates it — it is constructed from two estimates about different populations | **Accept** | Third reviewer to raise this | Say "construct a traceable prior" | — |
| ChatGPT | The VPI bound bounds a state-revealing human, not authority or context | **Accept** | Restate as "perfect state information is insufficient to justify escalation" | Rewrite §5.3's interpretation | A human also supplies authority, ownership, business criticality |
| ChatGPT | Defining rotate-safely as already-safe may be *why* investigation has low VOI | **Accept — best diagnostic in any review** | The model may have removed the very uncertainty that would make investigating worth it | Elevate the sequential limitation from §9 to the discussion | — |
| ChatGPT | Sweep parameters jointly, not one at a time | **Accept — best constructive suggestion in any review** | One-at-a-time sweeps cannot establish robustness over nine uncertain inputs | Add a Monte Carlo over the cost space; report the fraction in which each qualitative conclusion holds | — |
| ChatGPT | Calling revoked and fake "harmless" is too strong | **Accept** | A revoked key still has audit implications, reuse risk, and evidence of prior compromise | Replace with "do not carry the modelled live-credential exposure risk" | — |
| ChatGPT | The title promises general secret-scanner triage; the model is OpenAI project keys | **Accept** | — | Narrow the title, or add a case-study subtitle | — |
| ChatGPT | Reframe the scope as decision-making when direct verification is unavailable or prohibited | **Accept — the most valuable single suggestion received** | Converts the load-bearing weakness into the scope statement, which pre-empts "why not just test the key" | Rewrite §1 and the title around this | Three practitioners asked exactly that question |
| ChatGPT | Practitioner input is sensitivity evidence, not population estimation | **Accept** | And the irony is exact: one of them said a single response is an opinion, and n = 3 | Reframe in §5.5 | — |

## The five that actually change the paper

**1. P1 is confounded, and it is the paper's strongest argument.** P1 was
supposed to test *the threshold*. It also silently removed revoke-now and
escalate from the action set. Give the same 0.5 threshold a revoke-now fallback
and it costs 77.56 — **11.5% better than the baseline**, not 111% worse. So the
catastrophe is caused by dismissing, not by thresholding, and contribution 4's
second clause is not established. This must be re-run before anything else.

**2. The headline boundary is quoted on a line the agent can never be on.**
0.09385 holds when revoked and fake stay in the prior ratio. The free features
lock live:revoked at 1.778, so the agent only ever occupies a different line,
where the boundary is **0.06891**. Contribution 1 stakes the paper on "0.094".
I had spotted this discrepancy earlier and did not chase it, which is my error
rather than the reviewer's find.

**3. The premise survives, and I can now cite why.** The domain reviewer argued
that GitHub's validity checks make the hidden state observable. GitHub's own
pattern table marks OpenAI API Key as a partner pattern **without** validity-check
support. So for the exact detector and provider I chose, the scanner genuinely
cannot tell me whether the key works. This belongs in §2 as a citation rather
than as an assumption.

**4. But repository visibility is a free feature I do not have.** OpenAI *is* a
partner, which means GitHub reports leaked keys directly to OpenAI for public
repositories, and OpenAI may revoke them. A key in a public repo is therefore
more likely revoked than the same key in a private one — which is exactly the
live-versus-revoked separation §4.3 claims free evidence cannot provide. **The
invariant-ratio result is a private-repository claim**, and I did not know that
when I made it.

**5. Related work is not adequate for the venue.** Deriving a threshold from a
cost matrix is cost-sensitive learning, established twenty-five years ago. The
EVSI computation is pre-posterior analysis. The sequential formulation I defer
to in limitations is a POMDP. None of these fields is cited, so a reader cannot
tell what is new — and the honest answer may be that the contribution is the
domain instance rather than the method.

## Gemini (fourth model, second external one)

| Review Comment | Accept or Reject | Reason | Change | Evidence |
|---|---|---|---|---|
| "Escalation is never optimal" depends on the guessed 30-minute human; a 15-minute SOC analyst breaks it | **Accept — and it is worse than Gemini knew** | 24.64 is the max over the *whole simplex*. Over beliefs the agent can actually reach the max VPI is **15.03**. A 15-minute analyst does not merely approach the bound, it beats it | Report 15.03 as the bound and state the human cost it assumes | Reachable VPIs: 13.92 · 3.93 · 10.88 · 10.44 · 10.17 · **15.03** |
| Scaling the breach cost to ~20,000 minutes collapses P0, P2 and P3 into "always rotate" | **Reject** | The rotate/revoke boundary does not contain dismiss-live and does not move. Only the dismiss boundary moves, and no reachable belief is near it | Note the invariance as a robustness result | Boundary stays at 0.06891 for dismiss-live ∈ {2 400 … 120 000}; dismiss boundary moves 0.00145 → 0.00003 |
| Rotate-safely on a *fake* key at 20 minutes is unjustified — why deploy a replacement for a key that never existed? | **Accept, and it is load-bearing** | The whole P0-vs-P2 gap rests on this cell. Set it to 0 and P2 becomes rotate-everything — **identical to P0** — and the belief model is worth exactly nothing | Say what the 20 buys (discovering it is fake and stopping), and cite tudalex's "never a real key? Minutes" | rotate\|fake = 0 → P2 = 65.70, rotate 100%; = 20 → 68.94, revoke 14.5%; = 120 → 79.38 |
| The admin-API probe requires provisioning an org-wide admin credential to triage a low-value project key | **Accept — nobody else raised it** | A real risk asymmetry: a high-severity credential introduced into the scanning pipeline to resolve a low-severity finding | Add to limitations as a security-design cost of the probe | — |
| Commit-graph and temporal features (deletion commits, file age, external-contributor PRs) *can* separate live from revoked | **Accept** | Second reviewer to find a free feature that breaks the invariance — the other was repository visibility | State that the invariance holds for the static text features chosen, not for all repository evidence | — |
| Remove the meta-comment about first-person plural from the draft body | **Accept** | Drafting artefact | Delete the italic note under the title | — |
| Reframe §7.2 as a sensitivity discovery rather than "the belief model is useless" | **Accept** | Third reviewer to say the framing invites rejection | Rewrite §7.2 and the conclusion | — |

## What four independent reviewers agreed on

Convergence matters more than any single reviewer's opinion, because these four
saw the paper separately and could not coordinate. Five findings were raised by
more than one:

| Finding | Raised by |
|---|---|
| The 21.3% is a property of the model, not a measurement — the generator uses the agent's own tables | **4 reviewers** |
| §7.2 as written invites rejection; reframe it as a sensitivity result | **3 reviewers** |
| Sweep the cost components jointly, not one at a time | **3 reviewers** |
| The baseline is an idealised perfect human, uncited, and priced so it cannot win | **3 reviewers** |
| The prior is constructed, not derived — its two factors describe different populations | **3 reviewers** |
| Free evidence I did not use *can* separate live from revoked (repo visibility; commit semantics) | 2 reviewers |
| Conditional independence is unstated and load-bearing | 2 reviewers |
| Practitioner input is n = 3 anecdote, not validation | 2 reviewers |
| A live key authorised for nothing is a missing state | 2 reviewers |

**The one thing all four independent reviewers said** is that Section 7 is not
an experiment. That is now settled and I should stop presenting it as one.

**And I made the same mistake twice.** The 0.094 boundary and the 24.64-minute
VPI bound are both quoted from regions of the simplex the agent cannot occupy.
On the reachable set they are **0.06891** and **15.03**. Two different reviewers
found one each, without either finding the pattern. The pattern is that I
computed over the whole belief space when the free features restrict me to a
line inside it.

Anything three independent reviewers found is not a matter of taste.

**Where the reviewers were complementary rather than redundant.** The Claude
reviewers caught arithmetic and scholarship: the P1 confound, the boundary
parameterisation, the component sums, the escalate row, the entropy figure, the
unused dataset, the missing literature. ChatGPT caught none of those but was
much stronger on formulation: what the paper is actually claiming, and whether
the framing survives contact with a hostile reader. Running both was worth more
than running either twice.

## The reframe worth taking seriously

ChatGPT's suggestion, which no other reviewer offered: stop presenting this as
secret-scanner triage in general, and present it as **decision-making when
direct credential verification is unavailable or prohibited.**

This is worth doing because it converts the paper's most attackable assumption
into its scope statement. Right now three practitioners have said "just try the
key", and a reviewer will ask the same thing — at which point the paper has
spent its length answering a problem the reader does not believe exists. Stated
as scope, the question does not arise: the paper is about what to do *when that
option is off the table*, which is a real situation in plenty of organisations.

And ChatGPT's version of the research question is better than mine:

> When is evidence acquisition worth paying for in security triage?

Every result I have already answers that question — uncertainty is not the
trigger, information gain is not decision value, a strong hedge makes state
estimation nearly irrelevant, and value concentrates at action boundaries. The
paper I wrote asks whether cost-derived triage beats escalation. The paper my
results actually support asks when evidence is worth buying. Same experiments,
better question.

## Questions for the next version

1. What is the action-disagreement rate between P2 and P3, and is 3.98% of
   findings worth the machinery that produces it?
2. Does the invariant ratio survive adding repository visibility as a feature?
3. If P1 with a safe fallback beats the baseline, what is left of the argument
   for deriving thresholds rather than choosing them?
4. Can the likelihood tables be grounded in SecretBench rather than estimated?
5. What does "malformed" mean for a string that already matched the scanner's
   pattern?

## Later rounds, after the LaTeX draft

Three further rounds once the paper compiled. I am recording these separately
because their character is different: the first four reviews read a draft and
found defects in it, whereas these three mostly re-derived my own results and
the value was in where they disagreed.

| Source | Comment | Accept or Reject | Reason | Change |
|---|---|---|---|---|
| Gemini | The formulation is right and a generic four-state sketch of this problem is wrong | **No change** | It was correcting a different answer, not mine. Every "correct specification" in it was copied out of my paper | None. Recorded so the round is not mistaken for validation I earned twice |
| Gemini | "The ordering P2 < P0 < P1 < baseline is robust across 98.64% of draws" | **Reject** | The figure belongs to one pairwise claim. The compound ordering is bounded by 79.20% and P1 was never swept | Kept out of the paper. Logged as AI error 15 |
| Gemini | Adding git-history and passive organisational signals is the lever that breaks the 1.778 invariance and removes the 19.7% regret | **Reject** | I had already run the experiment that bears on it. Sweep B breaks the invariance deliberately and moves no conclusion by more than 3.2 points | None to the model. The channels are named in limitations without likelihood tables, because inventing eight more would deepen the weakness they are meant to address |
| Gemini | `expires_at` from the provider's admin API as a new evidence channel | **Accept, unbuilt** | It arrives on the same admin call I already price at three minutes, so it is a free strictly-more-informative upgrade to the probe rather than a new channel with a new price. The only suggestion in the list that could raise EVSI without raising cost | Named in limitations as the extension with the best ratio of value to work |
| Gemini | Historical triage tickets as a labelled dataset | **Reject** | They record what a responder decided, not what the key was. My own regret analysis finds every error is over-remediation, so a corpus labelled by responder behaviour encodes that bias as ground truth | Written into §6.1 as a second paragraph beside the SecretBench argument |
| Independent sourced rebuild | The whole model reparameterised in dollars with every figure traced to a citation, gaps marked | **Accept in part** | Its indifference point is 0.079%; my dismiss branch is unreachable below 0.15%. Two unrelated parameterisations, the same conclusion: ignore is not reachable and remediation is the default | The unreachability of dismiss promoted from a figure caption to a stated result, since it is the only place the model agrees with practice on something I did not tune it to agree with |
| Independent sourced rebuild | Exposure channel dominates: time from public commit to first attacker contact is reported in minutes against remediation in weeks, so for public leaks the governing state is *compromised*, not *live* | **Accept** | It is a condition on the whole model, not a caveat on one result. My paper had it as half a sentence in limitations | **Changed the paper's scope.** §1 now opens with private and internal exposure as a stated restriction |
| Independent sourced rebuild | Naive Bayes over correlated repo-context features saturates the posterior and makes the threshold inert | **Accept** | The sharpest methodological point anyone has made about this work, and none of the first four reviews caught it | Produced `experiments/shrinkage.py`. Results in §4.3 and `results/shrinkage.md` |
| Independent sourced rebuild | Report suppression rate as the headline, not the rotate/ignore decision — "report that your agent decides whether to rotate and a reviewer will ask why you did not just rotate" | **Accept as diagnosis, open as change** | This is exactly the rejection I received, written down before I received it | Not yet acted on. It implies reframing the contribution as detector, ranker and probe planner, which is a bigger change than the paper can absorb this week |
| Practitioner critique | Two-part credentials — an AWS `AKIA` access key ID is public, so `GetAccessKeyLastUsed` returns `Active` or `Inactive` for that exact key without touching the secret half | **Accept** | This dissolves my decision problem for AWS, Stripe, JWTs and STS credentials. The problem is a property of credential formats that expose no public identifier, and I chose the hard case by accident | Reframes the scoping paragraph from an arbitrary choice into a claim about which formats make the state observable. **Not yet written into §3.1** |
| Practitioner critique | Authenticating with a found key can trip a deliberately planted canary token and alert whoever planted it | **Accept** | A second reason for my constraint that is operational rather than moral, and the stronger one with practitioners | §1 now states the constraint as contested rather than mine alone, with both reasons |
| Practitioner critique | Liveness evidence buys queue ordering, not permission to ignore | **Accept** | Independently reached by a practitioner in the r/devops thread as "still-live is a nice-to-have after quarantine" | Same change as the sourced rebuild above. Two unrelated sources, one conclusion |

### On independence, again

Five of these twelve rows are the same model family as the first four reviews.
The practitioner rows are the only ones from people, and they produced the two
changes I would defend hardest — the constraint's second justification and the
credential-format reframe. The AI rounds were most useful when they disagreed
with each other, and least useful when they read my paper back to me with new
numbers attached, three of which were wrong.

## Verdict

Reviewer C: **reject**, with the single most valuable change being to ground the
likelihoods in real data and report the P0-versus-P2 disagreement rate.

I am recording that verdict without arguing with it. Items 1, 2 and 5 above are
real defects, not differences of taste, and two of them were things I could have
caught myself.

**A second verdict, from outside.** The finished preprint was submitted and
rejected as basic and not research-worthy. I am recording that here rather than
only in the publication section, because Reviewer C predicted it — textbook
expected-cost minimisation on a hand-built instance — and because the later
sourced rebuild predicted the exact form the objection would take. Two reviews
told me before submission and I read both as things to fix in the writing rather
than as statements about what the work was. The defect is that every input is my
estimate, and no amount of sensitivity analysis converts an estimate into a
measurement.

---

# Week 2 — the adversarial round

Run after the Week 2 paper existed as a finished draft, not during writing. Two
rounds against the same repository, with deliberately different briefs, plus my
own verification of every claim before accepting it. Nothing below is accepted on
a reviewer's say-so; the evidence column is what I ran.

## The two briefs, and why the difference is the finding

**Round A — defect hunt.** Three reviewers pointed at named failure modes:
confounded comparisons, random-number reuse across channels, stale derived
quantities, mutated globals, silent fallbacks in sampling loops, boundary
comparisons. Told to report only defects they had confirmed by running something.

**Round B — evaluative.** Asked to grade the project against three checklists:
seven probabilistic-modelling components, five deployment-risk categories, ten
research-quality criteria.

Both rounds had the same code. Round B explicitly reran four scripts and cited
line numbers in files nobody pointed it at, including `paper/limitations.md:104`,
so its access was real.

**They found almost disjoint sets of problems, and neither alone was enough.**

Round A found every defect that changes a number: an abstract crediting one fix
with three fixes' work, a policy comparison scored against the cost cell the
paper repudiates, a detection rate transplanted between experiments, three
random-number defects, a buried negative result. Round B found none of them.

Round B found every problem that is an *absence*: a baseline human modelled as a
perfect oracle, a harm model denominated only in engineer-minutes, four
stakeholders priced as one 30-minute unit, a privileged credential used to
investigate an unprivileged one. Round A found none of those, and structurally
could not — you cannot grep for a stakeholder nobody modelled.

The reason Round B missed the defects is in its own words: *"the core scripts
completed successfully and reproduced the reported results."* That is a
reproduction check. **Every defect Round A found is deterministic and reproduces
byte-identically forever** — `feedback.py`'s broken arm returns 61.04 on every
run there has ever been. A reproduction check cannot find a bug that reproduces.

I had assumed the difference would be code access. It was the brief. That is now
the second time this project has learned the same lesson in a different form: in
Week 1 four reviewers read the write-up and a fifth found a sampler bug by
reading the code. The Week 1 version of the lesson was *read the code*. The
Week 2 version is sharper: **reading the code is not enough either. You have to
be told what kind of thing to look for.**

## Round A — accepted

| # | Finding | Evidence I ran | Action |
|---|---|---|---|
| A1 | The abstract credits `p_exploit` alone with taking `fake` recall to 0.954 | `fixes.json`: fix 1 alone gives **0.588**. 0.954 needs all three fixes plus scope | **Changed a headline.** Abstract and §10 rewritten with the decomposition; Figure 2 now has three bars |
| A2 | P1's regret of 114.12 is scored against the 2400-minute cell §10 repudiates | Rescored on the corrected matrix: **13.89**. P0/P2/P3 unaffected — none of them ever dismisses a live key | **Changed a headline.** "Nine times worse" was 1.27×. Ladder now on one ruler |
| A3 | A negative result is in the results and absent from the paper | `week2-results.md` §"the probe did not pay for itself": P3 spends 0.132, recovers 0.066, ends behind P2 at 60.52 vs 60.45 | Restored as a finding, with a cost column so it cannot be hidden again |
| A4 | The drift-alarm's 100% detection is quoted against a failure it cannot see | `feedback.md`: the alarm watches free features, which carry zero bits about live vs revoked — the exact axis the drift is on | **Changed a claim.** §10.3 now says the agent has an alarm for the cheap drift and none for the expensive one |
| A5 | `feedback.py` learn/frozen arms short-circuit differently and simulate different worlds | Paired: `cost_frozen` 61.0417 → **60.4703**, identical to learned. The learned prior changes the action on 0 of 4000 findings | **Deleted a result.** The 0.57 min/finding advantage for learning does not exist |
| A6 | `registry.py` shares one RNG across three channels | At c = 0.5 the age rows are identical across states, so the channel is provably uninformative — and the table showed it changing regret by −0.8% | Three streams. Age-only at c = 0.5 now exactly **0.0%** |
| A7 | `scope_probe.evsi()` takes no cost matrix, so it prices information at 2400 forever | The probe purchase rate was **0.468 for all 75 perturbed matrices** in the cost sweep | Threaded through. "6 of 15 cells don't matter" → **3 of 15** |
| A8 | `generalization.py` identifier and scope draws share a stream | 19 of 500 identifier observations differ between arms of a paired A/B | Split. Scope value −0.230 → −0.149, recovered 80.8% → the ratio is withdrawn entirely (see A9) |
| A9 | "Recovers 80.8% of the value of perfect live/revoked knowledge" divides a total-regret gain by a live/revoked-only ceiling | The identifier also carries 0.8981 bits about live vs `fake`, so gains on excluded axes were counted inside the ratio | Replaced with an unratioed statement: 65% of total regret removed |
| A10 | `worked_examples.py` prints 0.0199 and 0.0380 bits for channels its own prose calls "0.0000 by construction" | Re-applying a spent channel's table to a belief containing it measures a second independent draw of an observation in hand | Bits column now 0.0000, matching the prose |
| A11 | Every number in the project is one seed and nothing reports an interval | Two of my own scripts disagreed about the same agent: balanced accuracy 0.467 vs 0.494 | **New experiment.** `stability.py`, 200 scope-draw seeds |

## Round B — accepted

| # | Finding | Why I accepted it | Action |
|---|---|---|---|
| B1 | The baseline human is a perfect oracle | `research-file.md`: *"A human resolves it correctly every time."* The entire cost-not-accuracy framing rests on it, and no real responder is that | New limitation, stated as what it is: every saving here is a saving against an idealisation |
| B2 | The harm model is engineer-minutes and nothing else | Customer outage, data exposure, regulatory consequence are outside the objective, so an action that saves 30 minutes and takes down a service scores better | New limitation. The 332-minute `revoke now` price is cleanup, not blast radius |
| B3 | "A human" is one price; real organisations have several | Security analyst, service owner, platform team, committer — different authority, availability and permissions, all priced at 30 minutes | New limitation, with the queue point folded in |
| B4 | `p_exploit = 0.10` is presented as a probability | It is ~4× a figure measured on *public* exposure, applied to private repos | Reframed in §10 as a stress-test parameter, with the 0.027 and its provenance stated |
| B5 | The agent needs a privileged credential to investigate an unprivileged one | Real, and the paper stated the boundary without noting nothing implements it | New limitation |
| B6 | The `fake` collapse to 0.0111 assumes conditional independence | `shrinkage.md`: 0.0111 → 0.0216 at w = 0.8 → **0.0576** at w = 0.5. The paper printed 0.0111 twice and never said "shrinkage" | New paragraph in §4 giving the range |

## Round B — rejected, with the check

| Claim | What I found |
|---|---|
| "The corrected boundary is 0.06891 on the reachable set" | It is **0.06588**. `evidence-selection.md:118`. Invented digit |
| "145 of 500 decisions are not hindsight-optimal" | `feedback.json` lists 8 failures. The number is not in the data |
| "`rotate\|fake = 20` materially determines your conclusion; set it to zero and P2 collapses into P0" | Published spans: `revoke\|live` 85.56, two cells at 48.56, `rotate\|revoked` 10.07. `rotate\|fake` span was **0.00**. Backwards. (It becomes 4.34 *after* fixing A7 — right cell, wrong reason, and the reviewer could not have known) |
| "Claims without evidence — FAIL: 23.2%, 1.75 min, never escalates" | All three are **Week 1 paper** claims. `23.2` appears in the Week 2 paper zero times, escalation is a rule firing on 2.6%, and the Week 1 paper is labelled as such in the README |
| "The New Questions aren't surfaced in the paper" | §14 is New Questions. Graded the wrong document, then recommended rewriting the paper around Week 2 — which is the paper it did not read |

## What the round cost and what it bought

Eleven confirmed defects in Round A, six accepted absences in Round B, five
rejections. Four defects changed a published number, one deleted a result
outright, and one added an experiment that did not exist.

The uncomfortable part: **in four cases the results file was already more careful
than the paper written from it.** `week2-results.md` reported the probe not
paying for itself. `feedback.md` said the alarm cannot see the drift that
matters. `shrinkage.md` gave the range on 0.0111. `fixes.md` had the
decomposition showing 0.588. Every one of those was in the repository before the
paper was written, and the paper contradicted all four.

That is not a review finding about the model. It is a finding about the step
between having a result and writing it down, which is where this project has now
lost more accuracy than in the experiments themselves.

## Verdict

Both rounds converge on the same thing, and it is the thing the Week 1 rejection
said: the decision machinery is sound and the probability model is not measured
against anything. Round B put it as *"you have demonstrated that you can build
and interrogate a probabilistic model; you have not demonstrated that your
probability model describes the real world."*

I am recording that without arguing with it, because it is correct, and because
the paper now says it in Section 13 in almost those words.
