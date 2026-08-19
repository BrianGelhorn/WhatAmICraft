#!/usr/bin/env python3
from publish_worker import choose_generation_format
from video_formats import priority_targets

settings = {"clues": {"enabled": True, "priority": 1}}
inventory = {"formats": {"clues": {"pending": [], "candidates": [], "missing": ["mc-03"]}}}
config = {"generation": {"formats": settings, "targetStock": 8}}

assert priority_targets(settings, 8) == {"clues": 8}
assert choose_generation_format(config, inventory) == "clues"
print("ok: definitive quiz is the only generation format")
