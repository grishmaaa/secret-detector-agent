"""
Joint sensitivity.

Two questions, not one:

  A. If every COST estimate is wrong at once, which conclusions survive?
  B. If the EVIDENCE model is also wrong, do they still?

Sampling. Each quantity is given a low / most-likely / high triple. Draws come
from a two-piece lognormal in which the most-likely value is the median and the
low and high are the 5th and 95th percentiles exactly. An earlier version used a
single sigma derived from log(high/low), which silently made the stated range
wrong whenever the estimate was not the geometric midpoint of low and high — for
'human' it sampled 8.7-103.9 while claiming 5-60, biasing the escalation result.

Independence. Components are drawn independently, which is an assumption and
almost certainly false: a deployment that is hard to run is probably also hard
to verify. These are 40,000 draws from a chosen uncertainty model, not 40,000
plausible organisations.

Reading the percentages. "99.07%" means 99.07% of sampled draws had that
property. It is not a confidence level and not a probability that the claim is
true.
"""
import math, os, random, json

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "..", "results")
SEED, N = 20260828, 40000
S = ["live", "revoked", "fake"]
Z90 = 1.6448536269514722

#  component            low    est    high
RANGES = {
 "revoke":            (   1,     2,     5),
 "issue":             (   1,    10,    25),
 "probe":             ( 0.5,     3,    10),
 "human":             (   5,    30,    60),
 "find":              (  10,    30,   120),
 "deploy":            (  10,    60,   180),
 "verify":            (   2,    10,    30),
 "outage":            (  30,   240,   480),
 "dismiss_live":      ( 240,  2400, 24000),
 "rotate_revoked":    (   5,    30,    90),
 "rotate_fake":       (   1,    20,    60),
 "revoke_fake":       (   1,     5,    20),
 "dismiss_inert":     (   1,     2,     5),
}
LIVE_SHARE = (0.40, 0.64, 0.85)
FAKE_SHARE = (0.10, 0.25, 0.45)
ALPHA = 40          # Dirichlet concentration for likelihood rows; higher = tighter

def two_piece(rng, low, est, high):
    """median = est, 5th pct = low, 95th pct = high, exactly."""
    z = rng.gauss(0, 1)
    sigma = math.log(est/low)/Z90 if z < 0 else math.log(high/est)/Z90
    return est*math.exp(z*sigma)

def dirichlet(rng, p, alpha):
    g = [rng.gammavariate(alpha*x, 1.0) if x > 0 else 0.0 for x in p]
    t = sum(g)
    return [x/t for x in g] if t > 0 else list(p)

PLACE0 = {"live":[.10,.30,.60],"revoked":[.10,.30,.60],"fake":[.70,.25,.05]}
WELL0  = {"live":[.99,.01],"revoked":[.99,.01],"fake":[.40,.60]}
PROBE0 = {"live":[.60,.20,.20],"revoked":[.02,.78,.20],"fake":[.01,.04,.95]}
BUCKETS = [(i,j,f"{p}/{w}") for i,p in enumerate(["placeholder","neutral","production"])
                            for j,w in enumerate(["well-formed","malformed"])]

def build(k):
    rot = {"live": k["issue"]+k["find"]+k["deploy"]+k["verify"]+k["revoke"],
           "revoked": k["rotate_revoked"], "fake": k["rotate_fake"]}
    rev = {"live": k["revoke"]+k["outage"]+k["find"]+k["deploy"],
           "revoked": k["revoke"], "fake": k["revoke_fake"]}
    dis = {"live": k["dismiss_live"], "revoked": k["dismiss_inert"], "fake": k["dismiss_inert"]}
    esc = {s: k["human"] + min(rot[s], rev[s], dis[s]) for s in S}
    return {"dismiss":dis, "escalate":esc, "revoke":rev, "rotate":rot}

def run(rng, perturb_evidence):
    k = {n: two_piece(rng, *r) for n, r in RANGES.items()}
    C = build(k)
    live = min(max(two_piece(rng, *LIVE_SHARE), 0.05), 0.95)
    pf   = min(max(two_piece(rng, *FAKE_SHARE), 0.02), 0.70) if perturb_evidence else 0.25
    PRIOR = {"live": (1-pf)*live, "revoked": (1-pf)*(1-live), "fake": pf}

    if perturb_evidence:
        PL = {s: dirichlet(rng, PLACE0[s], ALPHA) for s in S}
        WE = {s: dirichlet(rng, WELL0[s],  ALPHA) for s in S}
        PR = {s: dirichlet(rng, PROBE0[s], ALPHA) for s in S}
    else:
        PL, WE, PR = PLACE0, WELL0, PROBE0

    def ec(b,a): return sum(b[s]*C[a][s] for s in S)
    def best(b): return min(C, key=lambda a: ec(b,a))

    beliefs, probs = [], []
    for i,j,_ in BUCKETS:
        u = {s: PRIOR[s]*PL[s][i]*WE[s][j] for s in S}
        t = sum(u.values()); probs.append(t)
        beliefs.append({s: v/t for s,v in u.items()})

    # how much does the live:revoked ratio actually move across buckets?
    r0 = PRIOR["live"]/PRIOR["revoked"]
    drift = max(abs(math.log((b["live"]/b["revoked"])/r0)) for b in beliefs)

    acts = [best(b) for b in beliefs]
    p0   = best(PRIOR)
    base = sum(p*ec(b,"escalate") for p,b in zip(probs,beliefs))
    c_p0 = sum(p*ec(b,p0)         for p,b in zip(probs,beliefs))
    c_p2 = sum(p*ec(b,a)          for p,b,a in zip(probs,beliefs,acts))

    evsis = []
    for b in beliefs:
        now = ec(b,best(b)); after = 0.0
        for o in range(3):
            po = sum(b[s]*PR[s][o] for s in S)
            if po <= 0: continue
            u = {s: b[s]*PR[s][o] for s in S}; t = sum(u.values())
            post = {s: v/t for s,v in u.items()}
            after += po*ec(post,best(post))
        evsis.append(now-after)
    probe_share = sum(p for p,v in zip(probs,evsis) if v > k["probe"])
    vpi = max(ec(b,best(b)) - sum(b[s]*min(C[a][s] for a in C) for s in S) for b in beliefs)

    kk = 1 + 1/r0
    def line(a): return (C[a]["live"] + C[a]["revoked"]/r0 - kk*C[a]["fake"], C[a]["fake"])
    (mr,br),(mv,bv) = line("rotate"), line("revoke")
    bound = (bv-br)/(mr-mv) if abs(mr-mv) > 1e-12 else float("nan")

    return dict(base=base, p0=c_p0, p2=c_p2, p0act=p0, acts=acts,
                probe_share=probe_share, vpi=vpi, bound=bound, drift=drift,
                gain0=1-c_p0/base, gain2=1-c_p2/base, belief_worth=c_p0-c_p2,
                human=k["human"])

