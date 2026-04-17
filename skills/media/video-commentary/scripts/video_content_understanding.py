import argparse
import os
from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv
load_dotenv()

def _extract_output_text(response) -> str:
    out_items = getattr(response, "output", None)
    if out_items is None and isinstance(response, dict):
        out_items = response.get("output")
    if not out_items:
        return str(response)
    texts: list[str] = []
    for item in out_items:
        if getattr(item, "type", None) == "message" or (isinstance(item, dict) and item.get("type") == "message"):
            content = getattr(item, "content", None) if not isinstance(item, dict) else item.get("content")
            if not content:
                continue
            for c in content:
                t = getattr(c, "type", None) if not isinstance(c, dict) else c.get("type")
                if t in ("output_text", "text"):
                    txt = getattr(c, "text", None) if not isinstance(c, dict) else c.get("text")
                    if txt:
                        texts.append(str(txt))
    return "\n".join(texts).strip() if texts else str(response)

def run(
    input_video: str,
    prompt: str
) -> str:
    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3", 
        api_key=os.getenv("ARK_API_KEY")
    )
    file_obj = client.files.create(
        file=open(input_video, "rb"),
        purpose="user_data",
        preprocess_configs={"video": {"fps": 1}},
    )
    print(f"upload video file: {file_obj.id}")
    client.files.wait_for_processing(file_obj.id)
    print(f"video file processed: {file_obj.id}")
    file_id = str(file_obj.id)
    response = client.responses.create(
        model="doubao-seed-2-0-lite-260215",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_video", "file_id": file_id},
                    {"type": "input_text", "text": prompt},
                ],
            }
        ],
    )
    return _extract_output_text(response)

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True)
    p.add_argument("--prompt", required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    out = run(input_video=args.video, prompt=args.prompt)
    print(out)

if __name__ == "__main__":
    raise SystemExit(main())
