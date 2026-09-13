"""
CRICKET ANALYTICS
T20I PRE-IMPORT AUDIT V7
======================

READ-ONLY diagnostic.

Purpose:
1. Validate processed T20I match-team balls against raw legal balls.
2. Validate player-match event universe and key statistics.
3. Validate bowler wicket-credit rules, especially "timed out".
4. Reconcile processed player-match rows -> processed career statistics.
5. Compare raw statistical-event aggregates -> processed player-match/career.
6. Detect whether no-ball handling is consistent.

IMPORTANT:
- This script DOES NOT modify CSVs.
- This script DOES NOT modify MySQL.
- It reads the official Cricsheet JSON ZIP and processed T20I CSVs.
"""

import csv
import json
import os
import zipfile
from collections import defaultdict, Counter

BASE_DIR = r"D:\CricketAnalytics\cricket-analytics-data"
ZIP_PATH = os.path.join(
    BASE_DIR, "raw", "international", "t20s_json.zip"
)
PROCESSED_DIR = os.path.join(
    BASE_DIR, "processed", "t20i"
)

FILES = {
    "matches": os.path.join(PROCESSED_DIR, "matches.csv"),
    "match_team_stats": os.path.join(PROCESSED_DIR, "match_team_stats.csv"),
    "player_match_performance": os.path.join(
        PROCESSED_DIR, "player_match_performance.csv"
    ),
    "player_statistics": os.path.join(
        PROCESSED_DIR, "player_statistics.csv"
    ),
}

PASS = 0
WARN = 0
FAIL = 0


