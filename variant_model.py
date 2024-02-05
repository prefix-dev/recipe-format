import json
from typing import Generic, TypeVar, Union

from pydantic import BaseModel, Field, TypeAdapter

T = TypeVar("T")
ConditionalList = Union[T, "IfStatement[T]", list[Union[T, "IfStatement[T]"]]]


class IfStatement(BaseModel, Generic[T]):
    expr: str = Field(..., alias="if")
    then: T | list[T]
    otherwise: T | list[T] | None = Field(None, alias="else")


class MinPin(BaseModel):
    min_pin: str | None = Field(
        default=None, description="Defaults to x.x.x.x.x for pin, change to make less specific"
    )


class MaxPin(BaseModel):
    max_pin: str | None = Field(
        default=None, description="Defaults to x for pin, change to make more specific"
    )


class BothPin(BaseModel):
    min_pin: str | None = Field(
        default=None, description="Defaults to x.x.x.x.x for pin, change to make less specific"
    )
    max_pin: str | None = Field(
        default=None, description="Defaults to x for pin, change to make more specific"
    )


class VariantConfig(BaseModel, extra="allow"):
    """Usage docs: https://prefix-dev.github.io/rattler-build/variants

    Schema for variant configuration file for specifying recipe variants
    for automating builds.
    """

    zip_keys: ConditionalList[ConditionalList[str]] = Field(
        default=None,
        description="Zip keys have variant key that has multiple entries which is expanded to a build matrix for variants.",
    )
    pin_run_as_build: dict[str, MaxPin | MinPin | BothPin] = Field(
        default=None, description="Pinning package versions for variant"
    )
    model_config = {
        "json_schema_extra": {
            "additionalProperties": {
                "anyOf": [
                    {"type": "string"},
                    {"items": {"type": "string"}, "type": "array"},
                ]
            },
        },
    }


if __name__ == "__main__":
    print(json.dumps(TypeAdapter(VariantConfig).json_schema(), indent=2))
