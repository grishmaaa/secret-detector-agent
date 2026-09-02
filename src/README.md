# src

Empty on purpose. The agent, the policies and every experiment live in
`experiments/`, and the paper and results reference them by that path:

| File | What it is |
|---|---|
| `experiments/run_experiment.py` | The agent: prior, likelihoods, cost matrix, the four terminal actions and the probe, plus the five policies and the closed-form comparison |
| `experiments/errors.py` | Regret analysis over the forty frozen cases |
| `experiments/probe_sweep.py` | Where buying the probe starts to pay |
| `experiments/consumer_probe.py` | Why probing the key's consumers cannot move the boundary |
| `experiments/shrinkage.py` | What survives when the free features are treated as correlated |
| `experiments/monte_carlo.py` | Joint sensitivity over the whole cost and evidence model |

The project is one model rather than a library, so it is written as a small
number of scripts that import from `run_experiment.py` instead of a package.
Splitting it across modules would have added structure without adding clarity.
