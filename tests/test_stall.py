"""The stall detector's counting rule and its firing threshold.

Thresholds are measured from the log archive; the reasoning is in
pereval/_stall.py. These tests pin the counting semantics, not the thresholds.
"""

import asyncio

import pytest
from inspect_ai.model import ChatMessageAssistant, ChatMessageSystem, ChatMessageTool, ChatMessageUser
from inspect_ai.tool import ToolCall
from inspect_ai.util import LimitExceededError

from pereval._stall import IDLE_CHARS, IDLE_TURNS, StallDetector, idle_run_length

CONTINUE = "Please proceed to the next step using your best judgement."


def bare(text="Complete."):
    return ChatMessageAssistant(content=text)


def acting():
    return ChatMessageAssistant(
        content="",
        tool_calls=[ToolCall(id="1", function="bash", arguments={"cmd": "ls"})],
    )


def spin(n, text="Complete."):
    """n bare assistant turns, each answered by the continue message."""
    out = []
    for _ in range(n):
        out.append(bare(text))
        out.append(ChatMessageUser(content=CONTINUE))
    return out


def test_no_idle_turns_when_every_turn_acts():
    msgs = [ChatMessageSystem(content="sys"), ChatMessageUser(content="go"), acting()]
    assert idle_run_length(msgs) == 0


def test_continue_messages_do_not_reset_the_run():
    assert idle_run_length(spin(7)) == 7


def test_a_tool_result_resets_the_run():
    msgs = spin(5) + [ChatMessageTool(content="output", function="bash")] + spin(2)
    assert idle_run_length(msgs) == 2


def test_an_assistant_turn_with_content_resets_the_run():
    msgs = spin(9) + [bare("x" * (IDLE_CHARS + 50))] + [ChatMessageUser(content=CONTINUE)] + spin(3)
    assert idle_run_length(msgs) == 3


def test_a_tool_call_resets_the_run_even_with_empty_text():
    assert idle_run_length(spin(9) + [acting()]) == 0


def test_punctuation_and_case_do_not_rescue_a_bare_turn():
    # 'Complete.' and '**COMPLETE!!**' both normalise well under the threshold.
    assert idle_run_length(spin(4, "**COMPLETE!!**")) == 4


def test_hook_is_silent_below_the_threshold():
    asyncio.run(StallDetector().on_before_model_generate(_before(spin(IDLE_TURNS - 1))))


def test_hook_fires_at_the_threshold():
    with pytest.raises(LimitExceededError) as excinfo:
        asyncio.run(StallDetector().on_before_model_generate(_before(spin(IDLE_TURNS))))
    assert excinfo.value.value == IDLE_TURNS
    assert excinfo.value.limit == IDLE_TURNS


def test_hook_does_not_fire_on_a_long_productive_conversation():
    msgs = []
    for _ in range(IDLE_TURNS * 3):
        msgs += [acting(), ChatMessageTool(content="out", function="bash")]
    asyncio.run(StallDetector().on_before_model_generate(_before(msgs)))


def _before(messages):
    from inspect_ai.hooks import BeforeModelGenerate
    from inspect_ai.model import GenerateConfig

    return BeforeModelGenerate(
        model_name="test/model",
        input=messages,
        tools=[],
        tool_choice="auto",
        config=GenerateConfig(),
        cache=None,
    )
