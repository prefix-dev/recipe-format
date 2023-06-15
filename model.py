from __future__ import annotations

from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Literal
from pydantic import BaseModel, Extra, Field, constr, conint, schema_json_of, AnyHttpUrl
from pydantic.generics import GenericModel

NonEmptyStr = constr(min_length=1)

###########################
# Conditional formatting  #
###########################

# TODO: Pydantic doesnt seem to support Generic Type Aliases yet. We need these to make
#   the typing of ConditionalList work. For now though we'll just have to manually
#   expand the TypeAlias. So:
#
#  ```python
#  ConditionalList[T]
#  ````
#
#  becomes
#
#  ```python
#  Union[T, IfStatement[T], List[Union[T, IfStatement[T]]]]
#  ````
T = TypeVar("T")
ConditionalList = Union[T, "IfStatement[T]", List[Union[T, "IfStatement[T]"]]]


class IfStatement(GenericModel, Generic[T]):
    expr: str = Field(..., alias="if")
    then: Union[T, List[T]]
    otherwise: Optional[Union[T, List[T]]] = Field(None, alias="else")


ConditionalStringList = Union[str, IfStatement[str], List[Union[str, IfStatement[str]]]]
NonEmptyStringList = Union[
    NonEmptyStr,
    IfStatement[NonEmptyStr],
    List[Union[NonEmptyStr, IfStatement[NonEmptyStr]]],
]


# HACK: Pydantic doesnt support constrained typeds in combination with generic
#  models. This means we cant use `PathNoBackslash` in if statements. `str` is
#  supported though, so we'll just use that.
#
#  See: https://github.com/pydantic/pydantic/issues/4528
ListNoBackslash = Union[str, IfStatement[str], List[Union[str, IfStatement[str]]]]

###################
# Package section  #
###################


class BasePackage(BaseModel):
    class Config:
        extra = Extra.forbid

    name: str = Field(description="The package name")


class SimplePackage(BasePackage):
    class Config:
        extra = Extra.forbid

    version: str = Field(description="The package version")


class ComplexPackage(BasePackage):
    class Config:
        extra = Extra.forbid


###################
# Source section  #
###################

MD5Str = constr(min_length=32, max_length=32, regex=r"[a-fA-F0-9]{32}")
SHA256Str = constr(min_length=64, max_length=64, regex=r"[a-fA-F0-9]{64}")


class BaseSource(BaseModel):
    class Config:
        extra = Extra.forbid

    patches: ListNoBackslash = Field(
        [], description="A list of patches to apply after fetching the source"
    )
    folder: Optional[str] = Field(
        None, description="The location in the working directory to place the source"
    )


class UrlSource(BaseSource):
    url: str = Field(
        ...,
        description="The url that points to the source. This should be an archive that is extracted in the working directory.",
    )
    sha256: Optional[SHA256Str] = Field(
        None, description="The SHA256 hash of the source archive"
    )
    md5: Optional[MD5Str] = Field(
        None, description="The MD5 hash of the source archive"
    )


class GitSource(BaseSource):
    git_rev: str = Field("HEAD", description="The git rev the checkout.")
    git_url: str = Field(..., description="The url that points to the git repository.")
    git_depth: Optional[int] = Field(
        None, description="A value to use when shallow cloning the repository."
    )


class LocalSource(BaseSource):
    path: str = Field(
        ..., description="A path on the local machine that contains the source."
    )


Source = Union[UrlSource, GitSource, LocalSource]

###################
# Build section   #
###################

PythonEntryPoint = str
PathNoBackslash = constr(regex=r"^[^\\]+$")
MatchSpec = str

MatchSpecList = Union[
    MatchSpec, IfStatement[MatchSpec], List[Union[MatchSpec, IfStatement[MatchSpec]]]
]
UnsignedInt = conint(ge=0)


class RunExports(BaseModel):
    class Config:
        extra = Extra.forbid

    weak: Optional[MatchSpecList] = Field(
        None, description="Weak run exports apply from the host env to the run env"
    )
    strong: Optional[MatchSpecList] = Field(
        None,
        description="Strong run exports apply from the build and host env to the run env",
    )
    noarch: Optional[MatchSpecList] = Field(
        None,
        description="Noarch run exports are the only ones looked at when building noarch packages",
    )
    weak_constrains: Optional[MatchSpecList] = Field(
        None, description="Weak run constrains add run_constrains from the host env"
    )
    strong_constrains: Optional[MatchSpecList] = Field(
        None,
        description="Strong run constrains add run_constrains from the build and host env",
    )


