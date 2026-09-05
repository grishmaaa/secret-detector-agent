# src

Empty on purpose. The agent, the policies and every experiment live in
`experiments/`, and the paper and results reference them by that path.

## Week 1

| File | What it is |
|---|---|
| `experiments/run_experiment.py` | The agent: prior, likelihoods, cost matrix, the four terminal actions and the probe, plus the five policies and the closed-form comparison |
| `experiments/errors.py` | Regret analysis over the forty frozen cases |
| `experiments/probe_sweep.py` | Where buying the probe starts to pay |
| `experiments/consumer_probe.py` | Why probing the key's consumers cannot move the boundary |
| `experiments/shrinkage.py` | What survives when the free features are treated as correlated |
| `experiments/monte_carlo.py` | Joint sensitivity over the whole cost and evidence model |

## Week 2

These import from `run_experiment.py` and from each other, in this order.

| File | Imports from | What it is |
|---|---|---|
| `experiments/information.py` | `run_experiment` | Entropy, expected information gain, mutual information |
| `experiments/evidence_selection.py` | `information` | What evidence is worth buying, in minutes rather than bits |
| `experiments/week2_experiment.py` | `information` | The five-state agent: prior, likelihood tables, 500 cases, four policies, calibration |
| `experiments/scope_probe.py` | `week2_experiment` | A scope field on the admin probe, and the state it resolves |
| `experiments/fixes.py` | `scope_probe` | Explicit exploitation probability, escalation as a rule, a worst-case cost ceiling. **The cost matrix every later script uses comes from `fixes.costs()`** |
| `experiments/feedback.py` | `fixes` | Asymmetric discovery, belief drift, and the Jensen–Shannon drift alarm |
| `experiments/cost_sensitivity.py` | `fixes` | Regret by cause, and a 15-cell sweep of the cost matrix |
| `experiments/registry.py` | `fixes` | Commit age and registry coverage as evidence channels, both swept |
| `experiments/scope_sensitivity.py` | `fixes`, `scope_probe` | The scope field's reliability parameter, swept |
| `experiments/misspecified.py` | `fixes` | The agent against an agent that knows the true tables, in worlds the agent's model gets wrong |
| `experiments/model_uncertainty.py` | `fixes`, `feedback` | A Bayes factor between the agent's structural assumption and its negation |
| `experiments/worked_examples.py` | `fixes`, `registry`, `scope_probe` | The three pieces the paper shows by hand rather than reports |
| `experiments/generalization.py` | `fixes`, `scope_probe` | The same agent on a credential that does not hide its identifier |
| `experiments/stability.py` | `fixes` | How much of each headline is one draw: 200 scope-draw seeds |

The project is one model rather than a library, so it is written as a small
number of scripts that import from each other instead of a package. Splitting it
across modules would have added structure without adding clarity.

Every script writes to `results/`, one markdown file for the argument and one
JSON file for the numbers behind it. Two files in `results/` are written by hand
rather than by a script: `findings.md` and `error-analysis.md`.
