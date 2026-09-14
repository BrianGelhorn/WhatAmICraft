#!/usr/bin/env python3
"""Validate a visual-property family and its optional clue assignment."""
import argparse
import json
from pathlib import Path
import sys

FORBIDDEN_ATTRIBUTES = {"texture", "sound", "environment", "quantities", "montage"}
NO_BANK = object()
STATUS = {
    "documentation": "documented",
    "mechanics": "mechanics_pending",
    "candidate_preservation": "candidate_preservation_pending",
    "visual": "visual_pending",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, names, where):
    require(isinstance(value, dict), f"{where}: expected object")
    require(set(value) == set(names.split()), f"{where}: expected fields: {names}")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def identifiers(value, where, minimum=1):
    require(isinstance(value, list) and len(value) >= minimum and all(text(item) for item in value), f"{where}: expected at least {minimum} nonempty IDs")
    require(len(value) == len(set(value)), f"{where}: IDs must be unique")


def validate_episode_bank(bank):
    require(isinstance(bank, dict) and isinstance(bank.get("episodes"), list), "episode bank: expected object with episodes list")


def validate_source_cases(cases, targets, bank):
    require(isinstance(cases, list) and len(cases) == len(targets), "source_cases: exactly one cited case per target required")
    cited_targets = []
    for case in cases:
        fields(case, "target_id episode_id clue_index clue_text version source fact_ids", "source_cases[]")
        require(text(case["target_id"]) and text(case["episode_id"]) and text(case["clue_text"]) and text(case["version"]), "source_cases[]: target, episode, clue text and version required")
        require(type(case["clue_index"]) is int and 1 <= case["clue_index"] <= 3, "source_cases[].clue_index: expected 1..3")
        require(case["source"] == "data/quiz-copy-episodes.json", "source_cases[].source: expected read-only episode bank path")
        require(isinstance(case["fact_ids"], list) and all(text(item) for item in case["fact_ids"]), "source_cases[].fact_ids: expected optional string IDs")
        cited_targets.append(case["target_id"])
        if bank is not NO_BANK:
            episodes = [episode for episode in bank["episodes"] if isinstance(episode, dict) and episode.get("id") == case["episode_id"]]
            require(len(episodes) == 1, "source_cases[].episode_id: expected exactly one source episode")
            episode = episodes[0]
            answer = episode.get("answer")
            clues = episode.get("clues")
            require(isinstance(answer, dict) and answer.get("id") == case["target_id"], "source_cases[].target_id: differs from source answer")
            require(answer.get("version") == case["version"], "source_cases[].version: differs from source answer version")
            require(isinstance(clues, list) and len(clues) == 3 and isinstance(clues[case["clue_index"] - 1], dict) and clues[case["clue_index"] - 1].get("text") == case["clue_text"], "source_cases[].clue_text: differs from literal source clue")
    require(set(cited_targets) == set(targets) and len(cited_targets) == len(set(cited_targets)), "source_cases: citations must cover each distinct target exactly once")


def intersection(sets):
    result = set(sets[0])
    for values in sets[1:]:
        result &= set(values)
    return result


