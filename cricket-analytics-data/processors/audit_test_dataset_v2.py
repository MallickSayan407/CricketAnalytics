import csv
import json
import zipfile
from collections import defaultdict

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\tests_json.zip"
PROCESSED = r"D:\CricketAnalytics\cricket-analytics-data\processed\test"

def si(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0

def section(title):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

def result(ok, text):
    print(("[PASS] " if ok else "[FAIL] ") + text)

# -----------------------------
# Load processed CSVs
# -----------------------------
def load_csv(name, key=None):
    path = f"{PROCESSED}\\{name}"
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if key is None:
        return rows
    d = {}
    for r in rows:
        d[key(r)] = r
    return d

section("TEST DATASET FINAL FORENSIC AUDIT V2")
print("READ-ONLY: no files or database rows will be changed.")
print("Raw:", RAW_ZIP)
print("Processed:", PROCESSED)

matches_p = load_csv("matches.csv", lambda r: r["match_id"])
team_p_rows = load_csv("match_team_stats.csv")
pm_p_rows = load_csv("player_match_performance.csv")
career_p_rows = load_csv("player_statistics.csv")

section("1. BASIC COUNTS")
print("Processed matches:", len(matches_p))
print("Processed match-team rows:", len(team_p_rows))
print("Processed player-match rows:", len(pm_p_rows))
print("Processed career rows:", len(career_p_rows))
result(len(matches_p) == 918, "918 Test matches processed.")
result(len(team_p_rows) == 1836, "Exactly 2 match-team rows per 918 matches.")

# -----------------------------
# Raw reconstruction
# -----------------------------
raw_matches = {}
raw_team_stats = defaultdict(lambda: {
    "runs": 0, "wickets": 0, "legal_balls": 0,
    "fours": 0, "sixes": 0, "extras": 0
})
raw_pm = defaultdict(lambda: {
    "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
    "balls_bowled": 0, "runs_conceded": 0, "wickets": 0,
    "maidens": 0, "batted": False
})
raw_wickets_by_bowler = defaultdict(int)
raw_bowler_events = defaultdict(list)
raw_match_team_keys = set()

BOWLER_NOT_CREDITED = {
    "run out",
    "retired hurt",
    "retired not out",
    "obstructing the field",
    "retired out",
    "timed out",
    "handled the ball",
}

DELIVERY_EXTRAS = {"wides", "noballs", "byes", "legbyes", "penalty"}

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    files = [n for n in z.namelist()
             if n.lower().endswith(".json")]

    for fn in files:
        mid = fn.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].split(".")[0]
        data = json.loads(z.read(fn))
        info = data.get("info", {})
        raw_matches[mid] = data

        teams = info.get("teams", []) or []
        innings_seen = set()

        for innings in data.get("innings", []) or []:
            team = innings.get("team")
            if team:
                innings_seen.add(team)

            # Innings-level penalty runs are part of the full innings score.
            innings_pen = innings.get("penalty_runs", {}) or {}
            innings_pen_total = si(innings_pen.get("pre")) + si(innings_pen.get("post"))
            if team and innings_pen_total:
                raw_team_stats[(mid, team)]["runs"] += innings_pen_total
                raw_team_stats[(mid, team)]["extras"] += innings_pen_total

            # Track batter names for batting-event universe.
            declared_players = info.get("players", {}).get(team, []) if team else []
            for p in declared_players:
                ext = (info.get("registry", {}).get("people", {}) or {}).get(p)
                if ext:
                    raw_pm[(mid, ext)]["batted"] = raw_pm[(mid, ext)]["batted"]

            for over in innings.get("overs", []) or []:
                # Maiden determination: 6 legal deliveries and 0 bowler runs.
                over_bowler_runs = 0
                over_legal = 0
                over_bowler = None

                for d in over.get("deliveries", []) or []:
                    batter = d.get("batter")
                    bowler = d.get("bowler")
                    runs = d.get("runs", {}) or {}
                    batter_runs = si(runs.get("batter"))
                    total_runs = si(runs.get("total"))
                    extras = d.get("extras", {}) or {}

                    registry = info.get("registry", {}).get("people", {}) or {}
                    batter_ext = registry.get(batter)
                    bowler_ext = registry.get(bowler)

                    is_wide = "wides" in extras
                    is_nb = "noballs" in extras
                    legal = not is_wide and not is_nb

                    if team:
                        raw_team_stats[(mid, team)]["runs"] += total_runs
                        raw_team_stats[(mid, team)]["extras"] += total_runs - batter_runs
                        if legal:
                            raw_team_stats[(mid, team)]["legal_balls"] += 1
                        # Boundaries credited to batter.
                        if batter_runs == 4:
                            raw_team_stats[(mid, team)]["fours"] += 1
                        elif batter_runs == 6:
                            raw_team_stats[(mid, team)]["sixes"] += 1

                    if batter_ext:
                        raw_pm[(mid, batter_ext)]["runs"] += batter_runs
                        raw_pm[(mid, batter_ext)]["fours"] += (1 if batter_runs == 4 else 0)
                        raw_pm[(mid, batter_ext)]["sixes"] += (1 if batter_runs == 6 else 0)
                        raw_pm[(mid, batter_ext)]["batted"] = True
                        if legal:
                            raw_pm[(mid, batter_ext)]["balls"] += 1

                    if bowler_ext:
                        if legal:
                            raw_pm[(mid, bowler_ext)]["balls_bowled"] += 1
                        bowler_runs = batter_runs
                        bowler_runs += si(extras.get("wides"))
                        bowler_runs += si(extras.get("noballs"))
                        raw_pm[(mid, bowler_ext)]["runs_conceded"] += bowler_runs
                        over_bowler_runs += bowler_runs
                        over_bowler = bowler_ext

                    wickets = d.get("wickets", []) or []
                    if wickets:
                        for w in wickets:
                            kind = w.get("kind", "")
                            player_out = w.get("player_out")
                            out_ext = registry.get(player_out)

                            # Genuine dismissal counts as a team wicket except
                            # retired hurt / retired not out.
                            if team and kind not in {"retired hurt", "retired not out"}:
                                raw_team_stats[(mid, team)]["wickets"] += 1

                            # Bowler-credit wickets exclude special non-credit kinds.
                            if (bowler_ext and kind not in BOWLER_NOT_CREDITED):
                                raw_wickets_by_bowler[(mid, bowler_ext)] += 1
                                raw_bowler_events[(mid, bowler_ext)].append(
                                    (kind, player_out)
                                )

                # Cricsheet overs normally have 6 legal deliveries; miscounted
                # overs are preserved as supplied and not fabricated.
                # Maiden is assigned below from processed-style aggregate:
                # a bowler with 6 legal balls and 0 bowler runs in the over.
                if over_bowler is not None:
                    legal_count = sum(
                        1
                        for d in over.get("deliveries", []) or []
                        for _ in [0]
                        if "wides" not in (d.get("extras", {}) or {})
                        and "noballs" not in (d.get("extras", {}) or {})
                    )
                    if legal_count == 6 and over_bowler_runs == 0:
                        raw_pm[(mid, over_bowler)]["maidens"] += 1

        for team in teams:
            raw_match_team_keys.add((mid, team))

