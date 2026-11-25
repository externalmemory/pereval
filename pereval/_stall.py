"""Stop a sample that has stopped working instead of letting it run to another cap.

`basic_agent` terminates on a `submit` tool call. A model that decides it has
finished and says so in prose never calls it, so the agent replies with its
continue message, the model says it is finished again, and the pair spin until
some unrelated limit fires. deepseek-v4.1-flash-1017 did this on three-body
instance 1 for 354 consecutive turns and burned 59.8M of that run's 65.6M input
tokens before the endpoint cut it off, with a complete `predictions.csv` already
sitting in the sandbox. The same shape appears in the archive as an upstream
problem rather than a model one: Flint's quantile seed 2 spent 265 turns
returning empty content under the same continue message.

`basic_agent` offers no hook for this. `continue_message` is a plain string in
inspect-ai 0.3.245, and the branch that appends it keeps no counter. What inspect
does offer is `on_before_model_generate`, whose dispatcher re-raises
`LimitExceededError` specifically so that limits can be enforced from a hook, so
the detector lives here and no task or solver changes. Firing before the call
means the wasted request is never sent, and the sample lands with `sample.limit`
set rather than as an error.

Scoring is deliberately unchanged. A stalled sample is scored off whatever is in
the sandbox, exactly as a message-limited or time-limited one already is, which
is verified behaviour rather than an assumption. Whether such a cell is
reportable is a question for docs/limitations.md and not for this module.

THE THRESHOLDS ARE MEASURED, NOT CHOSEN. A sliding window over all 359 archived
logs, 1,076 samples and 251 stalls of four or more consecutive turns with no tool
call, swept window length against a per-turn content length. 205 of those stalls
ended with the model recovering and calling a tool again, and killing one of
those would discard real work, so they are the population that sets the floor.
Shorter windows are not safe: at 8 turns, 12 of the 205 recovered stalls would
have been cut off, at 12 turns 6 of them, and at 20 turns one, a Qwen3.6-35B cecl
sample that recovered after 23 idle turns and submitted normally. At 30 turns and
64 characters nothing recovered is touched and three stalls fire, all three
terminal: the deepseek loop above at idle turn 75 of 354, Flint's quantile seed 2
at turn 60 of 265, and a 58-turn Flint two-body stall at its last turn. Two of
those three set published cells, and firing does not change either, because an
empty or one-line turn writes nothing to the sandbox: whatever the scorer read at
the end was already there when the stall began.

What this deliberately does not catch is the verbose stall. deepseek-v4-flash-0731
looped for 156 turns on three-body instance 2 at a median of 306 characters a
turn, which cost that cell a truncated 340 against the 269 a re-run produced.
Catching it needs the content threshold at 400 characters, and that fires on four
recovered stalls including gpt-6-luna's quantile seed 0, which stalled for 49
turns, recovered, and set a published cell. On these two signals a model
repeating itself at length is not separable from a model thinking, so the rule
covers the empty-or-one-line class only.

Note also that the content test reads visible text, not reasoning. A model that
reasons at length and emits a one-line summary each turn without acting will be
stopped at 30 turns. That is intended: in a suite whose deliverable is a file on
disk, 30 turns without a tool call is not progress.
"""

from __future__ import annotations

import re
from typing import Sequence

from inspect_ai.hooks import BeforeModelGenerate, Hooks, hooks
from inspect_ai.util import LimitExceededError

#: Consecutive bare assistant turns tolerated before the sample is stopped.
IDLE_TURNS = 30

#: A turn counts as bare at or below this many normalised characters.
IDLE_CHARS = 64

_KEEP = re.compile(r"[^a-z0-9 ]")


def _normalised_len(text: str | None) -> int:
    return len(_KEEP.sub("", (text or "").lower()).strip())


def _is_bare(message) -> bool:
    """An assistant turn that neither called a tool nor said anything."""
    if getattr(message, "role", None) != "assistant":
        return False
    if getattr(message, "tool_calls", None):
        return False
    return _normalised_len(getattr(message, "text", None)) <= IDLE_CHARS


def idle_run_length(messages: Sequence[object]) -> int:
    """Trailing run of bare assistant turns.

    User messages are skipped rather than counted, because the continue message
    sits between every pair of them. A tool result or an assistant turn with
    content or a tool call ends the run.
    """
    count = 0
    for message in reversed(messages):
        if getattr(message, "role", None) == "user":
            continue
        if _is_bare(message):
            count += 1
        else:
            break
    return count


@hooks(
    name="stall_detector",
    description="Stops a sample stuck answering basic_agent's continue message.",
)
class StallDetector(Hooks):
    async def on_before_model_generate(self, data: BeforeModelGenerate) -> None:
        idle = idle_run_length(data.input)
        if idle >= IDLE_TURNS:
            raise LimitExceededError(
                type="custom",
                value=idle,
                limit=IDLE_TURNS,
                message=(
                    f"stalled: {idle} consecutive assistant turns with no tool call "
                    f"and no more than {IDLE_CHARS} characters of content"
                ),
            )


def install() -> None:
    """No-op: importing this module registers the hook. Called for symmetry."""
