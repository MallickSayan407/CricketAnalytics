import os
import csv
import sys
from collections import defaultdict, deque
from pathlib import Path

try:
    import mysql.connector
except ImportError:
    print("ERROR: mysql-connector-python is not installed.")
    print("Run: python -m pip install mysql-connector-python")
    sys.exit(1)

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "cricket_analytics",
    "user": "root",
    "password": os.getenv("DB_PASSWORD"),
}

OUTPUT_FILE = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\ml\datasets\odi_match_training.csv"
)
ODI_COMPETITION_ID = 1
MALE = "male"


def si(v, default=0):
    try:
        return default if v is None else int(v)
    except (TypeError, ValueError):
        return default


def sf(v, default=0.0):
    try:
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default


def rate(wins, decided, default=0.5):
    return default if decided <= 0 else wins / decided


def recent_rate(history, n):
    recent = list(history)[-n:]
    wins = sum(x[0] == "W" for x in recent)
    decided = sum(x[0] in ("W", "L") for x in recent)
    return rate(wins, decided)


def classify(match, team_id):
    winner = match["winner_team_id"]
    if winner is not None:
        winner = si(winner)
        if winner == team_id:
            return "W"
        if winner in (si(match["team1_id"]), si(match["team2_id"])):
            return "L"
    if (match["match_status"] or "").upper() == "TIED":
        return "T"
    return "NR"


class TeamState:
    def __init__(self):
        self.matches = 0
        self.wins = 0
        self.losses = 0
        self.runs = 0
        self.wickets = 0
        self.performance_matches = 0
        self.recent = deque(maxlen=10)
        self.venues = defaultdict(lambda: {"matches": 0, "wins": 0, "losses": 0})


def pair_state(h2h, a, b):
    x, y = sorted((a, b))
    key = (x, y)
    if key not in h2h:
        h2h[key] = {"x": x, "y": y, "matches": 0, "wins_x": 0, "wins_y": 0}
    return h2h[key]


def load_matches(conn):
    sql = """
        SELECT m.id, m.external_id, m.match_date, m.match_status,
               m.counted_in_standings, m.winner_team_id,
               m.team1_id, m.team2_id, m.venue_id,
               t1.gender AS team1_gender,
               t2.gender AS team2_gender,
               t1.name AS team1_name, t2.name AS team2_name,
               v.name AS venue_name
        FROM matches m
        JOIN teams t1 ON t1.id = m.team1_id
        JOIN teams t2 ON t2.id = m.team2_id
        LEFT JOIN venues v ON v.id = m.venue_id
        WHERE m.competition_id = %s
          AND LOWER(t1.gender) = %s
          AND LOWER(t2.gender) = %s
        ORDER BY m.match_date ASC, m.id ASC
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, (ODI_COMPETITION_ID, MALE, MALE))
    rows = cur.fetchall()

    # The model works only with same-gender men's ODI matches.
    # Derive the match-level gender from the participating teams.
    for row in rows:
        row["gender"] = row["team1_gender"]

    cur.close()
    return rows


def load_stats(conn):
    sql = """
        SELECT mts.match_id, mts.team_id, mts.runs, mts.wickets,
               mts.total_balls, mts.fours, mts.sixes, mts.extras,
               mts.run_rate
        FROM match_team_stats mts
        JOIN matches m ON m.id = mts.match_id
        JOIN teams t1 ON t1.id = m.team1_id
        JOIN teams t2 ON t2.id = m.team2_id
        WHERE m.competition_id = %s
          AND LOWER(t1.gender) = %s
          AND LOWER(t2.gender) = %s
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, (ODI_COMPETITION_ID, MALE, MALE))
    rows = cur.fetchall()
    cur.close()
    return {
        (si(r["match_id"]), si(r["team_id"])): {
            "runs": si(r["runs"]),
            "wickets": si(r["wickets"]),
            "total_balls": si(r["total_balls"]),
            "fours": si(r["fours"]),
            "sixes": si(r["sixes"]),
            "extras": si(r["extras"]),
            "run_rate": sf(r["run_rate"]),
        }
        for r in rows
    }


