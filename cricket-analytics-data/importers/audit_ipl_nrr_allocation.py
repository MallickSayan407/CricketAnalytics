import csv
import json
import zipfile
from pathlib import Path


BASE_DIR = Path(r"D:\CricketAnalytics\cricket-analytics-data")

ZIP_PATH = BASE_DIR / "raw" / "ipl" / "ipl_json.zip"

MATCH_STATS_PATH = (
    BASE_DIR
    / "processed"
    / "ipl"
    / "match_team_stats.csv"
)


TEAM_NORMALIZATION = {
    "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    "Royal Challengers Bengaluru": "Royal Challengers Bengaluru",

    "Kings XI Punjab": "Punjab Kings",
    "Punjab Kings": "Punjab Kings",

    "Delhi Daredevils": "Delhi Capitals",
    "Delhi Capitals": "Delhi Capitals",

    "Deccan Chargers": "Deccan Chargers",

    "Gujarat Lions": "Gujarat Lions",
    "Gujarat Titans": "Gujarat Titans",

    "Rising Pune Supergiant": "Rising Pune Supergiant",
    "Rising Pune Supergiants": "Rising Pune Supergiant",

    "Pune Warriors": "Pune Warriors",

    "Kochi Tuskers Kerala": "Kochi Tuskers Kerala",

    "Mumbai Indians": "Mumbai Indians",
    "Kolkata Knight Riders": "Kolkata Knight Riders",
    "Chennai Super Kings": "Chennai Super Kings",
    "Rajasthan Royals": "Rajasthan Royals",
    "Sunrisers Hyderabad": "Sunrisers Hyderabad",
    "Lucknow Super Giants": "Lucknow Super Giants",
}


def normalize_team(name):
    return TEAM_NORMALIZATION.get(name, name)


def is_super_over(innings):
    return bool(
        innings.get("super_over", False)
    )


def is_legal_delivery(delivery):
    extras = delivery.get("extras", {})

    return (
        "wides" not in extras
        and "noballs" not in extras
    )


def safe_int(value):
    if value is None:
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def count_actual_legal_balls(innings):
    total = 0

    for over in innings.get("overs", []):

        for delivery in over.get("deliveries", []):

            if is_legal_delivery(delivery):
                total += 1

    return total


def count_wickets(innings):
    total = 0

    for over in innings.get("overs", []):

        for delivery in over.get("deliveries", []):

            total += len(
                delivery.get("wickets", [])
            )

    return total


def count_innings_runs(innings):
    total = 0

    for over in innings.get("overs", []):

        for delivery in over.get("deliveries", []):

            runs = delivery.get(
                "runs",
                {}
            )

            total += safe_int(
                runs.get("total")
            )

    return total


def expected_allocated_balls(
    innings,
    innings_index,
    scheduled_overs
):
    """
    Expected NRR denominator according to the
    allocation rules used by the IPL processor.

    Rules:

    1. Normal full innings:
       scheduled overs × 6.

    2. First innings reduced before all-out:
       actual legal balls faced.

    3. First innings all-out before quota:
       full scheduled quota.

    4. Second innings with a target:
       - if target is successfully reached:
         actual legal balls faced.
       - otherwise:
         target overs × 6.

    5. Safety fallback:
       actual legal balls if a valid allocation
       cannot otherwise be determined.
    """

    scheduled_balls = (
        safe_int(scheduled_overs) * 6
    )

    actual_legal_balls = count_actual_legal_balls(
        innings
    )

    wickets = count_wickets(
        innings
    )

    innings_runs = count_innings_runs(
        innings
    )

    # ------------------------------------------------------------------
    # SECOND INNINGS / CHASE
    # ------------------------------------------------------------------

    target = innings.get("target")

    if isinstance(target, dict):

        target_overs = target.get(
            "overs"
        )

        target_runs = target.get(
            "runs"
        )

        target_overs_balls = None

        if target_overs is not None:
            target_overs_balls = (
                safe_int(target_overs) * 6
            )

        # Successful chase:
        # use actual legal balls faced.
        if (
            target_runs is not None
            and innings_runs >= safe_int(target_runs)
            and actual_legal_balls > 0
        ):
            return actual_legal_balls

        # Unsuccessful reduced-over chase:
        # use the target's allocated quota.
        if target_overs_balls is not None:
            return target_overs_balls

    # ------------------------------------------------------------------
    # FIRST INNINGS / REDUCED OVERS
    # ------------------------------------------------------------------

    if (
        innings_index == 0
        and actual_legal_balls > 0
        and actual_legal_balls < scheduled_balls
        and wickets < 10
    ):
        return actual_legal_balls

    # ------------------------------------------------------------------
    # NORMAL / ALL-OUT INNINGS
    # ------------------------------------------------------------------

    if scheduled_balls > 0:
        return scheduled_balls

    # Safety fallback.
    return actual_legal_balls


def load_processed_stats():

    result = {}

    with MATCH_STATS_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            key = (
                row["match_id"],
                row["team_name"]
            )

            result[key] = {
                "total_balls": safe_int(
                    row["total_balls"]
                ),

                "allocated_balls": safe_int(
                    row["allocated_balls"]
                ),

                "runs": safe_int(
                    row["runs"]
                ),

                "wickets": safe_int(
                    row["wickets"]
                ),
            }

    return result


