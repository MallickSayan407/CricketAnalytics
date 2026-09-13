import csv
import json
import os
import zipfile
from collections import defaultdict, Counter

# =============================================================================
# CONFIGURATION
# =============================================================================

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
PROCESSED_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"

MATCHES_CSV = os.path.join(PROCESSED_DIR, "matches.csv")
MATCH_TEAM_STATS_CSV = os.path.join(PROCESSED_DIR, "match_team_stats.csv")
PLAYER_MATCH_CSV = os.path.join(PROCESSED_DIR, "player_match_performance.csv")
PLAYER_STATS_CSV = os.path.join(PROCESSED_DIR, "player_statistics.csv")
TEAMS_CSV = os.path.join(PROCESSED_DIR, "teams.csv")

NOMINAL_OVERS = 20
TOLERANCE = 0.02

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

PASS_COUNT = 0
WARN_COUNT = 0
FAIL_COUNT = 0


def section(title):
    print("\n" + "=" * 95)
    print(title)
    print("=" * 95)


def pass_msg(message):
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"[PASS] {message}")


def warn_msg(message):
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"[WARN] {message}")


def fail_msg(message):
    global FAIL_COUNT
    FAIL_COUNT += 1
    print(f"[FAIL] {message}")


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_team(name):
    name = "" if name is None else str(name).strip()
    return TEAM_NORMALIZATION.get(name, name)


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def extras_of(delivery):
    value = delivery.get("extras", {})
    return value if isinstance(value, dict) else {}


def wickets_of(delivery):
    value = delivery.get("wickets", [])
    return value if isinstance(value, list) else []


def is_super_over(innings):
    value = innings.get("super_over", False)
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


def iter_deliveries(innings):
    for over in innings.get("overs", []) or []:
        if not isinstance(over, dict):
            continue
        for delivery in over.get("deliveries", []) or []:
            if isinstance(delivery, dict):
                yield delivery


def legal_ball(delivery):
    extras = extras_of(delivery)
    return "wides" not in extras and "noballs" not in extras


def wicket_counts_as_dismissal(wicket):
    kind = str(wicket.get("kind", "")).lower()
    return kind not in {"retired hurt", "retired not out"}


def wicket_counts_for_bowler(wicket):
    kind = str(wicket.get("kind", "")).lower()
    return kind not in {
        "retired hurt",
        "retired not out",
        "retired out",
        "obstructing the field",
    }


def innings_quota_balls(info, innings):
    """
    Best-effort quota inference.

    Priority:
      1. innings target.overs (when present)
      2. match-level info.overs
      3. nominal T20 quota (20 overs)

    This is used only for allocated-ball auditing.
    """
    target = innings.get("target")
    if isinstance(target, dict) and target.get("overs") is not None:
        overs = safe_float(target.get("overs"), NOMINAL_OVERS)
        return max(1, round(overs * 6)), "innings.target.overs"

    match_overs = info.get("overs")
    if match_overs is not None:
        overs = safe_float(match_overs, NOMINAL_OVERS)
        return max(1, round(overs * 6)), "info.overs"

    return NOMINAL_OVERS * 6, "nominal_20_overs"


def result_type(info):
    outcome = info.get("outcome", {})
    if not isinstance(outcome, dict):
        return "UNKNOWN"

    result = str(outcome.get("result", "")).strip().lower()

    if result == "no result":
        return "NO_RESULT"
    if result == "tie":
        return "TIED"
    if result == "draw":
        return "DRAW"
    if outcome.get("winner"):
        return "WINNER"

    # Some one-innings/abandoned records can have winner metadata without
    # a normal innings structure; winner is therefore a valid fallback.
    return "UNKNOWN"


def build_processed_maps():
    matches = load_csv(MATCHES_CSV)
    match_team = load_csv(MATCH_TEAM_STATS_CSV)
    player_match = load_csv(PLAYER_MATCH_CSV)
    player_stats = load_csv(PLAYER_STATS_CSV)
    teams = load_csv(TEAMS_CSV)

    pm = {
        (r["match_id"], r.get("player_external_id", "").strip()): r
        for r in player_match
    }

    career = {
        r.get("player_external_id", "").strip(): r
        for r in player_stats
        if r.get("player_external_id", "").strip()
    }

    mt = {
        (r["match_id"], normalize_team(r["team_name"])): r
        for r in match_team
    }

    return matches, match_team, player_match, player_stats, teams, pm, career, mt


