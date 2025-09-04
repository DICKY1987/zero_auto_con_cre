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
    video_key = v.get("video_portrait_s3_key") or v.get("video_landscape_s3_key")
    if not video_key: raise RuntimeError("No video key")
    if already_done("instagram", video_key): return {"skipped": True}
    t = _tok()
    page_id = t.get("page_id")
    page_token = t.get("page_access_token")
    if not page_id or not page_token: raise RuntimeError("Facebook/IG not authorized.")

    # Get IG Business Account connected to the page
    r = requests.get(f"https://graph.facebook.com/v17.0/{page_id}", params={
        "fields": "instagram_business_account", "access_token": page_token
    }, timeout=15).json()
    ig_id = r.get("instagram_business_account", {}).get("id")
    if not ig_id: raise RuntimeError("No IG business account linked to the page.")

    # Step 1: Create media container
    # For reels, we need public URL. We pre‑sign S3 URL (signed for short time).
    s3r = boto3.client("s3")
    url = s3r.generate_presigned_url("get_object", Params={"Bucket": ASSETS_BUCKET, "Key": video_key}, ExpiresIn=900)
    create = requests.post(f"https://graph.facebook.com/v17.0/{ig_id}/media", data={
        "access_token": page_token,
        "media_type": "REELS",
        "video_url": url,
        "caption": "AutoContent Pro"
    }, timeout=60).json()
    if "id" not in create: raise RuntimeError("IG create failed: " + json.dumps(create))
    container_id = create["id"]

    # Step 2: Publish container
    pub = requests.post(f"https://graph.facebook.com/v17.0/{ig_id}/media_publish", data={
        "access_token": page_token, "creation_id": container_id
    }, timeout=30).json()
    if "id" not in pub: raise RuntimeError("IG publish failed: " + json.dumps(pub))

    mark_done("instagram", video_key, pub["id"])
    return {"instagram_media_id": pub["id"]}
