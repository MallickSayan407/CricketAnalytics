import io
import json
import zipfile


ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\ipl\ipl_json.zip"


def main():

    print("=" * 80)
    print("CRICKET ANALYTICS")
    print("IPL SPECIAL MATCH AUDIT")
    print("=" * 80)

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        json_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        special_matches = []
        one_innings_matches = []

        for filename in json_files:

            with archive.open(filename) as raw_file:
                data = json.load(
                    io.TextIOWrapper(
                        raw_file,
                        encoding="utf-8"
                    )
                )

            info = data.get("info", {})
            innings = data.get("innings", [])

            record = {
                "match_id": filename.rsplit("/", 1)[-1].replace(".json", ""),
                "date": (
                    info.get("dates", ["UNKNOWN"])[0]
                    if info.get("dates")
                    else "UNKNOWN"
                ),
                "season": info.get("season"),
                "teams": info.get("teams", []),
                "venue": info.get("venue"),
                "outcome": info.get("outcome", {}),
                "innings": innings,
            }

            if len(innings) == 1:
                one_innings_matches.append(record)

            if len(innings) > 2:
                special_matches.append(record)

        print()
        print("=" * 80)
        print("ONE-INNINGS MATCHES")
        print("=" * 80)

        print()
        print(f"Count: {len(one_innings_matches)}")

        for match in one_innings_matches:

            print()
            print("-" * 80)
            print(f"Match ID : {match['match_id']}")
            print(f"Date     : {match['date']}")
            print(f"Season   : {match['season']}")
            print(f"Teams    : {' vs '.join(match['teams'])}")
            print(f"Venue    : {match['venue']}")
            print(f"Outcome  : {match['outcome']}")

            for index, innings in enumerate(match["innings"], start=1):

                print(
                    f"  Innings {index}: "
                    f"team={innings.get('team')}, "
                    f"target={innings.get('target')}, "
                    f"super_over={innings.get('super_over')}"
                )

        print()
        print("=" * 80)
        print("MATCHES WITH MORE THAN TWO INNINGS")
        print("=" * 80)

        print()
        print(f"Count: {len(special_matches)}")

        for match in special_matches:

            print()
            print("-" * 80)
            print(f"Match ID : {match['match_id']}")
            print(f"Date     : {match['date']}")
            print(f"Season   : {match['season']}")
            print(f"Teams    : {' vs '.join(match['teams'])}")
            print(f"Venue    : {match['venue']}")
            print(f"Outcome  : {match['outcome']}")
            print(f"Innings  : {len(match['innings'])}")

            for index, innings in enumerate(match["innings"], start=1):

                overs = innings.get("overs", [])

                deliveries = sum(
                    len(over.get("deliveries", []))
                    for over in overs
                )

                runs = 0
                wickets = 0

                for over in overs:

                    for delivery in over.get("deliveries", []):

                        runs += delivery.get(
                            "runs",
                            {}
                        ).get("total", 0)

                        wickets += len(
                            delivery.get("wickets", [])
                        )

                print(
                    f"  Innings {index}: "
                    f"team={innings.get('team')}, "
                    f"super_over={innings.get('super_over')}, "
                    f"runs={runs}, "
                    f"wickets={wickets}, "
                    f"deliveries={deliveries}"
                )

        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print()
        print(
            f"One-innings matches:        "
            f"{len(one_innings_matches)}"
        )

        print(
            f"More-than-two-innings:      "
            f"{len(special_matches)}"
        )

        print()
        print("=" * 80)
        print("IPL SPECIAL MATCH AUDIT COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    main()