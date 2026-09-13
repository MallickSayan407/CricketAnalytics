import io
import json
import zipfile
from collections import Counter


ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\ipl\ipl_json.zip"


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main():

    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL DATASET VALIDATION")
    print("=" * 80)

    print()
    print("Source:")
    print(ZIP_PATH)

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        json_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        print()
        print(f"JSON match files: {len(json_files)}")

        # ------------------------------------------------------------------
        # Counters
        # ------------------------------------------------------------------

        seasons = Counter()
        genders = Counter()
        match_types = Counter()
        teams = Counter()
        venues = Counter()
        cities = Counter()
        countries = Counter()

        innings_counts = Counter()
        result_types = Counter()
        toss_decisions = Counter()

        wicket_types = Counter()
        extras = Counter()

        player_names = set()
        player_ids = set()

        duplicate_match_ids = []
        match_ids = set()

        total_matches = 0
        total_deliveries = 0
        total_batter_runs = 0
        total_match_runs = 0

        total_fours = 0
        total_sixes = 0

        matches_with_super_over = 0
        matches_with_no_result = 0
        matches_with_tie = 0

        failed_files = []

        # ------------------------------------------------------------------
        # Scan every match
        # ------------------------------------------------------------------

        for index, filename in enumerate(json_files, start=1):

            try:

                with archive.open(filename) as raw_file:

                    data = json.load(
                        io.TextIOWrapper(
                            raw_file,
                            encoding="utf-8"
                        )
                    )

                info = data.get("info", {})

                total_matches += 1

                # ----------------------------------------------------------
                # Match ID
                # ----------------------------------------------------------

                match_id = filename.rsplit("/", 1)[-1].replace(".json", "")

                if match_id in match_ids:
                    duplicate_match_ids.append(match_id)

                match_ids.add(match_id)

                # ----------------------------------------------------------
                # Basic match information
                # ----------------------------------------------------------

                season = info.get("season")

                if season is not None:
                    seasons[str(season)] += 1

                gender = info.get("gender", "unknown")
                genders[str(gender)] += 1

                match_type = info.get("match_type", "unknown")
                match_types[str(match_type)] += 1

                # ----------------------------------------------------------
                # Teams
                # ----------------------------------------------------------

                for team in info.get("teams", []):

                    teams[team] += 1

                # ----------------------------------------------------------
                # Venue
                # ----------------------------------------------------------

                venue = info.get("venue")

                if venue:
                    venues[venue] += 1

                city = info.get("city")

                if city:
                    cities[city] += 1

                # ----------------------------------------------------------
                # Outcome
                # ----------------------------------------------------------

                outcome = info.get("outcome", {})

                if "winner" in outcome:

                    result_types["winner"] += 1

                elif "result" in outcome:

                    result_value = outcome.get("result")

                    if result_value:
                        result_types[str(result_value)] += 1

                        if str(result_value).lower() == "no result":
                            matches_with_no_result += 1

                elif "eliminator" in outcome:

                    result_types["eliminator"] += 1

                else:

                    result_types["other"] += 1

                if "winner" not in outcome and "result" in outcome:

                    result_value = str(
                        outcome.get("result", "")
                    ).lower()

                    if result_value == "tie":
                        matches_with_tie += 1

                # ----------------------------------------------------------
                # Toss
                # ----------------------------------------------------------

                toss = info.get("toss", {})

                decision = toss.get("decision")

                if decision:
                    toss_decisions[decision] += 1

                # ----------------------------------------------------------
                # Players + registry
                # ----------------------------------------------------------

                players_by_team = info.get("players", {})

                for team_player_list in players_by_team.values():

                    for player_name in team_player_list:

                        player_names.add(player_name)

                registry = info.get("registry", {})

                people = registry.get("people", {})

                for player_name, external_id in people.items():

                    player_ids.add(external_id)
                    player_names.add(player_name)

                # ----------------------------------------------------------
                # Innings
                # ----------------------------------------------------------

                innings = data.get("innings", [])

                innings_counts[len(innings)] += 1

                # ----------------------------------------------------------
                # Deliveries
                # ----------------------------------------------------------

                has_super_over = False

                for innings_block in innings:

                    # Cricsheet JSON has either:
                    #
                    # overs -> [{over: ..., deliveries: [...]}]
                    #
                    # or special innings metadata.
                    #
                    # We support the standard structure.

                    if innings_block.get("team") is None:
                        has_super_over = True

                    for over in innings_block.get("overs", []):

                        deliveries = over.get("deliveries", [])

                        for delivery in deliveries:

                            total_deliveries += 1

                            runs = delivery.get("runs", {})

                            batter_runs = safe_int(
                                runs.get("batter")
                            )

                            extras_runs = safe_int(
                                runs.get("extras")
                            )

                            total_batter_runs += batter_runs
                            total_match_runs += (
                                batter_runs + extras_runs
                            )

                            # ------------------------------------------------
                            # Extras
                            # ------------------------------------------------

                            delivery_extras = delivery.get(
                                "extras",
                                {}
                            )

                            for extra_type, extra_value in (
                                delivery_extras.items()
                            ):

                                extras[extra_type] += safe_int(
                                    extra_value
                                )

                            # ------------------------------------------------
                            # Fours / sixes
                            # ------------------------------------------------

                            if batter_runs == 4:
                                total_fours += 1

                            elif batter_runs == 6:
                                total_sixes += 1

                            # ------------------------------------------------
                            # Wickets
                            # ------------------------------------------------

                            for wicket in delivery.get(
                                "wickets",
                                []
                            ):

                                wicket_type = wicket.get(
                                    "kind"
                                )

                                if wicket_type:
                                    wicket_types[wicket_type] += 1

                if has_super_over:
                    matches_with_super_over += 1

            except Exception as exc:

                failed_files.append(
                    (filename, str(exc))
                )

            # Progress every 250 matches

            if index % 250 == 0 or index == len(json_files):

                print(
                    f"Processed: {index}/{len(json_files)}"
                )

        # ==================================================================
        # RESULTS
        # ==================================================================

        print()
        print("=" * 80)
        print("IPL DATASET SUMMARY")
        print("=" * 80)

        print()
        print(f"Matches:                 {total_matches}")
        print(f"Unique match IDs:        {len(match_ids)}")
        print(f"Players:                 {len(player_names)}")
        print(f"Registry player IDs:     {len(player_ids)}")
        print(f"Teams:                   {len(teams)}")
        print(f"Venues:                  {len(venues)}")
        print(f"Cities:                  {len(cities)}")

        print()
        print("SEASONS")

        for season, count in sorted(
            seasons.items(),
            key=lambda x: str(x[0])
        ):
            print(
                f"  {season}: {count} matches"
            )

        print()
        print("GENDER")

        for key, value in genders.items():
            print(f"  {key}: {value}")

        print()
        print("MATCH TYPES")

        for key, value in match_types.items():
            print(f"  {key}: {value}")

        print()
        print("TEAMS")

        for team, count in teams.most_common():
            print(
                f"  {team}: {count} matches"
            )

        print()
        print("TOP VENUES")

        for venue, count in venues.most_common(20):
            print(
                f"  {venue}: {count} matches"
            )

        print()
        print("INNINGS COUNTS")

        for innings_count, count in sorted(
            innings_counts.items()
        ):
            print(
                f"  {innings_count} innings: {count} matches"
            )

        print()
        print("RESULTS")

        for key, value in result_types.items():
            print(
                f"  {key}: {value}"
            )

        print()
        print(f"Ties:                    {matches_with_tie}")
        print(
            f"No-result matches:       {matches_with_no_result}"
        )
        print(
            f"Matches with special innings: "
            f"{matches_with_super_over}"
        )

        print()
        print("MATCH TOTALS")

        print(
            f"  Total deliveries:      {total_deliveries}"
        )

        print(
            f"  Batter runs:            {total_batter_runs}"
        )

        print(
            f"  Total match runs:       {total_match_runs}"
        )

        print(
            f"  Fours:                  {total_fours}"
        )

        print(
            f"  Sixes:                  {total_sixes}"
        )

        print()
        print("EXTRAS")

        for key, value in extras.most_common():
            print(
                f"  {key}: {value}"
            )

        print()
        print("WICKET TYPES")

        for key, value in wicket_types.most_common():
            print(
                f"  {key}: {value}"
            )

        print()
        print("=" * 80)
        print("VALIDATION")
        print("=" * 80)

        print()

        if len(match_ids) != total_matches:

            print(
                "Duplicate match IDs:     FAIL"
            )

            for duplicate in duplicate_match_ids:
                print(
                    f"  Duplicate: {duplicate}"
                )

        else:

            print(
                "Duplicate match IDs:     PASS"
            )

        if failed_files:

            print(
                f"Files failed:             {len(failed_files)}"
            )

            for filename, error in failed_files[:20]:

                print(
                    f"  {filename}: {error}"
                )

        else:

            print(
                "JSON files failed:       0"
            )

        if total_matches == len(json_files):

            print(
                "All JSON files processed: PASS"
            )

        else:

            print(
                "All JSON files processed: FAIL"
            )

        print()
        print("=" * 80)
        print("IPL VALIDATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    main()