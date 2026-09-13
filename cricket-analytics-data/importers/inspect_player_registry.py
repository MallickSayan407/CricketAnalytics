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

TARGET_NAMES = {
    "V Kohli",
    "Virat Kohli",
    "V Kohli ",
}


def main():

    print("=" * 80)
    print("CRICSHEET PLAYER REGISTRY INSPECTOR")
    print("=" * 80)

    print()
    print("Source:")
    print(ZIP_PATH)

    found = {}

    with zipfile.ZipFile(ZIP_PATH, "r") as archive:

        json_files = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".json")
        ]

        for filename in json_files:

            with archive.open(filename) as file:

                data = json.load(file)

            info = data.get(
                "info",
                {}
            )

            registry = info.get(
                "registry",
                {}
            )

            people = registry.get(
                "people",
                {}
            )

            for player_name, cricsheet_id in people.items():

                if player_name in TARGET_NAMES:

                    found[player_name] = cricsheet_id

    print()
    print("Matching players:")
    print("-" * 80)

    for name, identifier in sorted(
        found.items()
    ):

        print(
            f"{name:<30} -> {identifier}"
        )

    print()
    print("=" * 80)

    if not found:

        print("No matching player found.")

    else:

        print(
            f"Found {len(found)} registry entries."
        )

    print("=" * 80)


if __name__ == "__main__":
    main()