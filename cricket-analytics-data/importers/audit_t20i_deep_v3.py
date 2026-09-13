import csv
import json
import os
import zipfile
from collections import Counter, defaultdict

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
PROCESSED_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"

MATCHES_CSV = os.path.join(PROCESSED_DIR, "matches.csv")
MATCH_TEAM_CSV = os.path.join(PROCESSED_DIR, "match_team_stats.csv")
PLAYER_MATCH_CSV = os.path.join(PROCESSED_DIR, "player_match_performance.csv")
PLAYER_STATS_CSV = os.path.join(PROCESSED_DIR, "player_statistics.csv")
TEAMS_CSV = os.path.join(PROCESSED_DIR, "teams.csv")

TEAM_NORMALIZATION = {
    "United States of America": "United States of America",
    "USA": "United States of America",
    "U.S.A.": "United States of America",
    "United Arab Emirates": "United Arab Emirates",
    "UAE": "United Arab Emirates",
    "West Indies": "West Indies",
    "Hong Kong": "Hong Kong",
    "Hong Kong, China": "Hong Kong",
    "Türkiye": "Turkey",
    "Turks and Caicos Islands": "Turks and Caicos Island",
}

PASS = WARN = FAIL = 0

def section(s):
    print("\n" + "=" * 92)
    print(s)
    print("=" * 92)

def ok(s):
    global PASS
    PASS += 1
    print("[PASS]", s)

def warn(s):
    global WARN
    WARN += 1
    print("[WARN]", s)

def fail(s):
    global FAIL
    FAIL += 1
    print("[FAIL]", s)

