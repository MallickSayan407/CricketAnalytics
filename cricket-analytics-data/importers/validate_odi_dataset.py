import json
import zipfile
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ZIP_PATH = (
    BASE_DIR
    / "raw"
    / "international"
    / "odis_json.zip"
)


def validate_dataset():

    if not ZIP_PATH.exists():
        print("ERROR: ODI dataset not found:")
        print(ZIP_PATH)
        return

    print("=" * 80)
    print("CRICSHEET ODI DATASET VALIDATION")
    print("=" * 80)

    match_type_counter = Counter()
    gender_counter = Counter()
    team_counter = Counter()
    venue_counter = Counter()

    innings_count_counter = Counter()

    matches_with_no_result = []
    matches_with_tie = []
    matches_with_super_over = []

    unusual_innings = []
    delivery_edge_cases = Counter()
    wicket_types = Counter()

    total_matches = 0
    total_deliveries = 0
    total_overs = 0

    total_batter_runs = 0
    total_extra_runs = 0
    total_runs = 0

    print("\nReading ODI archive...")
    print(ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        json_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        print(f"\nJSON matches found: {len(json_files)}")

        for index, file_name in enumerate(json_files, start=1):

            try:

                with archive.open(file_name) as file:
                    match = json.load(file)

                total_matches += 1

                info = match.get("info", {})

                match_type_counter[
                    str(info.get("match_type"))
                ] += 1

                gender_counter[
                    str(info.get("gender"))
                ] += 1

                teams = info.get("teams", [])

                for team in teams:
                    team_counter[team] += 1

                venue = info.get("venue")

                if venue:
                    venue_counter[venue] += 1

                outcome = info.get("outcome", {})

                if not outcome:
                    matches_with_no_result.append(file_name)

                if "winner" not in outcome:
                    matches_with_no_result.append(file_name)

                if "winner" in outcome and "result" in outcome:
                    matches_with_tie.append(file_name)

                innings = match.get("innings", [])

                innings_count_counter[len(innings)] += 1

                if len(innings) != 2:
                    unusual_innings.append(
                        {
                            "file": file_name,
                            "innings": len(innings)
                        }
                    )

                match_has_super_over = False

                for innings_data in innings:

                    overs = innings_data.get("overs", [])

                    total_overs += len(overs)

                    for over in overs:

                        deliveries = over.get("deliveries", [])

                        for delivery in deliveries:

                            total_deliveries += 1

                            runs = delivery.get("runs", {})

                            batter_runs = runs.get(
                                "batter",
                                0
                            )

                            extra_runs = runs.get(
                                "extras",
                                0
                            )

                            total_delivery_runs = runs.get(
                                "total",
                                0
                            )

                            total_batter_runs += batter_runs
                            total_extra_runs += extra_runs
                            total_runs += total_delivery_runs

                            extras = delivery.get(
                                "extras",
                                {}
                            )

                            for extra_type in extras.keys():
                                delivery_edge_cases[
                                    f"extra:{extra_type}"
                                ] += 1

                            if "wickets" in delivery:

                                wickets = delivery.get(
                                    "wickets",
                                    []
                                )

                                for wicket in wickets:

                                    dismissal = wicket.get(
                                        "kind",
                                        "UNKNOWN"
                                    )

                                    wicket_types[dismissal] += 1

                            if "replacements" in delivery:
                                delivery_edge_cases[
                                    "replacements"
                                ] += 1

                            if delivery.get(
                                "review"
                            ) is not None:

                                delivery_edge_cases[
                                    "reviews"
                                ] += 1

                # Check whether this is a special innings/match
                # structure involving a super over.
                for innings_data in innings:

                    team = innings_data.get("team", "")

                    if "super" in team.lower():
                        match_has_super_over = True

                if match_has_super_over:
                    matches_with_super_over.append(
                        file_name
                    )

            except Exception as error:

                print(
                    f"\nERROR processing {file_name}:"
                )

                print(error)

            if index % 250 == 0:

                print(
                    f"Processed {index}/{len(json_files)} matches..."
                )

    print("\n")
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    print("\nTotal matches:")
    print(total_matches)

    print("\nMatch types:")
    for key, value in match_type_counter.most_common():
        print(f"  {key}: {value}")

    print("\nGender:")
    for key, value in gender_counter.most_common():
        print(f"  {key}: {value}")

    print("\nInnings count:")
    for key, value in sorted(
        innings_count_counter.items()
    ):
        print(
            f"  {key} innings: {value} matches"
        )

    print("\nTotal overs:")
    print(total_overs)

    print("\nTotal deliveries:")
    print(total_deliveries)

    print("\nTotal batter runs:")
    print(total_batter_runs)

    print("\nTotal extra runs:")
    print(total_extra_runs)

    print("\nTotal match runs:")
    print(total_runs)

    print("\n" + "=" * 80)
    print("EDGE CASES")
    print("=" * 80)

    print("\nExtras found:")

    for key, value in delivery_edge_cases.most_common():
        if key.startswith("extra:"):
            print(f"  {key}: {value}")

    print("\nWicket types:")

    for key, value in wicket_types.most_common():
        print(f"  {key}: {value}")

    print("\nOther delivery-level cases:")

    for key, value in delivery_edge_cases.most_common():
        if not key.startswith("extra:"):
            print(f"  {key}: {value}")

    print("\n" + "=" * 80)
    print("SPECIAL MATCH STRUCTURES")
    print("=" * 80)

    print(
        "\nMatches with unusual innings count:"
    )

    if unusual_innings:

        for item in unusual_innings[:30]:

            print(
                f"  {item['file']} "
                f"-> {item['innings']} innings"
            )

        if len(unusual_innings) > 30:
            print(
                f"  ... and "
                f"{len(unusual_innings) - 30} more"
            )

    else:

        print("  None")

    print("\nMatches detected with super over:")
    print(len(matches_with_super_over))

    if matches_with_super_over:

        for file_name in matches_with_super_over[:20]:
            print(f"  {file_name}")

    print("\nMatches without a normal winner:")
    print(len(matches_with_no_result))

    if matches_with_no_result:

        for file_name in matches_with_no_result[:20]:
            print(f"  {file_name}")

    print("\n" + "=" * 80)
    print("TOP TEAMS")
    print("=" * 80)

    for team, count in team_counter.most_common(30):

        print(
            f"{team:<35} {count:>5} matches"
        )

    print("\n" + "=" * 80)
    print("TOP VENUES")
    print("=" * 80)

    for venue, count in venue_counter.most_common(20):

        print(
            f"{venue:<50} {count:>5} matches"
        )

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    validate_dataset()