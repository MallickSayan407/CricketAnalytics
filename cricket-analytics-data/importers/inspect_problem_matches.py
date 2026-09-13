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

PROBLEM_MATCH_IDS = {
    "1233463",
    "1405125",
    "1474411",
}


def print_separator(char="=", length=100):
    print(char * length)


def inspect_match(match_id, data):
    info = data.get("info", {})

    print_separator()
    print(f"MATCH ID: {match_id}")
    print_separator()

    dates = info.get("dates", [])
    teams = info.get("teams", [])
    venue = info.get("venue")
    city = info.get("city")
    gender = info.get("gender")
    match_type = info.get("match_type")

    print(f"Date       : {dates}")
    print(f"Teams      : {teams}")
    print(f"Venue      : {venue}")
    print(f"City       : {city}")
    print(f"Gender     : {gender}")
    print(f"Match type : {match_type}")

    print()
    print("INNINGS")
    print_separator("-", 100)

    innings = data.get("innings", [])

    for innings_index, innings_data in enumerate(innings, start=1):

        team = innings_data.get("team")

        print()
        print(f"Innings {innings_index}: {team}")

        # Cricsheet JSON normally stores overs as a list.
        overs = innings_data.get("overs", [])

        team_wickets = []
        all_deliveries = []

        for over in overs:
            over_number = over.get("over")
            deliveries = over.get("deliveries", [])

            for delivery_number, delivery in enumerate(deliveries):

                all_deliveries.append(
                    {
                        "over": over_number,
                        "delivery": delivery_number,
                        "data": delivery,
                    }
                )

                wickets = delivery.get("wickets", [])

                for wicket in wickets:

                    player_out = wicket.get("player_out")
                    wicket_kind = wicket.get("kind")
                    fielders = wicket.get("fielders", [])

                    team_wickets.append(
                        {
                            "over": over_number,
                            "delivery": delivery_number,
                            "player_out": player_out,
                            "kind": wicket_kind,
                            "fielders": fielders,
                            "delivery_data": delivery,
                        }
                    )

        print(f"Total deliveries : {len(all_deliveries)}")
        print(f"Total wicket events: {len(team_wickets)}")

        print()
        print("WICKET EVENTS")
        print_separator("-", 100)

        for index, wicket in enumerate(team_wickets, start=1):

            delivery = wicket["delivery_data"]

            print(
                f"{index:2}. "
                f"over={wicket['over']}, "
                f"delivery={wicket['delivery']}, "
                f"player_out={wicket['player_out']}, "
                f"kind={wicket['kind']}"
            )

            if wicket["fielders"]:
                print(f"    fielders={wicket['fielders']}")

            print(
                f"    batter={delivery.get('batter')}, "
                f"bowler={delivery.get('bowler')}, "
                f"runs={delivery.get('runs')}"
            )

        print()
        print("WICKET TYPE COUNTS")
        print_separator("-", 100)

        wicket_type_counts = {}

        for wicket in team_wickets:
            wicket_type = wicket["kind"]

            wicket_type_counts[wicket_type] = (
                wicket_type_counts.get(wicket_type, 0) + 1
            )

        for wicket_type, count in sorted(
            wicket_type_counts.items(),
            key=lambda item: item[0]
        ):
            print(f"{wicket_type:30} {count}")

        print()
        print("SCORECARD OUTCOME")
        print_separator("-", 100)

        outcome = info.get("outcome", {})

        print(json.dumps(outcome, indent=4))


def main():

    print_separator()
    print("CRICSHEET PROBLEM MATCH INSPECTOR")
    print_separator()

    print()
    print(f"Source ZIP:")
    print(ZIP_PATH)

    if not ZIP_PATH.exists():
        print()
        print("ERROR: ZIP file does not exist.")
        return

    print()
    print("Problem matches:")
    for match_id in sorted(PROBLEM_MATCH_IDS):
        print(f"  {match_id}")

    print()
    print("Opening archive...")

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        names = archive.namelist()

        found = 0

        for match_id in sorted(PROBLEM_MATCH_IDS):

            possible_names = [
                name
                for name in names
                if Path(name).stem == match_id
                and name.lower().endswith(".json")
            ]

            if not possible_names:
                print()
                print(f"WARNING: Match {match_id} not found in ZIP.")
                continue

            filename = possible_names[0]

            print()
            print(f"Reading: {filename}")

            with archive.open(filename) as file:
                data = json.load(file)

            inspect_match(match_id, data)

            found += 1

    print()
    print_separator()
    print(f"Inspection complete. Found {found}/{len(PROBLEM_MATCH_IDS)} matches.")
    print_separator()


if __name__ == "__main__":
    main()