"""The real callers: one adapter per sorter (picks 10 to 12). Built and tested with fakes only; nothing here has
ever been run against a maker. Python 3.9 standard library only.

THE GUARD, IN THE CODE
  * require_switch(env): refuses unless env["SORT_REAL_CALLS"] is exactly "allow". It is the first thing done by
    read_key, by http_post_json and by every adapter's call, so with the switch unset nothing reads a key file and
    nothing opens a connection. A local (Ollama) adapter has no key, so the transport carries the same check.
  * read_key(source, env): the ONE function that reads a key. It checks the switch before it opens any file,
    key_sources.local.json included. key_sources.local.json (neither it nor its template is included in this
    public code edition) names, per maker, where the key is: {"kind": "env_line", "file": PATH,
    "name": NAME} (a NAME=value line) or {"kind": "whole_file", "file": PATH}, plus optional non-secret "headers"
    (for example anthropic-workspace-id, which an organisation-level Anthropic key needs). A value that still looks
    like a template placeholder ("<...>") is refused. No refusal message carries a key or a line of a key file.
  * Request headers are not directly saved. The key and extra header values are tracked for redaction of response
    values and dictionary keys BEFORE JSON serialization. Errors also remove JSON/string/bytes-repr spellings.
    Failed, incomplete, refused and model-mismatched replies remove API-key pieces six characters or longer.
    Extra header values are cleaned whole in every outcome; their fragments can be ordinary response words.
    Successful replies remove whole tracked values only. This is not arbitrary-encoding detection; see redact.
  * Model identity matching is strict by default. Missing, non-text or different reported model names yield no
    countable reply. An explicit Boolean require_model_match=False is recorded when that check is disabled.
  * Tests replace read_key, http_post_json, _urlopen and _open with tripwires before anything runs
    (tests/fakes_first.py) and pass a plain dict as env; os.environ is never given the switch.

FRESH SESSION. Each call sends only the messages it is given (the runner gives turn 1, or turn 1, the reply and
turn 2): no system text, no tools, no previous_response_id, no stored conversation, no fallbacks. Turn 1's reply is
sent back as its reply TEXT only (for Anthropic, without the thinking blocks; for DeepSeek, without
reasoning_content), the same for every maker. See README for why.

THINKING, from each maker's documentation (pages read 2026-11-25; see README):
  Anthropic  claude-fable-5-2, claude-opus-5-5: "thinking": {"type": "adaptive"}, "output_config": {"effort": "high"}
             (Opus 5.5 defaults to medium, so it is set explicitly), anthropic-version 2026-10-21.
  OpenAI     gpt-6.2-astra, gpt-6.2-sol (Responses API): "reasoning": {"effort": "high"}
  xAI        grok-4.7 (Responses API): "reasoning": {"effort": "high"}
  DeepSeek   deepseek-v4-pro (chat completions): "thinking": {"type": "enabled"}, "reasoning_effort": "high"
  Ollama     the model's own default: "think": null (documented as "uses the model default"), "stream": false

OUTPUT CAPS: OUTPUT_TOKEN_LIMIT is the main-call ceiling, SMOKE_OUTPUT_TOKEN_LIMIT the smoke ceiling.
Anthropic/DeepSeek use max_tokens; OpenAI/xAI use max_output_tokens; Ollama uses options.num_predict.
Accounting is maker-specific: xAI documents its cap as visible output only, excluding reasoning. The local
transport timeout is 900 seconds; cloud remains 1800. urllib's timeout bounds blocking socket operations,
not a hard wall-clock deadline for the whole call.

WHAT IS KEPT per call (the record): caller, turn, provider, model_requested, model_reported, model_matches, url,
settings_sent_json (the body without the messages), message_count, started_at and finished_at (from /bin/date),
complete, stop (the maker's stop reason or status), usage_json, response_body_json (the whole body as returned),
partial_text (when the maker said the reply was incomplete), error. A reply the maker marks incomplete, refused or
cut short gives no text (None): the turn fails to parse and the raw is kept as null, with the partial text beside it.
"""
import copy
import json
import os
import re
import urllib.error
import urllib.request

