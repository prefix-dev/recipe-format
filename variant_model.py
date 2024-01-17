import json

from pydantic import BaseModel, TypeAdapter


class Pin(BaseModel):
    min_pin: str | None = None
    max_pin: str | None = None


class VariantConfig(BaseModel, extra="allow"):
    zip_keys: list[list[str]] = []
    pin_run_as_build: dict[str, Pin | list[Pin]] = {}
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
