"""Public cross-platform command-line interface."""

import argparse
import json
import sys

from investopt.demo import demo, smoke
from investopt.experiment import experiment
from investopt.generator import generate
from investopt.ltv import train
from investopt.optimizer import optimize
from investopt.reporting import report
from investopt.validation import validate
from investopt.warehouse import build


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline SIMULATED acquisition analytics")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in [
        "generate",
        "validate",
        "build",
        "train",
        "experiment",
        "optimize",
        "report",
        "demo",
        "smoke",
    ]:
        command = sub.add_parser(name)
        command.add_argument(
            "--root", help="Independent pipeline output root (default project root)"
        )
        if name in {"generate", "train", "experiment", "demo"}:
            command.add_argument("--seed", type=int, default=42)
        if name in {"generate", "demo"}:
            command.add_argument("--leads", type=int, default=30000)
        if name == "generate":
            command.add_argument("--output", help="Custom raw Parquet output directory")
        if name == "optimize":
            command.add_argument("--budget", type=float, default=1000000)
    args = vars(parser.parse_args(argv))
    name = args.pop("command")
    functions = {
        "generate": generate,
        "validate": validate,
        "build": build,
        "train": train,
        "experiment": experiment,
        "optimize": optimize,
        "report": report,
        "demo": demo,
        "smoke": smoke,
    }
    try:
        result = functions[name](**args)
        if name == "train":
            result = {k: result[k] for k in ["model_version", "model", "baseline"]}
        elif name == "validate":
            result = {
                "passed": result["passed"],
                "checks": len(result["checks"]),
                "row_counts": result["row_counts"],
            }
        print(json.dumps(result, indent=2, default=str, allow_nan=False))
        return 0
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
