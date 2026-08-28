# Review Record

Three independent AI reviews of `paper/preprint.md`, each given the paper cold
with a different brief: methods and correctness, domain realism, and venue
acceptance. A fourth exchange with ChatGPT earlier in the project is included at
the end because it produced two substantive points.

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

## Verdict

Reviewer C: **reject**, with the single most valuable change being to ground the
likelihoods in real data and report the P0-versus-P2 disagreement rate.

I am recording that verdict without arguing with it. Items 1, 2 and 5 above are
real defects, not differences of taste, and two of them were things I could have
caught myself.
