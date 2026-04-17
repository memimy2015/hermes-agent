from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _demucs_cmd() -> list[str]:
    if shutil.which("demucs"):
        return ["demucs"]
    root = Path(__file__).resolve().parents[1]
    local = root / ".venv" / "bin" / "demucs"
    if local.exists():
        return [str(local)]
    return [sys.executable, "-m", "demucs.separate"]


def _ssl_env() -> dict[str, str] | None:
    env = dict(os.environ)
    try:
        import certifi

        ca = certifi.where()
    except Exception:
        ca = None
    if not ca:
        return None
    env["SSL_CERT_FILE"] = ca
    env["REQUESTS_CA_BUNDLE"] = ca
    env["CURL_CA_BUNDLE"] = ca
    return env


def _run(cmd: list[str], env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def _ffmpeg(*args: str) -> None:
    _run(["ffmpeg", "-hide_banner", "-loglevel", "error", *args])


def remove_voice(video_path: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_video = (out_dir / f"{video_path.stem}_without_voice.mp4").resolve()

    with tempfile.TemporaryDirectory(prefix="remove_voice_") as td:
        td_path = Path(td)
        audio_wav = td_path / "audio.wav"
        vocals_wav = td_path / "vocals.wav"
        no_vocals_wav = td_path / "no_vocals.wav"
        vocals_ducked = td_path / "vocals_ducked.wav"
        mixed_wav = td_path / "mixed.wav"

        _ffmpeg(
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(audio_wav),
        )

        demucs_out = td_path / "demucs_out"
        env = _ssl_env()
        _run([*_demucs_cmd(), "--two-stems=vocals", "-n", "htdemucs", "-o", str(demucs_out), str(audio_wav)], env=env)

        stem_dir = demucs_out / "htdemucs" / audio_wav.stem
        shutil.copyfile(stem_dir / "vocals.wav", vocals_wav)
        shutil.copyfile(stem_dir / "no_vocals.wav", no_vocals_wav)

        _ffmpeg(
            "-y",
            "-i",
            str(vocals_wav),
            "-af",
            "compand=attacks=0.01:decays=0.20:points=-90/-90|-35/-35|-28/-38|-22/-45|-16/-52|-10/-60|0/-70,alimiter=limit=0.97",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(vocals_ducked),
        )

        _ffmpeg(
            "-y",
            "-i",
            str(no_vocals_wav),
            "-i",
            str(vocals_ducked),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:normalize=0,alimiter=limit=0.97[a]",
            "-map",
            "[a]",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            "-ac",
            "2",
            str(mixed_wav),
        )

        _ffmpeg(
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(mixed_wav),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-af",
            "apad",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(out_video),
        )

    return out_video


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    args = p.parse_args(argv)
    out = remove_voice(Path(args.video), Path.cwd() / "segments_without_voice")
    print(f"remove voice success! output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