def section(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def ok(message):
    global PASS
    PASS += 1
    print("[PASS]", message)


def warn(message):
    global WARN
    WARN += 1
    print("[WARN]", message)


def fail(message):
    global FAIL
    FAIL += 1
    print("[FAIL]", message)


def safe_int(value, default=0):
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return int(float(text))
    except Exception:
        return default


def safe_float(value, default=0.0):
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except Exception:
        return default


def norm(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())


def get_extras(delivery):
    extras = delivery.get("extras", {})
    return extras if isinstance(extras, dict) else {}


def is_wide(delivery):
    return "wides" in get_extras(delivery)


def is_no_ball(delivery):
    return "noballs" in get_extras(delivery)


def is_legal_ball(delivery):
    # T20 cricket: wides and no-balls do not consume a legal ball.
    return not is_wide(delivery) and not is_no_ball(delivery)


def iter_json_files(zf):
    for name in zf.namelist():
        if name.lower().endswith(".json"):
            yield name


def load_csv(name):
    path = FILES[name]
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def innings_is_super_over(innings):
    return bool(innings.get("super_over", False))


# Bowler is credited only with dismissals that are bowler-creditable.
# In particular, timed out is NOT a bowler wicket.
BOWLER_NOT_CREDITED = {
    "run out",
    "retired hurt",
    "retired not out",
    "retired out",
    "obstructing the field",
    "timed out",
}


section("V7 CONFIGURATION")
print("Raw ZIP:")
print(ZIP_PATH)
print("Processed directory:")
print(PROCESSED_DIR)
print()
print("READ-ONLY: no files or database rows will be changed.")


section("LOAD PROCESSED CSVs")

matches = load_csv("matches")
match_team = load_csv("match_team_stats")
player_match = load_csv("player_match_performance")
career = load_csv("player_statistics")

print("matches:", len(matches))
print("match_team_stats:", len(match_team))
print("player_match_performance:", len(player_match))
print("player_statistics:", len(career))


# ---------------------------------------------------------------------------
# Processed indexes
# ---------------------------------------------------------------------------

processed_matches = {
    str(r["match_id"]): r
    for r in matches
}

processed_team = {
    (str(r["match_id"]), norm(r["team_name"])): r
    for r in match_team
}

processed_pm = {
    (str(r["match_id"]), str(r["player_external_id"])): r
    for r in player_match
}

processed_career = {
    (str(r["player_external_id"]), norm(r["gender"])): r
    for r in career
}


# ---------------------------------------------------------------------------
# V7 duplicate-key integrity
# ---------------------------------------------------------------------------

section("V7 DUPLICATE-KEY INTEGRITY")

def duplicate_count(rows, key_fn):
    counts = Counter(key_fn(r) for r in rows)
    return sum(1 for count in counts.values() if count > 1)

dup_matches = duplicate_count(
    matches, lambda r: str(r.get("match_id"))
)
dup_match_team = duplicate_count(
    match_team,
    lambda r: (str(r.get("match_id")), norm(r.get("team_name")))
)
dup_player_match = duplicate_count(
    player_match,
    lambda r: (str(r.get("match_id")), str(r.get("player_external_id")))
)
dup_career = duplicate_count(
    career,
    lambda r: (str(r.get("player_external_id")), norm(r.get("gender")))
)

print("Duplicate match keys:", dup_matches)
print("Duplicate match-team keys:", dup_match_team)
print("Duplicate player-match keys:", dup_player_match)
print("Duplicate career keys:", dup_career)

if not any([dup_matches, dup_match_team, dup_player_match, dup_career]):
    ok("No duplicate analytical keys detected.")
else:
    fail("Duplicate analytical keys detected.")


# ---------------------------------------------------------------------------
# RAW AGGREGATES
# ---------------------------------------------------------------------------

section("RAW DATA FORENSICS")

raw_match_ids = set()
raw_team = {}
raw_pm = {}
raw_event_pm = defaultdict(lambda: {
    "name": "",
    "gender": "",
    "matches": set(),
    "batting_innings": 0,
    "runs": 0,
    "balls_faced": 0,
    "fours": 0,
    "sixes": 0,
    "not_out": 0,
    "batted": False,
    "balls_bowled": 0,
    "runs_conceded": 0,
    "wickets": 0,
    "maidens": 0,
})

raw_legal_by_team = defaultdict(int)
raw_runs_by_team = defaultdict(int)
raw_fours_by_team = defaultdict(int)
raw_sixes_by_team = defaultdict(int)
raw_wickets_by_team = defaultdict(int)

raw_total_deliveries = 0
raw_regulation_deliveries = 0
raw_super_deliveries = 0
raw_regulation_legal = 0
raw_super_legal = 0
raw_regulation_runs = 0
raw_super_runs = 0

raw_timed_out = []
raw_bowler_wicket_events = 0
raw_bowler_creditable_wickets = 0

with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    json_files = list(iter_json_files(zf))

    print("JSON files:", len(json_files))

    for index, filename in enumerate(json_files, start=1):
        try:
            with zf.open(filename) as f:
                data = json.load(f)
        except Exception as exc:
            fail(f"JSON error: {filename}: {exc}")
            continue

        match_id = str(data.get("meta", {}).get("data_version", ""))

        # Cricsheet match ID is the JSON filename stem.
        match_id = os.path.splitext(os.path.basename(filename))[0]

        raw_match_ids.add(match_id)

        info = data.get("info", {})
        gender = str(info.get("gender", "")).lower()

        registry = info.get("registry", {})
        people = registry.get("people", {})
        if not isinstance(people, dict):
            people = {}

        innings_list = data.get("innings", [])
        if not isinstance(innings_list, list):
            innings_list = []

        # Map each raw team to its opponent.
        normalized_teams = []
        for team in info.get("teams", []):
            if team not in normalized_teams:
                normalized_teams.append(team)

        for innings in innings_list:
            if not isinstance(innings, dict):
                continue

            batting_team = str(innings.get("team", "")).strip()
            if not batting_team:
                continue

            super_over = innings_is_super_over(innings)

            bowling_team = ""
            for candidate in normalized_teams:
                if candidate != batting_team:
                    bowling_team = candidate
                    break

            for over in innings.get("overs", []):
                if not isinstance(over, dict):
                    continue

                deliveries = over.get("deliveries", [])
                if not isinstance(deliveries, list):
                    continue

                # Maiden calculation is kept simple and only for a normal
                # six-legal-ball over with one bowler and zero total runs.
                over_runs = 0
                over_legal = 0
                over_bowlers = set()

                for delivery in deliveries:
                    if not isinstance(delivery, dict):
                        continue

                    raw_total_deliveries += 1

                    runs = delivery.get("runs", {})
                    if not isinstance(runs, dict):
                        runs = {}

                    batter_runs = safe_int(runs.get("batter"))
                    total_runs = safe_int(runs.get("total"))

                    extras = get_extras(delivery)
                    legal = is_legal_ball(delivery)

                    if super_over:
                        raw_super_deliveries += 1
                        raw_super_runs += total_runs
                        if legal:
                            raw_super_legal += 1
                    else:
                        raw_regulation_deliveries += 1
                        raw_regulation_runs += total_runs

                        if legal:
                            raw_regulation_legal += 1
                            raw_legal_by_team[(match_id, norm(batting_team))] += 1

                        raw_runs_by_team[(match_id, norm(batting_team))] += total_runs

                        if batter_runs == 4:
                            raw_fours_by_team[(match_id, norm(batting_team))] += 1
                        if batter_runs == 6:
                            raw_sixes_by_team[(match_id, norm(batting_team))] += 1

                    if legal:
                        over_legal += 1

                    over_runs += total_runs

                    bowler = delivery.get("bowler", "")
                    if bowler:
                        over_bowlers.add(bowler)

                    # -------------------------------------------------------
                    # Normal player statistics only
                    # -------------------------------------------------------
                    if super_over:
                        continue

                    batter = delivery.get("batter")
                    if batter:
                        external_id = people.get(batter)
                        if external_id:
                            key = (match_id, str(external_id))

                            row = raw_event_pm[key]
                            row["name"] = str(batter)
                            row["gender"] = gender
                            row["matches"].add(match_id)
                            row["batted"] = True

                            row["runs"] += batter_runs

                            # Wide and no-ball do not consume a ball faced.
                            if legal:
                                row["balls_faced"] += 1

                            if batter_runs == 4:
                                row["fours"] += 1
                            if batter_runs == 6:
                                row["sixes"] += 1

                    bowler = delivery.get("bowler")
                    if bowler:
                        external_id = people.get(bowler)
                        if external_id:
                            key = (match_id, str(external_id))

                            row = raw_event_pm[key]
                            row["name"] = str(bowler)
                            row["gender"] = gender
                            row["matches"].add(match_id)

                            # A no-ball and a wide do not consume a legal
                            # bowling ball.
                            if legal:
                                row["balls_bowled"] += 1

                            # Bowler-conceded runs exclude byes and leg-byes.
                            bowler_runs = batter_runs
                            bowler_runs += safe_int(
                                extras.get("wides")
                            )
                            bowler_runs += safe_int(
                                extras.get("noballs")
                            )
                            row["runs_conceded"] += bowler_runs

                    # Wickets
                    for wicket in delivery.get("wickets", []) or []:
                        if not isinstance(wicket, dict):
                            continue

                        kind = norm(wicket.get("kind"))
                        player_out = wicket.get("player_out")

                        if player_out:
                            out_id = people.get(player_out)
                            if out_id:
                                key = (match_id, str(out_id))
                                raw_event_pm[key]["name"] = str(player_out)
                                raw_event_pm[key]["gender"] = gender
                                raw_event_pm[key]["matches"].add(match_id)

                        if bowler:
                            raw_bowler_wicket_events += 1

                            if kind not in BOWLER_NOT_CREDITED:
                                raw_bowler_creditable_wickets += 1

                                bowler_id = people.get(bowler)
                                if bowler_id:
                                    key = (match_id, str(bowler_id))
                                    raw_event_pm[key]["wickets"] += 1

                        # Team wicket: all genuine dismissals except retirements.
                        if kind not in {"retired hurt", "retired not out"}:
                            raw_wickets_by_team[
                                (match_id, norm(batting_team))
                            ] += 1

                        if kind == "timed out":
                            raw_timed_out.append(
                                (match_id, batting_team, player_out, bowler)
                            )

                # Maiden
                if (
                    not super_over
                    and over_runs == 0
                    and over_legal >= 6
                    and len(over_bowlers) == 1
                ):
                    bowler = next(iter(over_bowlers))
                    external_id = people.get(bowler)
                    if external_id:
                        key = (match_id, str(external_id))
                        raw_event_pm[key]["maidens"] += 1


print("Raw matches:", len(raw_match_ids))
print("Raw statistical player-match events:", len(raw_event_pm))
print("Raw timed-out dismissals:", len(raw_timed_out))
print("Raw bowler wicket events:", raw_bowler_wicket_events)
print("Raw creditable bowler wickets:", raw_bowler_creditable_wickets)
print("Raw regulation deliveries:", raw_regulation_deliveries)
print("Raw regulation legal balls:", raw_regulation_legal)
print("Raw regulation runs:", raw_regulation_runs)
print("Raw Super Over deliveries:", raw_super_deliveries)
print("Raw Super Over legal balls:", raw_super_legal)
print("Raw Super Over runs:", raw_super_runs)


# ---------------------------------------------------------------------------
# 1. Match universe
# ---------------------------------------------------------------------------

section("1. MATCH UNIVERSE")

missing_matches = raw_match_ids - set(processed_matches)
extra_matches = set(processed_matches) - raw_match_ids

print("Raw matches:", len(raw_match_ids))
print("Processed matches:", len(processed_matches))
print("Missing:", len(missing_matches))
print("Extra:", len(extra_matches))

if not missing_matches and not extra_matches:
    ok("Raw and processed match IDs are identical.")
else:
    fail("Raw and processed match ID sets differ.")
    print("Missing examples:", sorted(missing_matches)[:20])
    print("Extra examples:", sorted(extra_matches)[:20])


# ---------------------------------------------------------------------------
# 2. Match-team RAW -> PROCESSED RECONCILIATION
# ---------------------------------------------------------------------------

section("2. MATCH-TEAM RAW -> PROCESSED RECONCILIATION")

team_mismatches = []

for key, row in processed_team.items():
    mid, team = key

    expected = {
        "total_balls": raw_legal_by_team.get(key, 0),
        "runs": raw_runs_by_team.get(key, 0),
        "fours": raw_fours_by_team.get(key, 0),
        "sixes": raw_sixes_by_team.get(key, 0),
        "wickets": raw_wickets_by_team.get(key, 0),
    }

    actual = {
        "total_balls": safe_int(row.get("total_balls")),
        "runs": safe_int(row.get("runs")),
        "fours": safe_int(row.get("fours")),
        "sixes": safe_int(row.get("sixes")),
        "wickets": safe_int(row.get("wickets")),
    }

    for field in expected:
        if expected[field] != actual[field]:
            team_mismatches.append(
                (
                    mid,
                    team,
                    field,
                    expected[field],
                    actual[field],
                )
            )

processed_team_keys = set(processed_team)
raw_team_keys = set(raw_legal_by_team) | set(raw_runs_by_team)

missing_team_keys = raw_team_keys - processed_team_keys
extra_team_keys = processed_team_keys - raw_team_keys

print("Raw match-team keys:", len(raw_team_keys))
print("Processed match-team keys:", len(processed_team_keys))
print("Missing match-team keys:", len(missing_team_keys))
print("Extra match-team keys:", len(extra_team_keys))
print("Raw-vs-processed field mismatches:", len(team_mismatches))

if not missing_team_keys and not extra_team_keys and not team_mismatches:
    ok(
        "Raw regulation team statistics reconcile exactly with "
        "processed match-team statistics."
    )
else:
    fail("Raw and processed match-team statistics differ.")
    if missing_team_keys:
        print("Missing examples:", list(missing_team_keys)[:20])
    if extra_team_keys:
        print("Extra examples:", list(extra_team_keys)[:20])
    for item in team_mismatches[:50]:
        print(" ", item)


# ---------------------------------------------------------------------------
# 2B. TEAM RUN TOTAL / PLAYER RUN TOTAL RECONCILIATION
# ---------------------------------------------------------------------------

section("2B. TEAM / PLAYER RUN TOTAL RECONCILIATION")

processed_team_runs = sum(
    safe_int(row.get("runs")) for row in match_team
)

processed_player_runs = sum(
    safe_int(row.get("batting_runs")) for row in player_match
)

if processed_team_runs == raw_regulation_runs:
    ok(
        f"Processed team runs equal raw regulation runs: "
        f"{processed_team_runs}"
    )
else:
    fail(
        f"Processed team runs {processed_team_runs} != "
        f"raw regulation runs {raw_regulation_runs}."
    )

print("Processed team runs:", processed_team_runs)
print("Processed player batting runs:", processed_player_runs)
print(
    "Processed team runs minus player batting runs:",
    processed_team_runs - processed_player_runs,
)

# ---------------------------------------------------------------------------
# 3. Player-match event universe
# ---------------------------------------------------------------------------

section("3. PLAYER-MATCH STATISTICAL EVENT UNIVERSE")

raw_pm_keys = set(raw_event_pm)
proc_pm_keys = set(processed_pm)

missing_pm = raw_pm_keys - proc_pm_keys
extra_pm = proc_pm_keys - raw_pm_keys

print("Raw event keys:", len(raw_pm_keys))
print("Processed keys:", len(proc_pm_keys))
print("Missing:", len(missing_pm))
print("Extra:", len(extra_pm))

# A raw player-match key can exist only because of a wicket event
# even when that player has zero batting and bowling statistics.
# The processor intentionally does not create zero-stat rows for such
# metadata-only wicket events. Therefore classify missing keys by
# their actual raw statistical values before deciding PASS/FAIL.

zero_stat_missing = []
nonzero_stat_missing = []

for key in missing_pm:
    raw = raw_event_pm[key]

    has_statistics = any([
        raw["runs"] != 0,
        raw["balls_faced"] != 0,
        raw["fours"] != 0,
        raw["sixes"] != 0,
        raw["balls_bowled"] != 0,
        raw["runs_conceded"] != 0,
        raw["wickets"] != 0,
        raw["maidens"] != 0,
    ])

    if has_statistics:
        nonzero_stat_missing.append(key)
    else:
        zero_stat_missing.append(key)

print("Zero-stat missing events:", len(zero_stat_missing))
print("Non-zero-stat missing events:", len(nonzero_stat_missing))

if not extra_pm and not nonzero_stat_missing:
    ok(
        "All non-zero-stat raw player-match events are represented. "
        "Zero-stat metadata-only wicket events are intentionally omitted."
    )
else:
    fail("Player-match statistical event universes differ.")
    if nonzero_stat_missing:
        print(
            "Non-zero-stat missing examples:",
            nonzero_stat_missing[:20]
        )
    if extra_pm:
        print("Extra examples:", list(extra_pm)[:20])


# ---------------------------------------------------------------------------
# 4. Player-match fields
# ---------------------------------------------------------------------------

section("4. PLAYER-MATCH FIELD RECONCILIATION")

pm_mismatches = []

for key in raw_pm_keys & proc_pm_keys:
    raw = raw_event_pm[key]
    proc = processed_pm[key]

    checks = [
        ("runs", raw["runs"], safe_int(proc.get("batting_runs"))),
        (
            "balls_faced",
            raw["balls_faced"],
            safe_int(proc.get("balls_faced")),
        ),
        ("fours", raw["fours"], safe_int(proc.get("fours"))),
        ("sixes", raw["sixes"], safe_int(proc.get("sixes"))),
        (
            "balls_bowled",
            raw["balls_bowled"],
            safe_int(proc.get("balls_bowled")),
        ),
        (
            "runs_conceded",
            raw["runs_conceded"],
            safe_int(proc.get("runs_conceded")),
        ),
        ("wickets", raw["wickets"], safe_int(proc.get("wickets"))),
        ("maidens", raw["maidens"], safe_int(proc.get("maidens"))),
    ]

    for field, expected, actual in checks:
        if expected != actual:
            pm_mismatches.append(
                (
                    key[0],
                    key[1],
                    field,
                    expected,
                    actual,
                    raw["name"],
                )
            )

print("Field mismatches:", len(pm_mismatches))

if not pm_mismatches:
    ok("All audited player-match numeric fields reconcile.")
else:
    fail(
        f"{len(pm_mismatches)} player-match field mismatches."
    )
    for item in pm_mismatches[:50]:
        print(" ", item)


# ---------------------------------------------------------------------------
# 5. Timed-out wicket forensic
# ---------------------------------------------------------------------------

section("5. TIMED-OUT WICKET FORENSIC")

print("Timed-out dismissals:", len(raw_timed_out))

for item in raw_timed_out[:30]:
    print(" ", item)

timed_out_bowler_credited = [
    x for x in pm_mismatches
    if x[2] == "wickets"
]

# We do not infer correctness merely from mismatch count; print the exact
# target if present.
target = [
    x for x in pm_mismatches
    if x[0] == "1536623"
    and "K Kunwar" in x[5]
    and x[2] == "wickets"
]

if not target:
    ok(
        "No remaining K Kunwar timed-out wicket mismatch exists."
    )
else:
    fail(
        "K Kunwar timed-out wicket is still being counted differently."
    )
    for item in target:
        print(" ", item)


# ---------------------------------------------------------------------------
# 6. Processed player-match -> career reconciliation
# ---------------------------------------------------------------------------

section("6. PROCESSED PLAYER-MATCH -> CAREER RECONCILIATION")

derived_career = defaultdict(lambda: {
    "matches": set(),
    "batting_innings": 0,
    "runs": 0,
    "balls_faced": 0,
    "highest_score": 0,
    "not_outs": 0,
    "fours": 0,
    "sixes": 0,
    "fifties": 0,
    "centuries": 0,
    "bowling_innings": 0,
    "balls_bowled": 0,
    "wickets": 0,
    "runs_conceded": 0,
    "best_bowling_wickets": 0,
    "five_wicket_hauls": 0,
})

for (mid, eid), row in processed_pm.items():
    gender = norm(row.get("gender"))
    key = (eid, gender)

    d = derived_career[key]
    d["matches"].add(mid)

    batted = str(row.get("batted", "")).lower() in {
        "true", "1", "yes", "y"
    }

    if batted:
        d["batting_innings"] += 1

    runs = safe_int(row.get("batting_runs"))
    balls = safe_int(row.get("balls_faced"))
    wickets = safe_int(row.get("wickets"))
    balls_bowled = safe_int(row.get("balls_bowled"))
    runs_conceded = safe_int(row.get("runs_conceded"))

    d["runs"] += runs
    d["balls_faced"] += balls
    d["highest_score"] = max(d["highest_score"], runs)
    d["fours"] += safe_int(row.get("fours"))
    d["sixes"] += safe_int(row.get("sixes"))

    not_out = str(row.get("not_out", "")).lower() in {
        "true", "1", "yes", "y"
    }
    if batted and not_out:
        d["not_outs"] += 1

    if batted and runs >= 100:
        d["centuries"] += 1
    elif batted and runs >= 50:
        d["fifties"] += 1

    # This deliberately mirrors the processor's current semantics:
    # bowling_innings is incremented only when balls_bowled > 0.
    if balls_bowled > 0:
        d["bowling_innings"] += 1
        d["balls_bowled"] += balls_bowled
        d["wickets"] += wickets
        d["runs_conceded"] += runs_conceded
        d["best_bowling_wickets"] = max(
            d["best_bowling_wickets"], wickets
        )
        if wickets >= 5:
            d["five_wicket_hauls"] += 1

career_from_pm_mismatches = []

for key, proc in processed_career.items():
    d = derived_career.get(key)

    if d is None:
        career_from_pm_mismatches.append(
            (key, "missing_derived_row", None, proc.get("player_name"))
        )
        continue

    checks = [
        ("matches", len(d["matches"]), safe_int(proc.get("matches"))),
        (
            "batting_innings",
            d["batting_innings"],
            safe_int(proc.get("batting_innings")),
        ),
        ("runs", d["runs"], safe_int(proc.get("runs"))),
        (
            "balls_faced",
            d["balls_faced"],
            safe_int(proc.get("balls_faced")),
        ),
        (
            "highest_score",
            d["highest_score"],
            safe_int(proc.get("highest_score")),
        ),
        ("not_outs", d["not_outs"], safe_int(proc.get("not_outs"))),
        ("fours", d["fours"], safe_int(proc.get("fours"))),
        ("sixes", d["sixes"], safe_int(proc.get("sixes"))),
        ("fifties", d["fifties"], safe_int(proc.get("fifties"))),
        (
            "centuries",
            d["centuries"],
            safe_int(proc.get("centuries")),
        ),
        (
            "bowling_innings",
            d["bowling_innings"],
            safe_int(proc.get("bowling_innings")),
        ),
        (
            "balls_bowled",
            d["balls_bowled"],
            safe_int(proc.get("balls_bowled")),
        ),
        ("wickets", d["wickets"], safe_int(proc.get("wickets"))),
        (
            "runs_conceded",
            d["runs_conceded"],
            safe_int(proc.get("runs_conceded")),
        ),
        (
            "best_bowling_wickets",
            d["best_bowling_wickets"],
            safe_int(proc.get("best_bowling_wickets")),
        ),
        (
            "five_wicket_hauls",
            d["five_wicket_hauls"],
            safe_int(proc.get("five_wicket_hauls")),
        ),
    ]

    for field, expected, actual in checks:
        if expected != actual:
            career_from_pm_mismatches.append(
                (
                    key[0],
                    field,
                    expected,
                    actual,
                    proc.get("player_name"),
                )
            )

print(
    "Career rows whose values differ from their own "
    "processed player-match rows:",
    len(career_from_pm_mismatches),
)

if not career_from_pm_mismatches:
    ok(
        "Processed career statistics reconcile exactly "
        "from processed player-match rows."
    )
else:
    fail(
        f"{len(career_from_pm_mismatches)} career fields do not "
        "reconcile from processed player-match rows."
    )
    for item in career_from_pm_mismatches[:80]:
        print(" ", item)


# ---------------------------------------------------------------------------
# 7. Target career diagnostics
# ---------------------------------------------------------------------------

section("7. TARGET CAREER DIAGNOSTICS")

TARGET_NAMES = {
    "K Kunwar",
    "N Magagula",
    "Dilum Fernando",
    "S Ravikumar",
    "Hassan Nawaz",
}

for key, row in processed_career.items():
    if str(row.get("player_name", "")).strip() in TARGET_NAMES:
        d = derived_career.get(key, {})
        print()
        print("Player:", row.get("player_name"))
        print("External ID:", key[0])
        print("Gender:", key[1])
        print(
            "Career CSV:",
            "matches=", safe_int(row.get("matches")),
            "runs=", safe_int(row.get("runs")),
            "balls=", safe_int(row.get("balls_faced")),
            "balls_bowled=", safe_int(row.get("balls_bowled")),
            "runs_conceded=", safe_int(row.get("runs_conceded")),
            "wickets=", safe_int(row.get("wickets")),
        )
        print(
            "From PM:",
            "matches=", len(d.get("matches", set())),
            "runs=", d.get("runs", 0),
            "balls=", d.get("balls_faced", 0),
            "balls_bowled=", d.get("balls_bowled", 0),
            "runs_conceded=", d.get("runs_conceded", 0),
            "wickets=", d.get("wickets", 0),
        )


# ---------------------------------------------------------------------------
# 8. No-ball consistency diagnostic
# ---------------------------------------------------------------------------

section("8. NO-BALL HANDLING")

print(
    "Audit rule: legal ball = not wide AND not no-ball."
)
print(
    "Processed source must therefore exclude no-balls from "
    "balls faced, balls bowled, and team legal-ball totals."
)

# Count no-ball records in raw data for visibility.
raw_no_ball_deliveries = 0
raw_wide_deliveries = 0

with zipfile.ZipFile(ZIP_PATH, "r") as zf:
    for filename in iter_json_files(zf):
        with zf.open(filename) as f:
            data = json.load(f)

        for innings in data.get("innings", []) or []:
            if innings_is_super_over(innings):
                continue

            for over in innings.get("overs", []) or []:
                for delivery in over.get("deliveries", []) or []:
                    extras = get_extras(delivery)
                    if "noballs" in extras:
                        raw_no_ball_deliveries += 1
                    if "wides" in extras:
                        raw_wide_deliveries += 1

print("Raw no-ball deliveries:", raw_no_ball_deliveries)
print("Raw wide deliveries:", raw_wide_deliveries)

if raw_no_ball_deliveries > 0:
    warn(
        "The raw dataset contains no-balls. The processor must be "
        "verified to exclude them from legal-ball counts."
    )
else:
    ok("No no-ball deliveries found.")


# ---------------------------------------------------------------------------
# V7 GLOBAL RAW / PROCESSED SANITY CHECKS
# ---------------------------------------------------------------------------

section("V7 GLOBAL SANITY CHECKS")

print("Raw regulation legal balls:", raw_regulation_legal)
print(
    "Processed match-team legal balls:",
    sum(safe_int(r.get("total_balls")) for r in match_team),
)
print("Raw regulation runs:", raw_regulation_runs)
print(
    "Processed match-team runs:",
    sum(safe_int(r.get("runs")) for r in match_team),
)
print("Raw regulation fours:", sum(raw_fours_by_team.values()))
print("Processed fours:", sum(safe_int(r.get("fours")) for r in match_team))
print("Raw regulation sixes:", sum(raw_sixes_by_team.values()))
print("Processed sixes:", sum(safe_int(r.get("sixes")) for r in match_team))
print("Raw regulation wickets:", sum(raw_wickets_by_team.values()))
print("Processed wickets:", sum(safe_int(r.get("wickets")) for r in match_team))

global_checks = [
    (
        "legal balls",
        raw_regulation_legal,
        sum(safe_int(r.get("total_balls")) for r in match_team),
    ),
    (
        "runs",
        raw_regulation_runs,
        sum(safe_int(r.get("runs")) for r in match_team),
    ),
    (
        "fours",
        sum(raw_fours_by_team.values()),
        sum(safe_int(r.get("fours")) for r in match_team),
    ),
    (
        "sixes",
        sum(raw_sixes_by_team.values()),
        sum(safe_int(r.get("sixes")) for r in match_team),
    ),
    (
        "wickets",
        sum(raw_wickets_by_team.values()),
        sum(safe_int(r.get("wickets")) for r in match_team),
    ),
]

global_mismatches = [x for x in global_checks if x[1] != x[2]]

if not global_mismatches:
    ok("All global raw regulation team totals reconcile.")
else:
    fail("Global raw regulation team totals do not reconcile.")
    for item in global_mismatches:
        print(" ", item)


# ---------------------------------------------------------------------------
# V7 SUPER OVER EXCLUSION
# ---------------------------------------------------------------------------

section("V7 SUPER OVER EXCLUSION")

print("Raw Super Over deliveries:", raw_super_deliveries)
print("Raw Super Over legal balls:", raw_super_legal)
print("Raw Super Over runs:", raw_super_runs)

processed_team_balls = sum(
    safe_int(r.get("total_balls")) for r in match_team
)
processed_team_runs_total = sum(
    safe_int(r.get("runs")) for r in match_team
)

if (
    processed_team_balls == raw_regulation_legal
    and processed_team_runs_total == raw_regulation_runs
):
    ok(
        "Processed normal statistics exclude Super Over balls/runs; "
        "they reconcile to regulation-only raw totals."
    )
else:
    fail(
        "Processed team totals do not match regulation-only raw totals; "
        "Super Over exclusion requires investigation."
    )


# ---------------------------------------------------------------------------
# V7 NO-BALL / WIDE LEGAL-BALL QUANTITATIVE CHECK
# ---------------------------------------------------------------------------

section("V7 NO-BALL / WIDE QUANTITATIVE CHECK")

raw_non_legal = (
    raw_regulation_deliveries - raw_regulation_legal
)

print("Raw regulation deliveries:", raw_regulation_deliveries)
print("Raw regulation legal balls:", raw_regulation_legal)
print("Raw regulation non-legal deliveries:", raw_non_legal)
print("Raw no-ball deliveries:", raw_no_ball_deliveries)
print("Raw wide deliveries:", raw_wide_deliveries)

if raw_non_legal == raw_no_ball_deliveries + raw_wide_deliveries:
    ok(
        "Raw non-legal delivery count equals "
        "no-balls + wides."
    )
else:
    warn(
        "No-ball + wide count does not equal all non-legal deliveries; "
        "some deliveries may contain multiple extra categories."
    )

# ---------------------------------------------------------------------------
# 9. Final interpretation
# ---------------------------------------------------------------------------

section("V7 FINAL RESULT")

print("PASS:", PASS)
print("WARN:", WARN)
print("FAIL:", FAIL)
print()

if FAIL == 0:
    print("T20I PRE-IMPORT AUDIT V7: PASS")
    print()
    print(
        "The processed player-match and career statistics are internally "
        "consistent for the checks performed."
    )
else:
    print("T20I PRE-IMPORT AUDIT V7: FAIL")
    print()
    print(
        "Do NOT run the full T20I MySQL import yet."
    )
    print(
        "Use the listed mismatches to make the next targeted processor fix."
    )

print()
print("IMPORTANT:")
print(
    "The 41 innings containing 121/122 legal balls are not automatically "
    "processor errors. V5 showed these are genuine raw delivery structures, "
    "including overs containing 7 legal deliveries."
)