from common import Refuse, HERE, clock
from callers import (Caller, Reply, OUTPUT_TOKEN_LIMIT, SMOKE_OUTPUT_TOKEN_LIMIT,
                     validate_output_token_limit)

SWITCH = "SORT_REAL_CALLS"
KEY_SOURCES = os.path.join(HERE, "key_sources.local.json")
SMOKE_LINE = "Reply with the single word ready."
ANTHROPIC_VERSION = "2026-10-21"
TIMEOUT_SECONDS = 1800
LOCAL_TIMEOUT_SECONDS = 900
MIN_KEY_PIECE = 6

# Module-level so that tests can replace them before anything runs. Never call urlopen or open on a key directly.
_urlopen = urllib.request.urlopen
_open = open


def require_switch(env):
    env = os.environ if env is None else env
    if env.get(SWITCH) != "allow":
        raise Refuse("real calls are off: %s is not 'allow' in this run's environment, so no key was read and no "
                     "connection was opened" % SWITCH)


class TransportError(Exception):
    def __init__(self, status, body):
        self.status, self.body = status, body
        super().__init__("HTTP %s: %s" % (status, body))


def _placeholder(v):
    return isinstance(v, str) and v.strip().startswith("<")


def read_key(source, env=None, sources_path=None, opener=None):
    """The one function that reads a key. Returns (key, extra_headers). Refuses before touching any file unless the
    switch is on."""
    require_switch(env)
    opener = _open if opener is None else opener
    path = KEY_SOURCES if sources_path is None else sources_path
    try:
        with opener(path, encoding="utf-8") as fh:
            sources = json.load(fh)
    except (OSError, ValueError):
        raise Refuse("key sources file %s cannot be read as JSON; copy key_sources.local.TEMPLATE.json to "
                     "key_sources.local.json and fill it in" % path)
    entry = sources.get(source) if isinstance(sources, dict) else None
    if not isinstance(entry, dict):
        raise Refuse("key sources file has no entry for %r" % source)
    headers = entry.get("headers", {})
    if not isinstance(headers, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in headers.items()):
        raise Refuse("key source %r: headers must map header names to text" % source)
    if any(_placeholder(v) for v in list(entry.values()) + list(headers.values())):
        raise Refuse("key source %r still holds a template placeholder; fill key_sources.local.json" % source)
    kind, kfile = entry.get("kind"), entry.get("file")
    if kind not in ("env_line", "whole_file"):
        raise Refuse("key source %r: kind must be env_line or whole_file" % source)
    if not isinstance(kfile, str) or not kfile:
        raise Refuse("key source %r: file must name a file" % source)
    try:
        with opener(kfile, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        raise Refuse("key source %r: the file named for it cannot be read" % source)
    if kind == "whole_file":
        key = text.strip()
    else:
        name, key = entry.get("name"), None
        if not isinstance(name, str) or not name:
            raise Refuse("key source %r: env_line needs a name" % source)
        for line in text.split("\n"):
            s = line.strip()
            if s.startswith("export "):
                s = s[len("export "):].strip()
            if "=" not in s:
                continue
            n, v = s.split("=", 1)
            if n.strip() == name:
                v = v.strip()
                if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
                    v = v[1:-1]
                key = v
        if key is None:
            raise Refuse("key source %r: no line for the name %s in the file named for it" % (source, name))
    if not key or any(c.isspace() for c in key):
        raise Refuse("key source %r: the value found is empty or holds spaces" % source)
    return key, dict(headers)


def http_post_json(url, headers, body, timeout, env=None):
    """The transport. Refuses before opening a connection unless the switch is on. Never logs or keeps headers."""
    require_switch(env)
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=dict(headers), method="POST")
    try:
        with _urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        try:
            text = e.read().decode("utf-8", "replace")
        except Exception:
            text = ""
        raise TransportError(e.code, text[:4000])
    return json.loads(raw.decode("utf-8"))


