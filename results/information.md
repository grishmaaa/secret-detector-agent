# The information layer

Every number here is computed from the Week 1 model. Nothing was
re-parameterised. Log base 2 throughout, so the unit is bits and one
bit is one good yes/no question's worth of uncertainty.

Prior over the three hidden states: live 0.48, revoked 0.27, fake 0.25.
Its entropy is **1.5183 bits**, against a maximum of 1.5850 for three equally likely states. The agent starts
only slightly better informed than knowing nothing.

## What each evidence source is worth

The distinction that matters: *gain* is what you learned after seeing
one particular result. *Expected* gain is the average over the results
you might get, weighted by how likely each is, and it is the number
that decides which check to run, because you have to choose before
you know the answer.

| Evidence | H before | H after (expected) | **Expected gain** | Best single outcome | Worst single outcome |
|---|---|---|---|---|---|
| context | 1.5183 | 1.2274 | **0.2909** | production (+0.4218) | neutral (+0.0252) |
| well-formedness | 1.5183 | 1.1933 | **0.3250** | malformed (+1.1972) | well-formed (+0.1619) |
| both free features | 1.5183 | 1.0381 | **0.4802** | placeholder+malformed (+1.4508) | placeholder+well-formed (+0.0337) |
| probe (last_used_at) | 1.5183 | 0.9132 | **0.6051** | recent (+1.3167) | null (+0.1905) |
| everything | 1.5183 | 0.6507 | **0.8676** | placeholder+malformed+null (+1.5006) | neutral+well-formed+null (-0.0286) |

## The same question, asked about the axis that matters

The three-state numbers above are flattering, because most of what the
free features do is rule out *fake*. The decision, though, turns on
live versus revoked. So condition on the string being a real
credential and ask the question again.

On that restriction the prior is live 0.6400, revoked 0.3600, and its entropy is **0.9427 bits**.

| Evidence | Expected gain about live-vs-revoked | Fraction of the 0.9427 bits |
|---|---|---|
| context | **0.000000** | 0.00% |
| well-formedness | **0.000000** | 0.00% |
| both free features | **0.000000** | 0.00% |
| probe (last_used_at) | **0.335772** | 35.62% |

**This is the Week 1 invariance, restated exactly.** Section 4.3 of the
Week 1 paper says the two free features cannot separate live from
revoked, and shows the posterior ratio staying at 1.778. In bits the
same statement is that the mutual information between those features
and the live-versus-revoked distinction is **0.000000 bits**.

Exactly zero, not approximately zero. It is not a small number that
happened to come out near nothing; it is a consequence of the two
states carrying identical likelihood rows, and identical rows cannot
discriminate between the states they belong to. The computation
returns floating-point noise around 1e-16, which this script snaps to
zero rather than printing, because reporting it as a tiny non-zero
quantity would misrepresent an exact result as a measured one.

The probe carries **0.3358 bits** about the same axis, which is 35.6% of everything there is
to know about it. That is the whole asymmetry of this problem in two
numbers: the free evidence carries none of what the decision needs, and
the evidence that carries it has to be bought.

## Does any observation make the agent more confused?

Yes. Expected information gain is never negative, but the gain from a
*single* outcome can be, and here it is:

| Evidence | Outcome | P(outcome) | H before | H after | Change |
|---|---|---|---|---|---|
| everything | neutral+well-formed+null | 0.0683 | 1.5183 | 1.5469 | **-0.0286** |

This is not an arithmetic error. The prior leans towards *live*; an
outcome that knocks the leading explanation down without promoting a
single replacement leaves the belief flatter than it found it. The
agent has correctly moved from a confident guess to an honest
admission that it does not know, and entropy is the number that
records the change.

## The six beliefs the agent can actually hold

After the free features, and before any purchase.

| Context | Form | P(seen) | live | revoked | fake | Entropy | live:revoked | Probe EIG here |
|---|---|---|---|---|---|---|---|---|
| production | well-formed | 0.4505 | 0.6329 | 0.3560 | 0.0111 | 1.0202 | 1.7778 | 0.3534 |
| neutral | well-formed | 0.2477 | 0.5754 | 0.3237 | 0.1009 | 1.3194 | 1.7778 | 0.4747 |
| placeholder | well-formed | 0.1442 | 0.3294 | 0.1853 | 0.4853 | 1.4846 | 1.7778 | 0.6564 |
| placeholder | malformed | 0.1057 | 0.0045 | 0.0026 | 0.9929 | 0.0675 | 1.7778 | 0.0230 |
| neutral | malformed | 0.0398 | 0.0362 | 0.0204 | 0.9434 | 0.3672 | 1.7778 | 0.1589 |
| production | malformed | 0.0120 | 0.2400 | 0.1350 | 0.6250 | 1.3079 | 1.7778 | 0.5998 |

The live:revoked column is the invariance seen directly: identical to
four decimal places in every row the agent can reach, including rows
where the entropy differs by more than a bit.

The last column is worth reading against the Week 1 result that the
probe is bought on about 4% of findings. The probe carries useful bits
in every row. It is worth *paying* for in almost none of them, because
bits and value are different quantities and only one of them is what
the agent is spending minutes on. Commit W2-2 prices that difference.