class ScriptEnv(BaseModel):
    class Config:
        extra = Extra.forbid

    passthrough: NonEmptyStringList = Field(
        [],
        description="Environments variables to leak into the build environment from the host system. During build time these variables are recorded and stored in the package output. Use `secrets` for environment variables that should not be recorded.",
    )
    env: Dict[str, str] = Field(
        {}, description="Environment variables to set in the build environment."
    )
    secrets: NonEmptyStringList = Field(
        [],
        description="Environment variables to leak into the build environment from the host system that contain sensitve information. Use with care because this might make recipes no longer reproducible on other machines.",
    )


class Build(BaseModel):
    class Config:
        extra = Extra.forbid

    number: Optional[UnsignedInt] = Field(
        0,
        description="Build number to version current build in addition to package version",
    )
    string: Optional[str] = Field(
        None,
        description="Build string to identify build variant (if not explicitly set, computed automatically from used build variant)",
    )
    skip: Optional[NonEmptyStringList] = Field(
        None,
        description="List of conditions under which to skip the build of the package.",
    )
    script: Optional[NonEmptyStringList] = Field(
        None,
        description="Build script to be used. If not given, tries to find 'build.sh' on Unix or 'bld.bat' on Windows inside the recipe folder.",
    )

    noarch: Optional[Literal["generic", "python"]] = Field(
        None,
        description="Can be either 'generic' or 'python'. A noarch 'python' package compiles .pyc files upon installation.",
    )
    # Note: entry points only valid if noarch: python is used! Write custom validator?
    entry_points: Optional[
        Union[
            PythonEntryPoint,
            IfStatement[PythonEntryPoint],
            List[Union[PythonEntryPoint, IfStatement[PythonEntryPoint]]],
        ]
    ] = Field(
        None,
        description="Only valid if `noarch: python` - list of all entry points of the package. e.g. `bsdiff4 = bsdiff4.cli:main_bsdiff4`",
    )

    run_exports: Optional[Union[RunExports, MatchSpecList]] = Field(
        None,
        description="Additional `run` dependencies added to a package that is build against this package.",
    )
    ignore_run_exports: Optional[NonEmptyStringList] = Field(
        None,
        description="Ignore specific `run` dependencies that are added by dependencies in our `host` requirements section that have`run_exports`.",
    )
    ignore_run_exports_from: Optional[NonEmptyStringList] = Field(
        None,
        description="Ignore `run_exports` from the specified dependencies in our `host` section.`",
    )

    # deprecated, but still used to downweigh packages
    track_features: Optional[NonEmptyStringList] = Field(
        None, description="deprecated, but still used to downweigh packages"
    )

    # Features are completely deprecated
    # features: List[str]
    # requires_features: Dict[str, str]
    # provides_features: Dict[str, str],

    include_recipe: bool = Field(
        True,
        description="Whether or not to include the rendered recipe in the final package.",
    )

    pre_link: Optional[str] = Field(
        None,
        alias="pre-link",
        description="Script to execute when installing - before linking. Highly discouraged!",
    )
    post_link: Optional[str] = Field(
        None,
        alias="post-link",
        description="Script to execute when installing - after linking.",
    )
    pre_unlink: Optional[str] = Field(
        None,
        alias="pre-unlink",
        description="Script to execute when removing - before unlinking.",
    )

    no_link: Optional[ListNoBackslash] = Field(
        None,
        description="A list of files that are included in the package but should not be installed when installing the package.",
    )
    binary_relocation: Union[Literal[False], ListNoBackslash] = Field(
        [],
        description="A list of files that should be excluded from binary relocation or False to ignore all binary files.",
    )

    has_prefix_files: ListNoBackslash = Field(
        [],
        description="A list of files to force being detected as A TEXT file for prefix replacement.",
    )
    binary_has_prefix_files: ListNoBackslash = Field(
        [],
        description="A list of files to force being detected as A BINARY file for prefix replacement.",
    )
    ignore_prefix_files: Union[Literal[True], ListNoBackslash] = Field(
        [],
        description="A list of files that are not considered for prefix replacement, or True to ignore all files.",
    )

    # the following is defaulting to True on UNIX and False on Windows
    detect_binary_files_with_prefix: Optional[bool] = Field(
        None,
        description="Wether to detect binary files with prefix or not. Defaults to True on Unix and False on Windows.",
    )

    skip_compile_pyc: Optional[ListNoBackslash] = Field(
        None,
        description="A list of python files that should not be compiled to .pyc files at install time.",
    )

    rpaths: NonEmptyStringList = Field(
        ["lib/"], description="A list of rpaths (Linux only)."
    )
    # rpaths_patcher: Optional[str] = None

    # Note: this deviates from conda-build `script_env`!
    script_env: Optional[ScriptEnv] = Field(
        None,
        description="Environment variables to either pass through to the script environment or set.",
    )

    # Files to be included even if they are present in the PREFIX before building
    always_include_files: NonEmptyStringList = Field(
        [],
        description="Files to be included even if they are present in the PREFIX before building.",
    )

    # msvc_compiler: Optional[str] = None -- deprecated in conda_build
    # pin_depends: Optional[str] -- did not find usage anywhere, removed
    # preferred_env: Optional[str]
    # preferred_env_executable_paths': Optional[List]

    osx_is_app: bool = False
    disable_pip: bool = False
    preserve_egg_dir: bool = False

    # note didnt find _any_ usage of force_use_keys in conda-forge
    force_use_keys: Optional[NonEmptyStringList] = None
    force_ignore_keys: Optional[NonEmptyStringList] = None

    merge_build_host: bool = False

    missing_dso_whitelist: Optional[NonEmptyStringList] = None
    runpath_whitelist: Optional[NonEmptyStringList] = None

    error_overdepending: bool = Field(False, description="Error on overdepending")
    error_overlinking: bool = Field(False, description="Error on overlinking")


