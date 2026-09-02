# Failure analysis, feedback, and drift

## Part 1: five failures of the fixed agent

145 of 500 decisions were not the hindsight-best
action. The five most expensive are examined below. This is the P6
agent -- corrected breach cost, escalation rules, scope on the probe --
so these are the mistakes that survive every fix so far.

### Failure 1 — 132 minutes lost

**Category: Wrong action policy.** Belief and evidence were both reasonable; the mapping from belief to action is what produced the loss.

| Question | Answer |
|---|---|
| What did the agent believe? | zero_scope 0.817, live 0.076, revoked 0.046 |
| What was actually true? | **live** |
| Which evidence did it use? | context `neutral`, form `well-formed`, probe `null` + scope |
| Which evidence did it never obtain? | nothing further was available |
| Was the probability wrong? | P(truth) was 0.0756; no, the belief was reasonable |
| Was the hidden-state list incomplete? | no, the true state was in the model |
| Was the threshold wrong? | the agent chose `dismiss`; `rotate` was correct |
| Was the cost model wrong? | the costs are not what produced this one |
| Should it have asked for more information? | it did buy the probe |
| Should a human have been involved? | no — nothing about this case is unusual to the model |

### Failure 2 — 30 minutes lost

**Category: Wrong action policy.** Belief and evidence were both reasonable; the mapping from belief to action is what produced the loss.

| Question | Answer |
|---|---|
| What did the agent believe? | zero_scope 0.624, fake 0.221, other 0.062 |
| What was actually true? | **zero_scope** |
| Which evidence did it use? | context `placeholder`, form `well-formed`, probe `null` + scope |
| Which evidence did it never obtain? | nothing further was available |
| Was the probability wrong? | P(truth) was 0.6240; no, the belief was reasonable |
| Was the hidden-state list incomplete? | no, the true state was in the model |
| Was the threshold wrong? | the agent chose `escalate`; `dismiss` was correct |
| Was the cost model wrong? | the costs are not what produced this one |
| Should it have asked for more information? | it did buy the probe |
| Should a human have been involved? | no — nothing about this case is unusual to the model |

### Failure 3 — 30 minutes lost

**Category: Wrong action policy.** Belief and evidence were both reasonable; the mapping from belief to action is what produced the loss.

| Question | Answer |
|---|---|
| What did the agent believe? | live 0.571, zero_scope 0.205, other 0.204 |
| What was actually true? | **live** |
| Which evidence did it use? | context `placeholder`, form `well-formed`, probe `recent` + scope |
| Which evidence did it never obtain? | nothing further was available |
| Was the probability wrong? | P(truth) was 0.5709; no, the belief was reasonable |
| Was the hidden-state list incomplete? | no, the true state was in the model |
| Was the threshold wrong? | the agent chose `escalate`; `rotate` was correct |
| Was the cost model wrong? | the costs are not what produced this one |
| Should it have asked for more information? | it did buy the probe |
| Should a human have been involved? | no — nothing about this case is unusual to the model |

### Failure 4 — 30 minutes lost

**Category: Missing hidden state.** The truth was the residual. No likelihood in the model describes it, so no evidence could have identified it.

| Question | Answer |
|---|---|
| What did the agent believe? | zero_scope 0.677, revoked 0.167, other 0.075 |
| What was actually true? | **other** |
| Which evidence did it use? | context `placeholder`, form `well-formed`, probe `old` + scope |
| Which evidence did it never obtain? | nothing further was available |
| Was the probability wrong? | P(truth) was 0.0748; no, the belief was reasonable |
| Was the hidden-state list incomplete? | **yes** — the truth was the residual state |
| Was the threshold wrong? | the agent chose `escalate`; `rotate` was correct |
| Was the cost model wrong? | the costs are not what produced this one |
| Should it have asked for more information? | it did buy the probe |
| Should a human have been involved? | **yes** — this is exactly what the residual-state escalation trigger is for |

### Failure 5 — 30 minutes lost

**Category: Missing hidden state.** The truth was the residual. No likelihood in the model describes it, so no evidence could have identified it.

| Question | Answer |
|---|---|
| What did the agent believe? | revoked 0.492, live 0.258, other 0.187 |
| What was actually true? | **other** |
| Which evidence did it use? | context `neutral`, form `malformed`, probe `old` + scope |
| Which evidence did it never obtain? | nothing further was available |
| Was the probability wrong? | P(truth) was 0.1868; no, the belief was reasonable |
| Was the hidden-state list incomplete? | **yes** — the truth was the residual state |
| Was the threshold wrong? | the agent chose `escalate`; `rotate` was correct |
| Was the cost model wrong? | the costs are not what produced this one |
| Should it have asked for more information? | it did buy the probe |
| Should a human have been involved? | **yes** — this is exactly what the residual-state escalation trigger is for |

### All failures by category

| Category | Count | Share of failures |
|---|---|---|
| Wrong cost assumption | 111 | 76.6% |
| Wrong action policy | 24 | 16.6% |
| Missing hidden state | 6 | 4.1% |
| Misleading evidence | 3 | 2.1% |
| Insufficient information | 1 | 0.7% |

The distribution is the finding, not any single case. One category
dominating means the agent has one systematic weakness rather than
scattered bad luck, and a systematic weakness is fixable.

## Part 2: what the agent learns, and why it is wrong

The agent now acts, sometimes finds out it was wrong, and updates its
prior. The problem is not the updating. It is what reaches the agent.