section("2. MATCH UNIVERSE")
raw_ids = set(raw_matches)
proc_ids = set(matches_p)
print("Raw matches:", len(raw_ids))
print("Processed matches:", len(matches_p))
print("Missing:", len(raw_ids - set(matches_p)))
print("Extra:", len(set(matches_p) - raw_ids))
result(raw_ids == set(matches_p), "Raw and processed match IDs are identical.")

section("3. MATCH-TEAM UNIVERSE")
proc_team_keys = {(r["match_id"], r["team_name"]) for r in team_p_rows}
missing_team = raw_match_team_keys - proc_team_keys
extra_team = proc_team_keys - raw_match_team_keys
print("Raw info.teams keys:", len(raw_match_team_keys))
print("Processed keys:", len(proc_team_keys))
print("Missing:", len(missing_team))
print("Extra:", len(extra_team))
if missing_team:
    print("Missing examples:", sorted(missing_team)[:20])
if extra_team:
    print("Extra examples:", sorted(extra_team)[:20])
result(not missing_team and not extra_team,
       "Processed match-team keys exactly match info.teams.")

section("4. TEAM STATISTICS RECONCILIATION")
team_mismatches = []
for r in team_p_rows:
    key = (r["match_id"], r["team_name"])
    raw = raw_team_stats[key]
    checks = [
        ("runs", raw["runs"], si(r["runs"])),
        ("wickets", raw["wickets"], si(r["wickets"])),
        ("total_balls", raw["legal_balls"], si(r["total_balls"])),
        ("fours", raw["fours"], si(r["fours"])),
        ("sixes", raw["sixes"], si(r["sixes"])),
    ]
    for field, exp, act in checks:
        if exp != act:
            team_mismatches.append((key, field, exp, act))
