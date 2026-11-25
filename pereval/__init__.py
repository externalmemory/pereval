"""perEval: Inspect-based evaluation suite for quantitative model development tasks."""

from pereval import _stall as _stall  # registers the stall detector hook on import
from pereval._openrouter_cache import install as _install_openrouter_cache

__version__ = "0.0.1"

# Anthropic models reach OpenRouter without a usable cache breakpoint; see the
# module docstring. Installed here because every task imports this package
# before the first model call.
_install_openrouter_cache()

# A sample that stops calling tools used to spin against basic_agent's continue
# message until an unrelated cap fired; see pereval/_stall.py. Registered by the
# import above, which runs before the first model call for the same reason the
# cache patch does.
_stall.install()