# =============================================================================
# START
# =============================================================================

print("=" * 95)
print("T20I DEEP DATASET AUDIT V2 - FINAL PRE-IMPORT GATE")
print("=" * 95)
print("READ-ONLY AUDIT")
print("No files or database records will be modified.")

# =============================================================================
# FILES
# =============================================================================

section("FILE CHECK")

for path in [
    RAW_ZIP,
    MATCHES_CSV,
    MATCH_TEAM_STATS_CSV,
    PLAYER_MATCH_CSV,
    PLAYER_STATS_CSV,
    TEAMS_CSV,
]:
    if os.path.exists(path):
        pass_msg(f"Exists: {path}")
    else:
        fail_msg(f"Missing: {path}")

if FAIL_COUNT:
    raise SystemExit(1)

# =============================================================================
# PROCESSED DATA
# =============================================================================

section("LOAD PROCESSED CSV DATA")

(
    matches,
    match_team_stats,
    player_match,
    player_stats,
    teams,
    processed_player_match,
    processed_career,
    processed_match_team,
) = build_processed_maps()

print(f"Processed matches:                 {len(matches):,}")
print(f"Processed match-team rows:         {len(match_team_stats):,}")
print(f"Processed player-match rows:       {len(player_match):,}")
print(f"Processed career rows:              {len(player_stats):,}")
print(f"Processed teams:                    {len(teams):,}")

if len(matches) == 5700:
    pass_msg("Processed matches = 5,700")
else:
    fail_msg(f"Expected 5,700 processed matches, found {len(matches):,}")

if len(match_team_stats) == 11400:
    pass_msg("Processed match-team rows = 11,400")
else:
    fail_msg(f"Expected 11,400 match-team rows, found {len(match_team_stats):,}")

# =============================================================================
# RAW + PROCESSED ACCUMULATORS
# =============================================================================

raw_match_ids = set()
raw_match_team = {}
raw_player_match = defaultdict(lambda: {
    "runs": 0,
    "balls_faced": 0,
    "fours": 0,
    "sixes": 0,
    "balls_bowled": 0,
    "runs_conceded": 0,
    "wickets": 0,
})
raw_career = defaultdict(lambda: {
    "matches": set(),
    "runs": 0,
    "balls_faced": 0,
    "fours": 0,
    "sixes": 0,
    "balls_bowled": 0,
    "runs_conceded": 0,
    "wickets": 0,
})

raw_registry_name_to_id = {}
raw_registry_ids = set()

raw_regulation_runs = 0
raw_regulation_batter_runs = 0
raw_regulation_extras = 0
raw_legal_balls = 0
raw_wickets = 0
raw_fours = 0
raw_sixes = 0
raw_super_over_deliveries = 0
raw_super_over_runs = 0

raw_all_out = []
raw_shortened = []
allocated_audit = []

raw_result_counts = Counter()
raw_no_results = set()
raw_ties = set()
raw_super_over_matches = set()

player_name_aliases = defaultdict(set)

# =============================================================================
# RAW ZIP SCAN
# =============================================================================

