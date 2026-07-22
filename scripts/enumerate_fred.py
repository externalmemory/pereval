#!/usr/bin/env python3
"""Enumerate candidate FRED series for the quantile task.

Stage 1 (this script, cheap): page through the tag index, which returns full
series metadata, and filter on frequency, seasonal adjustment, units and history
length. No observations are fetched.

Stage 2 (fetch_screen.py): pull observations for survivors and apply the numeric
screen in screen_fred.py.

Output: scripts/out/candidates.json
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from screen_fred import MIN_YOY, metadata_ok   # noqa: E402

KEY = os.environ["FRED_API_KEY"]
BASE = "https://api.stlouisfed.org/fred"
TAGS = "nsa;monthly"
EXCLUDE = "county;msa;state;discontinued"
PAGE = 1000
MIN_MONTHS = MIN_YOY + 12          # observations needed before differencing
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def get(path, **kw):
    q = "&".join(f"{k}={v}" for k, v in kw.items())
    url = f"{BASE}/{path}?api_key={KEY}&file_type=json&{q}"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
            print(f"  retry {attempt + 1} after {e}", file=sys.stderr)


def months_between(a, b):
    return (int(b[:4]) - int(a[:4])) * 12 + int(b[5:7]) - int(a[5:7]) + 1


def main():
    os.makedirs(OUT, exist_ok=True)
    total = get("tags/series", tag_names=TAGS, exclude_tag_names=EXCLUDE,
                limit=1)["count"]
    print(f"tag index: {total} series")

    keep, seen, reasons = [], set(), {}
    for off in range(0, total, PAGE):
        d = get("tags/series", tag_names=TAGS, exclude_tag_names=EXCLUDE,
                limit=PAGE, offset=off)
        for s in d["seriess"]:
            if s["id"] in seen:
                continue
            seen.add(s["id"])
            ok, why = metadata_ok(s)
            if not ok:
                reasons[why.split("=")[0]] = reasons.get(why.split("=")[0], 0) + 1
                continue
            span = months_between(s["observation_start"], s["observation_end"])
            if span < MIN_MONTHS:
                reasons["too short"] = reasons.get("too short", 0) + 1
                continue
            keep.append(dict(id=s["id"], title=s["title"], units=s["units"],
                             start=s["observation_start"],
                             end=s["observation_end"], span=span))
        print(f"  {off + len(d['seriess']):6d}/{total}  kept {len(keep)}",
              flush=True)
        time.sleep(0.4)

    with open(f"{OUT}/candidates.json", "w") as f:
        json.dump(keep, f, indent=1)
    print(f"\ncandidates: {len(keep)}")
    for k, v in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  rejected {v:7d}  {k}")


if __name__ == "__main__":
    main()
