# Which evidence is worth obtaining

W2-1 asked what each source is worth in bits. This asks what each is
worth in engineer-minutes. The two answers rank the sources
differently, and the disagreement is the finding.

## The comparison table

| Evidence | Exp. gain (bits) | Bits about live-vs-revoked | Cost | Time | EVSI (min) | Can it change the action? | If it is wrong |
|---|---|---|---|---|---|---|---|
| Repository context (path, name, commit message) | 0.2909 | 0.0000 | free | seconds, automated | 0.0000 | **no** | A production-looking path around a fixture, or a fixture path in a repository that deploys from tests |
| Well-formedness (format match) | 0.3250 | 0.0000 | free | milliseconds, regex | 1.2696 | yes | An organisation that commits base-encoded real credentials by convention inverts this feature rather than weakening it |
| Probe: last_used_at from our own admin API | 0.6051 | 0.3358 | 3 min | one API call plus the engineer around it | 0.0000 | **no** | A live key that has been idle for months looks like a dead one; the field is silence, and silence is not death |

EVSI is measured at the prior, before anything has been observed. The
probe is measured again below at each belief the agent can actually
hold, which is the number that governs whether it gets bought.

## The two rankings

| Rank | By bits | By minutes saved |
|---|---|---|
| 1 | Probe: last_used_at from our own admin API (0.6051 bits) | Well-formedness (1.2696 min) |
| 2 | Well-formedness (0.3250 bits) | Repository context (0.0000 min) |
| 3 | Repository context (0.2909 bits) | Probe: last_used_at from our own admin API (0.0000 min) |

The probe is the most informative source in the table — 0.6051 bits, and the only one carrying anything at all
about live versus revoked. It is also the only one that costs money.
Repository context carries 0.2909 bits, less than the probe,
and carries exactly none of them about the axis the decision turns on —
yet it is free, so its value per minute spent is unbounded and it
should always be read first. Order follows from cost, not from bits.

## Evidence I can name but cannot price

Two channels came out of the practitioner discussions and are not in
the model. I am listing them without bits, deliberately: I have no
likelihood tables for them, and inventing tables so that they could
appear in the comparison would produce numbers that look measured and
are not. **You cannot price evidence you have not modelled**, and the
honest form of that is an empty cell rather than a plausible one.

| Channel | Cost | Time | Why it matters |
|---|---|---|---|
| Secret-store hash comparison | under 1 min | one lookup | Compare a hash of the finding against the current stored value. Dispositive when it hits. Absence is uninformative rather than favourable, because a credential created outside the provisioning pipeline is absent and may still authenticate. |
| expires_at from the same admin call | 0 additional min | already paid for | Arrives on the call already priced at 3 minutes, and an expiry in the past is deterministic where last_used_at is only suggestive. Strictly more information at strictly no extra cost. |

## The critical question: is the most informative check always the best one?

No, and this model answers it twice, in opposite directions.

### Case one — where bits and value agree

Compare the two free features against each other. Well-formedness
carries 0.3250 bits against repository context's
0.2909, and it is also worth more: 1.2696 minutes
against 0.0000. Ranking those two by bits gives the right
answer, because a malformed string collapses *fake* hard enough to
cross a decision boundary, and the movement and the crossing happen
together. When evidence moves a belief across a line, more movement is
more value and the two rankings coincide.

### Case two — it is not

Now ask where the agent actually stands. After the free features it
holds one of six beliefs. The probe is worth its price in exactly one
of them, and the ordering by bits is close to the reverse of the
ordering by value.

| Context | Form | P(seen) | Entropy | Probe bits | Probe EVSI (min) | Action now | Actions reachable | Buy at 3 min? |
|---|---|---|---|---|---|---|---|---|
| production | well-formed | 0.4505 | 1.0202 | 0.3534 | 0.0000 | rotate | rotate | no |
| neutral | well-formed | 0.2477 | 1.3194 | 0.4747 | 0.0000 | rotate | rotate | no |
| placeholder | well-formed | 0.1442 | 1.4846 | 0.6564 | 0.0000 | rotate | rotate | no |
| placeholder | malformed | 0.1057 | 0.0675 | 0.0230 | 1.4012 | revoke | dismiss, revoke, rotate | no |
| neutral | malformed | 0.0398 | 0.3672 | 0.1589 | 5.2118 | revoke | revoke, rotate | **yes** |
| production | malformed | 0.0120 | 1.3079 | 0.5998 | 0.0000 | rotate | rotate | no |

| Rank | Most bits | Most minutes saved |
|---|---|---|
| 1 | placeholder+well-formed (0.6564 bits) | neutral+malformed (5.2118 min) |
| 2 | production+malformed (0.5998 bits) | placeholder+malformed (1.4012 min) |
| 3 | neutral+well-formed (0.4747 bits) | placeholder+well-formed (0.0000 min) |
| 4 | production+well-formed (0.3534 bits) | neutral+well-formed (0.0000 min) |
| 5 | neutral+malformed (0.1589 bits) | production+well-formed (0.0000 min) |
| 6 | placeholder+malformed (0.0230 bits) | production+malformed (0.0000 min) |

**The two orderings are almost exactly reversed.** The belief where the
probe carries the most information is the one where it is worth
nothing, and the belief where it carries the least is the one where it
is worth the most. This is not a coincidence in the arithmetic: a
belief with high entropy is one where the agent is unsure *among
states*, and a belief near a boundary is one where it is unsure *among
actions*. Those are different kinds of doubt, and only the second one
is worth money.

Read the row `placeholder + well-formed`. The probe carries
**0.6564 bits** there — real information, more than either
free feature carries anywhere — and its value is
**0.0000 minutes**, because no outcome of it changes what
the agent does. Every branch still ends in `rotate`.

So the agent would pay three minutes to become measurably better
informed and then take the action it was already going to take. The
information is real. The value is zero. Buying it is a pure loss of
3 minutes.

**The rule that falls out.** Bits measure how much a belief moves.
Value measures whether the movement crosses a line that matters. A
belief can travel a long way inside one decision region and arrive
nowhere. Before buying evidence the question is not *how much will I
learn* but *is there an answer to this that would make me act
differently* — and if there is not, the price of the check is the whole
of its cost and none of its benefit, however many bits it carries.

## Why this matters more here than in most problems

The agent's decision boundary sits at P(live) = 0.06588, and the
cheapest remediation is tolerable in every state. That combination
makes the decision region enormous: almost every belief the agent can
reach falls inside it, so almost every piece of evidence moves the
belief without moving the decision. A problem with a boundary near 0.5
would buy evidence far more often. **The value of information is a
property of the cost matrix, not of the evidence.**