section("RAW ZIP SCAN + BALL-BY-BALL RECONCILIATION")

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    json_files = [
        n for n in z.namelist()
        if n.lower().endswith(".json") and not n.endswith("/")
    ]

    print(f"JSON files: {len(json_files):,}")

    if len(json_files) == 5700:
        pass_msg("Raw JSON file count = 5,700")
    else:
        fail_msg(f"Expected 5,700 JSON files, found {len(json_files):,}")

    for filename in json_files:
        with z.open(filename) as f:
            data = json.load(f)

        info = data.get("info", {})
        match_id = os.path.splitext(os.path.basename(filename))[0]
        raw_match_ids.add(match_id)

        gender = str(info.get("gender", "")).strip().lower()

        # Registry: name -> stable Cricsheet ID
        registry = info.get("registry", {})
        people = registry.get("people", {}) if isinstance(registry, dict) else {}
        if isinstance(people, dict):
            for name, external_id in people.items():
                name = str(name).strip()
                external_id = str(external_id).strip()
                if name and external_id:
                    raw_registry_name_to_id[name] = external_id
                    raw_registry_ids.add(external_id)

        outcome_kind = result_type(info)
        raw_result_counts[outcome_kind] += 1
        if outcome_kind == "NO_RESULT":
            raw_no_results.add(match_id)
        elif outcome_kind == "TIED":
            raw_ties.add(match_id)

        teams_in_match = [
            normalize_team(x)
            for x in (info.get("teams", []) or [])
        ]

        # Non-Super-Over team stats for this match.
        match_team_acc = defaultdict(lambda: {
            "runs": 0,
            "extras": 0,
            "legal_balls": 0,
            "fours": 0,
            "sixes": 0,
            "wickets": 0,
        })

        innings_seen = defaultdict(list)

        for innings in data.get("innings", []) or []:
            if not isinstance(innings, dict):
                continue

            team = normalize_team(innings.get("team", ""))
            super_over = is_super_over(innings)
            deliveries = list(iter_deliveries(innings))

            if super_over:
                raw_super_over_matches.add(match_id)
                raw_super_over_deliveries += len(deliveries)
                for d in deliveries:
                    runs = d.get("runs", {})
                    raw_super_over_runs += safe_int(
                        runs.get("batter", 0)
                    ) + safe_int(runs.get("extras", 0))
                continue

            # ---------------------------------------------------------------
            # Innings completion / allocation
            # ---------------------------------------------------------------

            dismissed = set()
            for d in deliveries:
                for wicket in wickets_of(d):
                    if not isinstance(wicket, dict):
                        continue
                    if wicket_counts_as_dismissal(wicket):
                        player_out = wicket.get("player_out")
                        if player_out:
                            dismissed.add(str(player_out).strip())

            all_out = len(dismissed) >= 10

            legal = sum(1 for d in deliveries if legal_ball(d))
            quota_balls, quota_source = innings_quota_balls(info, innings)

            # A team reaching its target early should use actual balls, not
            # the nominal quota. For an all-out innings, NRR convention uses
            # the full applicable quota.
            if all_out:
                allocated = quota_balls
                reason = "ALL_OUT"
            else:
                allocated = legal
                reason = "ACTUAL_BALLS"

            innings_seen[team].append({
                "legal_balls": legal,
                "allocated_balls": allocated,
                "all_out": all_out,
                "dismissed": len(dismissed),
                "quota_balls": quota_balls,
                "quota_source": quota_source,
                "deliveries": len(deliveries),
            })

            if all_out:
                raw_all_out.append(
                    (match_id, team, legal, allocated, quota_source)
                )

            # Flag likely shortened innings. This is informational unless the
            # processor's allocation disagrees with the explicit quota.
            if legal < quota_balls and not all_out:
                raw_shortened.append(
                    (match_id, team, legal, quota_balls, quota_source)
                )

            # ---------------------------------------------------------------
            # Regulation deliveries
            # ---------------------------------------------------------------

            for d in deliveries:
                runs = d.get("runs", {})
                batter = str(d.get("batter", "")).strip()
                bowler = str(d.get("bowler", "")).strip()
                batter_runs = safe_int(runs.get("batter", 0))
                extra_runs = safe_int(runs.get("extras", 0))
                total_runs = batter_runs + extra_runs

                extras = extras_of(d)
                is_legal = legal_ball(d)

                raw_regulation_runs += total_runs
                raw_regulation_batter_runs += batter_runs
                raw_regulation_extras += extra_runs

                if is_legal:
                    raw_legal_balls += 1

                if batter_runs == 4:
                    raw_fours += 1
                if batter_runs == 6:
                    raw_sixes += 1

                for wicket in wickets_of(d):
                    if not isinstance(wicket, dict):
                        continue

                    if wicket_counts_as_dismissal(wicket):
                        raw_wickets += 1
                        match_team_acc[team]["wickets"] += 1

                s = match_team_acc[team]
                s["runs"] += total_runs
                s["extras"] += extra_runs
                if is_legal:
                    s["legal_balls"] += 1
                if batter_runs == 4:
                    s["fours"] += 1
                if batter_runs == 6:
                    s["sixes"] += 1

                # Player identity MUST use registry ID, not display name.
                batter_id = raw_registry_name_to_id.get(batter)
                bowler_id = raw_registry_name_to_id.get(bowler)

                if batter_id:
                    key = (match_id, batter_id)
                    p = raw_player_match[key]
                    p["runs"] += batter_runs
                    if is_legal:
                        p["balls_faced"] += 1
                    if batter_runs == 4:
                        p["fours"] += 1
                    if batter_runs == 6:
                        p["sixes"] += 1
                    player_name_aliases[batter_id].add(batter)

                if bowler_id:
                    key = (match_id, bowler_id)
                    p = raw_player_match[key]

                    # Only runs charged to the bowler:
                    # batter runs + wides + no-balls.
                    p["runs_conceded"] += (
                        batter_runs
                        + safe_int(extras.get("wides", 0))
                        + safe_int(extras.get("noballs", 0))
                    )

                    if is_legal:
                        p["balls_bowled"] += 1

                    for wicket in wickets_of(d):
                        if isinstance(wicket, dict) and wicket_counts_for_bowler(wicket):
                            p["wickets"] += 1

                    player_name_aliases[bowler_id].add(bowler)

        for team in teams_in_match:
            s = match_team_acc[team]
            raw_match_team[(match_id, team)] = s

        # Store allocation expectations per match/team.
        for team, entries in innings_seen.items():
            # Normally one regulation innings per team in T20I.
            # If an unusual duplicate exists, sum the individual innings.
            legal_sum = sum(x["legal_balls"] for x in entries)
            allocated_sum = sum(x["allocated_balls"] for x in entries)
            all_out_count = sum(1 for x in entries if x["all_out"])
            raw_allocation = (legal_sum, allocated_sum, all_out_count)

            allocated_audit.append(
                (match_id, team, raw_allocation)
            )

