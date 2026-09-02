"""STOP-gate reachability probe — confirm every candidate answers before any eval run.

Per the eval's hard rule: if a candidate cannot be reached (bad/missing key, API
error, 404 slug), STOP and report — never fabricate a verdict. This makes a tiny,
cheap call to each candidate and prints model id + token usage (proving the cost
seam works), masking the keys. Baseline Opus is also pinged so the reference row is
grounded.

Covers two arms:
  * Anthropic direct — baseline Opus 4.8 + candidate Haiku 4.5.
  * OpenRouter gateway (the #16-superseding arm) — the models API (slug resolution)
    + a plain AND a json_object probe to each candidate slug (google/gemini-2.5-flash,
    deepseek/deepseek-v4-flash), confirming Bearer auth, the slug, and that json mode
    returns parseable JSON with usage. The legacy native-Gemini probe is kept so #16's
    AI-Studio row stays reproducible.

Run:  .venv/bin/python -m model_eval.reach_probe   (from repo root)
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from . import _env

GEMINI_CANDIDATES = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
OPENROUTER_SLUGS = ["google/gemini-2.5-flash", "deepseek/deepseek-v4-flash"]
_OR_BASE = "https://openrouter.ai/api/v1"


def mask(k: str | None) -> str:
    if not k:
        return "<MISSING>"
    return f"{k[:6]}…{k[-4:]} (len {len(k)})"


def probe_anthropic(model: str, key: str) -> dict:
    import anthropic

    client = anthropic.Anthropic(api_key=key)
    r = client.messages.create(
        model=model,
        max_tokens=16,
        messages=[{"role": "user", "content": "Reply with the single word: pong"}],
    )
    text = next((b.text for b in r.content if b.type == "text"), "")
    return {
        "ok": True,
        "model_echo": r.model,
        "text": text.strip(),
        "in_tok": r.usage.input_tokens,
        "out_tok": r.usage.output_tokens,
    }


def gemini_list_models(key: str) -> list[str]:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}&pageSize=200"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read())
    out = []
    for m in data.get("models", []):
        if "generateContent" in m.get("supportedGenerationMethods", []):
            out.append(m["name"].removeprefix("models/"))
    return out


def probe_gemini(model: str, key: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = json.dumps({
        "contents": [{"parts": [{"text": "Reply with the single word: pong"}]}],
        "generationConfig": {"maxOutputTokens": 16, "temperature": 0},
    }).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    cand = data.get("candidates", [{}])[0]
    parts = cand.get("content", {}).get("parts", [{}])
    text = "".join(p.get("text", "") for p in parts)
    um = data.get("usageMetadata", {})
    return {
        "ok": True,
        "model_echo": model,
        "text": text.strip(),
        "in_tok": um.get("promptTokenCount"),
        "out_tok": um.get("candidatesTokenCount"),
        "finish": cand.get("finishReason"),
    }


def openrouter_models(key: str) -> dict[str, dict]:
    """Map slug -> model entry from the OpenRouter models API (slug resolution +
    pass-through pricing). Confirms Bearer auth and that the slugs are real."""
    req = urllib.request.Request(f"{_OR_BASE}/models",
                                 headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return {m["id"]: m for m in data.get("data", [])}


def probe_openrouter(slug: str, key: str, json_mode: bool) -> dict:
    if json_mode:
        content = 'Return ONLY this JSON object: {"reply":"pong"}'
    else:
        content = "Reply with the single word: pong"
    # Budget headroom: DeepSeek v4-flash reasons by default (~60 reasoning tokens
    # even on a trivial prompt), so a 32-token probe would truncate before any
    # content — a probe artifact, not unreachability. The real runs use 4-8k.
    body = {"model": slug, "messages": [{"role": "user", "content": content}],
            "max_tokens": 256, "temperature": 0}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        f"{_OR_BASE}/chat/completions", data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read())
    if data.get("error"):
        raise RuntimeError(f"provider error: {str(data['error'])[:160]}")
    ch = (data.get("choices") or [{}])[0]
    text = (ch.get("message") or {}).get("content") or ""
    if json_mode:  # confirm it actually parses as JSON
        json.loads(text)
    u = data.get("usage", {}) or {}
    return {"ok": True, "text": text.strip()[:40], "in_tok": u.get("prompt_tokens"),
            "out_tok": u.get("completion_tokens"), "finish": ch.get("finish_reason")}


def main() -> int:
    ak = _env.anthropic_key()
    gk = _env.gemini_key()
    ork = _env.openrouter_key()
    print("=" * 72)
    print("REACHABILITY PROBE — STOP gate before any eval run")
    print("=" * 72)
    print(f"ANTHROPIC_API_KEY  : {mask(ak)}")
    print(f"GEMINI key         : {mask(gk)}")
    print(f"OPENROUTER_API_KEY : {mask(ork)}")
    print("-" * 72)

    failures = []

    # Anthropic: baseline Opus 4.8 + candidate Haiku 4.5
    if not ak:
        failures.append("ANTHROPIC key missing")
    else:
        for model in ["claude-opus-4-8", "claude-haiku-4-5"]:
            try:
                r = probe_anthropic(model, ak)
                print(f"[anthropic] {model:22} OK  echo={r['model_echo']:28} "
                      f"text={r['text']!r:8} in={r['in_tok']} out={r['out_tok']}")
            except Exception as e:  # noqa: BLE001
                print(f"[anthropic] {model:22} FAIL  {type(e).__name__}: {e}")
                failures.append(f"anthropic/{model}: {e}")

    # Gemini: list, then probe the first reachable candidate
    if not gk:
        failures.append("GEMINI key missing")
    else:
        try:
            models = gemini_list_models(gk)
            print(f"[gemini] {len(models)} generateContent models visible; "
                  f"candidates present: "
                  f"{[m for m in GEMINI_CANDIDATES if m in models]}")
            picked = next((m for m in GEMINI_CANDIDATES if m in models), None) or (models[0] if models else None)
            if not picked:
                failures.append("gemini: no generateContent model available")
            else:
                r = probe_gemini(picked, gk)
                print(f"[gemini]    {picked:22} OK  text={r['text']!r:8} "
                      f"in={r['in_tok']} out={r['out_tok']} finish={r['finish']}")
                print(f"[gemini] full 2.x/flash/pro list: "
                      f"{[m for m in models if m.startswith(('gemini-2', 'gemini-flash', 'gemini-pro'))][:20]}")
        except urllib.error.HTTPError as e:
            print(f"[gemini] FAIL  HTTP {e.code}: {e.read()[:200]!r}")
            failures.append(f"gemini: HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            print(f"[gemini] FAIL  {type(e).__name__}: {e}")
            failures.append(f"gemini: {e}")

    # OpenRouter: models-API slug resolution + plain & json_object probe per slug
    if not ork:
        failures.append("OPENROUTER key missing")
    else:
        try:
            catalog = openrouter_models(ork)
            print(f"[openrouter] models API OK — {len(catalog)} models visible")
            for slug in OPENROUTER_SLUGS:
                entry = catalog.get(slug)
                if not entry:
                    print(f"[openrouter] {slug:34} FAIL  slug not in models API (404-equivalent)")
                    failures.append(f"openrouter/{slug}: slug absent")
                    continue
                p = entry.get("pricing", {})
                price = f"${float(p.get('prompt',0))*1e6:.3f}/${float(p.get('completion',0))*1e6:.3f} per Mtok (list)"
                slug_failed = False
                for jm in (False, True):
                    try:
                        r = probe_openrouter(slug, ork, json_mode=jm)
                        print(f"[openrouter] {slug:34} OK  json={str(jm):5} "
                              f"text={r['text']!r:8} in={r['in_tok']} out={r['out_tok']}")
                    except Exception as e:  # noqa: BLE001
                        print(f"[openrouter] {slug:34} FAIL json={jm}  {type(e).__name__}: {str(e)[:120]}")
                        failures.append(f"openrouter/{slug} (json={jm}): {e}")
                        slug_failed = True
                if not slug_failed:
                    print(f"[openrouter] {slug:34} pricing: {price}")
        except urllib.error.HTTPError as e:
            print(f"[openrouter] FAIL  HTTP {e.code}: {e.read()[:200]!r}")
            failures.append(f"openrouter: HTTP {e.code}")
        except Exception as e:  # noqa: BLE001
            print(f"[openrouter] FAIL  {type(e).__name__}: {e}")
            failures.append(f"openrouter: {e}")

    print("=" * 72)
    if failures:
        print("RESULT: STOP — at least one candidate is unreachable:")
        for f in failures:
            print(f"   - {f}")
        return 1
    print("RESULT: all candidates reachable (Anthropic direct + OpenRouter gateway) — eval may proceed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
