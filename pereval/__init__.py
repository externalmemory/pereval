"""perEval: Inspect-based evaluation suite for quantitative model development tasks."""

from pereval._openrouter_cache import install as _install_openrouter_cache

__version__ = "0.0.1"

# Anthropic models reach OpenRouter without a usable cache breakpoint; see the
# module docstring. Installed here because every task imports this package
# before the first model call.
_install_openrouter_cache()
