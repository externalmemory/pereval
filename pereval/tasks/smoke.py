"""Smoke-test task: verifies the Inspect harness is wired up end to end.

Not an evaluation task. Run with:

    inspect eval pereval/tasks/smoke.py --model <provider/model>
"""

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import exact
from inspect_ai.solver import generate, system_message

SYSTEM = "Answer with a single number and nothing else."


@task
def smoke() -> Task:
    return Task(
        dataset=[
            Sample(
                input="What is the sum of the first 100 positive integers?",
                target="5050",
            )
        ],
        solver=[system_message(SYSTEM), generate()],
        scorer=exact(),
    )