def _escaped_spellings(text):
    """Raw, JSON, Python string repr, and UTF-8/Latin-1 bytes repr; no URL/base64 decoding."""
    result = {text, json.dumps(text, ensure_ascii=False)[1:-1], json.dumps(text, ensure_ascii=True)[1:-1],
              repr(text)[1:-1]}
    for encoding in ("utf-8", "latin-1"):
        try:
            result.add(repr(text.encode(encoding))[2:-1])
        except UnicodeEncodeError:
            pass
    return result


def _redaction_plan(values, min_piece, piece_values=None):
    """One matcher for whole tracked values; only selected values contribute pieces.

    Omitted piece_values preserves the single-key helper policy. Call finalization explicitly selects the API key,
    because fragments of identifiers in extra headers can be ordinary response words.
    """
    whole = set()
    pieces = set()
    for value in values:
        if not value:
            continue
        whole.update(_escaped_spellings(value))
        if min_piece and (piece_values is None or value in piece_values):
            for size in range(len(value) - 1, min_piece - 1, -1):
                for i in range(0, len(value) - size + 1):
                    pieces.update(_escaped_spellings(value[i:i + size]))
    candidates = whole | pieces
    ordered = sorted((value for value in candidates if value), key=lambda value: (-len(value), value))
    pattern = re.compile("|".join(re.escape(value) for value in ordered)) if ordered else None
    used_characters = set()
    for value in ordered:
        used_characters.update(value)
    separator = next((chr(point) for point in range(0xE000, 0xF900) if chr(point) not in used_characters), None)
    if separator is None:
        raise Refuse("no safe redaction separator is available")
    marks = []
    for mark in ("[KEY REDACTED]", "[KEY PIECE REDACTED]"):
        # Never replace with an empty string: that can concatenate neighboring text into another tracked value.
        # This character occurs in no tracked value or escaped spelling. Bound both sides of ordinary markers
        # too: an otherwise safe marker could complete a tracked value by joining the neighboring source text.
        marks.append(separator if any(value in mark for value in ordered) else separator + mark + separator)
    return pattern, whole, marks


def _redact_plan(text, plan):
    pattern, whole, marks = plan
    if not isinstance(text, str) or pattern is None:
        return text
    return pattern.sub(lambda match: marks[0 if match.group(0) in whole else 1], text)


def redact(text, key, min_piece=MIN_KEY_PIECE):
    """Remove raw/standard escaped spellings and >=min_piece substrings; zero preserves success fragments.

    No arbitrary decoding. A single pass never rescans inserted markers. Finalization combines all tracked values
    in one plan, so a later replacement cannot reintroduce an earlier value through a marker.
    """
    return _redact_plan(text, _redaction_plan([key], min_piece))


class RedactionCollision(ValueError):
    pass


def _scrub_plan(obj, plan):
    if isinstance(obj, str):
        return _redact_plan(obj, plan)
    if isinstance(obj, dict):
        cleaned = {}
        for name, value in obj.items():
            clean_name = _redact_plan(name, plan) if isinstance(name, str) else name
            if clean_name in cleaned:
                raise RedactionCollision("redaction makes dictionary keys ambiguous")
            cleaned[clean_name] = _scrub_plan(value, plan)
        return cleaned
    if isinstance(obj, list):
        return [_scrub_plan(value, plan) for value in obj]
    return obj


def scrub(obj, key, min_piece):
    return _scrub_plan(obj, _redaction_plan([key], min_piece))


def _tracked_values(key, extra_headers):
    if key is not None and not isinstance(key, str):
        raise Refuse("redaction key must be text or null")
    if extra_headers is None:
        extra_headers = {}
    if not isinstance(extra_headers, dict) or not all(isinstance(name, str) and isinstance(value, str)
                                                    for name, value in extra_headers.items()):
        raise Refuse("extra headers must map text names to text values")
    return sorted({value for value in [key] + list(extra_headers.values()) if value}, key=lambda value: (-len(value), value))


def _scrub_record(record, plan):
    # These field labels come from this module's public record schema, not from a provider or credential source.
    # Preserve them even when a tracked value happens to equal a label. Provider dictionaries inside values still
    # have their keys sanitized. No internal wrapper/envelope participates in redaction.
    return {name: _scrub_plan(value, plan) for name, value in record.items()}


