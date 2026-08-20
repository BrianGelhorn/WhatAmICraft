#!/usr/bin/env python3
"""Small, dependency-free guardrail for Remotion template manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


BAD_SOURCE = re.compile(r"^(?:https?://|[A-Za-z]:[\\/]|/)")
BAD_CODE = {
    "CSS transition": re.compile(r"\btransition\s*:", re.IGNORECASE),
    "CSS animation": re.compile(r"\banimation\s*:", re.IGNORECASE),
    "randomness": re.compile(r"Math\.random\s*\("),
    "wall clock": re.compile(r"(?:Date\.now|new\s+Date\s*\()"),
    "timer": re.compile(r"(?:setTimeout|setInterval)\s*\("),
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate(manifest_path: Path, root: Path, source_dir: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - message is the useful output
        return [f"manifest JSON inválido: {exc}"]

    for key in ("compositionId", "fps", "durationInFrames", "intro", "automation", "audio", "scenes", "animationPolicy"):
        if key not in manifest:
            fail(errors, f"falta {key}")

    if manifest.get("fps", 0) <= 0 or manifest.get("durationInFrames", 0) <= 0:
        fail(errors, "fps y durationInFrames deben ser positivos")

    intro = manifest.get("intro", {})
    hook_duration = intro.get("hookDurationFrames")
    handoff_duration = intro.get("handoffDurationFrames")
    content_start = intro.get("contentStartFrame")
    max_content_start = intro.get("maxContentStartFrame", 45)
    if not isinstance(hook_duration, int) or not 12 <= hook_duration <= 180:
        fail(errors, "intro.hookDurationFrames debe estar entre 12 y 180")
    if not isinstance(handoff_duration, int) or not 6 <= handoff_duration <= 15:
        fail(errors, "intro.handoffDurationFrames debe estar entre 6 y 15")
    if not isinstance(content_start, int) or content_start < 0 or content_start > max_content_start:
        fail(errors, f"intro.contentStartFrame debe iniciar el contenido antes de {max_content_start} frames")
    if isinstance(content_start, int) and isinstance(hook_duration, int) and isinstance(handoff_duration, int) and content_start > hook_duration + handoff_duration:
        fail(errors, "intro.contentStartFrame ocurre después del hook y el pase definidos")

    automation = manifest.get("automation", {})
    required_automation = ("format", "inputPath", "schemaPath", "producer", "generatedConfigPath", "editableFields", "generatedFields")
    for key in required_automation:
        if key not in automation:
            fail(errors, f"missing automation.{key}")
    if automation.get("inputPath", "").startswith("src/"):
        fail(errors, "automation.inputPath must point to editable JSON, not src/")
    if not isinstance(automation.get("editableFields"), list) or not automation.get("editableFields"):
        fail(errors, "automation.editableFields must contain at least one field")
    for path_key in ("inputPath", "schemaPath", "producer", "generatedConfigPath"):
        path_value = automation.get(path_key)
        if isinstance(path_value, str) and not (root / path_value).is_file():
            fail(errors, f"automation.{path_key} does not exist: {path_value}")

    scenes = manifest.get("scenes", [])
    cursor = 0
    for scene in scenes:
        start = scene.get("from")
        duration = scene.get("durationInFrames")
        if start != cursor:
            fail(errors, f"hueco o solapamiento en escena {scene.get('id', '?')}: esperaba frame {cursor}, llegó {start}")
        if not isinstance(duration, int) or duration <= 0:
            fail(errors, f"duración inválida en escena {scene.get('id', '?')}")
        else:
            cursor = start + duration
    if scenes and cursor != manifest.get("durationInFrames"):
        fail(errors, f"las escenas terminan en {cursor}, no en {manifest.get('durationInFrames')}")

    audio = manifest.get("audio", {})
    status = audio.get("status", "pending")
    allowed = set(audio.get("allowedSources", []))
    cues = audio.get("cues", [])
    if status not in {"pending", "complete"}:
        fail(errors, "audio.status must be pending or complete")
    if status == "pending" and (allowed or cues):
        fail(errors, "visual-only stage must have empty allowedSources and cues")
    if status == "complete" and (not allowed or not cues):
        fail(errors, "audio-complete stage needs sources and cues")
    for src in allowed:
        if BAD_SOURCE.match(src) or not src.startswith("audio/"):
            fail(errors, f"fuente no local o fuera de public/audio: {src}")
        elif not (root / "public" / src).is_file():
            fail(errors, f"fuente inexistente: public/{src}")

    voice_ranges: list[tuple[int, int, str]] = []
    for cue in cues:
        src = cue.get("src")
        start = cue.get("from")
        duration = cue.get("durationInFrames")
        role = cue.get("role")
        if src not in allowed:
            fail(errors, f"cue {cue.get('id', '?')} usa audio no autorizado: {src}")
        if not isinstance(start, int) or not isinstance(duration, int) or start < 0 or duration <= 0:
            fail(errors, f"timing inválido en cue {cue.get('id', '?')}")
        if not isinstance(cue.get("volume"), (int, float)) or not 0 <= cue["volume"] <= 1:
            fail(errors, f"volumen inválido en cue {cue.get('id', '?')}")
        if cue.get("visualEvent") is None:
            fail(errors, f"falta visualEvent en cue {cue.get('id', '?')}")
        if not isinstance(cue.get("maxOffsetFrames"), int) or cue["maxOffsetFrames"] < 0:
            fail(errors, f"maxOffsetFrames inválido en cue {cue.get('id', '?')}")
        if role == "voice" and isinstance(start, int) and isinstance(duration, int):
            voice_ranges.append((start, start + duration, cue.get("id", "?")))

    for index, (start, end, cue_id) in enumerate(voice_ranges):
        for other_start, other_end, other_id in voice_ranges[index + 1 :]:
            if start < other_end and other_start < end:
                fail(errors, f"voces solapadas: {cue_id} y {other_id}")

    policy = manifest.get("animationPolicy", {})
    if policy.get("allowCssTransitions") is not False:
        fail(errors, "animationPolicy debe prohibir CSS transitions")
    if policy.get("allowRandomness") is not False:
        fail(errors, "animationPolicy debe prohibir randomness")

    if source_dir.is_dir():
        for path in source_dir.rglob("*"):
            if path.suffix not in {".ts", ".tsx", ".js", ".jsx"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in BAD_CODE.items():
                if pattern.search(text):
                    fail(errors, f"{label} detectado en {path}")
    else:
        fail(errors, f"source-dir inexistente: {source_dir}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--source-dir", type=Path, required=True)
    args = parser.parse_args()
    errors = validate(args.manifest, args.root.resolve(), args.source_dir)
    if errors:
        print("template contract: FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("template contract: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
