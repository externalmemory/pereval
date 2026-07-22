#!/usr/bin/env python3
"""Write a markdown transcript to runs/ for each sample in an Inspect eval log.

Usage: save_transcript.py <log.eval> [more.eval ...]

Standing convention in this repo: every model run leaves a readable transcript
on disk, not just a score. Reasoning content is included when the provider
surfaces it (OpenRouter does; Zen's openai-api provider does not).
"""
import os
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


def render(log, sample) -> str:
    sc = (sample.scores or {}).get("quantile")
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
            args = tc.arguments or {}
            code = args.get("code") or args.get("cmd") or args.get("answer") or ""
            body.append(f"**tool call: {tc.function}**")
            body.append("")
            body.append("```")
            body.append(str(code)[:20000])
            body.append("```")
            body.append("")
    return "\n".join(head + body) + "\n"


def main(paths):
    os.makedirs(RUNS, exist_ok=True)
    for p in paths:
        log = read_eval_log(p)
        slug = log.eval.model.replace("/", "-")
        for s in (log.samples or []):
            sid = str(s.id)
            name = sid if sid.startswith(log.eval.task) else f"{log.eval.task}-{sid}"
            out = os.path.join(RUNS, f"{slug}-{name}.md")
            with open(out, "w") as f:
                f.write(render(log, s))
            print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
