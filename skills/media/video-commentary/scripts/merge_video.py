from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _load_list(arg: str) -> list[str]:
    if arg == "-":
        return json.loads(sys.stdin.read())
    p = Path(arg)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(arg)


def _merge(videos: list[str], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.parent / "concat_list.txt"
    tmp.write_text("\n".join(f"file {Path(v).resolve().as_posix()!r}" for v in videos) + "\n", encoding="utf-8")
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(tmp),
            "-c",
            "copy",
            str(out),
        ],
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--videos", required=True, help="JSON数组/JSON文件路径/-, 按顺序合并")
    p.add_argument("--output", required=True, help="输出文件名，如 out.mp4")
    args = p.parse_args(argv)

    videos = _load_list(args.videos)
    out_dir = Path.cwd() / "output"
    out = (out_dir / args.output).resolve()
    _merge(videos, out)
    print(f"merge video success! output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
