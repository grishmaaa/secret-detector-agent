# Deciding what to do about a possible key in a repository

A cost-aware triage agent for secret-scanner findings.

## The problem

A scanner reads a repository and reports that some string in it looks like a key. That is the entire input. It does not say what kind of key, and it does not say whether the key works.

> The agent observes a scanner result reporting that a string in the repository looks like an OpenAI key. It must select **dismiss**, **investigate**, **escalate**, **revoke now**, or **rotate safely**, without knowing what the string actually is.

Five things the string could turn out to be:

1. **A live key** — still authenticates. Whatever sits behind it is reachable by anyone holding the string.
2. **A revoked key** — was real once, no longer works. Harmless now.
3. **A fake key** — hard-coded by a developer, never authenticated against anything.
4. **A zero-scope key** — authenticates, but is authorised for nothing. Live by every test that asks "does this work", worthless to an attacker.
5. **Something else** — a string that is not a credential at all and just happens to look like one, because something in the code needed a long random-looking string.

Week 1 was built on the first three. States 4 and 5 were named in Week 1 and left out because I could not characterise them; Week 2 added both. The residual state matters more than its 1% prior suggests, because it is the only state whose cost model I do not trust, and that is what makes it the escalation trigger rather than a rounding error.

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

**One provider: OpenAI.** I started intending to use two — one that issues test keys and one that does not — and dropped it because the complexity was compounding faster than the insight.

**One finding at a time.** The agent decides about a single flagged string, not whether a whole repository is compromised.

**It never authenticates with a key it found.** The probe asks my own admin API about a key; it does not try the key. There is no live credential anywhere in this repository — every string in `data/cases.json` is a synthetic feature descriptor.

**It is a simulation.** No admin credential, no live API calls. Every likelihood is my estimate rather than a measurement, so the honest result is a sensitivity analysis, not a point estimate.

## Objective

The baseline is what a person actually does today: find a key, hand it to a human to check whether it is live, act on what they say.

The important property of that baseline is that it is never wrong about the state. A human resolves it correctly every time. So there is no accuracy for the agent to win against *that* baseline — it cannot beat a procedure that is already right. The only thing left to compete on is cost: how many human interruptions get spent getting to the same answer.

**Week 2 qualified this.** Cost is still the objective, but cost alone hides a specific failure: an agent that takes one action on everything can post a good cost number while being unable to tell the states apart at all. Week 2 therefore reports per-class recall and balanced accuracy alongside cost, not because accuracy is the goal but because it is the diagnostic that catches an agent optimising the metric instead of the problem. That is exactly what it caught — see `results/fixes.md`.

So the objective is:

**Does a probabilistic, cost-aware policy reach the same decisions as escalate-everything while spending fewer human interruptions — and under what conditions does it stop doing so?**

The second half is the part I care about. A rule that wins under every assumption I could vary would be evidence that I had built the comparison badly, not evidence that the agent is good.

## Status

### Week 1

| Assignment deliverable | Status |
|---|---|
| §3 problem statement | **Done** — stated above and in `research-file.md` |
| §4 research file | **Done** — terms, queries, sources, questions, and the AI prompt/error tables |
| §5 Reddit discussions | **Partly done** — three threads across two communities, roughly sixteen substantive replies, four of which changed something. Against a target of ten contributions across five communities. The weakest deliverable |
| §6 X discussions | **Not started** |
| §7 discussion record | **Partly done** — all three threads logged in full with their design consequences. Bounded by §5 |
| §8 agent design | **Done** — all seven parts settled and implemented in `experiments/run_experiment.py` |
| §9 experiment | **Done** — five policies against the baseline on forty frozen cases, five one-at-a-time sweeps, a five-error regret analysis, a probe-price sweep, a consumer-hunt invariance test, a correlation-shrinkage sweep, and a 40,000-draw joint sensitivity study |
| §10 probability decision record | **Done** — one finding worked end to end in `decisions/` |
| §11 AI reviews | **Done** — four independent reviews, then three later rounds against the compiled paper, each comment accepted or rejected with evidence in `review-record.md` |
| §13 preprint | **Done** — `paper/main.tex` and `paper/main.pdf`, IJCAI-ECAI 26 format, nine pages |
| §14 publication | **Attempted, rejected** as basic and not research-worthy. The verdict and my reading of it are in `review-record.md` |

### Week 2