def finalize_reply(adapter, record, response=None, error=None, key=None, extra_headers=None):
    """Pure response finalization, shared by the guarded caller and offline regression tests.

    No keys, files, clocks, environment or connections are read here. Input records/responses are not mutated.
    Identity decisions precede sanitization. Only sanitized structured bodies are serialized into the record.
    """
    strict = adapter.require_model_match
    if type(strict) is not bool:
        raise Refuse("require_model_match must be a Boolean")
    values = _tracked_values(key, extra_headers)
    rec = copy.deepcopy(record)
    rec.update(require_model_match=strict, complete=False, failure_reason=None, error=None,
               model_reported=None, model_matches=None, usage_json=None, response_body_json=None, partial_text=None)
    text, usage = None, None
    if error is not None:
        rec.update(error="%s: %s" % (type(error).__name__, error), failure_reason="transport_error")
    else:
        try:
            text, model, usage, stop, complete = adapter.read_response(response)
            if not isinstance(text, str):
                raise TypeError("reply text must be a string")
            rec.update(model_reported=model, model_matches=(model == adapter.model) if isinstance(model, str) and model else None,
                       stop=stop, complete=bool(complete))
            if strict and (not isinstance(model, str) or not model):
                reason = "model_reported_missing" if model is None or model == "" else "model_reported_invalid"
                rec.update(complete=False, failure_reason=reason, error="reported model is missing or is not nonempty text")
            elif strict and model != adapter.model:
                rec.update(complete=False, failure_reason="model_mismatch",
                           error="model mismatch: requested %r, reported %r" % (adapter.model, model))
            elif not complete:
                rec.update(failure_reason="provider_incomplete", error="provider did not complete the reply")
        except (KeyError, IndexError, TypeError, AttributeError, ValueError) as exc:
            rec.update(complete=False, failure_reason="unexpected_response_shape",
                       error="unexpected response shape (%s: %s)" % (type(exc).__name__, exc))
            text = None
    if not rec["complete"]:
        rec["partial_text"] = text
        text = None
    pieces = MIN_KEY_PIECE if not rec["complete"] or rec["error"] is not None else 0
    plan = _redaction_plan(values, pieces, piece_values=[key] if key else [])
    try:
        clean_record = _scrub_record(rec, plan)
        clean_body, clean_usage, clean_text = (_scrub_plan(response, plan), _scrub_plan(usage, plan), _scrub_plan(text, plan))
        clean_record["response_body_json"] = json.dumps(clean_body, ensure_ascii=False, sort_keys=True) if response is not None else None
        clean_record["usage_json"] = json.dumps(clean_usage, ensure_ascii=False, sort_keys=True) if usage is not None else None
        return Reply(clean_text, clean_record)
    except RedactionCollision:
        # Do not silently merge evidence or keep the unsanitized body when two keys become one.
        rec.update(complete=False, failure_reason="redaction_collision", error="redaction makes dictionary keys ambiguous",
                   model_reported=None, stop=None, usage_json=None, response_body_json=None, partial_text=None)
        return Reply(None, _scrub_record(rec, _redaction_plan(values, MIN_KEY_PIECE, piece_values=[key] if key else [])))


def check_messages(messages):
    if not isinstance(messages, list) or not messages:
        raise Refuse("messages must be a non-empty list")
    for i, m in enumerate(messages):
        if not isinstance(m, dict) or set(m) != {"role", "content"} or not isinstance(m["content"], str):
            raise Refuse("messages[%d] must be exactly {\"role\", \"content\"} with text content" % i)
        want = "user" if i % 2 == 0 else "assistant"
        if m["role"] != want:
            raise Refuse("messages must alternate user, assistant, user, starting with user; messages[%d] is %r"
                         % (i, m["role"]))
    if messages[-1]["role"] != "user":
        raise Refuse("messages must end with a user message")


