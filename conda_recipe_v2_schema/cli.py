"""Command line interface for generating and checking instances of the schema."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__

CLI = "conda-recipe-v2-schema"
GENERATE = "generate"
VALIDATE = "validate"


def get_parser() -> argparse.ArgumentParser:
    """Build a command line parser."""
    parser = argparse.ArgumentParser(CLI)
    parser.add_argument("-v", "--version", action="version", version=f"{CLI} {__version__}")

    sub = parser.add_subparsers(dest="action")

    sub.add_parser(GENERATE, help="print the schema")

    validate = sub.add_parser(
        VALIDATE, help="validate local paths and URLs against the schema and model"
    )

    validate.add_argument(
        "recipes",
        nargs="*",
        help="a relative path or URL for a `recipe.yaml`; may be given multiple times",
    )
    validate.add_argument(
        "-w", "--work-dir", type=Path, help="a work folder to persist remote recipes between runs"
    )
    validate.add_argument(
        "-c",
        "--conda-forge",
        action="append",
        help="names of conda-forge recipe to check (no `-feedstock`); may be given multiple times",
    )
    validate.add_argument(
        "-u",
        "--no-pretty",
        action="store_true",
        help="disable syntax highlighting for YAML findings",
    )
    validate.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="minimize output",
    )
    validate.add_argument("-s", "--schema", type=Path, help="alternate path to the schema to use")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse command line arguments and dispatch to appropriate function."""
    parser = get_parser()
    ns = parser.parse_args(argv)
    kwargs = {**vars(ns)}
    action = kwargs.pop("action")
    if action == GENERATE:
        from . import model

        return model.main()
    elif action == VALIDATE:
        from . import validate

        return validate.main(kwargs)

    parser.parse_args(["--help"])
    return 1
