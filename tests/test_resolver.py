"""The resolver carries both mandatory guards; the replay backend is deterministic."""

from mode_c import ReplayResolver, build_resolver_prompt, load_catalog
from mode_c.resolution import CannotResolve, Resolution
from mode_c.resolver import DERIVED_GUARD, GRAIN_GUARD, RESOLUTION_SCHEMA
from mode_c.fixtures import RECORDED
from mode_c.fixtures.resolutions import Q4


def test_prompt_carries_both_mandatory_guards():
    prompt = build_resolver_prompt(load_catalog())
    # the two guards that moved the proof from 1/3 to 5/5 on grain and killed the CPUE proxy
    assert GRAIN_GUARD in prompt
    assert DERIVED_GUARD in prompt
    assert "grain_key" in prompt and "substitute a proxy" in prompt


def test_prompt_embeds_the_catalog():
    prompt = build_resolver_prompt(load_catalog())
    assert "peskas/kenya_validated_trips.csv" in prompt
    assert "## Grain" in prompt  # the grain lines the resolver must reason over


def test_resolution_schema_requires_an_outcome():
    assert "outcome" in RESOLUTION_SCHEMA["required"]
    assert RESOLUTION_SCHEMA["properties"]["outcome"]["enum"] == [
        "resolve", "cannot_resolve", "needs_disambiguation",
    ]


def test_resolution_schema_is_strict():
    """Every property is required and no extras are allowed — structured output's strict mode.

    This asserted ``required == ["outcome"]`` until the schema became strict, and then simply
    failed. The prompt is written to match: it tells the resolver to emit the whole field set
    with inert defaults for a non-resolve outcome (``resolver.py`` system prompt — "these fields
    are required by the schema but ignored for non-resolve outcomes"), so a partial object is a
    schema violation, not a shortcut. Pinning the *property set* rather than a literal list means
    adding a field cannot leave the two halves silently out of step.
    """
    assert RESOLUTION_SCHEMA["additionalProperties"] is False
    assert set(RESOLUTION_SCHEMA["required"]) == set(RESOLUTION_SCHEMA["properties"])

    # the resolve-path fields the prompt must keep spelling out inert defaults for, or a
    # non-resolve outcome cannot satisfy the schema at all
    prompt = build_resolver_prompt(load_catalog())
    for field in ("grain_key", "metric_column", "derived_formula", "metric_label", "filters"):
        assert field in prompt, f"{field} is required by the schema but absent from the prompt"


def test_replay_resolver_is_normalised_and_total():
    r = ReplayResolver(RECORDED)
    # whitespace / case-insensitive lookup
    assert isinstance(r.resolve("  average TOTAL catch per trip in kwale?  "), Resolution)
    # unknown question -> explicit refusal, never a guess
    assert isinstance(r.resolve("how many fish are in the sea?"), CannotResolve)
