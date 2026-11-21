import json

import pytest
import yaml
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError

from conda_recipe_v2_schema.model import Recipe, top_level_schema


@pytest.fixture(
    scope="module",
    params=["mamba", "xtensor", "single-output", "zlib", "staging", "post-process", "extras"],
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
        "dollarschema",
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
    assert recipe_schema == top_level_schema()


def test_requirements_extras_valid(recipe_schema):
    """Recipes with requirements.extras pass validation (CEP 44)."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    requirements:
      run:
        - main-dependency
      extras:
        diff:
          - textual-diff-view >=0.1.5,<0.2
        "full-extra.v2":
          - extra-dependency >=2
          - if: unix
            then: posix-only-dependency
    """
    recipe_dict = yaml.safe_load(recipe_yaml)

    Recipe.validate_python(recipe_dict)
    validate(instance=recipe_dict, schema=recipe_schema)


def test_requirements_extras_invalid_group_name(recipe_schema):
    """Extras group names must match the CEP 44 grammar `[a-z0-9_.+-]{1,64}`."""
    recipe_yaml = """
    package:
      name: test
      version: 1.0.0
    requirements:
      extras:
        Invalid_Name:
          - extra-dependency
    """
    recipe_dict = yaml.safe_load(recipe_yaml)

    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)

    with pytest.raises(ValidationError):
        validate(instance=recipe_dict, schema=recipe_schema)


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


def test_staging_output_valid():
    """Test that a recipe with staging outputs passes validation."""
    recipe_yaml = """
    recipe:
      name: test-staging
      version: "1.0"
    outputs:
      - staging:
          name: my-cache
        requirements:
          build:
            - cmake
          host:
            - zlib
        build:
          script: build.sh
      - package:
          name: my-pkg
          version: "1.0"
        inherit: my-cache
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    Recipe.validate_python(recipe_dict)


def test_staging_inherit_short_form():
    """Test that short form inherit (string) passes validation."""
    recipe_yaml = """
    recipe:
      name: test-inherit
      version: "1.0"
    outputs:
      - staging:
          name: build-cache
        build:
          script: build.sh
      - package:
          name: my-pkg
          version: "1.0"
        inherit: build-cache
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    Recipe.validate_python(recipe_dict)


def test_staging_inherit_long_form():
    """Test that long form inherit (object with from and run_exports) passes validation."""
    recipe_yaml = """
    recipe:
      name: test-inherit
      version: "1.0"
    outputs:
      - staging:
          name: build-cache
        build:
          script: build.sh
      - package:
          name: my-pkg
          version: "1.0"
        inherit:
          from: build-cache
          run_exports: false
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    Recipe.validate_python(recipe_dict)


def test_staging_output_invalid_run_requirements():
    """Test that staging outputs with run requirements fail validation."""
    recipe_yaml = """
    recipe:
      name: test-staging
      version: "1.0"
    outputs:
      - staging:
          name: my-cache
        requirements:
          build:
            - cmake
          run:
            - zlib
    """
    recipe_dict = yaml.safe_load(recipe_yaml)
    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)


def _valid(recipe_schema, recipe_yaml):
    recipe_dict = yaml.safe_load(recipe_yaml)
    Recipe.validate_python(recipe_dict)
    validate(instance=recipe_dict, schema=recipe_schema)


def _invalid(recipe_schema, recipe_yaml):
    recipe_dict = yaml.safe_load(recipe_yaml)
    with pytest.raises(PydanticValidationError):
        Recipe.validate_python(recipe_dict)
    with pytest.raises(ValidationError):
        validate(instance=recipe_dict, schema=recipe_schema)


def test_attestations_single_and_list(recipe_schema):
    """`attestations` takes one mapping or a list; publishers can be strings or mappings."""
    _valid(
        recipe_schema,
        """
    package:
      name: flask
      version: 3.1.1
    source:
      url: https://pypi.io/packages/source/f/flask/flask-3.1.1.tar.gz
      sha256: 284c7b8f2f58cb737f0cf1c30fd7eaf0ccfcde196099d24ecede3fc2005aa59e
      attestations:
        publishers:
          - github:pallets(16748505)/flask(596892)@refs/tags/3.1.1
    """,
    )
    _valid(
        recipe_schema,
        """
    package:
      name: uv
      version: 0.12.1
    source:
      url: https://github.com/astral-sh/uv/releases/download/0.12.1/source.tar.gz
      attestations:
        - publishers:
            - github: astral-sh/uv
              ref: refs/tags/0.12.1
              repository_id: 632123311
              owner_id: 115962839
              environment: release
        - bundle_url: https://example.com/source.tar.gz.sigstore.json
          publishers:
            - github:astral-sh/uv
    """,
    )


def test_attestation_singular_key_rejected(recipe_schema):
    """The experimental `attestation` key was renamed to `attestations`."""
    _invalid(
        recipe_schema,
        """
    package:
      name: flask
      version: 3.1.1
    source:
      url: https://pypi.io/packages/source/f/flask/flask-3.1.1.tar.gz
      attestation:
        publishers:
          - github:pallets/flask
    """,
    )


def test_attestations_empty_list_rejected(recipe_schema):
    _invalid(
        recipe_schema,
        """
    package:
      name: flask
      version: 3.1.1
    source:
      url: https://pypi.io/packages/source/f/flask/flask-3.1.1.tar.gz
      attestations: []
    """,
    )


def test_build_steps_and_flags(recipe_schema):
    _valid(
        recipe_schema,
        """
    package:
      name: test
      version: 1.0.0
    build:
      flags:
        - cuda
        - if: unix
          then: blas:openblas
      steps:
        - if: unix
          run: |
            mkdir -p "$PREFIX/bin"
        - run:
            - python -m pip install .
          cwd: src
          interpreter: bash
          env:
            FOO: bar
    """,
    )


def test_build_step_requires_run(recipe_schema):
    _invalid(
        recipe_schema,
        """
    package:
      name: test
      version: 1.0.0
    build:
      steps:
        - if: unix
    """,
    )


def test_script_env_without_content_and_multiline_jinja(recipe_schema):
    _valid(
        recipe_schema,
        """
    recipe:
      version: 1.0.0
    build:
      variant:
        down_prioritize_variant: |
          ${{
            (1 if with_cuda else 0)
          + (1 if scalar == "complex" else 0) }}
    outputs:
      - package:
          name: test
        build:
          script:
            env:
              BUILD_VERSION: 1.0.0
    """,
    )
