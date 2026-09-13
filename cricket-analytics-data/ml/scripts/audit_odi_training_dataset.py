import csv
import sys
from collections import Counter
from pathlib import Path
from datetime import datetime


CSV_FILE = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\ml\datasets\odi_match_training.csv"
)


# Columns that identify the match but should NOT be fed directly to the ML model.
IDENTIFIER_COLUMNS = {
    "match_id",
    "external_id",
    "match_date",
    "team_a_id",
    "team_a",
    "team_b_id",
    "team_b",
    "venue_id",
    "venue",
    "target",
}


# These are the actual pre-match numerical features.
FEATURE_COLUMNS = {
    "team_a_matches_before",
    "team_a_wins_before",
    "team_a_decided_matches_before",
    "team_a_win_rate",
    "team_a_last5_win_rate",
    "team_a_last10_win_rate",
    "team_a_avg_runs",
    "team_a_avg_wickets",

    "team_b_matches_before",
    "team_b_wins_before",
    "team_b_decided_matches_before",
    "team_b_win_rate",
    "team_b_last5_win_rate",
    "team_b_last10_win_rate",
    "team_b_avg_runs",
    "team_b_avg_wickets",

    "team_a_venue_matches_before",
    "team_a_venue_win_rate",
    "team_b_venue_matches_before",
    "team_b_venue_win_rate",

    "head_to_head_matches_before",
    "head_to_head_a_wins",
    "head_to_head_b_wins",
    "head_to_head_a_win_rate",
    "head_to_head_b_win_rate",
}


def fail(message):
    print()
    print("FAIL:", message)
    sys.exit(1)


