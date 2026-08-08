from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from pytest_console_scripts import RunResult, ScriptRunner

import pytest

from conda_recipe_v2_schema import __version__
from conda_recipe_v2_schema.cli import CLI

HERE = Path(__file__).parent
ROOT = HERE.parent
SCHEMA = ROOT / "schema.json"
EXAMPLES = ROOT / "examples"
VALID = EXAMPLES.glob("valid/*/recipe.yaml")
INVALID = EXAMPLES.rglob("invalid/*.yaml")


@pytest.mark.parametrize(
    ("expect_rc", "args", "check"),
    [
        (0, ["--version"], lambda r: __version__ in r.stdout),
        (0, ["--help"], None),
        (0, ["generate"], lambda r: r.stdout == SCHEMA.read_text(encoding="utf-8")),
        *[(0, ["validate", f"{v}"], lambda r: r.stderr.startswith("0 findings")) for v in VALID],
        *[
            (None, ["validate", f"{i}"], lambda r: r.stderr.splitlines()[-1].startswith("!!!"))
            for i in INVALID
        ],
    ],
)
def test_cli_ok(
    script_runner: ScriptRunner,
    expect_rc: int | None,
    args: list[str],
    check: Callable[[RunResult], bool] | None,
) -> None:
    res = script_runner.run([CLI, *args])
    rc = res.returncode
    assert check is None or check(res)
    assert (rc == expect_rc) if expect_rc is not None else rc
