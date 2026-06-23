"""Model-call seam for the eval — one interface, three providers behind it.

Each backend exposes ``json_call`` (structured output, used by the mechanical
Mode-A/C bars) and ``text_call`` (free text, used by Mode B + ingestion), each
returning the parsed result PLUS a ``Usage`` (real token counts from the live
response) so cost is measured, never estimated. This is the swappable seam the
eval rides on; it changes no mode, pin, MODEL.md, or real Live path.

* Anthropic (Opus baseline, Haiku candidate): the installed ``anthropic`` SDK +
  the same ``output_config.format`` JSON-schema path the modes already use.
* Gemini (candidate): REST via stdlib ``urllib`` (no new dependency), schema
  translated by ``schema_gemini`` and ``usageMetadata`` read back for cost —
  output billed = answer tokens + thinking tokens (Gemini bundles thinking into
  output pricing).
* OpenRouter (the gateway for every non-Anthropic candidate — Gemini routed here
  AND the ultra-cheap open model DeepSeek): the official OpenAI-compatible
  ``/chat/completions`` endpoint, Bearer auth, ``response_format`` json_object to
  enforce parseable JSON (the structured-output mitigation the task calls for).
  Reuses stdlib ``urllib`` — same as the Gemini backend — so the harness adds NO
  new dependency (it is a trivial OpenAI-shaped POST). ``usage.prompt_tokens`` /
  ``completion_tokens`` are read back for cost; the ~5.5% OpenRouter credit fee is
  folded into the rate in ``costs.py``, not here.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from . import _env
from .schema_gemini import to_gemini


@dataclass
class Usage:
    in_tok: int = 0
    out_tok: int = 0          # billed output = answer + thinking (Gemini); output (Anthropic)
    thinking_tok: int = 0     # informational: portion of out_tok spent thinking (Gemini)
    raw: dict = field(default_factory=dict)


class JSONParseError(Exception):
    """The model returned text that is not parseable JSON (structured-output failure)."""


def render_contract(schema: dict) -> str:
    """Render an Anthropic-style JSON schema into a terse key contract for prompt-for-JSON.

    Anthropic's ``output_config.format`` rejects WDB's RESOLUTION_SCHEMA as "Schema
    is too complex" (the LiveResolver path is never exercised by the offline suite,
    so this was latent). The fair fallback — used identically for Opus baseline and
    Haiku candidate — is prompt-for-JSON: the SAME contract, described in-prompt, and
    tolerantly parsed. Gemini keeps its native responseSchema (which accepts the
    translated schema), so each provider is tested on its real structured-output
    mechanism. Any malformed Anthropic JSON is then a genuine structured-output
    reliability signal, not a schema artifact.
    """
    def one(name, spec):
        t = spec.get("type")
        if isinstance(t, list):
            t = "/".join(x for x in t if x != "null") + "|null"
        if spec.get("enum"):
            return f'{name}: one of {spec["enum"]}'
        if t == "array":
            it = spec.get("items", {})
            if it.get("type") == "object":
                keys = ", ".join(it.get("properties", {}).keys())
                return f"{name}: list of objects {{{keys}}}"
            return f"{name}: list"
        return f"{name}: {t}"
    props = schema.get("properties", {})
    req = set(schema.get("required", []))
    lines = [("  - " + one(k, v) + (" (required)" if k in req else "")) for k, v in props.items()]
    return "Return ONLY one JSON object with these keys (omit or null any that do not " \
           "apply); no prose, no markdown fences:\n" + "\n".join(lines)


def extract_json(text: str) -> dict:
    """Tolerant JSON extraction: strip ``` fences, take the outermost {...}."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t.strip("`")
        t = t[4:] if t.lower().startswith("json") else t
    i, j = t.find("{"), t.rfind("}")
    if i == -1 or j == -1:
        raise json.JSONDecodeError("no object found", t, 0)
    return json.loads(t[i:j + 1])


