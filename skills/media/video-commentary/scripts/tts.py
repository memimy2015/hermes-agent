from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv()


def tts_to_file(text: str, emotion: str, out_path: Path) -> Path:
    api_key = os.environ["MINIMAX_API_KEY"]
    url = "https://api.minimaxi.com/v1/t2a_v2"
    payload = {
        "model": "speech-2.8-hd",
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": "ttv-voice-2025062519422425-GrH4Wv1A",
            "speed": 1,
            "vol": 1,
            "pitch": 0,
            "emotion": emotion,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    obj = resp.json()
    audio_hex = obj["data"]["audio"]
    out_path.write_bytes(bytes.fromhex(audio_hex))
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--emotion", required=True)
    p.add_argument("--name", default="tts.mp3")
    args = p.parse_args(argv)

    out_dir = (Path.cwd() / "tts")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = (out_dir / args.name).resolve()
    tts_to_file(args.text, args.emotion, out)
    print(f"tts success! output={json.dumps({'output': str(out)}, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
