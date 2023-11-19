from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Generic, Literal, TypeVar, Union

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    TypeAdapter,
    conint,
    constr,
)

NonEmptyStr = constr(min_length=1)


class StrictBaseModel(BaseModel):
    class Config:
        extra = "forbid"


###########################
# Conditional formatting  #
###########################

T = TypeVar("T")
ConditionalList = Union[T, "IfStatement[T]", list[Union[T, "IfStatement[T]"]]]


class IfStatement(BaseModel, Generic[T]):
    expr: str = Field(..., alias="if")
    then: T | list[T]
    otherwise: T | list[T] | None = Field(None, alias="else")


###################
# Package section #
###################


class SimplePackage(StrictBaseModel):
    name: str = Field(description="The package name")
    version: str = Field(description="The package version")


class ComplexPackage(StrictBaseModel):
    name: str = Field(
        description="The recipe name, this is only used to identify the name of the recipe."
    )
    version: str | None = Field(
        None, description="The version of each output, this can be overwritten per output"
    )


###################
# Source section  #
###################

MD5Str = constr(min_length=32, max_length=32, pattern=r"[a-fA-F0-9]{32}")
SHA256Str = constr(min_length=64, max_length=64, pattern=r"[a-fA-F0-9]{64}")


class BaseSource(StrictBaseModel):
    patches: ConditionalList[PathNoBackslash] = Field(
        [],
        description="A list of patches to apply after fetching the source",
    )
    folder: str | None = Field(
        None,
        description="The location in the working directory to place the source",
    )


class UrlSource(BaseSource):
    url: str = Field(
        ...,
        description="The url that points to the source. This should be an archive that is extracted in the working directory.",
    )
    sha256: SHA256Str | None = Field(
        None,
        description="The SHA256 hash of the source archive",
    )
    md5: MD5Str | None = Field(
        None,
        description="The MD5 hash of the source archive",
    )


class GitSource(BaseSource):
    git_rev: str = Field("HEAD", description="The git rev the checkout.")
    git_url: str = Field(..., description="The url that points to the git repository.")
    git_depth: int | None = Field(
        None,
        description="A value to use when shallow cloning the repository.",
    )


class LocalSource(BaseSource):
    path: str = Field(
        ...,
        description="A path on the local machine that contains the source.",
    )


Source = UrlSource | GitSource | LocalSource

###################
# Build section   #
###################

PythonEntryPoint = str
PathNoBackslash = constr(pattern=r"^[^\\]+$")
MatchSpec = str

MatchSpecList = ConditionalList[MatchSpec]
UnsignedInt = conint(ge=0)


class RunExports(StrictBaseModel):
    weak: MatchSpecList | None = Field(
        None,
        description="Weak run exports apply from the host env to the run env",
    )
    strong: MatchSpecList | None = Field(
        None,
        description="Strong run exports apply from the build and host env to the run env",
    )
    noarch: MatchSpecList | None = Field(
        None,
        description="Noarch run exports are the only ones looked at when building noarch packages",
    )
    weak_constrains: MatchSpecList | None = Field(
        None,
        description="Weak run constrains add run_constrains from the host env",
    )
    strong_constrains: MatchSpecList | None = Field(
        None,
        description="Strong run constrains add run_constrains from the build and host env",
    )


class ScriptEnv(StrictBaseModel):
    passthrough: ConditionalList[NonEmptyStr] = Field(
        [],
        description="Environments variables to leak into the build environment from the host system. During build time these variables are recorded and stored in the package output. Use `secrets` for environment variables that should not be recorded.",
    )
    env: dict[str, str] = Field(
        {},
        description="Environment variables to set in the build environment.",
    )
    secrets: ConditionalList[NonEmptyStr] = Field(
        [],
        description="Environment variables to leak into the build environment from the host system that contain sensitve information. Use with care because this might make recipes no longer reproducible on other machines.",
    )


JinjaExpr = constr(pattern=r"\$\{\{.*\}\}")


