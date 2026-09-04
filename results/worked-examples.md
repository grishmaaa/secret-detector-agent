# Three things worked out by hand

The paper has to show a full belief update rather than report its
result, five candidate questions priced, and the umbrella problem in my
own numbers. All three are small enough to check on paper, which is the
point. They are also computed here with the same functions the agent
uses, so if the paper and the code ever drift apart this file is what
catches it.

## 1. One belief update, all four columns

The finding: a **well-formed** string on a **production**
path. Two free features, no probe, no purchase.

| State | Prior | P(production｜s) | P(well-formed｜s) | Prior x likelihoods | Posterior |
|---|---|---|---|---|---|
| `live` | 0.4356 | 0.600 | 0.990 | 0.258746 | 0.5780 |
| `revoked` | 0.2673 | 0.600 | 0.990 | 0.158776 | 0.3547 |
| `fake` | 0.2475 | 0.050 | 0.400 | 0.004950 | 0.0111 |
| `zero_scope` | 0.0396 | 0.600 | 0.990 | 0.023522 | 0.0525 |
| `other` | 0.0100 | 0.333 | 0.500 | 0.001667 | 0.0037 |
| **total** | **1.0000** | | | **0.447662** | **1.0000** |

Multiply across, add the column, divide each row by the total. That is
the whole of Bayes' theorem and there is nothing else in it.

Entropy falls from **1.7805** to **1.3127** bits, a gain of
0.4678. `fake` drops from 0.2475 to
0.0111 -- the evidence is almost entirely about that state.

**And the thing the update does not do is the point of the project.**
`live` moves from 0.4356 to 0.5780 and `revoked`
moves with it: the ratio between them is 1.6296 before and
1.6296 after. It is unchanged to every digit, because the two
rows of both likelihood tables are identical. The agent has learned
something real about whether this is a credential at all, and exactly
nothing about whether it still works.

## 2. Five questions the agent could ask

Value is EVSI -- expected minutes of decision cost removed -- computed
at the belief above, not at the prior. An evidence source is worth what
it changes from where the agent is standing.

| Question | Answers | Bits | Value, min | Cost, min | Time | Ask? |
|---|---|---|---|---|---|---|
| Is the string on a production-looking path? | placeholder / neutral / production | 0.0199 | 0.0000 | 0 | milliseconds, already read | no |
| Does the string match the provider's key format? | well-formed / malformed | 0.0380 | -0.0000 | 0 | milliseconds, one regex | no |
| Is the commit older than the rotation period? | old / young | 0.0000 | 0.0000 | 0 | seconds, git metadata | no |
| When did our own admin API last see this key used? | recent / old / null | 0.6642 | 2.9130 | 3 | 3 min, one API call plus the engineer around it | no |
| Does the string match a currently-deployed secret hash? | match / miss | 0.2245 | -0.0000 | 1 | 1 min, one lookup | no |

- *Is the string on a production-looking path?* Free, and already counted in the belief this table is computed from.
- *Does the string match the provider's key format?* Free, and likewise already in the belief.
- *Is the commit older than the rotation period?* Free. Worth nothing at c = 0.5 and worth a great deal at c = 0.9; the parameter is the organisation, not the evidence.
- *When did our own admin API last see this key used?* The scope field arrives on the same call, so they are priced together.
- *Does the string match a currently-deployed secret hash?* A match is near-proof of live. A miss is only as informative as the provisioning pipeline is complete.

**The agent asks none of them here, and the near miss is the**
**instructive part.** The admin probe carries 0.6642 bits, more than
everything else on the table put together, and is worth
2.9130 minutes against a price of 3. It loses by 0.087 of a
minute. Ranked by bits it is the obvious purchase; ranked by minutes it
is declined, and the two rankings are not close to each other.

The registry lookup is the sharper case. It carries 0.2245 bits and is
worth exactly nothing, because at this belief every answer it could
give leaves `rotate` cheapest. Information that changes what you pay but
not what you do is worth zero, whatever its bit count.

The two free channels show 0.0000 by construction -- they are already in
the belief the table is computed from. They appear because a reader
should see that they were asked first, and why: they cost nothing, so
nothing has to be priced before asking them.

The age channel is the one whose character changes with the deployment.
At c = 0.5 -- an organisation that rotates at random -- it is worth
0.0000
minutes. At c = 0.9 it is worth 1.4817. Same evidence,
same cost, and the difference is a fact about the company rather than
about secret scanning.

### Where the agent does buy, and why it is not where I expected

Whether to buy is not a property of the probe. It is a property of
where the agent is standing when it asks. The same question, priced
from all six beliefs the two free features can produce:

| Repository context | Format | The two features | P(live) | Cheapest action | Probe worth | Net | Buy? |
|---|---|---|---|---|---|---|---|
| placeholder | well-formed | conflict | 0.2985 | rotate | 9.6114 | +6.611 | **yes** |
| placeholder | malformed | agree | 0.0041 | dismiss | 0.4475 | -2.552 | no |
| neutral | well-formed | one is silent | 0.5239 | rotate | 4.1701 | +1.170 | **yes** |
| neutral | malformed | one is silent | 0.0319 | dismiss | 3.4179 | +0.418 | **yes** |
| production | well-formed | agree | 0.5780 | rotate | 2.9130 | -0.087 | no |
| production | malformed | conflict | 0.1929 | rotate | 9.5111 | +6.511 | **yes** |

**The only two beliefs the agent declines to buy from are the two where
its free features agree with each other.** A malformed string on a
placeholder path -- both say *not a credential* -- and a well-formed key
on a production path, where both say *a real key in a real place* and
which is the case that looks most alarming to a person. It buys on all
four of the others, and the two largest purchases, +6.61 and +6.51, are
the two outright contradictions.

That is not a heuristic anyone wrote. It falls out of the value rule.
When both features point the same way the belief is already far enough
from the boundary that no probe outcome can move the action across it,
so the information is worth nothing however alarming the finding looks.
When they conflict, the belief sits near the boundary and the probe can
flip it. **The agent spends its budget on its own confusion rather than
on apparent severity**, and a triage queue sorted by severity would
have bought the opposite set.

## 3. The umbrella, and why it is the same equation

There is a 35% chance of rain. Costs in units of annoyance,
and they are assumptions:

| | Carry it and no rain | Get wet | Cost if I carry | Cost if I do not | Break-even | Decision |
|---|---|---|---|---|---|---|
| A walk to the shop | 2 | 5 | 2.00 | 1.75 | 0.400 | **leave it** |
| A wedding, in clothes I cannot replace | 2 | 200 | 2.00 | 70.00 | 0.010 | **take it** |

Same 35%. Opposite decisions. The probability decided nothing;
the consequences did. And the break-even is one division -- the cost of
the cheap mistake over the cost of both mistakes together.

My agent's boundary is that division and no other:

| | Minutes |
|---|---|
| False positive: rotate a key that was already revoked | 30 |
| False negative: dismiss a key that is live | 244.5 |
| **Break-even belief** | **0.1093** |

10.9% -- not a number anyone chose. The
wedding is the interesting case for the same reason the live key is:
one of the two mistakes is so much worse than the other that the
threshold ends up nowhere near the middle. A reader who follows the
umbrella follows the agent, which is why it appears first in the paper.