| Commit | What it added | What it found |
|---|---|---|
| W2-1 | Entropy, expected information gain, mutual information | The Week 1 invariance restated exactly: I(free features; live vs revoked) = 0.000000 bits |
| W2-2 | Information value against information cost | Bits and value rank evidence in near-opposite orders. The belief where the probe carries most information is the belief where it is worth nothing |
| W2-3 | Five states, 500 cases, P0–P3, calibration | Adding the missing states alone changed nothing — identical actions on all 500 cases |
| W2-4a | A scope field on the admin probe | The state plus the field that resolves it took regret 10.91 → 8.43 |
| W2-4b | Three fixes: `p_exploit`, escalation as a rule, a cost ceiling | the cost of dismissing a live key, 2400, had an unstated `p_exploit = 1.0`. Making it explicit at 0.10 took `fake` recall 0.000 → 0.954 and balanced accuracy 0.300 → 0.467 |
| W2-4c | Failure analysis, asymmetric feedback, a JS drift alarm | Asymmetric discovery drifts P(live) from 0.4356 to 0.2691 — the agent learns the world is safer than it is. The alarm catches it at 100% on a 500-window |
| W2-5 | Regret decomposition and a 15-cell cost sweep | The costs are **not** mis-specified. The 76.6% "wrong cost assumption" category was mis-labelled and is irreducible hedging |
| W2-6 | Age and registry channels (*c*, *k*); scope reliability (*q*) | Commit age is free evidence that breaks the invariance. The Week 1 result is a property of *static text*, not of repository evidence. And 88% of the scope field's value comes from a column I copied rather than the number I invented |
| W2-7 | A simulator whose world disagrees with the agent | Policy conclusions survive mis-specification in 100% of worlds. The structural conclusion does not |
| W2-8 | Bayes-factor model comparison, H0 vs H1 | The broken invariance is detectable in 100% of runs at δ ≥ 0.10, from the agent's own biased feedback. The skew costs nothing; the sample size costs everything |
| W2-9 | The Week 2 paper | Not started |

Everything in Week 2 is an experiment plus a write-up. The results are in `results/`, one markdown file and one JSON file per experiment.

## Repeating the test

Python 3.9 or later. No third-party packages for the experiments; the figures
need `matplotlib`.

### Week 1

```bash
cd experiments

python run_experiment.py    # the agent, six policies, five one-at-a-time
                            # sweeps. Rewrites results/summary.json and,
                            # if data/cases.json is absent, regenerates the
                            # forty cases from seed 20260827
python errors.py            # regret analysis over the frozen cases
                            # -> results/errors.json
python probe_sweep.py       # what the probe price buys
python consumer_probe.py    # boundary invariance under the consumer-hunt cost
python shrinkage.py         # what survives a correlation correction
                            # -> results/shrinkage.{md,json}
python monte_carlo.py       # 40,000-draw joint sensitivity, about a minute
                            # -> results/robustness.json
```

### Week 2

Run in this order. Each script imports the ones before it.

```bash
cd experiments

python information.py        # entropy, expected information gain, mutual
                             # information -> results/information.{md,json}
python evidence_selection.py # bits against minutes
                             # -> results/evidence-selection.{md,json}
python week2_experiment.py   # five states, 500 cases from seed 20260902,
                             # P0-P3, calibration
                             # -> results/week2-results.{md,json}
python scope_probe.py        # the scope field -> results/scope-probe.{md,json}
python fixes.py              # p_exploit, escalation rule, cost ceiling
                             # -> results/fixes.{md,json}
python feedback.py           # failure analysis, asymmetric discovery, the
                             # drift alarm -> results/feedback.{md,json}
python cost_sensitivity.py   # regret decomposition, 15-cell cost sweep
                             # -> results/cost-sensitivity.{md,json}
python registry.py           # commit age and registry coverage, swept
                             # -> results/registry.{md,json}
python scope_sensitivity.py  # scope reliability q, swept
                             # -> results/scope-sensitivity.{md,json}
python misspecified.py       # a world that disagrees with the agent, ~2 min
                             # -> results/misspecified.{md,json}
python model_uncertainty.py  # Bayes factor, H0 vs H1, ~3 min
                             # -> results/model-uncertainty.{md,json}
```

`data/cases.json` is committed and is not regenerated while it exists. Delete it
only if you intend to change the frozen Week 1 case set, because every
realised-cost number in the paper is measured on exactly those forty cases. The
Week 2 cases are not stored — they are regenerated deterministically from seed
20260902 every run.

Every script is deterministic. `run_experiment.py` fixes seed 20260827,
`monte_carlo.py` fixes 20260828, `week2_experiment.py` fixes 20260902, and the
Week 2 scripts that need their own randomness fix their own seeds. A clean
checkout reproduces every file in `results/` byte for byte, with two exceptions:
`results/findings.md` and `results/error-analysis.md` are written by hand, not
by a script.

The paper builds with:

