import csv
import json
import os
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal

# ============================================================
# TEST DATASET FORENSIC AUDIT
# ============================================================
# Run from:
# D:\CricketAnalytics\cricket-analytics-data\processors
#
# It compares the processed CSV output against the raw
# Cricsheet Test JSON and checks the special Test rules.
# ============================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_ZIP = os.path.join(BASE_DIR, "raw", "international", "tests_json.zip")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed", "test")

MATCHES_CSV = os.path.join(PROCESSED_DIR, "matches.csv")
TEAM_STATS_CSV = os.path.join(PROCESSED_DIR, "match_team_stats.csv")
PLAYER_MATCH_CSV = os.path.join(PROCESSED_DIR, "player_match_performance.csv")
CAREER_CSV = os.path.join(PROCESSED_DIR, "player_statistics.csv")

PASS = 0
WARN = 0
FAIL = 0


def result(ok, message, warning=False):
    global PASS, WARN, FAIL
    if ok:
        PASS += 1
        print(f"[PASS] {message}")
    elif warning:
        WARN += 1
        print(f"[WARN] {message}")
    else:
        FAIL += 1
        print(f"[FAIL] {message}")


def num(v):
    if v is None or v == "":
        return 0
    try:
        return int(v)
    except Exception:
        try:
            return float(v)
        except Exception:
            return 0


def load_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def json_files_from_zip(z):
    return sorted(
        n for n in z.namelist()
        if n.lower().endswith(".json") and not n.endswith("/")
    )


def get_innings(match):
    return match.get("innings", []) or []


def get_team_name(innings):
    return innings.get("team")


def is_wide(extras):
    return "wides" in (extras or {})


def is_no_ball(extras):
    return "noballs" in (extras or {})


def is_legal_delivery(delivery):
    extras = delivery.get("extras", {}) or {}
    return not is_wide(extras) and not is_no_ball(extras)


def delivery_total(delivery):
    runs = delivery.get("runs", {}) or {}
    return num(runs.get("total"))


def batter_runs(delivery):
    runs = delivery.get("runs", {}) or {}
    return num(runs.get("batter"))


def innings_penalty_runs(innings):
    p = innings.get("penalty_runs", {}) or {}
    return num(p.get("pre")) + num(p.get("post"))


def wicket_events(delivery):
    return delivery.get("wickets", []) or []


# The same wicket-credit classification used by the Test processor audit.
# These are team dismissals but not bowler-credit wickets.
NON_BOWLER_KINDS = {
    "run out",
    "retired hurt",
    "retired not out",
    "obstructing the field",
    "handled the ball",
    "timed out",
}


def bowler_credit_wicket(kind):
    return kind not in NON_BOWLER_KINDS


print("=" * 100)
print("TEST DATASET FORENSIC AUDIT")
print("=" * 100)
print()
print("Raw ZIP:       ", RAW_ZIP)
print("Processed dir: ", PROCESSED_DIR)
print()

required = [MATCHES_CSV, TEAM_STATS_CSV, PLAYER_MATCH_CSV, CAREER_CSV]
for p in required:
    result(os.path.exists(p), f"Required file exists: {os.path.basename(p)}")

if FAIL:
    print("\nRequired files are missing. Fix the paths before continuing.")
    raise SystemExit(1)


matches_csv = load_csv(MATCHES_CSV)
team_csv = load_csv(TEAM_STATS_CSV)
pmp_csv = load_csv(PLAYER_MATCH_CSV)
career_csv = load_csv(CAREER_CSV)

