from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


_SAFE_NAME_RE = re.compile(r"[^0-9A-Za-z._-]+")


def _sanitize(name: str) -> str:
    s = _SAFE_NAME_RE.sub("_", name.strip())
    return s.strip("._-") or "segment"


def _load_segments(arg: str) -> list[dict]:
    if arg == "-":
        return json.loads(sys.stdin.read())
    p = Path(arg)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(arg)


# def _clear_dir(dir_path: Path) -> None:
#     dir_path.mkdir(parents=True, exist_ok=True)
#     for p in dir_path.iterdir():
#         if p.is_dir():
#             shutil.rmtree(p)
#         else:
#             p.unlink()


def _cut(video: str, start_time: str, end_time: str, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        start_time,
    ]
    if end_time:
        cmd += ["-to", end_time]
    cmd += [
        "-i",
        video,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(out),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--outdir", default=None)
    args = p.parse_args(argv)

    segs = _load_segments(args.segments)
    outdir = Path(args.outdir) if args.outdir else (Path.cwd() / "segments")
    # _clear_dir(outdir)
    outputs: list[str] = []
    for i, seg in enumerate(segs):
        st = str(seg["start_time"])
        et = str(seg.get("end_time") or "")
        name = _sanitize(str(seg.get("name") or seg.get("segment_name") or f"{i:03d}"))
        out = outdir / f"{i:03d}_{name}.mp4"
        _cut(args.video, st, et, out)
        print(f"[切割完成] 第{i:03d}段 {st}->{(et or 'EOF')} 输出={out}", flush=True)
        outputs.append(str(out.resolve()))

    print(f"cut segments success! outputs={json.dumps(outputs, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