def validate_assignment(assignment, family_targets):
    fields(assignment, "episode_id clue_index target_id candidate_universe_status candidate_universe_ids visual_candidate_ids clue_matches certification", "assignment")
    require(text(assignment["episode_id"]) and text(assignment["target_id"]), "assignment: episode_id and target_id required")
    require(type(assignment["clue_index"]) is int and 1 <= assignment["clue_index"] <= 3, "assignment.clue_index: expected integer 1..3")
    require(assignment["target_id"] in family_targets, "assignment.target_id: must be one of the family's cited targets")
    universe = assignment["candidate_universe_ids"]
    visual = assignment["visual_candidate_ids"]
    identifiers(universe, "assignment.candidate_universe_ids", 2)
    identifiers(visual, "assignment.visual_candidate_ids", 2)
    require(set(visual) <= set(universe), "assignment.visual_candidate_ids: V must be drawn from the declared universe")
    require(assignment["target_id"] in universe, "assignment.target_id: target must remain in the declared universe")
    require(assignment["candidate_universe_status"] in ("provisional", "complete"), "assignment.candidate_universe_status: expected provisional or complete")
    expected_certification = "refused_incomplete_universe" if assignment["candidate_universe_status"] == "provisional" else "not_certified_semantic_review"
    require(assignment["certification"] == expected_certification, "assignment.certification: parser never certifies semantic truth")
    matches = assignment["clue_matches"]
    require(isinstance(matches, list) and len(matches) == 3, "assignment.clue_matches: exactly three declared M_i sets required")
    ordered = []
    for expected_index, match in enumerate(matches, 1):
        fields(match, "index candidate_ids", "assignment.clue_matches[]")
        require(match["index"] == expected_index, "assignment.clue_matches[].index: expected ordered 1..3")
        identifiers(match["candidate_ids"], "assignment.clue_matches[].candidate_ids", 2)
        require(set(match["candidate_ids"]) <= set(universe), "assignment.clue_matches[]: M_i must use declared universe candidates")
        ordered.append(match["candidate_ids"])
    selected = ordered[assignment["clue_index"] - 1]
    require(set(selected) <= set(visual), "assignment: selected M_i must be contained in visual candidates V")
    first_two = intersection(ordered[:2])
    all_three = intersection(ordered)
    require(len(first_two) >= 2, "assignment: first two cumulative matches must retain at least two candidates")
    require(len(first_two) < len(ordered[0]), "assignment: clue 2 must strictly reduce the accumulated candidates")
    require(all_three == {assignment["target_id"]}, "assignment: all three cumulative matches must leave only target_id")
    require(len(all_three) < len(first_two), "assignment: clue 3 must strictly reduce the accumulated candidates")


def validate(family, bank=NO_BANK):
    require(isinstance(family, dict), "family: expected object")
    if bank is not NO_BANK:
        validate_episode_bank(bank)
    allowed = {"id", "title", "predicate", "targets", "source_cases", "candidate_universe", "illustrated_part", "not_demonstrated", "forbidden_audiovisual_attributes", "case_versions", "status", "assignment"}
    required = allowed - {"assignment"}
    require(required <= set(family) <= allowed, "family: unsupported or missing fields; historical scene briefs are not compatible")
    require(text(family["id"]) and family["id"].startswith("F"), "id: expected family ID beginning F")
    require(text(family["title"]) and text(family["predicate"]), "title and predicate: required")
    identifiers(family["targets"], "targets", 2)
    validate_source_cases(family["source_cases"], family["targets"], bank)
    universe = family["candidate_universe"]
    fields(universe, "status candidate_ids scope", "candidate_universe")
    require(universe["status"] in ("provisional", "complete"), "candidate_universe.status: expected provisional or complete")
    identifiers(universe["candidate_ids"], "candidate_universe.candidate_ids", 2)
    require(set(family["targets"]) <= set(universe["candidate_ids"]), "candidate_universe: must preserve all cited targets")
    require(text(universe["scope"]), "candidate_universe.scope: explain coverage without cherry-picking")
    require(text(family["illustrated_part"]), "illustrated_part: required")
    require(isinstance(family["not_demonstrated"], list) and family["not_demonstrated"] and all(text(item) for item in family["not_demonstrated"]), "not_demonstrated: required concrete limits")
    forbidden = family["forbidden_audiovisual_attributes"]
    require(isinstance(forbidden, dict) and set(forbidden) == FORBIDDEN_ATTRIBUTES and all(text(explanation) for explanation in forbidden.values()), "forbidden_audiovisual_attributes: require nonempty explanations for texture, sound, environment, quantities and montage")
    fields(family["case_versions"], "generated_content historical_bank server_capture", "case_versions")
    require(all(text(version) for version in family["case_versions"].values()), "case_versions: each case version must be nonempty")
    fields(family["status"], "documentation mechanics candidate_preservation visual", "status")
    require(family["status"] == STATUS, "status: use documented/mechanics_pending/candidate_preservation_pending/visual_pending; never verified")
    if "assignment" in family:
        validate_assignment(family["assignment"], family["targets"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family", type=Path)
    parser.add_argument("--episode-bank", type=Path, help="Read-only source check for cited target, literal clue and version")
    args = parser.parse_args()
    try:
        family = json.loads(args.family.read_text(encoding="utf-8-sig"))
        if args.episode_bank:
            validate(family, json.loads(args.episode_bank.read_text(encoding="utf-8-sig")))
        else:
            validate(family)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: family structure and declared candidate sets validated. " + ("Citations matched read-only episode bank. " if args.episode_bank else "Source bank NOT checked. ") + "No semantic, mechanics, candidate-completeness, visual, UI, capture or render certification was made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
