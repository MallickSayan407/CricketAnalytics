import csv
import json
import os
import zipfile
from collections import Counter, defaultdict


# ============================================================
# CONFIGURATION
# ============================================================

RAW_ZIP = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\t20s_json.zip"

PROCESSED_DIR = r"D:\CricketAnalytics\cricket-analytics-data\processed\t20i"

PLAYER_MATCH_CSV = os.path.join(
    PROCESSED_DIR,
    "player_match_performance.csv"
)


# ============================================================
# HELPERS
# ============================================================

def safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def section(title):
    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


# ============================================================
# LOAD PROCESSED PLAYER DATA
# ============================================================

section("LOADING PROCESSED PLAYER-MATCH DATA")

with open(
    PLAYER_MATCH_CSV,
    "r",
    encoding="utf-8-sig",
    newline=""
) as f:

    processed_rows = list(
        csv.DictReader(f)
    )


processed_wickets = {}

for row in processed_rows:

    key = (
        row["match_id"],
        row["player_name"]
    )

    processed_wickets[key] = safe_int(
        row["wickets"]
    )


print(
    f"Processed player-match rows: "
    f"{len(processed_rows):,}"
)


# ============================================================
# WICKET TYPE COUNTS
# ============================================================

section("RAW WICKET TYPE DISTRIBUTION")

wicket_type_counts = Counter()

raw_bowler_wickets = defaultdict(int)
raw_team_wickets = defaultdict(int)

raw_wicket_details = defaultdict(list)


# ============================================================
# PROCESS RAW ZIP
# ============================================================

with zipfile.ZipFile(
    RAW_ZIP,
    "r"
) as z:

    json_files = [
        name
        for name in z.namelist()
        if name.lower().endswith(".json")
    ]

    print(
        f"JSON files: {len(json_files):,}"
    )

    for index, filename in enumerate(
        json_files,
        start=1
    ):

        if index % 500 == 0:
            print(
                f"Scanned {index:,} / "
                f"{len(json_files):,} matches..."
            )

        with z.open(filename) as f:

            data = json.load(f)

        match_id = os.path.splitext(
            os.path.basename(filename)
        )[0]

        info = data.get(
            "info",
            {}
        )

        gender = str(
            info.get(
                "gender",
                ""
            )
        ).strip().lower()

        innings_list = data.get(
            "innings",
            []
        )

        if not isinstance(
            innings_list,
            list
        ):
            continue

        for innings in innings_list:

            if not isinstance(
                innings,
                dict
            ):
                continue

            # ----------------------------------------------------
            # DO NOT COUNT SUPER OVERS
            # ----------------------------------------------------

            if innings.get(
                "super_over",
                False
            ):
                continue

            batting_team = innings.get(
                "team",
                ""
            )

            overs = innings.get(
                "overs",
                []
            )

            if not isinstance(
                overs,
                list
            ):
                continue

            for over in overs:

                if not isinstance(
                    over,
                    dict
                ):
                    continue

                deliveries = over.get(
                    "deliveries",
                    []
                )

                if not isinstance(
                    deliveries,
                    list
                ):
                    continue

                for delivery in deliveries:

                    if not isinstance(
                        delivery,
                        dict
                    ):
                        continue

                    bowler = delivery.get(
                        "bowler",
                        ""
                    )

                    wickets = delivery.get(
                        "wickets",
                        []
                    )

                    if not isinstance(
                        wickets,
                        list
                    ):
                        continue

                    for wicket in wickets:

                        if not isinstance(
                            wicket,
                            dict
                        ):
                            continue

                        kind = str(
                            wicket.get(
                                "kind",
                                ""
                            )
                        ).strip().lower()

                        player_out = str(
                            wicket.get(
                                "player_out",
                                ""
                            )
                        ).strip()

                        wicket_type_counts[kind] += 1

                        # ------------------------------------------------
                        # TEAM WICKET
                        # ------------------------------------------------

                        if kind not in {
                            "retired hurt",
                            "retired not out",
                        }:

                            raw_team_wickets[
                                (
                                    match_id,
                                    batting_team
                                )
                            ] += 1

                        # ------------------------------------------------
                        # BOWLER-CREDITED WICKET
                        # ------------------------------------------------

                        bowler_not_credited = {
                            "run out",
                            "retired hurt",
                            "retired not out",
                            "obstructing the field",
                            "retired out",
                            "timed out",
                        }

                        if (
                            kind
                            not in bowler_not_credited
                        ):

                            if bowler:

                                key = (
                                    match_id,
                                    bowler
                                )

                                raw_bowler_wickets[
                                    key
                                ] += 1

                                raw_wicket_details[
                                    key
                                ].append(
                                    (
                                        kind,
                                        player_out
                                    )
                                )


