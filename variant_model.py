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
    min_pin: str | None = None


class MaxPin(BaseModel):
    max_pin: str | None = None


class BothPin(BaseModel):
    min_pin: str | None = None
    max_pin: str | None = None


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
        default=None, description="Pinning package versions."
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


print(json.dumps(TypeAdapter(VariantConfig).json_schema()))
