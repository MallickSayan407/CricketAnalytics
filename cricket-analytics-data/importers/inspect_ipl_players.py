import io
import json
import zipfile

ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\ipl\ipl_json.zip"


def main():

    print("=" * 80)
    print("IPL PLAYER REGISTRY AUDIT")
    print("=" * 80)

    players_without_registry = set()
    registry_players = set()

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        json_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        for filename in json_files:

            with archive.open(filename) as raw_file:

                data = json.load(
                    io.TextIOWrapper(
                        raw_file,
                        encoding="utf-8"
                    )
                )

            info = data.get("info", {})

            players_by_team = info.get("players", {})

            registry = info.get("registry", {})
            people = registry.get("people", {})

            registry_players.update(people.keys())

            for team_players in players_by_team.values():

                for player_name in team_players:

                    if player_name not in people:
                        players_without_registry.add(
                            player_name
                        )

    print()
    print(
        f"Players without registry ID: "
        f"{len(players_without_registry)}"
    )

    print()

    for player in sorted(players_without_registry):
        print(f"  {player}")

    print()
    print("=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()