def si(v, default=0):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def sf(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def norm_team(v):
    return TEAM_NORMALIZATION.get(str(v).strip(), str(v).strip())

def load(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def extras(d):
    x = d.get("extras", {})
    return x if isinstance(x, dict) else {}

def wickets(d):
    x = d.get("wickets", [])
    return x if isinstance(x, list) else []

def deliveries(inn):
    for ov in inn.get("overs", []) or []:
        if not isinstance(ov, dict):
            continue
        for d in ov.get("deliveries", []) or []:
            if isinstance(d, dict):
                yield d

def is_super(inn):
    return bool(inn.get("super_over", False))

# A wicket counts as a team dismissal except retired hurt/not out.
TEAM_DISMISSAL_EXCLUDED = {"retired hurt", "retired not out"}

# A wicket is credited to the bowler unless it is one of these.
# This is the normal dismissal-credit rule used by the processor audit.
BOWLER_WICKET_EXCLUDED = {
    "retired hurt",
    "retired not out",
    "retired out",
    "obstructing the field",
    "run out",
}

section("T20I DEEP DATASET AUDIT V3 - FINAL PRE-IMPORT GATE")
print("READ-ONLY AUDIT")
print("No files or database records will be modified.")

section("FILE CHECK")
paths = [RAW_ZIP, MATCHES_CSV, MATCH_TEAM_CSV, PLAYER_MATCH_CSV,
         PLAYER_STATS_CSV, TEAMS_CSV]
for p in paths:
    if os.path.exists(p):
        ok("Exists: " + p)
    else:
        fail("Missing: " + p)
if FAIL:
    raise SystemExit(1)

matches = load(MATCHES_CSV)
mts = load(MATCH_TEAM_CSV)
pm = load(PLAYER_MATCH_CSV)
career = load(PLAYER_STATS_CSV)
teams = load(TEAMS_CSV)

section("PROCESSED BASELINE")
print(f"Processed matches:          {len(matches):,}")
print(f"Processed match-team rows:  {len(mts):,}")
print(f"Processed player-match:     {len(pm):,}")
print(f"Processed career rows:      {len(career):,}")
print(f"Processed teams:            {len(teams):,}")

if len(matches) == 5700: ok("Processed matches = 5,700")
else: fail(f"Processed matches = {len(matches):,}")

if len(mts) == 11400: ok("Processed match-team rows = 11,400")
else: fail(f"Processed match-team rows = {len(mts):,}")

pm_by_key = {(r["match_id"], r["player_external_id"]): r for r in pm}
career_by_id = {r["player_external_id"]: r for r in career if r.get("player_external_id")}

section("RAW SCAN + AUTHORITATIVE RECOMPUTATION")

raw_ids = set()
raw_match_count = 0
raw_reg_runs = raw_reg_batter = raw_reg_extras = 0
raw_legal_balls = raw_so_deliveries = raw_so_runs = 0
raw_fours = raw_sixes = raw_team_wickets = raw_bowler_wickets = 0
raw_no_results = set()
raw_ties = set()
raw_super_matches = set()

# Raw match-team and player-match aggregates keyed by stable identity.
raw_team = defaultdict(lambda: {
    "runs":0, "extras":0, "legal":0, "fours":0, "sixes":0, "wickets":0
})
raw_pm = defaultdict(lambda: {
    "name": "", "runs":0, "balls":0, "fours":0, "sixes":0,
    "balls_bowled":0, "runs_conceded":0, "wickets":0
})
raw_pm_matches = defaultdict(set)

# For career aggregate by external ID.
raw_career = defaultdict(lambda: {
    "matches": set(), "runs":0, "balls":0, "fours":0, "sixes":0,
    "balls_bowled":0, "runs_conceded":0, "wickets":0
})

# Allocation diagnostics.
allocation_cases = Counter()
allocation_mismatches = []
all_out_count = 0
shortened_count = 0

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    files = [n for n in z.namelist() if n.lower().endswith(".json")]
    print("JSON files:", len(files))
    if len(files) == 5700: ok("Raw JSON file count = 5,700")
    else: fail(f"Raw JSON file count = {len(files):,}")

    for fn in files:
        mid = os.path.splitext(os.path.basename(fn))[0]
        raw_ids.add(mid)
        raw_match_count += 1
        with z.open(fn) as f:
            data = json.load(f)

        info = data.get("info", {})
        outcome = info.get("outcome", {}) or {}
        result = str(outcome.get("result", "")).strip().lower()

        if result == "no result":
            raw_no_results.add(mid)
        elif result == "tie":
            raw_ties.add(mid)

        inns = data.get("innings", []) or []
        has_so = any(is_super(i) for i in inns if isinstance(i, dict))
        if has_so:
            raw_super_matches.add(mid)

        # registry maps display name -> stable ID
        registry = ((info.get("registry") or {}).get("people") or {})
        name_to_id = {str(n).strip(): str(pid).strip()
                      for n, pid in registry.items() if pid}

        # Each participant listed by the innings is included in player-match
        # aggregates even if they have zero batting/bowling events.
        players_by_team = info.get("players", {}) or {}
        for plist in players_by_team.values():
            if isinstance(plist, list):
                for name in plist:
                    name = str(name).strip()
                    eid = name_to_id.get(name)
                    if eid:
                        key = (mid, eid)
                        raw_pm[key]["name"] = name
                        raw_pm_matches[eid].add(mid)

        for inn in inns:
            if not isinstance(inn, dict) or is_super(inn):
                # Super Overs are deliberately excluded from normal statistics.
                if isinstance(inn, dict) and is_super(inn):
                    for d in deliveries(inn):
                        raw_so_deliveries += 1
                        r = d.get("runs", {}) or {}
                        raw_so_runs += si(r.get("batter")) + si(r.get("extras"))
                continue

            team = norm_team(inn.get("team", ""))
            ds = list(deliveries(inn))

            dismissed = set()
            for d in ds:
                for w in wickets(d):
                    kind = str(w.get("kind", "")).lower()
                    po = w.get("player_out")
                    if po and kind not in TEAM_DISMISSAL_EXCLUDED:
                        dismissed.add(str(po).strip())

            legal = 0
            for d in ds:
                ex = extras(d)
                is_wide = "wides" in ex
                is_nb = "noballs" in ex
                legal_ball = not is_wide and not is_nb
                if legal_ball:
                    legal += 1
                r = d.get("runs", {}) or {}
                br = si(r.get("batter"))
                er = si(r.get("extras"))
                tr = br + er
                raw_reg_runs += tr
                raw_reg_batter += br
                raw_reg_extras += er
                raw_legal_balls += legal_ball
                if br == 4:
                    raw_fours += 1
                if br == 6:
                    raw_sixes += 1

                ts = raw_team[(mid, team)]
                ts["runs"] += tr
                ts["extras"] += er
                ts["legal"] += legal_ball
                ts["fours"] += br == 4
                ts["sixes"] += br == 6

                for w in wickets(d):
                    kind = str(w.get("kind", "")).lower()
                    if kind not in TEAM_DISMISSAL_EXCLUDED:
                        ts["wickets"] += 1
                        raw_team_wickets += 1
                    if kind not in BOWLER_WICKET_EXCLUDED:
                        raw_bowler_wickets += 1

                batter = str(d.get("batter", "")).strip()
                bowler = str(d.get("bowler", "")).strip()

                if batter:
                    eid = name_to_id.get(batter)
                    if eid:
                        k = (mid, eid)
                        p = raw_pm[k]
                        p["name"] = batter
                        p["runs"] += br
                        p["balls"] += legal_ball
                        p["fours"] += br == 4
                        p["sixes"] += br == 6

                if bowler:
                    eid = name_to_id.get(bowler)
                    if eid:
                        k = (mid, eid)
                        p = raw_pm[k]
                        p["name"] = bowler
                        # Bowler is charged batter runs + wides + no-balls.
                        p["runs_conceded"] += br + si(ex.get("wides")) + si(ex.get("noballs"))
                        p["balls_bowled"] += legal_ball
                        for w in wickets(d):
                            kind = str(w.get("kind", "")).lower()
                            if kind not in BOWLER_WICKET_EXCLUDED:
                                p["wickets"] += 1

            # Allocation diagnostics:
            # Actual legal balls are always authoritative for statistics.
            # For a normal 20-over innings, the maximum allocation is 120.
            # For a completed innings, NRR uses actual balls unless the team
            # completed the scheduled overs. For an incomplete/no-result
            # innings, the processor's stored allocation must be auditable.
            overs = inn.get("overs", []) or []
            max_over = None
            if overs:
                try:
                    max_over = max(si(o.get("over")) for o in overs if isinstance(o, dict))
                except ValueError:
                    max_over = None

            # Detect all-out independently.
            is_all_out = len(dismissed) >= 10
            if is_all_out:
                all_out_count += 1

            # The raw record can indicate reduced overs through target/official
            # metadata, but this source does not expose one universal field.
            # Therefore V3 records the case; it does NOT invent a false
            # expected allocation.
            nominal = 120
            if legal >= nominal:
                expected_alloc = nominal
                reason = "FULL_20_OVERS"
            elif is_all_out:
                expected_alloc = legal
                reason = "ALL_OUT"
            else:
                # Reached target / interruption / reduced overs cannot be
                # safely inferred solely from delivery count. Use legal balls
                # as the conservative allocation unless explicit processor
                # metadata says otherwise.
                expected_alloc = legal
                reason = "INCOMPLETE_OR_TARGET"

            allocation_cases[reason] += 1
            processed = next((r for r in mts
                              if r["match_id"] == mid and
                              norm_team(r["team_name"]) == team), None)
            if processed:
                actual_alloc = si(processed.get("allocated_balls"))
                # Only enforce allocation when it is objectively derivable.
                if reason in {"FULL_20_OVERS", "ALL_OUT"} and actual_alloc != expected_alloc:
                    allocation_mismatches.append(
                        (mid, team, reason, legal, expected_alloc, actual_alloc)
                    )

            # Build career aggregate after player-match data is known below.

# Raw player career by external ID.
for (mid, eid), s in raw_pm.items():
    c = raw_career[eid]
    c["matches"].add(mid)
    c["runs"] += s["runs"]
    c["balls"] += s["balls"]
    c["fours"] += s["fours"]
    c["sixes"] += s["sixes"]
    c["balls_bowled"] += s["balls_bowled"]
    c["runs_conceded"] += s["runs_conceded"]
    c["wickets"] += s["wickets"]

section("RAW BASELINES")
print(f"Raw matches:                    {raw_match_count:,}")
print(f"Raw regulation runs:            {raw_reg_runs:,}")
print(f"Raw batter runs:                {raw_reg_batter:,}")
print(f"Raw extras:                     {raw_reg_extras:,}")
print(f"Raw legal balls:                {raw_legal_balls:,}")
print(f"Raw team wickets:               {raw_team_wickets:,}")
print(f"Raw bowler wickets:             {raw_bowler_wickets:,}")
print(f"Raw fours:                      {raw_fours:,}")
print(f"Raw sixes:                      {raw_sixes:,}")
print(f"Raw Super Over deliveries:      {raw_so_deliveries:,}")
print(f"Raw Super Over runs:            {raw_so_runs:,}")
print(f"All-out regulation innings:     {all_out_count:,}")
print(f"Allocation mismatches enforced: {len(allocation_mismatches):,}")

if raw_match_count == 5700: ok("Raw matches = 5,700")
else: fail("Raw match count mismatch")

if len(raw_ids) == 5700: ok("Raw match IDs unique = 5,700")
else: fail("Raw match IDs not unique")

if raw_so_deliveries == 550: ok("Super Over deliveries = 550")
else: fail(f"Super Over deliveries = {raw_so_deliveries:,}")

if raw_so_runs == 1028: ok("Super Over runs = 1,028")
else: fail(f"Super Over runs = {raw_so_runs:,}")

section("RAW VS PROCESSED MATCH IDS")
processed_ids = {r["match_id"] for r in matches}
if raw_ids - processed_ids:
    fail(f"{len(raw_ids - processed_ids)} raw IDs missing from processed")
else: ok("Every raw match exists in processed")
if processed_ids - raw_ids:
    fail(f"{len(processed_ids - raw_ids)} processed IDs absent from raw")
else: ok("No extra processed matches")

section("RESULT RECONCILIATION")
raw_result = {"WINNER": raw_match_count - len(raw_no_results) - len(raw_ties),
              "TIED": len(raw_ties), "NO_RESULT": len(raw_no_results)}
proc_result = Counter()
for r in matches:
    rt = r.get("result_type", "").strip().upper()
    if rt in {"WINNER","TIED","NO_RESULT"}:
        proc_result[rt] += 1
print("Raw:", raw_result)
print("Processed:", dict(proc_result))
for k, expected in raw_result.items():
    if proc_result[k] == expected: ok(f"{k} count = {expected:,}")
    else: fail(f"{k} count mismatch")
proc_no = {r["match_id"] for r in matches if r["result_type"].strip().upper()=="NO_RESULT"}
proc_tie = {r["match_id"] for r in matches if r["result_type"].strip().upper()=="TIED"}
if proc_no == raw_no_results: ok("No-result match sets identical")
else: fail("No-result match sets differ")
if proc_tie == raw_ties: ok("Tied match sets identical")
else: fail("Tied match sets differ")

section("GLOBAL RUN / BALL RECONCILIATION")
p_runs = sum(si(r["batting_runs"]) for r in pm)
t_runs = sum(si(r["runs"]) for r in mts)
t_extra = sum(si(r["extras"]) for r in mts)
p_fours = sum(si(r["fours"]) for r in pm)
t_fours = sum(si(r["fours"]) for r in mts)
p_sixes = sum(si(r["sixes"]) for r in pm)
t_sixes = sum(si(r["sixes"]) for r in mts)
p_wickets = sum(si(r["wickets"]) for r in pm)
t_wickets = sum(si(r["wickets"]) for r in mts)
p_balls = sum(si(r["balls_faced"]) for r in pm)
t_balls = sum(si(r["total_balls"]) for r in mts)

print("Raw regulation runs:", raw_reg_runs)
print("Processed team runs:", t_runs)
print("Processed player runs:", p_runs)
print("Processed extras:", t_extra)
print("Raw legal balls:", raw_legal_balls)
print("Processed total_balls:", t_balls)

if t_runs == raw_reg_runs: ok("Team runs = raw regulation runs")
else: fail("Team runs mismatch")
if p_runs == raw_reg_batter: ok("Player batting runs = raw batter runs")
else: fail("Player batting runs mismatch")
if t_extra == raw_reg_extras: ok("Team extras = raw regulation extras")
else: fail("Extras mismatch")
if p_runs + t_extra == t_runs: ok("Player runs + extras = team runs")
else: fail("Player runs + extras mismatch")
if t_balls == raw_legal_balls: ok("Total balls = raw legal balls")
else: fail("Legal balls mismatch")
if p_fours == t_fours == raw_fours: ok("Fours reconcile")
else: fail("Fours mismatch")
if p_sixes == t_sixes == raw_sixes: ok("Sixes reconcile")
else: fail("Sixes mismatch")
if t_wickets == raw_team_wickets: ok("Team wickets = raw team dismissals")
else: fail("Team wickets mismatch")

section("ALLOCATED-BALLS AUDIT")
print("Only objectively derivable FULL_20_OVERS and ALL_OUT cases are enforced.")
print("This avoids falsely treating target-chases/reduced-overs/no-result innings as 120-ball innings.")
print("Allocation cases:", dict(allocation_cases))
print("Enforced allocation mismatches:", len(allocation_mismatches))
if not allocation_mismatches:
    ok("All objectively derivable allocated_balls values are correct")
else:
    fail(f"{len(allocation_mismatches)} objectively derivable allocated_balls mismatches")
    for x in allocation_mismatches[:40]:
        print(x)

section("PLAYER-MATCH RECONCILIATION BY EXTERNAL ID")
raw_keys = set(raw_pm)
proc_keys = set(pm_by_key)
print("Raw keys:", len(raw_keys))
print("Processed keys:", len(proc_keys))
missing = raw_keys - proc_keys
extra = proc_keys - raw_keys
print("Missing:", len(missing))
print("Extra:", len(extra))
if not missing: ok("Every raw player-match external-ID key exists")
else: fail(f"{len(missing)} player-match keys missing")
if not extra: ok("No extra processed player-match external-ID keys")
else: fail(f"{len(extra)} extra player-match keys")

mismatches = []
for key in raw_keys & proc_keys:
    a = raw_pm[key]
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
            mismatches.append((key, field, exp, act, a["name"]))
print("Field mismatches:", len(mismatches))
if not mismatches:
    ok("Raw and processed player-match statistics reconcile exactly")
else:
    fail(f"{len(mismatches)} player-match field mismatches")
    for x in mismatches[:40]:
        print(x)

section("CAREER RECONCILIATION BY EXTERNAL ID")
raw_career_ids = set(raw_career)
proc_career_ids = set(career_by_id)
print("Raw career IDs:", len(raw_career_ids))
print("Processed career IDs:", len(proc_career_ids))
cmissing = raw_career_ids - proc_career_ids
cextra = proc_career_ids - raw_career_ids
print("Missing:", len(cmissing))
print("Extra:", len(cextra))
if not cmissing: ok("Every raw career external ID exists in processed career")
else: fail(f"{len(cmissing)} career IDs missing")
if not cextra: ok("No extra processed career external IDs")
else: fail(f"{len(cextra)} extra career external IDs")

cm = []
for eid in raw_career_ids & proc_career_ids:
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
            cm.append((eid, field, exp, act, b.get("player_name")))
print("Career field mismatches:", len(cm))
if not cm: ok("Career statistics reconcile exactly by external ID")
else:
    fail(f"{len(cm)} career field mismatches")
    for x in cm[:40]:
        print(x)

section("CAREER DERIVED STATISTICS")
derived = []
for r in career:
    runs = si(r["runs"]); balls = si(r["balls_faced"])
    bb = si(r["balls_bowled"]); rc = si(r["runs_conceded"])
    inns = si(r["batting_innings"]); no = si(r["not_outs"])
    if no > inns:
        derived.append((r["player_external_id"], "not_outs > batting_innings"))
    if balls:
        expected = runs / balls * 100
        if abs(expected - sf(r["strike_rate"])) > 0.02:
            derived.append((r["player_external_id"], "strike_rate", expected, sf(r["strike_rate"])))
    if bb:
        expected = rc / bb * 6
        if abs(expected - sf(r["economy"])) > 0.02:
            derived.append((r["player_external_id"], "economy", expected, sf(r["economy"])))
print("Derived errors:", len(derived))
if not derived: ok("Career derived statistics are mathematically consistent")
else:
    fail(f"{len(derived)} derived-stat errors")
    for x in derived[:30]:
        print(x)

section("PLAYER ALIAS / ID SANITY")
names_by_id = defaultdict(set)
for (mid, eid), p in raw_pm.items():
    if p["name"]:
        names_by_id[eid].add(p["name"])
aliases = {eid:n for eid,n in names_by_id.items() if len(n)>1}
print("External IDs with multiple display names:", len(aliases))
if aliases:
    warn("Multiple display names exist for some stable IDs; external ID is correctly used for career identity.")
    for eid, names in list(aliases.items())[:15]:
        print(eid, sorted(names))
else:
    ok("No player alias collisions detected")

section("FINAL RESULT")
print("PASS checks:", PASS)
print("WARN checks:", WARN)
print("FAIL checks:", FAIL)
print()
if FAIL == 0:
    print("T20I DEEP AUDIT V3: PASS")
    print("SAFE TO PROCEED TO FULL T20I MYSQL IMPORT.")
else:
    print("T20I DEEP AUDIT V3: FAIL")
    print("DO NOT IMPORT ALL T20I DATA INTO MYSQL YET.")
