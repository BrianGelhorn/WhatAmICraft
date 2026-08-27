#!/usr/bin/env python3

import argparse
import json
import re
import sys
from pathlib import Path


ALLOWED_KINDS = {
    "block", "enchantment", "food", "item", "mineral", "mob", "plant",
    "potion", "structure", "tool", "weapon",
}
ALLOWED_MODES = {"open_answer", "multiple_choice"}
ALLOWED_SCOPES = {"family", "target", "variant"}
ALLOWED_SOURCE_TYPES = {"minecraft-data", "wiki", "inference"}
ALLOWED_DIFFICULTIES = {"easy", "medium", "hard", "specific"}
PRESENTATION_ROLES = ("property-state", "action-interaction", "origin-context")

STOP_WORDS = {
    "a", "an", "and", "are", "be", "can", "for", "i", "in", "is", "me",
    "my", "of", "on", "the", "to", "with", "you",
}


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def mentions(text: str, term: str) -> bool:
    return bool(term and re.search(rf"(?<!\w){re.escape(term)}(?!\w)", text))


def string_list(value, field: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list of strings")
        return []
    if not all(isinstance(item, str) for item in value):
        errors.append(f"{field} must be a list of strings")
        return []
    return value


def content_tokens(value: str) -> set[str]:
    return {token for token in normalize(value).split() if token not in STOP_WORDS}


def validate_presentation(clue: dict, index: int, fact_ids: list[str], required: bool, errors: list[str]) -> None:
    presentation = clue.get("presentation")
    if presentation is None:
        if required:
            errors.append(f"Clue {index}.presentation is required")
        return
    if not isinstance(presentation, dict):
        errors.append(f"Clue {index}.presentation must be an object")
        return
    expected_role = PRESENTATION_ROLES[index - 1] if index <= len(PRESENTATION_ROLES) else None
    if expected_role and presentation.get("role") != expected_role:
        errors.append(f"Clue {index}.presentation.role must be {expected_role}")
    display_text = presentation.get("display_text")
    if not isinstance(display_text, str) or not display_text.strip() or len(display_text) > 54:
        errors.append(f"Clue {index}.presentation.display_text must contain 1-54 characters")
    fragments = string_list(presentation.get("fragments", []), f"Clue {index}.presentation.fragments", errors)
    if not 1 <= len(fragments) <= 2 or any(not fragment.strip() or len(fragment) > 28 for fragment in fragments):
        errors.append(f"Clue {index}.presentation.fragments needs 1-2 texts of at most 28 characters")
    emphasis_words = string_list(presentation.get("emphasis_words", []), f"Clue {index}.presentation.emphasis_words", errors)
    if len(emphasis_words) > 3 or any(not word.strip() or len(word) > 18 for word in emphasis_words):
        errors.append(f"Clue {index}.presentation.emphasis_words allows at most 3 words of 18 characters")
    visual = presentation.get("visual")
    if not isinstance(visual, dict):
        errors.append(f"Clue {index}.presentation.visual must be an object")
        return
    prefab = visual.get("prefab")
    if not isinstance(prefab, str) or not prefab.strip() or normalize(prefab) in {"generic", "random", "flash"}:
        errors.append(f"Clue {index}.presentation.visual.prefab must name an implemented semantic prefab")
    steps = visual.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 2:
        errors.append(f"Clue {index}.presentation.visual.steps needs 1-2 steps")
        return
    if len(steps) != len(fragments):
        errors.append(f"Clue {index}.presentation fragments and visual steps must have equal length")
    starts = []
    for step_index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            errors.append(f"Clue {index}.presentation.visual.steps[{step_index}] must be an object")
            continue
        if not isinstance(step.get("type"), str) or not step["type"].strip():
            errors.append(f"Clue {index}.presentation.visual.steps[{step_index}].type is required")
        if step.get("fact_id") not in fact_ids:
            errors.append(f"Clue {index}.presentation.visual.steps[{step_index}].fact_id must belong to the clue")
        start = step.get("from")
        if isinstance(start, bool) or not isinstance(start, (int, float)) or not 0 <= start <= 0.9:
            errors.append(f"Clue {index}.presentation.visual.steps[{step_index}].from must be between 0 and 0.9")
        else:
            starts.append(start)
    if starts and (starts[0] != 0 or starts != sorted(set(starts))):
        errors.append(f"Clue {index}.presentation visual steps must start at 0 with unique ascending times")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Minecraft clue episode")
    parser.add_argument("episode_json", type=Path)
    parser.add_argument("--require-presentation", action="store_true")
    args = parser.parse_args()

    try:
        data = json.loads(args.episode_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "errors": [f"Invalid JSON: {error}"], "warnings": []}, ensure_ascii=False, indent=2))
        return 1

    episode = data.get("episode", data)
    if not isinstance(episode, dict):
        print(json.dumps({"valid": False, "errors": ["Episode must be an object"], "warnings": []}, ensure_ascii=False, indent=2))
        return 1

    target = episode.get("target", {})
    clues = episode.get("clues", [])
    candidates = episode.get("candidates", [])
    errors, warnings = [], []

    if not isinstance(target, dict):
        errors.append("target must be an object")
        target = {}
    if not isinstance(clues, list):
        errors.append("clues must be a list")
        clues = []
    if not isinstance(candidates, list) or not all(isinstance(candidate, str) for candidate in candidates):
        errors.append("candidates must be a list of strings")
        candidates = []

    target_id = target.get("id")
    required_target_fields = ("id", "display_name", "edition", "version", "kind", "family")
    for field in required_target_fields:
        if not target.get(field):
            errors.append(f"Missing target.{field}")
    if target.get("kind") not in ALLOWED_KINDS:
        errors.append(f"target.kind must be one of {sorted(ALLOWED_KINDS)}")

    mode = episode.get("mode")
    if mode not in ALLOWED_MODES:
        errors.append(f"mode must be one of {sorted(ALLOWED_MODES)}")
    if episode.get("difficulty") not in ALLOWED_DIFFICULTIES:
        errors.append(f"difficulty must be one of {sorted(ALLOWED_DIFFICULTIES)}")
    if not episode.get("clue_count_reason"):
        errors.append("Missing clue_count_reason")

    if len(candidates) != len(set(candidates)):
        errors.append("candidates contains duplicates")
    if target_id and target_id not in candidates:
        errors.append("Target is absent from candidates")

    expected_count = episode.get("clue_count")
    if expected_count != 3:
        errors.append("clue_count must be exactly 3")
    if expected_count != len(clues):
        errors.append(f"Expected {expected_count} clues, found {len(clues)}")

    facts = episode.get("facts", [])
    if not isinstance(facts, list):
        errors.append("facts must be a list")
        facts = []
    fact_by_id = {}
    fact_matches_by_id = {}
    fact_semantics = {}
    for fact in facts:
        if not isinstance(fact, dict) or not fact.get("id"):
            errors.append("Every fact needs an id")
            continue
        fact_id = fact["id"]
        if fact_id in fact_by_id:
            errors.append(f"Duplicate fact id: {fact_id}")
        fact_by_id[fact_id] = fact
        if fact.get("scope") not in ALLOWED_SCOPES:
            errors.append(f"Fact {fact_id} has an invalid scope")
        if fact.get("source_type") not in ALLOWED_SOURCE_TYPES:
            errors.append(f"Fact {fact_id} has an invalid source_type")
        if not fact.get("source"):
            errors.append(f"Fact {fact_id} has no source")
        if not fact.get("relation"):
            errors.append(f"Fact {fact_id} has no relation")
        if not fact.get("semantic_key"):
            errors.append(f"Fact {fact_id} has no semantic_key")
        if not isinstance(fact.get("verified"), bool):
            errors.append(f"Fact {fact_id}.verified must be boolean")
        if fact.get("source_type") == "inference" and fact.get("verified") is True:
            errors.append(f"Inference fact {fact_id} cannot be verified=true")
        matches = string_list(fact.get("matches_candidates", []), f"Fact {fact_id}.matches_candidates", errors)
        unknown_matches = set(matches).difference(candidates)
        if unknown_matches:
            errors.append(f"Fact {fact_id} references unknown candidates: {sorted(unknown_matches)}")
        if target_id and target_id not in matches:
            errors.append(f"Fact {fact_id} is not true for the target")
        fact_matches_by_id[fact_id] = set(matches)
        fact_semantics[fact_id] = (str(fact.get("relation", "")), str(fact.get("semantic_key", "")))

    sources = episode.get("sources", [])
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
    else:
        for source in sources:
            if not isinstance(source, dict) or not source.get("title") or not source.get("url"):
                errors.append("Every source needs title and url")

    target_aliases = string_list(target.get("aliases", []), "target.aliases", errors)
    forbidden_answer_terms = string_list(target.get("forbidden_terms", []), "target.forbidden_terms", errors)
    forbidden_mechanics = string_list(target.get("forbidden_clue_terms", []), "target.forbidden_clue_terms", errors)
    aliases = {normalize(target_id or ""), normalize(target.get("display_name", ""))}
    aliases.update(normalize(value) for value in target_aliases if value)
    forbidden_terms = {
        normalize(value)
        for value in [target.get("variant"), *forbidden_answer_terms]
        if value
    }
    forbidden_clue_terms = {
        normalize(value)
        for value in forbidden_mechanics
        if value
    }
    candidate_aliases = episode.get("candidate_aliases", {})
    peer_names = {normalize(candidate) for candidate in candidates if candidate != target_id}
    if candidate_aliases is not None and not isinstance(candidate_aliases, dict):
        errors.append("candidate_aliases must be an object of string lists")
        candidate_aliases = {}
    if isinstance(candidate_aliases, dict):
        for candidate, values in candidate_aliases.items():
            if candidate in candidates and candidate != target_id:
                peer_names.update(normalize(value) for value in string_list(values, f"candidate_aliases.{candidate}", errors) if value)
    comparison_pattern = re.compile(
        r"\b(like|unlike|similar to|same as|compared (?:to|with)|igual que|a diferencia de|similar a|tanto .+ como)\b"
    )
    aliases.discard("")
    remaining = set(candidates)
    remaining_counts = []
    previous_texts = set()
    previous_semantic_keys = set()
    previous_relations = set()
    previous_remaining_count = len(remaining)
    computed_clue_matches = []
    lexical_warnings = []

    for index, clue in enumerate(clues, start=1):
        if not isinstance(clue, dict):
            errors.append(f"Clue {index} must be an object")
            continue
        text = clue.get("text", "")
        norm_text = normalize(text)
        prior_texts = list(previous_texts)
        if not text:
            errors.append(f"Clue {index} has no text")
        if norm_text in previous_texts:
            errors.append(f"Clue {index} repeats an earlier clue")
        previous_texts.add(norm_text)
        if any(mentions(norm_text, alias) for alias in aliases):
            errors.append(f"Clue {index} leaks the answer")
        if any(mentions(norm_text, term) for term in forbidden_terms):
            errors.append(f"Clue {index} leaks a forbidden answer modifier")
        if any(mentions(norm_text, term) for term in forbidden_clue_terms):
            errors.append(f"Clue {index} leaks an iconic target mechanic")
        if comparison_pattern.search(norm_text):
            errors.append(f"Clue {index} uses forbidden comparative framing")
        named_peers = sorted(peer for peer in peer_names if peer and mentions(norm_text, peer))
        if named_peers:
            errors.append(f"Clue {index} names audited peer candidates: {named_peers}")

        fact_ids = string_list(clue.get("fact_ids", []), f"Clue {index}.fact_ids", errors)
        if not fact_ids:
            errors.append(f"Clue {index} has no fact_ids")
        else:
            unknown_facts = set(fact_ids).difference(fact_by_id)
            if unknown_facts:
                errors.append(f"Clue {index} references unknown facts: {sorted(unknown_facts)}")
        if clue.get("referent") != "target":
            errors.append(f"Clue {index} must declare referent=target")
        validate_presentation(clue, index, fact_ids, args.require_presentation, errors)

        fact_sets = [fact_matches_by_id[fact_id] for fact_id in fact_ids if fact_id in fact_matches_by_id]
        matches = set.intersection(*fact_sets) if fact_sets else set()
        declared_matches = string_list(clue.get("matches_candidates", []), f"Clue {index}.matches_candidates", errors)
        declared_set = set(declared_matches)
        if declared_set != matches:
            errors.append(
                f"Clue {index}.matches_candidates must equal the fact intersection: {sorted(matches)}"
            )
        if target_id and target_id not in matches:
            errors.append(f"Clue {index} is not true for the target")
        if len(matches) < 2:
            errors.append(f"Clue {index} is too revealing in isolation")
        remaining.intersection_update(matches)
        remaining_counts.append(len(remaining))
        if not remaining:
            errors.append(f"Clue {index} eliminates every candidate")
        if index < len(clues) and len(remaining) < 2:
            errors.append(f"Clue {index} makes the answer unique before the final clue")
        if index > 1 and len(remaining) >= previous_remaining_count:
            errors.append(f"Clue {index} does not reduce the remaining candidates")
        previous_remaining_count = len(remaining)

        semantic_pairs = [fact_semantics[fact_id] for fact_id in fact_ids if fact_id in fact_semantics]
        semantic_keys = {key for _, key in semantic_pairs if key}
        relations = {relation for relation, _ in semantic_pairs if relation}
        repeated_keys = semantic_keys.intersection(previous_semantic_keys)
        if repeated_keys:
            errors.append(f"Clue {index} repeats semantic facts: {sorted(repeated_keys)}")
        repeated_relations = relations.intersection(previous_relations)
        if repeated_relations:
            warnings.append(f"Clue {index} reuses relations already used: {sorted(repeated_relations)}")
        previous_semantic_keys.update(semantic_keys)
        previous_relations.update(relations)
        computed_clue_matches.append(sorted(matches))
        current_tokens = content_tokens(text)
        for prior_text in prior_texts:
            prior_tokens = content_tokens(prior_text)
            if len(current_tokens) >= 4 and len(prior_tokens) >= 4:
                overlap = len(current_tokens & prior_tokens) / max(1, len(current_tokens | prior_tokens))
                if overlap >= 0.72:
                    lexical_warnings.append(f"Clue {index} is lexically close to an earlier clue")
                    break

    declared_remaining = episode.get("remaining_after_each_clue")
    if not isinstance(declared_remaining, list):
        errors.append("Missing remaining_after_each_clue")
    elif declared_remaining != remaining_counts:
        errors.append(f"remaining_after_each_clue does not match calculated values: {remaining_counts}")

    if target.get("variant"):
        scopes = {
            fact_by_id[fid].get("scope")
            for clue in clues
            for fid in (clue.get("fact_ids", []) if isinstance(clue.get("fact_ids", []), list) else [])
            if fid in fact_by_id
        }
        if "variant" not in scopes:
            errors.append("Variant target lacks a variant-scoped clue")

    computed_unique = len(remaining) == 1 and target_id in remaining
    if episode.get("unique_answer") is not computed_unique:
        errors.append(f"unique_answer must be {computed_unique}")
    if not isinstance(episode.get("needs_review"), bool):
        errors.append("needs_review must be boolean")
    elif episode["needs_review"] == computed_unique:
        errors.append(f"needs_review must be {not computed_unique}")

    human_validation = episode.get("human_validation", {})
    for field in ("stable_referent", "progressive_reduction", "no_named_comparisons", "exact_answer_recoverable"):
        if human_validation.get(field) is not True:
            errors.append(f"human_validation.{field} must be true")
    if not human_validation.get("final_clue_rationale"):
        errors.append("human_validation.final_clue_rationale is required")
    for i in range(1, len(remaining_counts)):
        if remaining_counts[i] > remaining_counts[i - 1]:
            errors.append("Remaining candidate count increased unexpectedly")
    if len(clues) > 1 and all(remaining_counts[i] == remaining_counts[i - 1] for i in range(1, len(remaining_counts))):
        warnings.append("Clues do not progressively reduce candidates")
    if not computed_unique:
        errors.append(f"Final clues are ambiguous; remaining candidates: {sorted(remaining)}")

    warnings.extend(lexical_warnings)

    result = {
        "valid": not errors,
        "unique_answer": computed_unique,
        "remaining_after_each_clue": remaining_counts,
        "remaining_candidates": sorted(remaining),
        "audit": {
            "candidate_universe": sorted(candidates),
            "fact_matches": {fact_id: sorted(matches) for fact_id, matches in fact_matches_by_id.items()},
            "computed_clue_matches": computed_clue_matches,
            "semantic_keys": sorted({key for _, key in fact_semantics.values() if key}),
        },
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())

