#!/usr/bin/env python3
"""Validate a single-shot design brief, not Minecraft commands or visual quality."""
import argparse
import json
import math
from pathlib import Path
import re
import sys

RECIPES = {"discovery", "decision", "danger", "recovery", "scale", "reveal", "search", "presence", "reaction"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, names, where):
    require(isinstance(value, dict), f"{where}: expected object")
    require(set(value) == set(names.split()), f"{where}: expected fields: {names}")


def text(value):
    return isinstance(value, str) and bool(value.strip())


def texts(value, where, minimum=1):
    require(isinstance(value, list) and len(value) >= minimum and all(text(s) for s in value), f"{where}: expected list of nonempty strings (minimum {minimum})")


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def vector(value):
    return isinstance(value, list) and len(value) == 3 and all(type(n) in (int, float) and math.isfinite(n) for n in value)


def validate(scene):
    fields(scene, "id title recipe status fps duration_frames hook_frame uses props spoiler_exclusions setup automation beats camera reset reject_if output", "scene")
    require(text(scene["id"]) and re.fullmatch(r"[GC](?!00)\d{2}", scene["id"]), "id: use G01..G99 or C01..C99; this does not register it on the server")
    require(text(scene["title"]), "title: required")
    require(text(scene["recipe"]) and scene["recipe"] in RECIPES, "recipe: unknown recipe")
    require(scene["status"] == "pendiente_de_ensayo", "status: this brief must remain pendiente_de_ensayo")
    require(type(scene["fps"]) is int and scene["fps"] == 30, "fps: expected 30")
    duration = scene["duration_frames"]
    require(integer(duration, 30, 300), "duration_frames: expected integer 30..300 (single shot)")
    require(integer(scene["hook_frame"], 0, min(44, duration - 1)), "hook_frame: must be visible before frame 45 and inside the clip")
    uses = scene["uses"]
    require(isinstance(uses, list) and len(uses) >= 3, "uses: at least three categories required")
    categories = set()
    for use in uses:
        fields(use, "category reason", "uses[]")
        require(text(use["category"]) and text(use["reason"]), "uses[]: category and narrative reason required")
        categories.add(use["category"].strip().casefold())
    require(len(categories) >= 3, "uses: categories must be distinct")
    for key in ("props", "spoiler_exclusions", "setup", "reset", "reject_if"):
        texts(scene[key], key)
    automation = scene["automation"]
    fields(automation, "setup action manual_actions notes", "automation")
    for key in ("setup", "action"):
        require(automation[key] in ("manual", "datapack", "mixed"), f"automation.{key}: expected manual, datapack or mixed")
    texts(automation["manual_actions"], "automation.manual_actions", 1 if any(automation[k] != "datapack" for k in ("setup", "action")) else 0)
    require(text(automation["notes"]), "automation.notes: explain limits")
    beats = scene["beats"]
    require(isinstance(beats, list) and len(beats) == 3, "beats: exactly three moments required")
    cursor = 0
    for beat in beats:
        fields(beat, "start end action visible", "beats[]")
        require(integer(beat["start"], 0, duration - 1) and integer(beat["end"], 0, duration - 1), "beats[]: frames must be integers inside clip")
        require(beat["start"] == cursor and beat["end"] >= cursor, "beats[]: inclusive intervals must be contiguous, ordered and nonempty")
        require(text(beat["action"]) and text(beat["visible"]), "beats[]: describe action and visible result")
        cursor = beat["end"] + 1
    require(cursor == duration, "beats: intervals must cover the full duration")
    require(scene["hook_frame"] <= beats[0]["end"], "hook_frame: event must occur in the first moment")
    camera = scene["camera"]
    fields(camera, "space movement fov keyframes framing", "camera")
    require(camera["space"] in ("local", "world"), "camera.space: expected local or world")
    require(camera["movement"] in ("fixed", "linear"), "camera.movement: expected fixed or linear")
    require(integer(camera["fov"], 30, 90), "camera.fov: expected constant integer 30..90")
    require(text(camera["framing"]), "camera.framing: explain vertical composition")
    frames = camera["keyframes"]
    require(isinstance(frames, list) and len(frames) >= 2, "camera.keyframes: at least two required")
    previous = -1
    for frame in frames:
        fields(frame, "frame position look_at", "camera.keyframes[]")
        require(integer(frame["frame"], 0, duration - 1) and frame["frame"] > previous, "camera.keyframes[]: frames must increase inside clip")
        require(vector(frame["position"]) and vector(frame["look_at"]), "camera.keyframes[]: expected finite XYZ vectors")
        require(frame["position"] != frame["look_at"], "camera.keyframes[]: camera cannot look at its own position")
        if camera["movement"] == "fixed":
            require(frame["position"] == frames[0]["position"] and frame["look_at"] == frames[0]["look_at"], "camera: fixed camera cannot change position or look_at")
        previous = frame["frame"]
    require(frames[0]["frame"] == 0 and frames[-1]["frame"] == duration - 1, "camera: keyframes must span the clip")
    require(text(scene["output"]) and re.fullmatch(r"mc_[a-z0-9_]+_scene_t\d{2}\.mp4", scene["output"]), "output: expected mc_<description>_scene_t01.mp4, not a path, loop or background")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("brief", type=Path)
    args = parser.parse_args()
    try:
        validate(json.loads(args.brief.read_text(encoding="utf-8-sig")))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: brief structure and timing. Reuse, mechanics, collisions and visual quality require review. Nothing was installed or rendered.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