# =============================================================================
# RAW BASELINES
# =============================================================================

section("RAW BASELINES")

print(f"Raw matches:                       {len(raw_match_ids):,}")
print(f"Raw registry player IDs:           {len(raw_registry_ids):,}")
print(f"Raw regulation runs:               {raw_regulation_runs:,}")
print(f"Raw regulation batter runs:        {raw_regulation_batter_runs:,}")
print(f"Raw regulation extras:             {raw_regulation_extras:,}")
print(f"Raw regulation legal balls:        {raw_legal_balls:,}")
print(f"Raw wickets:                        {raw_wickets:,}")
print(f"Raw fours:                          {raw_fours:,}")
print(f"Raw sixes:                          {raw_sixes:,}")
print(f"Raw Super Over deliveries:          {raw_super_over_deliveries:,}")
print(f"Raw Super Over runs:                {raw_super_over_runs:,}")
print(f"All-out regulation innings:         {len(raw_all_out):,}")
print(f"Likely shortened innings:           {len(raw_shortened):,}")
print(f"Super Over matches:                 {len(raw_super_over_matches):,}")

if len(raw_match_ids) == 5700:
    pass_msg("Raw match IDs = 5,700")
else:
    fail_msg("Raw match count mismatch")

if raw_super_over_deliveries == 550:
    pass_msg("Super Over deliveries = 550")
else:
    fail_msg(f"Expected 550 Super Over deliveries, found {raw_super_over_deliveries:,}")

if raw_super_over_runs == 1028:
    pass_msg("Super Over runs = 1,028")
else:
    fail_msg(f"Expected 1,028 Super Over runs, found {raw_super_over_runs:,}")

# =============================================================================
# RAW VS PROCESSED MATCH IDS
# =============================================================================

section("RAW VS PROCESSED MATCH IDS")

processed_ids = {r["match_id"] for r in matches}
missing = raw_match_ids - processed_ids
extra = processed_ids - raw_match_ids