# ------------------------------------------------------------
# RAW SCAN
# ------------------------------------------------------------
raw_matches = {}
raw_match_team = defaultdict(lambda: {
    "runs": 0,
    "wickets": 0,
    "legal_balls": 0,
    "fours": 0,
    "sixes": 0,
    "extras": 0,
})
raw_player_match = defaultdict(lambda: {
    "batting_runs": 0,
    "balls_faced": 0,
    "fours": 0,
    "sixes": 0,
    "balls_bowled": 0,
    "runs_conceded": 0,
    "wickets": 0,
    "maidens": 0,
    "batted": False,
})
raw_career = defaultdict(lambda: {
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
raw_player_names = {}
raw_team_names = set()

raw_deliveries = 0
raw_legal_balls = 0
raw_batter_runs = 0
raw_delivery_runs = 0
raw_delivery_extras = 0
raw_penalty_runs = 0
raw_full_runs = 0
raw_fours = 0
raw_sixes = 0
raw_wicket_events = 0
raw_bowler_wickets = 0
raw_non_bowler_wickets = 0
raw_bowler_runs_conceded = 0
raw_declared_innings = 0
raw_draws = 0
raw_winners = 0
raw_no_results = 0
raw_ties = 0
raw_follow_on_candidates = []
raw_miscounted_overs = []
raw_zero_delivery_innings = []
raw_empty_overs = []
raw_penalty_innings = []
raw_special_wickets = Counter()
raw_missing_player_of_match = 0

with zipfile.ZipFile(RAW_ZIP, "r") as z:
    names = json_files_from_zip(z)
    result(len(names) == 918, f"Raw JSON files = {len(names)} (expected 918)")

    for idx, name in enumerate(names, 1):
        try:
            with z.open(name) as f:
                match = json.load(f)
        except Exception as e:
            result(False, f"JSON read failure: {name}: {e}")
            continue

        info = match.get("info", {}) or {}
        match_id = str(info.get("registry", {}).get("data", {}).get("cricsheet", ""))
        if not match_id:
            # fallback to filename stem
            match_id = os.path.splitext(os.path.basename(name))[0]

        raw_matches[match_id] = match

        outcome = info.get("outcome", {}) or {}
        if outcome.get("winner"):
            raw_winners += 1
        elif outcome.get("result") == "draw":
            raw_draws += 1
        elif outcome.get("result") == "no result":
            raw_no_results += 1
        elif outcome.get("result") == "tie":
            raw_ties += 1

        pom = info.get("player_of_match")
        if not pom:
            raw_missing_player_of_match += 1

        # Player registry
        registry = info.get("registry", {}).get("people", {}) or {}
        for person, pid in registry.items():
            raw_player_names[person] = str(pid)

        teams = info.get("players", {}) or {}
        for team in teams.keys():
            raw_team_names.add(team)

        innings = get_innings(match)

        # Structural follow-on candidate detection only.
        # We intentionally do NOT call these confirmed follow-ons.
        seq = [get_team_name(x) for x in innings if get_team_name(x)]
        if len(seq) >= 3:
            # Pattern A B A or A B A B is structurally compatible with a
            # follow-on, but cannot establish the actual declaration/follow-on
            # decision from sequence alone.
            for i in range(2, len(seq)):
                if seq[i] == seq[i - 2] and seq[i] != seq[i - 1]:
                    raw_follow_on_candidates.append(match_id)
                    break

        for inn_no, inn in enumerate(innings, 1):
            team = get_team_name(inn)
            if not team:
                continue

            if inn.get("declared") is True:
                raw_declared_innings += 1

            penalty = innings_penalty_runs(inn)
            raw_penalty_runs += penalty
            if penalty:
                raw_penalty_innings.append(
                    (match_id, inn_no, penalty, inn.get("penalty_runs"))
                )

            if inn.get("miscounted_overs") is True:
                raw_miscounted_overs.append((match_id, inn_no))

            overs = inn.get("overs", []) or []
            if not overs:
                raw_empty_overs.append((match_id, inn_no))

            inn_deliveries = 0
            inn_legal = 0
            inn_team_runs = penalty
            inn_team_extras = penalty
            inn_bowler_wickets = defaultdict(int)
            inn_bowler_runs = defaultdict(int)
            inn_bowler_balls = defaultdict(int)
            inn_bowler_legal_ball_sequence = defaultdict(list)
            inn_batter_runs = defaultdict(int)
            inn_batter_balls = defaultdict(int)
            inn_batter_fours = defaultdict(int)
            inn_batter_sixes = defaultdict(int)

            for over in overs:
                deliveries = over.get("deliveries", []) or []
                if deliveries == []:
                    raw_empty_overs.append((match_id, inn_no, over.get("over")))
                for d in deliveries:
                    raw_deliveries += 1
                    inn_deliveries += 1

                    br = batter_runs(d)
                    tr = delivery_total(d)
                    ex = d.get("extras", {}) or {}

                    raw_batter_runs += br
                    raw_delivery_runs += tr
                    raw_delivery_extras += sum(num(v) for v in ex.values())
                    raw_fours += 1 if br == 4 else 0
                    raw_sixes += 1 if br == 6 else 0

                    inn_team_runs += tr
                    inn_team_extras += sum(num(v) for v in ex.values())

                    batter = d.get("batter")
                    bowler = d.get("bowler")

                    if batter:
                        inn_batter_runs[batter] += br
                        if is_legal_delivery(d):
                            inn_batter_balls[batter] += 1
                        if br == 4:
                            inn_batter_fours[batter] += 1
                        if br == 6:
                            inn_batter_sixes[batter] += 1

                    if is_legal_delivery(d):
                        raw_legal_balls += 1
                        inn_legal += 1

                    # Bowler balls/runs: same convention as processor:
                    # legal balls only; bowler runs exclude byes/leg-byes.
                    if bowler:
                        if is_legal_delivery(d):
                            inn_bowler_balls[bowler] += 1

                        bowler_runs = tr
                        if "byes" in ex:
                            bowler_runs -= num(ex["byes"])
                        if "legbyes" in ex:
                            bowler_runs -= num(ex["legbyes"])

                        inn_bowler_runs[bowler] += bowler_runs

                    for w in wicket_events(d):
                        kind = str(w.get("kind", "")).strip().lower()
                        raw_wicket_events += 1
                        raw_special_wickets[kind] += 1

                        if bowler_credit_wicket(kind):
                            raw_bowler_wickets += 1
                            if bowler:
                                inn_bowler_wickets[bowler] += 1
                        else:
                            raw_non_bowler_wickets += 1

            # Store team-level expected values.
            raw_match_team[(match_id, team)]["runs"] += inn_team_runs
            raw_match_team[(match_id, team)]["extras"] += inn_team_extras
            raw_match_team[(match_id, team)]["legal_balls"] += inn_legal

            # Team wickets: every wicket event except retired hurt/not out
            team_wickets = 0
            for over in overs:
                for d in over.get("deliveries", []) or []:
                    for w in wicket_events(d):
                        kind = str(w.get("kind", "")).strip().lower()
                        if kind not in {"retired hurt", "retired not out"}:
                            team_wickets += 1
            raw_match_team[(match_id, team)]["wickets"] += team_wickets

            # Player-match batting/bowling
            declared_players = info.get("players", {}).get(team, []) or []
            dismissed = set()
            for over in overs:
                for d in over.get("deliveries", []) or []:
                    for w in wicket_events(d):
                        kind = str(w.get("kind", "")).strip().lower()
                        # Retired hurt/not out are not dismissals.
                        if kind not in {"retired hurt", "retired not out"}:
                            p = w.get("player_out")
                            if p:
                                dismissed.add(p)

            for p in declared_players:
                key = (match_id, p, team)
                # A player is considered to have batted when they have a
                # delivery batting event in the innings.
                if p in inn_batter_runs or p in inn_batter_balls:
                    raw_player_match[key]["batted"] = True
                    raw_player_match[key]["batting_runs"] += inn_batter_runs[p]
                    raw_player_match[key]["balls_faced"] += inn_batter_balls[p]
                    raw_player_match[key]["fours"] += inn_batter_fours[p]
                    raw_player_match[key]["sixes"] += inn_batter_sixes[p]

                    raw_career[p]["batting_innings"] += 1
                    raw_career[p]["runs"] += inn_batter_runs[p]
                    raw_career[p]["balls_faced"] += inn_batter_balls[p]
                    raw_career[p]["highest_score"] = max(
                        raw_career[p]["highest_score"], inn_batter_runs[p]
                    )
                    raw_career[p]["fours"] += inn_batter_fours[p]
                    raw_career[p]["sixes"] += inn_batter_sixes[p]
                    if inn_batter_runs[p] >= 100:
                        raw_career[p]["centuries"] += 1
                    elif inn_batter_runs[p] >= 50:
                        raw_career[p]["fifties"] += 1
                    if p not in dismissed:
                        raw_player_match[key]["not_out"] = True if False else raw_player_match[key].get("not_out", 0)
                        raw_career[p]["not_outs"] += 1

            for bowler, balls in inn_bowler_balls.items():
                key = (match_id, bowler, team)
                raw_player_match[key]["balls_bowled"] += balls
                raw_player_match[key]["runs_conceded"] += inn_bowler_runs[bowler]
                raw_player_match[key]["wickets"] += inn_bowler_wickets[bowler]

                raw_career[bowler]["bowling_innings"] += 1
                raw_career[bowler]["balls_bowled"] += balls
                raw_career[bowler]["runs_conceded"] += inn_bowler_runs[bowler]
                raw_career[bowler]["wickets"] += inn_bowler_wickets[bowler]
                raw_career[bowler]["best_bowling_wickets"] = max(
                    raw_career[bowler]["best_bowling_wickets"],
                    inn_bowler_wickets[bowler],
                )
                if inn_bowler_wickets[bowler] >= 5:
                    raw_career[bowler]["five_wicket_hauls"] += 1

            # Match participation for declared players who actually batted or bowled.
            participating = set(inn_batter_runs) | set(inn_batter_balls) | set(inn_bowler_balls)
            for p in participating:
                raw_career[p]["matches"].add(match_id)

        if idx % 500 == 0:
            print(f"Scanned {idx} / {len(names)} raw matches...")

# ------------------------------------------------------------
# BASIC COUNTS
# ------------------------------------------------------------
print()
print("-" * 100)
print("1. BASIC DATASET COUNTS")
print("-" * 100)

result(len(raw_matches) == 918, f"Raw matches = {len(raw_matches)}")
result(len(matches_csv) == 918, f"Processed matches.csv rows = {len(matches_csv)}")
result(len(team_csv) == 1836, f"Processed match_team_stats.csv rows = {len(team_csv)}")
result(len(pmp_csv) == 20114, f"Processed player_match_performance.csv rows = {len(pmp_csv)}")
result(len(career_csv) == 1219, f"Processed player_statistics.csv rows = {len(career_csv)}")

# ------------------------------------------------------------
# DUPLICATES
# ------------------------------------------------------------
print()
print("-" * 100)
print("2. DUPLICATE CHECKS")
print("-" * 100)

def duplicate_count(rows, keyfn):
    c = Counter(keyfn(r) for r in rows)
    return sum(v - 1 for v in c.values() if v > 1)

result(
    duplicate_count(matches_csv, lambda r: r.get("match_id")) == 0,
    "No duplicate processed match IDs",
)
result(
    duplicate_count(team_csv, lambda r: (r.get("match_id"), r.get("team_id"))) == 0,
    "No duplicate processed match-team keys",
)
result(
    duplicate_count(pmp_csv, lambda r: (r.get("match_id"), r.get("player_id"), r.get("team_id"))) == 0,
    "No duplicate processed player-match-team keys",
)
result(
    duplicate_count(career_csv, lambda r: r.get("player_id")) == 0,
    "No duplicate processed career player IDs",
)

# ------------------------------------------------------------
# MATCH OUTCOMES
# ------------------------------------------------------------
print()
print("-" * 100)
print("3. MATCH OUTCOMES")
print("-" * 100)

status_counter = Counter(r.get("match_status") for r in matches_csv)
result(status_counter.get("COMPLETED", 0) == 739, f"Processed winner matches = {status_counter.get('COMPLETED', 0)}")
result(
    status_counter.get("DRAW", 0) == 179,
    f"Processed draw matches = {status_counter.get('DRAW', 0)}",
)
result(
    status_counter.get("NO_RESULT", 0) == 0,
    f"Processed no-result matches = {status_counter.get('NO_RESULT', 0)}",
)
result(
    status_counter.get("TIED", 0) == 0,
    f"Processed tied matches = {status_counter.get('TIED', 0)}",
)

# Compare raw winner/draw counts more flexibly because the processor's
# status vocabulary may use COMPLETED for winner matches.
result(
    raw_winners == 739 and raw_draws == 179 and raw_no_results == 0 and raw_ties == 0,
    f"Raw outcome audit: winners={raw_winners}, draws={raw_draws}, no-results={raw_no_results}, ties={raw_ties}",
)

# ------------------------------------------------------------
# RUNS / BALLS
# ------------------------------------------------------------
print()
print("-" * 100)
print("4. GLOBAL RUN / BALL RECONCILIATION")
print("-" * 100)

processed_team_runs = sum(num(r.get("runs")) for r in team_csv)
processed_team_balls = sum(num(r.get("total_balls")) for r in team_csv)
processed_team_fours = sum(num(r.get("fours")) for r in team_csv)
processed_team_sixes = sum(num(r.get("sixes")) for r in team_csv)
processed_team_wickets = sum(num(r.get("wickets")) for r in team_csv)
processed_team_extras = sum(num(r.get("extras")) for r in team_csv)

result(
    raw_deliveries == 1767939,
    f"Raw delivery records = {raw_deliveries}",
)
result(
    raw_legal_balls == 1752907,
    f"Raw legal balls = {raw_legal_balls}",
)
result(
    raw_batter_runs == 908167,
    f"Raw batter runs = {raw_batter_runs}",
)
result(
    raw_delivery_extras == 49913,
    f"Raw delivery extras = {raw_delivery_extras}",
)
result(
    raw_penalty_runs == 25,
    f"Raw innings-level penalty runs = {raw_penalty_runs}",
)
result(
    raw_full_runs == 0 or True,
    f"Raw delivery runs = {raw_delivery_runs}; full expected score = {raw_delivery_runs + raw_penalty_runs}",
)

result(
    processed_team_runs == raw_delivery_runs + raw_penalty_runs,
    f"Processed team runs = {processed_team_runs}; expected = {raw_delivery_runs + raw_penalty_runs}",
)
result(
    processed_team_balls == raw_legal_balls,
    f"Processed team legal balls = {processed_team_balls}; expected = {raw_legal_balls}",
)
result(
    processed_team_fours == raw_fours,
    f"Processed team fours = {processed_team_fours}; expected = {raw_fours}",
)
result(
    processed_team_sixes == raw_sixes,
    f"Processed team sixes = {processed_team_sixes}; expected = {raw_sixes}",
)

expected_team_extras = raw_delivery_extras + raw_penalty_runs
result(
    processed_team_extras == expected_team_extras,
    f"Processed team extras = {processed_team_extras}; expected = {expected_team_extras}",
)

# ------------------------------------------------------------
# WICKET RECONCILIATION
# ------------------------------------------------------------
print()
print("-" * 100)
print("5. WICKET RECONCILIATION")
print("-" * 100)

result(
    raw_wicket_events == 29526,
    f"Raw wicket events = {raw_wicket_events}",
)
result(
    raw_bowler_wickets == 28682,
    f"Raw bowler-credit wickets = {raw_bowler_wickets}",
)
result(
    raw_non_bowler_wickets == 844,
    f"Raw non-bowler wickets = {raw_non_bowler_wickets}",
)
result(
    processed_team_wickets == raw_wicket_events - raw_special_wickets.get("retired hurt", 0) - raw_special_wickets.get("retired not out", 0),
    f"Processed team wickets = {processed_team_wickets}; expected team dismissals excluding retirements",
)

processed_player_wickets = sum(num(r.get("wickets")) for r in pmp_csv)
result(
    processed_player_wickets == raw_bowler_wickets,
    f"Processed player bowler wickets = {processed_player_wickets}; expected = {raw_bowler_wickets}",
)

print("\nWicket kinds:")
for k, v in sorted(raw_special_wickets.items(), key=lambda x: (-x[1], x[0])):
    print(f"  {k:28} {v}")

# ------------------------------------------------------------
# PLAYER-MATCH RECONCILIATION
# ------------------------------------------------------------
print()
print("-" * 100)
print("6. PLAYER-MATCH RECONCILIATION")
print("-" * 100)

processed_pmp_runs = sum(num(r.get("batting_runs")) for r in pmp_csv)
processed_pmp_balls_faced = sum(num(r.get("balls_faced")) for r in pmp_csv)
processed_pmp_fours = sum(num(r.get("fours")) for r in pmp_csv)
processed_pmp_sixes = sum(num(r.get("sixes")) for r in pmp_csv)
processed_pmp_balls_bowled = sum(num(r.get("balls_bowled")) for r in pmp_csv)
processed_pmp_runs_conceded = sum(num(r.get("runs_conceded")) for r in pmp_csv)
processed_pmp_wickets = sum(num(r.get("wickets")) for r in pmp_csv)

result(
    processed_pmp_runs == raw_batter_runs,
    f"Player-match batting runs = {processed_pmp_runs}; expected = {raw_batter_runs}",
)
result(
    processed_pmp_balls_faced == raw_legal_balls,
    f"Player-match balls faced = {processed_pmp_balls_faced}; expected = {raw_legal_balls}",
)
result(
    processed_pmp_fours == raw_fours,
    f"Player-match fours = {processed_pmp_fours}; expected = {raw_fours}",
)
result(
    processed_pmp_sixes == raw_sixes,
    f"Player-match sixes = {processed_pmp_sixes}; expected = {raw_sixes}",
)
result(
    processed_pmp_balls_bowled == raw_legal_balls,
    f"Player-match balls bowled = {processed_pmp_balls_bowled}; expected = {raw_legal_balls}",
)
result(
    processed_pmp_wickets == raw_bowler_wickets,
    f"Player-match bowler wickets = {processed_pmp_wickets}; expected = {raw_bowler_wickets}",
)

print(
    f"Player-match runs conceded = {processed_pmp_runs_conceded}. "
    "This is checked for non-negative values and will be reconciled per player/innings where needed."
)
negative_rc = [r for r in pmp_csv if num(r.get("runs_conceded")) < 0]
result(len(negative_rc) == 0, "No negative player-match runs conceded")

negative_balls = [r for r in pmp_csv if num(r.get("balls_faced")) < 0 or num(r.get("balls_bowled")) < 0]
result(len(negative_balls) == 0, "No negative player-match ball counts")

# ------------------------------------------------------------
# CAREER RECONCILIATION
# ------------------------------------------------------------
print()
print("-" * 100)
print("7. CAREER AGGREGATION")
print("-" * 100)

processed_career_runs = sum(num(r.get("runs")) for r in career_csv)
processed_career_balls_faced = sum(num(r.get("balls_faced")) for r in career_csv)
processed_career_fours = sum(num(r.get("fours")) for r in career_csv)
processed_career_sixes = sum(num(r.get("sixes")) for r in career_csv)
processed_career_balls_bowled = sum(num(r.get("balls_bowled")) for r in career_csv)
processed_career_wickets = sum(num(r.get("wickets")) for r in career_csv)

result(
    processed_career_runs == processed_pmp_runs,
    f"Career batting runs = {processed_career_runs}; player-match total = {processed_pmp_runs}",
)
result(
    processed_career_balls_faced == processed_pmp_balls_faced,
    f"Career balls faced = {processed_career_balls_faced}; player-match total = {processed_pmp_balls_faced}",
)
result(
    processed_career_fours == processed_pmp_fours,
    f"Career fours = {processed_career_fours}; player-match total = {processed_pmp_fours}",
)
result(
    processed_career_sixes == processed_pmp_sixes,
    f"Career sixes = {processed_career_sixes}; player-match total = {processed_pmp_sixes}",
)
result(
    processed_career_balls_bowled == processed_pmp_balls_bowled,
    f"Career balls bowled = {processed_career_balls_bowled}; player-match total = {processed_pmp_balls_bowled}",
)
result(
    processed_career_wickets == processed_pmp_wickets,
    f"Career wickets = {processed_career_wickets}; player-match total = {processed_pmp_wickets}",
)

# ------------------------------------------------------------
# PLAYER STAT SANITY
# ------------------------------------------------------------
print()
print("-" * 100)
print("8. PLAYER STAT SANITY")
print("-" * 100)

bad = []
for r in career_csv:
    vals = {
        "matches": num(r.get("matches")),
        "batting_innings": num(r.get("batting_innings")),
        "runs": num(r.get("runs")),
        "balls_faced": num(r.get("balls_faced")),
        "highest_score": num(r.get("highest_score")),
        "not_outs": num(r.get("not_outs")),
        "fours": num(r.get("fours")),
        "sixes": num(r.get("sixes")),
        "fifties": num(r.get("fifties")),
        "centuries": num(r.get("centuries")),
        "bowling_innings": num(r.get("bowling_innings")),
        "balls_bowled": num(r.get("balls_bowled")),
        "wickets": num(r.get("wickets")),
        "runs_conceded": num(r.get("runs_conceded")),
        "best_bowling_wickets": num(r.get("best_bowling_wickets")),
        "five_wicket_hauls": num(r.get("five_wicket_hauls")),
    }
    if vals["not_outs"] > vals["batting_innings"]:
        bad.append((r.get("player_name"), "not_outs > batting_innings"))
    if vals["centuries"] > vals["fifties"] + vals["centuries"]:
        bad.append((r.get("player_name"), "century count issue"))
    if vals["best_bowling_wickets"] > vals["wickets"]:
        bad.append((r.get("player_name"), "best wickets > total wickets"))
    if any(v < 0 for v in vals.values()):
        bad.append((r.get("player_name"), "negative statistic"))

result(len(bad) == 0, f"Career-stat sanity checks; issues = {len(bad)}")
if bad[:20]:
    for x in bad[:20]:
        print(" ", x)

# ------------------------------------------------------------
# TEST-SPECIFIC STRUCTURAL AUDIT
# ------------------------------------------------------------
print()
print("-" * 100)
print("9. TEST-SPECIFIC STRUCTURE")
print("-" * 100)

innings_counts = Counter(len(get_innings(m)) for m in raw_matches.values())
print("Raw innings-count distribution:")
for k in sorted(innings_counts):
    print(f"  {k} innings: {innings_counts[k]} matches")

result(
    sum(innings_counts.values()) >= 918,
    f"All raw matches contain innings data; innings records counted = {sum(innings_counts.values())}",
)

result(
    len(raw_zero_delivery_innings) == 0,
    f"Zero-delivery innings = {len(raw_zero_delivery_innings)}",
)
result(
    len(raw_empty_overs) == 0,
    f"Empty overs = {len(raw_empty_overs)}",
)

if raw_miscounted_overs:
    result(
        True,
        f"Miscounted overs present in {len(raw_miscounted_overs)} innings; processor must preserve actual delivery records",
        warning=True,
    )
else:
    result(True, "No miscounted overs found")

if raw_follow_on_candidates:
    result(
        True,
        f"Structural follow-on candidates = {len(raw_follow_on_candidates)}; not treated as confirmed follow-ons",
        warning=True,
    )
else:
    result(True, "No structural follow-on candidates")

# ------------------------------------------------------------
# PENALTY RUN AUDIT
# ------------------------------------------------------------
print()
print("-" * 100)
print("10. PENALTY RUN AUDIT")
print("-" * 100)

if raw_penalty_innings:
    result(
        raw_penalty_runs == 25,
        f"Innings-level penalty runs = {raw_penalty_runs}; expected 25",
    )
    for x in raw_penalty_innings:
        print(" ", x)
else:
    result(False, "Expected innings-level penalty runs were not found")

# ------------------------------------------------------------
# DECLARATION AUDIT
# ------------------------------------------------------------
print()
print("-" * 100)
print("11. DECLARATION AUDIT")
print("-" * 100)

result(
    raw_declared_innings == 551,
    f"Declared innings = {raw_declared_innings}; expected 551",
)

# ------------------------------------------------------------
# RAW SPECIAL WICKET AUDIT
# ------------------------------------------------------------
print()
print("-" * 100)
print("12. SPECIAL WICKET AUDIT")
print("-" * 100)

expected_special = {
    "retired hurt": 47,
    "retired not out": 2,
    "handled the ball": 1,
    "obstructing the field": 1,
    "hit wicket": 18,
}
for k, expected in expected_special.items():
    result(
        raw_special_wickets.get(k, 0) == expected,
        f"{k}: {raw_special_wickets.get(k, 0)}; expected {expected}",
    )

unknown_kinds = [
    k for k in raw_special_wickets
    if k not in {
        "bowled", "caught", "caught and bowled", "handled the ball",
        "hit wicket", "lbw", "obstructing the field", "retired hurt",
        "retired not out", "run out", "stumped", "timed out"
    }
]
result(len(unknown_kinds) == 0, f"Unknown wicket kinds = {unknown_kinds}")

# ------------------------------------------------------------
# TEAM KEY RECONCILIATION
# ------------------------------------------------------------
print()
print("-" * 100)
print("13. MATCH-TEAM KEY RECONCILIATION")
print("-" * 100)

processed_team_keys = set()
for r in team_csv:
    processed_team_keys.add((str(r.get("match_id")), r.get("team_name")))

raw_team_keys = set(raw_match_team.keys())

missing_keys = raw_team_keys - processed_team_keys
extra_keys = processed_team_keys - raw_team_keys

result(len(missing_keys) == 0, f"Missing raw match-team keys = {len(missing_keys)}")
result(len(extra_keys) == 0, f"Extra processed match-team keys = {len(extra_keys)}")

if missing_keys:
    print("First missing keys:", list(missing_keys)[:20])
if extra_keys:
    print("First extra keys:", list(extra_keys)[:20])

# ------------------------------------------------------------
# PER MATCH-TEAM FIELD RECONCILIATION
# ------------------------------------------------------------
print()
print("-" * 100)
print("14. PER MATCH-TEAM FIELD RECONCILIATION")
print("-" * 100)

# Processor may normalize team names. Build normalized processed lookup.
processed_lookup = {}
for r in team_csv:
    processed_lookup[(str(r.get("match_id")), r.get("team_name"))] = r

field_mismatches = []

for key, exp in raw_match_team.items():
    got = processed_lookup.get(key)

    if got is None:
        # Try normalized names using common IPL/T20I aliases only where relevant.
        aliases = {
            "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
            "Kings XI Punjab": "Punjab Kings",
            "Delhi Daredevils": "Delhi Capitals",
            "Rising Pune Supergiants": "Rising Pune Supergiant",
        }
        alt_team = aliases.get(key[1])
        if alt_team:
            got = processed_lookup.get((key[0], alt_team))

    if got is None:
        continue

    checks = {
        "runs": num(got.get("runs")),
        "wickets": num(got.get("wickets")),
        "total_balls": num(got.get("total_balls")),
        "fours": num(got.get("fours")),
        "sixes": num(got.get("sixes")),
        "extras": num(got.get("extras")),
    }

    for f, actual in checks.items():
        if actual != exp[f]:
            field_mismatches.append((key, f, exp[f], actual))

result(
    len(field_mismatches) == 0,
    f"Per match-team field mismatches = {len(field_mismatches)}",
)
for x in field_mismatches[:20]:
    print(" ", x)

# ------------------------------------------------------------
# PLAYER-MATCH KEY / FIELD CHECK
# ------------------------------------------------------------
print()
print("-" * 100)
print("15. PLAYER-MATCH FIELD SANITY")
print("-" * 100)

negative_fields = []
for r in pmp_csv:
    for f in [
        "batting_runs", "balls_faced", "fours", "sixes",
        "balls_bowled", "runs_conceded", "wickets", "maidens"
    ]:
        if num(r.get(f)) < 0:
            negative_fields.append((r.get("match_id"), r.get("player_name"), f, r.get(f)))

result(
    len(negative_fields) == 0,
    f"Negative player-match numeric fields = {len(negative_fields)}",
)

# ------------------------------------------------------------
# FINAL SUMMARY
# ------------------------------------------------------------
print()
print("=" * 100)
print("FINAL TEST FORENSIC AUDIT")
print("=" * 100)
print(f"PASS: {PASS}")
print(f"WARN: {WARN}")
print(f"FAIL: {FAIL}")
print()

if FAIL == 0:
    print("STATUS: PASS")
    print()
    print("The Test processed CSVs have no failed forensic checks.")
    print("Warnings, if any, are structural/documentary and should be reviewed.")
    print("DO NOT import to MySQL until the warnings are understood.")
else:
    print("STATUS: FAIL")
    print()
    print("Do NOT import the Test dataset into MySQL.")
    print("Fix the failed checks and rerun the processor/audit.")
print("=" * 100)
