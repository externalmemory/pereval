#!/usr/bin/env python3
"""Write a markdown transcript to runs/ for each sample in an Inspect eval log.

Usage: save_transcript.py <log.eval> [more.eval ...]

Standing convention in this repo: every model run leaves a readable transcript
on disk, not just a score. A task that knows how to draw its submission also
leaves a PNG beside the transcript, under the same stem, written by
`plot_backtest.render_png`. Drawing is best effort: a figure that cannot be
built prints to stderr and never costs the transcript it belongs to. Reasoning content is included when the provider
surfaces it (OpenRouter does; Zen's openai-api provider does not).

A re-run overwrites the transcript of the cell it re-runs. Model, task, instance, seed
and epoch name a cell rather than a run, so a re-run collides by construction, and the
rule here used to resolve that by suffixing the newcomer with `-<YYYY-MM-DD>`. That kept
both files and left the superseded one under the bare name the README points auditors
at, which is the wrong way round: a cell is re-run because the first attempt failed, so
the file holding the failure outranked the file holding the result. It happened on three
cells of one local-model run before anyone noticed.

Overwriting costs no evidence, because a transcript is derived and the `.eval` log is the
record. Logs carry their own timestamp and id, are never overwritten, and are committed,
so a superseded transcript can be rebuilt by running this script against the older log.
Keeping the old log is therefore the way to keep the old transcript. Re-saving the same
log twice is still a no-op, byte for byte, and a run that draws no figure now clears a
stale PNG left by the run it replaces, which would otherwise sit under a current
transcript's name showing the previous attempt's submission.
"""
import json
import os
import sys

from inspect_ai.log import read_eval_log

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
RUNS = os.path.join(ROOT, "runs")
if HERE not in sys.path:
    sys.path.insert(0, HERE)


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


def _target_path(path: str, content: str) -> str | None:
    """Where this sample's transcript goes. None if it is already there, byte for byte."""
    if os.path.exists(path):
        # newline="" disables universal-newline translation. Transcripts carry \r\n
        # from sandbox tool output, and a default text read turns that back into \n,
        # so the round trip never compares equal and every re-save rewrites the file.
        with open(path, newline="") as f:
            if f.read() == content:
                return None  # already saved, nothing to do and no figure to redraw
    return path


def sample_stem(log, sample) -> str:
    """The basename everything archived from one sample shares.

    The transcript and the figure have to agree on it, so it lives here, where
    the collision rules that shape it already live.
    """
    sid = str(sample.id)
    name = sid if sid.startswith(log.eval.task) else f"{log.eval.task}-{sid}"
    # Some tasks (quantile) reuse one sample id across seed runs, so the seed
    # must be in the filename or the runs overwrite each other.
    seed = (sample.metadata or {}).get("seed")
    if seed is not None and f"seed-{seed}" not in name:
        name = f"{name}-seed-{seed}"
    # With -T repeats=N the same instance is drawn N times in one log, so the
    # model, task, instance and seed no longer name a SAMPLE. Without the epoch
    # the repeats collide with each other and get handed the collision suffixes
    # meant for separate runs, which reads as three runs on three dates when it
    # is one run drawn three times, and the Nth repeat past the third has no
    # name left at all. Single-draw logs keep their bare names.
    if (log.eval.config.epochs or 1) > 1:
        name = f"{name}-epoch{sample.epoch}"
    return f"{log.eval.model.replace('/', '-')}-{name}"


def _write_figure(log, sample, md_path) -> None:
    """The companion figure, for a task that has one. Best effort, always.

    A figure that cannot be drawn has to take the previous run's figure with it.
    Transcripts are overwritten in place, so a cell that drew a plot on its first
    attempt and none on its second would otherwise keep the first attempt's plot
    beside the second attempt's transcript, under the same stem and with nothing
    on either file to say they came from different runs.
    """
    png = os.path.splitext(md_path)[0] + ".png"
    drawn = False
    try:
        from plot_backtest import render_png
        drawn = bool(render_png(log, sample, png))
        if drawn:
            print(png)
    except Exception as exc:                       # noqa: BLE001 - never fatal
        print(f"figure skipped for {os.path.basename(png)}: {exc}",
              file=sys.stderr)
    if not drawn and os.path.exists(png):
        os.remove(png)
        print(f"removed stale figure {png}")


def main(paths):
    os.makedirs(RUNS, exist_ok=True)
    for p in paths:
        log = read_eval_log(p)
        for s in (log.samples or []):
            stem = os.path.join(RUNS, f"{sample_stem(log, s)}.md")
            out = _target_path(stem, render(log, s))
            if out is None:
                continue
            with open(out, "w") as f:
                f.write(render(log, s))
            print(out)
            _write_figure(log, s, out)


if __name__ == "__main__":
    main(sys.argv[1:])