# --------------------------------------------------------------------------- #
# Anthropic — Opus 4.8 baseline + Haiku 4.5 candidate
# --------------------------------------------------------------------------- #
class AnthropicBackend:
    provider = "anthropic"

    def __init__(self, name: str, model_id: str):
        import anthropic

        self.name = name
        self.model_id = model_id
        self.client = anthropic.Anthropic(api_key=_env.anthropic_key())

    def _usage(self, r) -> Usage:
        return Usage(in_tok=r.usage.input_tokens, out_tok=r.usage.output_tokens,
                     raw={"id": r.id})

    def json_call(self, system: str, user: str, schema: dict, max_tokens: int = 2048,
                  contract: str | None = None):
        # prompt-for-JSON (output_config.format rejects RESOLUTION_SCHEMA as too complex)
        sys = system + "\n\n" + (contract or render_contract(schema))
        r = self.client.messages.create(
            model=self.model_id, max_tokens=max_tokens, system=sys,
            messages=[{"role": "user", "content": user}],
        )
        text = next((b.text for b in r.content if b.type == "text"), "")
        try:
            return extract_json(text), self._usage(r)
        except json.JSONDecodeError as e:
            err = JSONParseError(f"{self.name}: {e}; text={text[:300]!r}")
            err.usage = self._usage(r)
            raise err from e

    def text_call(self, system: str, user: str, max_tokens: int = 1024):
        r = self.client.messages.create(
            model=self.model_id, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = next((b.text for b in r.content if b.type == "text"), "")
        return text, self._usage(r)


# --------------------------------------------------------------------------- #
# Gemini — gemini-2.5-flash candidate (REST, stdlib only)
# --------------------------------------------------------------------------- #
_GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiBackend:
    provider = "gemini"

    def __init__(self, name: str, model_id: str):
        self.name = name
        self.model_id = model_id
        self.key = _env.gemini_key()

    def _post(self, payload: dict, max_retries: int = 4) -> dict:
        url = f"{_GEMINI_BASE}/{self.model_id}:generateContent?key={self.key}"
        body = json.dumps(payload).encode()
        last = None
        for attempt in range(max_retries):
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                code = e.code
                last = f"HTTP {code}: {e.read()[:200]!r}"
                if code in (429, 500, 503, 529) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 1)
                    continue
                raise RuntimeError(f"{self.name}: {last}") from e
            except urllib.error.URLError as e:
                last = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 1)
                    continue
                raise RuntimeError(f"{self.name}: {last}") from e
        raise RuntimeError(f"{self.name}: exhausted retries ({last})")

    def _usage(self, data: dict) -> Usage:
        um = data.get("usageMetadata", {})
        cand = um.get("candidatesTokenCount", 0) or 0
        think = um.get("thoughtsTokenCount", 0) or 0
        return Usage(in_tok=um.get("promptTokenCount", 0) or 0,
                     out_tok=cand + think, thinking_tok=think, raw=um)

    def _text_of(self, data: dict) -> str:
        cand = data.get("candidates", [{}])[0]
        if cand.get("finishReason") == "MAX_TOKENS":
            # surface truncation so it can be attributed to structured-output budget
            pass
        parts = cand.get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts), cand.get("finishReason")

    def json_call(self, system: str, user: str, schema: dict, max_tokens: int = 8192,
                  contract: str | None = None):
        if contract:
            system = system + "\n\n" + contract
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": to_gemini(schema),
                "temperature": 0,
                "maxOutputTokens": max_tokens,
            },
        }
        data = self._post(payload)
        usage = self._usage(data)
        text, finish = self._text_of(data)
        try:
            return json.loads(text), usage
        except json.JSONDecodeError as e:
            raise JSONParseError(
                f"{self.name}: {e}; finish={finish}; text={text[:300]!r}"
            ) from e

    def text_call(self, system: str, user: str, max_tokens: int = 4096):
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0, "maxOutputTokens": max_tokens},
        }
        data = self._post(payload)
        text, _ = self._text_of(data)
        return text, self._usage(data)


