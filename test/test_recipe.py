import json
import pytest
import yaml
from jsonschema import validate

@pytest.fixture(
    scope="module",
    params=[
        "mamba",
        "xtensor",
        "zlib"
    ],
)
def recipe(request) -> str:
    recipe_name = request.param
    with open(f"examples/{recipe_name}/recipe.yaml") as f:
        recipe = f.read()
    recipe_yml = yaml.safe_load(recipe)
    return recipe_yml

@pytest.fixture()
def recipe_schema():
    with open("schema.json", "r") as f:
        schema = json.load(f)
    return schema


def test_recipe_schema(recipe_schema, recipe):
    validate(instance=recipe, schema=recipe_schema)