class Adapter(Caller):
    is_dry = False
    kind = None
    key_source = None
    messages_field = "messages"

    def __init__(self, name, provider, model, url, require_model_match=True,
                 output_token_limit=OUTPUT_TOKEN_LIMIT):
        if type(require_model_match) is not bool:
            raise Refuse("require_model_match must be a Boolean")
        self.name, self.provider, self.model, self.url = name, provider, model, url
        self.timeout = LOCAL_TIMEOUT_SECONDS if self.kind == "ollama" else TIMEOUT_SECONDS
        self.require_model_match = require_model_match
        self.output_token_limit = validate_output_token_limit(output_token_limit)

    def settings(self):
        raise NotImplementedError

    def build_request(self, messages):
        """Pure: (url, body). The body is the documented settings plus the messages exactly as given."""
        validate_output_token_limit(self.output_token_limit)
        check_messages(messages)
        body = self.settings()
        body[self.messages_field] = copy.deepcopy(messages)
        return self.url, body

    def headers(self, key, extra):
        h = {"Content-Type": "application/json", "Authorization": "Bearer " + key}
        h.update(extra)
        return h

    def read_response(self, resp):
        """-> (text, model_reported, usage, stop, complete)"""
        raise NotImplementedError

    def call(self, conversation, env=None):
        require_switch(env)
        if type(self.require_model_match) is not bool:
            raise Refuse("require_model_match must be a Boolean")
        url, body = self.build_request(conversation.messages)
        key, extra = read_key(self.key_source, env=env) if self.key_source else (None, {})
        record = {"caller": self.name, "turn": conversation.turn(), "provider": self.provider,
                  "model_requested": self.model, "model_reported": None, "model_matches": None, "url": url,
                  "settings_sent_json": json.dumps(self.settings(), sort_keys=True),
                  "message_count": len(body[self.messages_field]), "started_at": clock(), "finished_at": None,
                  "complete": False, "stop": None, "usage_json": None, "response_body_json": None,
                  "partial_text": None, "error": None}
        resp, error = None, None
        try:
            headers = self.headers(key, extra)
            resp = http_post_json(url, headers, body, self.timeout, env=env)
        except Refuse:
            raise
        except Exception as e:  # HTTP error, network error, timeout, a body that is not JSON
            error = e
        record["finished_at"] = clock()
        return finalize_reply(self, record, response=resp, error=error, key=key, extra_headers=extra)


class AnthropicAdapter(Adapter):
    kind, key_source = "anthropic", "anthropic"

    def settings(self):
        return {"model": self.model, "max_tokens": self.output_token_limit, "thinking": {"type": "adaptive"},
                "output_config": {"effort": "high"}}

    def headers(self, key, extra):
        h = {"content-type": "application/json", "x-api-key": key, "anthropic-version": ANTHROPIC_VERSION}
        h.update(extra)
        return h

    def read_response(self, resp):
        text = "".join(b["text"] for b in resp["content"] if b.get("type") == "text")
        stop = resp.get("stop_reason")
        return text, resp.get("model"), resp.get("usage"), stop, stop == "end_turn"


class ResponsesAdapter(Adapter):
    """OpenAI and xAI, both through their Responses API."""
    messages_field = "input"

    def settings(self):
        return {"model": self.model, "max_output_tokens": self.output_token_limit,
                "reasoning": {"effort": "high"}}

    def read_response(self, resp):
        parts = []
        for item in resp["output"]:
            if item.get("type") == "message":
                parts += [c["text"] for c in item.get("content", []) if c.get("type") == "output_text"]
        status = resp.get("status")
        return "".join(parts), resp.get("model"), resp.get("usage"), status, status == "completed"


class OpenAIAdapter(ResponsesAdapter):
    kind, key_source = "openai", "openai"


class XAIAdapter(ResponsesAdapter):
    kind, key_source = "xai", "xai"


