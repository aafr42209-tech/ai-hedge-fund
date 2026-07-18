"""Provider-strict selector schema overlay for the R02 D3 runner successor."""

from __future__ import annotations

from .canonical import canonical_sha256
from .r02_contracts import R02SelectorResponsePayload


R02_D3_PREDECESSOR_SELECTOR_OUTPUT_SCHEMA_SHA256 = (
    "5466a24d3557e28251cb1393dac16e1049824637a27b969f3bea55c80ebc2eca"
)


def predecessor_selector_output_schema() -> dict[str, object]:
    schema = R02SelectorResponsePayload.model_json_schema()
    if canonical_sha256(schema) != R02_D3_PREDECESSOR_SELECTOR_OUTPUT_SCHEMA_SHA256:
        raise ValueError("predecessor selector schema identity drift")
    return schema


def predecessor_selector_output_schema_sha256() -> str:
    return canonical_sha256(predecessor_selector_output_schema())


def selector_output_schema() -> dict[str, object]:
    schema = predecessor_selector_output_schema()
    properties = schema.get("properties")
    if not isinstance(properties, dict) or not isinstance(
        properties.get("schema_version"), dict
    ):
        raise ValueError("selector schema_version property is missing")
    properties["schema_version"].pop("default", None)
    required = schema.get("required")
    if not isinstance(required, list):
        raise ValueError("selector required contract is missing")
    schema["required"] = ["schema_version", *required]
    return schema


def selector_output_schema_sha256() -> str:
    return canonical_sha256(selector_output_schema())


def validate_openai_strict_json_schema(schema: object, *, path: str = "$") -> None:
    if isinstance(schema, list):
        for index, value in enumerate(schema):
            validate_openai_strict_json_schema(value, path=f"{path}[{index}]")
        return
    if not isinstance(schema, dict):
        return
    properties = schema.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            raise ValueError(f"{path}.properties must be an object")
        required = schema.get("required")
        if not isinstance(required, list) or set(required) != set(properties):
            raise ValueError(f"{path}.required must contain every property exactly once")
        if len(required) != len(set(required)):
            raise ValueError(f"{path}.required contains duplicate properties")
        if schema.get("additionalProperties") is not False:
            raise ValueError(f"{path}.additionalProperties must be false")
    for key, value in schema.items():
        validate_openai_strict_json_schema(value, path=f"{path}.{key}")


def validate_selector_output_schema_for_successor() -> None:
    schema = selector_output_schema()
    validate_openai_strict_json_schema(schema)
    predecessor_selector_output_schema()
