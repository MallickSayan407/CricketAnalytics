import csv
import json
import os
import zipfile
from collections import Counter, defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_ZIP = os.path.join(BASE_DIR, "raw", "international", "tests_json.zip")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed", "test")

TEAM_CSV = os.path.join(PROCESSED_DIR, "match_team_stats.csv")
PMP_CSV = os.path.join(PROCESSED_DIR, "player_match_performance.csv")
CAREER_CSV = os.path.join(PROCESSED_DIR, "player_statistics.csv")

def n(v):
    try:
        return int(v or 0)
    except:
        return 0

def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def legal(d):
    e = d.get("extras", {}) or {}
    return "wides" not in e and "noballs" not in e

NON_BOWLER = {
    "run out", "retired hurt", "retired not out",
    "obstructing the field", "handled the ball", "timed out"
}

team_rows = load(TEAM_CSV)
pmp_rows = load(PMP_CSV)
career_rows = load(CAREER_CSV)

print("=" * 100)
print("TEST DATASET TARGETED DIAGNOSTIC")
print("=" * 100)

# ------------------------------------------------------------
# 1. Duplicate processed PMP keys
# ------------------------------------------------------------
print("\n" + "-" * 100)
print("1. DUPLICATE PLAYER-MATCH-TEAM KEYS")
print("-" * 100)

pmp_groups = defaultdict(list)
for r in pmp_rows:
    key = (r.get("match_id"), r.get("player_id"), r.get("team_id"))
    pmp_groups[key].append(r)

dup_pmp = {k:v for k,v in pmp_groups.items() if len(v) > 1}
print("Duplicate keys:", len(dup_pmp))
for key, rows in list(dup_pmp.items())[:100]:
    print("\nKEY:", key)
    for r in rows:
        print({
            "player_name": r.get("player_name"),
            "team_name": r.get("team_name"),
            "batting_runs": r.get("batting_runs"),
            "balls_faced": r.get("balls_faced"),
            "fours": r.get("fours"),
            "sixes": r.get("sixes"),
            "balls_bowled": r.get("balls_bowled"),
            "runs_conceded": r.get("runs_conceded"),
            "wickets": r.get("wickets"),
            "maidens": r.get("maidens"),
            "batted": r.get("batted"),
            "not_out": r.get("not_out"),
        })

# ------------------------------------------------------------
# 2. Duplicate career IDs
# ------------------------------------------------------------
print("\n" + "-" * 100)
print("2. DUPLICATE CAREER PLAYER IDs")
print("-" * 100)

career_groups = defaultdict(list)
for r in career_rows:
    career_groups[r.get("player_id")].append(r)

dup_career = {k:v for k,v in career_groups.items() if len(v) > 1}
print("Duplicate career IDs:", len(dup_career))
for key, rows in list(dup_career.items())[:100]:
    print("\nPLAYER ID:", key)
    for r in rows:
        print({
            "player_name": r.get("player_name"),
            "player_external_id": r.get("player_external_id"),
            "gender": r.get("gender"),
            "team_name": r.get("team_name"),
            "matches": r.get("matches"),
            "runs": r.get("runs"),
            "wickets": r.get("wickets"),
        })

# ------------------------------------------------------------
# 3. Extra team rows
# ------------------------------------------------------------
print("\n" + "-" * 100)
print("3. EXTRA PROCESSED MATCH-TEAM ROWS")
print("-" * 100)

extra_targets = [
    ("1022599", "India"),
    ("464989", "Sri Lanka"),
    ("352662", "West Indies"),
    ("817215", "South Africa"),
]

processed_team_lookup = defaultdict(list)
for r in team_rows:
    processed_team_lookup[(r.get("match_id"), r.get("team_name"))].append(r)

for match_id, team in extra_targets:
    print("\nMATCH:", match_id, "TEAM:", team)
    for r in processed_team_lookup.get((match_id, team), []):
        print("Processed:", dict(r))

# ------------------------------------------------------------
# 4. Find exact wicket discrepancy
# ------------------------------------------------------------
print("\n" + "-" * 100)
print("4. FIND EXACT EXTRA BOWLER WICKET")
print("-" * 100)