```bash
cd paper
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

`ijcai26.sty` and `named.bst` come from the official IJCAI author kit and are
gitignored rather than redistributed. Figures are rebuilt with
`python figures/make_figures.py`.

## What is in here

### Documents

| Path | What it holds |
|---|---|
| `research-file.md` | The working document: problem, scope, provider choice, cost model, belief model, policy, feedback, sources, and the AI prompt and error tables |
| `discussion-record.md` | Every public contribution and what it changed |
| `review-record.md` | AI reviews, each comment accepted or rejected with a reason |
| `decisions/decision-log.md` | Every decision from the first commit onward: the options, the choice, the reasoning, and what it later turned out to cost |
| `decisions/probability-decision-record.md` | §10 — one finding taken all the way through, including a probe priced at zero value |
| `paper/main.tex`, `paper/main.pdf` | The **Week 1** preprint, IJCAI-ECAI 26 format. It predates every Week 2 result and is kept as the Week 1 artifact |
| `paper/preprint.md` | The same Week 1 argument in markdown |
| `paper/limitations.md` | The long-form limitations |

### Week 1 code and results

| Path | What it holds |
|---|---|
| `experiments/run_experiment.py` | The agent and the policy comparison |
| `experiments/errors.py` | Regret analysis over the frozen cases |
| `experiments/probe_sweep.py` | Where buying evidence starts to pay |
| `experiments/consumer_probe.py` | Why probing which systems use the key cannot help: the hunt cost appears identically in both remediation actions, so the boundary is invariant |
| `experiments/shrinkage.py` | What survives when the two free features are treated as correlated rather than independent |
| `experiments/monte_carlo.py` | Joint sensitivity over the whole cost and evidence model |
| `results/findings.md` | What the experiment said |
| `results/error-analysis.md` | Five incorrect decisions, examined |
| `results/robustness.md` | Which conclusions survive when everything is wrong at once |
| `results/shrinkage.md` | The invariance survives any dependence correction; the *fake* collapse does not |
| `data/cases.json` | Forty frozen cases, written once and never regenerated |

### Week 2 code and results

| Path | What it holds |
|---|---|
| `experiments/information.py` | Entropy, expected information gain, mutual information |
| `experiments/evidence_selection.py` | What evidence is worth buying, in minutes rather than bits |
| `experiments/week2_experiment.py` | The five-state agent, 500 cases, four policies, calibration |
| `experiments/scope_probe.py` | A scope field on the admin probe, and the state it resolves |
| `experiments/fixes.py` | The three fixes: explicit exploitation probability, escalation as a rule, a worst-case cost ceiling |
| `experiments/feedback.py` | What the agent learns from asymmetric feedback, and the drift alarm that catches it |
| `experiments/cost_sensitivity.py` | Regret by cause, and a 15-cell sweep of the cost matrix |
| `experiments/registry.py` | Commit age and registry coverage as new evidence channels, both swept |
| `experiments/scope_sensitivity.py` | The scope field's reliability, swept, because it was the last invented number |
| `experiments/misspecified.py` | The agent in a world generated from different tables |
| `experiments/model_uncertainty.py` | A Bayes factor that asks whether the agent's structural assumption is the right model |
| `results/information.md` | The invariance restated exactly, in bits |
| `results/evidence-selection.md` | Bits and value rank evidence differently |
| `results/week2-results.md` | Five states, 500 cases, the policy ladder |
| `results/scope-probe.md` | Where the regret drop actually comes from |
| `results/fixes.md` | The hidden `p_exploit = 1.0`, and what removing it did |
| `results/feedback.md` | The failure breakdown, the drift, and the alarm |
| `results/cost-sensitivity.md` | Whether the cost model is wrong, or whether that is hedging |
| `results/registry.md` | The evidence that breaks the invariance |
| `results/scope-sensitivity.md` | How much of the best agent rests on one invented number |
| `results/misspecified.md` | What survives when the model is wrong, amended after W2-8 |
| `results/model-uncertainty.md` | Whether the agent can notice its own assumption is wrong |

## Honest state of the work

The public-discussion requirements — §5 and §6 — are the weakest part. Two
communities against a target of five, and nothing on X. They are also the
requirements nobody else can meet for me, and the ones my cost numbers are
supposed to come from.

That said, they are no longer producing nothing. Two practitioner replies
changed published numbers: one repriced the probe by a factor of ten, which
moved the investigate action from never selected to selected on about 4% of
findings; another withdrew an assumption I had been leaning on, that rotating a
key verifies itself. A third established that live-versus-revoked is a solved
problem for certificates and an unsolved one for API keys, which is the clearest
justification I have for the scope I chose.

**The Week 1 paper was submitted and rejected**, as basic and not
research-worthy. I think that verdict was right for what it was. Every input was
an estimate, the machinery is Raiffa and Schlaifer, and my own related-work
paragraph said the contribution was the instance rather than the method.

Week 2 changed what I can claim, in three specific ways.

**The headline Week 1 result is narrower than I stated it.** I reported that the
free features carry zero information about live-versus-revoked as though it were
a property of the problem. `registry.py` shows it is a property of *static text*:
commit age is free, sits in the same repository, and breaks the invariance
immediately. That is a real correction to a published claim, not a caveat.

**The agent had a failure that cost reporting could not see.** Before W2-4b it
took one action on almost everything and posted a respectable cost number while
being unable to produce the `fake` label at all — recall 0.000. The cause was a
breach cost carrying an unstated certainty. Cost alone would never have surfaced
it; per-class recall did, in one table.

**Three numbers that were mine are now parameters.** Exploitation probability,
registry coverage and rotation compliance, and scope reliability are each swept
rather than asserted, and in each case the useful finding turned out to be where
the conclusion changes rather than what it equals at a point estimate.

What has not changed: every cost number except the probe is still my own
estimate, and no part of this has ever been measured against real labelled
findings. W2-7 prices what that costs when the estimates are wrong, and W2-8
gives the agent a way to notice — but noticing is not measuring, and the gap
between them is still the honest limit of the project.
