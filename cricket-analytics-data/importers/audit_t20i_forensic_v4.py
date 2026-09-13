import csv
import json
import os
import zipfile
from collections import defaultdict

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
PROCESSED_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"

MATCHES_CSV = os.path.join(PROCESSED_DIR, "matches.csv")
MATCH_TEAM_CSV = os.path.join(PROCESSED_DIR, "match_team_stats.csv")
PLAYER_MATCH_CSV = os.path.join(PROCESSED_DIR, "player_match_performance.csv")
PLAYER_STATS_CSV = os.path.join(PROCESSED_DIR, "player_statistics.csv")

TARGET_WICKET_MATCH = "1536623"

def si(v, d=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return d

def norm(v):
    return str(v or "").strip()

def load(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def ex(d):
    x = d.get("extras", {})
    return x if isinstance(x, dict) else {}

def ws(d):
    x = d.get("wickets", [])
    return x if isinstance(x, list) else []

def ds(inn):
    for ov in inn.get("overs", []) or []:
        if not isinstance(ov, dict):
            continue
        over_no = si(ov.get("over"))
        for ball_no, d in enumerate(ov.get("deliveries", []) or [], start=1):
            if isinstance(d, dict):
                yield over_no, ball_no, d

def is_super(inn):
    return bool(inn.get("super_over", False))

section_count = 0
def section(title):
    global section_count
    section_count += 1
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

section("T20I FORENSIC AUDIT V4")
print("READ-ONLY: no CSV, ZIP, or database data will be modified.")

for p in [RAW_ZIP, MATCHES_CSV, MATCH_TEAM_CSV, PLAYER_MATCH_CSV, PLAYER_STATS_CSV]:
    if not os.path.exists(p):
        print("[FAIL] Missing:", p)
        raise SystemExit(1)
    print("[PASS] Exists:", p)

matches = load(MATCHES_CSV)
mts = load(MATCH_TEAM_CSV)
pm = load(PLAYER_MATCH_CSV)
career = load(PLAYER_STATS_CSV)

pm_by_key = {(r["match_id"], r["player_external_id"]): r for r in pm}
career_by_id = {r["player_external_id"]: r for r in career if r.get("player_external_id")}

# ---------------------------------------------------------------------------
# FORENSIC SCAN
# ---------------------------------------------------------------------------
section("FORENSIC RAW SCAN")

over120 = []
target_raw_pm = defaultdict(lambda: {
    "name": "",
    "runs": 0,
    "balls": 0,
    "fours": 0,
    "sixes": 0,
    "balls_bowled": 0,
    "runs_conceded": 0,
    "wickets": 0,
})
raw_career = defaultdict(lambda: {
    "matches": set(),
    "runs": 0,
    "balls": 0,
    "fours": 0,
    "sixes": 0,
    "balls_bowled": 0,
    "runs_conceded": 0,
    "wickets": 0,
})

target_match_data = None
all_regulation_event_keys = set()

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    json_files = [n for n in z.namelist() if n.lower().endswith(".json")]

    for fn in json_files:
        mid = os.path.splitext(os.path.basename(fn))[0]
        with z.open(fn) as f:
            data = json.load(f)

        info = data.get("info", {}) or {}
        registry = ((info.get("registry") or {}).get("people") or {})
        name_to_id = {norm(n): norm(pid) for n, pid in registry.items() if pid}

        if mid == TARGET_WICKET_MATCH:
            target_match_data = data

        for inn_no, inn in enumerate(data.get("innings", []) or [], start=1):
            if not isinstance(inn, dict) or is_super(inn):
                continue

            team = norm(inn.get("team"))
            deliveries_list = list(ds(inn))
            legal = 0
            dismissed = set()

            for over_no, ball_no, d in deliveries_list:
                e = ex(d)
                legal_ball = "wides" not in e and "noballs" not in e
                legal += legal_ball

                for w in ws(d):
                    kind = norm(w.get("kind")).lower()
                    po = norm(w.get("player_out"))
                    if po and kind not in {"retired hurt", "retired not out"}:
                        dismissed.add(po)

                batter = norm(d.get("batter"))
                bowler = norm(d.get("bowler"))
                r = d.get("runs", {}) or {}
                br = si(r.get("batter"))
                wr = si(e.get("wides"))
                nbr = si(e.get("noballs"))

                if batter and name_to_id.get(batter):
                    eid = name_to_id[batter]
                    key = (mid, eid)
                    all_regulation_event_keys.add(key)
                    p = target_raw_pm[key]
                    p["name"] = batter
                    p["runs"] += br
                    p["balls"] += legal_ball
                    p["fours"] += br == 4
                    p["sixes"] += br == 6

                if bowler and name_to_id.get(bowler):
                    eid = name_to_id[bowler]
                    key = (mid, eid)
                    all_regulation_event_keys.add(key)
                    p = target_raw_pm[key]
                    p["name"] = bowler
                    p["runs_conceded"] += br + wr + nbr
                    p["balls_bowled"] += legal_ball

                    for w in ws(d):
                        kind = norm(w.get("kind")).lower()
                        if kind not in {
                            "retired hurt",
                            "retired not out",
                            "retired out",
                            "obstructing the field",
                            "run out",
                        }:
                            p["wickets"] += 1

            if legal > 120:
                over120.append({
                    "match_id": mid,
                    "date": norm((info.get("dates") or [""])[0] if isinstance(info.get("dates"), list) else info.get("dates")),
                    "team": team,
                    "innings": inn_no,
                    "legal_balls": legal,
                    "delivery_count": len(deliveries_list),
                    "dismissed": len(dismissed),
                    "last_over": max((x[0] for x in deliveries_list), default=None),
                })

# Aggregate raw career from actual statistical event keys only.
for (mid, eid), p in target_raw_pm.items():
    c = raw_career[eid]
    c["matches"].add(mid)
    c["runs"] += p["runs"]
    c["balls"] += p["balls"]
    c["fours"] += p["fours"]
    c["sixes"] += p["sixes"]
    c["balls_bowled"] += p["balls_bowled"]
    c["runs_conceded"] += p["runs_conceded"]
    c["wickets"] += p["wickets"]

print("Innings with >120 legal balls:", len(over120))
for x in over120:
    print(x)

# ---------------------------------------------------------------------------
# ALLOCATION: report rather than impose a guessed rule.
# ---------------------------------------------------------------------------
section("ALLOCATED-BALLS FORENSIC REPORT")

mts_by_key = {(r["match_id"], norm(r["team_name"])): r for r in mts}

if over120:
    for x in over120:
        key = (x["match_id"], x["team"])
        row = mts_by_key.get(key)
        print(
            f"{x['match_id']} | {x['team']} | "
            f"legal={x['legal_balls']} | "
            f"processed_total={si(row['total_balls']) if row else 'MISSING'} | "
            f"processed_allocated={si(row['allocated_balls']) if row else 'MISSING'} | "
            f"innings={x['innings']} | dismissed={x['dismissed']} | "
            f"last_over={x['last_over']}"
        )
else:
    print("No >120 legal-ball innings found.")

# V4 does not declare an allocation failure simply from these records.
print("\nInterpretation:")
print("- total_balls is the actual legal-delivery count and was already reconciled globally.")
print("- allocated_balls is a denominator for NRR/standings and requires match-rule context.")
print("- The >120 cases are isolated for inspection; no processor change is made by V4.")

# ---------------------------------------------------------------------------
# TARGET MATCH 1536623
# ---------------------------------------------------------------------------
section("TARGET WICKET MATCH 1536623")

if target_match_data is None:
    print("[FAIL] Match 1536623 not found in raw ZIP")
else:
    info = target_match_data.get("info", {}) or {}
    outcome = info.get("outcome", {}) or {}
    print("Date:", (info.get("dates") or [""])[0] if isinstance(info.get("dates"), list) else info.get("dates"))
    print("Teams:", info.get("teams"))
    print("Outcome:", json.dumps(outcome, ensure_ascii=False))

    registry = ((info.get("registry") or {}).get("people") or {})
    name_to_id = {norm(n): norm(pid) for n, pid in registry.items() if pid}

    target_raw_bowler_wickets = defaultdict(list)

    for inn_no, inn in enumerate(target_match_data.get("innings", []) or [], start=1):
        if is_super(inn):
            continue
        print(f"\nInnings {inn_no}: {inn.get('team')}")
        for over_no, ball_no, d in ds(inn):
            for w in ws(d):
                kind = norm(w.get("kind")).lower()
                bowler = norm(d.get("bowler"))
                player_out = norm(w.get("player_out"))
                eid = name_to_id.get(bowler, "")
                target_raw_bowler_wickets[eid].append({
                    "over": over_no,
                    "ball_in_over": ball_no,
                    "bowler": bowler,
                    "external_id": eid,
                    "player_out": player_out,
                    "kind": kind,
                })
                print(
                    f"  over={over_no}.{ball_no} "
                    f"bowler={bowler} "
                    f"out={player_out} "
                    f"kind={kind}"
                )

    print("\nBowler wicket summary:")
    for eid, items in target_raw_bowler_wickets.items():
        credited = [
            x for x in items
            if x["kind"] not in {
                "retired hurt", "retired not out", "retired out",
                "obstructing the field", "run out"
            }
        ]
        print(
            f"  {items[0]['bowler'] if items else eid}: "
            f"all_dismissals={len(items)}, credited_to_bowler={len(credited)}, "
            f"external_id={eid}"
        )
        processed = pm_by_key.get((TARGET_WICKET_MATCH, eid))
        if processed:
            print("    processed wickets:", si(processed["wickets"]))
        else:
            print("    processed row: MISSING")

# ---------------------------------------------------------------------------
# PLAYER-MATCH EVENT-UNIVERSE RECONCILIATION
# ---------------------------------------------------------------------------
section("PLAYER-MATCH EVENT UNIVERSE")

raw_event_keys = set(target_raw_pm)
processed_keys = set(pm_by_key)
missing_event = raw_event_keys - processed_keys
extra_event = processed_keys - raw_event_keys

print("Raw statistical-event keys:", len(raw_event_keys))
print("Processed keys:", len(processed_keys))
print("Missing processed event keys:", len(missing_event))
print("Extra processed keys:", len(extra_event))

if not missing_event:
    print("[PASS] Every raw statistical-event player key exists in processed data")
else:
    print("[FAIL] Missing statistical-event player keys:", len(missing_event))
    for x in list(missing_event)[:30]:
        print(" ", x)

if not extra_event:
    print("[PASS] No extra processed player keys")
else:
    print("[FAIL] Extra processed player keys:", len(extra_event))

field_mismatches = []
for key in raw_event_keys & processed_keys:
    a = target_raw_pm[key]
    b = pm_by_key[key]
    checks = [
        ("runs", a["runs"], si(b["batting_runs"])),
        ("balls_faced", a["balls"], si(b["balls_faced"])),
        ("fours", a["fours"], si(b["fours"])),
        ("sixes", a["sixes"], si(b["sixes"])),
        ("balls_bowled", a["balls_bowled"], si(b["balls_bowled"])),
        ("runs_conceded", a["runs_conceded"], si(b["runs_conceded"])),
        ("wickets", a["wickets"], si(b["wickets"])),
    ]
    for field, exp, act in checks:
        if exp != act:
            field_mismatches.append((key, field, exp, act, a["name"]))

print("Statistical field mismatches:", len(field_mismatches))
if not field_mismatches:
    print("[PASS] Raw and processed player-match event statistics reconcile exactly")
else:
    print("[FAIL] Player-match mismatches:", len(field_mismatches))
    for x in field_mismatches[:50]:
        print(" ", x)

# ---------------------------------------------------------------------------
# CAREER BY EXTERNAL ID
# ---------------------------------------------------------------------------
section("CAREER BY EXTERNAL ID - EVENT UNIVERSE")

raw_ids = set(raw_career)
proc_ids = set(career_by_id)

missing_career = raw_ids - proc_ids
extra_career = proc_ids - raw_ids

print("Raw career IDs from statistical events:", len(raw_ids))
print("Processed career IDs:", len(proc_ids))
print("Missing:", len(missing_career))
print("Extra:", len(extra_career))

if not missing_career:
    print("[PASS] Every statistical-event career ID exists in processed career")
else:
    print("[FAIL] Missing career IDs:", len(missing_career))
    for x in list(missing_career)[:30]:
        print(" ", x)

if not extra_career:
    print("[PASS] No extra processed career IDs")
else:
    print("[FAIL] Extra career IDs:", len(extra_career))

career_mismatches = []
for eid in raw_ids & proc_ids:
    a = raw_career[eid]
    b = career_by_id[eid]
    checks = [
        ("matches", len(a["matches"]), si(b["matches"])),
        ("runs", a["runs"], si(b["runs"])),
        ("balls_faced", a["balls"], si(b["balls_faced"])),
        ("fours", a["fours"], si(b["fours"])),
        ("sixes", a["sixes"], si(b["sixes"])),
        ("balls_bowled", a["balls_bowled"], si(b["balls_bowled"])),
        ("runs_conceded", a["runs_conceded"], si(b["runs_conceded"])),
        ("wickets", a["wickets"], si(b["wickets"])),
    ]
    for field, exp, act in checks:
        if exp != act:
            career_mismatches.append((eid, field, exp, act, b.get("player_name")))

print("Career field mismatches:", len(career_mismatches))
if not career_mismatches:
    print("[PASS] Career statistics reconcile exactly by external ID")
else:
    print("[FAIL] Career mismatches:", len(career_mismatches))
    for x in career_mismatches[:50]:
        print(" ", x)

# ---------------------------------------------------------------------------
# FINAL DECISION
# ---------------------------------------------------------------------------
section("V4 INTERPRETATION")

print("V4 is a forensic diagnostic, not a blind import gate.")
print()
print("The three questions we are answering are:")
print("1. Are the 41 >120-ball cases real unusual innings or a processor error?")
print("2. Why does match 1536623 report K Kunwar as 2 raw bowler wickets vs 1 processed?")
print("3. After restricting the raw universe to actual batting/bowling events,")
print("   do player-match and career statistics reconcile by external ID?")
print()
print("IMPORTANT: Do not modify process_t20i_dataset.py or run the full MySQL import")
print("until these three questions are resolved.")
