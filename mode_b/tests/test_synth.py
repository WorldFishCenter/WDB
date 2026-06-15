"""The synthesis Live/Replay split + the pinned model record.

Replay is deterministic and offline; Live is the production path (pinned Sonnet
4.6) and is exercised only when the SDK is installed — like Mode C's live test.
"""

import os

import pytest

from mode_b.fixtures import Q_COVERED, RECORDED_PASSAGES, RECORDED_SYNTHESIS
from mode_b.model import SYNTH_MODEL
from mode_b.synth import ReplaySynthesizer, build_context, build_user_prompt


def test_synth_model_is_pinned_to_exact_id():
    assert SYNTH_MODEL == "claude-sonnet-4-6"     # not a floating alias


def test_replay_synthesizer_is_deterministic():
    s = ReplaySynthesizer(RECORDED_SYNTHESIS)
    out = s.synthesize(Q_COVERED, RECORDED_PASSAGES[Q_COVERED])
    assert "[1]" in out and "validat" in out.lower()
    # idempotent / no network
    assert s.synthesize(Q_COVERED, RECORDED_PASSAGES[Q_COVERED]) == out


def test_replay_synthesizer_refuses_unknown_question():
    with pytest.raises(KeyError):
        ReplaySynthesizer(RECORDED_SYNTHESIS).synthesize("never recorded", [])


def test_prompt_numbers_passages_for_citation():
    ctx = build_context(RECORDED_PASSAGES[Q_COVERED])
    assert ctx.startswith("[1] Source: peskas/")
    prompt = build_user_prompt(Q_COVERED, RECORDED_PASSAGES[Q_COVERED])
    assert Q_COVERED in prompt and "[1]" in prompt


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"),
                    reason="live synthesis needs anthropic SDK + ANTHROPIC_API_KEY")
def test_live_synthesizer_smoke():  # pragma: no cover - network
    from mode_b.synth import LiveSynthesizer

    out = LiveSynthesizer().synthesize(Q_COVERED, RECORDED_PASSAGES[Q_COVERED])
    assert isinstance(out, str) and out.strip()