# --------------------------------------------------------------------------- #
# OpenRouter — the gateway for every non-Anthropic candidate (Gemini + DeepSeek)
# --------------------------------------------------------------------------- #
_OR_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterBackend:
    provider = "openrouter"

    def __init__(self, name: str, model_id: str):
        self.name = name
        self.model_id = model_id          # the provider/model OpenRouter slug
        self.key = _env.openrouter_key()

    def _post(self, payload: dict, max_retries: int = 4) -> dict:
        body = json.dumps(payload).encode()
        headers = {
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            # OpenRouter's documented attribution headers (optional but polite).
            "HTTP-Referer": "https://worldfish.digital",
            "X-Title": "WDB model-eval",
        }
        last = None
        for attempt in range(max_retries):
            req = urllib.request.Request(_OR_URL, data=body, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = json.loads(resp.read())
            except urllib.error.HTTPError as e:
                code = e.code
                last = f"HTTP {code}: {e.read()[:200]!r}"
                if code in (429, 500, 502, 503, 529) and attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 1)
                    continue
                raise RuntimeError(f"{self.name}: {last}") from e
            except urllib.error.URLError as e:
                last = str(e)
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 1)
                    continue
                raise RuntimeError(f"{self.name}: {last}") from e
            # A 200 can still carry a provider-side error (OpenRouter passes it through).
            if data.get("error"):
                last = f"provider error: {str(data['error'])[:200]}"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt + 1)
                    continue
                raise RuntimeError(f"{self.name}: {last}")
            return data
        raise RuntimeError(f"{self.name}: exhausted retries ({last})")

    def _usage(self, data: dict) -> Usage:
        u = data.get("usage", {}) or {}
        # Reasoning tokens (when a model emits them) are billed inside completion_tokens
        # by OpenRouter; surface them informationally without double-counting.
        details = u.get("completion_tokens_details") or {}
        think = details.get("reasoning_tokens", 0) or 0
        return Usage(in_tok=u.get("prompt_tokens", 0) or 0,
                     out_tok=u.get("completion_tokens", 0) or 0,
                     thinking_tok=think, raw=u)

    def _text_of(self, data: dict) -> str:
        ch = (data.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        return msg.get("content") or "", ch.get("finish_reason")

    def json_call(self, system: str, user: str, schema: dict, max_tokens: int = 8192,
                  contract: str | None = None):
        # json_object mode guarantees valid JSON but not a schema, so — exactly like
        # the Anthropic path — the key contract is described in-prompt and tolerantly
        # parsed. Both OR candidates are thus tested on the same OpenAI-compatible
        # structured-output channel (NOT Gemini's native responseSchema). The budget
        # is generous (matches the Gemini backend) so a reasoning model — DeepSeek
        # v4-flash thinks by default — never truncates its JSON; only tokens actually
        # emitted are billed, so headroom is free.
        sys = system + "\n\n" + (contract or render_contract(schema))
        payload = {
            "model": self.model_id,
            "messages": [{"role": "system", "content": sys},
                         {"role": "user", "content": user}],
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        data = self._post(payload)
        usage = self._usage(data)
        text, finish = self._text_of(data)
        try:
            return extract_json(text), usage
        except json.JSONDecodeError as e:
            err = JSONParseError(f"{self.name}: {e}; finish={finish}; text={text[:300]!r}")
            err.usage = usage
            raise err from e

    def text_call(self, system: str, user: str, max_tokens: int = 4096):
        # Generous default (matches the Gemini backend) so a reasoning model's
        # thinking budget does not crowd out the Mode-B answer.
        payload = {
            "model": self.model_id,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        data = self._post(payload)
        text, _ = self._text_of(data)
        return text, self._usage(data)


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #
def opus() -> AnthropicBackend:
    return AnthropicBackend("opus-4.8", "claude-opus-4-8")


def sonnet() -> AnthropicBackend:
    return AnthropicBackend("sonnet-4.6", "claude-sonnet-4-6")


def haiku() -> AnthropicBackend:
    return AnthropicBackend("haiku-4.5", "claude-haiku-4-5")


def gemini_flash() -> GeminiBackend:
    return GeminiBackend("gemini-2.5-flash", "gemini-2.5-flash")


# OpenRouter candidates — slugs confirmed live via the models API on 2026-06-23
# (GET https://openrouter.ai/api/v1/models). Names carry an "-or" suffix so cost
# rows and result files never collide with the native gemini-2.5-flash row from #16.
def gemini_or() -> OpenRouterBackend:
    return OpenRouterBackend("gemini-2.5-flash-or", "google/gemini-2.5-flash")


def deepseek_or() -> OpenRouterBackend:
    return OpenRouterBackend("deepseek-v4-flash-or", "deepseek/deepseek-v4-flash")