print(f"Missing processed IDs:             {len(missing):,}")
print(f"Extra processed IDs:               {len(extra):,}")

if not missing:
    pass_msg("Every raw match exists in processed data")
else:
    fail_msg(f"{len(missing)} raw matches missing")

if not extra:
    pass_msg("No extra processed matches")
else:
    fail_msg(f"{len(extra)} processed matches absent from raw")

# =============================================================================
# RESULT RECONCILIATION
# =============================================================================

section("RESULT RECONCILIATION")

print("Raw:", dict(raw_result_counts))

processed_result_counts = Counter(
    str(r.get("result_type", "")).strip().upper()
    for r in matches
)

print("Processed:", dict(processed_result_counts))

if raw_result_counts["WINNER"] == 5536:
    pass_msg("Raw WINNER count = 5,536")
else:
    fail_msg(f"Raw WINNER count mismatch: {raw_result_counts['WINNER']}")

if raw_result_counts["TIED"] == 51:
    pass_msg("Raw TIED count = 51")
else:
    fail_msg(f"Raw TIED count mismatch: {raw_result_counts['TIED']}")

if raw_result_counts["NO_RESULT"] == 113:
    pass_msg("Raw NO_RESULT count = 113")
else:
    fail_msg(f"Raw NO_RESULT count mismatch: {raw_result_counts['NO_RESULT']}")

processed_no_results = {
    r["match_id"] for r in matches
    if str(r.get("result_type", "")).strip().upper() == "NO_RESULT"
}
processed_ties = {
    r["match_id"] for r in matches
    if str(r.get("result_type", "")).strip().upper() == "TIED"
}

if processed_no_results == raw_no_results:
    pass_msg("No-result match sets are identical")
else:
    fail_msg(
        f"No-result set mismatch: "
        f"missing={len(raw_no_results - processed_no_results)}, "
        f"extra={len(processed_no_results - raw_no_results)}"
    )

if processed_ties == raw_ties:
    pass_msg("Tied match sets are identical")
else:
    fail_msg(
        f"Tied set mismatch: "
        f"missing={len(raw_ties - processed_ties)}, "
        f"extra={len(processed_ties - raw_ties)}"
    )

# =============================================================================
# GLOBAL RUN / EXTRAS RECONCILIATION
# =============================================================================

section("GLOBAL RUN / EXTRAS RECONCILIATION")

processed_team_runs = sum(safe_int(r["runs"]) for r in match_team_stats)
processed_player_runs = sum(safe_int(r["batting_runs"]) for r in player_match)
processed_extras = sum(safe_int(r["extras"]) for r in match_team_stats)

print(f"Raw regulation runs:               {raw_regulation_runs:,}")
print(f"Processed team runs:               {processed_team_runs:,}")
print(f"Processed player batting runs:     {processed_player_runs:,}")
print(f"Processed extras:                  {processed_extras:,}")

if processed_team_runs == raw_regulation_runs:
    pass_msg("Processed team runs = raw regulation runs")
else:
    fail_msg("Processed team runs mismatch")

if processed_player_runs == raw_regulation_batter_runs:
    pass_msg("Processed player batting runs = raw batter runs")
else:
    fail_msg("Processed player batting runs mismatch")

if processed_extras == raw_regulation_extras:
    pass_msg("Processed extras = raw regulation extras")
else:
    fail_msg("Processed extras mismatch")

if processed_player_runs + processed_extras == processed_team_runs:
    pass_msg("Player batting runs + extras = team runs")
else:
    fail_msg("Player batting runs + extras mismatch")

# =============================================================================
# LEGAL BALL RECONCILIATION
# =============================================================================

section("LEGAL BALL RECONCILIATION")

processed_total_balls = sum(
    safe_int(r["total_balls"]) for r in match_team_stats
)

print(f"Raw legal balls:                   {raw_legal_balls:,}")
print(f"Processed total_balls:             {processed_total_balls:,}")

if processed_total_balls == raw_legal_balls:
    pass_msg("Processed total_balls = raw regulation legal balls")
else:
    fail_msg("Processed total_balls mismatch")

