"""Translate an Anthropic-style JSON schema into Gemini's responseSchema dialect.

WDB's modes declare structured output with a JSON Schema carrying
``additionalProperties: false`` and union types like ``["string", "null"]``
(``mode_c/resolver.py:RESOLUTION_SCHEMA``, ``mode_a/reasoner.py:RESPONSE_SCHEMA``).
Gemini's structured-output uses an OpenAPI-3 subset: uppercase type names,
``nullable`` instead of a null-union, and NO ``additionalProperties``. Translating
here (rather than rewriting the bar) keeps the *requirement* identical across
providers and makes any Gemini structured-output failure attributable to FORMAT,
not the schema being unfair. ``propertyOrdering`` is emitted for determinism.
"""
from __future__ import annotations

_TYPE = {
    "object": "OBJECT", "array": "ARRAY", "string": "STRING",
    "number": "NUMBER", "integer": "INTEGER", "boolean": "BOOLEAN",
}


def to_gemini(schema: dict) -> dict:
    t = schema.get("type")
    nullable = False
    if isinstance(t, list):  # ["string", "null"] -> STRING + nullable
        non_null = [x for x in t if x != "null"]
        nullable = "null" in t
        t = non_null[0] if non_null else "string"

    out: dict = {"type": _TYPE[t]}
    if nullable:
        out["nullable"] = True
    if "enum" in schema:
        out["enum"] = schema["enum"]
    if t == "object":
        props = schema.get("properties", {})
        out["properties"] = {k: to_gemini(v) for k, v in props.items()}
        if props:
            out["propertyOrdering"] = list(props.keys())
        if schema.get("required"):
            out["required"] = list(schema["required"])
    if t == "array":
        out["items"] = to_gemini(schema["items"])
    return out