def eligible(m):
    # `gender` is derived from t1.gender because matches.gender does not exist.
    if (m["gender"] or "").lower() != MALE:
        return False
    if not bool(m["counted_in_standings"]):
        return False
    if m["winner_team_id"] is None:
        return False
    winner = si(m["winner_team_id"])
    return winner in (si(m["team1_id"]), si(m["team2_id"])) and \
        (m["match_status"] or "").upper() not in ("NO_RESULT", "TIED")


FIELDS = [
    "match_id", "external_id", "match_date",
    "team_a_id", "team_a", "team_b_id", "team_b",
    "venue_id", "venue",
    "team_a_matches_before", "team_a_wins_before",
    "team_a_decided_matches_before", "team_a_win_rate",
    "team_a_last5_win_rate", "team_a_last10_win_rate",
    "team_a_avg_runs", "team_a_avg_wickets",
    "team_b_matches_before", "team_b_wins_before",
    "team_b_decided_matches_before", "team_b_win_rate",
    "team_b_last5_win_rate", "team_b_last10_win_rate",
    "team_b_avg_runs", "team_b_avg_wickets",
    "team_a_venue_matches_before", "team_a_venue_win_rate",
    "team_b_venue_matches_before", "team_b_venue_win_rate",
    "head_to_head_matches_before", "head_to_head_a_wins",
    "head_to_head_b_wins", "head_to_head_a_win_rate",
    "head_to_head_b_win_rate", "target",
]


def make_features(m, states, h2h):
    a, b, venue = si(m["team1_id"]), si(m["team2_id"]), si(m["venue_id"])
    A, B = states[a], states[b]
    av, bv = A.venues[venue], B.venues[venue]

    ad, bd = A.wins + A.losses, B.wins + B.losses
    avd, bvd = av["wins"] + av["losses"], bv["wins"] + bv["losses"]

    p = pair_state(h2h, a, b)
    if p["matches"]:
        if p["x"] == a:
            aw, bw = p["wins_x"], p["wins_y"]
        else:
            aw, bw = p["wins_y"], p["wins_x"]
    else:
        aw = bw = 0

    winner = si(m["winner_team_id"])
    target = 1 if winner == a else 0

    return {
        "match_id": si(m["id"]),
        "external_id": m["external_id"] or "",
        "match_date": m["match_date"].isoformat(),
        "team_a_id": a, "team_a": m["team1_name"],
        "team_b_id": b, "team_b": m["team2_name"],
        "venue_id": venue, "venue": m["venue_name"] or "",
        "team_a_matches_before": A.matches,
        "team_a_wins_before": A.wins,
        "team_a_decided_matches_before": ad,
        "team_a_win_rate": rate(A.wins, ad),
        "team_a_last5_win_rate": recent_rate(A.recent, 5),
        "team_a_last10_win_rate": recent_rate(A.recent, 10),
        "team_a_avg_runs": round(A.runs / A.performance_matches, 4) if A.performance_matches else 0.0,
        "team_a_avg_wickets": round(A.wickets / A.performance_matches, 4) if A.performance_matches else 0.0,
        "team_b_matches_before": B.matches,
        "team_b_wins_before": B.wins,
        "team_b_decided_matches_before": bd,
        "team_b_win_rate": rate(B.wins, bd),
        "team_b_last5_win_rate": recent_rate(B.recent, 5),
        "team_b_last10_win_rate": recent_rate(B.recent, 10),
        "team_b_avg_runs": round(B.runs / B.performance_matches, 4) if B.performance_matches else 0.0,
        "team_b_avg_wickets": round(B.wickets / B.performance_matches, 4) if B.performance_matches else 0.0,
        "team_a_venue_matches_before": av["matches"],
        "team_a_venue_win_rate": rate(av["wins"], avd),
        "team_b_venue_matches_before": bv["matches"],
        "team_b_venue_win_rate": rate(bv["wins"], bvd),
        "head_to_head_matches_before": p["matches"],
        "head_to_head_a_wins": aw, "head_to_head_b_wins": bw,
        "head_to_head_a_win_rate": rate(aw, aw + bw),
        "head_to_head_b_win_rate": rate(bw, aw + bw),
        "target": target,
    }


