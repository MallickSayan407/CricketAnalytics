import json
import zipfile
from collections import Counter, defaultdict


ZIP_PATH = r"D:\CricketAnalytics\cricket-analytics-data\raw\international\tests_json.zip"


# Wicket types that normally credit the bowler.
BOWLER_CREDIT_WICKETS = {
    "bowled",
    "caught",
    "caught and bowled",
    "lbw",
    "stumped",
    "hit wicket",
}


# Wicket types that do NOT normally credit the bowler.
NON_BOWLER_WICKETS = {
    "run out",
    "retired hurt",
    "retired not out",
    "obstructing the field",
    "handled the ball",
}


def main():

    print("=" * 90)
    print("TEST CRICKET SPECIAL-CASE AUDIT")
    print("=" * 90)
    print(f"ZIP: {ZIP_PATH}")
    print()

    matches = 0

    # -------------------------------------------------------------------------
    # INNINGS STRUCTURE
    # -------------------------------------------------------------------------

    innings_count = Counter()

    one_innings = []
    two_innings = []
    three_innings = []
    four_innings = []

    # -------------------------------------------------------------------------
    # DECLARATIONS
    # -------------------------------------------------------------------------

    declared_innings = 0
    declaration_matches = set()

    # -------------------------------------------------------------------------
    # FOLLOW-ONS
    # -------------------------------------------------------------------------

    follow_on_candidates = []
    follow_on_patterns = Counter()

    # -------------------------------------------------------------------------
    # MISCOUNTED OVERS
    # -------------------------------------------------------------------------

    miscounted_overs = 0
    miscounted_matches = set()
    miscounted_examples = []

    # -------------------------------------------------------------------------
    # PENALTY RUNS
    # -------------------------------------------------------------------------

    penalty_innings = 0
    penalty_runs = 0
    penalty_examples = []

    # -------------------------------------------------------------------------
    # WICKETS
    # -------------------------------------------------------------------------

    wicket_kinds = Counter()

    bowler_credit_wickets = 0
    non_bowler_wickets = 0
    unknown_wicket_kinds = Counter()

    wicket_examples = defaultdict(list)

    # -------------------------------------------------------------------------
    # RETIRED / SPECIAL DISMISSALS
    # -------------------------------------------------------------------------

    retired_hurt = 0
    retired_not_out = 0
    handled_ball = 0
    obstructing_field = 0

    # -------------------------------------------------------------------------
    # PLAYER PARTICIPATION
    # -------------------------------------------------------------------------

    player_names = set()
    registry_ids = set()

    players_without_registry = []

    # -------------------------------------------------------------------------
    # OUTCOME
    # -------------------------------------------------------------------------

    outcomes = Counter()

    draw_matches = []
    winner_matches = []

    # -------------------------------------------------------------------------
    # MATCH / INNINGS METADATA
    # -------------------------------------------------------------------------

    missing_metadata = Counter()

    zero_delivery_innings = []
    empty_overs = []

    # -------------------------------------------------------------------------
    # DELIVERY TOTALS
    # -------------------------------------------------------------------------

    total_deliveries = 0
    legal_balls = 0

    batter_runs = 0
    total_runs = 0

    extras = Counter()

    # -------------------------------------------------------------------------
    # FOLLOW-ON STRUCTURE
    # -------------------------------------------------------------------------

    # We will inspect the actual team sequence.
    # Examples:
    #
    # A B A
    # A B A B
    #
    # are structurally different from:
    #
    # A B B
    #
    # The processor must not assume that every third innings is a follow-on.
    # -------------------------------------------------------------------------

    with zipfile.ZipFile(ZIP_PATH, "r") as z:

        json_files = [
            name for name in z.namelist()
            if name.lower().endswith(".json")
        ]

        print(f"JSON files found: {len(json_files)}")
        print()

        for index, filename in enumerate(json_files, start=1):

            try:
                with z.open(filename) as f:
                    data = json.load(f)
            except Exception as exc:
                print(f"ERROR reading {filename}: {exc}")
                continue

            matches += 1

            match_id = filename.rsplit("/", 1)[-1].replace(".json", "")

            info = data.get("info", {})
            innings = data.get("innings", [])

            # =================================================================
            # OUTCOME
            # =================================================================

            outcome = info.get("outcome", {})

            winner = outcome.get("winner")
            result = outcome.get("result")

            if winner:
                outcomes["WINNER"] += 1
                winner_matches.append((match_id, winner))

            elif result:
                result_upper = str(result).upper()
                outcomes[result_upper] += 1

                if result_upper == "DRAW":
                    draw_matches.append(match_id)

            else:
                outcomes["UNKNOWN"] += 1

            # =================================================================
            # MISSING METADATA
            # =================================================================

            for missing_item in info.get("missing", []):

                if isinstance(missing_item, str):
                    missing_metadata[missing_item] += 1
                else:
                    missing_metadata[str(missing_item)] += 1

            # =================================================================
            # INNINGS COUNT
            # =================================================================

            count = len(innings)
            innings_count[count] += 1

            if count == 1:
                one_innings.append(match_id)

            elif count == 2:
                two_innings.append(match_id)

            elif count == 3:
                three_innings.append(match_id)

            elif count == 4:
                four_innings.append(match_id)

            # =================================================================
            # REGISTRY
            # =================================================================

            registry = info.get("registry", {})
            people_registry = registry.get("people", {})

            for player_name, external_id in people_registry.items():

                player_names.add(player_name)
                registry_ids.add(external_id)

            players = info.get("players", {})

            for team, team_players in players.items():

                for player in team_players:

                    if player not in people_registry:
                        players_without_registry.append(
                            (match_id, team, player)
                        )

            # =================================================================
            # TEAM ORDER / FOLLOW-ON CANDIDATES
            # =================================================================

            teams_in_innings = [
                innings_data.get("team")
                for innings_data in innings
            ]

            if len(teams_in_innings) >= 3:

                # Structural pattern.
                pattern = " ".join(
                    str(team) for team in teams_in_innings
                )

                follow_on_patterns[pattern] += 1

                if (
                    teams_in_innings[0]
                    and teams_in_innings[2]
                    and teams_in_innings[0]
                    == teams_in_innings[2]
                ):
                    follow_on_candidates.append(
                        (
                            match_id,
                            teams_in_innings
                        )
                    )

            # =================================================================
            # INNINGS DETAILS
            # =================================================================

            for innings_index, innings_data in enumerate(
                innings,
                start=1
            ):

                batting_team = innings_data.get("team")

                overs = innings_data.get("overs")

                # -------------------------------------------------------------
                # DECLARATION
                # -------------------------------------------------------------

                if innings_data.get("declared") is True:

                    declared_innings += 1
                    declaration_matches.add(match_id)

                # -------------------------------------------------------------
                # ZERO DELIVERY / EMPTY INNINGS
                # -------------------------------------------------------------

                if overs is None:

                    zero_delivery_innings.append(
                        (match_id, innings_index, batting_team)
                    )

                    continue

                if len(overs) == 0:

                    zero_delivery_innings.append(
                        (match_id, innings_index, batting_team)
                    )

                # -------------------------------------------------------------
                # MISCOUNTED OVERS
                # -------------------------------------------------------------

                innings_miscounted = innings_data.get(
                    "miscounted_overs",
                    []
                )

                if innings_miscounted:

                    miscounted_matches.add(match_id)

                    miscounted_overs += len(
                        innings_miscounted
                    )

                    for item in innings_miscounted:

                        if len(miscounted_examples) < 30:
                            miscounted_examples.append(
                                (
                                    match_id,
                                    innings_index,
                                    item
                                )
                            )

                # -------------------------------------------------------------
                # PENALTY RUNS
                # -------------------------------------------------------------

                penalty_data = innings_data.get(
                    "penalty_runs"
                )

                if penalty_data:

                    penalty_innings += 1

                    if isinstance(penalty_data, dict):

                        innings_penalty = sum(
                            int(value)
                            for value in penalty_data.values()
                            if isinstance(value, (int, float))
                        )

                        penalty_runs += innings_penalty

                    if len(penalty_examples) < 30:
                        penalty_examples.append(
                            (
                                match_id,
                                innings_index,
                                penalty_data
                            )
                        )

                # -------------------------------------------------------------
                # ABSENT HURT
                # -------------------------------------------------------------

                # This is metadata about players unavailable to bat,
                # not a dismissal event.
                # We intentionally do not count it as a wicket here.

                # -------------------------------------------------------------
                # OVERS / DELIVERIES
                # -------------------------------------------------------------

                for over in overs:

                    deliveries = over.get(
                        "deliveries",
                        []
                    )

                    if not deliveries:

                        if len(empty_overs) < 30:
                            empty_overs.append(
                                (
                                    match_id,
                                    innings_index,
                                    over.get("over")
                                )
                            )

                    for delivery in deliveries:

                        total_deliveries += 1

                        delivery_runs = delivery.get(
                            "runs",
                            {}
                        )

                        batter_value = int(
                            delivery_runs.get(
                                "batter",
                                0
                            )
                        )

                        total_value = int(
                            delivery_runs.get(
                                "total",
                                0
                            )
                        )

                        batter_runs += batter_value
                        total_runs += total_value

                        delivery_extras = delivery.get(
                            "extras",
                            {}
                        )

                        is_wide = (
                            "wides"
                            in delivery_extras
                        )

                        is_no_ball = (
                            "noballs"
                            in delivery_extras
                        )

                        # Test statistics use actual legal deliveries.
                        if not is_wide and not is_no_ball:
                            legal_balls += 1

                        for extra_type, value in delivery_extras.items():

                            extras[extra_type] += int(value)

                        # -----------------------------------------------------
                        # WICKETS
                        # -----------------------------------------------------

                        wickets = delivery.get(
                            "wickets",
                            []
                        )

                        for wicket in wickets:

                            kind = wicket.get(
                                "kind",
                                "UNKNOWN"
                            )

                            wicket_kinds[kind] += 1

                            if kind in BOWLER_CREDIT_WICKETS:

                                bowler_credit_wickets += 1

                                if len(
                                    wicket_examples[kind]
                                ) < 5:

                                    wicket_examples[kind].append(
                                        (
                                            match_id,
                                            innings_index,
                                            wicket
                                        )
                                    )

                            elif kind in NON_BOWLER_WICKETS:

                                non_bowler_wickets += 1

                                if len(
                                    wicket_examples[kind]
                                ) < 5:

                                    wicket_examples[kind].append(
                                        (
                                            match_id,
                                            innings_index,
                                            wicket
                                        )
                                    )

                            else:

                                unknown_wicket_kinds[kind] += 1

            # =================================================================
            # PROGRESS
            # =================================================================

            if index % 100 == 0:
                print(
                    f"Processed {index:,} / "
                    f"{len(json_files):,} matches..."
                )

    # =========================================================================
    # REPORT
    # =========================================================================

    print()
    print("=" * 90)
    print("TEST SPECIAL-CASE AUDIT REPORT")
    print("=" * 90)

    # -------------------------------------------------------------------------
    print()
    print("1. INNINGS STRUCTURE")
    print("-" * 90)

    for count, value in sorted(innings_count.items()):
        print(
            f"{count:>2} innings: "
            f"{value:>4} matches"
        )

    # -------------------------------------------------------------------------
    print()
    print("2. INNINGS EXAMPLES")
    print("-" * 90)

    print(f"One-innings matches:   {len(one_innings):,}")
    print(f"Two-innings matches:   {len(two_innings):,}")
    print(f"Three-innings matches: {len(three_innings):,}")
    print(f"Four-innings matches:  {len(four_innings):,}")

    if one_innings:
        print()
        print("One-innings examples:")
        for match_id in one_innings[:20]:
            print(match_id)

    if two_innings:
        print()
        print("Two-innings examples:")
        for match_id in two_innings[:20]:
            print(match_id)

    # -------------------------------------------------------------------------
    print()
    print("3. DECLARATIONS")
    print("-" * 90)

    print(f"Declared innings: {declared_innings:,}")
    print(
        f"Matches containing declarations: "
        f"{len(declaration_matches):,}"
    )

    # -------------------------------------------------------------------------
    print()
    print("4. FOLLOW-ON STRUCTURAL ANALYSIS")
    print("-" * 90)

    print(
        "Matches where innings 1 team == innings 3 team: "
        f"{len(follow_on_candidates):,}"
    )

    print()
    print("Most common innings team patterns:")

    for pattern, count in follow_on_patterns.most_common(30):
        print(
            f"{count:>4} | {pattern}"
        )

    print()
    print(
        "IMPORTANT: The structural candidate count is NOT "
        "treated as a confirmed follow-on count."
    )

    # -------------------------------------------------------------------------
    print()
    print("5. MISCOUNTED OVERS")
    print("-" * 90)

    print(
        f"Matches with miscounted overs: "
        f"{len(miscounted_matches):,}"
    )

    print(f"Miscounted overs: {miscounted_overs:,}")

    if miscounted_examples:

        print()
        print("Examples:")

        for example in miscounted_examples:
            print(example)

    # -------------------------------------------------------------------------
    print()
    print("6. PENALTY RUNS")
    print("-" * 90)

    print(f"Penalty-run innings: {penalty_innings:,}")
    print(f"Penalty runs detected: {penalty_runs:,}")

    if penalty_examples:

        print()
        print("Examples:")

        for example in penalty_examples:
            print(example)

    # -------------------------------------------------------------------------
    print()
    print("7. WICKET CLASSIFICATION")
    print("-" * 90)

    print(
        f"Total bowler-credit wickets: "
        f"{bowler_credit_wickets:,}"
    )

    print(
        f"Total non-bowler-credit wickets: "
        f"{non_bowler_wickets:,}"
    )

    print()
    print("Wicket kinds:")

    for kind, count in wicket_kinds.most_common():

        if kind in BOWLER_CREDIT_WICKETS:
            category = "BOWLER"

        elif kind in NON_BOWLER_WICKETS:
            category = "NON-BOWLER"

        else:
            category = "UNKNOWN"

        print(
            f"{kind:<28} "
            f"{count:>6} "
            f"{category}"
        )

    print()

    if unknown_wicket_kinds:

        print("UNKNOWN WICKET TYPES:")

        for kind, count in unknown_wicket_kinds.items():
            print(
                f"{kind}: {count:,}"
            )

    else:

        print(
            "No unknown wicket types detected."
        )

    # -------------------------------------------------------------------------
    print()
    print("8. SPECIAL DISMISSALS")
    print("-" * 90)

    print(
        f"Retired hurt: "
        f"{wicket_kinds.get('retired hurt', 0):,}"
    )

    print(
        f"Retired not out: "
        f"{wicket_kinds.get('retired not out', 0):,}"
    )

    print(
        f"Handled the ball: "
        f"{wicket_kinds.get('handled the ball', 0):,}"
    )

    print(
        f"Obstructing the field: "
        f"{wicket_kinds.get('obstructing the field', 0):,}"
    )

    # -------------------------------------------------------------------------
    print()
    print("9. DELIVERY / RUN RECONCILIATION")
    print("-" * 90)

    print(f"Total deliveries: {total_deliveries:,}")
    print(f"Legal balls: {legal_balls:,}")
    print(f"Batter runs: {batter_runs:,}")
    print(f"Total runs: {total_runs:,}")

    print()
    print("Extras:")

    for extra_type, value in sorted(extras.items()):
        print(
            f"{extra_type}: {value:,}"
        )

    total_extras = sum(extras.values())

    print(
        f"Total extras: {total_extras:,}"
    )

    # -------------------------------------------------------------------------
    print()
    print("10. PLAYER REGISTRY")
    print("-" * 90)

    print(
        f"Unique player names: "
        f"{len(player_names):,}"
    )

    print(
        f"Unique registry IDs: "
        f"{len(registry_ids):,}"
    )

    print(
        f"Players missing registry ID: "
        f"{len(players_without_registry):,}"
    )

    if players_without_registry:

        print()
        print("Examples:")

        for item in players_without_registry[:20]:
            print(item)

    # -------------------------------------------------------------------------
    print()
    print("11. MATCH OUTCOMES")
    print("-" * 90)

    for outcome, count in sorted(outcomes.items()):
        print(
            f"{outcome}: {count:,}"
        )

    print()
    print(
        f"Draw examples: "
        f"{len(draw_matches):,}"
    )

    for match_id in draw_matches[:20]:
        print(match_id)

    # -------------------------------------------------------------------------
    print()
    print("12. EMPTY / ZERO-DELIVERY STRUCTURES")
    print("-" * 90)

    print(
        f"Zero-delivery innings: "
        f"{len(zero_delivery_innings):,}"
    )

    if zero_delivery_innings:

        for item in zero_delivery_innings[:20]:
            print(item)

    print()
    print(
        f"Empty overs: "
        f"{len(empty_overs):,}"
    )

    if empty_overs:

        for item in empty_overs[:20]:
            print(item)

    # -------------------------------------------------------------------------
    print()
    print("13. MISSING METADATA")
    print("-" * 90)

    if missing_metadata:

        for key, count in missing_metadata.items():
            print(
                f"{key}: {count:,}"
            )

    else:

        print("No missing metadata.")

    # =========================================================================
    # VALIDATION
    # =========================================================================

    print()
    print("=" * 90)
    print("SPECIAL-CASE VALIDATION")
    print("=" * 90)

    passed = 0
    failed = 0
    warnings = 0

    def check(condition, label):

        nonlocal passed, failed

        if condition:
            print(f"PASS: {label}")
            passed += 1
        else:
            print(f"FAIL: {label}")
            failed += 1

    def warn(label):

        nonlocal warnings

        print(f"WARN: {label}")
        warnings += 1

    # -------------------------------------------------------------------------
    # Basic universe
    # -------------------------------------------------------------------------

    check(
        matches == 918,
        "Expected 918 Test matches"
    )

    check(
        len(one_innings)
        + len(two_innings)
        + len(three_innings)
        + len(four_innings)
        == matches,
        "All matches accounted for by innings structure"
    )

    check(
        players_without_registry == [],
        "All declared players have registry IDs"
    )

    # -------------------------------------------------------------------------
    # Run reconciliation
    # -------------------------------------------------------------------------

    check(
        total_runs == batter_runs + total_extras,
        "Total runs = batter runs + extras"
    )

    # -------------------------------------------------------------------------
    # Wicket classification
    # -------------------------------------------------------------------------

    check(
        sum(wicket_kinds.values())
        == bowler_credit_wickets
        + non_bowler_wickets
        + sum(unknown_wicket_kinds.values()),
        "Every wicket event has a classification"
    )

    check(
        len(unknown_wicket_kinds) == 0,
        "No unknown wicket types"
    )

    # -------------------------------------------------------------------------
    # Test-specific structures
    # -------------------------------------------------------------------------

    if declared_innings > 0:
        check(
            True,
            "Declared innings detected and available for processor handling"
        )
    else:
        warn("No declared innings found")

    if miscounted_overs > 0:
        warn(
            "Miscounted overs exist; processor must use actual delivery "
            "records rather than overs × 6."
        )

    # -------------------------------------------------------------------------
    # Penalty runs
    # -------------------------------------------------------------------------

    if penalty_runs > 0:
        warn(
            "Penalty runs exist and must be preserved in team/match totals."
        )

    # -------------------------------------------------------------------------
    # Follow-on
    # -------------------------------------------------------------------------

    if len(follow_on_candidates) > 0:
        warn(
            "Follow-on candidates exist; do not infer follow-on solely "
            "from innings count."
        )

    # -------------------------------------------------------------------------
    # Outcomes
    # -------------------------------------------------------------------------

    check(
        outcomes.get("DRAW", 0) > 0,
        "Draw outcomes detected"
    )

    # -------------------------------------------------------------------------
    # Final
    # -------------------------------------------------------------------------

    print()
    print(
        f"SPECIAL-CASE SUMMARY: "
        f"PASS={passed} "
        f"WARN={warnings} "
        f"FAIL={failed}"
    )

    if failed == 0:

        print()
        print(
            "TEST SPECIAL-CASE AUDIT: PASS "
            "(with informational warnings where appropriate)"
        )

    else:

        print()
        print(
            "TEST SPECIAL-CASE AUDIT: FAIL"
        )

    print("=" * 90)


if __name__ == "__main__":
    main()