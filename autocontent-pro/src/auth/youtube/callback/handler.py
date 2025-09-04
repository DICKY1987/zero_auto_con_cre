import os, urllib.parse, boto3, json, time, requests

ssm = boto3.client("ssm")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.getenv("TOKENS_TABLE"))

def _param(name):
    return ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    code = params.get("code")
    if not code:
        return {"statusCode": 400, "body": "Missing code"}

    client_id = _param("/autocontent/youtube/client_id")
    client_secret = _param("/autocontent/youtube/client_secret")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/youtube/callback"

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    tok = requests.post("https://oauth2.googleapis.com/token",
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data=data, timeout=15).json()

    table.put_item(Item={
        "provider": "youtube",
        "tokens": {
            "access_token": tok.get("access_token"),
            "refresh_token": tok.get("refresh_token"),
            "client_id": client_id,
            "client_secret": client_secret
        },
        "updated": int(time.time())
    })
    return {"statusCode": 200, "headers": {"Content-Type": "text/html"},
            "body": "<h3>YouTube connected. You can close this tab.</h3>"}
