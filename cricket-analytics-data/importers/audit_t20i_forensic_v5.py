import csv, json, os, zipfile
from collections import defaultdict

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
P = r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"
MT = os.path.join(P, "match_team_stats.csv")
PM = os.path.join(P, "player_match_performance.csv")
PS = os.path.join(P, "player_statistics.csv")

TARGETS = {
    "1536623": "K Kunwar wicket discrepancy",
    "3a54c25b": "N Magagula career discrepancy",
    "f6ba97c6": "Dilum Fernando career discrepancy",
    "5597338d": "S Ravikumar career discrepancy",
    "26a8b2fe": "Hassan Nawaz career discrepancy",
}

def load(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def si(x):
    try: return int(x)
    except: return 0

def name(v): return str(v or "").strip()

def deliveries(inn):
    for ov in inn.get("overs", []) or []:
        ono = si(ov.get("over"))
        for idx,d in enumerate(ov.get("deliveries",[]) or [],1):
            if isinstance(d,dict):
                yield ono,idx,d

def ex(d):
    return d.get("extras",{}) or {}

def wickets(d):
    return d.get("wickets",[]) or []

def super_over(inn):
    return bool(inn.get("super_over",False))

mt = load(MT)
pm = load(PM)
ps = load(PS)

pm_by_key = {(r["match_id"],r["player_external_id"]):r for r in pm}
ps_by_id = {r["player_external_id"]:r for r in ps if r.get("player_external_id")}

print("="*100)
print("T20I FORENSIC AUDIT V5 - FINAL DIAGNOSTIC")
print("="*100)
print("READ-ONLY")

# ------------------------------------------------------------------
# 1. Find all innings with >120 legal balls and inspect their overs.
# ------------------------------------------------------------------
over120 = []
with zipfile.ZipFile(RAW_ZIP) as z:
    files = [x for x in z.namelist() if x.lower().endswith(".json")]
    for fn in files:
        mid = os.path.splitext(os.path.basename(fn))[0]
        with z.open(fn) as f: data=json.load(f)
        info=data.get("info",{}) or {}
        date=(info.get("dates") or [""])[0] if isinstance(info.get("dates"),list) else info.get("dates","")
        for ino,inn in enumerate(data.get("innings",[]) or [],1):
            if not isinstance(inn,dict) or super_over(inn): continue
            by_over=defaultdict(lambda: {"legal":0,"deliveries":0,"illegal":[]})
            for ono,bno,d in deliveries(inn):
                e=ex(d)
                legal=("wides" not in e and "noballs" not in e)
                by_over[ono]["deliveries"]+=1
                by_over[ono]["legal"]+=legal
                if not legal:
                    by_over[ono]["illegal"].append((bno,e))
            total=sum(x["legal"] for x in by_over.values())
            if total>120:
                over120.append((mid,date,inn.get("team"),ino,total,by_over))

print("\n[1] >120 LEGAL-BALL INNINGS")
print("Count:",len(over120))
mt_by_key={(r["match_id"],name(r["team_name"])):r for r in mt}
for mid,date,team,ino,total,by_over in over120:
    print(f"\n{mid} | {date} | {team} | innings={ino} | legal={total}")
    for o in sorted(by_over):
        x=by_over[o]
        if x["legal"] != 6 or x["deliveries"] != 6:
            print(f"  over {o}: deliveries={x['deliveries']} legal={x['legal']} illegal={x['illegal']}")
    r=mt_by_key.get((mid,name(team)))
    if r:
        print("  processed total_balls=",si(r["total_balls"]),
              "allocated_balls=",si(r["allocated_balls"]))
    else:
        print("  processed match-team row MISSING")

# ------------------------------------------------------------------
# 2. Exact wicket forensic for 1536623.
# ------------------------------------------------------------------
print("\n"+"="*100)
print("[2] EXACT WICKET FORENSIC: 1536623 / K KUNWAR")
print("="*100)

with zipfile.ZipFile(RAW_ZIP) as z:
    fn=next((x for x in z.namelist()
             if os.path.splitext(os.path.basename(x))[0]=="1536623"),None)
    with z.open(fn) as f: data=json.load(f)

reg=((data.get("info",{}) or {}).get("registry",{}) or {}).get("people",{}) or {}
name_to_id={name(n):name(pid) for n,pid in reg.items() if p}

for ino,inn in enumerate(data.get("innings",[]) or [],1):
    if super_over(inn): continue
    print(f"\nInnings {ino}: {inn.get('team')}")
    for o,b,d in deliveries(inn):
        for w in wickets(d):
            bow=name(d.get("bowler")); eid=name_to_id.get(bow,"")
            kind=name(w.get("kind")).lower()
            po=name(w.get("player_out"))
            print(f"  {o}.{b}: bowler={bow} [{eid}] out={po} kind={kind}")
            if eid=="97e6e41a":
                print("      PROCESSED:", pm_by_key.get(("1536623",eid),{}).get("wickets"))

# ------------------------------------------------------------------
# 3. Career reconciliation must first be tested against processed PM.
# ------------------------------------------------------------------
print("\n"+"="*100)
print("[3] PROCESSED PLAYER-MATCH -> PROCESSED CAREER")
print("="*100)

pm_agg=defaultdict(lambda: {
    "matches":set(),"runs":0,"balls_faced":0,"fours":0,"sixes":0,
    "balls_bowled":0,"runs_conceded":0,"wickets":0
})
for r in pm:
    eid=name(r.get("player_external_id"))
    if not eid: continue
    a=pm_agg[eid]
    a["matches"].add(r["match_id"])
    a["runs"]+=si(r["batting_runs"])
    a["balls_faced"]+=si(r["balls_faced"])
    a["fours"]+=si(r["fours"])
    a["sixes"]+=si(r["sixes"])
    a["balls_bowled"]+=si(r["balls_bowled"])
    a["runs_conceded"]+=si(r["runs_conceded"])
    a["wickets"]+=si(r["wickets"])

fields=[
    ("matches",lambda a:len(a["matches"])),
    ("runs",lambda a:a["runs"]),
    ("balls_faced",lambda a:a["balls_faced"]),
    ("fours",lambda a:a["fours"]),
    ("sixes",lambda a:a["sixes"]),
    ("balls_bowled",lambda a:a["balls_bowled"]),
    ("runs_conceded",lambda a:a["runs_conceded"]),
    ("wickets",lambda a:a["wickets"]),
]
m=[]
for eid,a in pm_agg.items():
    r=ps_by_id.get(eid)
    if not r:
        m.append((eid,"CAREER_ROW_MISSING",None,None))
        continue
    for f,get in fields:
        exp=get(a); act=si(r[f])
        if exp!=act:
            m.append((eid,f,exp,act,r.get("player_name")))

print("Processed career rows:",len(ps_by_id))
print("PM-derived career IDs:",len(pm_agg))
print("PM -> career mismatches:",len(m))
for x in m[:100]:
    print(x)

# ------------------------------------------------------------------
# 4. Detailed target careers.
# ------------------------------------------------------------------
print("\n"+"="*100)
print("[4] TARGET CAREER DETAILS")
print("="*100)

target_eids=set()
for r in ps:
    if r.get("player_name") in {"N Magagula","Dilum Fernando","S Ravikumar","Hassan Nawaz","K Kunwar"}:
        target_eids.add(r["player_external_id"])
for eid in target_eids:
    print("\n",eid, ps_by_id[eid].get("player_name"))
    print("  career:", {k:ps_by_id[eid].get(k) for k in
          ["matches","runs","balls_faced","fours","sixes","balls_bowled","runs_conceded","wickets"]})
    print("  PM rows:")
    for r in pm:
        if r["player_external_id"]==eid:
            print("   ", {k:r.get(k) for k in
                  ["match_id","player_name","batting_runs","balls_faced","fours","sixes","balls_bowled","runs_conceded","wickets"]})

print("\n"+"="*100)
print("V5 DIAGNOSTIC COMPLETE")
print("="*100)
print("No files or database records were modified.")
print("Decision is intentionally NOT made here; use the exact evidence above before changing the processor.")
