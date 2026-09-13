import csv,json,os,zipfile
from collections import defaultdict,Counter

BASE=r"D:\CricketAnalytics\cricket-analytics-data"
ZIP=os.path.join(BASE,"raw","international","t20s_json.zip")
PM=os.path.join(BASE,"processed","t20i","player_match_performance.csv")
BOWLER_NOT_CREDITED={"run out","retired hurt","retired not out","retired out","obstructing the field","timed out"}

def si(v):
    try: return int(float(v or 0))
    except: return 0
def norm(v): return " ".join(str(v or "").strip().lower().split())
def ex(d): return d.get("extras",{}) if isinstance(d.get("extras",{}),dict) else {}
def legal(d):
    e=ex(d); return "wides" not in e and "noballs" not in e

with open(PM,encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
processed={(str(r["match_id"]),str(r["player_external_id"])) for r in rows}

raw=defaultdict(lambda:dict(name="",gender="",bat=0,bowl=0,wk=0,runs=0,bf=0,fours=0,sixes=0,bb=0,rc=0,wickets=0,maidens=0,kinds=Counter()))
with zipfile.ZipFile(ZIP) as z:
    files=[x for x in z.namelist() if x.lower().endswith(".json")]
    for fn in files:
        mid=os.path.splitext(os.path.basename(fn))[0]
        with z.open(fn) as f: data=json.load(f)
        info=data.get("info",{}); gender=str(info.get("gender","")).lower()
        people=info.get("registry",{}).get("people",{}) or {}
        teams=info.get("teams",[]) or []
        for inn in data.get("innings",[]) or []:
            if not isinstance(inn,dict) or inn.get("super_over",False): continue
            batting=str(inn.get("team","")).strip()
            bowling=next((t for t in teams if t!=batting),"")
            for ov in inn.get("overs",[]) or []:
                if not isinstance(ov,dict): continue
                orun=0; olegal=0; obowl=set()
                for d in ov.get("deliveries",[]) or []:
                    if not isinstance(d,dict): continue
                    r=d.get("runs",{}) if isinstance(d.get("runs",{}),dict) else {}
                    br=si(r.get("batter")); tr=si(r.get("total")); e=ex(d); lg=legal(d)
                    orun+=tr
                    b=d.get("batter")
                    if b and people.get(b):
                        k=(mid,str(people[b])); q=raw[k]; q["name"]=b;q["gender"]=gender;q["bat"]+=1;q["runs"]+=br
                        if lg:q["bf"]+=1
                        if br==4:q["fours"]+=1
                        if br==6:q["sixes"]+=1
                    bow=d.get("bowler")
                    if bow and people.get(bow):
                        k=(mid,str(people[bow]));q=raw[k];q["name"]=bow;q["gender"]=gender;q["bowl"]+=1
                        if lg:q["bb"]+=1
                        q["rc"]+=br+si(e.get("wides"))+si(e.get("noballs"))
                        obowl.add(str(people[bow]))
                    for w in d.get("wickets",[]) or []:
                        if not isinstance(w,dict):continue
                        kind=norm(w.get("kind")); out=w.get("player_out")
                        if out and people.get(out):
                            k=(mid,str(people[out]));q=raw[k];q["name"]=out;q["gender"]=gender;q["wk"]+=1;q["kinds"][kind]+=1
                        if bow and people.get(bow) and kind not in BOWLER_NOT_CREDITED:
                            raw[(mid,str(people[bow]))]["wickets"]+=1
                    if lg:olegal+=1
                if orun==0 and olegal>=6 and len(obowl)==1:
                    k=(mid,next(iter(obowl)))
                    if k in raw:raw[k]["maidens"]+=1

missing=set(raw)-processed
print("="*100);print("T20I FORENSIC AUDIT V7");print("="*100)
print("Raw keys:",len(raw));print("Processed keys:",len(processed));print("Missing:",len(missing));print("Extra:",len(processed-set(raw)))
cats=Counter(); genuine=[]; zero=[]
for k in missing:
    q=raw[k]
    if q["bat"] and q["bowl"]:cat="BATTER_AND_BOWLER"
    elif q["bat"]:cat="BATTER_ONLY"
    elif q["bowl"]:cat="BOWLER_ONLY"
    elif q["wk"]:cat="WICKET_ONLY"
    else:cat="OTHER"
    cats[cat]+=1
    nonzero=any(q[x] for x in ("runs","bf","fours","sixes","bb","rc","wickets","maidens"))
    (genuine if nonzero else zero).append((k,q,cat))
print("\nCLASSIFICATION")
for c,n in cats.most_common():print(f"{c:<25}{n}")
print("Non-zero missing events:",len(genuine));print("Zero-stat missing events:",len(zero))
print("\nDETAILED MISSING EVENTS")
for k,q,cat in sorted([(k,raw[k],None) for k in missing]):
    q=raw[k]
    if q["bat"] and q["bowl"]:cat="BATTER_AND_BOWLER"
    elif q["bat"]:cat="BATTER_ONLY"
    elif q["bowl"]:cat="BOWLER_ONLY"
    elif q["wk"]:cat="WICKET_ONLY"
    else:cat="OTHER"
    print(f"{k[0]:<9} {k[1]:<10} {q['name']:<28} {cat:<20} bat={q['bat']:<2} bowl={q['bowl']:<2} wk={q['wk']:<2} runs={q['runs']:<3} bf={q['bf']:<3} bb={q['bb']:<3} rc={q['rc']:<3} w={q['wickets']:<2}")
print("\nWICKET-ONLY KINDS")
wk=[(k,raw[k]) for k in missing if raw[k]["wk"] and not raw[k]["bat"] and not raw[k]["bowl"]]
kc=Counter()
for k,q in wk:kc.update(q["kinds"])
for x,n in kc.most_common():print(f"{x:<30}{n}")
print("\nRESULT")
if genuine: print("FAIL: missing event(s) carry statistical values.")
else: print("PASS: all missing events are zero-stat metadata/wicket-only events; no statistical row loss detected.")
print("READ-ONLY: no CSV or database changes.")
