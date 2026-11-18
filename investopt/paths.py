"""Portable project paths. INVESTOPT_HOME isolates independent pipeline runs."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    root: Path

    @property
    def raw(self):
        return self.root / "data" / "raw"

    @property
    def db(self):
        return self.root / "data" / "warehouse" / "analytics.duckdb"

    @property
    def artifacts(self):
        return self.root / "artifacts"

    @property
    def reports(self):
        return self.root / "reports"

    def prepare(self):
        for folder in (self.raw, self.db.parent, self.artifacts, self.reports):
            folder.mkdir(parents=True, exist_ok=True)
        return self


def paths(root=None):
    return Paths(Path(root or os.getenv("INVESTOPT_HOME", Path(__file__).parents[1])).resolve())