def analyse(R, label):
    def pct(f): return 100*sum(1 for r in R if f(r))/len(R)
    def ci(v, lo=5, hi=95):
        v = sorted(v); n = len(v)
        return v[int(n*lo/100)], v[n//2], v[min(n-1,int(n*hi/100))]
    print(f"\n{'='*74}\n{label}\n{'='*74}\n")
    claims = [
        ("P2 costs less than escalate-everything",   lambda r: r["p2"] < r["base"]),
        ("revoke/rotate boundary below 0.5",         lambda r: r["bound"] < 0.5),
        ("belief model worth under 5 min/finding",   lambda r: r["belief_worth"] < 5),
        ("P0 also costs less than the baseline",     lambda r: r["p0"] < r["base"]),
        ("escalate is chosen nowhere",               lambda r: "escalate" not in r["acts"]),
        ("the probe is bought somewhere",            lambda r: r["probe_share"] > 0),
        ("P0 chooses rotate-safely",                 lambda r: r["p0act"] == "rotate"),
    ]
    for n,f in claims:
        print(f"  {n:44s} {pct(f):6.2f}% of draws")
    print()
    for n,f,fm in [("P2 saving vs baseline (%)", lambda r:100*r["gain2"], "8.2f"),
                   ("value of belief model (min)", lambda r:r["belief_worth"], "8.2f"),
                   ("revoke/rotate boundary", lambda r:r["bound"], "8.4f"),
                   ("max VPI, reachable beliefs", lambda r:r["vpi"], "8.2f"),
                   ("findings probed (%)", lambda r:100*r["probe_share"], "8.2f"),
                   ("live:revoked log-drift across buckets", lambda r:r["drift"], "8.4f")]:
        lo,md,hi = ci([f(r) for r in R])
        print(f"  {n:40s}{lo:{fm}}{md:{fm}}{hi:{fm}}   (5th, median, 95th)")
    return {n: round(pct(f),2) for n,f in claims}

rng = random.Random(SEED)
A = [run(rng, False) for _ in range(N)]
rng = random.Random(SEED+1)
B = [run(rng, True)  for _ in range(N)]

print(f"{N:,} draws each, seed {SEED}")
ca = analyse(A, "A. COSTS UNCERTAIN, evidence model held fixed")
cb = analyse(B, f"B. COSTS AND EVIDENCE BOTH UNCERTAIN (Dirichlet alpha={ALPHA})")

print(f"\n{'='*74}\nWHAT ADDING EVIDENCE UNCERTAINTY COSTS EACH CLAIM\n{'='*74}\n")
for n in ca:
    d = cb[n]-ca[n]
    print(f"  {n:44s}{ca[n]:7.2f}% -> {cb[n]:6.2f}%  ({d:+.2f})")

print(f"\n{'='*74}\nCONTROLLED: everything at its point estimate, only the human varies\n{'='*74}\n")
pt = {n: e for n,(l,e,h) in RANGES.items()}
PRIOR0 = {"live":0.48,"revoked":0.27,"fake":0.25}
bel = []
for i,j,name in BUCKETS:
    u = {s: PRIOR0[s]*PLACE0[s][i]*WELL0[s][j] for s in S}
    t = sum(u.values()); bel.append((name, t, {s:v/t for s,v in u.items()}))
print(f"  {'human cost':>11s}   chosen action in each bucket")
prev=None
for h in [1,2,3,5,8,10,12,15,20,25,30,45,60]:
    pt["human"]=h; C=build(pt)
    acts=[min(C,key=lambda a: sum(b[s]*C[a][s] for s in S)) for _,_,b in bel]
    esc=sum(p for (_,p,_),a in zip(bel,acts) if a=="escalate")
    mark = "  <-- escalation appears" if ("escalate" in acts and prev=="no") else ""
    prev = "yes" if "escalate" in acts else "no"
    print(f"  {h:9d} min   {', '.join(sorted(set(acts))):28s} escalated on {esc*100:5.2f}%{mark}")

os.makedirs(RESULTS, exist_ok=True)
json.dump({"n_samples":N,"seed":SEED,"alpha":ALPHA,
           "ranges":{k:{"low":v[0],"most_likely":v[1],"high":v[2]} for k,v in RANGES.items()},
           "costs_only_pct":ca,"costs_and_evidence_pct":cb},
          open(os.path.join(RESULTS,"robustness.json"),"w"), indent=2)
print(f"\nWrote results/robustness.json")