# =============================================================================
# ALLOCATED BALLS
# =============================================================================

section("ALLOCATED-BALLS AUDIT")

processed_allocated = {
    (r["match_id"], normalize_team(r["team_name"])): safe_int(
        r.get("allocated_balls", 0)
    )
    for r in match_team_stats
}

allocation_mismatches = []

for match_id, team, raw_info in allocated_audit:
    legal_sum, expected_allocated, all_out_count = raw_info
    key = (match_id, team)

    if key not in processed_allocated:
        allocation_mismatches.append(
            (key, "MISSING", expected_allocated, None, raw_info)
        )
        continue

    actual = processed_allocated[key]

    if actual != expected_allocated:
        allocation_mismatches.append(
            (key, "allocated_balls", expected_allocated, actual, raw_info)
        )

print(f"Raw match-team allocation keys:   {len(allocated_audit):,}")
print(f"Allocated-ball mismatches:         {len(allocation_mismatches):,}")

if not allocation_mismatches:
    pass_msg(
        "Processed allocated_balls matches the audit rule "
        "(all-out => applicable quota, otherwise actual legal balls)"
    )
else:
    fail_msg(f"{len(allocation_mismatches)} allocated_balls mismatches")
    print("\nFirst 40 allocation mismatches:")
    for item in allocation_mismatches[:40]:
        print(item)

# =============================================================================
# MATCH-TEAM RECONCILIATION
# =============================================================================

section("MATCH-TEAM RAW VS PROCESSED")

team_mismatches = []

for key, raw in raw_match_team.items():
    row = processed_match_team.get(key)

    if row is None:
        team_mismatches.append((key, "MISSING", raw, None))
        continue

    checks = {
        "runs": (raw["runs"], safe_int(row["runs"])),
        "extras": (raw["extras"], safe_int(row["extras"])),
        "total_balls": (raw["legal_balls"], safe_int(row["total_balls"])),
        "fours": (raw["fours"], safe_int(row["fours"])),
        "sixes": (raw["sixes"], safe_int(row["sixes"])),
        "wickets": (raw["wickets"], safe_int(row["wickets"])),
    }

    for field, (expected, actual) in checks.items():
        if expected != actual:
            team_mismatches.append((key, field, expected, actual))

print(f"Raw match-team keys:               {len(raw_match_team):,}")
print(f"Match-team field mismatches:       {len(team_mismatches):,}")

if not team_mismatches:
    pass_msg("Raw and processed match-team statistics reconcile exactly")
else:
    fail_msg(f"{len(team_mismatches)} match-team mismatches")
    for item in team_mismatches[:40]:
        print(item)

# =============================================================================
# PLAYER-MATCH RECONCILIATION BY EXTERNAL ID
# =============================================================================

section("PLAYER-MATCH RECONCILIATION BY CRICSHEET EXTERNAL ID")

player_mismatches = []
missing_player_keys = []
extra_player_keys = []

raw_player_keys = set(raw_player_match.keys())
processed_player_keys = set(processed_player_match.keys())

for key in raw_player_keys:
    raw = raw_player_match[key]
    row = processed_player_match.get(key)

    if row is None:
        missing_player_keys.append(key)
        continue

    checks = {
        "batting_runs": (raw["runs"], safe_int(row["batting_runs"])),
        "balls_faced": (raw["balls_faced"], safe_int(row["balls_faced"])),
        "fours": (raw["fours"], safe_int(row["fours"])),
        "sixes": (raw["sixes"], safe_int(row["sixes"])),
        "balls_bowled": (raw["balls_bowled"], safe_int(row["balls_bowled"])),
        "runs_conceded": (raw["runs_conceded"], safe_int(row["runs_conceded"])),
        "wickets": (raw["wickets"], safe_int(row["wickets"])),
    }

    for field, (expected, actual) in checks.items():
        if expected != actual:
            player_mismatches.append(
                (key, field, expected, actual, row.get("player_name"))
            )

extra_player_keys = processed_player_keys - raw_player_keys

