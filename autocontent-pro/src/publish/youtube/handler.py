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

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

dynamodb = boto3.resource("dynamodb")
tokens = dynamodb.Table(os.getenv("TOKENS_TABLE"))

def _load_tokens():
    resp = tokens.get_item(Key={"provider": "youtube"})
    return resp.get("Item", {}).get("tokens")

def _get_creds():
    t = _load_tokens()
    if not t: raise RuntimeError("YouTube not authorized.")
    creds = Credentials(token=t.get("access_token"), refresh_token=t.get("refresh_token"),
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=t.get("client_id"), client_secret=t.get("client_secret"))
    if not creds.valid and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        tokens.put_item(Item={"provider": "youtube", "tokens": {
            "access_token": creds.token, "refresh_token": creds.refresh_token,
            "client_id": creds.client_id, "client_secret": creds.client_secret
        }, "updated": int(time.time())})
    return creds

def lambda_handler(event, context):
    v = (event or {}).get("video", {})
    # Prefer portrait to qualify as Short when length <= 60s
    video_key = v.get("video_portrait_s3_key") or v.get("video_landscape_s3_key")
    if not video_key: raise RuntimeError("No video key")
    if already_done("youtube", video_key): return {"skipped": True}

    tmp = os.path.join(tempfile.gettempdir(), os.path.basename(video_key))
    s3.download_file(ASSETS_BUCKET, video_key, tmp)

    creds = _get_creds()
    yt = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": "AutoContent Pro",
            "description": "Automated upload",
            "categoryId": "27"
        },
        "status": { "privacyStatus": "private" }
    }
    media = MediaFileUpload(tmp, chunksize=-1, resumable=True, mimetype="video/*")
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
    vid = response.get("id")
    mark_done("youtube", video_key, vid)
    return {"youtube_video_id": vid}