class DeepSeekAdapter(Adapter):
    kind, key_source = "deepseek", "deepseek"

    def settings(self):
        return {"model": self.model, "max_tokens": self.output_token_limit,
                "thinking": {"type": "enabled"}, "reasoning_effort": "high"}

    def read_response(self, resp):
        ch = resp["choices"][0]
        finish = ch.get("finish_reason")
        return ch["message"]["content"], resp.get("model"), resp.get("usage"), finish, finish == "stop"


class OllamaAdapter(Adapter):
    kind, key_source = "ollama", None

    def settings(self):
        return {"model": self.model, "stream": False, "think": None,
                "options": {"num_predict": self.output_token_limit}}

    def headers(self, key, extra):
        return {"Content-Type": "application/json"}

    def read_response(self, resp):
        usage = {k: v for k, v in resp.items() if k.endswith("_count") or k.endswith("_duration")}
        reason = resp.get("done_reason")
        return resp["message"]["content"], resp.get("model"), usage, reason, resp.get("done") is True and reason == "stop"


LOCAL_A = "http://local-a.example.invalid:11434/api/chat"
LOCAL_B = "http://local-b.example.invalid:11434/api/chat"
ADAPTERS = {
    "anthropic:claude-fable-5-2": (AnthropicAdapter, "anthropic", "claude-fable-5-2",
                                   "https://api.anthropic.com/v1/messages"),
    "anthropic:claude-opus-5-5": (AnthropicAdapter, "anthropic", "claude-opus-5-5",
                                  "https://api.anthropic.com/v1/messages"),
    "openai:gpt-6.2-astra": (OpenAIAdapter, "openai", "gpt-6.2-astra", "https://api.openai.com/v1/responses"),
    "openai:gpt-6.2-sol": (OpenAIAdapter, "openai", "gpt-6.2-sol", "https://api.openai.com/v1/responses"),
    "xai:grok-4.7": (XAIAdapter, "xai", "grok-4.7", "https://api.x.ai/v1/responses"),
    "deepseek:deepseek-v4-pro": (DeepSeekAdapter, "deepseek", "deepseek-v4-pro",
                                 "https://api.deepseek.com/chat/completions"),
    "ollama-local-a:qwen3.8:27b-draft4-text": (OllamaAdapter, "ollama-local-a", "qwen3.8:27b-draft4-text", LOCAL_A),
    "ollama-local-b:gemma4:e4b-mlx": (OllamaAdapter, "ollama-local-b", "gemma4:e4b-mlx", LOCAL_B),
}


def get_adapter(name, require_model_match=True, output_token_limit=OUTPUT_TOKEN_LIMIT):
    validate_output_token_limit(output_token_limit)
    if name not in ADAPTERS:
        raise Refuse("no caller named %r exists in this build" % name)
    cls, provider, model, url = ADAPTERS[name]
    return cls(name, provider, model, url, require_model_match=require_model_match,
               output_token_limit=output_token_limit)


# ---------- the test-file scan (brief rule 5) ----------

# Built from pieces, so that this file does not itself name a real key path.
FORBIDDEN_PIECES = ["." + "private-fixture-keys" + ".env", "deepseek" + ".key", "find-generic-" + "password", "Key" + "chain"]
KEY_NAME_IN_QUOTES = re.compile(r"[\"'][A-Z][A-Z0-9_]*_(?:KEY|TOKEN)[\"']")
KEY_NAME_FROM_ENV = re.compile(r"(?:environ|getenv)[^\n]*\b[A-Z][A-Z0-9_]*_(?:KEY|TOKEN)\b")


def scan_for_key_names(paths):
    """Every place in these files that names a real key path, the Keychain, or an environment variable whose name
    ends in _KEY or _TOKEN (in quotes, or read from the environment). Returns [(path, line number, what)]."""
    hits = []
    for p in paths:
        with open(p, encoding="utf-8") as fh:
            for n, line in enumerate(fh, start=1):
                for piece in FORBIDDEN_PIECES:
                    if piece.casefold() in line.casefold():
                        hits.append((p, n, "names %r" % piece))
                if KEY_NAME_IN_QUOTES.search(line) or KEY_NAME_FROM_ENV.search(line):
                    hits.append((p, n, "names a _KEY or _TOKEN variable"))
    return hits
