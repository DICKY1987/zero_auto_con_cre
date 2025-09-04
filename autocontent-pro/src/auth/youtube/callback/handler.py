import os, boto3, requests, time

ssm = boto3.client("ssm")
ddb = boto3.resource("dynamodb")
tokens = ddb.Table(os.getenv("TOKENS_TABLE"))
def _param(n): return ssm.get_parameter(Name=n, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    qs = event.get("queryStringParameters") or {}
    code = qs.get("code")
    if not code: return {"statusCode": 400, "body": "Missing code"}

    client_id = _param("/autocontent/youtube/client_id")
    client_secret = _param("/autocontent/youtube/client_secret")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/youtube/callback"

    tok = requests.post("https://oauth2.googleapis.com/token",
                        headers={"Content-Type":"application/x-www-form-urlencoded"},
                        data={
                          "code": code, "client_id": client_id, "client_secret": client_secret,
                          "redirect_uri": redirect_uri, "grant_type": "authorization_code"
                        }, timeout=15).json()

    tokens.put_item(Item={
        "provider": "youtube",
        "tokens": {
            "access_token": tok.get("access_token"),
            "refresh_token": tok.get("refresh_token"),
            "client_id": client_id, "client_secret": client_secret
        },
        "updated": int(time.time())
    })
    return {"statusCode": 200, "headers": {"Content-Type": "text/html"},
            "body": "<h3>YouTube connected. You can close this tab.</h3>"}