class Build(StrictBaseModel):
    number: UnsignedInt | JinjaExpr | None = Field(
        0,
        description="Build number to version current build in addition to package version",
    )
    string: str | None = Field(
        None,
        description="Build string to identify build variant (if not explicitly set, computed automatically from used build variant)",
    )
    skip: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="List of conditions under which to skip the build of the package.",
    )
    script: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="Build script to be used. If not given, tries to find 'build.sh' on Unix or 'bld.bat' on Windows inside the recipe folder.",
    )

    noarch: Literal["generic", "python"] | None = Field(
        None,
        description="Can be either 'generic' or 'python'. A noarch 'python' package compiles .pyc files upon installation.",
    )
    # Note: entry points only valid if noarch: python is used! Write custom validator?
    entry_points: ConditionalList[PythonEntryPoint] | None = Field(
        None,
        description="Only valid if `noarch: python` - list of all entry points of the package. e.g. `bsdiff4 = bsdiff4.cli:main_bsdiff4`",
    )

    run_exports: RunExports | MatchSpecList | None = Field(
        None,
        description="Additional `run` dependencies added to a package that is build against this package.",
    )
    ignore_run_exports: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="Ignore specific `run` dependencies that are added by dependencies in our `host` requirements section that have`run_exports`.",
    )
    ignore_run_exports_from: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="Ignore `run_exports` from the specified dependencies in our `host` section.`",
    )

    # deprecated, but still used to downweigh packages
    track_features: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="deprecated, but still used to downweigh packages",
    )

    # Features are completely deprecated
    # provides_features: Dict[str, str],

    include_recipe: bool = Field(
        default=True,
        description="Whether or not to include the rendered recipe in the final package.",
    )

    pre_link: str | None = Field(
        None,
        alias="pre-link",
        description="Script to execute when installing - before linking. Highly discouraged!",
    )
    post_link: str | None = Field(
        None,
        alias="post-link",
        description="Script to execute when installing - after linking.",
    )
    pre_unlink: str | None = Field(
        None,
        alias="pre-unlink",
        description="Script to execute when removing - before unlinking.",
    )

    no_link: ConditionalList[PathNoBackslash] | None = Field(
        None,
        description="A list of files that are included in the package but should not be installed when installing the package.",
    )
    binary_relocation: Literal[False] | ConditionalList[PathNoBackslash] = Field(
        [],
        description="A list of files that should be excluded from binary relocation or False to ignore all binary files.",
    )

    has_prefix_files: ConditionalList[PathNoBackslash] = Field(
        [],
        description="A list of files to force being detected as A TEXT file for prefix replacement.",
    )
    binary_has_prefix_files: ConditionalList[PathNoBackslash] = Field(
        [],
        description="A list of files to force being detected as A BINARY file for prefix replacement.",
    )
    ignore_prefix_files: Literal[True] | ConditionalList[PathNoBackslash] = Field(
        [],
        description="A list of files that are not considered for prefix replacement, or True to ignore all files.",
    )

    # the following is defaulting to True on UNIX and False on Windows
    detect_binary_files_with_prefix: bool | None = Field(
        None,
        description="Wether to detect binary files with prefix or not. Defaults to True on Unix and False on Windows.",
    )

    skip_compile_pyc: ConditionalList[PathNoBackslash] | None = Field(
        None,
        description="A list of python files that should not be compiled to .pyc files at install time.",
    )

    rpaths: ConditionalList[NonEmptyStr] = Field(
        ["lib/"],
        description="A list of rpaths (Linux only).",
    )

    # Note: this deviates from conda-build `script_env`!
    script_env: ScriptEnv | None = Field(
        None,
        description="Environment variables to either pass through to the script environment or set.",
    )

    # Files to be included even if they are present in the PREFIX before building
    always_include_files: ConditionalList[NonEmptyStr] = Field(
        [],
        description="Files to be included even if they are present in the PREFIX before building.",
    )

    # pin_depends: Optional[str] -- did not find usage anywhere, removed
    # preferred_env_executable_paths': Optional[List]

    osx_is_app: bool = False
    disable_pip: bool = False
    preserve_egg_dir: bool = False

    # note didnt find _any_ usage of force_use_keys in conda-forge
    force_use_keys: ConditionalList[NonEmptyStr] | None = None
    force_ignore_keys: ConditionalList[NonEmptyStr] | None = None

    merge_build_host: bool = False

    missing_dso_whitelist: ConditionalList[NonEmptyStr] | None = None
    runpath_whitelist: ConditionalList[NonEmptyStr] | None = None

    error_overdepending: bool = Field(default=False, description="Error on overdepending")
    error_overlinking: bool = Field(default=False, description="Error on overlinking")


#########################
# Requirements Section  #
#########################


class Requirements(StrictBaseModel):
    build: MatchSpecList | None = Field(
        None,
        description="Dependencies to install on the build platform architecture. Compilers, CMake, everything that needs to execute at build time.",
    )
    host: MatchSpecList | None = Field(
        None,
        description="Dependencies to install on the host platform architecture. All the packages that your build links against.",
    )
    run: MatchSpecList | None = Field(
        None,
        description="Dependencies that should be installed alongside this package. Dependencies in the `host` section with `run_exports` are also automatically added here.",
    )
    run_constrained: MatchSpecList | None = Field(
        None,
        description="Constrained optional dependencies at runtime.",
    )


################
# Test Section #
################


class TestElementRequires(StrictBaseModel):
    build: MatchSpecList | None = Field(
        None,
        description="extra requirements with build_platform architecture (emulators, ...)",
    )
    run: MatchSpecList | None = Field(None, description="extra run dependencies")


