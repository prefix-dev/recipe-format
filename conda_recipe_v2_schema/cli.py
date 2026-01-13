"""Command line utility for checking a recipe."""

from __future__ import annotations

import argparse
import functools
import hashlib
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib import parse, request

import yaml
from jsonschema.validators import Draft7Validator
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers.templates import YamlJinjaLexer

from .model import ComplexRecipe, Recipe, SimpleRecipe

if TYPE_CHECKING:
    from collections.abc import Iterator

HERE = Path(__file__).parent
SCHEMA = HERE.parent / "schema.json"
CLI = "conda-recipe-v2-schema"
CF_TEMPLATE = (
    "https://raw.githubusercontent.com/conda-forge/{recipe}-feedstock/"
    "refs/heads/main/recipe/recipe.yaml"
)

# force unescaped multiline string formatting
yaml.representer.SafeRepresenter.add_representer(
    str,
    lambda dumper, data: dumper.represent_scalar(
        "tag:yaml.org,2002:str", data, style="|" if "\n" in data or len(data) > 80 else None
    ),
)


def get_parser() -> argparse.ArgumentParser:
    """Builda command line parser."""
    parser = argparse.ArgumentParser(CLI)
    parser.add_argument("recipes", nargs="*", help="a relative path or URL for a `recipe.yaml`")
    parser.add_argument(
        "--work-dir", type=Path, help="a work folder to persist remote recipes between runs"
    )
    parser.add_argument(
        "--conda-forge",
        "-c",
        action="append",
        help="names of conda-forge recipes to check (no `-feedstock`)",
    )
    parser.add_argument(
        "--no-pretty", action="store_true", help="disable syntax highlighting for YAML findings"
    )
    return parser


@functools.lru_cache(1)
def get_validator() -> Draft7Validator:
    schema: dict[str, Any] | None = None
    if SCHEMA.exists():
        schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
    else:
        schema = Recipe.json_schema()
    if not schema:
        msg = "could not retrieve the schema"
        raise RuntimeError(msg)

    return Draft7Validator(schema, format_checker=Draft7Validator.FORMAT_CHECKER)


def check_one_local(path: Path, validator: Draft7Validator) -> Iterator[Any]:
    """Validate one local path."""
    recipe = yaml.safe_load(path.read_text(encoding="utf-8"))
    for error in validator.iter_errors(recipe):
        yield {
            "path": "/".join(["#", *error.path, ""]),
            "schema_path": "/".join(["#", *error.absolute_schema_path, ""]),
            "message": error.message,
        }
    model_cls = ComplexRecipe if "outputs" in recipe else SimpleRecipe
    try:
        model_cls(**recipe)
    except Exception as err:
        yield {f"{model_cls.__name__}": f"{err}"}


def check_one_recipe(path_or_url: str, validator: Draft7Validator, work_dir: Path) -> Iterator[Any]:
    """Validate on path or URL."""
    url = parse.urlparse(path_or_url)
    path: Path | None = None
    if url.scheme in {"file"}:
        path = Path(url.path)
    elif url.scheme in {"http", "https"}:
        path = work_dir / f"{hashlib.sha256(path_or_url.encode())}/recipe.yaml"
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                request.urlretrieve(path_or_url, path)
            except Exception as err:
                yield {"message": f"Failed to download {path_or_url}: {err}"}

    if not (path and path.exists()):
        yield {"message": f"Couldn't figure out what to do with {path_or_url}"}
        return

    yield from check_one_local(path, validator)


def check_recipes(
    recipes: list[str],
    work_dir: Path,
    conda_forge: list[str] | None = None,
) -> dict[str, Any]:
    """Check all the recipes."""
    validator = get_validator()
    cf = conda_forge or []
    recipes = sorted(recipes + [CF_TEMPLATE.format(recipe=recipe) for recipe in cf])
    return {recipe: [*check_one_recipe(recipe, validator, work_dir)] for recipe in recipes}


def main(argv: list[str] | None = None):
    """Get the count of validation errors from the CLI arguments."""
    kwargs = {**vars(get_parser().parse_args(argv))}
    work_dir = kwargs.pop("work_dir")
    no_pretty = kwargs.pop("no_pretty")
    if work_dir is None:
        with tempfile.TemporaryDirectory(prefix=f"{CLI}-") as td:
            findings_by_recipe = check_recipes(work_dir=Path(td), **kwargs)
    else:
        findings_by_recipe = check_recipes(work_dir=work_dir, **kwargs)
    if not findings_by_recipe:
        print(
            "No recipes were checked; please provide some URLs or conda-forge names",
            file=sys.stderr,
        )
        return 1
    count = sum(map(len, findings_by_recipe.values()))
    if count:
        text = yaml.safe_dump(
            {recipe: findings for recipe, findings in findings_by_recipe.items() if findings},
            default_flow_style=False,
        )
        print(text if no_pretty else highlight(text, YamlJinjaLexer(), Terminal256Formatter()))
    print(f"{CLI}: {count} findings in {len(findings_by_recipe)} recipes", file=sys.stderr)
    return count