print(f"Raw player-match keys:             {len(raw_player_keys):,}")
print(f"Processed player-match keys:       {len(processed_player_keys):,}")
print(f"Missing processed keys:             {len(missing_player_keys):,}")
print(f"Extra processed keys:               {len(extra_player_keys):,}")
print(f"Field mismatches:                   {len(player_mismatches):,}")

if not missing_player_keys:
    pass_msg("Every raw player-match external-ID key exists")
else:
    fail_msg(f"{len(missing_player_keys)} raw player-match keys missing")

if not extra_player_keys:
    pass_msg("No extra processed player-match external-ID keys")
else:
    fail_msg(f"{len(extra_player_keys)} extra processed player-match keys")

if not player_mismatches:
    pass_msg("Raw and processed player-match statistics reconcile exactly by external ID")
else:
    fail_msg(f"{len(player_mismatches)} player-match field mismatches")
    for item in player_mismatches[:50]:
        print(item)

# =============================================================================
# CAREER RECONCILIATION BY EXTERNAL ID
# =============================================================================

section("CAREER RECONCILIATION BY CRICSHEET EXTERNAL ID")

career_mismatches = []
missing_career = []
extra_career = []

for external_id, raw in raw_career.items():
    row = processed_career.get(external_id)

    if row is None:
        missing_career.append(external_id)
        continue

    checks = {
        "matches": (len(raw["matches"]), safe_int(row["matches"])),
        "runs": (raw["runs"], safe_int(row["runs"])),
        "balls_faced": (raw["balls_faced"], safe_int(row["balls_faced"])),
        "fours": (raw["fours"], safe_int(row["fours"])),
        "sixes": (raw["sixes"], safe_int(row["sixes"])),
        "balls_bowled": (raw["balls_bowled"], safe_int(row["balls_bowled"])),
        "runs_conceded": (raw["runs_conceded"], safe_int(row["runs_conceded"])),
        "wickets": (raw["wickets"], safe_int(row["wickets"])),
    }

    for field, (expected, actual) in checks.items():
        if expected != actual:
            career_mismatches.append(
                (
                    external_id,
                    row.get("player_name"),
                    field,
                    expected,
                    actual,
                )
            )

extra_career = set(processed_career) - set(raw_career)

print(f"Raw career players:                {len(raw_career):,}")
print(f"Processed career players:          {len(processed_career):,}")
print(f"Missing career rows:               {len(missing_career):,}")
print(f"Extra career rows:                 {len(extra_career):,}")
print(f"Career field mismatches:            {len(career_mismatches):,}")

if not missing_career:
    pass_msg("Every raw external-ID career player has a processed career row")
else:
    fail_msg(f"{len(missing_career)} career players missing")

if not extra_career:
    pass_msg("No extra career external IDs")
else:
    fail_msg(f"{len(extra_career)} extra career external IDs")

if not career_mismatches:
    pass_msg("Career statistics reconcile exactly by external ID")
else:
    fail_msg(f"{len(career_mismatches)} career field mismatches")
    for item in career_mismatches[:50]:
        print(item)

# =============================================================================
# ALIAS / ID SANITY
# =============================================================================

section("PLAYER ALIAS / EXTERNAL-ID SANITY")

multi_name_ids = {
    external_id: names
    for external_id, names in player_name_aliases.items()
    if len(names) > 1
}

print(f"External IDs with multiple display names: {len(multi_name_ids):,}")

if multi_name_ids:
    warn_msg(
        "Some stable external IDs have multiple display names; "
        "career auditing correctly uses external ID instead of name."
    )
    for external_id, names in list(multi_name_ids.items())[:20]:
        print(external_id, sorted(names))

# Every processed player-match row should have an external ID.
missing_processed_external_ids = [
    r for r in player_match
    if not r.get("player_external_id", "").strip()
]

if not missing_processed_external_ids:
    pass_msg("Every processed player-match row has player_external_id")
else:
    fail_msg(
        f"{len(missing_processed_external_ids)} processed player-match rows "
        "have no external ID"
    )

# =============================================================================
# DERIVED CAREER STATISTICS
# =============================================================================

section("CAREER DERIVED-STATISTICS CHECK")

derived_errors = []