#########################
# Requirements Section  #
#########################


class Requirements(BaseModel):
    class Config:
        extra = Extra.forbid

    build: Optional[MatchSpecList] = Field(
        None,
        description="Dependencies to install on the build platform architecture. Compilers, CMake, everything that needs to execute at build time.",
    )
    host: Optional[MatchSpecList] = Field(
        None,
        description="Dependencies to install on the host platform architecture. All the packages that your build links against.",
    )
    run: Optional[MatchSpecList] = Field(
        None,
        description="Dependencies that should be installed alongside this package. Dependencies in the `host` section with `run_exports` are also automatically added here.",
    )
    run_constrained: Optional[MatchSpecList] = Field(
        None, description="Constrained optional dependencies at runtime."
    )


################
# Test Section #
################


class TestElementRequires(BaseModel):
    class Config:
        extra = Extra.forbid

    build: Optional[MatchSpecList] = Field(
        None,
        description="extra requirements with build_platform architecture (emulators, ...)",
    )
    run: Optional[MatchSpecList] = Field(None, description="extra run dependencies")


class TestElementFiles(BaseModel):
    class Config:
        extra = Extra.forbid

    source: Optional[NonEmptyStringList] = Field(
        None, description="extra files from $SRC_DIR"
    )
    recipe: Optional[NonEmptyStringList] = Field(
        None, description="extra files from $RECIPE_DIR"
    )


class CommandTestElement(BaseModel):
    class Config:
        extra = Extra.forbid

    script: NonEmptyStringList = Field(
        None, description="A script to run to perform the test."
    )
    extra_requirements: Optional[TestElementRequires] = Field(
        None, description="Additional dependencies to install before running the test."
    )
    files: Optional[TestElementFiles] = Field(
        None, description="Additional files to include for the test."
    )


class ImportTestElement(BaseModel):
    class Config:
        extra = Extra.forbid

    imports: NonEmptyStringList = Field(
        ...,
        description="A list of Python imports to check after having installed the built package.",
    )


class DownstreamTestElement(BaseModel):
    class Config:
        extra = Extra.forbid

    downstream: MatchSpec = Field(
        ...,
        description="Install the package and use the output of this package to test if the tests in the downstream package still succeed.",
    )


TestElement = Union[CommandTestElement, ImportTestElement, DownstreamTestElement]

#########
# About #
#########


