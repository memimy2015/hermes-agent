from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _load_json(arg: str):
    if arg == "-":
        return json.loads(sys.stdin.read())
    p = Path(arg)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(arg)


def _parse_ts(ts: str) -> float:
    parts = ts.strip().split(":")
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + int(s)
    h, m, s = parts
    return int(h) * 3600 + int(m) * 60 + int(s)


def _merge(video: Path, audios: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)

    inputs: list[str] = ["-i", str(video)]
    chains: list[str] = ["[0:a]asetpts=PTS-STARTPTS[base]"]
    mix_inputs = ["[base]"]

    for i, a in enumerate(audios, start=1):
        start = _parse_ts(str(a["start_time"]))
        end_raw = a.get("end_time")
        path = a.get("audio") or a.get("audio_file") or a.get("path")
        inputs += ["-i", str(path)]

        label_in = f"[{i}:a]"
        label_out = f"[a{i}]"
        chain = label_in
        if end_raw:
            dur = max(0.0, _parse_ts(str(end_raw)) - start)
            chain += f"atrim=0:{dur:.3f},asetpts=PTS-STARTPTS,"
        else:
            chain += "asetpts=PTS-STARTPTS,"
        delay_ms = int(start * 1000)
        chain += f"adelay={delay_ms}|{delay_ms}{label_out}"
        chains.append(chain)
        mix_inputs.append(label_out)

    chains.append(
        f"{''.join(mix_inputs)}amix=inputs={len(mix_inputs)}:duration=first:normalize=0,apad,alimiter=limit=0.97[outa]"
    )
    fc = ";".join(chains)

    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            *inputs,
            "-filter_complex",
            fc,
            "-map",
            "0:v:0",
            "-map",
            "[outa]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out),
        ],
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--audios", required=True)
    args = p.parse_args(argv)

    video = Path(args.video)
    audios = _load_json(args.audios)
    out_dir = Path.cwd() / "merged_segments"
    out = (out_dir / f"{video.stem}_merged.mp4").resolve()
    _merge(video, audios, out)
    print(f"merge voice success! output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
