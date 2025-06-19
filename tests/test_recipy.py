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


def test_perl_test_valid():
    """Test that recipes with a Perl test pass validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - perl:
          uses:
            - Call::Context
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    Recipe.validate_python(recipe_dict)


def test_perl_test_invalid_missing_uses():
    """Test that a Perl test without uses fails validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - perl: {}
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)


def test_r_test_valid():
    """Test that recipes with an R test pass validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - r:
          libraries:
            - ggplot2
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    Recipe.validate_python(recipe_dict)


def test_r_test_invalid_missing_libraries():
    """Test that an R test without libraries fails validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - r: {}
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)


def test_package_contents_strict_valid(recipe_schema):
    """Recipes with a boolean strict flag should validate successfully."""
    for strict_val in (True, False):
        recipe_yaml = f"""
        package:
          name: test
          version: 1.0.0
        tests:
          - package_contents:
              strict: {str(strict_val).lower()}
              files:
                - foo.txt
        """
        recipe_dict = yaml.safe_load(recipe_yaml)

        Recipe.validate_python(recipe_dict)

        validate(instance=recipe_dict, schema=recipe_schema)


def test_package_contents_strict_invalid_type(recipe_schema):
    """Non-boolean values for strict should fail validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - package_contents:
          strict: 123
    """
    recipe_dict = yaml.safe_load(recipe_yaml)

    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)

    with pytest.raises(ValidationError):
        validate(instance=recipe_dict, schema=recipe_schema)


def test_package_contents_exists_and_not_exists_valid(recipe_schema):
    """Recipes using files.exists / files.not_exists should validate successfully."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - package_contents:
          files:
            exists:
              - bar.txt
            not_exists:
              - secret.key
              - '*.pem'
    """
    recipe_dict = yaml.safe_load(recipe_yaml)

    Recipe.validate_python(recipe_dict)
    validate(instance=recipe_dict, schema=recipe_schema)


def test_package_contents_exists_invalid_type(recipe_schema):
    """Non-string/non-list values for exists should fail validation."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    tests:
      - package_contents:
          files:
            exists: 123
    """
    recipe_dict = yaml.safe_load(recipe_yaml)

    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)

    with pytest.raises(ValidationError):
        validate(instance=recipe_dict, schema=recipe_schema)
