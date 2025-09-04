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
    resp = tokens.get_item(Key={"provider": "facebook"})
    return resp.get("Item", {}).get("tokens", {})

def lambda_handler(event, context):
    v = (event or {}).get("video", {})
    video_key = v.get("video_landscape_s3_key") or v.get("video_portrait_s3_key")
    if not video_key: raise RuntimeError("No video key")
    if already_done("facebook", video_key): return {"skipped": True}
    t = _tok()
    page_id = t.get("page_id")
    page_token = t.get("page_access_token")
    if not page_id or not page_token: raise RuntimeError("Facebook page not authorized.")
    # Download file to /tmp
    import os, tempfile
    tmp = os.path.join(tempfile.gettempdir(), os.path.basename(video_key))
    s3.download_file(ASSETS_BUCKET, video_key, tmp)
    # Upload to Page Videos endpoint
    files = { 'source': open(tmp, 'rb') }
    data = { 'access_token': page_token, 'title': 'AutoContent Pro', 'description': 'Automated upload' }
    r = requests.post(f"https://graph.facebook.com/v17.0/{page_id}/videos", files=files, data=data, timeout=60)
    resp = r.json()
    if "id" not in resp: raise RuntimeError("Facebook upload failed: " + json.dumps(resp))
    mark_done("facebook", video_key, resp["id"])
    return {"facebook_video_id": resp["id"]}