print("Team field mismatches:", len(team_mismatches))
for x in team_mismatches[:50]:
    print(" ", x)
result(not team_mismatches, "Team runs, wickets, legal balls and boundaries reconcile exactly.")

section("5. PLAYER-MATCH UNIQUENESS")
pm_keys = [(r["match_id"], r["player_external_id"]) for r in pm_p_rows]
pm_dupes = [k for k in set(pm_keys) if pm_keys.count(k) > 1]
blank_ext = [r for r in pm_p_rows if not r["player_external_id"].strip()]
print("Rows:", len(pm_p_rows))
print("Duplicate (match_id, player_external_id):", len(pm_dupes))
print("Blank external IDs:", len(blank_ext))
if pm_dupes:
    print("Duplicate examples:", pm_dupes[:20])
result(not pm_dupes and not blank_ext,
       "Player-match rows are unique by external player ID.")

section("6. PLAYER-MATCH STATISTICS")
proc_pm = {(r["match_id"], r["player_external_id"]): r for r in pm_p_rows}
pm_mismatches = []
for key, raw in raw_pm.items():
    # Only actual statistical participants belong in the CSV.
    has_stats = any(raw[k] for k in
                    ["runs", "balls", "fours", "sixes",
                     "balls_bowled", "runs_conceded", "wickets", "maidens"])
    if not has_stats:
        continue
    if key not in proc_pm:
        pm_mismatches.append((key, "MISSING", raw))
        continue
    p = proc_pm[key]
    checks = [
        ("runs", raw["runs"], si(p["batting_runs"])),
        ("balls", raw["balls"], si(p["balls_faced"])),
        ("fours", raw["fours"], si(p["fours"])),
        ("sixes", raw["sixes"], si(p["sixes"])),
        ("balls_bowled", raw["balls_bowled"], si(p["balls_bowled"])),
        ("runs_conceded", raw["runs_conceded"], si(p["runs_conceded"])),
        ("wickets", raw["wickets"], si(p["wickets"])),
        ("maidens", raw["maidens"], si(p["maidens"])),
    ]
    for field, exp, act in checks:
        if exp != act:
            pm_mismatches.append((key, field, exp, act, p.get("player_name")))
print("Player-match mismatches:", len(pm_mismatches))
for x in pm_mismatches[:80]:
    print(" ", x)
result(not pm_mismatches, "Player-match statistics reconcile by external ID.")

section("7. BOWLER WICKET FORENSIC")
target = ("63963", None)
sarandeep_ext = None
info = raw_matches["63963"]["info"]
sarandeep_ext = (info.get("registry", {}).get("people", {}) or {}).get("Sarandeep Singh")
print("Sarandeep Singh external ID:", sarandeep_ext)
print("Raw creditable wickets:", raw_wickets_by_bowler[("63963", sarandeep_ext)])
print("Raw wicket events:")
for e in raw_bowler_events[("63963", sarandeep_ext)]:
    print(" ", e)
if sarandeep_ext in {r["player_external_id"] for r in pm_p_rows if r["match_id"] == "63963"}:
    row = proc_pm[("63963", sarandeep_ext)]
    print("Processed wickets:", si(row["wickets"]))
    result(si(row["wickets"]) == 3,
           "Match 63963 correctly excludes 'handled the ball' from bowler wickets.")
else:
    result(False, "Sarandeep Singh player-match row is missing.")

section("8. CAREER UNIQUENESS")
career_keys = [(r["player_external_id"], r["gender"]) for r in career_p_rows]
career_dupes = [k for k in set(career_keys) if career_keys.count(k) > 1]
blank_career = [r for r in career_p_rows if not r["player_external_id"].strip()]
print("Career rows:", len(career_p_rows))
print("Duplicate (external_id, gender):", len(career_dupes))
print("Blank external IDs:", len(blank_career))
result(not career_dupes and not blank_career,
       "Career rows are unique by external player ID and gender.")