for row in player_stats:
    name = row.get("player_name", "")
    runs = safe_int(row.get("runs"))
    balls = safe_int(row.get("balls_faced"))
    balls_bowled = safe_int(row.get("balls_bowled"))
    runs_conceded = safe_int(row.get("runs_conceded"))
    not_outs = safe_int(row.get("not_outs"))
    batting_innings = safe_int(row.get("batting_innings"))
    strike_rate = safe_float(row.get("strike_rate"))
    economy = safe_float(row.get("economy"))

    if not_outs > batting_innings:
        derived_errors.append((name, "not_outs > batting_innings"))

    if balls > 0:
        expected_sr = runs / balls * 100
        if abs(strike_rate - expected_sr) > TOLERANCE:
            derived_errors.append(
                (name, "strike_rate", expected_sr, strike_rate)
            )

    if balls_bowled > 0:
        expected_econ = runs_conceded / balls_bowled * 6
        if abs(economy - expected_econ) > TOLERANCE:
            derived_errors.append(
                (name, "economy", expected_econ, economy)
            )

print(f"Derived-stat errors:                {len(derived_errors):,}")

if not derived_errors:
    pass_msg("Career derived statistics are mathematically consistent")
else:
    fail_msg(f"{len(derived_errors)} career derived-stat errors")
    for item in derived_errors[:40]:
        print(item)

# =============================================================================
# WICKET RECONCILIATION
# =============================================================================

section("WICKET RECONCILIATION")

processed_team_wickets = sum(
    safe_int(r["wickets"]) for r in match_team_stats
)
processed_bowler_wickets = sum(
    safe_int(r["wickets"]) for r in player_match
)

print(f"Raw dismissals:                    {raw_wickets:,}")
print(f"Processed team wickets:            {processed_team_wickets:,}")
print(f"Processed bowler wickets:          {processed_bowler_wickets:,}")

if processed_team_wickets == raw_wickets:
    pass_msg("Processed team wickets = raw dismissals")
else:
    fail_msg("Processed team wickets mismatch")

if processed_bowler_wickets <= processed_team_wickets:
    pass_msg("Bowler wickets do not exceed team wickets")
else:
    fail_msg("Bowler wickets exceed team wickets")

# =============================================================================
# SPECIAL MULTIPLE SUPER OVER
# =============================================================================

section("SPECIAL MULTIPLE-SUPER-OVER MATCH")

special_id = "1485939"

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    filename = special_id + ".json"
    if filename in z.namelist():
        with z.open(filename) as f:
            special = json.load(f)

        innings = special.get("innings", []) or []
        total_innings = len(innings)
        super_innings = sum(
            1 for x in innings if is_super_over(x)
        )
        total_deliveries = sum(
            1 for x in innings for _ in iter_deliveries(x)
        )

        print(f"Match ID:                          {special_id}")
        print(f"Total innings:                     {total_innings}")
        print(f"Super Over innings:                {super_innings}")
        print(f"Total deliveries:                  {total_deliveries}")

        if total_innings == 8 and super_innings == 6:
            pass_msg("Multiple-Super-Over match has 8 innings / 6 Super Over innings")
        else:
            fail_msg("Multiple-Super-Over structure mismatch")
    else:
        fail_msg(f"Special match {special_id} not found")

# =============================================================================
# FINAL
# =============================================================================

section("FINAL DEEP AUDIT RESULT")

print(f"PASS checks:                        {PASS_COUNT:,}")
print(f"WARN checks:                        {WARN_COUNT:,}")
print(f"FAIL checks:                        {FAIL_COUNT:,}")

if FAIL_COUNT == 0:
    print("\n" + "=" * 95)
    print("T20I DEEP AUDIT V2: PASS")
    print("=" * 95)
    print("The T20I raw and processed datasets passed all critical pre-import checks.")
    print("NEXT STEP: run the T20I MySQL importer with IMPORT_LIMIT = None.")
else:
    print("\n" + "=" * 95)
    print("T20I DEEP AUDIT V2: FAIL")
    print("=" * 95)
    print("DO NOT IMPORT ALL T20I DATA INTO MYSQL YET.")
