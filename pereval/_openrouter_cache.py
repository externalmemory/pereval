"""Make Anthropic prompt caching actually land on OpenRouter-routed runs.

Every other model in the suite caches without being asked: DeepSeek, Moonshot,
GLM, MiniMax and Ling all do automatic server-side prefix caching, and the logs
show them reading tens of millions of cached tokens. Anthropic is the only family
that requires the caller to mark the prefix with `cache_control`, so it is the
only one that can fail silently, and it did. Every Claude run in this repo,
across three tasks since July, reported zero cache reads.

Inspect's openrouter provider does try. It enables caching by default for
`openrouter/anthropic/*` and marks three places: the last system block, the last
tool definition, and a rolling message-level breakpoint. The first two are
correct. The third never lands here, because it requires a message whose
`content` is a list of blocks, and `basic_agent` with bash and python produces a
plain string for every role. The provider will not convert one, for a good
reason: a `role:"tool"` message has to keep string content for upstream
tool_result translation. So it gives up instead of looking further back, and on
all 30 turns of the haiku migration run not one message-level breakpoint was
placed.

What survived was a breakpoint covering the system message and the tool
definitions, about 240 tokens. Claude Haiku 4.5 has the highest minimum cacheable
prefix of any Claude model, 4096 tokens, and a prefix below the minimum is
skipped without an error: the response just comes back with
`cache_write_tokens: 0`. So the two markers that did land were seventeen times
too short to ever write an entry, which is why nothing in the usage line looked
like a misconfiguration.

The fix is to walk back from the end of `messages` to the newest message that can
carry a marker, which means role user or assistant with non-empty content, and
convert its string content to single-block list form. Messages with
`role:"tool"` are skipped so the tool_result invariant holds, and empty content
is skipped because an empty text block is rejected. Replayed against the logged
request sequences this lands on every turn, and replayed against the token
trajectory it turns $0.97 of input into $0.29.

This only changes how a request is marked, never what it contains, so it cannot
move a score. It is installed as a patch rather than a vendored provider so the
model string in the logs stays `openrouter/anthropic/claude-haiku-4.5` and the
runs stay comparable with the ones already in the table.
"""

from __future__ import annotations

from typing import Any

# Anthropic allows four breakpoints per request. The upstream function spends at
# most three, and this one only adds a message-level marker when upstream placed
# none, so the budget is unchanged.
_CACHEABLE_ROLES = ("user", "assistant")


def _place_rolling_breakpoint(messages: list[dict[str, Any]]) -> bool:
    """Mark the newest message whose content can hold a `cache_control` marker."""
    for msg in reversed(messages):
        if not isinstance(msg, dict) or msg.get("role") not in _CACHEABLE_ROLES:
            continue
        content = msg.get("content")
        if isinstance(content, list) and content and isinstance(content[-1], dict):
            content[-1]["cache_control"] = {"type": "ephemeral"}
            return True
        if isinstance(content, str) and content:
            msg["content"] = [
                {"type": "text", "text": content, "cache_control": {"type": "ephemeral"}}
            ]
            return True
    return False


def _has_message_breakpoint(messages: list[dict[str, Any]]) -> bool:
    """Whether a non-system message already carries a marker upstream placed."""
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") == "system":
            continue
        content = msg.get("content")
        if isinstance(content, list) and any(
            isinstance(block, dict) and "cache_control" in block for block in content
        ):
            return True
    return False


def install() -> bool:
    """Wrap the provider's marker placement. Returns whether the patch went on."""
    try:
        from inspect_ai.model._providers import openrouter
    except ImportError:  # pragma: no cover - inspect_ai is a hard dependency
        return False

    upstream = getattr(openrouter, "_add_anthropic_cache_markers", None)
    if upstream is None or getattr(upstream, "_pereval_patched", False):
        return False

    def _add_anthropic_cache_markers(request: dict[str, Any]) -> None:
        upstream(request)
        messages = request.get("messages")
        if isinstance(messages, list) and messages:
            if not _has_message_breakpoint(messages):
                _place_rolling_breakpoint(messages)

    _add_anthropic_cache_markers._pereval_patched = True  # type: ignore[attr-defined]
    openrouter._add_anthropic_cache_markers = _add_anthropic_cache_markers
    return True
