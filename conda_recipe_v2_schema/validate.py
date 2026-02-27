"""Command line utility for checking a recipe."""

from __future__ import annotations

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

from .model import ComplexRecipe, SimpleRecipe

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


def get_validator(schema: Path | None = None) -> Draft7Validator:
    """Get a JSON schema validator for the recipe from the built schema."""
    schema = schema or SCHEMA
    raw = yaml.safe_load(schema.read_text(encoding="utf-8"))
    if not raw:
        msg = (
            f"could not retrieve the schema from {schema};"
            " maybe run `conda-recipe-v2-schema generate`"
        )
        raise RuntimeError(msg)
    return Draft7Validator(raw, format_checker=Draft7Validator.FORMAT_CHECKER)


def check_one_local(path: Path, validator: Draft7Validator) -> Iterator[Any]:
    """Validate one local path."""
    recipe = yaml.safe_load(path.read_text(encoding="utf-8"))
    for error in validator.iter_errors(recipe):
        yield {
            "path": "/".join(["#", *error.path, ""]),
            "schema_path": "/".join(["#", *error.absolute_schema_path, ""]),
            "message": error.message,
        }
    try:
        model_cls = ComplexRecipe if "outputs" in recipe else SimpleRecipe
        model_cls(**recipe)
    except Exception as err:
        yield {"pydantic": f"{err}"}


def check_one_recipe(path_or_url: str, validator: Draft7Validator, work_dir: Path) -> Iterator[Any]:
    """Validate one path or URL."""
    url = parse.urlparse(path_or_url)
    path: Path | None = None
    if url.scheme in {"file"}:
        path = Path(url.path)
    elif url.scheme in {"http", "https"}:
        sha = hashlib.sha256(path_or_url.encode()).hexdigest()
        path = work_dir / f"{sha}/recipe.yaml"
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                request.urlretrieve(path_or_url, path)
            except Exception as err:
                yield {"message": f"Failed to download {path_or_url}: {err}"}
    elif not url.scheme:
        path = Path(path_or_url)

    if not (path and path.exists()):
        yield {"message": f"Couldn't figure out what to do with {path_or_url}"}
        return

    yield from check_one_local(path, validator)


def check_recipes(
    recipes: list[str],
    work_dir: Path,
    conda_forge: list[str] | None = None,
    schema: Path | None = None,
) -> dict[str, Any]:
    """Check all the recipes."""
    validator = get_validator(schema)
    cf = conda_forge or []
    recipes = sorted(recipes + [CF_TEMPLATE.format(recipe=recipe) for recipe in cf])
    return {recipe: [*check_one_recipe(recipe, validator, work_dir)] for recipe in recipes}


def main(kwargs: dict[str, Any]) -> int:
    """Get the count of validation errors from the CLI arguments and print a reports."""
    work_dir = kwargs.pop("work_dir")
    no_pretty = kwargs.pop("no_pretty")
    quiet = kwargs.pop("quiet")
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
    if count and not quiet:
        text = yaml.safe_dump(
            {recipe: findings for recipe, findings in findings_by_recipe.items() if findings},
            default_flow_style=False,
        )
        print(text if no_pretty else highlight(text, YamlJinjaLexer(), Terminal256Formatter()))
    print(
        f"{'!!! ' if count else ''}{count} findings in {len(findings_by_recipe)} recipes",
        file=sys.stderr,
    )
    return count