class DescriptionFile(BaseModel):
    class Config:
        extra = Extra.forbid

    file: PathNoBackslash = Field(
        ...,
        description="Path in the source directory that contains the packages description. E.g. README.md",
    )


class About(BaseModel):
    class Config:
        extra = Extra.forbid

    # URLs
    homepage: Optional[AnyHttpUrl] = Field(
        None, description="Url of the homepage of the package."
    )
    repository: Optional[AnyHttpUrl] = Field(
        None,
        description="Url that points to where the source code is hosted e.g. (github.com)",
    )
    documentation: Optional[AnyHttpUrl] = Field(
        None, description="Url that points to where the documentation is hosted."
    )

    # License
    license_: Optional[str] = Field(
        None, alias="license", description="An license in SPDX format."
    )
    license_file: Optional[ListNoBackslash] = Field(
        None, description="Paths to the license files of this package."
    )
    license_url: Optional[str] = Field(
        None, description="A url that points to the license file."
    )

    # Text
    summary: Optional[str] = Field(
        None, description="A short description of the package."
    )
    description: Optional[Union[str, DescriptionFile]] = Field(
        None,
        description="Extented description of the package or a file (usually a README).",
    )

    prelink_message: Optional[str] = None


###########
# Outputs #
###########


class OutputBuild(Build):
    cache_only: bool = Field(
        False,
        description="Do not output a package but use this output as an input to others.",
    )
    cache_from: Optional[NonEmptyStringList] = Field(
        None,
        description="Take the output of the specified outputs and copy them in the working directory.",
    )


class Output(BaseModel):
    package: Optional[SimplePackage] = Field(
        None, description="The package name and version."
    )

    source: Union[
        None, Source, IfStatement[Source], List[Union[Source, IfStatement[Source]]]
    ] = Field(
        None, description="The source items to be downloaded and used for the build."
    )
    build: Optional[OutputBuild] = Field(
        None, description="Describes how the package should be build."
    )

    requirements: Optional[Requirements] = Field(
        None, description="The package dependencies"
    )

    test: Optional[
        List[
            Union[
                TestElement,
                IfStatement[TestElement],
                List[Union[TestElement, IfStatement[TestElement]]],
            ]
        ]
    ] = Field(None, description="Tests to run after packaging")

    about: Optional[About] = Field(
        None,
        description="A human readable description of the package information. The values here are merged with the top level `about` field.",
    )

    extra: Optional[Dict[str, Any]] = Field(
        None,
        description="An set of arbitrary values that are included in the package manifest. The values here are merged with the top level `extras` field.",
    )


#####################
# The Recipe itself #
#####################


class BaseRecipe(BaseModel):
    class Config:
        extra = Extra.forbid

    context: Optional[Dict[str, Any]] = Field(
        None, description="Defines arbitrary key-value pairs for Jinja interpolation"
    )

    source: Union[
        None, Source, IfStatement[Source], List[Union[Source, IfStatement[Source]]]
    ] = Field(
        None, description="The source items to be downloaded and used for the build."
    )
    build: Optional[Build] = Field(
        None, description="Describes how the package should be build."
    )

    about: Optional[About] = Field(
        None, description="A human readable description of the package information"
    )
    extra: Optional[Dict[str, Any]] = Field(
        None,
        description="An set of arbitrary values that are included in the package manifest",
    )


class ComplexRecipe(BaseRecipe):
    class Config:
        extra = Extra.forbid

    package: Optional[ComplexPackage] = Field(None, description="The package version.")

    outputs: List[Union[Output, IfStatement[Output]]] = Field(
        ..., description="A list of outputs that are generated for this recipe."
    )


class SimpleRecipe(BaseRecipe):
    class Config:
        extra = Extra.forbid

    package: SimplePackage = Field(..., description="The package name and version.")

    test: Optional[
        List[
            Union[
                TestElement,
                IfStatement[TestElement],
                List[Union[TestElement, IfStatement[TestElement]]],
            ]
        ]
    ] = Field(None, description="Tests to run after packaging")

    requirements: Optional[Requirements] = Field(
        None, description="The package dependencies"
    )


Recipe = Union[SimpleRecipe, ComplexRecipe]


if __name__ == "__main__":
    print(schema_json_of(Recipe, title="rattler-builds schema", indent=2))