| Situation | How often anyone finds out |
|---|---|
| Remediated something that did not need it | 80% |
| Dismissed a key that was live | 5% |
| Decided correctly | 30% |

A wasted rotation breaks somebody's deploy and generates a ticket the
same afternoon. A live key left in place does nothing at all today,
and if it does something in four months nobody connects it back to
this finding. **The agent hears about its false positives and almost
never about its false negatives.**

Over 4,000 findings, 50.5% of outcomes were
discovered and fed back. Here is what the agent came to believe:

| State | True world | What the agent learned | Error |
|---|---|---|---|
| live | 0.4356 | 0.2691 | -0.1665 |
| revoked | 0.2673 | 0.4184 | +0.1511 |
| fake | 0.2475 | 0.2463 | -0.0012 |
| zero_scope | 0.0396 | 0.0622 | +0.0226 |
| other | 0.0100 | 0.0041 | -0.0059 |

The largest distortion is **live**, off by -0.1665.

The direction is what matters. The states the agent remediates
unnecessarily are the ones it keeps being told about, so their counts
rise; the state it under-reacts to is the one nobody reports, so its
count lags. An agent learning from this feedback becomes progressively
more confident that findings are harmless, in a world where they are
not. **The feedback loop corrects the over-remediation bias and keeps
going, into the error that costs 2400 minutes instead of 30.**

Cost with learning: 60.47 min/finding. Frozen prior: 61.04.

The practical conclusion is not *do not learn*. It is that an agent
must weight feedback by how likely it was to hear about the outcome at
all, and this one does not. That is the clearest single improvement
left in the design, and it is not implemented here.

## Part 3: noticing that the world has moved

The prior was set from how the world used to be. Nothing breaks loudly
when that stops being true -- the agent keeps producing confident
answers from beliefs that no longer describe anything.

The alarm compares the evidence distribution the agent *expects* with
the one it *observes* over a rolling window of 250 findings, using
Jensen-Shannon divergence. KL divergence is the natural first choice
and is unusable here: it is asymmetric, so the answer depends on which
distribution you name first, and it returns infinity the first time a
genuinely new kind of evidence appears -- which is precisely the
moment you need a number rather than an overflow. JSD is symmetric,
bounded by 1 bit, and finite always.

At finding 1,500 the world shifts: `fake` becomes 1.7x more common. Nothing tells
the agent.

| Window ending at | JSD (bits) |
|---|---|
| 250 | 0.00333 |
| 450 | 0.00233 |
| 650 | 0.00260 |
| 850 | 0.00897 |
| 1050 | 0.00148 |
| 1250 | 0.00616 |
| 1450 | 0.00995 |
| 1650 | 0.00705 |
| 1850 | 0.02057 |
| 2050 | 0.01806 |
| 2250 | 0.02485 |
| 2450 | 0.01589 |
| 2650 | 0.01575 |
| 2850 | 0.00944 |

Before the shift, JSD sits between 0.00078 and 0.01303. After it, the mean is 0.01666 and individual windows run from 0.00916 to 0.02779.

Eyeballing one run is not an answer, and the single run above is
ambiguous: the ranges overlap. So the alarm is calibrated properly
instead. The threshold is the highest divergence seen across eight
**control runs in which nothing changes**, and detection and
false-alarm rates are then measured on separate held-out runs against
that fixed threshold. A threshold read off the same run you evaluate
is guaranteed to look good and means nothing.

| Window | Shift in `fake` | Threshold (bits) | Detection | False alarms |
|---|---|---|---|---|
| 250 | x2.2 | 0.01767 | **52%** | 0.2% |
| 250 | x4.0 | 0.01767 | **100%** | 0.2% |
| 250 | x8.0 | 0.01767 | **100%** | 0.2% |
| 500 | x2.2 | 0.00736 | **100%** | 0.0% |
| 500 | x4.0 | 0.00736 | **100%** | 0.0% |
| 500 | x8.0 | 0.00736 | **100%** | 0.0% |
| 1000 | x2.2 | 0.00374 | **100%** | 0.0% |
| 1000 | x4.0 | 0.00374 | **100%** | 0.0% |
| 1000 | x8.0 | 0.00374 | **100%** | 0.0% |

Two things in that table are worth reading carefully.

**The single run was misleading and the sweep corrected it.** Judging
by eye off one seed suggested the alarm did not separate signal from
noise. With a threshold calibrated on held-out control runs it
separates them cleanly. The difference is not a better alarm; it is a
better experiment. One run of a stochastic process is an anecdote.

**The threshold falls faster than the window grows.** Doubling the
window from 250 to 500 findings drops the noise floor from 0.01767 to
0.00736 bits, better than half, because the divergence of an empirical
distribution from its source shrinks with sample size while a real
shift does not shrink at all. That is the whole mechanism: wait longer,
and the noise goes away while the signal stays.

The cost is latency, and it is the only real trade here. On a queue of
a few hundred findings a week, a 500-case window means the agent runs
on stale beliefs for something like a fortnight before the alarm
clears the floor. It is a smoke detector, not a tripwire, and a paper
that reports the detection rate without reporting the delay has
answered half the question.

One limitation I cannot sweep away. This alarm watches the free
features, which carry zero bits about live-versus-revoked. It will
therefore notice a shift in how many findings are fake and stay
completely silent on a shift in how many are still live -- which is
the shift that would actually cost something. Watching the probe
channel instead would fix that, and the probe is bought on a minority
of findings, so the effective window would be several times longer
again. Detect the drift that matters and wait months, or detect the
drift that does not and wait weeks. That is not answered here.

