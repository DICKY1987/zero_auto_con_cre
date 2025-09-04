import os, urllib.parse, boto3, secrets

ssm = boto3.client("ssm")
def _param(n): return ssm.get_parameter(Name=n, WithDecryption=True)["Parameter"]["Value"]

def lambda_handler(event, context):
    client_key = _param("/autocontent/tiktok/client_key")
    proto = event['headers'].get("x-forwarded-proto", "https")
    host = event['headers']['host']
    redirect_uri = f"{proto}://{host}/auth/tiktok/callback"
    state = secrets.token_urlsafe(16)
    scope = "video.upload"
    auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": client_key, "redirect_uri": redirect_uri, "response_type": "code", "scope": scope, "state": state
    })
    return {"statusCode": 302, "headers": {"Location": auth_url}}
