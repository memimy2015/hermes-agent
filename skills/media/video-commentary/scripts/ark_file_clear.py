import os
from volcenginesdkarkruntime import Ark
from dotenv import load_dotenv
load_dotenv()

def run():
    api_key = os.getenv('ARK_API_KEY')
    client = Ark(
        base_url='https://ark.cn-beijing.volces.com/api/v3',
        api_key=api_key,
    )
    response = client.files.list()
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    if not data:
        return
    for f in data:
        fid = getattr(f, "id", None) if not isinstance(f, dict) else f.get("id")
        if not fid:
            continue
        try:
            client.files.delete(file_id=fid)
        except Exception:
            continue

def main() -> str:
    run()
    return "clear file success!"

if __name__ == "__main__":
    raise SystemExit(main())