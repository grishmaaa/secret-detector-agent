# Probability Decision Record

## Case

_[Select one case for which the correct state is not known]_

## Evidence

> Information that the agent observed.

## Hidden States

> Possible explanations.

## Beliefs

> Probability of each hidden state. The sum of all hidden-state probabilities must be 100 percent.

## Event

> Hidden states that are important to the user.

## Actions

> Available actions.

## Costs

> Results of correct and incorrect actions.

## Policy

> Decision rule and threshold.

## Decision

> Selected action and reason.

## Audit Data

> Time, data version, model version, and policy version.

---

## Bayesian Update

> Add one new item of evidence and complete these steps.
> Use recent and comparable historical cases.
> Do not use a large data group only because it is easy to find.
> Search for evidence for the safe state and the unsafe state.

1. State the prior probability.
2. State the new evidence.
3. Estimate the likelihood for each important hidden state.
4. Calculate or simulate the posterior probability.
5. Compare the posterior probability with the decision threshold.
6. Record the new action.
