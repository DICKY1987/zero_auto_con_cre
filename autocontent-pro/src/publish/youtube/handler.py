import os, time, boto3, tempfile
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ASSETS_BUCKET=os.getenv("ASSETS_BUCKET")
dynamodb=boto3.resource("dynamodb")
idem=dynamodb.Table(os.getenv("IDEMPOTENCY_TABLE"))
tokens=dynamodb.Table(os.getenv("TOKENS_TABLE"))
s3=boto3.client("s3")

def _done(k): return "Item" in idem.get_item(Key={"k":k})
def _mark(k, rid): idem.put_item(Item={"k":k,"ts":int(time.time()),"remote_id":rid})
def _yt_tokens():
    r=tokens.get_item(Key={"provider":"youtube"}); return r.get("Item",{}).get("tokens")
def _creds():
    t=_yt_tokens()
    if not t: raise RuntimeError("YouTube not authorized.")
    c=Credentials(token=t.get("access_token"), refresh_token=t.get("refresh_token"), token_uri="https://oauth2.googleapis.com/token", client_id=t.get("client_id"), client_secret=t.get("client_secret"))
    if not c.valid and c.expired and c.refresh_token:
        c.refresh(Request())
        tokens.put_item(Item={"provider":"youtube","tokens":{"access_token":c.token,"refresh_token":c.refresh_token,"client_id":c.client_id,"client_secret":c.client_secret},"updated":int(time.time())})
    return c

def lambda_handler(event, context):
    v=(event or {}).get("video",{})
    key=v.get("video_portrait_s3_key") or v.get("video_landscape_s3_key")
    if not key: raise RuntimeError("No video key")
    idem_key=f"youtube#{key}"
    if _done(idem_key): return {"skipped":True}
    tmp=os.path.join(tempfile.gettempdir(), os.path.basename(key)); s3.download_file(ASSETS_BUCKET, key, tmp)
    yt=build("youtube","v3",credentials=_creds())
    body={"snippet":{"title":"AutoContent Pro","description":"Automated upload","categoryId":"27"},"status":{"privacyStatus":"private"}}
    media=MediaFileUpload(tmp, chunksize=-1, resumable=True, mimetype="video/*")
    req=yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp=None
    while resp is None:
        status, resp = req.next_chunk()
    vid=resp.get("id"); _mark(idem_key, vid)
    return {"youtube_video_id": vid}
