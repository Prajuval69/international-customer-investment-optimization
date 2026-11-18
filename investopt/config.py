"""Explicit illustrative assumptions; never interpreted as current FX rates."""

import hashlib
import json
from pathlib import Path

import yaml

DEFAULTS = Path(__file__).parent / "defaults"


def configuration(root=None):
    values, hashes = {}, {}
    for name in ("markets", "scenario"):
        candidate = Path(root) / "config" / f"{name}.yaml" if root else DEFAULTS / f"{name}.yaml"
        file = candidate if candidate.exists() else DEFAULTS / f"{name}.yaml"
        raw = file.read_bytes()
        values[name] = yaml.safe_load(raw)
        hashes[name] = hashlib.sha256(raw).hexdigest()
    s = values["scenario"]
    if s["annual_discount_rate"] < 0:
        raise ValueError("Annual discount rate must be nonnegative")
    if any(m["usd_per_local_unit"] <= 0 for m in values["markets"]["markets"]):
        raise ValueError("All illustrative FX rates must be positive")
    return values, hashes


def write_json(file, value):
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps(value, indent=2, allow_nan=False, default=str), encoding="utf-8")
