import json
import subprocess
import sys

from investopt.generator import generate
from investopt.warehouse import build


def test_idempotent_warehouse(warehouse):
    before = json.loads((warehouse / "artifacts/reconciliation.json").read_text())
    after = build(warehouse)
    assert before["lead_count"] == after["lead_count"]
    assert abs(before["spend_mart_usd"] - after["spend_mart_usd"]) < 1e-8


def test_cli_error_is_nonzero(tmp_path):
    command = subprocess.run(
        [sys.executable, "-m", "investopt", "smoke", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert command.returncode == 1 and "Run:" in command.stderr


def test_cli_smoke_and_help(completed):
    command = subprocess.run(
        [sys.executable, "-m", "investopt", "smoke", "--root", str(completed)],
        capture_output=True,
        text=True,
    )
    assert command.returncode == 0 and json.loads(command.stdout)["passed"]
    help_result = subprocess.run(
        [sys.executable, "-m", "investopt", "--help"], capture_output=True, text=True
    )
    assert all(c in help_result.stdout for c in ["demo", "experiment", "optimize", "train"])


def test_small_alternate_volume(tmp_path):
    result = generate(seed=99, leads=100, root=tmp_path)
    assert result["row_counts"]["leads"] == 100
    assert result["lead_end_date"] == "2025-03-06"