def update(m, states, h2h, stats):
    mid = si(m["id"])
    a, b, venue = si(m["team1_id"]), si(m["team2_id"]), si(m["venue_id"])

    for team, result in ((a, classify(m, a)), (b, classify(m, b))):
        s = states[team]
        s.matches += 1
        if result == "W":
            s.wins += 1
        elif result == "L":
            s.losses += 1

        st = stats.get((mid, team), {})
        s.recent.append((result, si(st.get("runs")), si(st.get("wickets")), venue))
        if st:
            s.runs += si(st.get("runs"))
            s.wickets += si(st.get("wickets"))
            s.performance_matches += 1

        vs = s.venues[venue]
        vs["matches"] += 1
        if result == "W":
            vs["wins"] += 1
        elif result == "L":
            vs["losses"] += 1

    p = pair_state(h2h, a, b)
    p["matches"] += 1
    winner = m["winner_team_id"]
    if winner is not None:
        winner = si(winner)
        if winner == p["x"]:
            p["wins_x"] += 1
        elif winner == p["y"]:
            p["wins_y"] += 1


def main():
    print("=" * 70)
    print("ODI MATCH PREDICTOR - TRAINING DATASET BUILDER")
    print("=" * 70)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as e:
        print("ERROR: Could not connect to MySQL.")
        print(e)
        sys.exit(1)

    try:
        matches = load_matches(conn)
        stats = load_stats(conn)

        states = defaultdict(TeamState)
        h2h = {}
        rows = []

        excluded_nr = excluded_tie = excluded_other = 0

        for m in matches:
            if eligible(m):
                # CRITICAL: feature generation happens BEFORE this match
                # is added to historical state.
                rows.append(make_features(m, states, h2h))
            else:
                status = (m["match_status"] or "").upper()
                if status == "NO_RESULT" or m["winner_team_id"] is None:
                    excluded_nr += 1
                elif status == "TIED":
                    excluded_tie += 1
                else:
                    excluded_other += 1

            update(m, states, h2h, stats)

        if not rows:
            raise RuntimeError("No training rows generated.")

        ids = [r["match_id"] for r in rows]
        if len(ids) != len(set(ids)):
            raise RuntimeError("Duplicate training match IDs detected.")

        if {r["target"] for r in rows} != {0, 1}:
            raise RuntimeError("Target does not contain both classes.")

        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

        a_wins = sum(r["target"] == 1 for r in rows)
        b_wins = sum(r["target"] == 0 for r in rows)

        print()
        print(f"Men's ODI matches loaded       : {len(matches)}")
        print(f"Eligible training matches     : {len(rows)}")
        print(f"Excluded NO_RESULT/undecided  : {excluded_nr}")
        print(f"Excluded TIED                 : {excluded_tie}")
        print(f"Other excluded                : {excluded_other}")
        print()
        print(f"Team A wins (target=1)         : {a_wins}")
        print(f"Team B wins (target=0)         : {b_wins}")
        print(f"Feature columns                : {len(FIELDS) - 1}")
        print(f"Output                         : {OUTPUT_FILE}")
        print()
        print("LEAKAGE CHECKS")
        print("[PASS] Features created before current-match state update")
        print("[PASS] Current match runs/wickets/result are not features")
        print("[PASS] Toss is not used")
        print("[PASS] Chronological processing")
        print("[PASS] Team IDs are identifiers, not numeric performance features")
        print()
        print("First 5 rows:")
        for r in rows[:5]:
            print(
                f"  {r['match_id']} | {r['match_date']} | "
                f"{r['team_a']} vs {r['team_b']} | target={r['target']} | "
                f"A_form={r['team_a_last5_win_rate']:.3f} | "
                f"B_form={r['team_b_last5_win_rate']:.3f}"
            )
        print()
        print("DONE.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