def main():
    print("=" * 72)
    print("ODI MATCH PREDICTOR - TRAINING DATASET AUDIT")
    print("=" * 72)
    print()

    if not CSV_FILE.exists():
        fail(f"CSV file not found:\n{CSV_FILE}")

    print("Input:")
    print(CSV_FILE)
    print()

    with CSV_FILE.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        columns = reader.fieldnames or []

    print(f"Rows loaded       : {len(rows)}")
    print(f"Columns loaded    : {len(columns)}")
    print()

    # ---------------------------------------------------------
    # 1. Basic structure
    # ---------------------------------------------------------

    required_columns = (
        IDENTIFIER_COLUMNS
        | FEATURE_COLUMNS
    )

    missing_columns = sorted(
        required_columns - set(columns)
    )

    if missing_columns:
        fail(
            "Required columns are missing:\n"
            + "\n".join(f"  - {x}" for x in missing_columns)
        )

    print("[PASS] Required columns present")

    # ---------------------------------------------------------
    # 2. Row count
    # ---------------------------------------------------------

    if len(rows) != 2440:
        print(
            f"[WARNING] Expected approximately 2440 rows, "
            f"found {len(rows)}"
        )
    else:
        print("[PASS] Row count = 2440")

    # ---------------------------------------------------------
    # 3. Duplicate match IDs
    # ---------------------------------------------------------

    match_ids = [
        row["match_id"]
        for row in rows
    ]

    duplicate_ids = [
        match_id
        for match_id, count in Counter(match_ids).items()
        if count > 1
    ]

    if duplicate_ids:
        fail(
            "Duplicate match IDs detected: "
            + ", ".join(duplicate_ids[:10])
        )

    print("[PASS] Duplicate match IDs = 0")

    # ---------------------------------------------------------
    # 4. Missing values
    # ---------------------------------------------------------

    missing = {}

    for column in columns:
        count = sum(
            1
            for row in rows
            if row.get(column, "").strip() == ""
        )

        if count:
            missing[column] = count

    if missing:
        print("[WARNING] Missing values found:")
        for column, count in missing.items():
            print(f"  {column}: {count}")
    else:
        print("[PASS] No missing values")

    # ---------------------------------------------------------
    # 5. Target validation
    # ---------------------------------------------------------

    targets = []

    for row in rows:
        try:
            target = int(row["target"])
        except ValueError:
            fail(
                f"Invalid target for match {row['match_id']}"
            )

        targets.append(target)

    invalid_targets = [
        target
        for target in targets
        if target not in (0, 1)
    ]

    if invalid_targets:
        fail(
            f"Invalid target values detected: "
            f"{set(invalid_targets)}"
        )

    target_0 = targets.count(0)
    target_1 = targets.count(1)

    print("[PASS] Target contains only 0 and 1")
    print(f"       Team B wins (0): {target_0}")
    print(f"       Team A wins (1): {target_1}")

    # ---------------------------------------------------------
    # 6. Target balance
    # ---------------------------------------------------------

    total = len(targets)

    pct_0 = target_0 / total * 100
    pct_1 = target_1 / total * 100

    print()
    print("TARGET BALANCE")
    print(f"  Team B: {pct_0:.2f}%")
    print(f"  Team A: {pct_1:.2f}%")

    if abs(pct_0 - pct_1) > 25:
        print("[WARNING] Target classes are substantially imbalanced")
    else:
        print("[PASS] Target balance is reasonable")

    # ---------------------------------------------------------
    # 7. Date ordering
    # ---------------------------------------------------------

    parsed_dates = []

    for row in rows:
        try:
            parsed_dates.append(
                (
                    datetime.strptime(
                        row["match_date"],
                        "%Y-%m-%d",
                    ).date(),
                    int(row["match_id"]),
                )
            )
        except Exception:
            fail(
                f"Invalid date for match {row['match_id']}: "
                f"{row['match_date']}"
            )

    if parsed_dates != sorted(parsed_dates):
        fail("Rows are not chronologically ordered")

    print("[PASS] Rows are chronologically ordered")

    # ---------------------------------------------------------
    # 8. Historical feature sanity checks
    # ---------------------------------------------------------

    numeric_columns = sorted(FEATURE_COLUMNS)

    numeric_errors = []

    for row in rows:
        for column in numeric_columns:
            try:
                value = float(row[column])
            except ValueError:
                numeric_errors.append(
                    (row["match_id"], column, row[column])
                )
                continue

            if value != value:  # NaN
                numeric_errors.append(
                    (row["match_id"], column, "NaN")
                )

    if numeric_errors:
        print("[WARNING] Numeric parsing problems:")
        for item in numeric_errors[:10]:
            print(" ", item)
    else:
        print("[PASS] All model features are numeric")

    # ---------------------------------------------------------
    # 9. Rate range checks
    # ---------------------------------------------------------

    rate_columns = [
        column
        for column in FEATURE_COLUMNS
        if "rate" in column
    ]

    bad_rates = []

    for row in rows:
        for column in rate_columns:
            value = float(row[column])

            if value < 0 or value > 1:
                bad_rates.append(
                    (
                        row["match_id"],
                        column,
                        value,
                    )
                )

    if bad_rates:
        fail(
            "Win-rate feature outside [0,1]:\n"
            + "\n".join(
                str(x)
                for x in bad_rates[:10]
            )
        )

    print("[PASS] Win-rate features are within [0,1]")

    # ---------------------------------------------------------
    # 10. Historical count checks
    # ---------------------------------------------------------

    count_columns = [
        "team_a_matches_before",
        "team_a_wins_before",
        "team_a_decided_matches_before",
        "team_b_matches_before",
        "team_b_wins_before",
        "team_b_decided_matches_before",
        "team_a_venue_matches_before",
        "team_b_venue_matches_before",
        "head_to_head_matches_before",
        "head_to_head_a_wins",
        "head_to_head_b_wins",
    ]

    bad_counts = []

    for row in rows:
        for column in count_columns:
            value = int(float(row[column]))

            if value < 0:
                bad_counts.append(
                    (
                        row["match_id"],
                        column,
                        value,
                    )
                )

    if bad_counts:
        fail(
            "Negative historical counts detected"
        )

    print("[PASS] Historical count features are non-negative")

    # ---------------------------------------------------------
    # 11. Logical historical checks
    # ---------------------------------------------------------

    logical_errors = []

    for row in rows:
        match_id = row["match_id"]

        a_matches = int(row["team_a_matches_before"])
        b_matches = int(row["team_b_matches_before"])

        a_wins = int(row["team_a_wins_before"])
        b_wins = int(row["team_b_wins_before"])

        a_decided = int(
            row["team_a_decided_matches_before"]
        )
        b_decided = int(
            row["team_b_decided_matches_before"]
        )

        h2h = int(
            row["head_to_head_matches_before"]
        )

        h2h_a = int(
            row["head_to_head_a_wins"]
        )

        h2h_b = int(
            row["head_to_head_b_wins"]
        )

        if a_wins > a_decided:
            logical_errors.append(
                (match_id, "A wins > A decided matches")
            )

        if b_wins > b_decided:
            logical_errors.append(
                (match_id, "B wins > B decided matches")
            )

        if a_decided > a_matches:
            logical_errors.append(
                (match_id, "A decided matches > A matches")
            )

        if b_decided > b_matches:
            logical_errors.append(
                (match_id, "B decided matches > B matches")
            )

        if h2h_a + h2h_b > h2h:
            logical_errors.append(
                (match_id, "H2H wins > H2H matches")
            )

    if logical_errors:
        fail(
            "Logical historical-feature errors:\n"
            + "\n".join(
                str(x)
                for x in logical_errors[:10]
            )
        )

    print("[PASS] Historical feature relationships are valid")

    # ---------------------------------------------------------
    # 12. First-row leakage sanity check
    # ---------------------------------------------------------

    first = rows[0]

    print()
    print("FIRST TRAINING MATCH")
    print(
        f"  Match      : {first['match_id']}"
    )
    print(
        f"  Date       : {first['match_date']}"
    )
    print(
        f"  Teams      : {first['team_a']} vs {first['team_b']}"
    )
    print(
        f"  A matches before : {first['team_a_matches_before']}"
    )
    print(
        f"  B matches before : {first['team_b_matches_before']}"
    )

    if (
        int(first["team_a_matches_before"]) == 0
        or int(first["team_b_matches_before"]) == 0
    ):
        print("[PASS] First training row has a team with zero history")
    else:
        print(
            "[WARNING] First training row has no zero-history team"
        )

    # ---------------------------------------------------------
    # 13. Explicit leakage-column scan
    # ---------------------------------------------------------

    forbidden_keywords = [
        "runs",
        "wickets",
        "strike",
        "result",
        "winner",
        "toss",
        "score",
        "balls",
        "fours",
        "sixes",
        "economy",
    ]

    suspicious = []

    for column in FEATURE_COLUMNS:
        lower = column.lower()

        # Average historical runs/wickets are allowed.
        if column in (
            "team_a_avg_runs",
            "team_b_avg_runs",
            "team_a_avg_wickets",
            "team_b_avg_wickets",
        ):
            continue

        for keyword in forbidden_keywords:
            if keyword in lower:
                suspicious.append(column)
                break

    if suspicious:
        print(
            "[WARNING] Feature names deserve manual leakage review:"
        )
        for column in sorted(set(suspicious)):
            print(f"  {column}")
    else:
        print("[PASS] No obvious current-match leakage columns")

    # ---------------------------------------------------------
    # 14. Feature ranges
    # ---------------------------------------------------------

    print()
    print("FEATURE RANGE SUMMARY")
    print("-" * 72)

    for column in sorted(FEATURE_COLUMNS):
        values = [
            float(row[column])
            for row in rows
        ]

        print(
            f"{column:38s} "
            f"min={min(values):10.4f} "
            f"max={max(values):10.4f}"
        )

    # ---------------------------------------------------------
    # 15. Final verdict
    # ---------------------------------------------------------

    print()
    print("=" * 72)
    print("FINAL DATASET AUDIT")
    print("=" * 72)

    if (
        not duplicate_ids
        and not invalid_targets
        and not bad_rates
        and not bad_counts
        and not logical_errors
    ):
        print("PASS: ODI training dataset is structurally ready for ML.")
    else:
        print("FAIL: Dataset requires correction before ML training.")

    print()
    print("Next step:")
    print("  Train chronological Logistic Regression,")
    print("  Random Forest and XGBoost models.")
    print()


if __name__ == "__main__":
    main()