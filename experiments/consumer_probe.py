S=["live","revoked","fake"]
def costs(F):
    # F = minutes to find the consumers. Appears in rotate, revoke and escalate.
    rot = {"live":10+F+60+10+2, "revoked":30, "fake":20}
    rev = {"live":2+240+F+60,   "revoked":2,  "fake":5}
    return {"dismiss":{"live":2400,"revoked":2,"fake":2},
            "escalate":{"live":30+rot["live"],"revoked":30,"fake":30},
            "revoke":rev, "rotate":rot}

def boundaries(F):
    C=costs(F)
    # live/revoked ratio is locked at 1.778 by the free features, so sweep P(live)
    # with revoked = live/1.778 and fake taking the rest.
    prev=None; out=[]
    for i in range(200001):
        pl=i/200000
        pr=pl/1.7777777778
        pf=1-pl-pr
        if pf<0: break
        b={"live":pl,"revoked":pr,"fake":pf}
        best=min(C,key=lambda a: sum(b[s]*C[a][s] for s in S))
        if best!=prev:
            out.append((pl,best)); prev=best
    return out

print(f"{'find-consumers':>15s}   regime boundaries along the reachable line")
for F in [30,60,120,240,480]:
    segs=boundaries(F)
    txt="  ".join(f"{a} from P(live)={p:.5f}" for p,a in segs)
    print(f"{F:>15d}   {txt}")

print("\nwhy: F appears identically in rotate and revoke on the live column")
for F in [30,480]:
    C=costs(F)
    print(f"  F={F:3d}   rotate(live)={C['rotate']['live']:4d}  "
          f"revoke(live)={C['revoke']['live']:4d}  difference={C['revoke']['live']-C['rotate']['live']}")
