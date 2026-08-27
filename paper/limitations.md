# Limitations

Draft for the preprint. I have kept the ones that would change a result
separate from the ones that only narrow what the result applies to, because a
reader should be able to tell those apart quickly.

## 1. Where the model is deliberately wrong

**It decides once, and the world does not.** Every action here is atomic — the
agent forms a belief, picks one action, and the case ends. Rotate safely is not
atomic. It is issue a key, find the consumers, update them, deploy, confirm
nothing is calling the old one, revoke. Evidence arrives partway through that
sequence, and a sequential formulation could abandon the remaining steps when
it does. Mine cannot; it commits at the start and pays the average. This almost
certainly understates the value of investigating, because a model that can stop
halfway has more places for information to be useful.

**Two of the five actions are not the same kind of object as the other three.**
Dismiss, revoke now and rotate safely are terminal: they end the case and
compete on expected cost. Investigate does not end anything — it buys an answer
and returns the decision to the agent, so its cost cell is an entry fee rather
than a price, and it is compared on whether what it buys exceeds what it costs
rather than by being placed in the same minimisation. I handle that correctly in
the implementation but the fifteen-cell presentation obscures it.

Escalate has the same problem for a different reason. I priced it as an
epistemic act — thirty minutes of human attention, after which the human takes
the correct action — and under that pricing it loses at every belief in the
simplex. But escalation in practice is frequently a *permission* boundary: the
agent is not authorised to revoke a key owned by another team, whatever it
believes. Under that reading escalate is a constraint on the action space rather
than a candidate inside it, and my result that it is never chosen answers a
question nobody was asking. **The correct claim is narrower than the one my
sweep supports: escalation never wins on cost. It may still be mandatory.**

## 2. Where the numbers come from

**Almost every cost is my own estimate.** Nine components produce fifteen cells,
and eight of the nine components are figures I reasoned my way to rather than
measured. The exception is the probe, which practitioners priced at roughly a
minute a call — and correcting it from my guess of ten minutes to three changed
which actions the agent takes, on about 4% of findings. That one correction is
the strongest available evidence that the other eight are also wrong, in
directions I cannot predict. It is the reason four quantities are swept rather
than reported as points.

**The case generator draws from the agent's own likelihood tables.** Findings
are sampled from the same distributions the agent reasons with, so the agent is
being evaluated in a world that agrees with its assumptions. This flatters every
policy that uses evidence, and the effect is not small: it is the mechanism by
which P2's belief model can only help. A real evaluation needs findings whose
true states were established independently of my model, and I do not have those.
The case file is written once and never regenerated so that at least the
comparison between policies is held fixed.

**Forty cases is few.** One dismissed live key costs 2400 minutes and moves the
sampled total by more than half — it is 56% of P1's entire bill on the sample.
Expected costs are therefore also reported in closed form, which is exact
because there are only fifty-four possible worlds, and the two numbers should be
read together rather than either alone.

**Nothing was executed.** No admin credential was held, no live API call was
made, and the repository contains no credential material — every string in it is
a synthetic feature descriptor. The probe is modelled from OpenAI's documented
response shape, not observed.

## 3. What the scope excludes

**One provider, and it gives the weakest version of the evidence.** OpenAI's
`last_used_at` returns a timestamp. A practitioner described the identical probe
on AWS IAM returning the service, the region and the date for each key. The
same design on a provider with richer telemetry would have a sharper probe and
probably a different answer about when to buy it, so my conclusion that
investigation is rarely worth its price is specific to the provider I chose.

**One finding at a time.** The agent assumes the flagged string is the thing
that matters. A practitioner described rotating a credential cleanly and still
breaking production, because the thing that broke was a *second* key nobody had
written down. Nothing in this design would see that.

**A state I know about and did not model.** Failures that a wrapper reports as
"auth failed" are at least two different things: a rejected credential, and a
credential that authenticated successfully and is authorised for nothing. The
second is a live key that can reach no resource. My cost matrix charges 2400 to
dismiss a live key precisely because what sits behind it is reachable, and for
this state nothing is. Three states is what I could price with the evidence
available; this is the strongest candidate for a fourth.

**Engineer-minutes cannot express three real costs.** Harm falling on customers
rather than the team. Money that is not anyone's time — revoking a certificate
with a public CA costs a few hundred dollars. And the case where no action
helps, raised about GPG master signing keys with no published revocation
certificate. My matrix has no cell for *nothing you do now will work*.

## 4. Where practitioners disagreed with the design

**Three said to just try the key.** The constraint that the agent will never
authenticate with a credential it found is mine, chosen before I knew what it
cost, and it is the direct cause of live-versus-revoked being unresolvable from
free evidence. It is not a constraint the field shares. Everything downstream —
the probe, the invariant ratio, the entire value-of-information analysis —
exists because of a choice a practitioner would not make.

**One said the safe action does not verify itself.** I had argued that rotate
safely reveals the true state as a by-product, since confirming nothing calls
the old key is an observation. A practitioner rotated a credential, saw the
deploy go green and nothing break, and was wrong — the old value was still live
because it had been baked in at image build time rather than read at startup.
Nothing breaking is not evidence the rotation took. That argument is withdrawn.

**One said the problem should not exist.** Infrastructure-as-code declares what
consumes what, and the undocumented-consumer case disappears. This is correct,
and it means the agent is most valuable exactly where practice is worst — which
is a real limit on who it helps. A second practitioner sharpened it: automate
what saves hours, not minutes, and my agent saves minutes per finding. A third
gave the counterweight without being asked — automate what has to be right the
first time, every time — and dismissing a live key is precisely the error that
cannot be taken back.

**One priced the outage differently and reached the opposite action.** My model
rotates safely under uncertainty; they revoke immediately, on the grounds that
service fallout matters less than security fallout. The disagreement is entirely
in the price of an outage, and the sweep covers the range where they are right:
at an outage cost of 60 minutes or less, revoke-now becomes competitive.

## 5. The headline result is the one I trust least

P0 — acting on the prior with no evidence at all — beats the escalate-everything
baseline by 19.3%, and the full belief model reaches only 21.3%. On these
numbers the evidence is worth 1.76 minutes per finding and the cost structure
does everything else.

I believe the direction of that result and not its size. It depends on
rotate-safely costing 120, 30 and 20 across the three states, and those are
three of the eight numbers I invented. A safe action that is cheap in every
state is exactly what makes evidence worthless, so the finding and the shakiest
inputs are the same inputs. If the hedge is more expensive than I think, the
evidence is worth more than I measured.
