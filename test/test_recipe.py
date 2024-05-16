import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jsonschema
import pytest
import yaml

if TYPE_CHECKING:
    from jsonschema.protocols import Validator

TAnyDict = dict[str, Any]

HERE = Path(__file__).parent
ROOT = HERE.parent
EXAMPLES = ROOT / "examples"
SCHEMA = ROOT / "schema.json"
UTF8 = {"encoding": "utf-8"}
INVALID = [p.name for p in (EXAMPLES / "invalid").glob("*.yaml")]
VALID = [p.name for p in (EXAMPLES / "valid").glob("*") if p.is_dir()]


@pytest.fixture(scope="module", params=VALID)
def valid_recipe(request: pytest.FixtureRequest) -> TAnyDict:
    recipe = EXAMPLES / "valid" / f"{request.param}" / "recipe.yaml"
    return dict(yaml.safe_load(recipe.read_text(**UTF8)))


@pytest.fixture(scope="module", params=INVALID)
def invalid_recipe(request: pytest.FixtureRequest) -> TAnyDict:
    recipe = EXAMPLES / "invalid" / f"{request.param}"
    return dict(yaml.safe_load(recipe.read_text(**UTF8)))


@pytest.fixture(scope="module")
def recipe_schema() -> TAnyDict:
    return dict(json.loads(SCHEMA.read_text(encoding="utf-8")))


@pytest.fixture(scope="module")
def validator(recipe_schema: TAnyDict) -> "Validator":
    validator_cls: "type[Validator]" = jsonschema.validators.validator_for(recipe_schema)
    return validator_cls(recipe_schema, format_checker=validator_cls.FORMAT_CHECKER)


def test_recipe_schema_valid(validator: "Validator", valid_recipe: TAnyDict) -> None:
    errors = [*validator.iter_errors(valid_recipe)]
    assert not errors


def test_recipe_schema_invalid(validator: "Validator", invalid_recipe: TAnyDict) -> None:
    errors = [*validator.iter_errors(invalid_recipe)]
    assert errors
