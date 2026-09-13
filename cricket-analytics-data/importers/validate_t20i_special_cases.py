import json
import zipfile
from pathlib import Path
from collections import Counter


# ============================================================
# CONFIGURATION
# ============================================================

ZIP_PATH = Path(
    r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"
)


# ============================================================
# HELPERS
# ============================================================

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def get_match_id(member):
    return Path(member).stem


def format_teams(info):
    teams = info.get("teams", [])
    return " vs ".join(teams)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 90)
    print("T20 INTERNATIONAL SPECIAL-CASE AUDIT")
    print("=" * 90)

    if not ZIP_PATH.exists():
        print("\nERROR: ZIP file not found:")
        print(ZIP_PATH)
        return

    # --------------------------------------------------------
    # Collections
    # --------------------------------------------------------

    tied_matches = []
    tied_without_super_over = []

    no_result_matches = []

    super_over_matches = []
    multiple_super_over_matches = []

    one_innings_matches = []
    four_innings_matches = []
    eight_innings_matches = []

    super_over_innings_counter = Counter()

    total_super_over_deliveries = 0
    total_super_over_runs = 0

    # --------------------------------------------------------
    # Read ZIP
    # --------------------------------------------------------

    with zipfile.ZipFile(ZIP_PATH, "r") as z:

        members = [
            name
            for name in z.namelist()
            if name.lower().endswith(".json")
        ]

        for member in members:

            try:
                with z.open(member) as f:
                    data = json.load(f)
            except Exception:
                continue

            info = data.get("info", {})
            match_id = get_match_id(member)

            teams = info.get("teams", [])
            dates = info.get("dates", [])
            season = info.get("season")

            if isinstance(dates, list):
                match_date = dates[0] if dates else "UNKNOWN"
            else:
                match_date = dates or "UNKNOWN"

            outcome = info.get("outcome", {})

            result = outcome.get("result")
            winner = outcome.get("winner")
            eliminator = outcome.get("eliminator")

            innings = data.get("innings", [])

            # ------------------------------------------------
            # Basic metadata
            # ------------------------------------------------

            if result == "tie":
                tied_matches.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "winner": winner,
                    "eliminator": eliminator,
                    "innings": len(innings)
                })

            if result == "no result":
                no_result_matches.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "innings": len(innings)
                })

            # ------------------------------------------------
            # Innings analysis
            # ------------------------------------------------

            super_over_count = 0
            match_super_over_deliveries = 0
            match_super_over_runs = 0

            for innings_data in innings:

                is_super_over = bool(
                    innings_data.get("super_over", False)
                )

                if is_super_over:

                    super_over_count += 1

                    overs = innings_data.get("overs", [])

                    for over in overs:

                        for delivery in over.get("deliveries", []):

                            match_super_over_deliveries += 1

                            runs = delivery.get("runs", {})

                            match_super_over_runs += safe_int(
                                runs.get("total", 0)
                            )

            super_over_innings_counter[super_over_count] += 1

            if super_over_count > 0:

                super_over_matches.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "result": result,
                    "winner": winner,
                    "eliminator": eliminator,
                    "innings": len(innings),
                    "super_over_innings": super_over_count,
                    "super_over_deliveries": match_super_over_deliveries,
                    "super_over_runs": match_super_over_runs
                })

                total_super_over_deliveries += (
                    match_super_over_deliveries
                )

                total_super_over_runs += (
                    match_super_over_runs
                )

                if super_over_count > 1:

                    multiple_super_over_matches.append({
                        "id": match_id,
                        "date": match_date,
                        "season": season,
                        "teams": teams,
                        "result": result,
                        "winner": winner,
                        "eliminator": eliminator,
                        "innings": len(innings),
                        "super_over_innings": super_over_count,
                        "super_over_deliveries": match_super_over_deliveries,
                        "super_over_runs": match_super_over_runs
                    })

            # ------------------------------------------------
            # Tied without Super Over
            # ------------------------------------------------

            if result == "tie" and super_over_count == 0:

                tied_without_super_over.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "winner": winner,
                    "eliminator": eliminator,
                    "innings": len(innings)
                })

            # ------------------------------------------------
            # Unusual innings counts
            # ------------------------------------------------

            if len(innings) == 1:

                one_innings_matches.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "result": result,
                    "winner": winner,
                    "innings": len(innings)
                })

            elif len(innings) == 4:

                four_innings_matches.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "result": result,
                    "winner": winner,
                    "eliminator": eliminator,
                    "innings": len(innings),
                    "super_over_innings": super_over_count
                })

            elif len(innings) == 8:

                eight_innings_matches.append({
                    "id": match_id,
                    "date": match_date,
                    "season": season,
                    "teams": teams,
                    "result": result,
                    "winner": winner,
                    "eliminator": eliminator,
                    "innings": len(innings),
                    "super_over_innings": super_over_count
                })

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n" + "=" * 90)
    print("SPECIAL-CASE SUMMARY")
    print("=" * 90)

    print(
        f"\nTied matches:                    "
        f"{len(tied_matches)}"
    )

    print(
        f"Tied without Super Over:        "
        f"{len(tied_without_super_over)}"
    )

    print(
        f"No-result matches:              "
        f"{len(no_result_matches)}"
    )

    print(
        f"Matches with Super Over:        "
        f"{len(super_over_matches)}"
    )

    print(
        f"Multiple Super Over matches:    "
        f"{len(multiple_super_over_matches)}"
    )

    print(
        f"One-innings matches:             "
        f"{len(one_innings_matches)}"
    )

    print(
        f"Four-innings matches:            "
        f"{len(four_innings_matches)}"
    )

    print(
        f"Eight-innings matches:           "
        f"{len(eight_innings_matches)}"
    )

    print(
        f"\nSuper Over deliveries:           "
        f"{total_super_over_deliveries:,}"
    )

    print(
        f"Super Over runs:                 "
        f"{total_super_over_runs:,}"
    )

    # ========================================================
    # SUPER OVER INNINGS DISTRIBUTION
    # ========================================================

    print("\n" + "=" * 90)
    print("SUPER OVER INNINGS DISTRIBUTION")
    print("=" * 90)

    for count, matches in sorted(super_over_innings_counter.items()):

        print(
            f"{count} Super Over innings: "
            f"{matches} matches"
        )

    # ========================================================
    # TIED MATCHES
    # ========================================================

    print("\n" + "=" * 90)
    print("ALL TIED MATCHES")
    print("=" * 90)

    for item in tied_matches:

        print(
            f"{item['id']} | "
            f"{item['date']} | "
            f"{item['season']} | "
            f"{format_teams({'teams': item['teams']})} | "
            f"winner={item['winner']} | "
            f"eliminator={item['eliminator']} | "
            f"innings={item['innings']}"
        )

    # ========================================================
    # TIES WITHOUT SUPER OVER
    # ========================================================

    print("\n" + "=" * 90)
    print("TIED MATCHES WITHOUT SUPER OVER")
    print("=" * 90)

    if not tied_without_super_over:

        print("None")

    else:

        for item in tied_without_super_over:

            print(
                f"{item['id']} | "
                f"{item['date']} | "
                f"{item['season']} | "
                f"{format_teams({'teams': item['teams']})} | "
                f"winner={item['winner']} | "
                f"eliminator={item['eliminator']} | "
                f"innings={item['innings']}"
            )

    # ========================================================
    # MULTIPLE SUPER OVERS
    # ========================================================

    print("\n" + "=" * 90)
    print("MULTIPLE SUPER OVER MATCHES")
    print("=" * 90)

    if not multiple_super_over_matches:

        print("None")

    else:

        for item in multiple_super_over_matches:

            print(
                f"{item['id']} | "
                f"{item['date']} | "
                f"{item['season']} | "
                f"{format_teams({'teams': item['teams']})} | "
                f"winner={item['winner']} | "
                f"eliminator={item['eliminator']} | "
                f"innings={item['innings']} | "
                f"SO innings={item['super_over_innings']} | "
                f"SO deliveries={item['super_over_deliveries']} | "
                f"SO runs={item['super_over_runs']}"
            )

    # ========================================================
    # ONE-INNINGS MATCHES
    # ========================================================

    print("\n" + "=" * 90)
    print("ONE-INNINGS MATCHES")
    print("=" * 90)

    if not one_innings_matches:

        print("None")

    else:

        for item in one_innings_matches:

            print(
                f"{item['id']} | "
                f"{item['date']} | "
                f"{item['season']} | "
                f"{format_teams({'teams': item['teams']})} | "
                f"result={item['result']} | "
                f"winner={item['winner']}"
            )

    # ========================================================
    # FOUR-INNINGS MATCHES
    # ========================================================

    print("\n" + "=" * 90)
    print("FOUR-INNINGS MATCHES")
    print("=" * 90)

    for item in four_innings_matches:

        print(
            f"{item['id']} | "
            f"{item['date']} | "
            f"{item['season']} | "
            f"{format_teams({'teams': item['teams']})} | "
            f"result={item['result']} | "
            f"winner={item['winner']} | "
            f"eliminator={item['eliminator']} | "
            f"SO innings={item['super_over_innings']}"
        )

    # ========================================================
    # EIGHT-INNINGS MATCHES
    # ========================================================

    print("\n" + "=" * 90)
    print("EIGHT-INNINGS MATCHES")
    print("=" * 90)

    if not eight_innings_matches:

        print("None")

    else:

        for item in eight_innings_matches:

            print(
                f"{item['id']} | "
                f"{item['date']} | "
                f"{item['season']} | "
                f"{format_teams({'teams': item['teams']})} | "
                f"result={item['result']} | "
                f"winner={item['winner']} | "
                f"eliminator={item['eliminator']} | "
                f"SO innings={item['super_over_innings']}"
            )

    # ========================================================
    # NO RESULTS
    # ========================================================

    print("\n" + "=" * 90)
    print("NO-RESULT MATCHES")
    print("=" * 90)

    for item in no_result_matches:

        print(
            f"{item['id']} | "
            f"{item['date']} | "
            f"{item['season']} | "
            f"{format_teams({'teams': item['teams']})} | "
            f"innings={item['innings']}"
        )

    # ========================================================
    # FINAL CONSISTENCY CHECKS
    # ========================================================

    print("\n" + "=" * 90)
    print("CONSISTENCY CHECKS")
    print("=" * 90)

    checks = []

    checks.append((
        "Tied matches identified",
        len(tied_matches) == 51
    ))

    checks.append((
        "No-result matches identified",
        len(no_result_matches) == 113
    ))

    checks.append((
        "Super Over matches identified",
        len(super_over_matches) == 46
    ))

    checks.append((
        "Super Over eliminators match Super Over count",
        len(super_over_matches)
        == len([m for m in tied_matches if m["eliminator"]])
    ))

    checks.append((
        "At least one unusual innings case exists",
        len(one_innings_matches)
        + len(four_innings_matches)
        + len(eight_innings_matches)
        > 0
    ))

    for name, passed in checks:

        print(
            f"[{'PASS' if passed else 'FAIL'}] "
            f"{name}"
        )

    print("\n" + "=" * 90)

    if all(passed for _, passed in checks):

        print("T20I SPECIAL-CASE AUDIT: PASS")

    else:

        print("T20I SPECIAL-CASE AUDIT: REVIEW REQUIRED")

    print("=" * 90)


if __name__ == "__main__":
    main()