def main():

    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL NRR ALLOCATION AUDIT")
    print("=" * 80)

    processed = load_processed_stats()

    audited_matches = []
    mismatches = []

    successful_chases = 0
    reduced_first_innings = 0
    all_out_before_quota = 0
    reduced_chases = 0

    with zipfile.ZipFile(
        ZIP_PATH,
        "r"
    ) as z:

        json_files = [
            name
            for name in z.namelist()
            if name.lower().endswith(".json")
        ]

        for filename in json_files:

            with z.open(filename) as f:

                data = json.load(f)

            info = data.get(
                "info",
                {}
            )

            scheduled_overs = info.get(
                "overs",
                20
            )

            innings_list = [
                innings
                for innings in data.get(
                    "innings",
                    []
                )
                if not is_super_over(innings)
            ]

            if not innings_list:
                continue

            match_id = str(
                info.get("registry", {})
                .get("data", {})
                .get("id", "")
            )

            # Cricsheet files use their filename as
            # the match ID when registry ID is unavailable.
            if not match_id:
                match_id = Path(
                    filename
                ).stem

            match_requires_audit = False

            # ----------------------------------------------------------
            # Determine whether this match contains a reduced-over
            # situation.
            # ----------------------------------------------------------

            for innings_index, innings in enumerate(
                innings_list
            ):

                actual_legal_balls = (
                    count_actual_legal_balls(
                        innings
                    )
                )

                wickets = count_wickets(
                    innings
                )

                target = innings.get(
                    "target"
                )

                target_overs = None

                if isinstance(target, dict):

                    if target.get("overs") is not None:

                        target_overs = safe_int(
                            target.get("overs")
                        )

                        if target_overs != safe_int(
                            scheduled_overs
                        ):
                            match_requires_audit = True
                            reduced_chases += 1

                    target_runs = target.get(
                        "runs"
                    )

                    innings_runs = count_innings_runs(
                        innings
                    )

                    # Successful chase.
                    if (
                        target_runs is not None
                        and innings_runs >= safe_int(
                            target_runs
                        )
                    ):
                        successful_chases += 1

                        if actual_legal_balls < (
                            safe_int(scheduled_overs) * 6
                        ):
                            match_requires_audit = True

                # First innings reduced before all-out.
                if (
                    innings_index == 0
                    and actual_legal_balls > 0
                    and actual_legal_balls < (
                        safe_int(scheduled_overs) * 6
                    )
                    and wickets < 10
                ):
                    match_requires_audit = True
                    reduced_first_innings += 1

                # First innings all-out before full quota.
                if (
                    actual_legal_balls > 0
                    and actual_legal_balls < (
                        safe_int(scheduled_overs) * 6
                    )
                    and wickets >= 10
                ):
                    all_out_before_quota += 1

            if not match_requires_audit:
                continue

            audited_matches.append(
                match_id
            )

            # ----------------------------------------------------------
            # Compare every normal innings against processed CSV.
            # ----------------------------------------------------------

            for innings_index, innings in enumerate(
                innings_list
            ):

                team = normalize_team(
                    innings.get("team", "")
                )

                expected = expected_allocated_balls(
                    innings,
                    innings_index,
                    scheduled_overs
                )

                key = (
                    match_id,
                    team
                )

                actual_row = processed.get(
                    key
                )

                if actual_row is None:

                    mismatches.append({
                        "match_id": match_id,
                        "team": team,
                        "expected": expected,
                        "actual": "MISSING",
                        "reason": "No processed CSV row"
                    })

                    continue

                actual = actual_row[
                    "allocated_balls"
                ]

                if actual != expected:

                    mismatches.append({
                        "match_id": match_id,
                        "team": team,
                        "expected": expected,
                        "actual": actual,
                        "total_balls": actual_row[
                            "total_balls"
                        ],
                        "runs": actual_row[
                            "runs"
                        ],
                        "wickets": actual_row[
                            "wickets"
                        ],
                        "reason": "Allocation mismatch"
                    })

    print()
    print("NRR ALLOCATION AUDIT")
    print("-" * 80)

    print(
        f"Matches requiring audit: "
        f"{len(set(audited_matches))}"
    )

    print(
        f"Successful/reduced chases detected: "
        f"{successful_chases}"
    )

    print(
        f"Reduced first innings detected: "
        f"{reduced_first_innings}"
    )

    print(
        f"All-out before full quota detected: "
        f"{all_out_before_quota}"
    )

    print()
    print("MISMATCHES")
    print("-" * 80)

    if not mismatches:

        print(
            "No allocation mismatches found."
        )

    else:

        for mismatch in mismatches:

            print(mismatch)

    print()
    print("=" * 80)

    if mismatches:

        print(
            "NRR ALLOCATION AUDIT: FAIL"
        )

    else:

        print(
            "NRR ALLOCATION AUDIT: PASS"
        )

    print("=" * 80)


if __name__ == "__main__":
    main()