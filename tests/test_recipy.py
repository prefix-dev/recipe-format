import json

import pytest
import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

from conda_recipe_v2_schema.model import Recipe


@pytest.fixture(
    scope="module",
    params=["mamba", "xtensor", "single-output", "zlib"],
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


def test_recipe_schema_not_changed(recipe_schema):
    assert recipe_schema == Recipe.json_schema()


def test_patches_valid_conditional():
    """Test that patches with conditionals inside a list pass validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    source:
      url: https://example.com/test.tar.gz
      patches:
        - file.patch
        - if: target_platform == 'win-64'
          then: windows.patch
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    # This should not raise an exception
    Recipe.validate_python(recipe_dict)


def test_patches_invalid_conditional():
    """Test that patches with standalone conditionals fail validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    source:
      url: https://example.com/test.tar.gz
      patches:
        if: target_platform == 'win-64'
        then: windows.patch
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    # This should raise a validation error
    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)
