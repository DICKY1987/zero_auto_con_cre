import os, boto3, requests, time

ssm = boto3.client("ssm")
ddb = boto3.resource("dynamodb")
tokens = ddb.Table(os.getenv("TOKENS_TABLE"))

def _param(n): return ssm.get_parameter(Name=n, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}
    code = qs.get("code")
    if not code: return {"statusCode":400, "body":"Missing code"}

    client_key = _param("/autocontent/tiktok/client_key")
    client_secret = _param("/autocontent/tiktok/client_secret")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/tiktok/callback"

    resp = requests.post("https://open-api.tiktok.com/oauth/access_token/", data={
        "client_key": client_key, "client_secret": client_secret, "code": code, "grant_type": "authorization_code", "redirect_uri": redirect_uri
    }, timeout=15).json()

    access_token = resp.get("data", {}).get("access_token")
    open_id = resp.get("data", {}).get("open_id")

    tokens.put_item(Item={
        "provider": "tiktok",
        "tokens": {"access_token": access_token, "open_id": open_id, "client_key": client_key, "client_secret": client_secret},
        "updated": int(time.time())
    })

    return {"statusCode": 200, "headers": {"Content-Type":"text/html"}, "body": "<h3>TikTok connected. You can close this tab.</h3>"}