section("9. CAREER RECONCILIATION")
derived = defaultdict(lambda: {
    "matches": set(), "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
    "not_outs": 0, "highest_score": 0, "balls_bowled": 0,
    "runs_conceded": 0, "wickets": 0, "maidens": 0,
    "batting_innings": 0, "bowling_innings": 0
})
for r in pm_p_rows:
    k = (r["player_external_id"], r["gender"])
    d = derived[k]
    d["matches"].add(r["match_id"])
    runs = si(r["batting_runs"])
    balls = si(r["balls_faced"])
    bb = si(r["balls_bowled"])
    rc = si(r["runs_conceded"])
    wk = si(r["wickets"])
    batted = str(r.get("batted", "")).lower() == "true"
    if batted:
        d["batting_innings"] += 1
        d["runs"] += runs
        d["balls"] += balls
        d["fours"] += si(r["fours"])
        d["sixes"] += si(r["sixes"])
        d["highest_score"] = max(d["highest_score"], runs)
        if str(r.get("not_out", "")).lower() == "true":
            d["not_outs"] += 1
    if bb > 0:
        d["bowling_innings"] += 1
    d["balls_bowled"] += bb
    d["runs_conceded"] += rc
    d["wickets"] += wk
    d["maidens"] += si(r["maidens"])

career = {(r["player_external_id"], r["gender"]): r for r in career_p_rows}
career_mismatches = []
for k, p in career.items():
    d = derived[k]
    checks = [
        ("matches", len(d["matches"]), si(p["matches"])),
        ("runs", d["runs"], si(p["runs"])),
        ("balls_faced", d["balls"], si(p["balls_faced"])),
        ("fours", d["fours"], si(p["fours"])),
        ("sixes", d["sixes"], si(p["sixes"])),
        ("not_outs", d["not_outs"], si(p["not_outs"])),
        ("highest_score", d["highest_score"], si(p["highest_score"])),
        ("balls_bowled", d["balls_bowled"], si(p["balls_bowled"])),
        ("runs_conceded", d["runs_conceded"], si(p["runs_conceded"])),
        ("wickets", d["wickets"], si(p["wickets"])),
        ("maidens", d["maidens"], si(p["maidens"])),
        ("batting_innings", d["batting_innings"], si(p["batting_innings"])),
        ("bowling_innings", d["bowling_innings"], si(p["bowling_innings"])),
    ]
    for field, exp, act in checks:
        if exp != act:
            career_mismatches.append((k, field, exp, act, p.get("player_name")))
print("Career mismatches:", len(career_mismatches))
for x in career_mismatches[:80]:
    print(" ", x)
result(not career_mismatches, "Career statistics reconcile from player-match rows.")

section("10. GLOBAL TOTALS")
team_runs = sum(si(r["runs"]) for r in team_p_rows)
team_balls = sum(si(r["total_balls"]) for r in team_p_rows)
team_fours = sum(si(r["fours"]) for r in team_p_rows)
team_sixes = sum(si(r["sixes"]) for r in team_p_rows)
team_wkts = sum(si(r["wickets"]) for r in team_p_rows)

print("Processed team legal balls:", team_balls)
print("Processed team runs:", team_runs)
print("Processed team fours:", team_fours)
print("Processed team sixes:", team_sixes)
print("Processed team wickets:", team_wkts)
result(team_balls == 1752907, "Legal-ball total matches the raw delivery audit.")
result(team_runs == 958105, "Full team-run total includes the 25 innings-level penalty runs.")

section("11. MATCH OUTCOMES")
statuses = defaultdict(int)
for r in matches_p.values():
    statuses[r["match_status"]] += 1
print(dict(statuses))
result(statuses["COMPLETED"] + statuses["DRAW"] == 918,
       "All 918 matches are represented as completed/draw outcomes.")
print("NOTE: the exact status labels above depend on the processor's representation.")

section("12. FINAL VERDICT")
all_core = (
    len(matches_p) == 918
    and len(team_p_rows) == 1836
    and raw_ids == set(matches_p)
    and not missing_team and not extra_team
    and not team_mismatches
    and not pm_dupes and not blank_ext
    and not pm_mismatches
    and not career_dupes and not blank_career
    and not career_mismatches
    and team_balls == 1752907
    and team_runs == 958105
)
if all_core:
    print("[PASS] TEST PROCESSOR PASSES THE CORE FORENSIC AUDIT.")
    print("Safe to proceed to the MySQL importer.")
else:
    print("[FAIL] TEST PROCESSOR IS NOT YET READY FOR MYSQL IMPORT.")
    print("Fix every reported core failure before importing.")
