import json
import pytest
import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError


@pytest.fixture(
    scope="module",
    params=[
        "mamba",
        "xtensor",
        "zlib"
    ],
)
def valid_recipe(request) -> str:
    recipe_name = request.param
    with open(f"examples/valid/{recipe_name}/recipe.yaml") as f:
        recipe = f.read()
    recipe_yml = yaml.safe_load(recipe)
    return recipe_yml


@pytest.fixture(
    scope="module",
    params=[
        "complex1",
        "simple1",
    ],
)
def invalid_recipe(request) -> str:
    recipe_name = request.param
    with open(f"examples/invalid/{recipe_name}.yaml") as f:
        recipe = f.read()
    recipe_yml = yaml.safe_load(recipe)
    return recipe_yml


@pytest.fixture()
def recipe_schema():
    with open("schema.json", "r") as f:
        schema = json.load(f)
    return schema


def test_recipe_schema_valid(recipe_schema, valid_recipe):
    validate(instance=valid_recipe, schema=recipe_schema)


def test_recipe_schema_invalid(recipe_schema, invalid_recipe):
    with pytest.raises(ValidationError):
        validate(instance=invalid_recipe, schema=recipe_schema)
