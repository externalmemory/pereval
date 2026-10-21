#!/usr/bin/env python3
"""Write a markdown transcript to runs/ for each sample in an Inspect eval log.

Usage: save_transcript.py <log.eval> [more.eval ...]

Standing convention in this repo: every model run leaves a readable transcript
on disk, not just a score. Reasoning content is included when the provider
surfaces it (OpenRouter does; Zen's openai-api provider does not).

Transcripts are never overwritten. Model, task, instance, seed and epoch do not
identify a RUN, only a cell, so re-running any cell used to silently destroy the
archived record of the previous attempt. That is exactly backwards for a repository whose tables are
audited from these files: it deletes evidence at the moment a result is being revised.
On collision the new transcript takes a `-<YYYY-MM-DD>` suffix, and a further `-<logid>`
if that also exists, so archived runs keep their bare names and later generations sit
beside them. Re-saving the same log twice is a no-op.
"""
import json
import os
import re
import sys

from inspect_ai.log import read_eval_log

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RUNS = os.path.join(ROOT, "runs")


def _text(content):
    if isinstance(content, str):
        return content
    out = []
    for part in content or []:
        kind = getattr(part, "type", "")
        if kind == "text":
            out.append(getattr(part, "text", ""))
        elif kind == "reasoning":
            r = getattr(part, "reasoning", "") or ""
            if r:
                out.append("**[reasoning]**\n\n> " + r.replace("\n", "\n> "))
    return "\n\n".join(out)


#: Argument names that hold the body of a tool call. `command` is what Inspect's
#: own bash() and python() tools use, and leaving it out silently archived 259 of
#: 281 calls in one migration run as an empty block: a transcript of the agent's
#: reasoning with the work removed. Anything unrecognised is dumped whole rather
#: than dropped, so a tool signature this list has not met costs noise, not
#: evidence.
BODY_KEYS = ("command", "code", "cmd", "answer", "input", "text")


def _call_text(args: dict) -> str:
    """The body of a tool call, whatever the tool chose to name its argument."""
    for key in BODY_KEYS:
        if isinstance(args.get(key), str) and args[key].strip():
            return args[key]
    return "" if not args else json.dumps(args, indent=2, default=str)


def render(log, sample) -> str:
    scores = sample.scores or {}
    sc = scores.get(log.eval.task) or (next(iter(scores.values())) if scores else None)
    head = [f"# {log.eval.model} — {log.eval.task} (id={sample.id})", ""]
    if sc:
        head.append(f"- {sc.explanation}")
    head.append(f"- messages {len(sample.messages)} | limit {sample.limit} "
                f"| seed {(sample.metadata or {}).get('seed')}")
    head += ["", "---", ""]

    body = []
    for i, m in enumerate(sample.messages):
        body.append(f"## [{i}] {m.role}")
        body.append("")
        t = _text(m.content)
        if t.strip():
            body.append(t)
            body.append("")
        for tc in (getattr(m, "tool_calls", None) or []):
            code = _call_text(tc.arguments or {})
            body.append(f"**tool call: {tc.function}**")
            body.append("")
            body.append("```")
            body.append(str(code)[:20000])
            body.append("```")
            body.append("")
    return "\n".join(head + body) + "\n"


def _free_path(path: str, content: str, log_path: str) -> str | None:
    """A path that will not clobber a different run. None if this run is already saved."""
    stem = os.path.basename(log_path)
    date = (re.match(r"(\d{4}-\d{2}-\d{2})", stem) or [None, "rerun"])[1]
    logid = os.path.splitext(stem)[0].rsplit("_", 1)[-1][:8]
    for candidate in (path, _suffixed(path, date), _suffixed(path, f"{date}-{logid}")):
        if not os.path.exists(candidate):
            return candidate
        # newline="" disables universal-newline translation. Transcripts carry \r\n
        # from sandbox tool output, and a default text read turns that back into \n,
        # so the round trip never compares equal and every re-save forks a new file.
        with open(candidate, newline="") as f:
            if f.read() == content:
                return None  # already saved, byte for byte
    raise RuntimeError(f"cannot find a free transcript name for {path}")


def _suffixed(path: str, suffix: str) -> str:
    base, ext = os.path.splitext(path)
    return f"{base}-{suffix}{ext}"


def main(paths):
    os.makedirs(RUNS, exist_ok=True)
    for p in paths:
        log = read_eval_log(p)
        slug = log.eval.model.replace("/", "-")
        for s in (log.samples or []):
            sid = str(s.id)
            name = sid if sid.startswith(log.eval.task) else f"{log.eval.task}-{sid}"
            # Some tasks (quantile) reuse one sample id across seed runs, so the
            # seed must be in the filename or the runs overwrite each other.
            seed = (s.metadata or {}).get("seed")
            if seed is not None and f"seed-{seed}" not in name:
                name = f"{name}-seed-{seed}"
            # With -T repeats=N the same instance is drawn N times in one log, so the
            # model, task, instance and seed no longer name a SAMPLE. Without the epoch
            # the repeats collide with each other and get handed the collision suffixes
            # meant for separate runs, which reads as three runs on three dates when it
            # is one run drawn three times, and the Nth repeat past the third has no
            # name left at all. Single-draw logs keep their bare names.
            if (log.eval.config.epochs or 1) > 1:
                name = f"{name}-epoch{s.epoch}"
            out = _free_path(os.path.join(RUNS, f"{slug}-{name}.md"), render(log, s), p)
            if out is None:
                continue
            with open(out, "w") as f:
                f.write(render(log, s))
            print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
