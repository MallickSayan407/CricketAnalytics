import json
import zipfile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

ZIP_PATH = (
    BASE_DIR
    / "raw"
    / "international"
    / "odis_json.zip"
)


def inspect_archive():
    if not ZIP_PATH.exists():
        print("ERROR: Dataset not found:")
        print(ZIP_PATH)
        return

    print("=" * 70)
    print("CRICSHEET DATASET INSPECTOR")
    print("=" * 70)

    print("\nDataset:")
    print(ZIP_PATH)

    size_mb = ZIP_PATH.stat().st_size / (1024 * 1024)

    print("\nZIP size:")
    print(f"{size_mb:.2f} MB")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        print(f"\nJSON files found: {len(files)}")

        if not files:
            print("ERROR: No JSON files found.")
            return

        print("\nFirst 10 files:")

        for file_name in files[:10]:
            print(f"  {file_name}")

        sample_file = files[0]

        print("\n" + "=" * 70)
        print("SAMPLE FILE")
        print("=" * 70)

        print(sample_file)

        with archive.open(sample_file) as file:
            data = json.load(file)

        print("\nTop-level fields:")

        for key in data.keys():
            print(f"  - {key}")

        print("\n" + "=" * 70)
        print("MATCH INFORMATION")
        print("=" * 70)

        info = data.get("info", {})

        print("\nDates:")
        print(info.get("dates"))

        print("\nGender:")
        print(info.get("gender"))

        print("\nMatch type:")
        print(info.get("match_type"))

        print("\nTeams:")
        print(info.get("teams"))

        print("\nVenue:")
        print(info.get("venue"))

        print("\nCity:")
        print(info.get("city"))

        print("\nToss:")
        print(info.get("toss"))

        print("\nOutcome:")
        print(info.get("outcome"))

        print("\nPlayers:")

        players = info.get("players", {})

        for team, team_players in players.items():
            print(f"\n{team}:")

            for player in team_players:
                print(f"  - {player}")

        print("\n" + "=" * 70)
        print("INNINGS STRUCTURE")
        print("=" * 70)

        innings = data.get("innings", [])

        print(f"\nNumber of innings: {len(innings)}")

        if innings:

            first_innings = innings[0]

            print("\nFirst innings keys:")

            for key in first_innings.keys():
                print(f"  - {key}")

            print("\nFirst innings batting team:")
            print(first_innings.get("team"))

            overs = first_innings.get("overs", [])

            print(f"\nNumber of overs in first innings: {len(overs)}")

            if overs:

                first_over = overs[0]

                print("\nFirst over keys:")

                for key in first_over.keys():
                    print(f"  - {key}")

                deliveries = first_over.get("deliveries", [])

                print(
                    f"\nDeliveries in first over: "
                    f"{len(deliveries)}"
                )

                if deliveries:

                    print("\nFirst delivery:")

                    print(
                        json.dumps(
                            deliveries[0],
                            indent=4
                        )
                    )

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    inspect_archive()