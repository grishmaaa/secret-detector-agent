# Deciding what to do about a possible key in a repository

A cost-aware triage agent for secret-scanner findings.

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
| §4 research file | **Done** — terms, queries, sources, questions, and the AI prompt/error tables. The X accounts table is candidates only |
| §5 Reddit discussions | **Partly done** — three threads across two communities, roughly sixteen substantive replies, four of which changed something. Against a target of ten contributions across five communities. The weakest deliverable |
| §6 X discussions | **Not started** |
| §7 discussion record | **Partly done** — all three threads logged in full with their design consequences. Bounded by §5 |
| §8 agent design | **Done** — all seven parts settled and implemented in `experiments/run_experiment.py` |
| §9 experiment | **Done** — five policies against the baseline on forty frozen cases, five one-at-a-time sweeps, a five-error regret analysis, a probe-price sweep, a consumer-hunt invariance test, a correlation-shrinkage sweep, and a 40,000-draw joint sensitivity study. Results in `results/` |
| §10 probability decision record | **Done** — one finding worked end to end in `decisions/` |
| §11 AI reviews | **Done** — four independent reviews of the draft, then three later rounds against the compiled paper, each comment accepted or rejected with evidence in `review-record.md`. Three claims tested and rejected; three review-supplied numbers found wrong |
| §13 preprint | **Done** — `paper/main.tex` and `paper/main.pdf`, IJCAI-ECAI 26 format, nine pages, compiling clean. `paper/preprint.md` is kept as the markdown source of the same argument |
| §14 publication | **Attempted, rejected.** Submitted and returned as basic and not research-worthy. The verdict and my reading of it are in `review-record.md`. No venue chosen yet |

## Repeating the test

Python 3.9 or later. No third-party packages for the experiments; the figures
need `matplotlib`.

```bash
cd experiments

python run_experiment.py    # the agent, six policies, five one-at-a-time
                            # sweeps. Rewrites results/summary.json and,
                            # if data/cases.json is absent, regenerates the
                            # forty cases from seed 20260827
python errors.py            # regret analysis over the frozen cases
                            # -> results/error-analysis.md, results/errors.json
python probe_sweep.py       # what the probe price buys
python consumer_probe.py    # boundary invariance under the consumer-hunt cost
python shrinkage.py         # what survives a correlation correction
                            # -> results/shrinkage.md, results/shrinkage.json
python monte_carlo.py       # 40,000-draw joint sensitivity, about a minute
                            # -> results/robustness.md, results/robustness.json
```

`data/cases.json` is committed and is not regenerated while it exists. Delete it
only if you intend to change the frozen case set, because every realised-cost
number in the paper is measured on exactly those forty cases. The expected costs
are closed-form over all 54 possible worlds and do not depend on the file.

Every script is deterministic. `monte_carlo.py` fixes seed 20260828 and
`run_experiment.py` fixes 20260821, so a clean checkout reproduces every number
in `results/` and in the paper exactly.

The paper builds with:

```bash
cd paper
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

`ijcai26.sty` and `named.bst` come from the official IJCAI author kit and are
gitignored rather than redistributed. Figures are rebuilt with
`python figures/make_figures.py`.

## What is in here

| Path | What it holds |
|---|---|
| `research-file.md` | The working document: problem, scope, provider choice, cost model, belief model, policy, feedback, sources, and the AI prompt and error tables |
| `discussion-record.md` | Every public contribution and what it changed |
| `review-record.md` | Four AI reviews, each comment accepted or rejected with a reason |
| `decisions/probability-decision-record.md` | §10 — one finding taken all the way through, including a probe priced at zero value |
| `decisions/decision-log.md` | Every decision from the first commit onward: the options, the choice, the reasoning, and what it later turned out to cost |
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
| `paper/main.tex`, `paper/main.pdf` | The preprint, IJCAI-ECAI 26 format |
| `paper/preprint.md` | The same argument in markdown |
| `paper/limitations.md` | The long-form limitations |
| `data/cases.json` | Forty frozen cases, written once and never regenerated |

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

Every cost number except the probe is still my own estimate. That is why the
project ends in a 40,000-draw sensitivity study rather than a point estimate,
and why the conclusions I keep are about ordering rather than magnitude.

**The paper was submitted and rejected**, as basic and not research-worthy. I
think that verdict is right and I am not going to soften it here. Every input is
an estimate, the machinery is Raiffa and Schlaifer, and my own related-work
paragraph says the contribution is the instance rather than the method. A
sensitivity study shows that the conclusions survive the parameters moving; it
cannot show that the parameters were ever right.

Two things point at the version of this that would be research. A practitioner
observed that credentials which expose a public identifier — an AWS `AKIA`
access key ID, a Stripe `sk_test_` prefix, a JWT's `exp` claim — let you read
liveness straight off your own admin API, which means the problem I chose is a
property of credential formats that hide the identifier rather than of secret
scanning. And an independent reparameterisation of the model in dollars, with
every figure sourced, reached the same conclusion mine did about ignore being
unreachable, while naming the one number nobody has published: the share of real
secrets that are production secrets. That is small, checkable, and measurable
from a dataset that exists.

Neither is in the paper yet. Both are recorded in `review-record.md` and
`discussion-record.md` so the next version starts from them rather than from
where this one stopped.
