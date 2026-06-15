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
    assert RESOLUTION_SCHEMA["required"] == ["outcome"]
    assert RESOLUTION_SCHEMA["properties"]["outcome"]["enum"] == [
        "resolve", "cannot_resolve", "needs_disambiguation",
    ]


def test_replay_resolver_is_normalised_and_total():
    r = ReplayResolver(RECORDED)
    # whitespace / case-insensitive lookup
    assert isinstance(r.resolve("  average TOTAL catch per trip in kwale?  "), Resolution)
    # unknown question -> explicit refusal, never a guess
    assert isinstance(r.resolve("how many fish are in the sea?"), CannotResolve)
