import io
import json
import zipfile

from process_ipl_dataset import (
    normalize_team,
    process_match_team_stats,
    process_player_match_performance,
    is_super_over,
)


ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\ipl\ipl_json.zip"


SPECIAL_MATCH_IDS = {
    "1082625",
    "1175365",
    "1178426",
    "1216493",
    "1216512",
    "1216517",
    "1216547",
    "1254077",
    "1473469",
    "1529281",
    "392190",
    "419121",
    "598004",
    "598017",
    "729315",
    "829741",
}


NO_RESULT_MATCH_IDS = {
    "1359519",
    "1473492",
    "1473495",
    "1527685",
    "501265",
    "829763",
}


def main():

    print("=" * 80)
    print("IPL SPECIAL-MATCH PROCESSING TEST")
    print("=" * 80)

    with zipfile.ZipFile(
        ZIP_PATH,
        "r"
    ) as archive:

        for filename in archive.namelist():

            if not filename.endswith(".json"):
                continue

            match_id = (
                filename
                .rsplit("/", 1)[-1]
                .replace(".json", "")
            )

            if (
                match_id not in SPECIAL_MATCH_IDS
                and match_id not in NO_RESULT_MATCH_IDS
            ):
                continue

            with archive.open(filename) as raw_file:

                data = json.load(
                    io.TextIOWrapper(
                        raw_file,
                        encoding="utf-8"
                    )
                )

            info = data["info"]
            innings = data.get("innings", [])

            outcome = info.get(
                "outcome",
                {}
            )

            super_over_count = sum(
                1
                for innings_block in innings
                if is_super_over(innings_block)
            )

            normal_innings = [
                innings_block
                for innings_block in innings
                if not is_super_over(innings_block)
            ]

            team_stats = process_match_team_stats(
                match_id,
                innings
            )

            print()
            print("-" * 80)

            print(
                f"Match ID:       {match_id}"
            )

            print(
                f"Season:         {info.get('season')}"
            )

            print(
                f"Teams:          "
                f"{' vs '.join(info.get('teams', []))}"
            )

            print(
                f"Outcome:        {outcome}"
            )

            print(
                f"Total innings:  {len(innings)}"
            )

            print(
                f"Normal innings: {len(normal_innings)}"
            )

            print(
                f"Super Overs:    {super_over_count}"
            )

            print(
                "Processed team stats:"
            )

            for row in team_stats:

                print(
                    f"  {row['team_name']}: "
                    f"{row['runs']} runs, "
                    f"{row['wickets']} wickets, "
                    f"{row['total_balls']} balls"
                )

            # ---------------------------------------------------------------
            # Assertions
            # ---------------------------------------------------------------

            if match_id in NO_RESULT_MATCH_IDS:

                assert outcome.get(
                    "result"
                ) == "no result"

                assert super_over_count == 0

                print(
                    "NO-RESULT TEST: PASS"
                )

            else:

                assert outcome.get(
                    "result"
                ) == "tie"

                assert outcome.get(
                    "eliminator"
                )

                assert super_over_count >= 1

                # Team stats must contain only normal innings.
                assert len(team_stats) == 2

                print(
                    "SUPER-OVER TEST: PASS"
                )

    print()
    print("=" * 80)
    print("SPECIAL-MATCH PROCESSING TEST: PASS")
    print("=" * 80)


if __name__ == "__main__":
    main()