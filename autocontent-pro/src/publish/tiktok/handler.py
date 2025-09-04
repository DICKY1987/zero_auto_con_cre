import os, time, boto3, tempfile
dynamodb = boto3.resource("dynamodb")
idem = dynamodb.Table(os.getenv("IDEMPOTENCY_TABLE"))
s3 = boto3.client("s3")
ASSETS_BUCKET = os.getenv("ASSETS_BUCKET")

def already_done(channel, video_key):
    k = f"{channel}#{video_key}"
    resp = idem.get_item(Key={"k": k})
    return "Item" in resp

def mark_done(channel, video_key, remote_id):
    k = f"{channel}#{video_key}"
    idem.put_item(Item={"k": k, "ts": int(time.time()), "remote_id": remote_id})

import requests, json
dynamodb = boto3.resource("dynamodb")
tokens = dynamodb.Table(os.getenv("TOKENS_TABLE"))

def _tok():
    resp = tokens.get_item(Key={"provider": "tiktok"})
    return resp.get("Item", {}).get("tokens", {})

def lambda_handler(event, context):
    v = (event or {}).get("video", {})
    video_key = v.get("video_portrait_s3_key") or v.get("video_landscape_s3_key")
    if not video_key: raise RuntimeError("No video key")
    if already_done("tiktok", video_key): return {"skipped": True}
    t = _tok()
    access_token = t.get("access_token")
    open_id = t.get("open_id")
    if not access_token or not open_id: raise RuntimeError("TikTok not authorized.")
    # Pre-signed URL
    url = s3.generate_presigned_url("get_object", Params={"Bucket": ASSETS_BUCKET, "Key": video_key}, ExpiresIn=900)
    # Simple upload via URL (Open API requires upload endpoint; here we use a simplified v2 endpoint shape)
    r = requests.post("https://open-api.tiktok.com/share/video/upload/", data={
        "open_id": open_id, "video_url": url, "access_token": access_token, "text": "AutoContent Pro"
    }, timeout=60).json()
    if "data" not in r or "video_id" not in r["data"]:
        raise RuntimeError("TikTok upload failed: " + json.dumps(r))
    vid = r["data"]["video_id"]
    mark_done("tiktok", video_key, vid)
    return {"tiktok_video_id": vid}