raw_wickets = []
with zipfile.ZipFile(RAW_ZIP, "r") as z:
    for filename in z.namelist():
        if not filename.lower().endswith(".json"):
            continue
        with z.open(filename) as f:
            m = json.load(f)

        info = m.get("info", {}) or {}
        rid = str(info.get("registry", {}).get("data", {}).get("cricsheet", ""))
        if not rid:
            rid = os.path.splitext(os.path.basename(filename))[0]

        # Map player name -> declared registry ID where available
        people = info.get("registry", {}).get("people", {}) or {}

        for inn_no, inn in enumerate(m.get("innings", []) or [], 1):
            team = inn.get("team")
            for over in inn.get("overs", []) or []:
                for over_no, d in [(over.get("over"), d) for d in over.get("deliveries", []) or []]:
                    bowler = d.get("bowler")
                    for wi, w in enumerate(d.get("wickets", []) or []):
                        kind = str(w.get("kind", "")).strip().lower()
                        if kind in NON_BOWLER:
                            continue
                        raw_wickets.append({
                            "match_id": rid,
                            "innings": inn_no,
                            "over": over_no,
                            "bowler": bowler,
                            "bowler_id": people.get(bowler),
                            "player_out": w.get("player_out"),
                            "kind": kind,
                            "fielders": w.get("fielders"),
                        })

# Processed wicket totals grouped by player/match/team.
processed_wickets = defaultdict(int)
for r in pmp_rows:
    processed_wickets[(r.get("match_id"), r.get("player_id"), r.get("team_id"), r.get("player_name"))] += n(r.get("wickets"))

# Build name -> IDs from raw registry.
raw_expected_by_name_match = defaultdict(int)
raw_examples_by_name_match = defaultdict(list)
for w in raw_wickets:
    key = (w["match_id"], w["bowler"], str(w["bowler_id"] or ""))
    raw_expected_by_name_match[key] += 1
    raw_examples_by_name_match[key].append(w)

# Compare raw bowler wickets against processed using player external id where possible.
# First create processed rows indexed by external ID.
processed_by_external = defaultdict(int)
processed_rows_by_external = defaultdict(list)
for r in pmp_rows:
    key = (r.get("match_id"), r.get("player_external_id"))
    processed_by_external[key] += n(r.get("wickets"))
    processed_rows_by_external[key].append(r)

differences = []
for key, expected in raw_expected_by_name_match.items():
    match_id, bowler_name, bowler_ext = key
    if not bowler_ext:
        continue
    actual = processed_by_external.get((match_id, bowler_ext), 0)
    if actual != expected:
        differences.append((key, expected, actual, raw_examples_by_name_match[key]))

print("Raw bowler-credit wicket identities checked:", len(raw_expected_by_name_match))
print("Identity-level differences:", len(differences))

for key, expected, actual, examples in differences[:100]:
    print("\nDIFFERENCE")
    print("match_id:", key[0])
    print("bowler:", key[1])
    print("external_id:", key[2])
    print("expected:", expected, "actual:", actual)
    print("wickets:")
    for x in examples:
        print(" ", x)

# ------------------------------------------------------------
# 5. Inspect raw details of the four extra team matches
# ------------------------------------------------------------
print("\n" + "-" * 100)
print("5. RAW DETAILS FOR EXTRA TEAM MATCHES")
print("-" * 100)

target_set = set(x[0] for x in extra_targets)

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    for filename in z.namelist():
        if not filename.lower().endswith(".json"):
            continue
        with z.open(filename) as f:
            m = json.load(f)

        info = m.get("info", {}) or {}
        rid = str(info.get("registry", {}).get("data", {}).get("cricsheet", ""))
        if rid not in target_set:
            continue

        print("\nMATCH", rid)
        print("teams:", info.get("teams"))
        print("gender:", info.get("gender"))
        print("dates:", info.get("dates"))
        print("venue:", info.get("venue"))
        print("outcome:", info.get("outcome"))
        print("innings teams:", [x.get("team") for x in m.get("innings", []) or []])

# ------------------------------------------------------------
# 6. Player external-ID collisions / duplicate identity clues
# ------------------------------------------------------------
print("\n" + "-" * 100)
print("6. PLAYER IDENTITY COLLISION CHECK")
print("-" * 100)

ext_to_names = defaultdict(set)
id_to_names = defaultdict(set)
for r in pmp_rows:
    ext_to_names[r.get("player_external_id")].add(r.get("player_name"))
    id_to_names[r.get("player_id")].add(r.get("player_name"))

ext_collisions = {k:v for k,v in ext_to_names.items() if k and len(v) > 1}
id_collisions = {k:v for k,v in id_to_names.items() if k and len(v) > 1}

print("External IDs mapped to multiple names:", len(ext_collisions))
for k,v in list(ext_collisions.items())[:50]:
    print(" ", k, "=>", v)

print("Player IDs mapped to multiple names:", len(id_collisions))
for k,v in list(id_collisions.items())[:50]:
    print(" ", k, "=>", v)

print("\n" + "=" * 100)
print("DIAGNOSTIC COMPLETE")
print("=" * 100)
print("Paste the complete output back here.")