# ============================================================
# PRINT WICKET TYPES
# ============================================================

section("WICKET TYPES")

total_wickets = sum(
    wicket_type_counts.values()
)

print(
    f"Total raw regulation wickets: "
    f"{total_wickets:,}"
)

print()

for kind, count in sorted(
    wicket_type_counts.items(),
    key=lambda x: (-x[1], x[0])
):

    print(
        f"{kind:<30} {count:>8,}"
    )


# ============================================================
# TOTAL BOWLER WICKETS
# ============================================================

section("RAW BOWLER-CREDITED WICKETS")

raw_bowler_total = sum(
    raw_bowler_wickets.values()
)

processed_bowler_total = sum(
    processed_wickets.values()
)

print(
    f"Raw bowler wickets:        "
    f"{raw_bowler_total:,}"
)

print(
    f"Processed bowler wickets:  "
    f"{processed_bowler_total:,}"
)

print(
    f"Difference:               "
    f"{raw_bowler_total - processed_bowler_total:,}"
)


# ============================================================
# PLAYER-MATCH COMPARISON
# ============================================================

section("PLAYER-MATCH WICKET COMPARISON")

raw_keys = set(
    raw_bowler_wickets.keys()
)

processed_keys = set(
    processed_wickets.keys()
)

print(
    f"Raw bowler wicket keys:       "
    f"{len(raw_keys):,}"
)

print(
    f"Processed player-match keys:  "
    f"{len(processed_keys):,}"
)


# ============================================================
# EXACT WICKET DIFFERENCES
# ============================================================

differences = []

for key, raw_value in raw_bowler_wickets.items():

    processed_value = processed_wickets.get(
        key,
        0
    )

    if raw_value != processed_value:

        differences.append(
            (
                key,
                raw_value,
                processed_value,
                raw_value - processed_value
            )
        )


print()
print(
    f"Exact wicket differences: "
    f"{len(differences):,}"
)


# ============================================================
# DIFFERENCE SUMMARY
# ============================================================

difference_distribution = Counter()

for (
    key,
    raw_value,
    processed_value,
    difference
) in differences:

    difference_distribution[
        difference
    ] += 1


section("WICKET DIFFERENCE DISTRIBUTION")

for difference, count in sorted(
    difference_distribution.items()
):

    print(
        f"Difference {difference:+d}: "
        f"{count:,} player-match rows"
    )


# ============================================================
# FIRST 50 DIFFERENCES
# ============================================================

section("FIRST 50 WICKET DIFFERENCES")

for (
    key,
    raw_value,
    processed_value,
    difference
) in differences[:50]:

    match_id, player_name = key

    print()
    print(
        f"Match:       {match_id}"
    )

    print(
        f"Player:      {player_name}"
    )

    print(
        f"Raw wickets: {raw_value}"
    )

    print(
        f"Processed:   {processed_value}"
    )

    print(
        f"Difference:  {difference:+d}"
    )

    details = raw_wicket_details.get(
        key,
        []
    )

    if details:

        print(
            "Raw dismissals:"
        )

        for kind, player_out in details:

            print(
                f"    {kind} -> {player_out}"
            )


# ============================================================
# CHECK WHETHER ALL DIFFERENCES ARE +1
# ============================================================

section("DIFFERENCE PATTERN")

positive_one = sum(
    1
    for item in differences
    if item[3] == 1
)

negative_one = sum(
    1
    for item in differences
    if item[3] == -1
)

other = sum(
    1
    for item in differences
    if item[3] not in {1, -1}
)

print(
    f"Raw = Processed + 1:       "
    f"{positive_one:,}"
)

print(
    f"Raw = Processed - 1:       "
    f"{negative_one:,}"
)

print(
    f"Other differences:         "
    f"{other:,}"
)


# ============================================================
# FINAL DIAGNOSIS
# ============================================================

section("FINAL WICKET AUDIT RESULT")

if (
    raw_bowler_total
    == processed_bowler_total
    and not differences
):

    print(
        "[PASS] Raw and processed bowler wickets "
        "match exactly."
    )

    print()
    print(
        "No processor correction is required."
    )

elif positive_one == len(differences):

    print(
        "[INFO] Every mismatch is exactly "
        "one wicket."
    )

    print()
    print(
        "This strongly indicates that the raw "
        "audit and processor use different wicket "
        "credit rules."
    )

    print()
    print(
        "DO NOT MODIFY THE PROCESSOR YET."
    )

else:

    print(
        "[WARNING] Wicket differences require "
        "further investigation."
    )

    print()
    print(
        "DO NOT IMPORT T20I DATA INTO MYSQL YET."
    )

print("=" * 90)