class TestElementFiles(StrictBaseModel):
    source: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="extra files from $SRC_DIR",
    )
    recipe: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="extra files from $RECIPE_DIR",
    )


class CommandTestElement(StrictBaseModel):
    script: ConditionalList[NonEmptyStr] = Field(
        None,
        description="A script to run to perform the test.",
    )
    extra_requirements: TestElementRequires | None = Field(
        None,
        description="Additional dependencies to install before running the test.",
    )
    files: TestElementFiles | None = Field(
        None,
        description="Additional files to include for the test.",
    )


class ImportTestElement(StrictBaseModel):
    imports: ConditionalList[NonEmptyStr] = Field(
        ...,
        description="A list of Python imports to check after having installed the built package.",
    )


class DownstreamTestElement(StrictBaseModel):
    downstream: MatchSpec = Field(
        ...,
        description="Install the package and use the output of this package to test if the tests in the downstream package still succeed.",
    )


TestElement = CommandTestElement | ImportTestElement | DownstreamTestElement

#########
# About #
#########


class DescriptionFile(StrictBaseModel):
    file: PathNoBackslash = Field(
        ...,
        description="Path in the source directory that contains the packages description. E.g. README.md",
    )


class About(StrictBaseModel):
    # URLs
    homepage: AnyHttpUrl | None = Field(
        None,
        description="Url of the homepage of the package.",
    )
    repository: AnyHttpUrl | None = Field(
        None,
        description="Url that points to where the source code is hosted e.g. (github.com)",
    )
    documentation: AnyHttpUrl | None = Field(
        None,
        description="Url that points to where the documentation is hosted.",
    )

    # License
    license_: str | None = Field(
        None,
        alias="license",
        description="An license in SPDX format.",
    )
    license_file: ConditionalList[PathNoBackslash] | None = Field(
        None,
        description="Paths to the license files of this package.",
    )
    license_url: str | None = Field(
        None,
        description="A url that points to the license file.",
    )

    # Text
    summary: str | None = Field(
        None,
        description="A short description of the package.",
    )
    description: str | DescriptionFile | None = Field(
        None,
        description="Extented description of the package or a file (usually a README).",
    )

    prelink_message: str | None = None


###########
# Outputs #
###########


class OutputBuild(Build):
    cache_only: bool = Field(
        default=False,
        description="Do not output a package but use this output as an input to others.",
    )
    cache_from: ConditionalList[NonEmptyStr] | None = Field(
        None,
        description="Take the output of the specified outputs and copy them in the working directory.",
    )


class Output(BaseModel):
    package: ComplexPackage | None = Field(
        None,
        description="The package name and version, this overwrites any top-level fields.",
    )

    source: ConditionalList[Source] | None = Field(
        None,
        description="The source items to be downloaded and used for the build.",
    )
    build: OutputBuild | None = Field(
        None,
        description="Describes how the package should be build.",
    )

    requirements: Requirements | None = Field(
        None,
        description="The package dependencies",
    )

    test: list[
        TestElement | IfStatement[TestElement] | list[TestElement | IfStatement[TestElement]]
    ] | None = Field(None, description="Tests to run after packaging")

    about: About | None = Field(
        None,
        description="A human readable description of the package information. The values here are merged with the top level `about` field.",
    )

    extra: dict[str, Any] | None = Field(
        None,
        description="An set of arbitrary values that are included in the package manifest. The values here are merged with the top level `extras` field.",
    )


#####################
# The Recipe itself #
#####################


class BaseRecipe(StrictBaseModel):
    context: dict[str, Any] | None = Field(
        None,
        description="Defines arbitrary key-value pairs for Jinja interpolation",
    )

    source: None | Source | IfStatement[Source] | list[Source | IfStatement[Source]] = Field(
        None,
        description="The source items to be downloaded and used for the build.",
    )
    build: Build | None = Field(
        None,
        description="Describes how the package should be build.",
    )

    about: About | None = Field(
        None,
        description="A human readable description of the package information",
    )
    extra: dict[str, Any] | None = Field(
        None,
        description="An set of arbitrary values that are included in the package manifest",
    )


class ComplexRecipe(BaseRecipe):
    recipe: ComplexPackage | None = Field(None, description="The package version.")

    outputs: ConditionalList[Output] = Field(
        ...,
        description="A list of outputs that are generated for this recipe.",
    )


class SimpleRecipe(BaseRecipe):
    package: SimplePackage = Field(..., description="The package name and version.")

    test: ConditionalList[TestElement] | None = Field(
        None,
        description="Tests to run after packaging",
    )

    requirements: Requirements | None = Field(
        None,
        description="The package dependencies",
    )


Recipe = TypeAdapter(SimpleRecipe | ComplexRecipe)


if __name__ == "__main__":
    with Path.open("schema.json", "w") as f:
        f.write(json.dumps(Recipe.json_schema(), indent=2))
